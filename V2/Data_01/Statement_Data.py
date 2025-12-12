import edgar
import pandas as pd
import requests
import io

class EdgarCompany:
    """
    A client to interact with the SEC EDGAR database for a specific company.
    Handles initialization and retrieval of filings and item parts.
    """
    def __init__(self, email: str, ticker: str):
        """Initializes the EdgarCompany client.

        This sets the user identity required for making requests to the
        SEC EDGAR database and then creates a Company object for the given stock ticker.

        Args:
            email (str): The email address to use as the user agent for SEC requests.
                         This is required by the SEC to identify the user/application.
            ticker (str): The stock ticker symbol for the desired company.
        """
        edgar.set_identity(email)
        self.header = {'User-Agent': email}
        self.company = edgar.Company(ticker)
        self.ticker = ticker

    def get_filing(self, filing_type: str, index: int):
        """Retrieves a specific filing for the company.

        This method fetches all filings of a specified type for the company and
        then returns a single filing based on the provided index.

        Args:
            filing_type (str): The form type of the filing to retrieve (e.g., '10-K', '10-Q').
            index (int): The index of the filing to return. 0 is the most recent,
                         1 is the second most recent, and so on.

        Returns:
            A single filing object corresponding to the specified type and index.
            The specific type is `edgar.Filing`.
        """
        filings = self.company.get_filings(form=filing_type)
        indexed_filing = filings[index]
        return indexed_filing
    
    def get_item_by_part(self, filing_object, part: str, item: str):
        """Retrieves a specific part of a filing.

        This method extracts a specific section or item from the provided filing.

        Args:
            filing: The filing object from which to extract the part.
            part (str): The specific part or item to retrieve from the filing
                        (e.g., 'Item 1A. Risk Factors').

        Returns:
            A string containing the extracted part of the filing.
        """
        text_obj = filing_object.get_item_with_part(part=part, item=item)

        #Format text with new lines
        if callable(text_obj):
            text = text_obj()
        else:
            text = str(text_obj)

        return text

class EdgarFinancials(EdgarCompany):
    """
    A class for retrieving and processing financial data from SEC EDGAR filings.
    Inherits from EdgarCompany to access company information, filings, and item parts.
    """
    
    def get_statements_pages(self, filing):
        """Retrieves financial statement pages from a filing (note not filing objects).

        Args:
            filing: The filing object from which to extract the financial statements.

        Returns:
            array of pages for statements
        """
        statement_pages = []

        all_reports = filing.reports

        for i,report in enumerate(all_reports):
            if report.menu_category == 'Statements':
                statement_pages.append(i)
                
        return statement_pages

    @staticmethod
    def clean_dataframe_header(df: pd.DataFrame) -> pd.DataFrame:
        """
        Cleans the header of a DataFrame where parts of the header are in the first row.

        This function is designed to handle cases where the main column headers are
        split, with some parts in the header row and date components in the first
        data row (often with 'Unnamed:' column placeholders).

        Args:
            df (pd.DataFrame): The input DataFrame to clean.

        Returns:
            pd.DataFrame: A new DataFrame with cleaned headers and data.
        """
        # Make a copy to avoid modifying the original DataFrame
        df_copy = df.copy()
        
        # Condition to check if cleaning is needed: 'Unnamed:' in columns and first row has non-NaN values
        if any('Unnamed:' in str(col) for col in df_copy.columns) and not df_copy.iloc[0].isnull().all():
            new_headers = []
            first_row = df_copy.iloc[0].fillna('')
            for i, col in enumerate(df_copy.columns):
                col_name = str(col)
                if 'Unnamed:' in col_name:
                    new_headers.append(str(first_row.iloc[i]))
                else:
                    new_headers.append(f"{col_name} {first_row.iloc[i]}".strip())
            df_copy.columns = new_headers
            
            # Clean up column names
            df_copy.columns = df_copy.columns.str.strip().str.replace(r'\s+', ' ', regex=True)
            
            # The first column name might have absorbed text from adjacent columns. Let's fix it.
            # We assume the first column's true name doesn't contain a date-like string from the second column.
            if len(df_copy.columns) > 1:
                second_col_val = str(df.iloc[0, 1]) if pd.notna(df.iloc[0, 1]) else ''
                if second_col_val and second_col_val in df_copy.columns[0]:
                     df_copy.columns.values[0] = df_copy.columns[0].split(second_col_val)[0].strip()

            # Drop the first row (which is now part of the header) and reset the index
            df_copy = df_copy.iloc[1:].reset_index(drop=True)
        
        return df_copy
    
    def get_excel_from_filing(self, filing):
        """
        Retrieves the Excel file from a filing and returns a list of DataFrames for each sheet.

        Args:
            filing: The filing object from which to extract the Excel file.
        
        Returns:
            list: List of tuples containing (sheet_name, DataFrame) for each sheet in the Excel file.
        """
        accession_number = filing.accession_number
        cik = self.company.cik

        accession_number_no_hyphens = accession_number.replace("-", "")
        base_link = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number_no_hyphens}"
        excel_file_link = f"{base_link}/Financial_Report.xlsx"

        try:
            response = requests.get(excel_file_link, headers=self.header)
            response.raise_for_status()
            
            # Read all sheets from the Excel file in memory
            excel_file = pd.ExcelFile(io.BytesIO(response.content))
            
            # Create a list of tuples with (sheet_name, dataframe)
            dataframes = []
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                dataframes.append((sheet_name, df))
            
            return dataframes
        except requests.exceptions.HTTPError as e:
            print(f"Could not retrieve Excel file. It may not exist for this filing ({filing.accession_number}). HTTP Status: {e.response.status_code}")
            return []

        
