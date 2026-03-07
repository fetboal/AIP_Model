import edgar


class EdgarClient:
    """
    A client to interact with the SEC EDGAR database for a specific company.
    Handles initialization and retrieval of filings and item parts.
    """

    def __init__(self, email: str, ticker: str):
        """Initializes the EdgarClient.

        Sets the user identity required for making requests to the SEC EDGAR
        database and creates a Company object for the given stock ticker.

        Args:
            email (str): The email address to use as the user agent for SEC requests.
                         Required by the SEC to identify the user/application.
            ticker (str): The stock ticker symbol for the desired company.
        """
        edgar.set_identity(email)
        self.header = {'User-Agent': email}
        self.company = edgar.Company(ticker)
        self.ticker = ticker

    def get_multiple_filings(self, filing_type: str, count: int) -> list:
        """Gets multiple filings of a specified type for the company.

        Args:
            filing_type (str): The form type of the filings to retrieve (e.g., '10-K', '10-Q').
            count (int): The number of filings to retrieve.

        Returns:
            list: List of filing objects corresponding to the specified type and count.
        """
        filings = self.company.get_filings(form=filing_type)
        result = []
        for i in range(count):
            result.append(filings[i])
        return result

    def get_item_by_part(self, filing_object, part: str, item: str) -> str:
        """Retrieves a specific part of a filing.

        Args:
            filing_object: The filing object from which to extract the part.
            part (str): The part to retrieve (e.g., 'Part I').
            item (str): The item to retrieve (e.g., 'Item 1A. Risk Factors').

        Returns:
            str: A string containing the extracted part of the filing.
        """
        text_obj = filing_object.get_item_with_part(part=part, item=item)

        if callable(text_obj):
            text = text_obj()
        else:
            text = str(text_obj)

        return text
