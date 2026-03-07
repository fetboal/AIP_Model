import os

from dotenv import load_dotenv
load_dotenv()

from src.services.edgar_client import EdgarClient
from src.tools.financial_data_tools import get_statements_by_type, combine_dataframes
from src.utils.export_utils import export_dataframes_to_csv


def main():
    """
    Fetches financial statements from SEC EDGAR for a given ticker and exports them to CSV.
    """

    # --- Configuration ---
    # Set SEC_EMAIL in your .env file or environment. The SEC requires a valid
    # email address as the User-Agent for all EDGAR API requests.
    EMAIL_FOR_SEC = os.getenv("SEC_EMAIL", "your-email@example.com")
    TICKER = "NVDA"  # Example: NVIDIA Corporation

    print(f"Initializing EDGAR client for {TICKER}...")
    client = EdgarClient(email=EMAIL_FOR_SEC, ticker=TICKER)

    print(f"Fetching the most recent 10 10-K filings for {TICKER}...")
    latest_10ks = client.get_multiple_filings(filing_type='10-K', count=10)
    print(f"Retrieved {len(latest_10ks)} 10-K filings")

    statement_types = ['Income Statement', 'Balance Sheet', 'Cash Flow Statement']

    print(f"\nExtracting statement types: {statement_types}")
    print("Fetching and processing financial statements using keyword matching...")

    statements = get_statements_by_type(client, latest_10ks, statement_types)

    print(f"\n{'='*80}")
    print(f"Successfully retrieved {len(statements)} statements")
    print(f"{'='*80}\n")

    combined_balance_sheet, combined_cash_flow, combined_income_statement = combine_dataframes(statements)

    export_dataframes_to_csv(combined_balance_sheet, combined_cash_flow, combined_income_statement, TICKER)


if __name__ == "__main__":
    main()
