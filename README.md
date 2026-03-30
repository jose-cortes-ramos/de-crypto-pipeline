# De-Crypto Pipeline: Crypto Market ETL 🚀

**Data Engineering Portfolio - Jose Cortes**

Professional ETL pipeline designed to extract, transform, and load cryptocurrency market data from the CoinGecko API into a PostgreSQL data warehouse.

## 🏗️ Architecture Overview

The pipeline follows a modern data engineering approach:
1.  **Extraction:** REST API consumption with robust retry logic (Exponential Backoff).
2.  **Transformation:** Data cleaning and schema enforcement using Pandas and Pydantic.
3.  **Loading:** Idempotent ingestion (Upsert) into PostgreSQL for historical analysis.

## 🛠️ Technology Stack

*   **Language:** Python 3.11
*   **Data Processing:** Pandas
*   **Persistence:** PostgreSQL 15 (SQLAlchemy ORM)
*   **Infrastructure:** Docker & Docker Compose
*   **Observability:** Structured Logging
*   **Quality:** Pytest, Pydantic, Black/Flake8 (CI/CD ready)

## 🚀 Quick Start (Development)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/de-crypto-pipeline.git
    cd de-crypto-pipeline
    ```

2.  **Configure environment:**
    ```bash
    cp .env.example .env
    # Edit .env with your local credentials if needed
    ```

3.  **Deploy with Docker:**
    ```bash
    docker-compose up --build
    ```

---
*Developed by Jose Cortes - Senior Data Engineering Portfolio*
