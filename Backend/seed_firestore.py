"""Script de Seed para poblar Firebase Firestore con cotizaciones iniciales realistas.

Permite que las estadísticas en vivo (KPIs, gráficos de barras y dona,
y tabla de recientes) se visualicen de inmediato con datos verídicos del mercado.
"""

from datetime import datetime, timedelta, timezone
import json
import os
import random
import sys
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(BASE_DIR, "Scripts")
MODELS_DIR = os.path.join(BASE_DIR, "models")
KEY_PATH = os.path.join(os.path.dirname(__file__), "serviceAccountKey.json")

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import joblib
import preprocesamiento
import firebase_admin
from firebase_admin import credentials, firestore

def main():
    print("=== YA CARRO PREDICT — SEED FIRESTORE ===")
    
    # 1. Conexión a Firebase
    if not os.path.exists(KEY_PATH):
        print(f"ERROR: No se encontró el archivo de credenciales en: {KEY_PATH}")
        sys.exit(1)

    if not firebase_admin._apps:
        cred = credentials.Certificate(KEY_PATH)
        firebase_admin.initialize_app(cred)

    db = firestore.client()
    print("✅ Conectado a Firestore.")

    # 2. Cargar modelos para predecir sobre datos de prueba reales
    print("Cargando modelos ML...")
    modelo_gb = joblib.load(os.path.join(MODELS_DIR, "modelo_regresion_gb.joblib"))
    modelo_rf = joblib.load(os.path.join(MODELS_DIR, "modelo_regresion_rf.joblib"))
    modelo_clf = joblib.load(os.path.join(MODELS_DIR, "modelo_clasificacion_segmento.joblib"))

    # 3. Cargar muestra del conjunto de prueba
    test_csv_path = os.path.join(SCRIPTS_DIR, "data", "procesado", "carroya_test.csv")
    df_test = pd.read_csv(test_csv_path)

    # Seleccionar 25 vehículos representativos y variados (populares en Colombia)
    marcas_populares = ["CHEVROLET", "RENAULT", "TOYOTA", "MAZDA", "KIA", "NISSAN", "VOLKSWAGEN", "FORD"]
    muestra = df_test[df_test["marca"].isin(marcas_populares)].sample(n=25, random_state=42)

    columnas_entrada = [
        "marca", "modelo", "anio", "kilometraje", "combustible",
        "transmision", "cilindraje", "carroceria", "departamento", "tipo_vendedor"
    ]

    print(f"Insertando 25 cotizaciones simuladas en la colección 'predicciones'...")
    coleccion = db.collection("predicciones")

    now = datetime.now(timezone.utc)
    batch = db.batch()

    for idx, (_, row) in enumerate(muestra.iterrows()):
        registro = {col: row[col] for col in columnas_entrada}
        registro["anio"] = int(registro["anio"])
        registro["kilometraje"] = float(registro["kilometraje"])
        registro["cilindraje"] = float(registro["cilindraje"])

        df_fila = pd.DataFrame([registro])
        precio_gb = max(0.0, float(modelo_gb.predict(df_fila)[0]))
        precio_rf = max(0.0, float(modelo_rf.predict(df_fila)[0]))
        segmento = str(modelo_clf.predict(df_fila)[0])

        # Distribuir timestamps en las últimas 48 horas para realismo
        horas_atras = random.uniform(0.1, 48.0)
        timestamp = (now - timedelta(hours=horas_atras)).isoformat()

        doc_data = {
            **registro,
            "precio_gb": round(precio_gb),
            "precio_rf": round(precio_rf),
            "segmento": segmento,
            "timestamp": timestamp
        }

        doc_ref = coleccion.document()
        batch.set(doc_ref, doc_data)
        print(f" [{idx+1:02d}/25] {registro['marca']} {registro['modelo']} {registro['anio']} -> ${round(precio_gb):,} COP ({segmento})")

    # Ejecutar guardado por lote
    batch.commit()
    print("\n🎉 ¡Seed completado con éxito! Se han registrado 25 cotizaciones en Firestore.")
    print("Recarga tu aplicación en Render o local para ver los KPIs y gráficos activos.")

if __name__ == "__main__":
    main()
