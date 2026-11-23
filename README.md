# YaCarroPredict 🚗📊
> **Proyecto de Ciencia de los Datos** — Universidad Nacional de Colombia (UNAL)  
> **Integrantes:** Esteban Giraldo Ruiz & Diego Aristizabal

---

## 📌 1. Descripción del Proyecto

**YaCarroPredict** es una solución de aprendizaje automático orientada a la estimación y análisis del valor comercial de vehículos usados en el mercado automotor colombiano. A partir de variables objetivas y verificables (marca, modelo, año, kilometraje, transmisión, cilindraje, tipo de combustible, carrocería, ubicación y tipo de vendedor), el sistema es capaz de:

1. **Predecir el precio continuo de mercado en pesos colombianos (COP)** con estimación de intervalos de confianza empíricos.
2. **Clasificar el vehículo en un segmento de mercado** (**BAJO**, **MEDIO**, **ALTO**) de acuerdo con terciles calibrados sobre las publicaciones observadas.

---

## 👥 Autores

- **Esteban Giraldo Ruiz**
- **Diego Aristizabal**

---

## 🚦 2. Estado Actual del Proyecto

| Componente | Estado | Descripción |
|---|:---:|---|
| **Recolección de Datos (Scraping)** | ✅ Completado | Extracción de **20.494 avisos reales** mediante endpoints de la API de Carroya (`Scripts/scraper_carroya.py`). |
| **Limpieza y Auditoría (ETL)** | ✅ Completado | Deduplicación por atributos físicos, corrección de anomalías de dominio y trazabilidad fila a fila (`carroya_auditoria_limpieza.csv`). |
| **Ingeniería de Características** | ✅ Completado | Variables derivadas (`antiguedad`, `km_por_anio`, `marca_modelo`), normalización de texto y codificación One-Hot con manejo de infrecuentes. |
| **Prevención de Data Leakage** | ✅ Completado | Partición previa 70% Train / 15% Val / 15% Test. Todos los transformadores ajustados exclusivamente en entrenamiento. |
| **Entrenamiento de Modelos (x3)** | ✅ Completado | 2 regresores de precio continuo y 1 clasificador multinomial con sintonización de hiperparámetros y validación cruzada. |
| **Persistencia de Pipelines** | ✅ Completado | Exportación de preprocesadores y modelos finales en formato `.joblib`, acompañados de metadatos y opciones de formulario en JSON. |
| **Backend (API REST)** | ⏳ En desarrollo | Estructura base en Flask (`Backend/app.py`). Próxima fase: integración con los modelos `.joblib`. |
| **Frontend (Interfaz de Usuario)** | ⏳ En desarrollo | Maquetación inicial del formulario (`Frontend/index.html`). Próxima fase: conexión dinámica con la API y visualización de resultados. |

---

## 🧠 3. Modelos Entrenados y Desempeño

El preprocesamiento y entrenamiento se diseñó bajo una **fuente única de verdad** (`Scripts/preprocesamiento.py`). Los modelos de regresión se ajustaron sobre la escala logarítmica $\log(1 + \text{precio})$ mediante `TransformedTargetRegressor` para penalizar equitativamente errores relativos y mitigar el sesgo hacia vehículos de gama alta.

### Resumen de Métricas en el Conjunto de Prueba (*Test Set* — 3.056 vehículos)

| Modelo | Tipo | Algoritmo | MAE (Error Medio) | MAPE (%) | $R^2$ / $R^2_{\log}$ | Métrica Clasificación |
|---|---|---|:---:|:---:|:---:|:---:|
| **Modelo 1 (Principal)** | Regresión | **HistGradientBoostingRegressor** | **$9.040.110 COP** | **11,68 %** | 0,862 / **0,920** | Intervalo 80%: $[-16,56\%, +20,47\%]$ (Cobertura: 81,48%) |
| **Modelo 2 (Alternativo)** | Regresión | **RandomForestRegressor** | $12.122.207 COP | 14,79 % | 0,729 / 0,877 | Intervalo 80%: $[-20,03\%, +27,90\%]$ (Cobertura: 81,97%) |
| **Modelo 3 (Segmento)** | Clasificación | **LogisticRegression (Multinomial L2)** | — | — | — | **Accuracy: 85,96 %** <br> F1-Macro: 85,93 % <br> AUC-ROC: 0,959 |

> **Umbrales del Segmento de Mercado:**
> - **BAJO:** Menor a \$43.333.333 COP
> - **MEDIO:** Entre \$43.333.333 COP y \$73.000.000 COP
> - **ALTO:** Mayor a \$73.000.000 COP

---

## 👁️ 4. ¿Cómo Visualizar y Probar lo que Llevamos?

Aunque el frontend definitivo se conectará en la siguiente fase, **todo el trabajo de ciencia de datos, evaluación de modelos e inferencia puede visualizarse e interactuarse inmediatamente** de tres formas:

---

### Opción A: Visualizar los Notebooks Ejecutados (Gráficos, Curvas y Diagnóstico)

Los notebooks en la carpeta `ETL/` contienen todos los resultados, gráficas y tablas ya ejecutadas:

1. **`ETL/Limpieza_Transformacion_Carroya.ipynb`**:
   - Auditoría de datos nulos y valores atípicos (análisis de cilindrajes erróneos y kilometrajes extremos).
   - Justificación empírica de transformaciones (distribuciones antes y después de `log1p`, escalado robusto).
   - Balanceo de clases por cuantiles y comprobación de ausencia de fuga de datos.
2. **`ETL/Entrenamiento_Modelos_Carroya.ipynb`**:
   - Comparación de modelos contra baselines de la mediana.
   - **Gráficos de diagnóstico en prueba:** dispersión de precio real vs. precio predicho, distribución de errores porcentuales y análisis de residuos.
   - **Evaluación de clasificación:** matrices de confusión y curvas ROC multiclase.
   - **Importancia por permutación:** identificación de las variables de mayor impacto en la predicción (`anio`, `kilometraje`, `marca_modelo`).

---

### Opción B: Inferencia Rápida por Consola de Python (Probar los Modelos en Vivo)

Puedes probar los modelos guardados en `models/` ejecutando el siguiente comando en la raíz del repositorio:

```bash
python -c "
import sys; sys.path.append('Scripts')
import joblib, pandas as pd, preprocesamiento

# Cargar los pipelines entrenados
modelo_gb = joblib.load('models/modelo_regresion_gb.joblib')
modelo_clf = joblib.load('models/modelo_clasificacion_segmento.joblib')

# Ejemplo de vehículo a cotizar
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

# Inferencia
precio = modelo_gb.predict(vehiculo)[0]
segmento = modelo_clf.predict(vehiculo)[0]
probabilidades = dict(zip(modelo_clf.classes_, modelo_clf.predict_proba(vehiculo)[0]))

print(f'=== PREDICCIÓN YACARROPREDICT ===')
print(f'Precio Estimado: ${precio:,.0f} COP')
print(f'Rango Confianza (80%): [${precio * 0.8344:,.0f} COP - ${precio * 1.2047:,.0f} COP]')
print(f'Segmento de Mercado: {segmento}')
print(f'Probabilidades: {probabilidades}')
"
```

---

### Opción C: Inspeccionar los Archivos de Metadatos y Auditoría

- **`models/metadatos_modelos.json`**: Registro formal de versiones de librerías, semillas aleatorias, mejores hiperparámetros encontrados en validación cruzada y métricas completas en Train, Val y Test.
- **`models/opciones_formulario.json`**: Listado de marcas, modelos, departamentos y combustibles válidos para autocompletar el frontend.
- **`evidencias/justificacionDecisiones.md`**: Memoria técnica detallada con la justificación de cada regla de negocio, filtros aplicados y alternativas descartadas.
- **`Scripts/data/procesado/carroya_auditoria_limpieza.csv`**: Registro transparente fila a fila de cada corrección aplicada a los datos crudos.

---

## 📁 5. Estructura del Repositorio

```text
YaCarroPredict-ProyectoCLD/
│
├── Backend/                                # Servidor API (Flask / FastAPI)
│   └── app.py                              # Endpoint de predicción (en desarrollo)
│
├── ETL/                                    # Notebooks interactivos de Ciencia de Datos
│   ├── Limpieza_Transformacion_Carroya.ipynb  # Limpieza, auditoría, transformación y partición
│   └── Entrenamiento_Modelos_Carroya.ipynb    # Modelado, validación cruzada, métricas y diagnóstico
│
├── Frontend/                               # Interfaz web cliente
│   ├── index.html                          # Formulario de consulta (en desarrollo)
│   └── api.js                              # Cliente de conexión hacia el Backend
│
├── models/                                 # Artefactos y modelos exportados
│   ├── modelo_regresion_gb.joblib          # Modelo 1: HistGradientBoostingRegressor
│   ├── modelo_regresion_rf.joblib          # Modelo 2: RandomForestRegressor
│   ├── modelo_clasificacion_segmento.joblib# Modelo 3: LogisticRegression (segmentos)
│   ├── preprocesador.joblib                # Pipeline de preprocesamiento ajustado en Train
│   ├── metadatos_modelos.json              # Hiperparámetros, métricas y cortes de segmento
│   └── opciones_formulario.json            # Opciones categóricas para la interfaz de usuario
│
├── Scripts/                                # Módulos reutilizables y datos
│   ├── preprocesamiento.py                 # Lógica compartida de transformación (ETL + Backend)
│   ├── scraper_carroya.py                  # Script de extracción web desde la API de Carroya
│   ├── calidad_datos.py                    # Reglas de validación de calidad de datos
│   └── data/
│       ├── raw/                            # Extracción original (carroya_raw.jsonl)
│       └── procesado/                      # Particiones finales (train, val, test) y auditoría
│
├── evidencias/                             # Justificación metodológica y bitácoras
│   ├── justificacionDecisiones.md          # Justificación técnica de decisiones de limpieza
│   └── evidencias.md                       # Logs de scraping y extracción
│
└── README.md                               # Documentación principal del proyecto
```

---

## 🛠️ 6. Próximos Pasos (Roadmap de Cierre)

1. **Integración Backend:** Reemplazar el controlador provisional en `Backend/app.py` por el consumo real de los modelos guardados (`models/*.joblib`), validando las entradas con `opciones_formulario.json`.
2. **Conexión Frontend:** Vincular los campos de `Frontend/index.html` con las opciones disponibles y mostrar tarjetas de resultados con precio estimado, intervalo y segmento.
3. **Refinamiento de Estilos:** Pulir el diseño visual y la experiencia de usuario (UX/UI) del dashboard final.
