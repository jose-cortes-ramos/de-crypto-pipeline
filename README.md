# De-Crypto Pipeline: Crypto Market ETL 🚀

**Data Engineering Portfolio - Jose Cortes**

Professional ETL pipeline designed to extract, transform, and load cryptocurrency market data from the CoinGecko API into a PostgreSQL data warehouse.

## 🏗️ Architecture Overview

The pipeline follows a modern data engineering approach with a **Modular OOP Architecture**:
1.  **Extraction:** Decoupled extractor using `tenacity` for **Exponential Backoff** (handles 429/5xx errors gracefully).
2.  **Validation:** **Schema-on-Read** enforcement using `Pydantic` to guarantee data integrity at the source.
3.  **Transformation:** Data cleaning and metadata enrichment using `Pandas`.
4.  **Loading:** Time-series optimized ingestion into `PostgreSQL` using `SQLAlchemy`.

## ✨ Key Features (Senior Implementation)

*   **Resilient Extraction:** Implements intelligent retry logic to handle API rate limits and network instability.
*   **Strict Data Contracts:** Prevents data corruption by validating incoming JSON payloads against strictly typed schemas.
*   **Centralized Configuration:** Zero hardcoding approach using a dedicated `Config` layer for environment-agnostic deployment.
*   **Time-Series Optimized:** Database schema designed with composite indexes for high-performance historical data querying.

## 🛠️ Technology Stack

*   **Language:** Python 3.11
*   **Libraries:** Pandas, SQLAlchemy, Pydantic, Tenacity, Requests.
*   **Database:** PostgreSQL 15 (Alpine)
*   **Infrastructure:** Docker & Docker Compose
*   **Quality:** Pytest, Black, Flake8.

## 🚀 Quick Start

1.  **Configure environment:**
    ```bash
    cp .env.example .env
    # Edit .env with your credentials
    ```

2.  **Deploy with Docker:**
    ```bash
    docker-compose up --build
    ```

---
*Developed by Jose Cortes - Senior Data Engineering Portfolio*
