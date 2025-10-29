## AI-Powered 10-K Document Analysis

### Project Overview
This project leverages advanced AI models (specifically OpenAI's GPT-4o) to automate the parsing, classification, and extraction of key information from 10-K financial documents. The goal is to transform unstructured PDF data into structured, analyzable formats, facilitating in-depth financial and operational analysis.

### Key Features and Functionality

#### 1. Document Pre-processing
-   **PDF Splitting**: Automatically splits large PDF documents into individual pages for granular processing.
-   **Page Extraction**: Ability to extract specific pages or groups of pages (e.g., all "Financial Statement" pages) into new PDF files.

#### 2. AI-Driven Content Understanding
-   **Intelligent Page Classification**: Each page is classified into one of several predefined categories using few-shot learning with the AI model:
    -   `Financial Statement`
    -   `Operational and Risk`
    -   `Debt and Loans`
    -   `Legal`
    -   `Other`
-   **Structured Data Extraction**: For classified pages (excluding 'Other'), the AI extracts detailed information into predefined JSON schemas. This includes:
    -   **Financial Statements**: Key figures from Income Statements, Balance Sheets, and Cash Flow statements (e.g., Net Sales, Total Assets, Net Cash from Operating Activities).
    -   **Operational and Risk**: Business segments, geographic exposure, competitive landscape, key risks, and Management Discussion & Analysis (MD&A) commentary.
    -   **Debt and Loans**: Details on debt instruments, covenants, and capital structure.
    -   **Legal**: Information on litigation, regulatory matters, and corporate governance.
-   **Business Segment Identification**: Identifies the specific business segment(s) (e.g., "Performance Coatings", "Consolidated") to which the extracted data pertains.

#### 3. Data Management & Reporting
-   **Data Persistence**: All classification results, extracted schemas, and raw AI responses are saved to a compressed pickle file (`.pkl.gz`) for efficient storage and retrieval.
-   **Comprehensive PDF Report Generation**: A human-readable PDF report is generated, summarizing:
    -   Overall classification statistics.
    -   Detailed breakdown for each processed page, including its category, overall focus, reasoning points, and extracted business segments.
-   **Category-Specific PDF Artifacts**: Separate PDF files are generated for each major category (e.g., "Financial_Statement_Pages.pdf", "Operational_and_Risk_Pages.pdf"), containing only the relevant pages from the original document.

#### 4. Data Analysis & Exploration
-   **Pandas DataFrame Integration**: The persisted structured data can be loaded and transformed into Pandas DataFrames, enabling powerful data manipulation, querying, and further analysis.
-   **Exploration Script**: An `analysis.py` script is provided to demonstrate how to load the data and create DataFrames for easy exploration of extracted metrics.

### Project Goals (Original)
-   Build an AI agent to parse the document and summarize key features.
-   Put the key data from the 10-K into dataframes to allow for manipulation.
    -   Find key financial data.
    -   Summarize key market segments.
    -   Revenue drivers and MD&A.
    -   Comparison to competition.
-   Aim to make production-level code with LLM reasoning closely documented.
-   Overall goal: try to find the reason that AIP purchased PPG.

### Technology Stack
-   **Python**: Core programming language.
-   **OpenAI API (GPT-4o)**: For AI classification and data extraction.
-   **PyPDF2**: For PDF manipulation (splitting, merging, extraction).
-   **ReportLab**: For generating custom PDF reports.
-   **Pandas**: For data structuring and analysis.
-   **python-dotenv**: For managing environment variables (API keys).

### Setup and Usage
1.  **Environment Variables**: Create a `.env` file in the project root and add your OpenAI API key:
    ```
    OPENAI_API_KEY="your_openai_api_key_here"
    ```
2.  **Run `main.py`**: Execute `main.py` to start the PDF processing pipeline. You can configure `IS_TESTING` to process a subset of pages or the entire document.
3.  **Analyze Results**: After `main.py` completes, explore the generated PDFs in the `generated PDFS` directory and use `analysis.py` to load and interact with the structured data in Pandas DataFrames.
