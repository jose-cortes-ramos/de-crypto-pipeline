# Architecture Decisions & Technical Stack 🏗️

Este documento explica las decisiones técnicas tomadas en el proyecto **De-Crypto Pipeline**, justificando cada componente desde una perspectiva de **Senior Data Engineering**. El diseño prioriza la robustez, la precisión financiera y la observabilidad.

---

## 1. Diseño de Software y Estructura
Un proyecto profesional debe estar organizado para ser escalable y mantenible.

### 1.1 Estructura Modular
*   **Decisión:** Separar la lógica en `src/` (negocio), `sql/` (esquema), `tests/` (calidad) y `docs/` (transparencia).
*   **Justificación:** El desacoplamiento entre configuración (`config.py`), contratos de datos (`schemas.py`) y lógica de extracción (`extractors.py`) asegura el cumplimiento del principio de Responsabilidad Única (SoC).

### 1.2 Evolución a Arquitectura OOP
*   **Decisión:** Migrar de scripts lineales a una arquitectura modular orientada a objetos.
*   **Justificación:** Facilita la inyección de dependencias, mejora la testabilidad y permite centralizar comportamientos complejos como los reintentos y el logging sin duplicar código.

---

## 2. Infraestructura y Despliegue 🐳

### 2.1 Estrategia de Contenerización (Docker)
*   **Decisión:** Uso de `python:3.11-slim` y orquestación con Docker Compose.
*   **Optimización Contextual (.dockerignore):** Se implementó una política de exclusión de archivos (venv, caches, logs).
*   **Impacto Senior:** Reducción del tiempo de build de **~320s a <1s**, optimizando el ciclo de vida del desarrollo y la eficiencia del CI/CD.

### 2.2 Gestión de Módulos (PYTHONPATH)
*   **Decisión:** Configurar la raíz del proyecto en el `PYTHONPATH` y ejecutar mediante `python -m src.main`.
*   **Justificación:** Evita errores de importación relativos y asegura que el orquestador se ejecute siempre dentro del contexto del paquete, un estándar en aplicaciones de producción.

---

## 3. Almacenamiento y Optimización de Datos 📈

### 3.1 Modelado para Series Temporales (PostgreSQL)
*   **PK Compuesta `(id, extracted_at)`:** Garantiza integridad referencial y permite la partición lógica de datos históricos.
*   **Índices Especializados:**
    *   `idx_crypto_extracted_at`: Optimizado para filtros de tiempo (ej. reportes diarios).
    *   `idx_crypto_symbol_time`: Índice compuesto descendente para consultas de "último precio" ultra rápidas.

---

## 4. Ingeniería de Resiliencia y Calidad

### 4.1 Capa de Reintentos (Tenacity)
*   **Estrategia:** Exponential Backoff.
*   **Valor:** El pipeline no falla ante errores 429 (Rate Limit) o 5xx de la API; se auto-recupera esperando tiempos incrementales, lo que garantiza la continuidad del servicio.

### 4.2 Estrategia Fail-Fast (Healthchecks)
*   **Decisión:** Validar conectividad con la API (`/ping`) y PostgreSQL (`SELECT 1`) antes de iniciar el ETL.
*   **Justificación:** Previene ejecuciones fallidas que consumen recursos. Si la infraestructura base no está lista, el pipeline aborta de forma controlada.

### 4.3 Validación de Contratos (Pydantic)
*   **Schema-on-Read:** Validación inmediata post-extracción para detectar cambios en la fuente externa.
*   **Schema-on-Write:** Firewall final pre-ingesta que asegura la integridad estructural del Warehouse.

---

## 5. Integridad de Datos (Senior Implementation)

### 5.1 Precisión Financiera (Decimal vs Float)
*   **Decisión:** Uso estricto de `decimal.Decimal` en Python y `NUMERIC(18, 8)` en SQL.
*   **Justificación:** Los floats introducen errores de redondeo binarios. En criptomonedas con valores ínfimos, la precisión exacta es un requisito de negocio no negociable.

### 5.2 Idempotencia mediante Upsert
*   **Estrategia:** `INSERT ... ON CONFLICT (id, extracted_at) DO UPDATE`.
*   **Valor:** Permite re-ejecutar el pipeline N veces sin duplicar datos, facilitando la recuperación ante desastres (Disaster Recovery).

### 5.3 Transacciones Atómicas y Pooling
*   **Connection Pooling:** Reutilización de conexiones mediante SQLAlchemy para optimizar recursos del servidor.
*   **Atomicidad (ACID):** Uso de `engine.begin()` para asegurar cargas "todo o nada". Cualquier error parcial dispara un Rollback automático.

---

## 6. Observabilidad y DataOps

### 6.1 Telemetría Estructurada (JSON Logging)
*   **Decisión:** Migración a `python-json-logger`.
*   **Justificación:** Los logs en JSON son machine-readable, permitiendo que plataformas como Datadog o ELK realicen análisis y alertas automáticas basadas en campos específicos.

### 6.2 Auditoría de Carga (Closed-Loop)
*   **Decisión:** Verificación dinámica post-carga comparando registros en memoria vs registros reales en DB.
*   **Justificación:** Cierra el ciclo de confianza. Validamos empíricamente que el estado final de la base de datos es 100% consistente con lo procesado.

### 6.3 Automatización de Calidad (CI/CD)
*   **GitHub Actions:** Ejecución de tests contra un PostgreSQL real en el CI. Monitoreo de Code Coverage.
*   **Pre-commit Hooks:** Blindaje local que impide subir código que no cumpla con los estándares de Black y Flake8.

---
Este proyecto prioriza la **confiabilidad** sobre la complejidad, estableciendo una base sólida para un entorno de datos productivo.
