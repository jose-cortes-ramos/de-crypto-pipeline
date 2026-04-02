# Operations & Deployment Guide 🛠️

This document describes the procedures for deploying, maintaining, and scaling the **De-Crypto Pipeline** in production environments.

---

## 1. Configuration & Secrets Management

### **A. .env Files (Local)**
*   Use `.env.example` as a template to configure PostgreSQL credentials and the CoinGecko API Key.
*   **Warning:** Never commit real `.env` files (included in `.gitignore`).

### **B. Production Secrets (Cloud)**
*   If deploying to AWS/GCP/Azure, use services like **AWS Secrets Manager** or **GitHub Actions Secrets**.
*   **Procedure:** Inject variables (`COINGECKO_API_KEY`, `DATABASE_URL`) as environment variables directly into the container orchestrator (ECS, Kubernetes).

---

## 2. Monitoring & Auditing

### **A. Log Analysis (Observability)**
The pipeline generates logs in **JSON** format. To search for production failures, use filters on these fields:
*   `levelname == "ERROR"`: Identifies critical network or database failures.
*   `levelname == "WARNING"`: Records data quality issues (filtered prices).
*   `message.contains("Audit")`: Filters the results of the post-load integrity verification loop.

### **B. Healthchecks (Fail-Fast)**
The system performs two proactive checks before starting:
1.  **API Check:** Calls CoinGecko's `/ping`.
2.  **DB Check:** Calls `SELECT 1` in PostgreSQL.
*   *Action on failure:* Do not retry the entire pipeline; first verify the base infrastructure (Network/Database).

---

## 3. Scalability Strategy

### **A. Extraction Scaling (Volume)**
The pipeline is configured for 50 assets per page. If you need to scale to thousands of assets:
*   Adjust `PER_PAGE` in `src/config.py`.
*   Implement **Pagination** logic in `src/extractors.py`.

### **B. Database (Time-Series)**
Over time, the `crypto_prices` table will grow massively.
*   **Senior Decision:** Implement **Table Partitioning** in PostgreSQL based on the `extracted_at` field (monthly or quarterly).

---

## 4. Code Maintenance (DataOps)

### **A. CI/CD Pipeline**
Every code change must pass through the GitHub Actions flow:
1.  **Linter Check:** Ensures visual consistency (Black/Flake8).
2.  **Integration Tests:** Validates real persistence against an ephemeral PostgreSQL.
3.  **Coverage:** Ensures the coverage percentage does not decrease.

### **B. Local Quality Commands**
To ensure the CI passes on the first attempt, run these commands before pushing your code:
```bash
# Auto-formatting
black .

# Standards validation (Should return 0 errors)
flake8 .

# Run tests with coverage
pytest --cov=src
```

### **C. Pre-commit Hooks**
Install hooks to automate quality on every commit:
```bash
pip install pre-commit
pre-commit install
```

---
*This project is designed to be operated with minimal human intervention, prioritizing early failure detection and absolute data integrity.*
