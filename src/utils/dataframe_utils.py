import pandas as pd


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
    df_copy = df.copy()

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

        df_copy.columns = df_copy.columns.str.strip().str.replace(r'\s+', ' ', regex=True)

        if len(df_copy.columns) > 1:
            second_col_val = str(df.iloc[0, 1]) if pd.notna(df.iloc[0, 1]) else ''
            if second_col_val and second_col_val in df_copy.columns[0]:
                df_copy.columns.values[0] = df_copy.columns[0].split(second_col_val)[0].strip()

        df_copy = df_copy.iloc[1:].reset_index(drop=True)

    return df_copy
