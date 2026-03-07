import io
import re
import xml.etree.ElementTree as ET

import pandas as pd
import requests

from src.services.edgar_client import EdgarClient
from src.tools.statement_keywords import STATEMENT_KEYWORDS
from src.utils.dataframe_utils import clean_dataframe_header


def find_statement_indices_by_keywords(client: EdgarClient, filing, statement_types: list) -> dict:
    """Find statement indices dynamically using keyword matching.

    Args:
        client (EdgarClient): The EDGAR client instance.
        filing: The filing object from which to find statements.
        statement_types (list): List of statement type keys
                                (e.g., ['Income Statement', 'Balance Sheet']).

    Returns:
        dict: Dictionary mapping statement types to their indices in the filing.
    """
    all_reports = filing.reports
    reports_df = all_reports.to_pandas()

    statements_df = reports_df[reports_df['MenuCategory'] == 'Statements'].copy()

    statement_indices = {}

    for statement_type in statement_types:
        if statement_type not in STATEMENT_KEYWORDS:
            print(f"Warning: No keywords defined for '{statement_type}'")
            continue

        keywords = STATEMENT_KEYWORDS[statement_type]

        for idx, row in statements_df.iterrows():
            shortname = row['ShortName'].lower()
            if any(keyword.lower() in shortname for keyword in keywords):
                statement_indices[statement_type] = idx
                break

    for statement_type in statement_types:
        if statement_type in STATEMENT_KEYWORDS and statement_type not in statement_indices:
            print(f"Nothing could be found for '{statement_type}' in filing {filing.accession_number}")

    return statement_indices


def get_excel_from_filing(client: EdgarClient, filing) -> list:
    """Retrieves the Excel file from a filing and returns a list of DataFrames per sheet.

    Args:
        client (EdgarClient): The EDGAR client instance.
        filing: The filing object from which to extract the Excel file.

    Returns:
        list: List of tuples (sheet_name, DataFrame) for each sheet in the Excel file,
              or an empty list if the file is not available.
    """
    accession_number = filing.accession_number
    cik = client.company.cik
    accession_number_no_hyphens = accession_number.replace("-", "")
    base_link = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number_no_hyphens}"
    excel_file_link = f"{base_link}/Financial_Report.xlsx"

    try:
        response = requests.get(excel_file_link, headers=client.header)
        response.raise_for_status()

        excel_file = pd.ExcelFile(io.BytesIO(response.content))

        dataframes = []
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            dataframes.append((sheet_name, df))

        return dataframes
    except requests.exceptions.HTTPError as e:
        print(
            f"Could not retrieve Excel file. It may not exist for this filing "
            f"({filing.accession_number}). HTTP Status: {e.response.status_code}"
        )
        return []


def get_statement_html_files(client: EdgarClient, filing, statement_types: list) -> dict:
    """Retrieves statement HTML file names from FilingSummary.xml.

    Args:
        client (EdgarClient): The EDGAR client instance.
        filing: The filing object.
        statement_types (list): Statement types to locate.

    Returns:
        dict: Mapping statement_type -> (short_name, html_file_name).
    """
    accession_number = filing.accession_number
    cik = client.company.cik
    accession_number_no_hyphens = accession_number.replace("-", "")
    base_link = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number_no_hyphens}"
    filing_summary_link = f"{base_link}/FilingSummary.xml"

    try:
        response = requests.get(filing_summary_link, headers=client.header)
        response.raise_for_status()
        root = ET.fromstring(response.content)
    except (requests.exceptions.RequestException, ET.ParseError) as e:
        print(f"Could not retrieve/parse FilingSummary.xml for {filing.accession_number}: {e}")
        return {}

    statement_files = {}
    for statement_type in statement_types:
        keywords = STATEMENT_KEYWORDS.get(statement_type, [])
        if not keywords:
            continue

        for report in root.findall('.//Report'):
            menu_category = report.findtext('MenuCategory', default='')
            short_name = report.findtext('ShortName', default='')
            html_file_name = report.findtext('HtmlFileName', default='')

            if menu_category == 'Statements' and html_file_name:
                if any(keyword.lower() in short_name.lower() for keyword in keywords):
                    statement_files[statement_type] = (short_name, html_file_name)
                    break

    return statement_files


def get_statements_from_html(client: EdgarClient, filing, statement_types: list) -> list:
    """Fallback statement extraction using HTML pages listed in FilingSummary.xml.

    Args:
        client (EdgarClient): The EDGAR client instance.
        filing: The filing object.
        statement_types (list): Statement types to extract.

    Returns:
        list: List of tuples (accession_number, statement_type, sheet_name, DataFrame).
    """
    accession_number = filing.accession_number
    cik = client.company.cik
    accession_number_no_hyphens = accession_number.replace("-", "")
    base_link = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number_no_hyphens}"

    statement_files = get_statement_html_files(client, filing, statement_types)
    series_of_statements = []

    for statement_type in statement_types:
        statement_info = statement_files.get(statement_type)
        if not statement_info:
            continue

        short_name, html_file_name = statement_info
        statement_link = f"{base_link}/{html_file_name}"

        try:
            response = requests.get(statement_link, headers=client.header)
            response.raise_for_status()
            tables = pd.read_html(io.StringIO(response.text))
            candidate_tables = [t for t in tables if t.shape[0] > 3 and t.shape[1] > 1]
            if not candidate_tables:
                continue

            df = max(candidate_tables, key=lambda t: (t.shape[1], t.shape[0]))
            cleaned_df = clean_dataframe_header(df)
            series_of_statements.append((accession_number, statement_type, short_name, cleaned_df))
        except (requests.exceptions.RequestException, ValueError) as e:
            print(
                f"Could not retrieve/parse HTML statement '{statement_type}' "
                f"for {filing.accession_number}: {e}"
            )

    return series_of_statements


def get_statements_by_type(client: EdgarClient, multiple_filings: list, statement_types: list) -> list:
    """Returns a list of statement DataFrames for multiple filings based on statement type keywords.

    Attempts to use the Financial_Report.xlsx Excel file first; falls back to
    HTML statement pages if the Excel file is unavailable.

    Args:
        client (EdgarClient): The EDGAR client instance.
        multiple_filings (list): List of filing objects to process.
        statement_types (list): Statement type keys to extract
                                (e.g., ['Income Statement', 'Balance Sheet']).

    Returns:
        list: List of tuples (accession_number, statement_type, sheet_name, DataFrame).
    """
    series_of_statements = []

    for filing in multiple_filings:
        statement_indices = find_statement_indices_by_keywords(client, filing, statement_types)
        excel_sheets = get_excel_from_filing(client, filing)

        if not excel_sheets:
            print(f"Falling back to FilingSummary HTML statements for filing {filing.accession_number}")
            series_of_statements.extend(get_statements_from_html(client, filing, statement_types))
            continue

        for statement_type, idx in statement_indices.items():
            if idx < len(excel_sheets):
                sheet_name, df = excel_sheets[idx]
                cleaned_df = clean_dataframe_header(df)
                series_of_statements.append((filing.accession_number, statement_type, sheet_name, cleaned_df))

    return series_of_statements


def combine_dataframes(statements: list) -> tuple:
    """Combines multiple filing DataFrames into one DataFrame per statement type.

    For overlapping years across filings, the most recent filing's values take
    precedence. Years present only in older filings are appended.

    Args:
        statements (list): List of tuples (accession_number, statement_type, sheet_name, DataFrame).

    Returns:
        tuple: (balance_sheet_df, cash_flow_df, income_statement_df), each a
               DataFrame with unique year columns sorted newest-first.
    """

    def flatten_columns(df):
        df_copy = df.copy()
        if isinstance(df_copy.columns, pd.MultiIndex):
            df_copy.columns = [
                ' '.join(map(str, col)).strip() if isinstance(col, tuple) else str(col)
                for col in df_copy.columns
            ]
        return df_copy

    def extract_year(col_name):
        col_str = str(col_name)
        match = re.search(r'\b(20\d{2})\b', col_str)
        if match:
            return match.group(1)
        return col_str

    def merge_statement_dataframes(statement_dfs):
        if not statement_dfs:
            return pd.DataFrame()

        statement_dfs.sort(key=lambda x: x[0], reverse=True)

        all_dataframes = []
        existing_years = set()

        for accession_number, _, _, df in statement_dfs:
            df_copy = flatten_columns(df).copy()

            if len(df_copy.columns) > 0:
                df_copy = df_copy.set_index(df_copy.columns[0])
                df_copy = df_copy[~df_copy.index.duplicated(keep='first')]

                year_columns = {}
                for col in df_copy.columns:
                    year = extract_year(col)
                    if year not in existing_years:
                        year_columns[col] = year
                        existing_years.add(year)

                if year_columns:
                    df_filtered = df_copy[[col for col in year_columns.keys()]].copy()
                    df_filtered.rename(columns=year_columns, inplace=True)
                    all_dataframes.append(df_filtered)

        if all_dataframes:
            result_df = pd.concat(all_dataframes, axis=1, join='outer')
            year_cols = sorted(result_df.columns, reverse=True)
            result_df = result_df[year_cols]
            return result_df

        return pd.DataFrame()

    balance_sheets = []
    cash_flows = []
    income_statements = []

    for accession_number, statement_type, sheet_name, df in statements:
        if statement_type == 'Balance Sheet':
            balance_sheets.append((accession_number, statement_type, sheet_name, df))
        elif statement_type == 'Cash Flow Statement':
            cash_flows.append((accession_number, statement_type, sheet_name, df))
        elif statement_type == 'Income Statement':
            income_statements.append((accession_number, statement_type, sheet_name, df))

    balance_sheet_df = merge_statement_dataframes(balance_sheets)
    cash_flow_df = merge_statement_dataframes(cash_flows)
    income_statement_df = merge_statement_dataframes(income_statements)

    return balance_sheet_df, cash_flow_df, income_statement_df
