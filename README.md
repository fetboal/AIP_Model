# AIP Model — AI-Powered Financial Analysis

Fetches multi-year 10-K filings from SEC EDGAR for any US-listed company and produces
consolidated balance sheet, income statement, and cash flow CSV files. Designed to feed
structured financial data to LLM agents for investment analysis.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure your SEC email
cp .env.example .env
# Edit .env and set SEC_EMAIL=your-email@example.com

# 3. Run
python -m scripts.fetch_financials
```

Output CSVs are written to the `outputs/` directory.

## Configuration

Edit `scripts/fetch_financials.py` to change the ticker or filing count:

```python
TICKER = "NVDA"   # any US-listed ticker
count=10          # number of 10-K filings to retrieve
```

## Project Structure

```
src/
  agents/    Future LLM agent implementations
  tools/     Data extraction and transformation functions
  services/  SEC EDGAR client (external API wrapper)
  models/    Data models (FinancialStatement dataclass)
  utils/     DataFrame utilities and CSV export helpers
scripts/     Runnable entry points
tests/       Test suite (stubs — contributions welcome)
docs/        Architecture documentation
outputs/     Generated CSV files
```

## SEC Data Policy

The SEC requires a valid email address in the User-Agent header for all EDGAR API
requests. Set `SEC_EMAIL` in your `.env` file. Do not make abusive or high-frequency
requests to the EDGAR API.

## Roadmap

- **Phase 1 (current)**: SEC EDGAR data extraction → structured CSVs
- **Phase 2**: LLM agent analysis (ratios, trends, red flags, MD&A summarisation)
- **Phase 3**: Multi-company comparison and competitive analysis
