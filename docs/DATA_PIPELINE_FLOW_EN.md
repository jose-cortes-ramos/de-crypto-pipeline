# Data Pipeline Flow: Technical Deep Dive 🧠

This document details the data flow of the **De-Crypto Pipeline**, explaining the technical logic behind each stage and the justification for the selected tools under **Senior Data Engineering** standards.

---

## 1. Extraction & Resilience Layer (The Source)

### **A. CoinGecko API (REST/JSON)**
*   **Tool:** `requests`
*   **Logic:** We consume the `/coins/markets` endpoint to obtain real-time data.
*   **Why:** REST is the standard for public data. JSON allows for a flexible structure that we can validate before processing.

### **B. Resilience Layer: Tenacity (Retry Logic)**
*   **Tool:** `tenacity` (Exponential Backoff)
*   **Logic:** If the API returns a `429` (Rate Limit) or `5xx` (Server Error), the pipeline does not "die." It waits for a period (1s, 2s, 4s...) before retrying.
*   **Senior Justification:** External APIs are unreliable sources by definition. A production pipeline **must** be able to self-recover from momentary network failures without human intervention.

---

## 2. Contract Validation (The Firewall)

### **C. Schema-on-Read (Pydantic Validation)**
*   **Tool:** `pydantic` (`CryptoMarketData`)
*   **Logic:** Immediately after receiving the JSON, we pass it through a validation model.
*   **Why:** We apply the **Fail-Fast** strategy. If the API changes its structure (e.g., a price comes as a string instead of a number), the error is detected here, preventing garbage data from entering our transformation layers.

---

## 3. Transformation & Precision (The Processor)

### **D. Pandas Transformation**
*   **Tool:** `pandas`
*   **Logic:** Column cleaning, filtering of inconsistent records (prices <= 0), and metadata enrichment (`extracted_at`).
*   **Why:** Pandas is unbeatable for in-memory data manipulation. It allows for vectorizing cleaning operations much more efficiently than Python loops.

### **E. Type Hardening: Decimal Precision**
*   **Tool:** `decimal.Decimal`
*   **Logic:** We convert all financial values from `float` to `Decimal`.
*   **Senior Justification:** Floats in computing (IEEE 754) have rounding errors (e.g., `0.1 + 0.2 != 0.3`). In crypto, where a token can be worth `0.00000456`, losing decimals is unacceptable. Using `Decimal` guarantees **absolute mathematical precision**.

---

## 4. Persistence & Idempotency (The Warehouse)

### **F. Schema-on-Write (Output Enforcement)**
*   **Tool:** `pydantic` (`CryptoPriceOutput`)
*   **Logic:** Before touching the database, we validate that the final DataFrame meets the output contract.
*   **Why:** It is our last line of defense (Firewall) to ensure the Data Warehouse maintains its structural integrity.

### **G. UPSERT Strategy (Idempotency)**
*   **Tool:** `SQLAlchemy` (PostgreSQL Dialect)
*   **Logic:** We use `INSERT ... ON CONFLICT (id, extracted_at) DO UPDATE`.
*   **Senior Justification:** **Idempotency** is the property that a process can be executed multiple times with the same result. If the pipeline runs twice by mistake, the Upsert updates instead of duplicating, keeping the history clean.

### **H. Connection Pooling & Atomic Transactions**
*   **Logic:** Connection pool management and use of `engine.begin()`.
*   **Why:**
    *   **Pooling:** Reuses connections to avoid saturating PostgreSQL (Efficiency).
    *   **Transactions:** Ensures the load is **Atomic**. If record 49 of 50 fails, a total Rollback is performed. We do not allow corrupt partial loads.

---

## 5. Quality & Trust (The Quality Gate)

### **I. Post-Ingestion Verification**
*   **Logic:** Post-load audit log verification.
*   **Why:** A Senior does not assume the SQL worked because there was no error. We empirically validate that the operation closed the trust loop.

### **J. CI/CD Lifecycle Firewall**
*   **Logic:** Integration of `Black`, `Flake8`, and `Pytest` into the software lifecycle.
*   **Senior Justification:** Data flow is not just technical; it's procedural. If the code does not meet 100% of the style and testing standards, the "Quality Firewall" (CI) blocks the deployment, ensuring that only high-quality code reaches production.

---
*This flow ensures that data is truthful, accurate, and persistent from origin to final destination.*
