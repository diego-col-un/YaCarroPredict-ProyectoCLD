import pandas as pd
import numpy as np
from scipy import stats

# ==========================================
# CONFIGURACIÓN DE RUTA
# ==========================================
file_path = r'C:\Users\diego\Documents\UNAL-26-2\Ciencia de Los Datos\Proyecto\Scripts\data\carroya_dataset.csv'

def quality_control_audit(path):
    print("🚀 Iniciando Auditoría de Control de Calidad...\n")
    
    try:
        # Cargar dataset
        df = pd.read_csv(path)
        print(f"✅ Archivo cargado exitosamente. Dimensiones: {df.shape[0]} filas x {df.shape[1]} columnas.\n")
    except Exception as e:
        print(f"❌ Error al cargar el archivo: {e}")
        return

    report = []

    # 1. VALORES NULOS O VACÍOS
    print("🔍 Analizando valores nulos...")
    nulls = df.isnull().sum()
    nulls_pct = (nulls / len(df)) * 100
    null_df = pd.concat([nulls, nulls_pct], axis=1, keys=['Total Nulos', '%'])
    null_issues = null_df[null_df['Total Nulos'] > 0]
    if not null_issues.empty:
        report.append(f"VALORES NULOS:\n{null_issues}")
    else:
        report.append("VALORES NULOS: No se encontraron valores nulos.")

    # 2. REGISTROS DUPLICADOS
    print("🔍 Analizando duplicados...")
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        report.append(f"DUPLICADOS: Se encontraron {duplicates} registros duplicados completos.")
    else:
        report.append("DUPLICADOS: No se encontraron registros duplicados.")

    # 3. OUTLIERS (Valores Atípicos Numéricos)
    print("🔍 Analizando outliers (Método Z-Score)...")
    num_cols = df.select_dtypes(include=[np.number]).columns
    outliers_found = {}
    for col in num_cols:
        z_scores = np.abs(stats.zscore(df[col].dropna()))
        outliers = np.where(z_scores > 3)[0] # Umbral estándar de 3 desviaciones estándar
        if len(outliers) > 0:
            outliers_found[col] = len(outliers)
    
    if outliers_found:
        report.append(f"OUTLIERS: Valores atípicos detectados (Z-score > 3):\n{outliers_found}")
    else:
        report.append("OUTLIERS: No se detectaron valores atípicos significativos.")

    # 4. INCONSISTENCIAS DE FORMATO
    print("🔍 Analizando formatos...")
    format_issues = []
    for col in df.columns:
        # Detectar si una columna numérica tiene strings (mezcla de tipos)
        if df[col].dtype == 'object':
            # Intentar detectar si es una fecha mal formateada
            try:
                pd.to_datetime(df[col])
            except:
                pass # No es fecha
    
    report.append("FORMATOS: Se recomienda revisar columnas 'object' para asegurar que no haya mezclas de tipos de datos.")

    # 5. INCOHERENCIAS LÓGICAS (Reglas generales)
    print("🔍 Analizando incoherencias lógicas...")
    logic_issues = []
    
    # Ejemplo: Precios negativos
    price_cols = [col for col in df.columns if 'precio' in col.lower() or 'price' in col.lower()]
    for col in price_cols:
        if (df[col] < 0).any():
            logic_issues.append(f"Columna {col}: Contiene valores negativos.")

    # Ejemplo: Edades irreales (si existe columna edad o año)
    year_cols = [col for col in df.columns if 'año' in col.lower() or 'year' in col.lower()]
    for col in year_cols:
        # Asumimos que un carro no puede ser del año 1000 ni del 2100
        if (df[col] < 1900).any() or (df[col] > 2025).any():
            logic_issues.append(f"Columna {col}: Contiene años fuera de rango lógico (1900-2025).")

    if logic_issues:
        report.append(f"INCOHERENCIAS LÓGICAS:\n" + "\n".join(logic_issues))
    else:
        report.append("INCOHERENCIAS LÓGICAS: No se detectaron errores lógicos básicos.")

    # ==========================================
    # IMPRESIÓN DEL REPORTE FINAL
    # ==========================================
    print("\n" + "="*50)
    print("📋 REPORTE DE CONTROL DE CALIDAD")
    print("="*50)
    for item in report:
        print(f"\n{item}")
    print("\n" + "="*50)

# Ejecutar el análisis
quality_control_audit(file_path)
