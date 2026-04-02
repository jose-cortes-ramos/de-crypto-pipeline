# Data Pipeline Flow: Technical Deep Dive 🧠

Este documento detalla el flujo de datos del **De-Crypto Pipeline**, explicando la lógica técnica detrás de cada etapa y la justificación de las herramientas seleccionadas bajo estándares de **Senior Data Engineering**.

---

## 1. Extracción y Capa de Resiliencia (The Source)

### **A. CoinGecko API (REST/JSON)**
*   **Herramienta:** `requests`
*   **Lógica:** Consumimos el endpoint `/coins/markets` para obtener datos en tiempo real.
*   **Por qué:** REST es el estándar para datos públicos. JSON nos permite una estructura flexible que podemos validar antes de procesar.

### **B. Resilience Layer: Tenacity (Retry Logic)**
*   **Herramienta:** `tenacity` (Exponential Backoff)
*   **Lógica:** Si la API devuelve un error `429` (Rate Limit) o `5xx` (Server Error), el pipeline no "muere". Espera un tiempo (1s, 2s, 4s...) antes de reintentar.
*   **Justificación Senior:** Las APIs externas son fuentes no confiables por definición. Un pipeline de producción **debe** ser capaz de auto-recuperarse ante fallas de red momentáneas sin intervención humana.

---

## 2. Validación de Contratos (The Firewall)

### **C. Schema-on-Read (Pydantic Validation)**
*   **Herramienta:** `pydantic` (`CryptoMarketData`)
*   **Lógica:** Inmediatamente después de recibir el JSON, lo pasamos por un modelo de validación.
*   **Por qué:** Aplicamos la estrategia **Fail-Fast**. Si la API cambia su estructura (ej. un precio viene como string en lugar de número), el error se detecta aquí, evitando que basura (garbage data) entre a nuestras capas de transformación.

---

## 3. Transformación y Precisión (The Processor)

### **D. Pandas Transformation**
*   **Herramienta:** `pandas`
*   **Lógica:** Limpieza de columnas, filtrado de registros inconsistentes (precios <= 0) y enriquecimiento con metadatos (`extracted_at`).
*   **Por qué:** Pandas es imbatible para manipulación de datos en memoria. Permite vectorizar operaciones de limpieza de forma mucho más eficiente que los loops de Python.

### **E. Type Hardening: Decimal Precision**
*   **Herramienta:** `decimal.Decimal`
*   **Lógica:** Convertimos todos los valores financieros de `float` a `Decimal`.
*   **Justificación Senior:** Los floats en computación (IEEE 754) tienen errores de redondeo (ej. `0.1 + 0.2 != 0.3`). En cripto, donde un token puede valer `0.00000456`, perder decimales es inaceptable. El uso de `Decimal` garantiza **precisión matemática absoluta**.

---

## 4. Persistencia e Idempotencia (The Warehouse)

### **F. Schema-on-Write (Output Enforcement)**
*   **Herramienta:** `pydantic` (`CryptoPriceOutput`)
*   **Lógica:** Antes de tocar la base de datos, validamos que el DataFrame final cumpla el contrato de salida.
*   **Por qué:** Es nuestra última línea de defensa (Firewall) para asegurar que el Data Warehouse mantenga su integridad estructural.

### **G. UPSERT Strategy (Idempotency)**
*   **Herramienta:** `SQLAlchemy` (Dialecto PostgreSQL)
*   **Lógica:** Usamos `INSERT ... ON CONFLICT (id, extracted_at) DO UPDATE`.
*   **Justificación Senior:** La **Idempotencia** es la propiedad de que un proceso se pueda ejecutar múltiples veces dando el mismo resultado. Si el pipeline corre dos veces por error, el Upsert actualiza en lugar de duplicar, manteniendo el historial limpio.

### **H. Connection Pooling & Atomic Transactions**
*   **Lógica:** Gestión de pool de conexiones y uso de `engine.begin()`.
*   **Por qué:**
    *   **Pooling:** Reutiliza conexiones para no saturar a PostgreSQL (Eficiencia).
    *   **Transacciones:** Asegura que la carga sea **Atómica**. Si falla el registro 49 de 50, se hace un Rollback total. No permitimos cargas parciales corruptas.

---

## 5. Calidad y Confianza (The Quality Gate)

### **I. Post-Ingestion Verification**
*   **Lógica:** Verificación de logs de auditoría post-carga.
*   **Por qué:** Un Senior no asume que el SQL funcionó porque no hubo error. Validamos empíricamente que la operación cerró el ciclo de confianza.

### **J. CI/CD Lifecycle Firewall**
*   **Lógica:** Integración de `Black`, `Flake8` y `Pytest` en el ciclo de vida del software.
*   **Justificación Senior:** El flujo de datos no es solo técnico, es de proceso. Si el código no cumple con el 100% de los estándares de estilo y pruebas, el "Firewall de Calidad" (CI) bloquea el despliegue, garantizando que solo código de alta calidad llegue a producción.

---
*Este flujo garantiza que el dato sea veraz, preciso y persistente desde el origen hasta el destino final.*
