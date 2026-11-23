"""Backend API en Flask para YaCarroPredict.

Endpoints:
  GET  /                      → sirve el frontend (index.html)
  GET  /api/health            → estado del servidor
  GET  /api/opciones          → opciones del formulario
  POST /api/prediccion        → inferencia + guarda en Firestore
  GET  /api/estadisticas      → KPIs agregados desde Firestore
  GET  /api/recientes         → últimas N predicciones
"""

import json
import os
import sys
from datetime import datetime, timezone

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import pandas as pd

# ── Rutas del proyecto ──────────────────────────────────────────────────────
BASE_DIR    = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(BASE_DIR, "Scripts")
MODELS_DIR  = os.path.join(BASE_DIR, "models")
FRONTEND_DIR= os.path.join(BASE_DIR, "Frontend")
KEY_PATH    = os.path.join(os.path.dirname(__file__), "serviceAccountKey.json")

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import joblib          # noqa: E402
import preprocesamiento  # noqa: E402  (requerido para deserializar pipelines)

# ── Flask ───────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)

# ── Firebase / Firestore ────────────────────────────────────────────────────
db = None
try:
    import firebase_admin
    from firebase_admin import credentials, firestore

    # Buscar la clave en múltiples ubicaciones (Render monta secretos en /etc/secrets/)
    posibles_rutas = [
        os.path.join(os.path.dirname(__file__), "serviceAccountKey.json"),  # Backend/
        os.path.join(BASE_DIR, "serviceAccountKey.json"),                    # Raíz del repo
        "/etc/secrets/serviceAccountKey.json",                              # Render Secret Files
        os.environ.get("FIREBASE_KEY_PATH", "")                             # Variable opcional
    ]

    cred = None
    # 1. Si existe en variable de entorno como texto JSON directo
    if os.environ.get("FIREBASE_CREDENTIALS_JSON"):
        info_json = json.loads(os.environ["FIREBASE_CREDENTIALS_JSON"])
        cred = credentials.Certificate(info_json)
    else:
        # 2. Buscar en las rutas de archivo
        for ruta in posibles_rutas:
            if ruta and os.path.exists(ruta):
                cred = credentials.Certificate(ruta)
                print(f"[YaCarroPredict] Usando credencial Firebase desde: {ruta}")
                break

    if cred and not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("[YaCarroPredict] ✅ Firestore conectado correctamente.")
    elif not cred:
        print("[YaCarroPredict ⚠️] No se encontró el archivo serviceAccountKey.json en ninguna ruta conocida.")
except Exception as e:
    print(f"[YaCarroPredict ⚠️] Firestore NO disponible: {e}")
    print("  → Las predicciones se realizarán igual, pero no se guardarán.")

# ── Modelos ML ──────────────────────────────────────────────────────────────
print("[YaCarroPredict] Cargando modelos y metadatos...")

modelo_gb  = joblib.load(os.path.join(MODELS_DIR, "modelo_regresion_gb.joblib"))
modelo_rf  = joblib.load(os.path.join(MODELS_DIR, "modelo_regresion_rf.joblib"))
modelo_clf = joblib.load(os.path.join(MODELS_DIR, "modelo_clasificacion_segmento.joblib"))

with open(os.path.join(MODELS_DIR, "metadatos_modelos.json"), encoding="utf-8") as f:
    metadatos = json.load(f)
with open(os.path.join(MODELS_DIR, "opciones_formulario.json"), encoding="utf-8") as f:
    opciones_formulario = json.load(f)

intervalo_gb = metadatos["modelos"]["regresion_gb"]["intervalo_empirico"]
ERR_INF_GB   = intervalo_gb["error_relativo_inferior"]
ERR_SUP_GB   = intervalo_gb["error_relativo_superior"]

print("[YaCarroPredict] ✅ Modelos cargados.")

# ── Helpers ──────────────────────────────────────────────────────────────────
def _fmt_cop(valor: float) -> str:
    return f"${round(valor):,} COP".replace(",", ".")


def _guardar_prediccion(registro: dict, pred: dict) -> None:
    """Guarda un documento en la colección 'predicciones' de Firestore."""
    if db is None:
        return
    try:
        doc = {
            **{k: registro[k] for k in [
                "marca", "modelo", "anio", "kilometraje", "combustible",
                "transmision", "cilindraje", "carroceria", "departamento",
                "tipo_vendedor",
            ]},
            "precio_gb":    pred["precio_estimado"],
            "precio_rf":    pred["modelo_alternativo"]["precio"],
            "segmento":     pred["segmento"],
            "timestamp":    datetime.now(timezone.utc).isoformat(),
        }
        db.collection("predicciones").add(doc)
    except Exception as e:
        print(f"[Firestore ⚠️] Error guardando predicción: {e}")


# ── Endpoints estáticos ──────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)


# ── API ──────────────────────────────────────────────────────────────────────
@app.route("/api/health")
def health():
    return jsonify({
        "estado": "activo",
        "servicio": "YaCarroPredict",
        "firestore": db is not None,
    })


@app.route("/api/opciones")
def obtener_opciones():
    return jsonify(opciones_formulario)


@app.route("/api/prediccion", methods=["POST"])
@app.route("/prediccion", methods=["POST"])
def predecir():
    datos = request.get_json(silent=True)
    if not datos:
        return jsonify({"exito": False, "error": "JSON inválido o vacío."}), 400

    campos = [
        "marca", "modelo", "anio", "kilometraje", "combustible",
        "transmision", "cilindraje", "carroceria", "departamento", "tipo_vendedor",
    ]
    faltantes = [c for c in campos if c not in datos or datos[c] is None]
    if faltantes:
        return jsonify({"exito": False,
                        "error": f"Campos faltantes: {', '.join(faltantes)}"}), 400

    try:
        registro = {
            "marca":        str(datos["marca"]).strip(),
            "modelo":       str(datos["modelo"]).strip(),
            "anio":         int(datos["anio"]),
            "kilometraje":  float(datos["kilometraje"]),
            "combustible":  str(datos["combustible"]).strip(),
            "transmision":  str(datos["transmision"]).strip(),
            "cilindraje":   float(datos["cilindraje"]),
            "carroceria":   str(datos["carroceria"]).strip(),
            "departamento": str(datos["departamento"]).strip(),
            "tipo_vendedor":str(datos["tipo_vendedor"]).strip(),
        }
        df_in = pd.DataFrame([registro])

        precio_gb = max(0.0, float(modelo_gb.predict(df_in)[0]))
        precio_rf = max(0.0, float(modelo_rf.predict(df_in)[0]))
        segmento  = str(modelo_clf.predict(df_in)[0])
        probas    = {c: round(float(p), 4)
                     for c, p in zip(modelo_clf.classes_,
                                     modelo_clf.predict_proba(df_in)[0])}

        pred = {
            "precio_estimado":         round(precio_gb),
            "precio_estimado_formato": _fmt_cop(precio_gb),
            "intervalo_80": {
                "min":        round(max(0.0, precio_gb * (1 + ERR_INF_GB))),
                "max":        round(precio_gb * (1 + ERR_SUP_GB)),
                "min_formato": _fmt_cop(max(0.0, precio_gb * (1 + ERR_INF_GB))),
                "max_formato": _fmt_cop(precio_gb * (1 + ERR_SUP_GB)),
                "nivel": "80%",
            },
            "segmento": segmento,
            "probabilidades_segmento": probas,
            "modelo_alternativo": {
                "nombre":       "RandomForestRegressor",
                "precio":       round(precio_rf),
                "precio_formato": _fmt_cop(precio_rf),
            },
        }

        _guardar_prediccion(registro, pred)

        return jsonify({"exito": True, "prediccion": pred, "vehiculo": registro})

    except Exception as err:
        return jsonify({"exito": False,
                        "error": f"Error en inferencia: {err}"}), 500


@app.route("/api/estadisticas")
def estadisticas():
    """KPIs calculados a partir de los documentos de Firestore."""
    if db is None:
        return jsonify({"disponible": False,
                        "mensaje": "Firestore no conectado"}), 503
    try:
        docs = list(db.collection("predicciones")
                      .order_by("timestamp", direction=firestore.Query.DESCENDING)
                      .limit(500).stream())

        if not docs:
            return jsonify({
                "disponible": True,
                "total": 0,
                "precio_promedio": 0,
                "segmento_frecuente": "—",
                "marcas_top": [],
                "distribucion_segmentos": {"BAJO": 0, "MEDIO": 0, "ALTO": 0},
            })

        registros = [d.to_dict() for d in docs]
        total = len(registros)
        precio_promedio = round(sum(r["precio_gb"] for r in registros) / total)

        segmentos = [r["segmento"] for r in registros]
        seg_frec  = max(set(segmentos), key=segmentos.count)

        from collections import Counter
        marcas_cnt = Counter(r["marca"] for r in registros)
        marcas_top = [{"marca": m, "total": c}
                      for m, c in marcas_cnt.most_common(5)]

        seg_dist = Counter(segmentos)
        distribucion = {
            "BAJO":  seg_dist.get("BAJO",  0),
            "MEDIO": seg_dist.get("MEDIO", 0),
            "ALTO":  seg_dist.get("ALTO",  0),
        }

        return jsonify({
            "disponible":          True,
            "total":               total,
            "precio_promedio":     precio_promedio,
            "precio_promedio_fmt": _fmt_cop(precio_promedio),
            "segmento_frecuente":  seg_frec,
            "marcas_top":          marcas_top,
            "distribucion_segmentos": distribucion,
        })

    except Exception as e:
        return jsonify({"disponible": False, "error": str(e)}), 500


@app.route("/api/recientes")
def recientes():
    """Últimas 8 predicciones almacenadas en Firestore."""
    if db is None:
        return jsonify({"disponible": False, "datos": []}), 503
    try:
        from firebase_admin import firestore as _fs
        docs = list(db.collection("predicciones")
                      .order_by("timestamp", direction=_fs.Query.DESCENDING)
                      .limit(8).stream())
        datos = []
        for d in docs:
            r = d.to_dict()
            datos.append({
                "marca":      r.get("marca", "—"),
                "modelo":     r.get("modelo", "—"),
                "anio":       r.get("anio", "—"),
                "precio_fmt": _fmt_cop(r.get("precio_gb", 0)),
                "segmento":   r.get("segmento", "—"),
                "timestamp":  r.get("timestamp", "—")[:10],
            })
        return jsonify({"disponible": True, "datos": datos})
    except Exception as e:
        return jsonify({"disponible": False, "error": str(e)}), 500


# ── Inicio ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    print(f"[YaCarroPredict] Servidor en http://localhost:{puerto}")
    app.run(host="0.0.0.0", port=puerto, debug=True)
