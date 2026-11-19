import csv, json, random, re, sys, time
from datetime import datetime
from pathlib import Path

import requests

URL = "https://carroya-habilitadora-api.avaldigitallabs.com/find-filters"
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Content-Type": "application/json",
    "Origin": "https://www.carroya.com",
    "Referer": "https://www.carroya.com/",
    "Accept-Language": "es-CO,es;q=0.9",
}
RAW_DIR = Path("data/raw"); RAW_DIR.mkdir(parents=True, exist_ok=True)
RAW = RAW_DIR / "carroya_raw.jsonl"
DONE = RAW_DIR / "paginas_hechas.txt"
CSV_OUT = Path("data/carroya_dataset.csv")

# Campos que NO se guardan (datos personales o peso inútil)
DROP = {"cclienteidusuario", "cselleremail", "csellername", "csellercity", "cselleradress",
        "cselleradress2", "cdireccion", "memail", "cplaca", "clplaca", "ccontactpointname",
        "ccontactpointid", "csellerid", "cclienteidgrupo", "cclienteurlmicrositio",
        "cusuariocreacion", "clogoempresa", "cnombreempresa",
        "images", "images4seo", "image4seosizes", "detail", "curlimagen", "cnombreimagen"}

RE_TEL = re.compile(r"(?<!\d)(?:\+?57[\s-]?)?3\d{2}[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)")
RE_MAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")

def limpiar_texto(s):
    if not isinstance(s, str):
        return s
    return RE_MAIL.sub("[email]", RE_TEL.sub("[tel]", s))

SESSION = requests.Session()
SESSION.headers.update(H)

def pedir(page, seo=None, intentos=5):
    body = {"seoArray": seo or ["carros-y-camionetas"], "params": {"page": str(page)},
            "isReqForRedirect": False}
    for i in range(intentos):
        try:
            r = SESSION.post(URL, json=body, timeout=30)
            if r.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"{r.status_code}")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            espera = 5 * (2 ** i)
            print(f"  page {page}: {e}; reintento en {espera}s")
            time.sleep(espera)
    return None

def registros(data):
    res = data.get("results", {})
    return (res.get("superHighlights") or []) + (res.get("megaHighlights") or [])

def scrapear():
    primera = pedir(1)
    if not primera:
        sys.exit("No se pudo consultar la página 1")
    total_pag = int(primera.get("pages", 1))
    print(f"count={primera.get('count')}  pages={total_pag}")
    hechas = set(int(x) for x in DONE.read_text().split()) if DONE.exists() else set()
    vacias = 0
    ahora = datetime.now().isoformat(timespec="seconds")

    with open(RAW, "a", encoding="utf-8") as f_raw, open(DONE, "a") as f_done:
        for p in range(1, total_pag + 1):
            if p in hechas:
                continue
            data = primera if p == 1 else pedir(p)
            if data is None:
                print(f"page {p}: falló; se salta (reanuda y la reintenta)")
                continue
            regs = registros(data)
            vacias = vacias + 1 if not regs else 0
            for r in regs:
                r = {k: v for k, v in r.items() if k not in DROP}
                r["ccomentarios"] = limpiar_texto(r.get("ccomentarios"))
                r["_page"], r["_fecha_extraccion"] = p, ahora
                f_raw.write(json.dumps(r, ensure_ascii=False) + "\n")
            f_raw.flush(); f_done.write(f"{p}\n"); f_done.flush()
            if p % 25 == 0:
                print(f"page {p}/{total_pag}")
            if vacias >= 5:
                print("5 páginas vacías seguidas: me detengo"); break
            time.sleep(random.uniform(1.5, 3.0))

# --- Raw -> CSV (esquema del proyecto) ---
MAPA = {
    "id": "id", "estado": "status", "marca": "brand", "modelo": "model", "version": "clinea2",
    "anio": "year", "kilometraje": "kilometers", "precio": "price", "moneda": "ctipomoneda",
    "combustible": "ccombustible", "transmision": "ctipocaja", "cilindraje": "cylindrical",
    "color": "color", "ciudad": "city", "departamento": "cdivision", "carroceria": "ctipo",
    "tipo_vendedor": "cofrecidopor", "pico_placa": "cpicoyplaca", "ciudad_placa": "cciudadplaca",
    "num_fotos": "cnumfotos", "fecha_publicacion": "cfechapublicacion",
    "negociable": "cprecionegociable", "unico_dueno": "cunicoduenofenomenoya",
    "blindado": "cesblindado", "destacado": "featured", "tipo_direccion": "ctipodireccion",
    "torque": "ctorque", "potencia": "ctipopotencia", "titulo": "title",
    "caracteristicas": "ccaracteristicas", "accesorios": "caccesorios",
    "descripcion": "ccomentarios", "fecha_extraccion": "_fecha_extraccion",
}

def a_csv():
    vistos = {}
    with open(RAW, encoding="utf-8") as f:
        for linea in f:
            r = json.loads(linea)
            vistos[r.get("id")] = r          # deduplica por id (queda el último)
    with open(CSV_OUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["fuente", *MAPA.keys()])
        w.writeheader()
        for r in vistos.values():
            fila = {"fuente": "carroya"}
            for col, k in MAPA.items():
                v = r.get(k)
                fila[col] = json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
            w.writerow(fila)
    print(f"{len(vistos)} avisos únicos -> {CSV_OUT}")

if __name__ == "__main__":
    if "csv" not in sys.argv:
        scrapear()
    a_csv()