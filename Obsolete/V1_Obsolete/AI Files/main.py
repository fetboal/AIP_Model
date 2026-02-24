from PDFPageFunctions import open_pdf_by_index, extract_pages_from_original, split_pdf_to_pages
from AI_interaction import (
    page_type_selection, 
    extract_financial_statement_details,
    extract_operational_risk_details,
    extract_debt_loans_details,
    extract_legal_details
)
from data_persistence import save_classification_data, load_classification_data
from report_generator import ReportGenerator
from utils import print_ai_response

# Loading Enviornment Variable
import dotenv

# Import the new analysis modules
from financial_statement_analysis import create_analysis_dataframes, run_financial_statement_analysis
from operational_risk_analysis import run_operational_risk_analysis
from legal_analysis import run_legal_analysis
from debt_analysis import run_debt_analysis

import os

#Import Open AI
from openai import OpenAI

# --- Project Root Setup ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# --- Load Environment Variables ---
# Explicitly load the .env file from the project root
dotenv_path = os.path.join(PROJECT_ROOT, '.env')
dotenv.load_dotenv(dotenv_path=dotenv_path)

def initialize_app():
    """Initializes the application by setting up the environment and OpenAI client."""
    if not os.path.exists(dotenv_path):
        print("Warning: .env file not found. Please create one with your OPENAI_API_KEY.")
        return None, None

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set.")
    client = OpenAI(api_key=api_key)

    output_pdf_dir = os.path.join(PROJECT_ROOT, "generated PDFS")
    os.makedirs(output_pdf_dir, exist_ok=True)
    
    return client, output_pdf_dir

def prepare_pages_to_process(all_pages, is_testing=True):
    """
    Selects a subset of pages for processing based on the is_testing flag.
    
    Returns:
        A list of (original_index, page_data) tuples.
    """
    if is_testing:
        # Manually select page indices (0-based) for testing.
        # These are good examples covering different categories.
        test_page_indices = [
            1,   # Other (Table of Contents)
            22,  # Operational and Risk (MD&A)
            26,  # Financial Statement (Sales discussion)
            39,  # Financial Statement (Balance Sheet)
            47,  # Financial Statement (Assets for sale)
            53,  # Debt and Loans
            73,  # Operational and Risk (Segment descriptions)
            409, # Legal
        ]
        # Create a list of (original_index, page_data) tuples
        pages_to_process_with_indices = [(i, all_pages[i]) for i in test_page_indices if 0 <= i < len(all_pages)]
        print("\n--- RUNNING IN TEST MODE ---")
        print(f"Processing a subset of {len(pages_to_process_with_indices)} pages with original indices: {test_page_indices}")
    else:
        print("\n--- RUNNING IN FULL MODE ---")
        print(f"Processing all {len(all_pages)} pages.")
        # Create a list of (original_index, page_data) tuples for all pages
        pages_to_process_with_indices = list(enumerate(all_pages))
    
    return pages_to_process_with_indices

def run_ai_processing(pages_to_process, client):
    """
    Runs the full AI processing pipeline: page classification and detailed schema extraction.
    """
    # Step 1: Classify pages
    page_classifications, raw_ai_responses = page_type_selection(pages_to_process, client)
    
    # Step 2: Populate detailed schemas based on classification
    print("\n--- Populating Detailed Schemas for Each Page ---")
    for page_index, classification in page_classifications.items():
        category = classification['category']
        page_content = next((p[1] for p in pages_to_process if p[0] == page_index), None)

        if not page_content:
            continue

        print(f"  Populating schema for page {page_index + 1} (Category: {category})...")
        if category == "Financial Statement":
            details = extract_financial_statement_details(page_content, client)
        elif category == "Operational and Risk":
            details = extract_operational_risk_details(page_content, client)
        elif category == "Debt and Loans":
            details = extract_debt_loans_details(page_content, client)
        elif category == "Legal":
            details = extract_legal_details(page_content, client)
        else:
            details = {} # No details to extract for 'Other'

        if details:
            # Preserve the business_segment that was already extracted
            existing_segment = classification['key_metrics'].get('business_segment')
            
            # Update the key_metrics with the new, detailed data
            classification['key_metrics'] = details
            
            # Restore the original business_segment
            classification['key_metrics']['business_segment'] = existing_segment

    return page_classifications, raw_ai_responses

def generate_artifacts(page_classifications, raw_responses, pdf_path, output_dir):
    """Saves processed data and generates output reports and PDFs."""
    # Save classification data as a pickle file
    pickle_path = save_classification_data(page_classifications, raw_responses)
    print(f"Classification data saved to: {pickle_path}")
    
    # Generate readable PDF report
    report_filename = "PPG_Classification_Report.pdf"
    report_path = os.path.join(output_dir, report_filename)
    classification_reporter = ReportGenerator(report_path)
    classification_reporter.generate_classification_report(page_classifications)
    classification_reporter.build()
    print(f"Classification report saved to: {report_path}")
    
    # Group pages by category to create separate PDFs
    category_pages = {
        'Financial Statement': [],
        'Operational and Risk': [],
        'Debt and Loans': [],
        'Legal': [],
        'Other': []
    }
    for page_idx, classification in page_classifications.items():
        category = classification['category']
        if category in category_pages:
            category_pages[category].append(page_idx)
    
    # Extract pages for each category that has content
    print("\n--- Generating PDFs for each category ---")
    for category, page_indexes in category_pages.items():
        if page_indexes:  # Only extract if there are pages in this category
            category_filename = f"{category.replace(' ', '_').replace('&', 'and')}_Pages.pdf"
            category_output_path = os.path.join(output_dir, category_filename)
            extract_pages_from_original(pdf_path, page_indexes, output_path=category_output_path, open_pdf=False)

def run_classification_pipeline(pdf_path: str, is_testing: bool):
    """
    Executes the full data extraction and classification pipeline.
    """
    print("\n--- Starting Classification Pipeline ---")
    client, output_dir = initialize_app()
    if not client:
        return # Exit if initialization fails

    all_pages = split_pdf_to_pages(pdf_path)
    print(f"Got {len(all_pages)} pages from PDF.")

    pages_to_process = prepare_pages_to_process(all_pages, is_testing=is_testing)
    
    if not pages_to_process:
        print("No pages selected for processing. Exiting.")
        return

    page_classifications, raw_responses = run_ai_processing(pages_to_process, client)

    generate_artifacts(page_classifications, raw_responses, pdf_path, output_dir)
    print("\n--- Classification Pipeline Completed Successfully ---")

def run_analysis_pipeline(analysis_types: list, financial_segments: list | None = None, print_to_console: bool = True):
    """
    Loads processed data and runs the selected analysis modules.
    """
    analysis_results = {}
    print("\n--- Starting Analysis Pipeline ---")
    try:
        page_classifications, _, _ = load_classification_data()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please run the 'classification' mode first to generate the data file.")
        return

    # Set pandas display options for better console output
    import pandas as pd
    pd.options.display.float_format = '{:,.2f}'.format
    pd.set_option('display.max_rows', 100)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 150)
    pd.set_option('display.max_colwidth', 80)

    _, categorized_dfs = create_analysis_dataframes(page_classifications)

    if categorized_dfs is None:
        print("Error: Failed to create analysis dataframes.")
        return

    if 'financial' in analysis_types:
        analysis_results['financial'] = run_financial_statement_analysis(page_classifications, target_segments=financial_segments, print_to_console=print_to_console)
    if 'operational' in analysis_types:
        analysis_results['operational'] = run_operational_risk_analysis(categorized_dfs, print_to_console=print_to_console)
    if 'legal' in analysis_types:
        analysis_results['legal'] = run_legal_analysis(categorized_dfs, print_to_console=print_to_console)
    if 'debt' in analysis_types:
        analysis_results['debt'] = run_debt_analysis(categorized_dfs, print_to_console=print_to_console)
    
    print("\n--- Analysis Pipeline Completed ---")

    # --- Generate Analysis Report ---
    if analysis_results:
        print("\n--- Generating Analysis Report PDF ---")
        _, output_dir = initialize_app() # Get output directory
        if output_dir is None:
            print("Error: Failed to initialize output directory. Skipping report generation.")
            return
        report_filename = "PPG_Analysis.pdf"
        report_path = os.path.join(output_dir, report_filename)
        analysis_reporter = ReportGenerator(report_path)
        analysis_reporter.generate_analysis_report(analysis_results)
        analysis_reporter.build()
    else:
        print("\nNo analysis was run, skipping report generation.")

def main():
    """Main function to run the entire PDF analysis pipeline."""
    # --- Configuration ---
    PDF_PATH = os.path.join(PROJECT_ROOT, "PPG_10K_2024.pdf")
    IS_TESTING = True # Set to False to run on all pages in classification mode

    # --- Mode Selection ---
    # Choose 'classification' to process the PDF and save data.
    # Choose 'analysis' to load saved data and run analyses.
    MODE = "analysis" 

    # --- Analysis Selection (only used in 'analysis' mode) ---
    # Add 'financial', 'operational', 'legal', or 'debt' to the list to run them.
    ANALYSIS_TO_RUN = ['financial', 'operational', 'legal', 'debt'] # Can be any combination

    # --- Financial Analysis Configuration (only used if 'financial' is in ANALYSIS_TO_RUN) ---
    # Specify which business segments to include in the financial analysis.
    # Common values are ['Consolidated'], or you can add specific segments like ['Performance Coatings'].
    FINANCIAL_ANALYSIS_SEGMENTS = ['Consolidated']

    # --- Console Output Configuration ---
    PRINT_ANALYSIS_TO_CONSOLE = False # Set to False to suppress console output from analysis modules

    if MODE == 'classification':
        run_classification_pipeline(PDF_PATH, IS_TESTING)
    elif MODE == 'analysis':
        if not ANALYSIS_TO_RUN:
            print("Analysis mode selected, but no analysis types were specified in ANALYSIS_TO_RUN.")
            print("Please add 'financial', 'operational', 'legal', or 'debt' to the list.")
        else:
            run_analysis_pipeline(ANALYSIS_TO_RUN, financial_segments=FINANCIAL_ANALYSIS_SEGMENTS, print_to_console=PRINT_ANALYSIS_TO_CONSOLE)
    else:
        print(f"Error: Invalid MODE '{MODE}'. Please choose 'classification' or 'analysis'.")
        
if __name__ == "__main__":
    main()
