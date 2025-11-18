import pandas as pd
from data_persistence import load_classification_data
import pprint
import os
import numpy as np
from typing import Optional

def create_analysis_dataframes(page_classifications: dict):
    """
    Creates Pandas DataFrames for analysis from loaded classification data.

    Args:
        page_classifications (dict): The dictionary of structured page data.

    Returns:
        tuple: A tuple containing:
            - pd.DataFrame: The main DataFrame with all classified pages.
            - dict: A dictionary of DataFrames, keyed by category.
    """
    if not page_classifications:
        print("No classification data provided to create DataFrames.")
        return None, None

    # Convert the dictionary of pages into a list of records
    records = list(page_classifications.values())

    # Use json_normalize to flatten the nested key_metrics structure
    # This creates columns like 'key_metrics.Income Statement.Net Sales'
    df = pd.json_normalize(records, sep='.')

    # Set the page_number as the index for easier lookup
    df = df.set_index('page_number')
    df.sort_index(inplace=True)

    print("\nCreated main DataFrame. Info:")
    df.info()
    
    print("\nCategory distribution in DataFrame:")
    print(df['category'].value_counts())

    # Create separate DataFrames for each category
    category_dfs = {}
    for category in df['category'].unique():
        category_dfs[category] = df[df['category'] == category].copy()
        print(f"\nCreated DataFrame for '{category}' with {len(category_dfs[category])} pages.")

    return df, category_dfs

# Helper function for unit conversion
def _convert_value_with_unit(value, unit):
    """Converts a value based on its unit (e.g., 'million', 'billion')."""
    if value is None:
        return None
    
    # Try to convert value to float if it's not already numeric
    if not isinstance(value, (int, float)):
        try:
            # Remove commas and currency symbols before converting to float
            if isinstance(value, str):
                value = value.replace(',', '').replace('$', '').strip()
            value = float(value)
        except (ValueError, TypeError):
            return None # Return None if conversion fails

    unit = str(unit).lower()
    if 'million' in unit:
        return value * 1_000_000
    elif 'billion' in unit:
        return value * 1_000_000_000
    elif 'thousand' in unit:
        return value * 1_000
    # Add more unit conversions as needed (e.g., percentage, currency symbols)
    return value

def reconstruct_financial_statements(page_classifications: dict, segments_to_include: Optional[list] = None) -> dict:
    """
    Reconstructs simplified Income Statements, Balance Sheets, and Cash Flow Statements
    from the extracted financial data.

    Args:
        page_classifications (dict): The dictionary of structured page data.
        segments_to_include (list, optional): A list of segment names to include. If None, all segments are used.

    Returns:
        dict: A dictionary where keys are statement types (e.g., 'Income Statement')
              and values are Pandas DataFrames representing the reconstructed statements.
              Each DataFrame will have 'item' as index, and a MultiIndex of ('year', 'segment') as columns.
    """
    financial_data_points = []

    for page_idx, classification in page_classifications.items():
        if classification['category'] == 'Financial Statement':
            key_metrics = classification['key_metrics']
            # The 'business_segment' from the first AI call is stored directly in key_metrics
            # The detailed extraction also includes 'segment' per item. Prioritize item's segment.
            page_segment_list = key_metrics.get('business_segment')
            # page_number = classification.get('page_number', page_idx + 1) # Get page number
            if page_segment_list and isinstance(page_segment_list, list) and len(page_segment_list) > 0:
                page_segment_default = page_segment_list[0] # Take the first segment if multiple
            else:
                page_segment_default = 'Consolidated' # Fallback if list is empty or empty

            for statement_type in ["Income Statement", "Balance Sheet", "Cash Flow"]:
                if statement_type in key_metrics:
                    statement_items = key_metrics[statement_type]
                    for item_name, item_data_list in statement_items.items():
                        if isinstance(item_data_list, list):
                            for item_data in item_data_list:
                                if isinstance(item_data, dict):
                                    value = item_data.get('value')
                                    unit = item_data.get('unit', '')
                                    year = item_data.get('year')
                                    # Use item's segment if present, else page's default
                                    segment = item_data.get('segment', page_segment_default) 

                                    converted_value = _convert_value_with_unit(value, unit)
                                    
                                    if converted_value is not None and year is not None:
                                        financial_data_points.append({
                                            'statement_type': statement_type,
                                            'item': item_name,
                                            'value': converted_value,
                                            'year': int(year), # Ensure year is integer
                                            'segment': segment
                                        })
    
    if not financial_data_points:
        print("No financial statement data points found.")
        return {}

    df_all_financials = pd.DataFrame(financial_data_points)

    # Filter by selected segments if provided
    if segments_to_include:
        print(f"Reconstructing financial statements for segments: {segments_to_include}")
        df_all_financials = df_all_financials[df_all_financials['segment'].isin(segments_to_include)]

    
    reconstructed_statements = {}
    for statement_type in df_all_financials['statement_type'].unique():
        df_statement = df_all_financials[df_all_financials['statement_type'] == statement_type].copy()
        
        # Pivot to get items as rows, and years/segments as columns
        # If multiple values exist for the same item/year/segment, take the first one.
        # This assumes that the AI extraction is generally consistent or that the first entry is sufficient.
        df_pivot = df_statement.pivot_table(
            index=['item'], 
            columns=['year', 'segment'], 
            values='value', 
            aggfunc='first' 
        )
        
        # Sort columns by year then segment for consistent ordering
        df_pivot = df_pivot.sort_index(axis=1, level=['year', 'segment'])
        
        reconstructed_statements[statement_type] = df_pivot
        
    return reconstructed_statements

def calculate_financial_ratios(reconstructed_statements: dict, segments_to_include: Optional[list] = None) -> dict:
    """
    Calculates key financial ratios from reconstructed financial statements.

    Args:
        reconstructed_statements (dict): Dictionary of reconstructed financial statements
                                         (DataFrames for Income Statement, Balance Sheet, Cash Flow).

        segments_to_include (list, optional): A list of segment names to include. If None, all segments are used.
    Returns:
        dict: A dictionary where keys are ratio categories (e.g., 'Profitability')
              and values are DataFrames of calculated ratios, indexed by (year, segment).
    """
    ratios = {}
    
    inc_stmt = reconstructed_statements.get("Income Statement")
    bal_sheet = reconstructed_statements.get("Balance Sheet")
    cash_flow = reconstructed_statements.get("Cash Flow")

    if inc_stmt is None or bal_sheet is None:
        print("Income Statement or Balance Sheet not available for ratio analysis.")
        return ratios

    # Filter by selected segments if provided
    if segments_to_include:
        print(f"Filtering ratio analysis for segments: {segments_to_include}")
        if inc_stmt is not None:
            inc_stmt = inc_stmt.loc[:, pd.IndexSlice[:, segments_to_include]]
        if bal_sheet is not None:
            bal_sheet = bal_sheet.loc[:, pd.IndexSlice[:, segments_to_include]]
        if cash_flow is not None:
            cash_flow = cash_flow.loc[:, pd.IndexSlice[:, segments_to_include]]

    if inc_stmt is None or bal_sheet is None or inc_stmt.empty or bal_sheet.empty:
        print("Income Statement or Balance Sheet not available or empty after segment filtering.")
        return {}

    # Align columns (years, segments) across statements
    common_cols = inc_stmt.columns.intersection(bal_sheet.columns)
    if cash_flow is not None:
        common_cols = common_cols.intersection(cash_flow.columns)
    
    if common_cols.empty:
        print("No common years/segments found across financial statements for ratio analysis.")
        return ratios

    ratio_records = []

    for year, segment in common_cols:
        # Helper to safely get a value from a statement for a specific year/segment
        def get_value(statement_df, item_name, year_col, segment_col):
            if item_name in statement_df.index and (year_col, segment_col) in statement_df.columns:
                return statement_df.loc[item_name, (year_col, segment_col)]
            return np.nan

        # Income Statement items
        net_sales = get_value(inc_stmt, 'Net Sales', year, segment)
        cogs = get_value(inc_stmt, 'Cost of Goods Sold', year, segment)
        gross_profit = get_value(inc_stmt, 'Gross Profit', year, segment)
        operating_income = get_value(inc_stmt, 'Operating Income', year, segment)
        net_income = get_value(inc_stmt, 'Net Income', year, segment)
        interest_expense = get_value(inc_stmt, 'Interest Expense', year, segment)

        # Balance Sheet items
        cash_equiv = get_value(bal_sheet, 'Cash and Cash Equivalents', year, segment)
        accounts_receivable = get_value(bal_sheet, 'Accounts Receivable', year, segment)
        inventory = get_value(bal_sheet, 'Inventory', year, segment)
        total_current_assets = get_value(bal_sheet, 'Total Current Assets', year, segment)
        total_current_liabilities = get_value(bal_sheet, 'Total Current Liabilities', year, segment)
        total_assets = get_value(bal_sheet, 'Total Assets', year, segment)
        total_liabilities = get_value(bal_sheet, 'Total Liabilities', year, segment)
        total_shareholders_equity = get_value(bal_sheet, "Total Shareholders' Equity", year, segment)

        # --- Profitability Ratios ---
        gross_margin = (gross_profit / net_sales) if net_sales != 0 and not pd.isna(gross_profit) else np.nan
        operating_margin = (operating_income / net_sales) if net_sales != 0 and not pd.isna(operating_income) else np.nan
        net_profit_margin = (net_income / net_sales) if net_sales != 0 and not pd.isna(net_income) else np.nan
        # ROA: Net Income / Total Assets (using current year's total assets for simplicity)
        roa = (net_income / total_assets) if total_assets != 0 and not pd.isna(net_income) else np.nan
        # ROE: Net Income / Total Shareholders' Equity (using current year's equity for simplicity)
        roe = (net_income / total_shareholders_equity) if total_shareholders_equity != 0 and not pd.isna(net_income) else np.nan

        # --- Liquidity Ratios ---
        current_ratio = (total_current_assets / total_current_liabilities) if total_current_liabilities != 0 and not pd.isna(total_current_assets) else np.nan
        quick_ratio = ((total_current_assets - inventory) / total_current_liabilities) if total_current_liabilities != 0 and not pd.isna(total_current_assets) and not pd.isna(inventory) else np.nan

        # --- Solvency Ratios ---
        debt_to_equity = (total_liabilities / total_shareholders_equity) if total_shareholders_equity != 0 and not pd.isna(total_liabilities) else np.nan
        debt_to_asset = (total_liabilities / total_assets) if total_assets != 0 and not pd.isna(total_liabilities) else np.nan
        # Interest Coverage Ratio: Operating Income / Interest Expense. Assuming Operating Income is a proxy for EBIT.
        interest_coverage = (operating_income / interest_expense) if interest_expense != 0 and not pd.isna(operating_income) else np.nan

        # --- Efficiency Ratios ---
        # Inventory Turnover: COGS / Inventory (using current year's inventory for simplicity)
        inventory_turnover = (cogs / inventory) if inventory != 0 and not pd.isna(cogs) and not pd.isna(inventory) else np.nan
        # Accounts Receivable Turnover: Net Sales / Accounts Receivable (using current year's AR for simplicity)
        ar_turnover = (net_sales / accounts_receivable) if accounts_receivable != 0 and not pd.isna(net_sales) else np.nan
        # Asset Turnover: Net Sales / Total Assets (using current year's total assets for simplicity)
        asset_turnover = (net_sales / total_assets) if total_assets != 0 and not pd.isna(net_sales) else np.nan

        ratio_records.append({
            'year': year,
            'segment': segment,
            'Gross Margin': gross_margin,
            'Operating Margin': operating_margin,
            'Net Profit Margin': net_profit_margin,
            'ROA': roa,
            'ROE': roe,
            'Current Ratio': current_ratio,
            'Quick Ratio': quick_ratio,
            'Debt-to-Equity Ratio': debt_to_equity,
            'Debt-to-Asset Ratio': debt_to_asset,
            'Interest Coverage Ratio': interest_coverage,
            'Inventory Turnover': inventory_turnover,
            'Accounts Receivable Turnover': ar_turnover,
            'Asset Turnover': asset_turnover
        })
    
    if not ratio_records:
        return {}

    df_ratios = pd.DataFrame(ratio_records).set_index(['year', 'segment']).sort_index()

    # Group ratios by category
    ratios['Profitability'] = df_ratios[['Gross Margin', 'Operating Margin', 'Net Profit Margin', 'ROA', 'ROE']]
    ratios['Liquidity'] = df_ratios[['Current Ratio', 'Quick Ratio']]
    ratios['Solvency'] = df_ratios[['Debt-to-Equity Ratio', 'Debt-to-Asset Ratio', 'Interest Coverage Ratio']]
    ratios['Efficiency'] = df_ratios[['Inventory Turnover', 'Accounts Receivable Turnover', 'Asset Turnover']]

    return ratios

def perform_trend_analysis(data_df: pd.DataFrame, name: str = "Financial Item", periods: int = 1) -> dict:
    """
    Performs trend analysis on financial data or ratios over reported periods.

    Args:
        data_df (pd.DataFrame): A DataFrame with a MultiIndex (year, segment) and numeric columns.
                                Can be a reconstructed statement or a ratios DataFrame.
        name (str): A descriptive name for the data being analyzed (e.g., "Net Sales", "Profitability Ratios").
        periods (int): The number of periods to look back for percentage change calculation.

    Returns:
        dict: A dictionary containing DataFrames for absolute change and percentage change.
    """
    if data_df.empty:
        print(f"No data provided for trend analysis of {name}.")
        return {}

    # Ensure the DataFrame is sorted by year and segment for correct shifting
    data_df_sorted = data_df.sort_index(level=['year', 'segment'])

    trend_results = {}

    # Calculate absolute change (difference from previous period)
    # Group by segment to calculate change within each segment
    absolute_change = data_df_sorted.groupby(level='segment').diff(periods=periods)
    trend_results['Absolute Change'] = absolute_change.rename(columns=lambda x: f"{x} (Abs Change)")

    # Calculate percentage change
    percentage_change = data_df_sorted.groupby(level='segment').pct_change(periods=periods, fill_method=None) * 100
    trend_results['Percentage Change'] = percentage_change.rename(columns=lambda x: f"{x} (Pct Change %)")

    print(f"\nTrend analysis for {name} complete.")
    return trend_results

def perform_cash_flow_analysis(reconstructed_statements: dict, segments_to_include: Optional[list] = None) -> pd.DataFrame:
    """
    Analyzes the company's sources and uses of cash from the Cash Flow Statement.

    Args:
        reconstructed_statements (dict): Dictionary of reconstructed financial statements.
        segments_to_include (list, optional): A list of segment names to include. If None, all segments are used.

    Returns:
        pd.DataFrame: A DataFrame summarizing cash flow activities, indexed by (year, segment).
    """
    if "Cash Flow" not in reconstructed_statements:
        print("Cash Flow Statement not available for analysis.")
        return pd.DataFrame()

    cash_flow_stmt = reconstructed_statements["Cash Flow"]

    if segments_to_include:
        print(f"Filtering cash flow analysis for segments: {segments_to_include}")
        cash_flow_stmt = cash_flow_stmt.loc[:, pd.IndexSlice[:, segments_to_include]]
    
    if cash_flow_stmt.empty:
        print("Cash Flow statement is empty after segment filtering.")
        return pd.DataFrame()

    # Select key cash flow items
    cash_flow_items = [
        "Net Cash from Operating Activities",
        "Net Cash from Investing Activities",
        "Net Cash from Financing Activities"
    ]
    
    # Filter for available items and transpose for easier analysis
    available_cf_items = cash_flow_stmt.index.intersection(cash_flow_items)
    if available_cf_items.empty:
        print("No relevant cash flow items found for analysis.")
        return pd.DataFrame()

    df_cash_flow_summary = cash_flow_stmt.loc[available_cf_items].transpose()
    df_cash_flow_summary.index.names = ['year', 'segment']
    
    # Calculate Net Change in Cash (if all three components are present)
    if all(item in df_cash_flow_summary.columns for item in cash_flow_items):
        df_cash_flow_summary['Net Change in Cash'] = df_cash_flow_summary[cash_flow_items].sum(axis=1)

    print("\nCash Flow Analysis complete.")
    return df_cash_flow_summary

def print_financial_statements(reconstructed_statements: dict, print_to_console: bool = True):
    """Prints the reconstructed financial statements to the console."""
    if print_to_console:
        if reconstructed_statements:
            print("\n--- Reconstructed Financial Statements ---")
            for stmt_type, df_stmt in reconstructed_statements.items():
                print(f"\nStatement Type: {stmt_type}")
                if not df_stmt.empty:
                    print(df_stmt.to_string())
                else:
                    print("  (No data available for this statement)")
        else:
            print("\nNo financial statements could be reconstructed.")

def print_financial_ratios(financial_ratios: dict, print_to_console: bool = True):
    """Prints the calculated financial ratios to the console."""
    if print_to_console:
        if financial_ratios:
            print("\n--- Calculated Financial Ratios ---")
            for ratio_type, df_ratios in financial_ratios.items():
                print(f"\nRatio Category: {ratio_type}")
                print(df_ratios.to_string())
        else:
            print("\nNo financial ratios could be calculated.")

def print_trend_analysis(trend_results: dict, analysis_name: str, print_to_console: bool = True):
    """Prints the trend analysis results to the console."""
    if print_to_console:
        if trend_results:
            print(f"\n--- Trend Analysis for {analysis_name} ---")
            for trend_type, df_trend in trend_results.items():
                print(f"\n{trend_type} for {analysis_name}:")
                if not df_trend.empty:
                    print(df_trend.to_string())
                else:
                    print("  (No trend data available)")

def print_cash_flow_summary(cash_flow_df: pd.DataFrame, print_to_console: bool = True):
    """Prints the cash flow analysis summary to the console."""
    if print_to_console:
        if not cash_flow_df.empty:
            print("\n--- Cash Flow Analysis Summary ---")
            print(cash_flow_df.to_string())
        else:
            print("\nNo cash flow analysis performed.")

def run_financial_statement_analysis(page_classifications: dict, target_segments: Optional[list] = None, print_to_console: bool = True) -> dict:
    """
    Runs a full financial analysis pipeline and prints the results to the console.

    This includes:
    - Reconstructing financial statements.
    - Calculating key financial ratios.
    - Performing trend analysis on key metrics.
    - Analyzing cash flow.

    Args:
        page_classifications (dict): The dictionary of structured page data.
        target_segments (list, optional): A list of segment names to analyze. Defaults to ['Consolidated'].
        print_to_console (bool): If True, prints analysis results to the console.

    Returns:
        dict: A dictionary containing all the analysis results (statements, ratios, trends, etc.).
    """
    # --- Analysis Configuration ---
    if target_segments is None:
        target_segments = ['Consolidated']  # Default behavior if not specified
    if print_to_console:
        print(f"\nRunning financial analysis for segments: {target_segments}")

    # --- Financial Analysis Section ---
    if print_to_console:
        print("\n" + "="*50 + "\n--- Starting Financial Analysis ---\n" + "="*50)

    analysis_results = {}

    reconstructed_statements = reconstruct_financial_statements(page_classifications, segments_to_include=target_segments)
    analysis_results['reconstructed_statements'] = reconstructed_statements
    print_financial_statements(reconstructed_statements, print_to_console=print_to_console)

    financial_ratios = calculate_financial_ratios(reconstructed_statements, segments_to_include=target_segments)
    analysis_results['financial_ratios'] = financial_ratios
    print_financial_ratios(financial_ratios, print_to_console=print_to_console)

    # Trend Analysis
    analysis_results['trends'] = {}
    if "Income Statement" in reconstructed_statements:
        # Transpose and set MultiIndex for trend analysis function compatibility
        net_sales_df = reconstructed_statements["Income Statement"].loc[['Net Sales']].transpose()
        net_sales_df.index.names = ['year', 'segment']
        # Filter for target segments before analysis
        net_sales_df = net_sales_df[net_sales_df.index.get_level_values('segment').isin(target_segments)]
        analysis_results['trends']['Net Sales'] = perform_trend_analysis(net_sales_df, name="Net Sales")
        print_trend_analysis(analysis_results['trends']['Net Sales'], "Net Sales", print_to_console=print_to_console)

    if "Balance Sheet" in reconstructed_statements:
        # Transpose and set MultiIndex for trend analysis function compatibility
        total_assets_df = reconstructed_statements["Balance Sheet"].loc[['Total Assets']].transpose()
        total_assets_df.index.names = ['year', 'segment']
        # Filter for target segments before analysis
        total_assets_df = total_assets_df[total_assets_df.index.get_level_values('segment').isin(target_segments)]
        analysis_results['trends']['Total Assets'] = perform_trend_analysis(total_assets_df, name="Total Assets")
        print_trend_analysis(analysis_results['trends']['Total Assets'], "Total Assets", print_to_console=print_to_console)

    if financial_ratios and "Profitability" in financial_ratios:
        analysis_results['trends']['Profitability Ratios'] = perform_trend_analysis(financial_ratios["Profitability"], name="Profitability Ratios")
        print_trend_analysis(analysis_results['trends']['Profitability Ratios'], "Profitability Ratios", print_to_console=print_to_console)

    # Cash Flow Analysis
    cash_flow_summary_df = perform_cash_flow_analysis(reconstructed_statements, segments_to_include=target_segments)
    analysis_results['cash_flow_summary'] = cash_flow_summary_df
    print_cash_flow_summary(cash_flow_summary_df, print_to_console=print_to_console)

    return analysis_results


if __name__ == "__main__":
    # This allows the script to be run directly to inspect the data
    try:
        page_classifications, raw_responses, metadata = load_classification_data("classifications.pkl.gz")
        print("Successfully loaded classification data.")
        print("---" * 10)
        print("Metadata from processing run:")
        print(f"  Timestamp: {metadata.get('timestamp')}")
        print(f"  Total Pages: {metadata.get('total_pages')}")
        print("  Category Counts:", metadata.get('categories', {}))
        print("---" * 10)
        
        # --- Set Display Options for Better Readability ---
        # Format floats to 2 decimal places for ratios, and with commas for large numbers
        pd.options.display.float_format = '{:,.2f}'.format
        print("Set pandas float display format for better readability.")

        # --- Analysis Configuration ---
        # Specify which business segments to include in the financial analysis.
        FINANCIAL_ANALYSIS_SEGMENTS = ['Consolidated']

        # Run the full analysis using the new function
        run_financial_statement_analysis(page_classifications, target_segments=FINANCIAL_ANALYSIS_SEGMENTS, print_to_console=True)

    except (FileNotFoundError, Exception) as e:
        print(f"Error: Could not load or process data. {e}")
        print("Please run main.py first to generate the classification data.")
        main_df = None # Ensure main_df is None on error
        page_classifications = None

    
