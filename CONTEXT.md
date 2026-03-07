# Project Context

## Purpose

AI-powered financial analysis system. The project retrieves 10-K filings from SEC EDGAR,
extracts structured financial statements (income statement, balance sheet, cash flow), and
is designed to pass that data to LLM agents for investment analysis.

## Architecture

Four-layer design:

```
services/  (external APIs)
    ↓
tools/     (data transformation, callable by agents)
    ↓
agents/    (LLM orchestration — placeholder)
    ↓
outputs/   (CSV files, reports)
```

See [docs/architecture.md](docs/architecture.md) for more detail.

## Key Decisions

- **SEC EDGAR via `edgar` library**: Wraps the EDGAR REST API. A valid email must be
  supplied as `SEC_EMAIL` in `.env` — required by SEC policy for the User-Agent header.
- **Excel-first, HTML fallback**: Statements are extracted from `Financial_Report.xlsx`
  when available. If absent, `FilingSummary.xml` is parsed to find statement HTML files.
- **`STATEMENT_KEYWORDS` is the single source of truth** for mapping statement types to
  EDGAR short names. It lives in `src/tools/statement_keywords.py`. Changing it affects
  all extraction.
- **`FinancialStatement` dataclass** (`src/models/financial_statement.py`) is the contract
  between the data layer and the future LLM agent layer.
- **Composition over inheritance**: Tool functions in `src/tools/financial_data_tools.py`
  accept an `EdgarClient` instance as a parameter rather than inheriting from it. This
  makes mocking and testing straightforward.

## Environment Variables

| Variable    | Required | Description                              |
|-------------|----------|------------------------------------------|
| `SEC_EMAIL` | Yes      | Email for SEC EDGAR User-Agent header    |

## Known Tech Debt

- `SEC_EMAIL` defaults to a placeholder string if not set in the environment.
- `STATEMENT_KEYWORDS` uses single-word matching; the richer multi-phrase dictionary
  from `Obsolete/V2/Test_Sec_Data/Edgar_Functions.py` is a candidate upgrade.

## How to Extend

To add a new LLM agent:
1. Create `src/agents/<your_agent>.py`.
2. Import tools from `src.tools` and models from `src.models`.
3. Document the agent interface here.
