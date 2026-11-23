"""Script para grabar y compilar un GIF de demostración interactiva de YaCarroPredict.

Usa Playwright para simular una interacción real de usuario sobre la aplicación
en producción y Pillow para generar un demo animado optimizado para el README.
"""

import os
import time
from PIL import Image
from playwright.sync_api import sync_playwright

URL_APP = "https://yacarropredict-proyectocld.onrender.com/"
OUTPUT_GIF = os.path.join(os.path.dirname(__file__), "..", "evidencias", "demo.gif")
FRAMES_DIR = os.path.join(os.path.dirname(__file__), "..", "evidencias", "temp_frames")

def main():
    print(f"Iniciando grabación automatizada sobre: {URL_APP}")
    os.makedirs(FRAMES_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_GIF), exist_ok=True)

    captured_frames = []
    frame_durations = []

    def snap(page, count=1, duration=350):
        time.sleep(0.15)
        path = os.path.join(FRAMES_DIR, f"frame_{len(captured_frames):04d}.png")
        page.screenshot(path=path)
        for _ in range(count):
            captured_frames.append(path)
            frame_durations.append(duration)
        print(f"  [Frame {len(captured_frames):03d}] Capturado")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 820})
        page = context.new_page()

        print("1. Cargando la aplicación en vivo...")
        page.goto(URL_APP, wait_until="networkidle", timeout=60000)
        time.sleep(2)

        # Captura del Hero
        snap(page, count=4, duration=500)

        # Scroll al panel de estadísticas y gráficos
        print("2. Mostrando estadísticas y gráficos...")
        page.evaluate("window.scrollTo({top: 450, behavior: 'smooth'})")
        time.sleep(1.2)
        snap(page, count=6, duration=500)

        # Scroll al formulario de cotización
        print("3. Desplazándose al formulario...")
        page.evaluate("window.scrollTo({top: 950, behavior: 'smooth'})")
        time.sleep(1.2)
        snap(page, count=3, duration=400)

        # Llenar formulario
        print("4. Simulando ingreso de datos del vehículo...")
        page.wait_for_selector("#marca option[value='CHEVROLET']", state="attached", timeout=15000)
        page.select_option("#marca", "CHEVROLET")
        snap(page, count=2, duration=300)

        # Esperar a que se poblen los modelos de Chevrolet
        page.wait_for_selector("#modelo option[value='ONIX']", state="attached", timeout=10000)
        page.select_option("#modelo", "ONIX")
        snap(page, count=2, duration=300)

        page.fill("#anio", "2021")
        snap(page, count=1, duration=250)

        page.fill("#kilometraje", "35000")
        snap(page, count=1, duration=250)

        page.select_option("#combustible", "GASOLINA")
        snap(page, count=1, duration=250)

        page.select_option("#transmision", "MECANICA")
        snap(page, count=1, duration=250)

        page.fill("#cilindraje", "1000")
        snap(page, count=1, duration=250)

        page.select_option("#carroceria", "AUTOMOVIL")
        snap(page, count=1, duration=250)

        page.select_option("#departamento", "BOGOTA D.C.")
        snap(page, count=1, duration=250)

        page.select_option("#tipo_vendedor", "CONCESIONARIO")
        snap(page, count=3, duration=400)

        # Enviar formulario
        print("5. Enviando cotización y esperando predicción...")
        page.click("#submitBtn")
        time.sleep(0.5)
        snap(page, count=2, duration=200)

        # Esperar a que se despliegue el resultado
        page.wait_for_selector("#resultSection", state="visible", timeout=15000)
        time.sleep(1.0)
        page.evaluate("document.getElementById('resultSection').scrollIntoView({behavior: 'smooth', block: 'center'})")
        time.sleep(1.0)

        # Capturas fijas del resultado
        print("6. Capturando tarjeta de resultados...")
        snap(page, count=10, duration=400)

        # Scroll hacia la tabla de recientes
        print("7. Mostrando actualización de historial...")
        page.evaluate("document.getElementById('secRecientes').scrollIntoView({behavior: 'smooth', block: 'center'})")
        time.sleep(1.0)
        snap(page, count=8, duration=400)

        browser.close()

    print(f"\n8. Procesando y optimizando {len(captured_frames)} fotogramas...")
    images = []
    # Escalar a 960x615 para excelente nitidez y tamaño liviano
    target_size = (960, 615)
    for fpath in captured_frames:
        im = Image.open(fpath).convert("P", palette=Image.ADAPTIVE, colors=128)
        im_resized = im.resize(target_size, Image.Resampling.LANCZOS)
        images.append(im_resized)

    print(f"Guardando GIF animado en: {OUTPUT_GIF}")
    images[0].save(
        OUTPUT_GIF,
        save_all=True,
        append_images=images[1:],
        duration=frame_durations,
        loop=0,
        optimize=True
    )

    # Limpiar fotogramas temporales
    for f in set(captured_frames):
        try:
            os.remove(f)
        except OSError:
            pass
    try:
        os.rmdir(FRAMES_DIR)
    except OSError:
        pass

    file_size_mb = os.path.getsize(OUTPUT_GIF) / (1024 * 1024)
    print(f"🎉 ¡GIF generado exitosamente! Tamaño: {file_size_mb:.2f} MB")

if __name__ == "__main__":
    main()
