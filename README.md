<div align="center">

# 🚗 YaCarroPredict
### Sistema Predictivo de Valoración y Segmentación Comercial de Vehículos Usados en Colombia

[![Python Version](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.3+-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![Firebase](https://img.shields.io/badge/Firebase_Firestore-NoSQL-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)](https://firebase.google.com/)
[![Render](https://img.shields.io/badge/Render-Deployed-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://yacarropredict-proyectocld.onrender.com/)

<br>

**Universidad Nacional de Colombia (UNAL)**  
— *Ciencia de los Datos (2026)* —

🌐 **Aplicación en Vivo:** [https://yacarropredict-proyectocld.onrender.com/#cotizar](https://yacarropredict-proyectocld.onrender.com/#cotizar)

</div>

---

## 👥 Equipo y Autores

| Nombre Completo | Usuario GitHub | Rol en el Proyecto |
|---|---|---|
| **Diego Aristizabal** | [@diego-col-un](https://github.com/diego-col-un) | Ingeniería de Datos, Modelado ML & Despliegue Cloud |
| **Esteban Giraldo Ruiz** | [@esgiraldor-maker](https://github.com/esgiraldor-maker) | Preprocesamiento, Validación Estadística & Frontend |

---

## 📌 1. Descripción del Problema

El mercado automotor de vehículos usados en Colombia se caracteriza por una marcada **asimetría de información** y alta dispersión en precios de oferta. Un comprador o vendedor particular a menudo carece de referencias objetivas para determinar el valor justo de mercado según las características mecánicas, kilometraje y procedencia geográfica.

**YaCarroPredict** resuelve este problema mediante un sistema de aprendizaje automático de extremo a extremo que:
1. **Predice el precio continuo de mercado en pesos colombianos (COP)** con rangos de confianza empíricos al 80%.
2. **Clasifica el vehículo en su segmento comercial** (**BAJO**, **MEDIO**, **ALTO**) según cuantiles empíricos del mercado.
3. **Persiste cada consulta en tiempo real** en una base de datos documental serverless en la nube (Google Cloud Firestore).
4. **Analiza el mercado en vivo** a través de un panel interactivo con KPIs de cotizaciones, top de marcas más buscadas y distribución de segmentos.

---

## 🏗️ 2. Arquitectura de Extremo a Extremo

```
┌────────────────────────────────────────────────────────────────────────┐
│                   CLIENTE (Frontend Web Responsivo)                    │
│   Bootstrap 5.3  ·  Bootstrap Icons  ·  Chart.js 4  ·  Vanilla JS      │
│   • Formulario reactivo con filtrado dinámico Marca → Modelo           │
│   • Tarjeta de predicción con precio, comparativa e intervalo al 80%   │
│   • Dashboard de analítica en tiempo real (Barras + Dona)              │
│   • Historial de cotizaciones recientes en vivo                        │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ HTTP REST (JSON)
┌───────────────────────────────────▼────────────────────────────────────┐
│                       SERVIDOR (Backend API)                           │
│   Flask  ·  Gunicorn  ·  Python 3.11  ·  Render Cloud                  │
│   • Pipeline de transformación compartida (Scripts/preprocesamiento.py)│
│   • Carga en memoria en el arranque (< 20 ms de latencia por inferencia)│
│   • Endpoints: /api/opciones, /api/prediccion, /api/estadisticas       │
└───────────────────▲────────────────────────────────▲───────────────────┘
                    │                                │
┌───────────────────▼───────────────────┐  ┌─────────▼───────────────────┐
│     ARTEFACTOS DE MACHINE LEARNING    │  │    BASE DE DATOS EN LA NUBE │
│   • HistGradientBoosting (Principal)  │  │   Google Cloud Firestore    │
│   • RandomForest (Alternativo)        │  │   (Firebase Admin SDK)      │
│   • LogisticRegression (Segmentos)    │  │   • Colección 'predicciones'│
│   • Target en log1p(precio)           │  │   • Persistencia desacoplada│
│   • ColumnTransformer serializado     │  │   • KPIs y métricas en vivo │
└───────────────────────────────────────┘  └─────────────────────────────┘
```

---

## 📊 3. Datos y Preprocesamiento

* **Fuente:** Publicaciones reales extraídas mediante web scraping estructurado desde la API de **Carroya**.
* **Volumen:** **20.494 avisos únicos** con fecha de corte de noviembre de 2026.
* **Partición sin Fuga de Información (*Data Leakage*):**
  - **Entrenamiento (70%):** 14.261 registros (únicos usados para aprender estadísticas, medianas y categorías).
  - **Validación (15%):** 3.056 registros (usados para sintonizar hiperparámetros y cortes).
  - **Prueba Independiente (15%):** 3.056 registros (evaluación final no vista).
  - Estratificación por deciles de precio.

### Decisiones Clave de Limpieza e Ingeniería:
- **Trazabilidad total:** Se conservaron filas con cilindrajes erróneos (imputados con la mediana de entrenamiento) dejando registro en una bitácora de auditoría (`carroya_auditoria_limpieza.csv`).
- **Variables Derivadas:** `antiguedad` ($2026 - \text{año}$), `km_por_anio` (intensidad de uso) y `marca_modelo` (evita colisión de nombres entre fabricantes).
- **Transformación Logarítmica:** Regresiones entrenadas sobre $\log(1 + \text{precio})$ para estabilizar la varianza residual y optimizar el error relativo porcentual.

---

## 🧠 4. Rendimiento de los Modelos (Evaluación en Prueba)

Métricas calculadas sobre los **3.056 vehículos** del conjunto de prueba independiente:

| Modelo | Algoritmo | Papel | MAE (Error Medio) | MAPE (%) | $R^2_{\log}$ | Métrica Específica |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **Modelo 1** | **HistGradientBoostingRegressor** | **Principal** | **$9.040.110 COP** | **11,68 %** | **0,920** | Intervalo 80%: $[-16,56\%, +20,47\%]$ (Cobertura: 81,48%) |
| **Modelo 2** | **RandomForestRegressor** | **Alternativo** | $12.122.207 COP | 14,79 % | 0,877 | Intervalo 80%: $[-20,03\%, +27,90\%]$ (Cobertura: 81,97%) |
| **Modelo 3** | **LogisticRegression (L2, C=30)** | **Segmento** | — | — | — | **Accuracy: 85,96 %** <br> F1-Macro: 85,93 % <br> AUC-ROC: 0,959 |

> **Segmentos de Mercado Calibrados:**
> - 🟢 **BAJO:** Menor a \$43.333.333 COP
> - 🟡 **MEDIO:** Entre \$43.333.333 COP y \$73.000.000 COP
> - 🔴 **ALTO:** Mayor a \$73.000.000 COP

---

## 🚀 5. Despliegue y Acceso

### Enlace Oficial en la Nube
El sistema se encuentra desplegado de forma continua en **Render** conectado a la base de datos **Firebase Firestore**:
👉 **[https://yacarropredict-proyectocld.onrender.com/#cotizar](https://yacarropredict-proyectocld.onrender.com/#cotizar)**

*(El servicio cuenta con monitoreo activo para garantizar disponibilidad instantánea).*

---

### Ejecución Local

Si deseas clonar y ejecutar el entorno en tu máquina local:

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/diego-col-un/YaCarroPredict-ProyectoCLD.git
   cd YaCarroPredict-ProyectoCLD
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar el servidor:**
   ```bash
   python Backend/app.py
   ```

4. **Abrir en el navegador:**
   Ingresa a [http://localhost:5000](http://localhost:5000).

---

## 📁 6. Estructura del Repositorio

```text
YaCarroPredict-ProyectoCLD/
│
├── Backend/                                # Servidor API y controladores
│   ├── app.py                              # Endpoints REST, inferencia ML y Firestore
│   ├── seed_firestore.py                   # Script de inicialización de datos de prueba
│   └── serviceAccountKey.json              # Credencial privada Firebase (ignorado en git)
│
├── ETL/                                    # Notebooks reproducibles de investigación
│   ├── Limpieza_Transformacion_Carroya.ipynb  # Limpieza, auditoría y partición 70/15/15
│   └── Entrenamiento_Modelos_Carroya.ipynb    # Modelado, curvas de aprendizaje y diagnóstico
│
├── Frontend/                               # Aplicación web cliente (Bootstrap 5.3 + Chart.js)
│   ├── index.html                          # Dashboard, hero, formulario reactivo y tablas
│   └── api.js                              # Consumo asíncrono y renderizado dinámico
│
├── models/                                 # Artefactos serializados y metadatos
│   ├── modelo_regresion_gb.joblib          # HistGradientBoostingRegressor
│   ├── modelo_regresion_rf.joblib          # RandomForestRegressor
│   ├── modelo_clasificacion_segmento.joblib# LogisticRegression
│   ├── preprocesador.joblib                # ColumnTransformer ajustado
│   ├── metadatos_modelos.json              # Hiperparámetros, métricas y cortes
│   └── opciones_formulario.json            # Opciones de marcas y modelos para la UI
│
├── Scripts/                                # Módulos reutilizables
│   ├── preprocesamiento.py                 # Pipeline único compartido (Train + API)
│   ├── scraper_carroya.py                  # Extractor de datos desde Carroya
│   ├── calidad_datos.py                    # Reglas de validación y auditoría
│   └── data/                               # Almacén de datasets procesados
│
├── evidencias/                             # Sustentación técnica formal
│   ├── justificacionDecisiones.md          # Memoria técnica de decisiones de datos y arquitectura
│   └── evidencias.md                       # Bitácora de extracción web
│
├── .gitignore                              # Exclusión de claves privadas y temporales
├── requirements.txt                        # Dependencias de Python fijadas
└── README.md                               # Documentación principal
```

---

<div align="center">
  <sub>Desarrollado con fines académicos para la asignatura <b>Ciencia de los Datos</b> · Universidad Nacional de Colombia · 2026</sub>
</div>
