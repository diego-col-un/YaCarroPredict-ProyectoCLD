"""Preprocesamiento compartido del proyecto Carroya.

Este módulo lo usan DOS sitios, para garantizar que el entrenamiento y el
backend transformen los datos exactamente igual:

1. El notebook ETL/Limpieza_Transformacion_Carroya.ipynb (entrenamiento).
2. El backend (FastAPI/Flask), que carga los pipelines guardados con joblib.

Importante: joblib guarda las funciones por referencia (nombre del módulo),
así que este archivo debe poder importarse (``import preprocesamiento``) tanto
al guardar como al cargar los modelos.
"""

import re
import unicodedata

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import MissingIndicator, SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, RobustScaler

# --------------------------------------------------------------------------
# Parámetros de las reglas (documentados en el notebook y en el informe)
# --------------------------------------------------------------------------
ANIO_REFERENCIA = 2026      # año de la extracción; base para calcular antigüedad
KM_MAX = 1_000_000          # por encima es imposible o relleno (9.999.999); entre 500.000 y 1.000.000 se conserva
CILINDRAJE_MIN = 300        # cc mínimos razonables para un automóvil
CILINDRAJE_MAX = 8_000      # cc máximos razonables
LITROS_MAX = 9              # valores enteros 1..9 se interpretan como litros (2 -> 2000 cc)
PRECIO_MIN = 3_000_000      # por debajo no es un precio de venta plausible (COP)
MIN_FRECUENCIA = 30         # categorías con menos avisos se agrupan en "poco frecuentes"
USAR_LOG_NUMERICAS = True   # aplicar log1p a kilometraje y km_por_anio (ver sección 10.3 del notebook)

ETIQUETAS_SEGMENTO = ["BAJO", "MEDIO", "ALTO"]

# --------------------------------------------------------------------------
# Columnas
# --------------------------------------------------------------------------
# Lo que el usuario escribe en el formulario (y lo que recibe el backend)
COLS_ENTRADA = [
    "marca", "modelo", "anio", "kilometraje", "combustible",
    "transmision", "cilindraje", "carroceria", "departamento", "tipo_vendedor",
]
# Columnas de texto categórico que se normalizan
COLS_TEXTO = [
    "marca", "modelo", "combustible", "transmision",
    "carroceria", "departamento", "tipo_vendedor",
]
# Columnas que entran al modelo después de crear variables
NUM_SESGADAS = ["kilometraje", "km_por_anio"]
NUM_SIMPLES = ["antiguedad", "cilindraje"]
CAT_BAJA = ["combustible", "transmision", "carroceria", "tipo_vendedor"]
CAT_ALTA = ["marca", "marca_modelo", "departamento"]
COLS_MODELO = NUM_SESGADAS + NUM_SIMPLES + CAT_BAJA + CAT_ALTA


# --------------------------------------------------------------------------
# Limpieza de texto
# --------------------------------------------------------------------------
def _normalizar_valor(valor):
    """Quita tildes, colapsa espacios y pasa a MAYÚSCULAS. Vacío -> NaN."""
    if pd.isna(valor):
        return np.nan
    texto = unicodedata.normalize("NFKD", str(valor))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"\s+", " ", texto).strip().upper()
    return texto if texto else np.nan


def normalizar_texto(serie):
    """Versión vectorizada de ``_normalizar_valor`` para una Serie de pandas."""
    return serie.map(_normalizar_valor)


# --------------------------------------------------------------------------
# Valores imposibles -> NaN (el registro se conserva)
# --------------------------------------------------------------------------
def sanear_numericos(df, convertir_litros=True):
    """Marca como faltantes los valores numéricos imposibles o dudosos.

    No elimina filas: el valor dudoso pasa a NaN y luego se imputa dentro del
    pipeline (con la mediana del conjunto de entrenamiento).
    Espera que ``combustible`` ya esté normalizado (MAYÚSCULAS, sin tildes).
    """
    df = df.copy()
    anio = pd.to_numeric(df["anio"], errors="coerce")
    km = pd.to_numeric(df["kilometraje"], errors="coerce")
    cc = pd.to_numeric(df["cilindraje"], errors="coerce")
    electrico = normalizar_texto(df["combustible"]).str.contains("ELECTRIC", na=False)

    # Año: año-modelo como máximo un año después de la extracción
    anio = anio.mask((anio < 1900) | (anio > ANIO_REFERENCIA + 1))

    # Kilometraje: negativo y valores imposibles o de relleno (> KM_MAX, p. ej. 9.999.999)
    km = km.mask((km < 0) | (km > KM_MAX))
    # Un usado de hace más de 1 año con 0 km no es creíble
    km = km.mask((km == 0) & (anio < ANIO_REFERENCIA - 1))

    # Cilindraje
    cc = cc.mask(cc < 0)
    pequeno = cc.between(1, LITROS_MAX) & ~electrico
    if convertir_litros:
        cc = cc.where(~pequeno, cc * 1000)       # 2 -> 2000 cc
    else:
        cc = cc.mask(pequeno)
    cc = cc.mask((cc == 0) & ~electrico)         # 0 cc solo es válido en eléctricos
    cc = cc.mask((cc > 0) & (cc < CILINDRAJE_MIN) & ~electrico)
    cc = cc.mask(cc > CILINDRAJE_MAX)
    cc = cc.where(~electrico, 0)                 # un eléctrico no tiene cilindraje

    df["anio"] = anio
    df["kilometraje"] = km
    df["cilindraje"] = cc
    return df


# --------------------------------------------------------------------------
# Variables derivadas (se usa igual en entrenamiento y en el backend)
# --------------------------------------------------------------------------
def crear_variables(df):
    """Normaliza texto, sanea numéricos y crea variables derivadas.

    Recibe las 10 columnas de ``COLS_ENTRADA`` tal como las escribe el usuario
    y devuelve exactamente las columnas de ``COLS_MODELO``.
    """
    df = df.copy()
    for col in COLS_TEXTO:
        df[col] = normalizar_texto(df[col])
    df = sanear_numericos(df)

    df["marca_modelo"] = df["marca"].str.cat(df["modelo"], sep=" ")
    antiguedad = (ANIO_REFERENCIA - df["anio"]).clip(lower=0)
    df["antiguedad"] = antiguedad
    df["km_por_anio"] = df["kilometraje"] / antiguedad.clip(lower=1)
    return df[COLS_MODELO]


# --------------------------------------------------------------------------
# Transformadores (se ajustan SOLO con entrenamiento)
# --------------------------------------------------------------------------
def construir_preprocesador():
    """ColumnTransformer: imputación, indicadores de faltante, log, escalado y one-hot."""
    pasos_sesgadas = [("imputar", SimpleImputer(strategy="median"))]
    if USAR_LOG_NUMERICAS:
        pasos_sesgadas.append(("log", FunctionTransformer(np.log1p, feature_names_out="one-to-one")))
    pasos_sesgadas.append(("escalar", RobustScaler()))
    sesgadas = Pipeline(pasos_sesgadas)
    simples = Pipeline([
        ("imputar", SimpleImputer(strategy="median")),
        ("escalar", RobustScaler()),
    ])
    categoricas = Pipeline([
        ("imputar", SimpleImputer(strategy="constant", fill_value="NO INFORMADO")),
        ("onehot", OneHotEncoder(
            handle_unknown="infrequent_if_exist",
            min_frequency=MIN_FRECUENCIA,
            sparse_output=False,
        )),
    ])
    return ColumnTransformer([
        ("faltante", MissingIndicator(features="all"), ["kilometraje", "cilindraje"]),
        ("num_sesgadas", sesgadas, NUM_SESGADAS),
        ("num_simples", simples, NUM_SIMPLES),
        ("categoricas", categoricas, CAT_BAJA + CAT_ALTA),
    ])


def construir_pipeline_preprocesamiento():
    """Pipeline completo: de las 10 entradas crudas a la matriz numérica del modelo."""
    return Pipeline([
        ("variables", FunctionTransformer(crear_variables, validate=False)),
        ("transformador", construir_preprocesador()),
    ])


# --------------------------------------------------------------------------
# Auxiliares para el objetivo
# --------------------------------------------------------------------------
def asignar_segmento(precio, cortes):
    """BAJO / MEDIO / ALTO con los cortes (terciles) calculados en entrenamiento."""
    return pd.cut(
        precio,
        bins=[-np.inf, cortes[0], cortes[1], np.inf],
        labels=ETIQUETAS_SEGMENTO,
    ).astype(str)


def a_pesos(prediccion_log):
    """Revierte log1p: de la predicción del modelo al precio en pesos."""
    return np.expm1(prediccion_log)
