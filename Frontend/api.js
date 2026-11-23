// =============================================================================
// YaCarroPredict — api.js
// =============================================================================

const API_BASE = window.location.origin.includes(":5000") ? "" : "http://localhost:5000";

let opcionesGlobales = null;

// Referencias DOM
const form       = document.getElementById("predictionForm");
const submitBtn  = document.getElementById("submitBtn");
const btnText    = document.getElementById("btnText");
const btnSpinner = document.getElementById("btnSpinner");
const banner     = document.getElementById("statusBanner");

const selMarca       = document.getElementById("marca");
const selModelo      = document.getElementById("modelo");
const selCombustible = document.getElementById("combustible");
const selTransmision = document.getElementById("transmision");
const selCarroceria  = document.getElementById("carroceria");
const selDepto       = document.getElementById("departamento");
const selTipo        = document.getElementById("tipo_vendedor");
const inpCilindraje  = document.getElementById("cilindraje");

// Gráficos Chart.js
let chartMarcas    = null;
let chartSegmentos = null;

// ─── Helpers de UI ───────────────────────────────────────────────────────────
function mostrarBanner(msg, tipo = "danger") {
  banner.className = `alert alert-${tipo}`;
  banner.innerHTML = `<i class="bi bi-exclamation-triangle-fill me-2"></i>${msg}`;
  banner.style.display = "block";
}
function ocultarBanner() { banner.style.display = "none"; }

function setCargando(on) {
  submitBtn.disabled = on;
  btnText.style.display    = on ? "none" : "inline";
  btnSpinner.style.display = on ? "inline" : "none";
}

function llenarSelect(sel, lista, placeholder) {
  sel.innerHTML = `<option value="" selected disabled>${placeholder}</option>`;
  lista.forEach(v => {
    const o = document.createElement("option");
    o.value = o.textContent = v;
    sel.appendChild(o);
  });
}

function resetForm() {
  form.reset();
  selModelo.innerHTML = '<option value="" selected disabled>Selecciona una marca primero</option>';
  selModelo.disabled = true;
  document.getElementById("resultSection").style.display = "none";
  ocultarBanner();
  window.scrollTo({ top: document.getElementById("cotizar").offsetTop - 70, behavior: "smooth" });
}

function segClasses(seg) {
  const map = { BAJO: "seg-BAJO", MEDIO: "seg-MEDIO", ALTO: "seg-ALTO" };
  return map[seg] || "";
}

// ─── Carga de opciones ────────────────────────────────────────────────────────
async function cargarOpciones() {
  try {
    const res = await fetch(`${API_BASE}/api/opciones`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    opcionesGlobales = await res.json();

    llenarSelect(selMarca,       opcionesGlobales.marca,          "Selecciona una marca");
    llenarSelect(selCombustible, opcionesGlobales.combustible,    "Selecciona el combustible");
    llenarSelect(selTransmision, opcionesGlobales.transmision,    "Selecciona la transmisión");
    llenarSelect(selCarroceria,  opcionesGlobales.carroceria,     "Selecciona la carrocería");
    llenarSelect(selDepto,       opcionesGlobales.departamento,   "Selecciona el departamento");
    llenarSelect(selTipo,        opcionesGlobales.tipo_vendedor,  "Selecciona el tipo de vendedor");

    ocultarBanner();
  } catch (err) {
    console.warn("No se pudieron cargar las opciones:", err);
    mostrarBanner(
      "El backend no está activo. Ejecuta <code>python Backend/app.py</code> y recarga la página.",
      "warning"
    );
  }
}

// ─── Dependencia Marca → Modelo ───────────────────────────────────────────────
selMarca.addEventListener("change", () => {
  const modelos = opcionesGlobales?.modelos_por_marca?.[selMarca.value] || [];
  if (modelos.length) {
    llenarSelect(selModelo, modelos, "Selecciona un modelo");
    selModelo.disabled = false;
  } else {
    selModelo.innerHTML = '<option value="" selected disabled>Sin modelos disponibles</option>';
    selModelo.disabled = true;
  }
});

// Sugerencia cilindraje eléctrico
selCombustible.addEventListener("change", () => {
  if (selCombustible.value.includes("ELECTRIC") && !inpCilindraje.value) {
    inpCilindraje.value = 0;
  }
});

// ─── Envío del formulario ─────────────────────────────────────────────────────
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  ocultarBanner();

  const payload = {
    marca:        selMarca.value,
    modelo:       selModelo.value,
    anio:         Number(document.getElementById("anio").value),
    kilometraje:  Number(document.getElementById("kilometraje").value),
    combustible:  selCombustible.value,
    transmision:  selTransmision.value,
    cilindraje:   Number(inpCilindraje.value),
    carroceria:   selCarroceria.value,
    departamento: selDepto.value,
    tipo_vendedor:selTipo.value,
  };

  setCargando(true);
  try {
    const res  = await fetch(`${API_BASE}/api/prediccion`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok || !data.exito) throw new Error(data.error || `HTTP ${res.status}`);

    renderResultado(data.prediccion, data.vehiculo);
    // Refrescar KPIs y tabla después de guardar en Firestore
    setTimeout(() => { cargarEstadisticas(); cargarRecientes(); }, 1200);

  } catch (err) {
    mostrarBanner(`Error al predecir: ${err.message}`, "danger");
  } finally {
    setCargando(false);
  }
});

// ─── Renderizar resultado ─────────────────────────────────────────────────────
function renderResultado(pred, vehiculo) {
  document.getElementById("rPrecio").textContent   = pred.precio_estimado_formato;
  document.getElementById("rIntervalo").textContent =
    `${pred.intervalo_80.min_formato} — ${pred.intervalo_80.max_formato}`;

  const badge = document.getElementById("rSegBadge");
  badge.textContent  = `Segmento ${pred.segmento}`;
  badge.className    = `seg-badge ${segClasses(pred.segmento)}`;

  // Probabilidades
  const pills = document.getElementById("rProbPills");
  pills.innerHTML = "";
  for (const [seg, prob] of Object.entries(pred.probabilidades_segmento)) {
    const pill = document.createElement("span");
    pill.className = "prob-pill";
    pill.textContent = `${seg}: ${(prob * 100).toFixed(1)} %`;
    pills.appendChild(pill);
  }

  document.getElementById("rGB").textContent = pred.precio_estimado_formato;
  document.getElementById("rRF").textContent = pred.modelo_alternativo.precio_formato;

  // Chips del vehículo
  const chips = document.getElementById("rVehiculo");
  chips.innerHTML = "";
  const campos = [
    ["car",    vehiculo.marca + " " + vehiculo.modelo],
    ["calendar3", vehiculo.anio],
    ["speedometer", vehiculo.kilometraje.toLocaleString("es-CO") + " km"],
    ["fuel-pump", vehiculo.combustible],
    ["gear-wide-connected", vehiculo.transmision],
    ["tools", vehiculo.cilindraje + " cc"],
    ["geo-alt", vehiculo.departamento],
    ["person", vehiculo.tipo_vendedor],
  ];
  campos.forEach(([icon, val]) => {
    const chip = document.createElement("span");
    chip.className = "badge";
    chip.style.cssText = "background:#1a1a1a;border:1px solid #2e2e2e;color:#bbb;font-size:.75rem;font-weight:400";
    chip.innerHTML = `<i class="bi bi-${icon} me-1"></i>${val}`;
    chips.appendChild(chip);
  });

  const sec = document.getElementById("resultSection");
  sec.style.display = "block";
  sec.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ─── Estadísticas (KPIs + Gráficos) ──────────────────────────────────────────
async function cargarEstadisticas() {
  try {
    const res  = await fetch(`${API_BASE}/api/estadisticas`);
    const data = await res.json();
    if (!data.disponible) return;

    document.getElementById("kpiTotal").textContent   = data.total.toLocaleString("es-CO");
    document.getElementById("kpiPrecio").textContent  = data.precio_promedio_fmt || "—";
    document.getElementById("kpiSegmento").textContent = data.segmento_frecuente || "—";
    document.getElementById("kpiMarca").textContent   =
      data.marcas_top.length ? data.marcas_top[0].marca : "—";

    // ── Gráfico de barras: Top marcas ──
    const ctxBar = document.getElementById("chartMarcas").getContext("2d");
    const labels  = data.marcas_top.map(m => m.marca);
    const valores = data.marcas_top.map(m => m.total);

    if (chartMarcas) chartMarcas.destroy();
    chartMarcas = new Chart(ctxBar, {
      type: "bar",
      data: {
        labels,
        datasets: [{
          label: "Consultas",
          data: valores,
          backgroundColor: "rgba(79,142,247,.7)",
          borderColor: "rgba(79,142,247,1)",
          borderWidth: 1,
          borderRadius: 5,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: "#888" }, grid: { color: "#1e1e1e" } },
          y: { ticks: { color: "#888", stepSize: 1 }, grid: { color: "#1e1e1e" }, beginAtZero: true },
        },
      },
    });

    // ── Gráfico de dona: Segmentos ──
    const dist = data.distribucion_segmentos;
    const ctxDona = document.getElementById("chartSegmentos").getContext("2d");
    if (chartSegmentos) chartSegmentos.destroy();
    chartSegmentos = new Chart(ctxDona, {
      type: "doughnut",
      data: {
        labels: ["BAJO", "MEDIO", "ALTO"],
        datasets: [{
          data: [dist.BAJO, dist.MEDIO, dist.ALTO],
          backgroundColor: [
            "rgba(52,199,89,.75)",
            "rgba(255,185,0,.75)",
            "rgba(255,55,95,.75)",
          ],
          borderColor: ["#34c759","#ffb900","#ff375f"],
          borderWidth: 1,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        cutout: "60%",
        plugins: {
          legend: {
            position: "bottom",
            labels: { color: "#aaa", boxWidth: 12, padding: 16, font: { size: 11 } },
          },
        },
      },
    });

  } catch (err) {
    console.warn("No se pudieron cargar estadísticas:", err);
  }
}

// ─── Tabla recientes ───────────────────────────────────────────────────────────
async function cargarRecientes() {
  const tbody = document.getElementById("tbRecientes");
  try {
    const res  = await fetch(`${API_BASE}/api/recientes`);
    const data = await res.json();

    if (!data.disponible || !data.datos.length) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-center text-secondary py-4">Aún no hay cotizaciones registradas.</td></tr>';
      return;
    }

    tbody.innerHTML = data.datos.map(r => `
      <tr>
        <td><strong class="text-white">${r.marca}</strong> ${r.modelo}</td>
        <td>${r.anio}</td>
        <td class="text-white fw-semibold">${r.precio_fmt}</td>
        <td><span class="seg-badge ${segClasses(r.segmento)}" style="font-size:.7rem;padding:2px 10px">${r.segmento}</span></td>
        <td class="text-secondary">${r.timestamp}</td>
      </tr>
    `).join("");
  } catch (err) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center text-secondary py-4">No disponible.</td></tr>';
  }
}

// ─── Inicio ───────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  cargarOpciones();
  cargarEstadisticas();
  cargarRecientes();
});
