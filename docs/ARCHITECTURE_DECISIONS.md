# Architecture Decisions & Technical Stack 🏗️

Este documento explica las decisiones técnicas tomadas en el proyecto **De-Crypto Pipeline**, justificando cada componente desde una perspectiva de **Senior Data Engineering**.

## 1. Estructura del Proyecto
Un proyecto profesional debe estar organizado para ser escalable y mantenible:
*   `src/`: Contiene la lógica de negocio (ETL). Separar el código de la configuración es vital.
*   `sql/`: Scripts de definición de datos (DDL). Permite versionar el esquema de la base de datos.
*   `tests/`: Suite de pruebas. Un pipeline sin tests no es apto para producción.
*   `docs/`: Documentación técnica y seguimiento de issues (Transparencia).

## 2. Infraestructura: Docker & Docker Compose
*   **Docker (`Dockerfile`):** Crea un entorno aislado y reproducible para el pipeline. Usamos `python:3.11-slim` para mantener la imagen ligera y segura.
*   **Docker Compose:** Orquesta dos servicios independientes:
    *   `db` (PostgreSQL): El almacenamiento persistente.
    *   `pipeline` (Python): La lógica que procesa los datos.
*   **Separación de Servicios:** Permite escalar el pipeline independientemente de la base de datos y asegura que cada componente tenga una única responsabilidad.

## 3. Librerías Core (El Motor)
*   **Requests:** Para consumo de APIs REST. Es el estándar de la industria por su simplicidad y potencia.
*   **Pandas:** La herramienta definitiva para manipulación de datos en Python. Ideal para limpieza, tipado y transformaciones rápidas en memoria.
*   **SQLAlchemy:** Un ORM (Object Relational Mapper) que nos permite interactuar con la base de datos de forma agnóstica al motor SQL, facilitando la mantenibilidad.
*   **psycopg2-binary:** El driver necesario para que Python hable con PostgreSQL.

## 4. Librerías Senior (Robustez y Calidad)
Aquí es donde el proyecto se diferencia de uno junior:

### 🛠️ Robustez: `tenacity`
En el mundo real, las APIs fallan o tienen límites (Rate Limits). 
*   **Uso:** Implementamos *Exponential Backoff*. Si la API nos bloquea, el pipeline no falla inmediatamente; espera un tiempo que aumenta exponencialmente antes de reintentar. 
*   **Valor:** Asegura que el proceso termine exitosamente incluso bajo condiciones de red inestables.

### ✅ Calidad de Datos: `pydantic`
No basta con traer datos; hay que asegurar que sean correctos.
*   **Uso:** Definimos esquemas (Models) que validan que el precio sea un número, que el ID no esté vacío, etc.
*   **Valor:** Detecta errores de esquema de la API antes de que lleguen a la base de datos (Data Contract).

### 🧪 Confianza: `pytest`
*   **Uso:** Automatizamos pruebas para la lógica de transformación.
*   **Valor:** Permite hacer cambios en el código con la seguridad de que no romperemos funcionalidades existentes (Regresión).

### ✨ Estética y Estándares: `black` & `flake8`
*   **Uso:** `black` formatea el código automáticamente y `flake8` busca errores de estilo.
*   **Valor:** Garantiza que el código sea legible y siga las PEP 8 (estándares oficiales de Python), facilitando la revisión de código por otros ingenieros.

---
*Este proyecto prioriza la robustez y la integridad de los datos sobre la complejidad innecesaria.*
