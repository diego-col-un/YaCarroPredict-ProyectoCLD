# YaCarroPredict 🚗📊
> **Proyecto de Ciencia de los Datos** — Universidad Nacional de Colombia (UNAL)  
> **Integrantes:** Esteban Giraldo Ruiz & Diego Aristizabal

---

## 📌 1. Descripción del Proyecto

**YaCarroPredict** es una plataforma integral de analítica y aprendizaje automático orientada a la estimación y diagnóstico del valor comercial de vehículos usados en el mercado automotor colombiano. A partir de variables objetivas y verificables (marca, modelo, año, kilometraje, transmisión, cilindraje, tipo de combustible, carrocería, ubicación y tipo de vendedor), el sistema es capaz de:

1. **Predecir el precio continuo de mercado en pesos colombianos (COP)** con estimación de intervalos de confianza empíricos al 80%.
2. **Clasificar el vehículo en su segmento de mercado** (**BAJO**, **MEDIO**, **ALTO**) según terciles empíricos calculados en entrenamiento.
3. **Persistir y auditar cada cotización en tiempo real** mediante una base de datos NoSQL documental en la nube (Google Cloud Firestore).
4. **Visualizar métricas del mercado en vivo** a través de un dashboard con KPIs analíticos, gráficos dinámicos con Chart.js y registro de consultas recientes.

---

## 👥 Autores

- **Esteban Giraldo Ruiz**
- **Diego Aristizabal**

---

## 🛠️ 2. Arquitectura y Stack Tecnológico

```
┌────────────────────────────────────────────────────────────────────────┐
│                   CLIENTE (Frontend Web Responsivo)                    │
│   Bootstrap 5.3  ·  Bootstrap Icons  ·  Chart.js 4  ·  Vanilla JS      │
│   • Formulario reactivo (Filtro dinámico Marca → Modelo)               │
│   • Tarjeta de predicción con intervalo de confianza al 80%            │
│   • Dashboard de KPIs y gráficas en tiempo real (Barras + Dona)        │
│   • Historial de cotizaciones recientes                                │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ HTTP REST (JSON)
┌───────────────────────────────────▼────────────────────────────────────┐
│                       SERVIDOR (Backend API)                           │
│   Flask  ·  Flask-CORS  ·  Python 3.11                                 │
│   • Preprocesador único compartido (Scripts/preprocesamiento.py)       │
│   • Endpoints: /api/opciones, /api/prediccion, /api/estadisticas       │
└───────────────────▲────────────────────────────────▲───────────────────┘
                    │                                │
┌───────────────────▼───────────────────┐  ┌─────────▼───────────────────┐
│     ARTEFACTOS DE MACHINE LEARNING    │  │    BASE DE DATOS EN LA NUBE │
│   • HistGradientBoosting (Principal)  │  │   Google Cloud Firestore    │
│   • RandomForest (Alternativo)        │  │   (Firebase NoSQL)          │
│   • LogisticRegression (Segmentos)    │  │   • Colección 'predicciones'│
│   • TransformedTargetRegressor (log1p)│  │   • Auditoría de cotizaciones│
│   • Preprocesador ajustado (Joblib)   │  │   • KPIs agregados en vivo  │
└───────────────────────────────────────┘  └─────────────────────────────┘
```

| Capa | Tecnología | Justificación |
|---|---|---|
| **Modelado ML** | `scikit-learn`, `joblib`, `pandas`, `numpy` | Pipelines serializados con inferencia en memoria (< 20 ms). |
| **Backend API** | `Flask`, `Flask-CORS` | Servidor liviano acoplado al runtime de Python, sin sobrecarga monolítica. |
| **Persistencia** | `Firebase Firestore` (`firebase-admin`) | NoSQL Serverless en la nube: resistente a reinicios de contenedores, sin costo fijo. |
| **Frontend UI** | `Bootstrap 5.3`, `Chart.js 4` (CDN) | Sin dependencias de compilación (`npm`), 100% responsivo y visualmente profesional. |

---

## 🚦 3. Estado de Componentes del Proyecto

| Componente | Estado | Detalle |
|---|:---:|---|
| **Extracción de Datos (Scraping)** | ✅ Completado | **20.494 avisos reales** extraídos de la API de Carroya (`Scripts/scraper_carroya.py`). |
| **Limpieza y Auditoría (ETL)** | ✅ Completado | Deduplicación física, saneamiento de cilindrajes y kilometrajes (`carroya_auditoria_limpieza.csv`). |
| **Ingeniería de Características** | ✅ Completado | Creación de `antiguedad`, `km_por_anio`, `marca_modelo` y One-Hot con agrupación de raras. |
| **Prevención de Data Leakage** | ✅ Completado | Partición previa 70% Train / 15% Val / 15% Test. Ajuste exclusivo en entrenamiento. |
| **Entrenamiento de Modelos (x3)** | ✅ Completado | 2 regresores continuos y 1 clasificador de segmentos con hiperparámetros óptimos. |
| **Persistencia en la Nube (BD)** | ✅ Completado | Integración con **Firebase Firestore** para auditar cada predicción y servir KPIs. |
| **Backend API (Flask)** | ✅ Completado | Endpoints `/api/opciones`, `/api/prediccion`, `/api/estadisticas` y `/api/recientes`. |
| **Frontend Profesional** | ✅ Completado | UI con Hero section, formulario dinámico, gráficos Chart.js y tabla de historial. |

---

## 🧠 4. Modelos Entrenados y Desempeño

El preprocesamiento y entrenamiento se rigen por una **fuente única de verdad** ([Scripts/preprocesamiento.py](file:///c:/Users/diego/Documents/UNAL-26-2/Ciencia%20de%20Los%20Datos/Proyecto/YaCarroPredict-ProyectoCLD/Scripts/preprocesamiento.py)). Los modelos de regresión se entrenaron sobre la escala $\log(1 + \text{precio})$ mediante `TransformedTargetRegressor` para penalizar proporcionalmente el error relativo y controlar la asimetría del mercado.

### Resultados en la Partición de Prueba Independiente (*Test Set* — 3.056 vehículos)

| Modelo | Tipo | Algoritmo | MAE (COP) | MAPE (%) | $R^2$ / $R^2_{\log}$ | Métrica de Clasificación / Intervalo |
|---|---|---|:---:|:---:|:---:|:---:|
| **Modelo 1 (Principal)** | Regresión | **HistGradientBoostingRegressor** | **$9.040.110** | **11,68 %** | 0,862 / **0,920** | Intervalo 80%: $[-16,56\%, +20,47\%]$ (Cobertura: 81,48%) |
| **Modelo 2 (Alternativo)** | Regresión | **RandomForestRegressor** | $12.122.207 | 14,79 % | 0,729 / 0,877 | Intervalo 80%: $[-20,03\%, +27,90\%]$ (Cobertura: 81,97%) |
| **Modelo 3 (Segmento)** | Clasificación | **LogisticRegression (Multinomial L2)** | — | — | — | **Accuracy: 85,96 %** <br> F1-Macro: 85,93 % <br> AUC-ROC: 0,959 |

> **Cortes de Segmento de Mercado (Terciles en Entrenamiento):**
> - **BAJO:** Menor a \$43.333.333 COP
> - **MEDIO:** Entre \$43.333.333 COP y \$73.000.000 COP
> - **ALTO:** Mayor a \$73.000.000 COP

---

## 🚀 5. ¿Cómo Ejecutar y Visualizar el Proyecto?

### Opción A: Aplicación Web Completa (Backend Flask + Firestore + UI)

1. **Instalar dependencias:**
   ```bash
   pip install flask flask-cors pandas scikit-learn joblib firebase-admin
   ```

2. **Configurar Firebase (Opcional pero recomendado para persistencia):**
   - Coloca tu archivo `serviceAccountKey.json` en la carpeta `Backend/`.
   - *Nota:* Si no se suministra la clave, el sistema arranca igualmente en modo contingencia: realiza todas las predicciones ML pero omite el guardado en la nube.

3. **Iniciar el servidor Flask:**
   ```bash
   python Backend/app.py
   ```

4. **Acceder en el navegador:**
   - Abre [http://localhost:5000](http://localhost:5000).
   - Disfruta de la cotización reactiva en tiempo real, consulta de estadísticas y gráficos automáticos.

---

### Opción B: Inferencia Rápida por Consola de Python

Puedes probar la inferencia directa de los modelos entrenados con el siguiente comando en la raíz del repositorio:

```bash
python -c "
import sys; sys.path.append('Scripts')
import joblib, pandas as pd, preprocesamiento

modelo_gb = joblib.load('models/modelo_regresion_gb.joblib')
modelo_clf = joblib.load('models/modelo_clasificacion_segmento.joblib')

vehiculo = pd.DataFrame([{
    'marca': 'CHEVROLET',
    'modelo': 'ONIX',
    'anio': 2021,
    'kilometraje': 35000,
    'combustible': 'GASOLINA',
    'transmision': 'MECANICA',
    'cilindraje': 1000,
    'carroceria': 'HATCHBACK',
    'departamento': 'BOGOTA D.C.',
    'tipo_vendedor': 'CONCESIONARIO'
}])

precio = modelo_gb.predict(vehiculo)[0]
segmento = modelo_clf.predict(vehiculo)[0]
probas = dict(zip(modelo_clf.classes_, [round(p, 3) for p in modelo_clf.predict_proba(vehiculo)[0]]))

print(f'Precio Estimado: ${precio:,.0f} COP')
print(f'Intervalo 80%: [${precio * 0.8344:,.0f} COP - ${precio * 1.2047:,.0f} COP]')
print(f'Segmento: {segmento} | Probabilidades: {probas}')
"
```

---

### Opción C: Visualización de Notebooks de Investigación (EDA, Curvas y Diagnóstico)

Los notebooks en la carpeta `ETL/` contienen todos los gráficos ya renderizados:
- **`ETL/Limpieza_Transformacion_Carroya.ipynb`**: Distribuciones, comparaciones de transformaciones y matriz de correlación.
- **`ETL/Entrenamiento_Modelos_Carroya.ipynb`**: Gráficos de dispersión real vs. predicho, distribución de residuos, curvas ROC multiclase e importancia de variables por permutación.

---

## 🌐 6. Guía de Despliegue Gratuito en la Nube

Para publicar el proyecto en internet de forma **100% gratuita**, permanente y profesional, la mejor opción recomendada es **Render**:

### ¿Por qué Render (Web Service Free Tier)?
1. **Soporte nativo de Python:** Detecta automáticamente `requirements.txt` y ejecuta servidores WSGI como `gunicorn`.
2. **Certificado SSL automático (HTTPS):** Dominio seguro gratuito `https://yacarropredict.onrender.com`.
3. **Despliegue continuo con GitHub:** Cada `git push` a la rama principal actualiza la aplicación.
4. **Compatible con Firebase:** Puedes almacenar la clave privada de Firebase de forma segura como variable de entorno secreta.

### Pasos para Desplegar en Render:
1. Sube tu código a GitHub (asegúrate de que `serviceAccountKey.json` esté en `.gitignore`).
2. Entra a [render.com](https://render.com) e inicia sesión con GitHub.
3. Haz clic en **New +** → **Web Service** y selecciona tu repositorio.
4. Configura los parámetros básicos:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn Backend.app:app`
5. **Configuración de la clave de Firebase:**
   - En la pestaña **Environment Variables**, crea una variable llamada `FIREBASE_KEY_BASE64` o añade un archivo secreto (**Secret File**) con la ruta `Backend/serviceAccountKey.json` copiando el contenido de tu JSON.
6. Haz clic en **Create Web Service**. ¡Listo! En 2 minutos tu web estará disponible para todo el mundo.

---

## 📁 7. Estructura del Repositorio

```text
YaCarroPredict-ProyectoCLD/
│
├── Backend/                                # Servidor API y persistencia
│   ├── app.py                              # Endpoints REST, integración ML y Firestore
│   └── serviceAccountKey.json              # Credencial privada Firebase (ignorado en git)
│
├── ETL/                                    # Notebooks reproducibles de Ciencia de Datos
│   ├── Limpieza_Transformacion_Carroya.ipynb  # Limpieza, auditoría, transformación y partición
│   └── Entrenamiento_Modelos_Carroya.ipynb    # Entrenamiento, validación cruzada y diagnóstico
│
├── Frontend/                               # Interfaz de usuario (Bootstrap 5.3 + Chart.js)
│   ├── index.html                          # Dashboard, hero, formulario reactivo y tablas
│   └── api.js                              # Consumo asíncrono de API y renderizado de gráficos
│
├── models/                                 # Modelos y metadatos exportados
│   ├── modelo_regresion_gb.joblib          # HistGradientBoostingRegressor (Principal)
│   ├── modelo_regresion_rf.joblib          # RandomForestRegressor (Alternativo)
│   ├── modelo_clasificacion_segmento.joblib# LogisticRegression (Segmentos)
│   ├── preprocesador.joblib                # ColumnTransformer ajustado en Train
│   ├── metadatos_modelos.json              # Métricas, hiperparámetros y cortes de tercil
│   └── opciones_formulario.json            # Catálogo de marcas y modelos para el frontend
│
├── Scripts/                                # Lógica modular reutilizable
│   ├── preprocesamiento.py                 # Transformación unificada (Entrenamiento + API)
│   ├── scraper_carroya.py                  # Extractor de datos desde la API de Carroya
│   ├── calidad_datos.py                    # Reglas de validación y auditoría
│   └── data/
│       ├── raw/                            # Extracción original (carroya_raw.jsonl)
│       └── procesado/                      # Particiones finales (train, val, test) y auditoría
│
├── evidencias/                             # Sustentación técnica formal
│   ├── justificacionDecisiones.md          # Justificación metodológica de datos y arquitectura
│   └── evidencias.md                       # Logs y auditoría de web scraping
│
├── .gitignore                              # Reglas de exclusión (claves, temporales, venv)
├── requirements.txt                        # Lista de dependencias del proyecto
└── README.md                               # Documentación general del proyecto
```
