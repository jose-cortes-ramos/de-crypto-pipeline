# Architecture Decisions & Technical Stack 🏗️

Este documento explica las decisiones técnicas tomadas en el proyecto **De-Crypto Pipeline**, justificando cada componente desde una perspectiva de **Senior Data Engineering**.

## 1. Estructura del Proyecto
Un proyecto profesional debe estar organizado para ser escalable y mantenible:
*   `src/`: Contiene la lógica de negocio (ETL). Separar el código de la configuración es vital.
*   `sql/`: Scripts de definición de datos (DDL). Permite versionar el esquema de la base de datos.
*   `tests/`: Suite de pruebas. Un pipeline sin tests no es apto para producción.
*   `docs/`: Documentación técnica y seguimiento de issues (Transparencia).

## 1.1 Refactorización: Evolución de Script a Arquitectura Modular (Issue 2) 🏗️
Durante el desarrollo del **Issue 2 (Extracción)**, se tomó la decisión de evolucionar el código de un script lineal hacia una **arquitectura modular orientada a objetos (OOP)** por las siguientes razones de ingeniería senior:
*   **Separación de Responsabilidades (SoC):** Desacoplamos la configuración (`config.py`), la validación de contratos de datos (`schemas.py`) y la lógica de consumo de API (`extractors.py`). Esto asegura que cada componente tenga una única responsabilidad.
*   **Eliminación de Hardcoding:** Centralizamos parámetros como URLs, límites de tasa y credenciales en una clase de configuración, permitiendo cambiar el comportamiento del pipeline sin modificar el código fuente.
*   **Robustez y Observabilidad:** La modularización permite integrar `tenacity` para reintentos automáticos y logging estructurado de manera más limpia, facilitando el monitoreo del rendimiento de la API.

## 2. Infraestructura: Docker & Docker Compose
*   **Docker (`Dockerfile`):** Crea un entorno aislado y reproducible para el pipeline. Usamos `python:3.11-slim` para mantener la imagen ligera y segura.
*   **Docker Compose:** Orquesta dos servicios independientes:
    *   `db` (PostgreSQL): El almacenamiento persistente.
    *   `pipeline` (Python): La lógica que procesa los datos.
*   **Separación de Servicios:** Permite escalar el pipeline independientemente de la base de datos y asegura que cada componente tenga una única responsabilidad.

## 2.1 Optimización de Base de Datos (Time-Series) 📈
Como este es un pipeline de precios históricos, la base de datos se ha optimizado para consultas de **Series Temporales**:
*   **Primary Key Compuesta `(id, extracted_at)`:** Garantiza la integridad referencial y evita duplicados en el mismo timestamp, permitiendo una partición lógica natural.
*   **Índice en `extracted_at`:** Vital para reportes cronológicos y filtros de tiempo (ej. "Precios de la última hora").
*   **Índice Compuesto `(symbol, extracted_at DESC)`:** Optimizado para la consulta más frecuente en cripto: "Dame el historial de precio de BTC ordenado del más reciente al más antiguo". Esto reduce el costo de escaneo de la tabla de O(N) a O(log N).

## 2.2 Estrategia de Contenerización Profesional 🐳
Para asegurar que el pipeline sea reproducible y evite errores de importación comunes en entornos aislados:
*   **Gestión de Módulos (`PYTHONPATH`):** Configuramos `/app` como la raíz del `PYTHONPATH` en Docker Compose, permitiendo que las importaciones absolutas (`from src.xxx`) funcionen sin problemas.
*   **Ejecución de Módulos (`python -m`):** El contenedor lanza el proceso usando `python -m src.main`. Esta es la mejor práctica de Python para asegurar que el orquestador se ejecute dentro del contexto de un paquete, resolviendo dependencias de forma robusta.

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

### 4. Robustez e Integridad de Datos
En un sistema de produccion, la resiliencia y la precision de los datos son requisitos criticos. Las siguientes decisiones aseguran que el pipeline sea confiable y preciso bajo estandares de ingenieria senior.

#### 4.1 Precision Financiera: Uso de Decimal sobre Float
*   **Problema:** Los tipos de datos de punto flotante binario (float en Python y DOUBLE PRECISION en SQL) introducen errores de redondeo inherentes a la representacion binaria de fracciones decimales. En el contexto de criptomonedas con valores de mercado extremadamente bajos, estos errores se acumulan y comprometen la integridad de los reportes financieros.
*   **Decision:** Se implementa el uso estricto de la libreria decimal.Decimal en la capa de transformacion y el tipo de dato NUMERIC(18, 8) en PostgreSQL.
*   **Justificacion Senior:** Garantiza precision aritmetica exacta, un requisito indispensable para cualquier sistema de datos financieros o de intercambio de activos.

#### 4.2 Idempotencia mediante Estrategia de Upsert
*   **Problema:** Un pipeline basado unicamente en la estrategia de adicion (append) carece de re-ejecutabilidad segura. Si un proceso falla parcialmente y se reinicia, los datos ya cargados se duplican, invalidando el analisis historico.
*   **Decision:** Se implementa una logica de carga mediante Upsert (INSERT ... ON CONFLICT (id, extracted_at) DO UPDATE).
*   **Justificacion Senior:** Asegura la idempotencia del pipeline, permitiendo que el proceso se ejecute multiples veces con el mismo resultado final. Esto facilita la recuperacion automatica ante fallos y la ingesta de datos historicos sin riesgo de duplicacion.

#### 4.3 Data Contract: Validacion Schema-on-Read con Pydantic
*   **Problema:** Las APIs externas representan fuentes de datos no confiables cuyos esquemas pueden cambiar sin previo aviso. Permitir que datos con esquemas incorrectos lleguen a la base de datos genera fallos costosos de depurar.
*   **Decision:** Se establece Pydantic como un firewall de validacion de contratos de datos (Data Contracts) inmediatamente despues de la extraccion.
*   **Justificacion Senior:** Implementa una estrategia de Fail-Fast y mejora la observabilidad del sistema. Las inconsistencias se detectan en la etapa de ingestion, evitando que datos corruptos afecten la integridad del Data Warehouse.

#### 4.4 Gestion Resiliente de Conexiones: Connection Pooling
*   **Problema:** Abrir y cerrar conexiones a la base de datos por cada registro o batch es una operacion costosa que puede agotar los recursos del servidor y aumentar la latencia del pipeline.
*   **Decision:** Se implementa un pool de conexiones mediante SQLAlchemy (`pool_size`, `max_overflow`), configurado a traves de variables de entorno.
*   **Justificacion Senior:** Optimiza el uso de recursos y mejora la capacidad del pipeline para manejar cargas concurrentes. Asegura que el sistema sea escalable y que las conexiones se reutilicen de manera eficiente, evitando el overhead de negociacion de red en cada carga.

#### 4.5 Transacciones Atomicas (Cumplimiento ACID)
*   **Problema:** Una falla durante la ingesta de un batch de datos puede dejar la base de datos en un estado inconsistente (carga parcial), dificultando la auditoria y el re-procesamiento.
*   **Decision:** Se utiliza el gestor de contextos `engine.begin()` de SQLAlchemy para asegurar que toda la operacion de carga ocurra dentro de una transaccion atomica.
*   **Justificacion Senior:** Garantiza que el proceso de carga sea "todo o nada". Si ocurre un error, la transaccion se revierte automaticamente (rollback), manteniendo la integridad referencial y estructural del Data Warehouse en todo momento.

#### 4.6 Verificacion de Calidad Post-Ingesta
*   **Problema:** La confirmacion de exito de la libreria de persistencia no siempre garantiza que los datos en la tabla reflejen exactamente lo procesado en memoria.
*   **Decision:** Se implementa una capa de validacion post-carga que confirma la integridad de la operacion mediante logs de verificacion.
*   **Justificacion Senior:** Cierra el ciclo de confianza del ETL. No solo confiamos en el exito del comando SQL, sino que validamos empiricamente que el estado final de la base de datos es el esperado, elevando el estandar de observabilidad del pipeline.

---
Este proyecto prioriza la robustez y la integridad de los datos sobre la complejidad innecesaria.
