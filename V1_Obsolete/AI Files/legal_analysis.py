import pandas as pd
import json
from typing import Any

def _format_item_as_string(item: Any) -> str:
    """
    Recursively formats an item (string, dict, list) into a readable string.
    - Dictionaries are formatted as "Key: Value".
    - Lists are joined with commas.
    - Other types are converted to a simple string.
    """
    if isinstance(item, dict):
        # Format dictionary into a readable "Key: Value" string
        parts = []
        for key, value in item.items():
            # Recursively format the value in case it's also a dict or list
            formatted_value = _format_item_as_string(value)
            parts.append(f"{key}: {formatted_value}")
        return "; ".join(parts)
    elif isinstance(item, list):
        return ", ".join(_format_item_as_string(i) for i in item)
    return str(item)

def analyze_litigation(legal_df: pd.DataFrame) -> str:
    """
    Analyzes and summarizes litigation cases from the legal DataFrame.

    Args:
        legal_df (pd.DataFrame): The DataFrame containing 'Legal' data.

    Returns:
        str: A formatted string summarizing litigation cases and their potential impacts.
    """
    col_name = 'key_metrics.Litigation'
    if col_name not in legal_df.columns:
        return "Litigation data column not found."

    # Filter for rows with valid litigation data (non-empty lists)
    litigation_series = legal_df.dropna(subset=[col_name])
    litigation_series = litigation_series[col_name][litigation_series[col_name].apply(lambda x: isinstance(x, list) and len(x) > 0)]

    if litigation_series.empty:
        return "No litigation data found to analyze."

    all_cases = []
    # The index of the series is the page number
    for page_num, cases_on_page in litigation_series.items():
        for case_info in cases_on_page:
            if isinstance(case_info, dict):
                case = case_info.get('case', 'N/A')
                impact = case_info.get('impact', 'Not specified')
                all_cases.append({'case': case, 'impact': impact, 'page_number': page_num})

    if not all_cases:
        return "No valid litigation cases found after processing."

    # Create a DataFrame to handle duplicates and format output
    cases_df = pd.DataFrame(all_cases).drop_duplicates(subset=['case', 'impact']).sort_values(by='page_number')

    synthesis = "\n\n".join(
        f"• Case: {row.case}\n  Impact: {row.impact} (Page {row.page_number})"
        for row in cases_df.itertuples()
    )
    return synthesis

def analyze_regulatory_matters(legal_df: pd.DataFrame) -> str:
    """
    Compiles a list of unique regulatory matters from the legal DataFrame.

    Args:
        legal_df (pd.DataFrame): The DataFrame containing 'Legal' data.

    Returns:
        str: A formatted string listing unique regulatory matters.
    """
    col_name = 'key_metrics.Regulatory Matters'
    if col_name not in legal_df.columns:
        return "Regulatory Matters column not found."

    # 1. Filter for rows with valid data, explode them, and keep the page number index
    matters_df = legal_df.dropna(subset=[col_name])
    matters_df = matters_df[matters_df[col_name].apply(lambda x: isinstance(x, list) and len(x) > 0)]
    exploded_matters = matters_df[col_name].explode().dropna()

    if exploded_matters.empty:
        return "No regulatory matters found."

    # 2. Create a DataFrame of unique matters and their first-mentioned page number
    # The AI returns strings for this field, so we can use them directly.
    matters_with_pages = exploded_matters.reset_index().rename(columns={'index': 'page_number', col_name: 'matter'})

    # Convert 'matter' column to string to prevent sorting errors if it contains dicts
    # and create a clean version for display
    matters_with_pages['matter_str'] = matters_with_pages['matter'].apply(_format_item_as_string)
    unique_matters_df = matters_with_pages.drop_duplicates(subset=['matter_str'], keep='first').sort_values(by='matter_str')
    
    # 3. Build the formatted string with page numbers
    synthesis = "\n\n".join(f"• {row.matter_str} (Page {row.page_number})" for row in unique_matters_df.itertuples())
    return synthesis

def summarize_corporate_governance(legal_df: pd.DataFrame) -> str:
    """
    Summarizes corporate governance commentary from the legal DataFrame.

    Args:
        legal_df (pd.DataFrame): The DataFrame containing 'Legal' data.

    Returns:
        str: A formatted string containing corporate governance commentary.
    """
    col_name = 'key_metrics.Corporate Governance'
    if col_name not in legal_df.columns:
        return "Corporate Governance column not found."

    # Get all non-null, non-empty governance statements
    governance_series = legal_df.dropna(subset=[col_name])[col_name]
    # The index is the page number
    governance_commentary = list(governance_series.items())

    if not governance_commentary:
        return "No corporate governance commentary found."

    synthesis = "\n\n".join(
        f"• {_format_item_as_string(text)} (Page {page_num})" for page_num, text in governance_commentary
    )
    return synthesis

def run_legal_analysis(categorized_dfs: dict, print_to_console: bool = True) -> dict:
    """
    Runs a full legal analysis pipeline on the provided data
    and prints the results to the console.

    Args:
        categorized_dfs (dict): A dictionary of DataFrames, keyed by category.
                                Expected to contain 'Legal'.
        print_to_console (bool): If True, prints analysis results to the console.
    Returns:
        dict: A dictionary containing the analysis results.
    """
    analysis_results = {}
    if 'Legal' in categorized_dfs:
        if print_to_console:
            print("\n" + "="*50 + "\n--- Starting Legal Analysis ---\n" + "="*50)
        legal_df = categorized_dfs['Legal']

        analysis_results['litigation_summary'] = analyze_litigation(legal_df)
        if print_to_console: print(f"\n--- Litigation Summary ---\n{analysis_results['litigation_summary']}")

        analysis_results['regulatory_summary'] = analyze_regulatory_matters(legal_df)
        if print_to_console: print(f"\n--- Regulatory Matters Summary ---\n{analysis_results['regulatory_summary']}")

        analysis_results['governance_summary'] = summarize_corporate_governance(legal_df)
        if print_to_console: print(f"\n--- Corporate Governance Commentary ---\n{analysis_results['governance_summary']}")
    else:
        print("\nNo 'Legal' data found to analyze.")
    
    return analysis_results

if __name__ == "__main__":
    try:
        from data_persistence import load_classification_data
        from financial_statement_analysis import create_analysis_dataframes

        page_classifications, _, _ = load_classification_data("classifications.pkl.gz")
        print("Successfully loaded classification data for analysis.")

        pd.set_option('display.max_rows', 100)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 150)
        pd.set_option('display.max_colwidth', 80)

        _, categorized_dfs = create_analysis_dataframes(page_classifications)

        # Run the full analysis
        if categorized_dfs is not None:
            run_legal_analysis(categorized_dfs, print_to_console=True)
        else:
            print("Error: categorized_dfs is None, cannot run legal analysis.")

    except (FileNotFoundError, Exception) as e:
        print(f"Error: Could not load or process data. {e}")
        print("Please run main.py first to generate the classification data.")
