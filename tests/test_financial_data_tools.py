"""
Tests for src.tools.financial_data_tools

Test cases to implement:
- test_find_statement_indices_by_keywords: Returns correct mapping for a known filing.
- test_get_excel_from_filing_success: Returns list of (sheet_name, DataFrame) tuples.
- test_get_excel_from_filing_missing: Returns empty list on HTTP 404.
- test_get_statements_by_type_excel_path: Uses Excel when available.
- test_get_statements_by_type_html_fallback: Falls back to HTML when no Excel file.
- test_combine_dataframes_deduplicates_years: Older filing years do not overwrite newer.
- test_combine_dataframes_empty_input: Returns three empty DataFrames.
"""

# TODO: Implement tests using pytest and unittest.mock to avoid live SEC calls
