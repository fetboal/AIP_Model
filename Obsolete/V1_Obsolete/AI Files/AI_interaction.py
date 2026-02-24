from openai import OpenAI
from io import BytesIO
import tempfile
import os
import re

from data_parser import structure_ai_response_data, get_schema_for_category
import json

class PDFPageClassificationExample:
    def __init__(self, page_index, page_number, category, reasoning_points, overall_focus):
        self.page_index = page_index
        self.page_number = page_number  
        self.category = category
        self.reasoning_points = reasoning_points
        self.overall_focus = overall_focus
    
    def to_prompt_format(self):
        points_text = "\n".join([f"• {point}" for point in self.reasoning_points])
        return f"""Page {self.page_number} (index {self.page_index}):
Output: This page is part of the {self.category.lower()} section for the following reasons:
{points_text}
• Overall, {self.overall_focus}"""

# Define few-shot learning examples
classification_examples = [
    # Operational and Risk Examples
    PDFPageClassificationExample(
        page_index=73, page_number=74, category="Operational and Risk",
        reasoning_points=[
            "Lists the three main segments: Global Architectural Coatings, Performance Coatings, and Industrial Coatings",
            "The Global Architectural Coatings, Performance Coatings, and Industrial Coatings breakdowns, including products and distribution locations",
            "Discusses production facilities and sales strategies for PPG's reportable business segments",
            "This section covers the fact that the company's decision maker is the Executive Committee and the process for resource allocation"
        ],
        overall_focus="it has a focus on company operations"
    ),
    PDFPageClassificationExample(
        page_index=22, page_number=23, category="Operational and Risk",
        reasoning_points=[
            "It covers significant divestitures, including the Company's completed divestitures of the silica products business and the architectural coatings business in the U.S. and Canada",
            "Describes the macroeconomic expectations in different regions, including Europe, Mexico, and China",
            "Discusses financing strategies, including share repurchases, capex, and dividends",
            "Describes price improvements across the fiscal year",
            "Looks into the effects of tax and forex on business operations"
        ],
        overall_focus="it has a focus on company operations"
    ),
    
    # Financial Statement Examples
    PDFPageClassificationExample(
        page_index=39, page_number=40, category="Financial Statement",
        reasoning_points=[
            "This section is the consolidated balance sheet",
            "Gives a table covering assets, liabilities, and shareholders' equity"
        ],
        overall_focus="it focuses on financial data"
    ),
    PDFPageClassificationExample(
        page_index=47, page_number=48, category="Financial Statement",
        reasoning_points=[
            "Give a table with the assets held for sale",
            "Included current and non-current assets"
        ],
        overall_focus="it focuses on financial data"
    ),
    PDFPageClassificationExample(
        page_index=26, page_number=27, category="Financial Statement",
        reasoning_points=[
            "Shows the change in sales from 2022 to 2023 and from 2023 to 2024",
            "Looking at sales behavior relative to expectations"
        ],
        overall_focus="it focuses on financial data"
    ),
    
    # Debt and Loans Example
    PDFPageClassificationExample(
        page_index=53, page_number=54, category="Debt and Loans",
        reasoning_points=[
            "Focuses on a €500 million term loan credit agreement",
            "Highlight the interest rate and currencies for the loan (SOFR and USD/Euro)",
            "Talks about debt covenants and the event of default"
        ],
        overall_focus="it focuses on debt and its characteristics"
    ),
    
    # Legal Example
    PDFPageClassificationExample(
        page_index=409, page_number=410, category="Legal",
        reasoning_points=[
            "This section covers the terms of the contract",
            "Looks at deductions for compensation, fringe benefits, or vacation pay"
        ],
        overall_focus="it focuses on the company and its employees' legal responsibilities"
    ),
    
    # Other Example
    PDFPageClassificationExample(
        page_index=1, page_number=2, category="Other",
        reasoning_points=[
            "This section is the table of contents",
            "Does not fall into any of the other categories",
            "Does not cover any information that would be used in a company analysis"
        ],
        overall_focus="it does not fit standard analysis categories"
    )
]

def get_classification_examples(num_examples=5):
    """Get a selection of classification examples for few-shot learning"""
    # Get diverse examples across categories
    examples_by_category = {}
    for example in classification_examples:
        if example.category not in examples_by_category:
            examples_by_category[example.category] = []
        examples_by_category[example.category].append(example)
    
    # Select examples ensuring category diversity
    selected = []
    for category, examples in examples_by_category.items():
        selected.extend(examples[:2])  # Take up to 2 examples per category
        if len(selected) >= num_examples:
            break
    
    return selected[:num_examples]

def build_classification_prompt(examples):
    """Build the few-shot learning prompt with examples"""
    prompt = """Analyze this PDF page and classify it into one of these categories:
• Operational and Risk
• Financial Statement  
• Debt and Loans
• Legal
• Other

Here are examples of how to classify pages:

"""
    
    for example in examples:
        prompt += example.to_prompt_format() + "\n\n"
    
    prompt += """Now classify this page following the same format. Provide specific reasoning points and an overall focus statement.

Output: This page is part of the [CATEGORY] section for the following reasons:
• [Specific reason 1]
• [Specific reason 2]
• [Additional reasons as needed]
• Overall, [a summary of the page's focus]
"""
    
    return prompt

def build_schema_extraction_prompt(category: str):
    """Builds a prompt to extract schema data for a given category."""
    
    # We can customize this later to include the full schema for the AI to fill out
    # For now, we focus on the business segment as requested.
    
    prompt = f"""
The provided page has been classified as '{category}'.

Your task is to identify which business segment(s) the information on this page pertains to.
Business segments might be names like "Performance Coatings", "Industrial Coatings", "Global Architectural Coatings", or a consolidated name like "Total", "Consolidated", or "Corporate".

If the page clearly relates to one or more specific segments, list them.
If the page contains consolidated data for the entire company, use "Consolidated".
If the page does not relate to any specific business segment (e.g., a table of contents), state "Not Applicable".

Provide the output ONLY in the following format:
BUSINESS SEGMENT: [Segment Name 1], [Segment Name 2]

Example 1:
BUSINESS SEGMENT: Performance Coatings

Example 2:
BUSINESS SEGMENT: Consolidated"""
    
    return prompt

def page_type_selection(pages_with_indices: list[tuple[int, BytesIO]], client: OpenAI):
    '''
    Function that is given an array of PDF pages as a BytesIO objects.
    
    It analyses each page and classifies it into different types such as:
        - Operational and Risk
        - Financial Statement 
        - Debt and Loans
        - Legal
        - Other
        
    Uses few-shot learning with examples to improve classification accuracy.
    Returns two separate dictionaries: classifications and raw AI responses.
    '''

    # Get few-shot learning examples
    examples = get_classification_examples(num_examples=6)
    classification_prompt = build_classification_prompt(examples)

    page_classification = {}
    raw_responses = {}
    schema_response_text = "" # Initialize schema response text

    for original_index, pdf_page in pages_with_indices:
        # Reset BytesIO position to beginning
        pdf_page.seek(0)
        
        # Save BytesIO to a temporary file with proper PDF extension
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(pdf_page.read())
            temp_file_path = temp_file.name
        
        # --- Step 1: Classification Call ---
        try:
            # Upload the temporary file to OpenAI
            with open(temp_file_path, 'rb') as f:
                file = client.files.create(
                    file=f,
                    purpose="user_data"
                )
        finally:
            # We will reuse the temp file for the second call
            pass

        classification_response = client.responses.create(
            model="gpt-4o",
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_file",
                            "file_id": file.id,
                        },
                        {
                            "type": "input_text",
                            "text": classification_prompt,
                        },
                    ]
                }
            ]
        )

        classification_response_text = classification_response.output_text.strip()
        # Print progress update
        print(f"Page {original_index + 1} (index {original_index}): Classification complete.")

        # Temporarily parse to get the category for the next step
        temp_structured_data = structure_ai_response_data(classification_response_text)
        page_category = temp_structured_data['category']

        # --- Step 2: Schema Data Extraction Call ---
        if page_category != 'Other':
            schema_prompt = build_schema_extraction_prompt(page_category)
            try:
                # Re-upload the same file if needed, or reuse file_id if API allows
                with open(temp_file_path, 'rb') as f:
                    file_for_schema = client.files.create(file=f, purpose="user_data")

                schema_response = client.responses.create(
                    model="gpt-4o",
                    input=[{"role": "user", "content": [{"type": "input_file", "file_id": file_for_schema.id}, {"type": "input_text", "text": schema_prompt}]}]
                )
                schema_response_text = schema_response.output_text.strip()
                print(f"Page {original_index + 1} (index {original_index}): Schema data extraction complete.")

            except Exception as e:
                print(f"Error during schema extraction on page {original_index + 1}: {e}")
                schema_response_text = "" # Ensure it's empty on error
        else:
            schema_response_text = "" # No schema extraction for 'Other'

        # Clean up the temporary file after both calls are done
        os.unlink(temp_file_path)

        # --- Step 3: Final Structuring ---
        # Now structure the final object using both AI responses
        structured_data = structure_ai_response_data(classification_response_text, schema_response_text)
        
        # Store the structured classification results. The parser now returns the exact format we need.
        page_classification[original_index] = structured_data
        page_classification[original_index]['page_number'] = original_index + 1
        
        # Store raw AI response separately
        raw_responses[original_index] = {
            'page_number': original_index + 1,
            'classification_text': classification_response_text,
            'schema_text': schema_response_text,
            'length': len(classification_response_text) + len(schema_response_text)
        }
    
    return page_classification, raw_responses

def _extract_details_with_json_prompt(pdf_page: BytesIO, client: OpenAI, prompt: str) -> dict:
    """
    A generic helper function to call the AI with a JSON-based extraction prompt.
    """
    pdf_page.seek(0)
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        temp_file.write(pdf_page.read())
        temp_file_path = temp_file.name
    
    try:
        with open(temp_file_path, 'rb') as f:
            file = client.files.create(file=f, purpose="user_data")
        
        response = client.responses.create(
            model="gpt-4o",
            input=[{"role": "user", "content": [{"type": "input_file", "file_id": file.id}, {"type": "input_text", "text": prompt}]}],
        )
        # The model is instructed to return a JSON string in the prompt.
        # We need to parse this string.
        raw_text = response.output_text.strip()
        
        # Clean the text: remove markdown code block fences if they exist
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        
        try:
            return json.loads(raw_text.strip())
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from AI response: {e}")
            print(f"Raw AI output: {response.output_text}")
            return {}
    except Exception as e:
        print(f"An error occurred during JSON data extraction: {e}")
        return {}
    finally:
        os.unlink(temp_file_path)

def extract_financial_statement_details(pdf_page: BytesIO, client: OpenAI) -> dict:
    """Extracts details for a Financial Statement page."""
    schema = get_schema_for_category("Financial Statement")
    prompt = f"""
    Analyze the provided Financial Statement page. Extract all relevant financial figures and populate the following JSON structure.
    For each financial item, create an object with the value, unit, year, and the business segment it applies to (e.g., "Consolidated", "Performance Coatings").
    If a value is not present, use an empty list []. Return ONLY a valid JSON object.

    Example for a single item: "Net Sales": [{{"value": 100, "unit": "million", "year": 2023, "segment": "Consolidated"}}]

    {json.dumps(schema, indent=4)}
    """
    return _extract_details_with_json_prompt(pdf_page, client, prompt)

def extract_operational_risk_details(pdf_page: BytesIO, client: OpenAI) -> dict:
    """Extracts details for an Operational and Risk page."""
    schema = get_schema_for_category("Operational and Risk")
    prompt = f"""
    Analyze the provided 'Operational and Risk' page. Extract all relevant details and populate the following JSON structure.
    If a field is not mentioned, use null or an empty list []. Return ONLY a valid JSON object.

    {json.dumps(schema, indent=4)}
    """
    return _extract_details_with_json_prompt(pdf_page, client, prompt)

def extract_debt_loans_details(pdf_page: BytesIO, client: OpenAI) -> dict:
    """Extracts details for a Debt and Loans page."""
    schema = get_schema_for_category("Debt and Loans")
    prompt = f"""
    Analyze the provided 'Debt and Loans' page. Extract all relevant details and populate the following JSON structure.
    If a field is not mentioned, use null or an empty list []. Return ONLY a valid JSON object.

    {json.dumps(schema, indent=4)}
    """
    return _extract_details_with_json_prompt(pdf_page, client, prompt)

def extract_legal_details(pdf_page: BytesIO, client: OpenAI) -> dict:
    """Extracts details for a Legal page."""
    schema = get_schema_for_category("Legal")
    prompt = f"""
    Analyze the provided 'Legal' page. Extract all relevant details and populate the following JSON structure.
    If a field is not mentioned, use null or an empty list []. Return ONLY a valid JSON object.

    {json.dumps(schema, indent=4)}
    """
    return _extract_details_with_json_prompt(pdf_page, client, prompt)
