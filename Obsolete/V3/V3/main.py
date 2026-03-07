import os
import sys

# This ensures that the script can find the modules in the '01_Data' directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from _01_Data_Analysis.Statement_Data import EdgarFinancials

def main():
    """
    Main function to demonstrate fetching financial statements from SEC EDGAR.
    """
    
    # --- Configuration ---
    # Replace with your email as required by the SEC for the User-Agent.
    # It's good practice to use environment variables for this.
    EMAIL_FOR_SEC = "feb2126@columbia.edu"
    TICKER = "NVDA"  # Example: NVIDIA Corporation

    print(f"Initializing EDGAR financials client for {TICKER}...")
    # Create an instance of the EdgarFinancials class
    edgar_client = EdgarFinancials(email=EMAIL_FOR_SEC, ticker=TICKER)

    print(f"Fetching the most recent 5 10-K filings for {TICKER}...")
    # Get the most recent 10 10-K filings
    # This can take a moment as it's downloading data from the SEC.
    latest_10ks = edgar_client.get_multiple_filings(filing_type='10-K', count=10)

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

    # Combine all statements using the combine dataframes function
    combined_balance_sheet, combined_cash_flow, combined_income_statement = edgar_client.combine_dataframes(statements)

    # Export to CSV using export_dataframes_to_csv function
    edgar_client.export_dataframes_to_csv(combined_balance_sheet, combined_cash_flow, combined_income_statement, TICKER)

if __name__ == "__main__":
    main()