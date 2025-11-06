import re


def get_schema_for_category(category: str) -> dict:
    """
    Returns a predefined dictionary schema for the key metrics of a given category.
    """
    schema = {} # Initialize an empty schema dictionary
    if category == "Financial Statement":
        schema = {
            "Income Statement": {
                "Net Sales": [], "Cost of Goods Sold": [], "Gross Profit": [],
                "Operating Income": [], "Interest Expense": [], "Income Before Tax": [],
                "Net Income": []
            },
            "Balance Sheet": {
                "Cash and Cash Equivalents": [], "Accounts Receivable": [], "Inventory": [],
                "Total Current Assets": [], "Property, Plant & Equipment (Net)": [],
                "Total Assets": [], "Accounts Payable": [], "Total Current Liabilities": [],
                "Long-term Debt": [], "Total Liabilities": [], "Total Shareholders' Equity": []
            },
            "Cash Flow": {
                "Net Cash from Operating Activities": [], "Net Cash from Investing Activities": [],
                "Net Cash from Financing Activities": []
            },
        }
    elif category == "Operational and Risk":
        schema = {
            "Business Segments": [],  # List of dicts: {'name': str, 'products': str, 'revenue': float, 'income': float}
            "Geographic Exposure": [],  # List of dicts: {'region': str, 'revenue': float}
            "Competitive Landscape": {
                "Competitors": [],
                "Market Position": None
            },
            "Key Risks": [],  # List of dicts: {'risk': str, 'mitigation': str}
            "MD&A": {
                "Commentary on Performance": None,
                "Forward-looking Statements": None
            }
        }
    elif category == "Debt and Loans":
        schema = {
            "Debt Instruments": [],  # List of dicts: {'type': str, 'amount': float, 'rate': str, 'maturity': str}
            "Covenants": None,
            "Capital Structure": {
                "Total Debt": None,
                "Total Equity": None
            }
        }
    elif category == "Legal":
        schema = {
            "Litigation": [],  # List of dicts: {'case': str, 'impact': str}
            "Regulatory Matters": [],
            "Corporate Governance": None
        }
    # For 'Other', schema remains an empty dict {}
    
    # Add the common variable to all schemas. It will be a list to hold multiple segments if found.
    schema["business_segment"] = []
    return schema

def structure_ai_response_data(classification_response_text: str, schema_response_text: str = ""):
    """
    Create a structured version of the data from the two-step AI process.
    
    Args:
        classification_response_text (str): Raw text from the classification AI call.
        schema_response_text (str): Raw text from the schema extraction AI call.
        
    Returns:
        dict: Structured data with category, reasoning, and summary
    """
    lines = classification_response_text.split('\n')

    # Initialize result structure with defaults
    result = {
        'category': 'Other',
        'reasoning_points': [],
        'overall_focus': 'Not specified',
        'summary': classification_response_text[:200] + "..." if len(classification_response_text) > 200 else classification_response_text
    }

    # 1. More precise category extraction
    # The prompt asks for "This page is part of the [CATEGORY] section..."
    category_pattern = re.compile(r"part of the ([\w\s&]+) section", re.IGNORECASE)
    for line in lines:
        match = category_pattern.search(line)
        if match:
            # Normalize the extracted category name
            cat_text = match.group(1).strip().lower()
            if "operational and risk" in cat_text:
                result['category'] = 'Operational and Risk'
            elif "financial statement" in cat_text:
                result['category'] = 'Financial Statement'
            elif "debt and loans" in cat_text:
                result['category'] = 'Debt and Loans'
            elif "legal" in cat_text:
                result['category'] = 'Legal'
            # 'Other' remains the default
            break

    # 2. Initialize the structured key_metrics based on the determined category
    result['key_metrics'] = get_schema_for_category(result['category'])

    # 3. Refined extraction for reasoning points and overall focus
    for line in lines:
        line = line.strip()
        # Match bullet points for reasoning
        if re.match(r'^[•\-*§]|\d+\.', line):
            # Clean the line by removing the bullet/number part
            cleaned = re.sub(r'^[•\-*§\d\.]\s*', '', line).strip()
            if cleaned and "overall," not in cleaned.lower():
                result['reasoning_points'].append(cleaned)
        # Match the "Overall" summary line
        elif line.lower().startswith('overall'):
            overall_match = re.search(r'overall[,:]?\s*(.+)', line, re.IGNORECASE)
            if overall_match:
                result['overall_focus'] = overall_match.group(1).strip()

    # 4. Parse the schema data from the second AI call
    if schema_response_text:
        # Look for the line "BUSINESS SEGMENT: ..."
        segment_match = re.search(r"BUSINESS SEGMENT:\s*(.*)", schema_response_text, re.IGNORECASE)
        if segment_match and "not applicable" not in segment_match.group(1).lower():
            # Split by comma and strip whitespace for each segment
            segments = [s.strip() for s in segment_match.group(1).split(',')]
            result['key_metrics']['business_segment'] = segments

    return result
