import os
import pandas as pd


def export_dataframes_to_csv(
    balance_sheet_df: pd.DataFrame,
    cash_flow_df: pd.DataFrame,
    income_statement_df: pd.DataFrame,
    ticker: str,
    output_dir: str = "outputs",
) -> list:
    """
    Export financial statements to CSV files in the specified output directory.

    Args:
        balance_sheet_df: DataFrame for the balance sheet.
        cash_flow_df: DataFrame for the cash flow statement.
        income_statement_df: DataFrame for the income statement.
        ticker (str): Stock ticker symbol.
        output_dir (str): Path to output directory, resolved relative to the
                          project root (default: 'outputs').

    Returns:
        list: List of file paths that were created.
    """
    # Resolve output_dir relative to the project root (two levels up from this file:
    # src/utils/ -> src/ -> project root)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_path = os.path.join(project_root, output_dir)

    os.makedirs(output_path, exist_ok=True)

    created_files = []

    statements_dict = {
        'Balance_Sheet': balance_sheet_df,
        'Cash_Flow_Statement': cash_flow_df,
        'Income_Statement': income_statement_df,
    }

    for statement_name, df in statements_dict.items():
        if not df.empty:
            filename = f"{ticker}_{statement_name}.csv"
            filepath = os.path.join(output_path, filename)
            df.to_csv(filepath, index=True)
            created_files.append(filepath)
            print(f"Exported: {filename}")

    print(f"\nAll {len(created_files)} files exported to: {output_path}")
    return created_files
