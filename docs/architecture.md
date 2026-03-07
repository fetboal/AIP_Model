# Architecture

The project uses a four-layer architecture:

```
services/  ->  tools/  ->  agents/  ->  outputs/
```

- **services/** — Wraps external APIs (SEC EDGAR). Handles authentication and raw data retrieval. `EdgarClient` is the only current implementation.
- **tools/** — Transforms raw filing data into structured DataFrames. Functions here are the callable units that an LLM agent invokes. `financial_data_tools.py` contains all extraction and combination logic.
- **agents/** — LLM orchestration layer (placeholder). Agents accept a `FinancialStatement` model and use tools to produce analysis.
- **outputs/** — Generated CSV files from script runs.

See `CONTEXT.md` at the project root for full context and key design decisions.
