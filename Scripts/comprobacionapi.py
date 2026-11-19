import json, time, requests

URL = "https://carroya-habilitadora-api.avaldigitallabs.com/find-filters"
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Content-Type": "application/json",
    "Origin": "https://www.carroya.com",
    "Referer": "https://www.carroya.com/",
    "Accept-Language": "es-CO,es;q=0.9",
}

def pedir(page, seo=None):
    body = {"seoArray": seo or ["carros-y-camionetas"], "params": {"page": str(page)}, "isReqForRedirect": False}
    r = requests.post(URL, headers=H, json=body, timeout=30)
    r.raise_for_status()
    return r.json()

# 1) Registro completo de un aviso
d1 = pedir(1)
reg = d1["results"]["superHighlights"][0]
print(json.dumps(reg, ensure_ascii=False, indent=2))
print("\nCLAVES:", list(reg.keys()))
print("megaHighlights[0] claves:", list(d1["results"]["megaHighlights"][0].keys()))

# 2) Paginación profunda y repetidos (usa la clave que parezca el id del vehículo)
def ids(d, clave):
    return [x.get(clave) for x in d["results"]["superHighlights"]]

clave_id = next((k for k in reg if k.lower() in ("cid", "id", "cidvehiculo", "cvehiculoid", "cidaviso")), None)
print("\nclave de id detectada:", clave_id)

for p in (2, 500, 1026, 1027):
    time.sleep(2)
    try:
        d = pedir(p)
        lista = d["results"]["superHighlights"]
        print(f"page {p}: {len(lista)} avisos", ids(d, clave_id)[:3] if clave_id else "")
    except Exception as e:
        print(f"page {p}: error {e}")