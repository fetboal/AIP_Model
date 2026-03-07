from dataclasses import dataclass
import pandas as pd

@dataclass
class FinancialStatement:
    ticker: str
    cash_flow: pd.DataFrame
    income_statement: pd.DataFrame
    balance_sheet: pd.DataFrame
    MD_A: str

