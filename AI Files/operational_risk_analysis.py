import pandas as pd
import numpy as np
from data_persistence import load_classification_data
from financial_statement_analysis import create_analysis_dataframes


def analyze_business_segments(op_risk_df: pd.DataFrame, segments_to_include: list = None) -> pd.DataFrame:
    """
    Analyzes and summarizes business segment data from the operational and risk DataFrame.

    Args:
        op_risk_df (pd.DataFrame): The DataFrame containing 'Operational and Risk' data.
        segments_to_include (list, optional): A list of segment names to analyze. If None, all are included.

    Returns:
        pd.DataFrame: A DataFrame summarizing revenue, income, and products for each segment.
    """
    detailed_col = 'key_metrics.Business Segments'
    simple_col = 'key_metrics.business_segment'

    if detailed_col not in op_risk_df.columns and simple_col not in op_risk_df.columns:
        print("No business segment columns found. Cannot analyze business segments.")
        return pd.DataFrame()

    # Use a set to store unique segments to avoid recounting within a single complex entry
    all_segments_list = []

    def extract_segments_from_series(series: pd.Series):
        """Helper to extract segment names from a series containing lists of strings or dicts."""
        segments = []
        # Drop rows with None, NaN, or empty lists
        series = series.dropna()
        series = series[series.apply(lambda x: isinstance(x, list) and len(x) > 0)]
        
        if not series.empty:
            exploded = series.explode()
            # Check if the first valid item is a dictionary with 'name'
            first_item = exploded.dropna().iloc[0]
            if isinstance(first_item, dict) and 'name' in first_item:
                # Handle list of dictionaries
                normalized = pd.json_normalize(exploded)
                if 'name' in normalized.columns:
                    segments.extend(normalized['name'].dropna().tolist())
            else:
                # Handle list of strings
                segments.extend(exploded.dropna().astype(str).tolist())
        return segments

    # Process both columns and aggregate the results
    if detailed_col in op_risk_df.columns:
        all_segments_list.extend(extract_segments_from_series(op_risk_df[detailed_col]))
    if simple_col in op_risk_df.columns:
        all_segments_list.extend(extract_segments_from_series(op_risk_df[simple_col]))

    if not all_segments_list:
        print("No business segment data found in either 'Business Segments' or 'business_segment' columns.")
        return pd.DataFrame()

    # Count mentions of each segment and return as a DataFrame
    summary = pd.Series(all_segments_list).value_counts().reset_index()
    summary.columns = ['Business Segment', 'Mentions']
    return summary

def analyze_competitive_landscape(op_risk_df: pd.DataFrame) -> dict:
    """
    Identifies key competitors and summarizes market positioning statements.

    Args:
        op_risk_df (pd.DataFrame): The DataFrame containing 'Operational and Risk' data.

    Returns:
        dict: A dictionary with a list of unique competitors and market position statements.
    """
    competitors_col = 'key_metrics.Competitive Landscape.Competitors'
    market_pos_col = 'key_metrics.Competitive Landscape.Market Position'
    
    results = {
        "identified_competitors": [],
        "market_position_statements": []
    }

    # Extract competitors
    if competitors_col in op_risk_df.columns:
        # Explode lists, drop nulls, get unique values
        all_competitors = op_risk_df.dropna(subset=[competitors_col])[competitors_col].explode().dropna().unique()
        results["identified_competitors"] = sorted(list(all_competitors))

    # Extract market position statements
    if market_pos_col in op_risk_df.columns:
        all_statements = op_risk_df.dropna(subset=[market_pos_col])[market_pos_col].unique()
        results["market_position_statements"] = list(all_statements)
        
    return results

def synthesize_mda(op_risk_df: pd.DataFrame) -> str:
    """
    Synthesizes a narrative from Management Discussion & Analysis sections.

    Args:
        op_risk_df (pd.DataFrame): The DataFrame containing 'Operational and Risk' data.

    Returns:
        str: A formatted string containing a summary of MD&A commentary.
    """
    perf_col = 'key_metrics.MD&A.Commentary on Performance'
    outlook_col = 'key_metrics.MD&A.Forward-looking Statements'
    
    performance_commentary = []
    if perf_col in op_risk_df.columns:
        # Create a list of (page_number, text) tuples
        perf_series = op_risk_df.dropna(subset=[perf_col])[perf_col]
        performance_commentary = list(perf_series.items())

    forward_looking = []
    if outlook_col in op_risk_df.columns:
        # Create a list of (page_number, text) tuples
        outlook_series = op_risk_df.dropna(subset=[outlook_col])[outlook_col]
        forward_looking = list(outlook_series.items())

    if not performance_commentary and not forward_looking:
        return "No MD&A commentary found."

    # Build a formatted string
    synthesis = "Management Discussion & Analysis Synthesis:\n"
    synthesis += "="*40 + "\n"

    if performance_commentary:
        synthesis += "\n--- Commentary on Performance ---\n"
        synthesis += "\n\n".join(f"• {text} (Page {page_num})" for page_num, text in performance_commentary) + "\n"

    if forward_looking:
        synthesis += "\n--- Forward-Looking Statements ---\n"
        synthesis += "\n\n".join(f"• {text} (Page {page_num})" for page_num, text in forward_looking) + "\n"

    return synthesis

def compile_key_risks(op_risk_df: pd.DataFrame) -> str:
    """
    Compiles a comprehensive list of unique risks from the operational and risk DataFrame.

    Args:
        op_risk_df (pd.DataFrame): The DataFrame containing 'Operational and Risk' data.

    Returns:
        str: A formatted string listing the unique risks.
    """
    col_name = 'key_metrics.Key Risks'
    if col_name not in op_risk_df.columns:
        return "Key risks column not found."

    # 1. Filter for rows with valid risk data and explode them, keeping the page number index
    risks_df = op_risk_df.dropna(subset=[col_name])
    risks_df = risks_df[risks_df[col_name].apply(lambda x: isinstance(x, list) and len(x) > 0)]
    exploded_risks = risks_df[col_name].explode().dropna()

    if exploded_risks.empty:
        return "No valid risks found after processing."

    # 2. Create a DataFrame of unique risks and their first-mentioned page number
    risks_with_pages = exploded_risks.reset_index().rename(columns={'index': 'page_number', col_name: 'risk'})
    unique_risks_df = risks_with_pages.drop_duplicates(subset=['risk'], keep='first').sort_values(by='risk')

    # 3. Build the formatted string with page numbers
    synthesis = "\n\n".join(f"• {row.risk} (Page {row.page_number})" for row in unique_risks_df.itertuples())
    return synthesis

def analyze_geographic_exposure(op_risk_df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyzes and summarizes the unique geographic regions of operation, ordered by mentions.

    Args:
        op_risk_df (pd.DataFrame): The DataFrame containing 'Operational and Risk' data.

    Returns:
        pd.DataFrame: A DataFrame listing the unique regions and their mention counts. **Only returns top 10**
    """
    col_name = 'key_metrics.Geographic Exposure'
    if col_name not in op_risk_df.columns:
        print(f"Column '{col_name}' not found. Cannot analyze geographic exposure.")
        return pd.DataFrame()

    # Drop rows where the geographic data is missing/null
    geo_df = op_risk_df.dropna(subset=[col_name])
    if geo_df.empty:
        print("No geographic exposure data found to analyze.")
        return pd.DataFrame()

    # The AI is returning a list of strings, not a list of dicts.
    # We can directly explode the list and use the values.
    exploded_series = geo_df[col_name].explode().dropna()

    if exploded_series.empty:
        print("No valid geographic regions found after processing.")
        return pd.DataFrame()

    # Count mentions of each region and return as a DataFrame, ordered by mentions
    summary = exploded_series.value_counts().reset_index()
    summary.columns = ['Region of Operation', 'Mentions']
    
    return summary.head(10)

def run_operational_risk_analysis(categorized_dfs: dict, print_to_console: bool = True) -> dict:
    """
    Runs a full operational and risk analysis pipeline on the provided data
    and prints the results to the console.

    Args:
        categorized_dfs (dict): A dictionary of DataFrames, keyed by category.
                                Expected to contain 'Operational and Risk'.
        print_to_console (bool): If True, prints analysis results to the console.
    
    Returns:
        dict: A dictionary containing all the analysis results.
    """
    analysis_results = {}
    if 'Operational and Risk' in categorized_dfs:
        if print_to_console:
            print("\n" + "="*50 + "\n--- Starting Operational and Risk Analysis ---\n" + "="*50)
        op_risk_df = categorized_dfs['Operational and Risk']

        # 1. Analyze Business Segments and store
        analysis_results['segment_summary'] = analyze_business_segments(op_risk_df)
        if print_to_console:
            print("\n--- Business Segment Summary ---")
            print(analysis_results['segment_summary'].to_string())

        # 2. Analyze Competitive Landscape and store
        analysis_results['competition_summary'] = analyze_competitive_landscape(op_risk_df)
        if print_to_console:
            print("\n--- Competitive Landscape ---")
            print(f"Identified Competitors: {analysis_results['competition_summary']['identified_competitors']}")
            print("\nMarket Position Statements:")
            for stmt in analysis_results['competition_summary']['market_position_statements']:
                print(f"- {stmt}")

        # 3. Synthesize MD&A and store
        analysis_results['mda_summary'] = synthesize_mda(op_risk_df)
        if print_to_console: print(f"\n{analysis_results['mda_summary']}")

        # 4. Compile Key Risks and store
        analysis_results['risks_summary'] = compile_key_risks(op_risk_df)
        if print_to_console: print(f"\n--- Key Risks Summary ---\n{analysis_results['risks_summary']}")

        # 5. Analyze Geographic Exposure and store
        analysis_results['geo_summary'] = analyze_geographic_exposure(op_risk_df)
        if print_to_console:
            print("\n--- Geographic Exposure Summary ---")
            print("(Showing top 10 most mentioned regions)")
            print(analysis_results['geo_summary'].to_string())
    else:
        print("\nNo 'Operational and Risk' data found to analyze.")
    
    return analysis_results

if __name__ == "__main__":
    try:
        # Load the processed data from the pickle file
        page_classifications, _, metadata = load_classification_data("classifications.pkl.gz")
        print("Successfully loaded classification data for analysis.")
        
        # Set pandas display options for better console output
        pd.options.display.float_format = '{:,.2f}'.format
        pd.set_option('display.max_rows', 100)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 150)
        pd.set_option('display.max_colwidth', 80)

        # Create the main and categorized DataFrames
        main_df, categorized_dfs = create_analysis_dataframes(page_classifications)

        # Run the analysis using the new function
        run_operational_risk_analysis(categorized_dfs, print_to_console=True)

    except (FileNotFoundError, Exception) as e:
        print(f"Error: Could not load or process data. {e}")
        print("Please run main.py first to generate the classification data.")