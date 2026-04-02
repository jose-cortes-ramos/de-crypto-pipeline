# Operations & Deployment Guide 🛠️

Este documento describe los procedimientos para el despliegue, mantenimiento y escalabilidad del **De-Crypto Pipeline** en entornos de producción.

---

## 1. Gestión de Configuración y Secretos

### **A. Archivos .env (Local)**
*   Utilizar `.env.example` como plantilla para configurar las credenciales de PostgreSQL y la API Key de CoinGecko.
*   **Advertencia:** Nunca commitear archivos `.env` reales (incluidos en `.gitignore`).

### **B. Secretos en Producción (Cloud)**
*   Si despliegas en AWS/GCP/Azure, utiliza servicios como **AWS Secrets Manager** o **GitHub Actions Secrets**.
*   **Procedimiento:** Inyectar las variables (`COINGECKO_API_KEY`, `DATABASE_URL`) como variables de entorno directamente en el orquestador de contenedores (ECS, Kubernetes).

---

## 2. Monitoreo y Auditoría

### **A. Análisis de Logs (Observabilidad)**
El pipeline genera logs en formato **JSON**. Para buscar fallas en producción, utiliza filtros sobre los campos:
*   `levelname == "ERROR"`: Identifica fallas críticas de red o base de datos.
*   `levelname == "WARNING"`: Registra problemas de calidad de datos (precios filtrados).
*   `message.contains("Audit")`: Filtra los resultados del loop de verificación de integridad post-carga.

### **B. Healthchecks (Fail-Fast)**
El sistema realiza dos chequeos proactivos antes de iniciar:
1.  **API Check:** Llama a `/ping` de CoinGecko.
2.  **DB Check:** Llama a `SELECT 1` en PostgreSQL.
*   *Acción si falla:* No re-intentar el pipeline completo; verificar primero la infraestructura base (Red/Base de datos).

---

## 3. Estrategia de Escalabilidad

### **A. Escalado de Extracción (Volume)**
El pipeline está configurado para 50 activos por página. Si necesitas escalar a miles de activos:
*   Ajustar `PER_PAGE` en `src/config.py`.
*   Implementar una lógica de **Paginación** en `src/extractors.py`.

### **B. Base de Datos (Time-Series)**
Con el tiempo, la tabla `crypto_prices` crecerá masivamente.
*   **Decisión Senior:** Implementar **Table Partitioning** en PostgreSQL basado en el campo `extracted_at` (por mes o por trimestre).

---

## 4. Mantenimiento del Código (DataOps)

### **A. CI/CD Pipeline**
Cada cambio en el código debe pasar por el flujo de GitHub Actions:
1.  **Linter Check:** Garantiza consistencia visual (Black/Flake8).
2.  **Integration Tests:** Valida la persistencia real contra un PostgreSQL efímero.
3.  **Coverage:** Asegura que el % de cobertura no disminuya.

### **B. Comandos de Calidad Local**
Para asegurar que el CI pase en el primer intento, ejecute estos comandos antes de subir su código:
```bash
# Formateo automático
black .

# Validación de estándares (Debe devolver 0 errores)
flake8 .

# Ejecución de pruebas con cobertura
pytest --cov=src
```

### **C. Pre-commit Hooks**
Instalar los hooks para automatizar la calidad en cada commit:
```bash
pip install pre-commit
pre-commit install
```

---
*Este proyecto está diseñado para ser operado con mínima intervención humana, priorizando la detección temprana de fallas y la integridad absoluta de los datos.*
