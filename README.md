# Rodoc Documentation Indexer and Search Engine

This project is a comprehensive system designed to crawl, index, and provide advanced search capabilities for documentation sources. It handles the entire lifecycle from web crawling to vector database indexing and retrieval.

## 🚀 Features

*   **Web Crawling:** Robust module (`src/crawl`) capable of extracting structured content from various sources.
*   **Content Detection & Conversion:** Uses specialized detectors and converters (e.g., Markdown) to standardize extracted data.
*   **Indexing Pipeline:** Implements a full indexing pipeline (`src/index`), including chunking, embedding generation, and storage in a vector store (FAISS).
*   **Search Service (MCP):** Provides a dedicated search microservice layer (`src/mcp_docs_server`) for querying the index.

## 🛠️ Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd rodoc
    ```
2.  **Install dependencies:**
    The project uses `requirements.txt` and `pyproject.toml`. Install all necessary packages:
    ```bash
    pip install -r requirements.txt
    # Or using poetry/pipenv if preferred, based on pyproject.toml
    ```

## ⚙️ Usage Guide

### 1. Crawling Documentation

Run the crawler to discover and extract content from specified URLs or directories. This process populates the raw data needed for indexing.

*   **Command:** `python src/main.py` (or use a dedicated script like `list_docs.sh`)
*   **Details:** The crawling module handles fetching, parsing, and saving initial content chunks.

### 2. Indexing the Content

After crawling, the raw data must be indexed into the vector store for fast semantic search.

*   **Command:** `python src/index/main.py`
*   **Process:** This script loads documents, splits them into manageable chunks (`src/index/chunker.py`), generates embeddings (`src/index/embedding.py`), and stores them in the FAISS index (`src/index/faiss_store.py`).

### 3. Searching Documentation (Search Service)

The search service provides an API-like interface to query the indexed knowledge base.

*   **CLI Tool:** Use `python src/mcp_docs_server/search_docs.py`
## 🧩 Integration with opencode (MCP Example)

When integrating the search service into an `opencode` configuration, you can define it under the `"mcp"` key. This example shows how to configure both a remote and a local documentation source:

```json
"mcp": {
  "maestro": {
   "type": "remote",
   "url": "http://localhost:8000/mcp"
  },
  "local-docs": {
        "type": "local",
        "command": ["/media/elson/IA/clude_code/workspace/rodoc/run_mcp.sh"],
        "enabled": true
      }
 }
```

## 📂 Project Structure Overview

*   `src/crawl/`: Contains modules responsible for fetching and parsing content (e.g., `crawler.py`, `markdown_converter.py`).
*   `src/index/`: Handles the vector database operations, including chunking, embedding, and storage management.
*   `src/mcp_docs_server/`: Implements the search API logic and document listing utilities.
*   `run.sh`, `list_docs.sh`: Utility scripts for running common workflows.

