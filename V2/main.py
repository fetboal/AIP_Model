import os
import sys

# This ensures that the script can find the modules in the '01_Data' directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from _01_Data_Analysis.Statement_Data import EdgarFinancials
from _02_Report_Generation.Report_Generator import ReportGenerator

def main():
    """
    Main function to demonstrate fetching financial statements from SEC EDGAR.
    """
    # --- Configuration ---
    # Replace with your email as required by the SEC for the User-Agent.
    # It's good practice to use environment variables for this.
    EMAIL_FOR_SEC = "feb2126@columbia.edu"
    TICKER = "PPG"  # Example: PPG Industries, Inc.

    print(f"Initializing EDGAR financials client for {TICKER}...")
    # Create an instance of the EdgarFinancials class
    edgar_client = EdgarFinancials(email=EMAIL_FOR_SEC, ticker=TICKER)

    print(f"Fetching the most recent 5 10-K filings for {TICKER}...")
    # Get the most recent 5 10-K filings
    # This can take a moment as it's downloading data from the SEC.
    latest_10ks = edgar_client.get_multiple_filings(filing_type='10-K', count=1)

    print(f"Retrieved {len(latest_10ks)} 10-K filings")

    # Define desired statement types to extract
    statement_types = ['Income Statement', 'Balance Sheet', 'Cash Flow Statement']
    
    print(f"\nExtracting statement types: {statement_types}")
    print("Fetching and processing financial statements using keyword matching...")
    
    # Get statements using get_statements_by_type with dynamic keyword matching
    statements = edgar_client.get_statements_by_type(latest_10ks, statement_types)

    print(f"\n{'='*80}")
    print(f"Successfully retrieved {len(statements)} statements")
    print(f"{'='*80}\n")

    # Generate PDF report with tables
    output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_03_Outputs')
    report_gen = ReportGenerator(report_name='test', save_location=output_folder)
    
    print("Generating PDF report with tables...")
    
    # Add each statement as a table without titles
    for accession_number, statement_type, sheet_name, df in statements:
        report_gen.add_table_from_df(df, title=None)
    
    # Save the final PDF
    report_gen.save()

if __name__ == "__main__":
    main()