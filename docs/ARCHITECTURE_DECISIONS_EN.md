# Architecture Decisions & Technical Stack 🏗️

This document explains the technical decisions made in the **De-Crypto Pipeline** project, justifying each component from a **Senior Data Engineering** perspective. The design prioritizes robustness, financial precision, and observability.

---

## 1. Software Design & Structure
A professional project must be organized to be scalable and maintainable.

### 1.1 Modular Structure
*   **Decision:** Separate logic into `src/` (business), `sql/` (schema), `tests/` (quality), and `docs/` (transparency).
*   **Justification:** Decoupling configuration (`config.py`), data contracts (`schemas.py`), and extraction logic (`extractors.py`) ensures compliance with the Single Responsibility Principle (SoC).

### 1.2 Evolution to OOP Architecture
*   **Decision:** Migrate from linear scripts to a modular object-oriented architecture.
*   **Justification:** Facilitates dependency injection, improves testability, and allows centralizing complex behaviors like retries and logging without code duplication.

---

## 2. Infrastructure & Deployment 🐳

### 2.1 Containerization Strategy (Docker)
*   **Decision:** Use `python:3.11-slim` and orchestration with Docker Compose.
*   **Contextual Optimization (.dockerignore):** Implemented a strict file exclusion policy (venv, caches, logs).
*   **Senior Impact:** Reduced build time from **~320s to <1s**, optimizing the development lifecycle and CI/CD efficiency.

### 2.2 Module Management (PYTHONPATH)
*   **Decision:** Configure the project root in the `PYTHONPATH` via `pyproject.toml` and execute using `python -m src.main`.
*   **Justification:** Avoids relative import errors and ensures that automation environments (GitHub Actions) correctly resolve project dependencies.

---

## 3. Storage & Data Optimization 📈

### 3.1 Time-Series Modeling (PostgreSQL)
*   **Composite PK `(id, extracted_at)`:** Guarantees referential integrity and allows logical partitioning of historical data.
*   **Specialized Indexes:**
    *   `idx_crypto_extracted_at`: Optimized for time filters (e.g., daily reports).
    *   `idx_crypto_symbol_time`: Descending composite index for ultra-fast "latest price" queries.

---

## 4. Resilience & Quality Engineering

### 4.1 Retry Layer (Tenacity)
*   **Strategy:** Exponential Backoff.
*   **Value:** The pipeline does not fail on API 429 (Rate Limit) or 5xx errors; it self-recovers by waiting for incremental times, ensuring service continuity.

### 4.2 Fail-Fast Strategy (Healthchecks)
*   **Decision:** Validate connectivity with the API (`/ping`) and PostgreSQL (`SELECT 1`) before starting the ETL.
*   **Justification:** Prevents failed executions that unnecessarily consume resources. If the base infrastructure is not ready, the pipeline aborts in a controlled manner.

### 4.3 Contract Validation (Pydantic)
*   **Schema-on-Read:** Immediate post-extraction validation to detect changes in the external source.
*   **Schema-on-Write:** Final pre-ingestion firewall ensuring the structural integrity of the Warehouse.

---

## 5. Data Integrity (Senior Implementation)

### 5.1 Financial Precision (Decimal vs Float)
*   **Decision:** Strict use of `decimal.Decimal` in Python and `NUMERIC(18, 8)` in SQL.
*   **Justification:** Floats introduce binary rounding errors. In cryptocurrencies with minute values, exact precision is a non-negotiable business requirement.

### 5.2 Idempotency via Upsert
*   **Strategy:** `INSERT ... ON CONFLICT (id, extracted_at) DO UPDATE`.
*   **Value:** Allows re-executing the pipeline N times without duplicating data, facilitating disaster recovery.

### 5.3 Atomic Transactions & Pooling
*   **Connection Pooling:** Connection reuse via SQLAlchemy to optimize server resources.
*   **Atomicity (ACID):** Use of `engine.begin()` to ensure "all-or-nothing" loads. Any partial error triggers an automatic Rollback.

---

## 6. Observability & DataOps

### 6.1 Structured Telemetry (JSON Logging)
*   **Decision:** Migration to `python-json-logger`.
*   **Justification:** JSON logs are machine-readable, allowing platforms like Datadog or ELK to perform automated analysis and alerting based on specific fields.

### 6.2 Load Auditing (Closed-Loop)
*   **Decision:** Dynamic post-load verification comparing memory records vs real records in the DB.
*   **Justification:** Closes the trust loop. We empirically validate that the final state of the database is 100% consistent with what was processed.

### 6.3 Quality Automation (CI/CD)
*   **GitHub Actions:** Execution of tests against a real PostgreSQL in the CI. Code Coverage monitoring.
*   **Pre-commit Hooks:** Local shielding that prevents uploading code that does not meet Black and Flake8 standards.

### 6.4 Single Source of Truth (pyproject.toml)
*   **Decision:** Centralize configuration for `black`, `pytest`, and other development tools in a single file.
*   **Justification:** Eliminates configuration file dispersion and ensures that both developers and CI systems use the same execution parameters.

---
This project prioritizes **reliability** over complexity, establishing a solid foundation for a productive data environment.
