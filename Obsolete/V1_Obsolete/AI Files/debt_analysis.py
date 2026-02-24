import pandas as pd
from typing import Any

def _format_covenant_text(text: Any) -> str:
    """
    Formats covenant text, handling strings, lists of strings, and lists of dictionaries.
    """
    # Case 1: The text is a list.
    if isinstance(text, list) and text:
        # Subcase 1a: List of dictionaries (extract keys).
        if isinstance(text[0], dict):
            covenant_dict = text[0]
            covenant_names = list(covenant_dict.keys())
            return ", ".join(covenant_names)
        # Subcase 1b: List of strings.
        elif isinstance(text[0], str):
            return ", ".join(text)
    
    # Case 2: The text is already a simple, well-formatted string.
    if isinstance(text, str):
        return text
        
    # Fallback for any other unexpected format.
    return str(text)

def summarize_covenants(debt_df: pd.DataFrame) -> str:
    """
    Summarizes debt covenants from the 'Debt and Loans' DataFrame.

    Args:
        debt_df (pd.DataFrame): The DataFrame containing 'Debt and Loans' data.

    Returns:
        str: A formatted string containing covenant commentary.
    """
    col_name = 'key_metrics.Covenants'
    if col_name not in debt_df.columns:
        return "Covenants column not found."

    # Get all non-null, non-empty covenant statements
    covenant_series = debt_df.dropna(subset=[col_name])[col_name]
    covenant_commentary = list(covenant_series.items())

    if not covenant_commentary:
        return "No debt covenant commentary found."

    synthesis = "\n\n".join(
        f"• {_format_covenant_text(text)} (Page {page_num})" for page_num, text in covenant_commentary
    )
    return synthesis

def analyze_capital_structure(debt_df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyzes the capital structure (debt and equity) from the 'Debt and Loans' DataFrame.

    Args:
        debt_df (pd.DataFrame): The DataFrame containing 'Debt and Loans' data.

    Returns:
        pd.DataFrame: A DataFrame summarizing total debt and equity.
    """
    debt_col = 'key_metrics.Capital Structure.Total Debt'
    equity_col = 'key_metrics.Capital Structure.Total Equity'

    if debt_col not in debt_df.columns and equity_col not in debt_df.columns:
        print("Capital Structure columns not found.")
        return pd.DataFrame()

    # Select relevant columns and drop rows where all are null
    cap_structure_df = debt_df[[debt_col, equity_col]].dropna(how='all')
    cap_structure_df.index.name = 'page_number'

    return cap_structure_df.reset_index()

def run_debt_analysis(categorized_dfs: dict, print_to_console: bool = True) -> dict:
    """
    Runs a full debt and capital structure analysis and prints the results.

    Args:
        categorized_dfs (dict): A dictionary of DataFrames, keyed by category.
                                Expected to contain 'Debt and Loans'.
        print_to_console (bool): If True, prints analysis results to the console.
    Returns:
        dict: A dictionary containing the analysis results.
    """
    analysis_results = {}
    if 'Debt and Loans' in categorized_dfs:
        if print_to_console:
            print("\n" + "="*50 + "\n--- Starting Debt and Capital Structure Analysis ---\n" + "="*50)
        debt_df = categorized_dfs['Debt and Loans']

        analysis_results['covenants'] = summarize_covenants(debt_df)
        if print_to_console: print(f"\n--- Debt Covenants ---\n{analysis_results['covenants']}")

        analysis_results['capital_structure'] = analyze_capital_structure(debt_df)
        if print_to_console:
            print("\n--- Capital Structure Summary ---")
            print(analysis_results['capital_structure'].to_string(na_rep=''))
    else:
        print("\nNo 'Debt and Loans' data found to analyze.")
    
    return analysis_results

if __name__ == "__main__":
    # This allows the script to be run directly to inspect the data
    try:
        from data_persistence import load_classification_data
        from financial_statement_analysis import create_analysis_dataframes

        page_classifications, _, _ = load_classification_data("classifications.pkl.gz")
        print("Successfully loaded classification data for debt analysis.")

        # Set pandas display options for better console output
        pd.options.display.float_format = '{:,.2f}'.format
        pd.set_option('display.max_rows', 100)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 150)
        pd.set_option('display.max_colwidth', 80)

        # Create the categorized DataFrames
        _, categorized_dfs = create_analysis_dataframes(page_classifications)

        # Run the debt analysis
        if categorized_dfs is not None:
            run_debt_analysis(categorized_dfs, print_to_console=True)
        else:
            print("Error: Failed to create categorized DataFrames.")

    except (FileNotFoundError, Exception) as e:
        print(f"Error: Could not load or process data. {e}")
        print("Please run main.py first to generate the classification data.")