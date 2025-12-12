import os
import sys

# This ensures that the script can find the modules in the '01_Data' directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Data_01.Statement_Data import EdgarFinancials

def main():
    """
    Main function to demonstrate fetching financial statements from SEC EDGAR.
    """
    # --- Configuration ---
    # Replace with your email as required by the SEC for the User-Agent.
    # It's good practice to use environment variables for this.
    EMAIL_FOR_SEC = "feb2126@columbia.edu"
    TICKER = "PPG"  # Example: Apple Inc.

    print(f"Initializing EDGAR financials client for {TICKER}...")
    # Create an instance of the EdgarFinancials class
    edgar_client = EdgarFinancials(email=EMAIL_FOR_SEC, ticker=TICKER)

    print(f"Fetching the most recent 10-K filing for {TICKER}...")
    # Get the most recent (index=0) 10-K filing
    # This can take a moment as it's downloading data from the SEC.
    latest_10k = edgar_client.get_filing(filing_type='10-K', index=0)

    if latest_10k:
        print("Extracting financial statements from the filing...")
        # Get the indices of the financial statement reports
        statement_indices = edgar_client.get_statements_pages(latest_10k)

        if statement_indices:
            print(f"Found {len(statement_indices)} financial statement reports at the following indices:")
            print(statement_indices)
        else:
            print("No financial statement reports found in this filing.")

        print("\nFetching Excel report from the filing...")
        excel_sheets = edgar_client.get_excel_from_filing(latest_10k)

        if excel_sheets:
            print(f"Found {len(excel_sheets)} sheets in the Excel file:")
        else:
            print("No Excel file found for this filing.")

        #Print the dataframes for the financial statement array

        for idx in statement_indices:
            if idx < len(excel_sheets):
                sheet_name, df = excel_sheets[idx]
                cleaned_df = edgar_client.clean_dataframe_header(df)
                print(f"\n--- Cleaned DataFrame for sheet '{sheet_name}' ---")
                print(cleaned_df.head())

if __name__ == "__main__":
    main()