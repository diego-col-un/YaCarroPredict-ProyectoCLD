# Justificación de las decisiones de limpieza y transformación

Proyecto de Ciencia de los Datos (UNAL) · Dataset Carroya (vehículos usados) · Notebook `Limpieza_Transformacion_Carroya.ipynb` · Módulo `preprocesamiento.py`

## Cómo leer este documento

Cada decisión se explica con cuatro elementos: qué se hizo, qué alternativa se descartó, por qué y qué evidencia la respalda. Sirve de base para la sección 5.2 del informe técnico (decisiones de preprocesamiento).

Las cifras de partida salen de los datos reales (20.494 avisos, extraídos el 4 de noviembre de 2026). Los conteos exactos de cada regla los imprime el notebook al ejecutarse; la sección 8 indica de qué celda sale cada uno para copiarlos al informe.

---

## 1. Principios que guían el proceso

1. **Conservar registros.** Un valor imposible no justifica perder el resto del aviso. Se marca como faltante, se imputa después y se deja constancia de la corrección. Solo se eliminan filas cuando el dato no se puede recuperar (precio imposible) o cuando el aviso está repetido.
2. **Dividir antes de ajustar.** Los imputadores, codificadores y escaladores aprenden estadísticas (medianas, categorías, escalas). Si se ajustan con todos los datos, la prueba influye en el entrenamiento y las métricas salen infladas. Por eso se divide primero y todo se ajusta solo con entrenamiento.
3. **Una sola fuente de verdad.** Las reglas de limpieza y el preprocesador viven en `preprocesamiento.py`, el mismo módulo que cargará el backend. Así los datos nuevos reciben exactamente la misma transformación que los de entrenamiento.
4. **Trazabilidad.** Toda corrección numérica queda registrada con el valor original, el valor final y una bandera por regla en `carroya_auditoria_limpieza.csv`. Las banderas son de auditoría y no entran al modelo.

---

## 2. Resumen de decisiones

| # | Decisión | Alternativa descartada | Razón principal |
|---|---|---|---|
| 1 | Quitar avisos repetidos del mismo vehículo (km > 0), conservando el más reciente | Deduplicar solo por `id` | Una copia en entrenamiento y otra en prueba infla las métricas |
| 2 | Conservar 10 columnas de entrada y el precio | Usar las 34 columnas | Solo se usan variables que el usuario conoce al cotizar |
| 3 | Normalizar texto (sin tildes, mayúsculas, sin espacios dobles) | Mapa de equivalencias aprendido de los datos | Es determinista y el backend lo aplica igual a lo que escriba el usuario |
| 4 | Valores imposibles a `NaN`, sin borrar filas, con auditoría | `dropna()` o cortes IQR que eliminan filas | Se conserva la información del resto del aviso |
| 5 | Eliminar precios menores a 3 millones | Imputar el precio | Imputar el objetivo inventa la respuesta |
| 6 | Entrenar las regresiones con `log(1 + precio)` | Entrenar con el precio en pesos | Distribución muy sesgada; importa el error relativo |
| 7 | Crear `antiguedad`, `km_por_anio` y `marca_modelo` | Usar `anio` y `modelo` tal cual | Más interpretables y sin colisiones entre marcas |
| 8 | División aleatoria 70/15/15 estratificada por deciles de precio | División temporal | Los datos son un corte único, no una serie de tiempo |
| 9 | Segmento de precio con terciles calculados en entrenamiento | Terciles sobre todos los datos | Evita que la prueba defina las clases |
| 10 | No discretizar `antiguedad` | Igual ancho, igual frecuencia o k-means | Los árboles ya buscan sus cortes y la variable continua conserva más información |
| 11 | One-Hot con categorías raras agrupadas (mínimo 30 avisos) | Label, frecuencia o Target Encoding | Conserva la identidad de cada categoría sin imponer orden ni filtrar información |
| 12 | `log1p` más `RobustScaler` en kilometraje y km por año (condicionado a la evidencia) | Escalado estándar | Los extremos que sobreviven a la limpieza no dominan la escala |
| 13 | Imputar con la mediana (numéricas) y `NO INFORMADO` (categóricas), más indicadores de faltante | Eliminar filas con faltantes | La ausencia puede ser informativa y no se pierden registros |

---

## 3. Hallazgos sobre los datos reales que motivan las decisiones

- El archivo tiene **20.494 filas y 34 columnas**, sin `id` repetidos ni precios faltantes.
- Cinco columnas (`negociable`, `unico_dueno`, `tipo_direccion`, `torque`, `potencia`) tienen **94,95 % de nulos**.
- `cilindraje` tiene 580 valores menores o iguales a 0 (565 ceros y 15 negativos) y 169 mayores a 8.000, con máximo de 99.000. Muchos ceros son vehículos eléctricos. **De los 169 valores mayores a 8.000, 35 son idénticos al kilometraje del mismo aviso**, lo que indica un error de extracción (el kilometraje quedó copiado en la columna de cilindraje).
- `kilometraje` tiene 14 ceros, 81 valores mayores a 500.000, 25 mayores a 1.000.000 y 2 iguales a 9.999.999 (valor de relleno).
- 53 avisos tienen un año posterior al de extracción (2027), compatible con año-modelo.
- `precio` va de 308.000 a 1.200 millones de pesos y está muy sesgado a la derecha.
- Al normalizar espacios y mayúsculas, `departamento` pasa de 58 a 43 categorías, `marca` de 89 a 87, `modelo` de 787 a 784 y `version` de 3.404 a 3.375.
- En el análisis de Spearman, `precio` se relaciona con `anio` (0,69) y con `kilometraje` (-0,56).

---

## 4. Las decisiones en detalle

### 4.1 Duplicados

**Qué se hizo.** Se confirma que no hay filas completas ni `id` repetidos, y además se buscan avisos del mismo vehículo con distinto `id` (misma marca, modelo, versión, año, kilometraje, precio, ciudad, color, combustible, transmisión y cilindraje). Se conserva el más reciente según `fecha_publicacion`.

**Por qué.** Un aviso republicado es el mismo carro. Si una copia queda en entrenamiento y otra en prueba, el modelo ya vio ese carro y las métricas salen mejores de lo real.

**Excepción.** Los avisos con kilometraje 0 se conservan: varias unidades nuevas idénticas del mismo concesionario son avisos legítimos distintos.

### 4.2 Selección de columnas

Se conservan `marca`, `modelo`, `anio`, `kilometraje`, `combustible`, `transmision`, `cilindraje`, `carroceria`, `departamento`, `tipo_vendedor` y el objetivo `precio`. El criterio: las entradas del modelo deben coincidir con las que el usuario puede escribir en el formulario del frontend. Se descartan columnas, no filas.

| Grupo | Columnas | Motivo |
|---|---|---|
| Constantes | `fuente`, `moneda`, `fecha_extraccion` | No aportan variación |
| Identificador | `id` | No es un predictor |
| Casi constante | `estado` | Prácticamente todos los avisos son usados |
| Muy nulas | `negociable`, `unico_dueno`, `tipo_direccion`, `torque`, `potencia` | 94,95 % de nulos |
| Atributos del aviso o de la plataforma | `num_fotos`, `destacado`, `fecha_publicacion` | No se conocen al cotizar; los datos son un solo corte |
| Derivadas de la placa | `pico_placa`, `ciudad_placa` | No describen el vehículo |
| Alta cardinalidad o no pedidas | `version`, `ciudad`, `color`, `blindado` | Cientos o miles de categorías, o no se piden en el formulario |
| Texto libre | `titulo`, `descripcion`, `caracteristicas`, `accesorios` | Repiten información, pueden contener datos personales y exigirían procesamiento de lenguaje |

El notebook comprueba automáticamente que toda columna constante o con más de 90 % de nulos tenga una decisión documentada, y que ninguna columna del dataset quede sin decisión.

**Costo conocido.** `version` (por ejemplo, el nivel de equipamiento de una misma camioneta) probablemente explica parte del precio. Se excluyó para mantener un formulario simple y evitar miles de categorías; es la primera variable a probar si las métricas no son suficientes (ver sección 7).

### 4.3 Normalización de categorías

**Qué se hizo.** Una regla fija para todo el texto categórico: quitar tildes, colapsar espacios y pasar a mayúsculas.

**Por qué una regla y no un mapa.** El backend recibe lo que escribe el usuario (por ejemplo `Bogotá` o `bogota`) y debe llegar a la misma categoría que en entrenamiento. Una regla determinista se aplica igual en ambos lados.

**Por qué se quitan las tildes.** El usuario puede escribir con o sin tilde; si no se quitaran, `BOGOTÁ` y `BOGOTA` serían categorías distintas. El notebook muestra las variantes que se fusionaron para revisar que no haya colisiones indebidas.

**Límite conocido.** La regla no puede saber si dos escrituras distintas son la misma marca (por ejemplo `MERCEDES-BENZ` y `MERCEDES BENZ`); esos casos se corrigen con un mapeo manual si aparecen.

### 4.4 Valores imposibles o dudosos

Regla general: el registro se conserva, el valor dudoso pasa a `NaN` y luego se imputa con la mediana de entrenamiento. Cada corrección queda en la tabla de auditoría con su bandera.

| Variable | Regla | Razón |
|---|---|---|
| `anio` | Fuera de 1900 a (año de extracción + 1) pasa a `NaN` | El año-modelo puede ir un año adelante; por eso 2027 se acepta |
| `kilometraje` | Negativo o mayor a 1.000.000 pasa a `NaN` | Valores imposibles o de relleno (9.999.999) |
| `kilometraje` | Entre 500.000 y 1.000.000 se **conserva** y se reporta | Puede ser un taxi o un vehículo de trabajo real; borrarlo perdería información legítima |
| `kilometraje` | 0 con año anterior a 2025 pasa a `NaN` | Un usado de más de un año con 0 km no es creíble; en vehículos recientes sí |
| `cilindraje` | Negativo pasa a `NaN` | Imposible |
| `cilindraje` | Entero de 1 a 9 en no eléctricos se multiplica por 1.000 | Se interpreta como litros (2 equivale a 2.000 cc); es una hipótesis que el notebook verifica con la versión del aviso |
| `cilindraje` | 0 en no eléctricos, menor a 300 o mayor a 8.000 pasa a `NaN` | Fuera de lo razonable para un automóvil; parte de los mayores a 8.000 son copia exacta del kilometraje |
| `cilindraje` | En eléctricos se fija en 0 | Un eléctrico no tiene cilindraje; 0 es un valor legítimo |

**Por qué el límite de kilometraje es 1.000.000 y no 500.000.** Una versión inicial usaba 500.000. Se subió a 1.000.000 porque entre ambos valores hay vehículos de uso intensivo plausibles (81 avisos superan 500.000, pero solo 25 superan 1.000.000). Convertir un kilometraje alto real en faltante lo reemplazaría por la mediana y haría que el modelo viera un carro de kilometraje típico con un precio muy bajo, lo que añade ruido. Con `log1p` y `RobustScaler`, los valores altos reales no dominan la escala. Si al ejecutar se ven muchos errores evidentes en ese rango, se baja `KM_MAX`.

**Por qué los cilindrajes mayores a 8.000 pasan a faltante.** Ningún automóvil de este mercado tiene ese cilindraje, y hay evidencia directa del error: 35 de los 169 casos son idénticos al kilometraje del mismo aviso. Dejarlos (hasta 99.000) distorsionaría la variable.

**Por qué no se usaron cortes genéricos tipo boxplot.** En un mercado de vehículos, los valores extremos pueden ser reales (clásicos, deportivos, taxis con muchos kilómetros). Un corte estadístico automático borraría avisos genuinos; las reglas de dominio solo tocan lo que es imposible o evidentemente un relleno.

**Por qué no se usó `dropna()` global.** Con cinco columnas de 94,95 % de nulos, `dropna()` dejaría unas 1.034 filas de las 20.494. Se eliminan las columnas, no las filas.

### 4.5 Precio objetivo

Un precio imposible no se puede imputar sin inventar la respuesta que el modelo debe aprender, así que es el único caso en que se eliminan filas por valor. El umbral mínimo es de 3 millones de pesos. Como el 1 % más barato del conjunto está por debajo de 13 millones, el umbral afecta como máximo a una fracción mínima de los avisos; el notebook reporta el conteo exacto.

Los precios altos no se eliminan: pueden ser vehículos genuinos. El notebook lista los diez más altos para revisarlos.

**Transformación logarítmica.** Las regresiones se entrenan sobre `log(1 + precio)` porque la distribución es muy sesgada a la derecha y el error relativo importa más que el absoluto: equivocarse por 5 millones pesa distinto en un carro de 20 millones que en uno de 300. La transformación inversa va incluida en el modelo guardado (`TransformedTargetRegressor`), así que `predict` devuelve pesos y las métricas finales (MAE, RMSE, MAPE) se calculan directamente en pesos. Con esta decisión, el R² sobre `log(precio)` en validación es 0,914 con Gradient Boosting y 0,873 con Random Forest, frente a 0,000 del baseline.

### 4.6 Variables nuevas

- **`antiguedad`** = 2026 menos el año, con mínimo 0. Resume el año en un valor más interpretable y evita la colinealidad con `anio`, que se descarta. El año de referencia es una constante fija, no la fecha actual, para que el backend calcule lo mismo que el entrenamiento.
- **`km_por_anio`** = kilometraje dividido por la antigüedad (mínimo 1). Distingue un carro de uso intensivo de uno de poco uso con el mismo kilometraje total.
- **`marca_modelo`**: el nombre de un modelo puede repetirse entre marcas; combinado con la marca evita colisiones.

### 4.7 Partición de los datos

División aleatoria 70 % entrenamiento, 15 % validación y 15 % prueba. Es aleatoria porque los datos son un corte único del mercado y no una serie de tiempo; el orden temporal solo es obligatorio en series de tiempo. Se estratifica por deciles de precio para que las tres particiones tengan una distribución de precio parecida, y se fija una semilla para que sea reproducible. El notebook comprueba que las tres particiones sumen todos los registros y no se solapen.

### 4.8 Variable objetivo de clasificación

`segmento_precio` tiene tres clases (BAJO, MEDIO, ALTO) definidas por los terciles del precio **en entrenamiento**. Los mismos cortes se aplican a validación y prueba: si se calcularan con todos los datos, la prueba influiría en la definición de las clases. Es una discretización por igual frecuencia, que produce clases balanceadas por construcción. Los cortes se guardan en `cortes_segmento.json`.

### 4.9 Transformaciones

**Discretización de `antiguedad`.** El notebook compara tres estrategias (igual ancho, igual frecuencia y k-means) con cinco intervalos, midiendo con la correlación de Spearman cuánta relación con el precio se pierde al discretizar. Se decide no discretizar en el pipeline: los árboles encuentran sus propios puntos de corte y la variable continua conserva al menos tanta relación con el precio como cualquier versión discretizada. El modelo 3 es una Regresión Logística (lineal) y en principio podría beneficiarse de intervalos; no se evaluó una versión discretizada, y con la variable continua ya alcanza un F1 macro de 0,854 en validación con la configuración inicial (`C = 1`), por lo que se mantiene sin discretizar.

**Codificación de categóricas.** One-Hot con las categorías de menos de 30 avisos agrupadas en una sola columna.

| Alternativa | Por qué se descarta |
|---|---|
| Label u ordinal | Impone un orden falso entre marcas o departamentos |
| Frecuencia | Dos marcas con la misma frecuencia quedarían iguales |
| Target Encoding | Aprende del precio y exige validación cruzada interna para no filtrar información |

La agrupación de raras reduce el ruido de `marca_modelo`, que tiene cientos de categorías, y permite que una categoría no vista en entrenamiento caiga en el grupo de raras sin romper el backend.

**Escalado.** `kilometraje` y `km_por_anio` llevan `log1p` y luego `RobustScaler`; `antiguedad` y `cilindraje` solo `RobustScaler`. El escalado robusto usa mediana y rango intercuartílico, así que los extremos que sobreviven a la limpieza no dominan la escala. El `log1p` está condicionado a la evidencia: el notebook calcula si realmente reduce la asimetría y, si no lo hace (puede pasar con muchos vehículos casi nuevos, con kilometraje cercano a 0), se desactiva con el interruptor `USAR_LOG_NUMERICAS`. Los árboles (modelos 1 y 2) no necesitan escalado, pero la Regresión Logística (modelo 3) sí, y un mismo preprocesador sirve a los tres modelos. Que el modelo lineal alcance un F1 macro de 0,854 en validación con la configuración inicial sugiere que el escalado y la codificación son adecuados.

**Imputación.** Mediana para numéricas (robusta a extremos) y la categoría `NO INFORMADO` para categóricas. Además se agregan indicadores de faltante para `kilometraje` y `cilindraje`, porque que un dato falte puede ser informativo. La mediana se calcula solo con entrenamiento.

---

## 5. Reproducibilidad en el backend

El requisito del enunciado es que el mismo preprocesamiento se aplique a los datos nuevos. Se cumple así:

- El `Pipeline` de preprocesamiento recibe las 10 columnas crudas del formulario. Dentro, el primer paso normaliza texto, sanea numéricos y crea las variables derivadas con la misma función que se usó en el entrenamiento.
- El preprocesador se ajusta una sola vez con entrenamiento y se guarda con `joblib`. Cada modelo final se guarda como un `Pipeline` completo (preprocesamiento más algoritmo), de modo que el backend carga un archivo por modelo y llama a `predict`.
- El notebook verifica la reproducibilidad: recarga el archivo guardado, comprueba que produce la misma matriz y prueba una entrada escrita a mano sin normalizar (por ejemplo `chevrolet`, `Antioquia`).
- El backend debe poder importar `preprocesamiento.py`, porque `joblib` guarda las funciones por referencia al módulo.
- Los modelos de regresión se entrenan sobre `log(1 + precio)`, pero el archivo guardado incluye la transformación inversa (`TransformedTargetRegressor`): `predict` ya devuelve pesos y el backend no debe convertir nada. El modelo de clasificación devuelve probabilidades por segmento con `predict_proba`.
- La versión de scikit-learn con que se guardaron los modelos queda registrada en `metadatos_modelos.json`; el backend debe usar la misma.

---

## 6. Diccionario de datos de las variables usadas

| Variable | Tipo | Descripción | Papel |
|---|---|---|---|
| `marca` | Categórica | Marca del vehículo, normalizada | Entrada |
| `modelo` | Categórica | Modelo del vehículo; se combina con la marca en `marca_modelo` | Entrada |
| `anio` | Numérica | Año del vehículo; se transforma en `antiguedad` | Entrada |
| `kilometraje` | Numérica | Kilómetros recorridos | Entrada |
| `combustible` | Categórica | Tipo de combustible (gasolina, diésel, eléctrico, etc.) | Entrada |
| `transmision` | Categórica | Mecánica o automática; puede faltar | Entrada |
| `cilindraje` | Numérica | Cilindrada en centímetros cúbicos; 0 en eléctricos | Entrada |
| `carroceria` | Categórica | Tipo de carrocería | Entrada |
| `departamento` | Categórica | Departamento donde se publica el aviso | Entrada |
| `tipo_vendedor` | Categórica | Particular o concesionario | Entrada |
| `precio` | Numérica | Precio de publicación en pesos colombianos | Objetivo de regresión |
| `antiguedad` | Numérica derivada | Años de antigüedad respecto a 2026 | Entrada derivada |
| `km_por_anio` | Numérica derivada | Kilometraje dividido por antigüedad | Entrada derivada |
| `marca_modelo` | Categórica derivada | Marca y modelo concatenados | Entrada derivada |
| `segmento_precio` | Categórica derivada | BAJO, MEDIO o ALTO según terciles de precio en entrenamiento | Objetivo de clasificación |

---

## 7. Limitaciones y posibles mejoras

- **Umbrales.** `KM_MAX`, `CILINDRAJE_MIN`, `CILINDRAJE_MAX` y `PRECIO_MIN` están en `preprocesamiento.py`. Tras ejecutar, hay que revisar cuántos registros afecta cada uno y ajustarlos si algo no tiene sentido con los datos reales.
- **Hipótesis de litros.** La conversión del cilindraje de 1 a 9 se basa en una hipótesis. Si la evidencia del notebook no la respalda, se desactiva con `CONVERTIR_LITROS`.
- **Fusión de categorías.** La regla de normalización puede dejar sin unir variantes que significan lo mismo; conviene revisar la tabla del notebook.
- **Variables descartadas que podrían mejorar el modelo.** `version` es la primera candidata (mucho valor informativo, pero miles de categorías). También `ciudad` y `blindado`. Conviene probarlas solo si las métricas lo justifican.
- **Variables con poca importancia.** En la importancia por permutación sobre validación, `departamento` y `tipo_vendedor` quedaron en 0,00 en los dos modelos de regresión, mientras que `anio` es la más influyente (0,37 en Gradient Boosting). Es evidencia a favor de quitar esas dos entradas del formulario, pero antes hay que reentrenar sin ellas y comprobar que las métricas no empeoran. La importancia por permutación subestima variables correlacionadas (`modelo` con `marca`, `kilometraje` con `anio`), así que esas dos no deben descartarse por este criterio.
- **Datos de un solo corte.** Los precios son de avisos publicados, no de ventas cerradas, y reflejan un momento del mercado. Los modelos no capturan la evolución del precio en el tiempo.
- **Licencia.** El dataset no tiene licencia abierta identificada; el uso es académico, y esto debe constar en el informe junto con la fuente y la fecha de obtención.
- **Si se cambia un parámetro**, hay que ejecutar de nuevo todo el notebook para regenerar el preprocesador, las particiones y la auditoría.

---

## 8. De dónde sale cada cifra para el informe

| Dato para el informe | Dónde aparece en el notebook |
|---|---|
| Avisos repetidos del mismo vehículo | Sección 2 (duplicados) y tabla de resumen final |
| Categorías antes y después de normalizar | Sección 4 |
| Cilindrajes mayores a 8.000 idénticos al kilometraje | Sección 5, celda de evidencia |
| Valores que pasan a faltante por variable | Sección 5, tabla `pasan_a_NaN` |
| Conteo por regla (con banderas) | Sección 5, tabla de auditoría y `carroya_auditoria_limpieza.csv` |
| Precios eliminados por umbral | Sección 6 |
| Tamaño y precio mediano de train, validación y prueba | Sección 8 |
| Cortes de los segmentos y balance de clases | Sección 9 |
| Comparación de discretización, codificación y escalado | Secciones 10.1, 10.2 y 10.3 |
| Número de columnas de la matriz final | Sección 11 |
| Filas que quedan después de cada etapa | Tabla «Resumen del proceso» al final |

---

## 9. Validación de las decisiones con los resultados del entrenamiento

Resultados en la partición de **validación** (la de prueba no se usó para decidir nada):

| Indicador | Baseline (mediana) | Gradient Boosting | Random Forest |
|---|---|---|---|
| MAE | 33,7 M | 9,3 M | 12,3 M |
| MAPE | 55,5 % | 12,4 % | 15,6 % |
| R² sobre `log(precio)` | 0,000 | 0,914 | 0,873 |

- **Sin señales de fuga de datos.** El MAPE pasa de 10,0 % en entrenamiento a 12,4 % en validación (Gradient Boosting) y de 13,8 % a 15,6 % (Random Forest). Una brecha pequeña es lo esperable si el preprocesamiento se ajustó solo con entrenamiento.
- **La partición es representativa.** El RMSE de prueba es 0,94 veces el de validación en ambos modelos, es decir, prueba y validación se comportan igual.
- **Clasificación.** Con la configuración inicial (`C = 1`), la Regresión Logística obtiene un F1 macro de 0,854 en validación, frente a 0,169 del baseline. Actualiza esta cifra con la salida de la sección 5 del notebook de entrenamiento una vez ajustado `C`.
- Las métricas completas, los hiperparámetros finales y el análisis de sobreajuste van en el documento de modelos e hiperparámetros.