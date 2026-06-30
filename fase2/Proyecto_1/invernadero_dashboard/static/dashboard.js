// dashboard.js
// Maneja toda la lógica del frontend:
// - Conexión en tiempo real con el servidor
// - Actualización de valores en pantalla
// - Gráficas históricas
// - Envío de comandos

// ═══════════════════════════════════════
// CONEXIÓN EN TIEMPO REAL
// ═══════════════════════════════════════

// Conectar al servidor Flask via SocketIO
const socket = io();
const INTERVALO_DECISION_ARM64_MS = 2000;
let ultimaConsultaDecisionARM64 = 0;
let consultaDecisionARM64EnCurso = false;

// Cuando el servidor envía una actualización de datos
socket.on("actualizacion", function(datos) {
    actualizarPanel(datos);
    refrescarDecisionARM64EnVivo();
});

socket.on("connect", function() {
    console.log("✅ Conectado al servidor en tiempo real");
});

socket.on("disconnect", function() {
    console.log("❌ Desconectado del servidor");
    actualizarBadgeEstado("DESCONECTADO");
});


// ═══════════════════════════════════════
// ACTUALIZAR PANEL PRINCIPAL
// ═══════════════════════════════════════

function actualizarPanel(datos) {
    // Sensores
    actualizarSensor("temperatura",  datos.temperatura,      28, 35, "°C");
    actualizarSensor("humedad",      datos.humedad_ambiente, 40, 80, "%");
    actualizarSensor("suelo1",       datos.humedad_suelo_area1,  400, 700, "ADC");
    actualizarSensor("suelo2",       datos.humedad_suelo_area2,  400, 700, "ADC");
    actualizarSensor("luz",          datos.luz,              100, 800, "lux");
    actualizarSensor("gas",          datos.gas,              0,  300, "ppm");

    // Actuadores
    actualizarActuador("riego",      datos.riego);
    actualizarActuador("ventilador", datos.ventilador);
    actualizarActuador("luces",      datos.luces);
    actualizarActuador("alarma",     datos.alarma);

    // Estado global y última actualización
    actualizarBadgeEstado(datos.estado_global);
    const elemAct = document.getElementById("ultima-act");
    if (elemAct) elemAct.textContent = datos.ultima_actualizacion || "--";
}


function actualizarSensor(id, valor, minNormal, maxNormal, unidad) {
    // Actualizar el número
    const elemValor = document.getElementById("val-" + id);
    if (elemValor) {
        elemValor.textContent =
            valor === undefined || valor === null || valor === "" ? "--" : valor;
    }

    // Determinar y mostrar el estado
    const elemEstado = document.getElementById("est-" + id);
    if (!elemEstado) return;

    const num = parseFloat(valor);
    if (isNaN(num)) {
        elemEstado.textContent  = "Sin datos";
        elemEstado.className    = "sensor-estado";
        return;
    }

    if (id === "suelo1" || id === "suelo2") {
        if (num >= maxNormal) {
            elemEstado.textContent = "SECO";
            elemEstado.className   = "sensor-estado advertencia";
        } else if (num < minNormal) {
            elemEstado.textContent = "SATURADO";
            elemEstado.className   = "sensor-estado advertencia";
        } else {
            elemEstado.textContent = "NORMAL";
            elemEstado.className   = "sensor-estado";
        }
    } else if (id === "gas") {
        if (num > maxNormal) {
            elemEstado.textContent = "⚠️ PELIGRO";
            elemEstado.className   = "sensor-estado emergencia";
        } else if (num > maxNormal * 0.7) {
            elemEstado.textContent = "ADVERTENCIA";
            elemEstado.className   = "sensor-estado advertencia";
        } else {
            elemEstado.textContent = "NORMAL";
            elemEstado.className   = "sensor-estado";
        }
    } else {
        if (num > maxNormal) {
            elemEstado.textContent = "⬆️ ALTO";
            elemEstado.className   = "sensor-estado advertencia";
        } else if (num < minNormal) {
            elemEstado.textContent = "⬇️ BAJO";
            elemEstado.className   = "sensor-estado advertencia";
        } else {
            elemEstado.textContent = "NORMAL";
            elemEstado.className   = "sensor-estado";
        }
    }
}


function actualizarActuador(id, valor) {
    const elem = document.getElementById("act-" + id);
    if (!elem) return;

    const activo = valor === "ON" || valor === "ENCENDIDO";
    elem.textContent = activo ? "ON" : "OFF";
    elem.className   = "actuador-badge " + (activo ? "on" : "off");
}


function actualizarBadgeEstado(estado) {
    const badge = document.getElementById("badge-estado");
    if (!badge) return;

    badge.textContent = estado || "DESCONECTADO";

    // Quitar todas las clases de color anteriores
    badge.className = "badge";

    const mapaClases = {
        "NORMAL":       "badge-normal",
        "ADVERTENCIA":  "badge-advertencia",
        "EMERGENCIA":   "badge-emergencia",
        "RIEGO_ACTIVO": "badge-riego",
        "MODO_MANUAL":  "badge-manual",
        "DESCONECTADO": "badge-desconectado"
    };

    badge.classList.add(mapaClases[estado] || "badge-desconectado");
}


// ═══════════════════════════════════════
// NAVEGACIÓN ENTRE SECCIONES
// ═══════════════════════════════════════

function mostrarSeccion(nombre) {
    // Ocultar todas las secciones
    document.querySelectorAll(".seccion").forEach(s => {
        s.classList.remove("activa");
    });

    // Quitar clase active de todos los botones
    document.querySelectorAll(".nav-btn").forEach(b => {
        b.classList.remove("active");
    });

    // Mostrar la sección pedida
    const seccion = document.getElementById("seccion-" + nombre);
    if (seccion) seccion.classList.add("activa");

    // Marcar el botón activo
    event.target.classList.add("active");

    // Cargar datos según la sección
    if (nombre === "graficas")  cargarGraficas();
    if (nombre === "historial") cargarHistorial();
    if (nombre === "arm64")     cargarARM64();
}


// ═══════════════════════════════════════
// GRÁFICAS HISTÓRICAS
// ═══════════════════════════════════════

// Guardar referencia a cada gráfica para actualizarlas
const graficas = {};

function crearGrafica(idCanvas, label, color) {
    const ctx = document.getElementById(idCanvas);
    if (!ctx) return null;

    // Si ya existe la destruimos antes de recrear
    if (graficas[idCanvas]) {
        graficas[idCanvas].destroy();
    }

    graficas[idCanvas] = new Chart(ctx, {
        type: "line",
        data: {
            labels:   [],
            datasets: [{
                label:           label,
                data:            [],
                borderColor:     color,
                backgroundColor: color + "22",  // color con transparencia
                borderWidth:     2,
                pointRadius:     3,
                tension:         0.3,            // línea suavizada
                fill:            true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    ticks: { maxTicksLimit: 8, font: { size: 10 } }
                },
                y: {
                    beginAtZero: false,
                    ticks: { font: { size: 10 } }
                }
            }
        }
    });

    return graficas[idCanvas];
}


async function cargarGraficas() {
    try {
        const respuesta = await fetch("/api/lecturas");
        const lecturas  = await respuesta.json();
        actualizarDecisionARM64(lecturas);

        // Separar lecturas por tipo de sensor
        const datos = {
            temperatura:            { labels: [], valores: [] },
            humedad_ambiente:       { labels: [], valores: [] },
            humedad_suelo_area1:    { labels: [], valores: [] },
            humedad_suelo_area2:    { labels: [], valores: [] },
            luz:                    { labels: [], valores: [] },
            gas:                    { labels: [], valores: [] }
        };

        function agregarDato(sensor, lectura, valor) {
            if (valor === undefined || valor === null || valor === "") return;
            if (!datos[sensor]) return;

            datos[sensor].labels.push(lectura.timestamp || "--");
            datos[sensor].valores.push(parseFloat(valor));
        }

        // las lecturas ya vienen en orden cronológico desde /api/lecturas
        lecturas.forEach(l => {
            if (l.tipo && datos[l.tipo]) {
                agregarDato(l.tipo, l, l.valor);
                return;
            }

            agregarDato("temperatura", l, l.temperatura);
            agregarDato("humedad_ambiente", l, l.humedad_ambiente);
            agregarDato("humedad_suelo_area1", l, l.humedad_suelo_area1);
            agregarDato("humedad_suelo_area2", l, l.humedad_suelo_area2);
            agregarDato("luz", l, l.luz);
            agregarDato("gas", l, l.gas);
        });

        // Crear o actualizar cada gráfica
        actualizarGrafica("grafica-temperatura", datos.temperatura,      "#e63946");
        actualizarGrafica("grafica-humedad",     datos.humedad_ambiente,  "#457b9d");
        actualizarGrafica("grafica-suelo1",      datos.humedad_suelo_area1,   "#2d6a4f");
        actualizarGrafica("grafica-suelo2",      datos.humedad_suelo_area2,   "#52b788");
        actualizarGrafica("grafica-luz",         datos.luz,               "#f4a261");
        actualizarGrafica("grafica-gas",         datos.gas,               "#6c47c4");

    } catch (error) {
        console.error("Error cargando gráficas:", error);
    }
}


async function cargarDecisionARM64() {
    try {
        const respuesta = await fetch("/api/decision-arm64/latest");
        const payload = await respuesta.json();

        if (!payload.ok) {
            limpiarDecisionARM64();
            return;
        }

        actualizarDecisionARM64([payload]);
    } catch (error) {
        console.error("Error cargando decision ARM64:", error);
        limpiarDecisionARM64();
    }
}


async function refrescarDecisionARM64EnVivo() {
    const ahora = Date.now();

    if (consultaDecisionARM64EnCurso) return;
    if (ahora - ultimaConsultaDecisionARM64 < INTERVALO_DECISION_ARM64_MS) return;

    consultaDecisionARM64EnCurso = true;
    ultimaConsultaDecisionARM64 = ahora;

    try {
        await cargarDecisionARM64();
    } finally {
        consultaDecisionARM64EnCurso = false;
    }
}


function actualizarDecisionARM64(lecturas) {
    const lectura = Array.isArray(lecturas)
        ? lecturas.find(l => l.decision_arm64 && Object.keys(l.decision_arm64).length > 0)
        : null;

    if (!lectura) {
        limpiarDecisionARM64();
        return;
    }

    const decision = lectura.decision_arm64 || {};
    setText("live-arm64-output", formatearDecisionARM64(lectura, decision));
    setText("live-arm64-accion-ejecutada", lectura.accion_ejecutada || "Sin datos");
    setText("live-arm64-resultado-actuador", lectura.resultado_actuador || "Sin datos");
    setText(
        "live-arm64-gpio-aplicado",
        lectura.gpio_aplicado === undefined || lectura.gpio_aplicado === null
            ? "Sin datos"
            : String(lectura.gpio_aplicado)
    );
}


function obtenerCampoDecisionARM64(decision, minuscula, mayuscula) {
    const valor = decision[minuscula] ?? decision[mayuscula];
    return valor === undefined || valor === null || valor === "" ? "Sin datos" : valor;
}


function formatearDecisionARM64(lectura, decision) {
    const status = lectura.status_arm64 ||
        obtenerCampoDecisionARM64(decision, "status", "STATUS");

    if (String(status).toUpperCase() === "ERROR") {
        return [
            `STATUS=${status}`,
            `ERROR=${obtenerCampoDecisionARM64(decision, "error", "ERROR")}`,
            `DETAIL=${obtenerCampoDecisionARM64(decision, "detail", "DETAIL")}`
        ].join("\n");
    }

    return [
        `ACTION=${obtenerCampoDecisionARM64(decision, "action", "ACTION")}`,
        `TARGET=${obtenerCampoDecisionARM64(decision, "target", "TARGET")}`,
        `RISK=${obtenerCampoDecisionARM64(decision, "risk", "RISK")}`,
        `REASON=${obtenerCampoDecisionARM64(decision, "reason", "REASON")}`,
        `VALUE=${obtenerCampoDecisionARM64(decision, "value", "VALUE")}`,
        `INDICATOR=${obtenerCampoDecisionARM64(decision, "indicator", "INDICATOR")}`,
        `STATUS=${status}`
    ].join("\n");
}


function limpiarDecisionARM64() {
    [
        "live-arm64-output",
        "live-arm64-accion-ejecutada",
        "live-arm64-resultado-actuador",
        "live-arm64-gpio-aplicado"
    ].forEach(id => setText(id, "Sin datos"));
}


function actualizarGrafica(idCanvas, datos, color) {
    if (!graficas[idCanvas]) {
        crearGrafica(idCanvas, idCanvas, color);
    }

    const grafica = graficas[idCanvas];
    if (!grafica) return;

    grafica.data.labels              = datos.labels;
    grafica.data.datasets[0].data    = datos.valores;
    grafica.data.datasets[0].borderColor     = color;
    grafica.data.datasets[0].backgroundColor = color + "22";
    grafica.update();
}


// ═══════════════════════════════════════
// HISTORIAL DE EVENTOS Y COMANDOS
// ═══════════════════════════════════════

async function cargarHistorial() {
    await cargarEventos();
    await cargarComandos();
}


async function cargarEventos() {
    try {
        const respuesta = await fetch("/api/eventos");
        const eventos   = await respuesta.json();
        const tbody     = document.getElementById("tabla-eventos");
        if (!tbody) return;

        if (eventos.length === 0) {
            tbody.innerHTML = "<tr><td colspan='4' style='text-align:center;color:#6c757d'>Sin eventos registrados</td></tr>";
            return;
        }

        tbody.innerHTML = eventos.map(e => `
            <tr>
                <td>${e.timestamp || "--"}</td>
                <td>${e.tipo || "--"}</td>
                <td>${e.descripcion || "--"}</td>
                <td class="nivel-${(e.nivel || "info").toLowerCase()}">
                    ${e.nivel || "INFO"}
                </td>
            </tr>
        `).join("");

    } catch (error) {
        console.error("Error cargando eventos:", error);
    }
}


async function cargarComandos() {
    try {
        const respuesta = await fetch("/api/comandos");
        const comandos  = await respuesta.json();
        const tbody     = document.getElementById("tabla-comandos");
        if (!tbody) return;

        if (comandos.length === 0) {
            tbody.innerHTML = "<tr><td colspan='4' style='text-align:center;color:#6c757d'>Sin comandos registrados</td></tr>";
            return;
        }

        tbody.innerHTML = comandos.map(c => `
            <tr>
                <td>${c.timestamp || "--"}</td>
                <td>${c.accion || "--"}</td>
                <td>${c.valor || "--"}</td>
                <td>${c.origen || "--"}</td>
            </tr>
        `).join("");

    } catch (error) {
        console.error("Error cargando comandos:", error);
    }
}


// ═══════════════════════════════════════
// RESULTADOS ARM64
// ═══════════════════════════════════════

async function cargarARM64() {
    try {
        const respuesta = await fetch("/api/arm64");
        const resultados = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(`HTTP ${respuesta.status}`);
        }

        // Quitar el placeholder de carga
        const placeholder = document.querySelector(".arm64-card.placeholder");
        if (placeholder) placeholder.style.display = "none";

        // Solo actualiza las cinco tarjetas fijas mediante setText().
        // No agrega tarjetas ni elementos dinámicos al contenedor.
        // Los resultados vienen del más reciente al más antiguo; al recorrerlos
        // al revés, el documento más reciente queda aplicado al final.
        resultados.slice().reverse().forEach(documento => {
            const resultado =
                documento.result ||
                documento.parsed ||
                documento;

            llenarModuloARM64(resultado);
        });

    } catch (error) {
        console.error("Error cargando ARM64:", error);
    }
}


function llenarModuloARM64(resultado) {
    const modulo = resultado.CALC || resultado.modulo || resultado.MODULE || "";

    if (resultado.STATUS === "ERROR") {
        mostrarErrorModuloARM64(modulo, resultado);
        return;
    }

    if (modulo === "MEDIA" || modulo === "WEIGHTED_MEAN") {
        setText("m1-total", resultado.COUNT || resultado.TOTAL_VALUES);
        setText("m1-pesos", obtenerRangoModulo(resultado) || resultado.COLUMN || "--");
        setText(
            "m1-media",
            resultado.MEAN || resultado.WEIGHTED_MEAN
        );

    } else if (modulo === "VARIANZA" || modulo === "VARIANCE") {
        setText("m2-media", resultado.MEAN);
        setText("m2-varianza", resultado.VARIANCE);
        setText("m2-desv", obtenerDesviacionVisual(resultado));

    } else if (modulo === "ANOMALIAS" || modulo === "ANOMALY_DETECTION") {
        setText("m3-media", resultado.MEAN);
        setText("m3-anomalias", resultado.ANOMALIES);
        pintarTextoConColor(
            "m3-riesgo",
            resultado.SYSTEM_RISK,
            { HIGH: "#e63946", MEDIUM: "#f4a261", NORMAL: "#2d6a4f" }
        );

    } else if (modulo === "PREDICCION" || modulo === "PREDICTION") {
        setText("m4-inicial", resultado.INITIAL_VALUE);
        setText("m4-final", resultado.FINAL_VALUE);
        setText(
            "m4-pred",
            obtenerPrediccionVisual(resultado) ||
                resultado.PREDICTED ||
                resultado.NEXT_VALUE
        );

    } else if (modulo === "TENDENCIA" || modulo === "ADVANCED_TREND") {
        setText("m5-inc", resultado.INCREMENTS);
        setText("m5-dec", resultado.DECREMENTS);
        pintarTextoConColor(
            "m5-tendencia",
            resultado.TREND,
            { UP: "#2d6a4f", DOWN: "#e63946", STABLE: "#457b9d" }
        );
    }
}


function obtenerRangoModulo(resultado) {
    if (tieneValor(resultado.WINDOW_START) && tieneValor(resultado.WINDOW_END)) {
        return `${resultado.WINDOW_START}-${resultado.WINDOW_END}`;
    }

    return "";
}


function obtenerDesviacionVisual(resultado) {
    if (tieneValor(resultado.STD_DEV)) return resultado.STD_DEV;

    const varianza = Number(resultado.VARIANCE);
    if (Number.isFinite(varianza) && varianza >= 0) {
        return String(Math.floor(Math.sqrt(varianza)));
    }

    return "--";
}


function obtenerPrediccionVisual(resultado) {
    if (tieneValor(resultado.NEXT_VALUE_X100)) {
        const valor = Number(resultado.NEXT_VALUE_X100);
        return Number.isFinite(valor) ? (valor / 100).toFixed(2) : "";
    }

    if (tieneValor(resultado.PREDICTED_X100)) {
        const valor = Number(resultado.PREDICTED_X100);
        return Number.isFinite(valor) ? (valor / 100).toFixed(2) : "";
    }

    const predictedKey = Object.keys(resultado).find(key =>
        key.startsWith("PREDICTED_")
    );

    if (predictedKey) return resultado[predictedKey];

    return "";
}


function tieneValor(valor) {
    return valor !== undefined && valor !== null && valor !== "";
}


function limpiarModuloARM64(moduleNumber) {
    const idsPorModulo = {
        1: ["m1-total", "m1-pesos", "m1-media"],
        2: ["m2-media", "m2-varianza", "m2-desv"],
        3: ["m3-media", "m3-anomalias", "m3-riesgo"],
        4: ["m4-inicial", "m4-final", "m4-pred"],
        5: ["m5-inc", "m5-dec", "m5-tendencia"]
    };

    (idsPorModulo[moduleNumber] || []).forEach(id => {
        setText(id, "--");
        const elem = document.getElementById(id);
        if (elem) elem.style.color = "";
    });
}


function mostrarErrorModuloARM64(modulo, resultado) {
    const moduloPorCalc = {
        MEDIA: 1,
        WEIGHTED_MEAN: 1,
        VARIANZA: 2,
        VARIANCE: 2,
        ANOMALIAS: 3,
        ANOMALY_DETECTION: 3,
        PREDICCION: 4,
        PREDICTION: 4,
        TENDENCIA: 5,
        ADVANCED_TREND: 5
    };

    const moduleNumber = moduloPorCalc[modulo];
    if (!moduleNumber) return;

    limpiarModuloARM64(moduleNumber);
    const idsError = {
        1: "m1-media",
        2: "m2-varianza",
        3: "m3-riesgo",
        4: "m4-pred",
        5: "m5-tendencia"
    };
    const errorText = resultado.ERROR || resultado.DETAIL || "ERROR";
    pintarTextoConColor(idsError[moduleNumber], errorText, {});
}


function pintarTextoConColor(id, valor, colores) {
    const elem = document.getElementById(id);
    if (!elem) return;

    elem.textContent = valor || "--";
    elem.style.color = colores[valor] || "#e63946";
}


async function ejecutarModulo(moduleNumber) {
    const columnSelect =
        document.getElementById(`sensor-m${moduleNumber}`) ||
        document.getElementById("arm64-column");

    const resultBox = document.getElementById(
        "resultado-arm64-reciente"
    );

    const selectedColumn = columnSelect
        ? parseInt(columnSelect.value || "2", 10)
        : 2;

    const column = Number.isInteger(selectedColumn) &&
        selectedColumn >= 2 &&
        selectedColumn <= 7
        ? selectedColumn
        : 2;

    const button = document.querySelector(
        `button[onclick="ejecutarModulo(${moduleNumber})"]`
    );

    const originalButtonText = button ? button.textContent : "";

    if (button) {
        button.disabled = true;
        button.textContent = "Ejecutando...";
    }

    if (resultBox) {
        resultBox.className = "arm64-result-box loading";
        resultBox.textContent =
            `Ejecutando módulo ARM64 ${moduleNumber}, columna ${column}...`;
    }

    limpiarModuloARM64(moduleNumber);

    try {
        const response = await fetch("/api/arm64/fase1/run", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                module_number: moduleNumber,
                column: column
            })
        });

        let payload;

        try {
            payload = await response.json();
        } catch (error) {
            throw new Error(
                `El servidor devolvió una respuesta inválida (HTTP ${response.status})`
            );
        }

        if (!response.ok || !payload.ok) {
            const errorResult = payload.data?.parsed || {
                CALC: moduleNumberToCalc(moduleNumber),
                STATUS: "ERROR",
                ERROR: payload.error || "ERROR",
                DETAIL: payload.detail
            };
            mostrarErrorModuloARM64(errorResult.CALC, errorResult);

            if (resultBox) {
                resultBox.className = "arm64-result-box error";
                resultBox.textContent =
                    "ERROR ARM64\n" +
                    JSON.stringify(payload, null, 2);
            }
            return;
        }

        const parsed = payload.data?.parsed || {};

        if (resultBox) {
            resultBox.className = "arm64-result-box success";
            resultBox.textContent =
                "RESULTADO ARM64\n" +
                JSON.stringify(parsed, null, 2);
        }

        // Actualización inmediata de la tarjeta correspondiente.
        llenarModuloARM64(parsed);

        // Recargar los resultados persistidos desde MongoDB.
        await cargarARM64();

    } catch (error) {
        if (resultBox) {
            resultBox.className = "arm64-result-box error";
            resultBox.textContent =
                "ERROR DE CONEXIÓN\n" +
                (error.message || String(error));
        }

        console.error("Error ejecutando módulo ARM64:", error);

    } finally {
        if (button) {
            button.disabled = false;
            button.textContent = originalButtonText;
        }
    }
}


window.ejecutarModulo = ejecutarModulo;


const MODULOS_FASE2 = {
    1: "modulo_1_rmse",
    2: "modulo_2_regresion",
    3: "modulo_3_prediccion_futura",
    4: "modulo_4_integral_error",
    5: "modulo_5_derivada_local"
};
const COLUMNAS_FASE2 = new Set([
    "TEMP",
    "HUM_AIRE",
    "SOIL1",
    "SOIL2",
    "LUZ",
    "GAS"
]);


function crearInputARM64(id, type, value, attrs = {}) {
    const input = document.createElement("input");
    input.id = id;
    input.type = type;
    input.value = value;
    Object.entries(attrs).forEach(([key, val]) => input.setAttribute(key, val));
    return input;
}


function prepararControlesFase2Historicos() {
    for (let moduleNumber = 1; moduleNumber <= 5; moduleNumber += 1) {
        const control = document.getElementById(`fase2-column-${moduleNumber}`)?.parentElement;
        if (!control || document.getElementById(`fase2-file-${moduleNumber}`)) continue;

        const button = control.querySelector("button");
        control.insertBefore(
            crearInputARM64(`fase2-file-${moduleNumber}`, "text", "lecturas.csv", {
                "aria-label": `Archivo CSV Fase 2 módulo ${moduleNumber}`
            }),
            button
        );
        control.insertBefore(
            crearInputARM64(`fase2-start-${moduleNumber}`, "number", "1", {
                min: "1",
                step: "1",
                "aria-label": `Línea inicial Fase 2 módulo ${moduleNumber}`
            }),
            button
        );
        control.insertBefore(
            crearInputARM64(`fase2-end-${moduleNumber}`, "number", "30", {
                min: "1",
                step: "1",
                "aria-label": `Línea final Fase 2 módulo ${moduleNumber}`
            }),
            button
        );
    }
}


function idsModuloFase2(moduleNumber) {
    return {
        1: ["f2-1-count", "f2-1-ideal", "f2-1-rmse", "f2-1-status"],
        2: ["f2-2-count", "f2-2-slope", "f2-2-trend", "f2-2-status"],
        3: ["f2-3-count", "f2-3-k", "f2-3-slope", "f2-3-predicted", "f2-3-status"],
        4: ["f2-4-count", "f2-4-ideal", "f2-4-error-integral", "f2-4-status"],
        5: ["f2-5-count", "f2-5-window-size", "f2-5-max-slope", "f2-5-status"]
    }[moduleNumber] || [];
}


function limpiarModuloFase2(moduleNumber) {
    idsModuloFase2(moduleNumber).forEach(id => {
        setText(id, "--");
        const elem = document.getElementById(id);
        if (elem) elem.style.color = "";
    });
}


function valorResultadoFase2(resultado, ...keys) {
    for (const key of keys) {
        if (tieneValor(resultado[key])) return resultado[key];
    }
    return "--";
}


function pintarModuloFase2(moduleNumber, resultado) {
    const status = valorResultadoFase2(resultado, "STATUS", "status");

    if (moduleNumber === 1) {
        setText("f2-1-count", valorResultadoFase2(resultado, "COUNT"));
        setText("f2-1-ideal", valorResultadoFase2(resultado, "IDEAL"));
        setText("f2-1-rmse", valorResultadoFase2(resultado, "RMSE"));
        setText("f2-1-status", status);

    } else if (moduleNumber === 2) {
        setText("f2-2-count", valorResultadoFase2(resultado, "COUNT"));
        setText("f2-2-slope", valorResultadoFase2(resultado, "SLOPE_X100"));
        setText("f2-2-trend", valorResultadoFase2(resultado, "TREND"));
        setText("f2-2-status", status);

    } else if (moduleNumber === 3) {
        setText("f2-3-count", valorResultadoFase2(resultado, "COUNT"));
        setText("f2-3-k", valorResultadoFase2(resultado, "K"));
        setText("f2-3-slope", valorResultadoFase2(resultado, "SLOPE_X100"));
        setText("f2-3-predicted", obtenerPrediccionFase2(resultado));
        setText("f2-3-status", status);

    } else if (moduleNumber === 4) {
        setText("f2-4-count", valorResultadoFase2(resultado, "COUNT"));
        setText("f2-4-ideal", valorResultadoFase2(resultado, "IDEAL"));
        setText("f2-4-error-integral", valorResultadoFase2(resultado, "ERROR_INTEGRAL"));
        setText("f2-4-status", status);

    } else if (moduleNumber === 5) {
        setText("f2-5-count", valorResultadoFase2(resultado, "COUNT"));
        setText("f2-5-window-size", valorResultadoFase2(resultado, "WINDOW_SIZE"));
        setText("f2-5-max-slope", valorResultadoFase2(resultado, "MAX_LOCAL_SLOPE_X100"));
        setText("f2-5-status", status);
    }
}


function obtenerPrediccionFase2(resultado) {
    if (tieneValor(resultado.PREDICTED_5)) return resultado.PREDICTED_5;
    if (tieneValor(resultado.PREDICTED_K)) return resultado.PREDICTED_K;

    const predictedKey = Object.keys(resultado).find(key =>
        key.startsWith("PREDICTED_")
    );

    return predictedKey ? resultado[predictedKey] : "--";
}


function obtenerPayloadFase2(moduleNumber) {
    const columnSelect = document.getElementById(`fase2-column-${moduleNumber}`);
    const fileInput = document.getElementById(`fase2-file-${moduleNumber}`);
    const startInput = document.getElementById(`fase2-start-${moduleNumber}`);
    const endInput = document.getElementById(`fase2-end-${moduleNumber}`);
    const idealInput = document.getElementById(`fase2-ideal-${moduleNumber}`);
    const kInput = document.getElementById(`fase2-k-${moduleNumber}`);
    const selectedColumn = columnSelect ? columnSelect.value : "TEMP";
    const column = COLUMNAS_FASE2.has(selectedColumn) ? selectedColumn : "TEMP";

    return {
        module_number: moduleNumber,
        module_name: MODULOS_FASE2[moduleNumber],
        file_path: fileInput ? fileInput.value.trim() || "lecturas.csv" : "lecturas.csv",
        start_line: startInput ? Number(startInput.value) : 1,
        end_line: endInput ? Number(endInput.value) : 30,
        column: column,
        ideal: idealInput ? idealInput.value || 25 : 25,
        k: kInput ? kInput.value || 5 : 5
    };
}


async function ejecutarModuloFase2(moduleNumber) {
    const resultBox = document.getElementById("resultado-arm64-reciente");
    const button = document.querySelector(
        `button[onclick="ejecutarModuloFase2(${moduleNumber})"]`
    );
    const originalButtonText = button ? button.textContent : "";

    if (button) {
        button.disabled = true;
        button.textContent = "Ejecutando...";
    }

    limpiarModuloFase2(moduleNumber);

    if (resultBox) {
        resultBox.className = "arm64-result-box loading";
        resultBox.textContent = `Ejecutando ${MODULOS_FASE2[moduleNumber]}...`;
    }

    try {
        const response = await fetch("/api/arm64/fase2/run", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(obtenerPayloadFase2(moduleNumber))
        });

        const payload = await response.json();
        const parsed = payload.parsed || payload.data?.parsed || {};

        if (!response.ok || !payload.ok) {
            pintarModuloFase2(moduleNumber, {
                STATUS: "ERROR",
                ERROR: payload.error || "ERROR",
                DETAIL: payload.detail || ""
            });

            if (resultBox) {
                resultBox.className = "arm64-result-box error";
                resultBox.textContent =
                    "ERROR ARM64 FASE 2\n" +
                    JSON.stringify(payload, null, 2);
            }
            return;
        }

        pintarModuloFase2(moduleNumber, parsed);

        if (resultBox) {
            resultBox.className = "arm64-result-box success";
            resultBox.textContent =
                "RESULTADO ARM64 FASE 2\n" +
                JSON.stringify(parsed, null, 2);
        }

    } catch (error) {
        if (resultBox) {
            resultBox.className = "arm64-result-box error";
            resultBox.textContent =
                "ERROR DE CONEXIÓN\n" +
                (error.message || String(error));
        }

        console.error("Error ejecutando módulo ARM64 Fase 2:", error);

    } finally {
        if (button) {
            button.disabled = false;
            button.textContent = originalButtonText;
        }
    }
}


window.ejecutarModuloFase2 = ejecutarModuloFase2;


function moduleNumberToCalc(moduleNumber) {
    return {
        1: "MEDIA",
        2: "VARIANZA",
        3: "ANOMALIAS",
        4: "PREDICCION",
        5: "TENDENCIA"
    }[moduleNumber] || "";
}


async function ejecutarAnalisisHistorico() {
    const fileInput = document.getElementById("historical-file-path");
    const startInput = document.getElementById("historical-start-line");
    const endInput = document.getElementById("historical-end-line");
    const columnSelect = document.getElementById("historical-column");
    const idealInput = document.getElementById("historical-ideal");
    const kInput = document.getElementById("historical-k");
    const resultBox = document.getElementById(
        "resultado-historico-arm64"
    );
    const button = document.getElementById("btn-historical-arm64");

    const filePath = fileInput ? fileInput.value.trim() : "";
    const startLine = startInput ? Number(startInput.value) : NaN;
    const endLine = endInput ? Number(endInput.value) : NaN;
    const column = columnSelect ? columnSelect.value : "";
    const ideal = idealInput ? Number(idealInput.value) : 25;
    const k = kInput ? Number(kInput.value) : 10;

    const validColumns = new Set([
        "TEMP",
        "HUM_AIRE",
        "SOIL1",
        "SOIL2",
        "LUZ",
        "GAS"
    ]);

    function showValidationError(message) {
        pintarErrorTarjetaARM64("historical-full", message, {
            error: "VALIDATION_ERROR"
        });
    }

    if (!filePath) {
        showValidationError("El archivo CSV no puede estar vacío.");
        return;
    }

    if (!Number.isInteger(startLine) || startLine < 1) {
        showValidationError(
            "La línea inicial debe ser un entero mayor o igual a 1."
        );
        return;
    }

    if (!Number.isInteger(endLine) || endLine < startLine) {
        showValidationError(
            "La línea final debe ser un entero mayor o igual a la inicial."
        );
        return;
    }

    if (!validColumns.has(column)) {
        showValidationError("La columna seleccionada no es válida.");
        return;
    }

    if (!Number.isInteger(ideal) || ideal < 1 || !Number.isInteger(k) || k < 1) {
        showValidationError("IDEAL y K deben ser enteros mayores o iguales a 1.");
        return;
    }

    const originalButtonText = button ? button.textContent : "";

    if (button) {
        button.disabled = true;
        button.textContent = "Ejecutando...";
    }

    if (resultBox) {
        resultBox.className =
            "arm64-result-box historical-result-box loading";
        resultBox.textContent = "Ejecutando análisis histórico...";
    }

    try {
        const response = await fetch("/api/arm64/historical/run", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                file_path: filePath,
                start_line: startLine,
                end_line: endLine,
                column: column,
                ideal: ideal,
                k: k
            })
        });

        const payload = await response.json();

        if (!response.ok || !payload.ok) {
            const errorName =
                payload.error || "HISTORICAL_ANALYSIS_FAILED";
            const detail =
                payload.detail ||
                payload.data?.detail ||
                "El análisis histórico no pudo completarse.";

            pintarErrorTarjetaARM64("historical-full", detail, {
                error: errorName
            });
            return;
        }

        const outputText =
            payload.data?.output_text ||
            payload.raw_output ||
            "";
        const parsed = payload.data?.parsed || {};

        pintarResultadoTarjetaARM64("historical-full", parsed, outputText);

        if (typeof cargarARM64 === "function") {
            await cargarARM64();
        }

    } catch (error) {
        pintarErrorTarjetaARM64(
            "historical-full",
            error.message || String(error),
            { error: "CONNECTION_ERROR" }
        );

        console.error(
            "Error ejecutando análisis histórico ARM64:",
            error
        );

    } finally {
        if (button) {
            button.disabled = false;
            button.textContent = originalButtonText;
        }
    }
}


window.ejecutarAnalisisHistorico = ejecutarAnalisisHistorico;


// Función auxiliar para poner texto en un elemento
function setText(id, valor) {
    const elem = document.getElementById(id);
    if (elem) elem.textContent = valor !== undefined ? valor : "--";
}


// ═══════════════════════════════════════
// ENVÍO DE COMANDOS
// ═══════════════════════════════════════

async function enviarComando(accion, valor) {
    try {
        const respuesta = await fetch("/api/comando", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ accion, valor })
        });

        const resultado = await respuesta.json();

        if (resultado.ok) {
            mostrarNotificacion(`✅ Comando enviado: ${accion} → ${valor}`);
        } else {
            mostrarNotificacion(`❌ Error: ${resultado.error}`, true);
        }

    } catch (error) {
        mostrarNotificacion("❌ Error de conexión con el servidor", true);
        console.error("Error enviando comando:", error);
    }
}


async function cambiarModo(modo) {
    try {
        const respuesta = await fetch("/api/modo", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ modo })
        });

        const resultado = await respuesta.json();

        if (resultado.ok) {
            const elemModo = document.getElementById("modo-actual");
            if (elemModo) elemModo.textContent = resultado.modo || modo;
            mostrarNotificacion(`✅ Modo cambiado a: ${resultado.modo || modo}`);
        } else {
            mostrarNotificacion(`❌ Error: ${resultado.error}`, true);
        }

    } catch (error) {
        mostrarNotificacion("❌ Error de conexión con el servidor", true);
        console.error("Error cambiando modo:", error);
    }
}


function mostrarNotificacion(mensaje, esError = false) {
    const notif = document.getElementById("notificacion");
    if (!notif) return;

    notif.textContent = mensaje;
    notif.className   = "notificacion";

    if (esError) {
        notif.style.background = "#f8d7da";
        notif.style.color      = "#842029";
    } else {
        notif.style.background = "";
        notif.style.color      = "";
    }

    notif.classList.remove("oculto");

    // Ocultar después de 3 segundos
    setTimeout(() => {
        notif.classList.add("oculto");
    }, 3000);
}


// ═══════════════════════════════════════
// TARJETAS ARM64 NUEVAS
// ═══════════════════════════════════════

const ARM64_COLUMNAS = [
    ["TEMP", "Temperatura"],
    ["HUM_AIRE", "Humedad aire"],
    ["SOIL1", "Suelo 1"],
    ["SOIL2", "Suelo 2"],
    ["LUZ", "Luz"],
    ["GAS", "Gas"]
];

const ARM64_FASE1_CARDS = [
    { number: 1, title: "Media", resultKeys: ["CALC", "COLUMN", "WINDOW_START", "WINDOW_END", "COUNT", "MEAN", "STATUS"] },
    { number: 2, title: "Varianza y desviación", resultKeys: ["CALC", "COLUMN", "WINDOW_START", "WINDOW_END", "COUNT", "MEAN", "VARIANCE", "STD_DEV", "STATUS"] },
    { number: 3, title: "Detección de anomalías", resultKeys: ["CALC", "COLUMN", "WINDOW_START", "WINDOW_END", "COUNT", "MEAN", "STD_DEV", "ANOMALIES", "SYSTEM_RISK", "STATUS"] },
    { number: 4, title: "Predicción lineal", resultKeys: ["CALC", "COLUMN", "WINDOW_START", "WINDOW_END", "COUNT", "INITIAL_VALUE", "FINAL_VALUE", "TOTAL_DIFF", "AVG_CHANGE_X100", "NEXT_VALUE_X100", "STATUS"] },
    { number: 5, title: "Tendencia acumulada", resultKeys: ["CALC", "COLUMN", "WINDOW_START", "WINDOW_END", "COUNT", "INCREMENTS", "DECREMENTS", "MAX_UP_STREAK", "MAX_DOWN_STREAK", "ACCUM_DIFF", "TREND", "STATUS"] }
];

const ARM64_FASE2_CARDS = [
    { number: 1, title: "RMSE", moduleName: "modulo_1_rmse", ideal: true, resultKeys: ["CALC", "COLUMN", "WINDOW_START", "WINDOW_END", "COUNT", "IDEAL", "MSE", "RMSE", "STATUS"] },
    { number: 2, title: "Regresión lineal", moduleName: "modulo_2_regresion", resultKeys: ["CALC", "COLUMN", "WINDOW_START", "WINDOW_END", "COUNT", "SLOPE_X100", "INTERCEPT_X100", "TREND", "STATUS"] },
    { number: 3, title: "Predicción futura", moduleName: "modulo_3_prediccion_futura", k: true, resultKeys: ["CALC", "COLUMN", "WINDOW_START", "WINDOW_END", "COUNT", "K", "SLOPE_X100", "PREDICTED_5", "PREDICTED_K", "STATUS"] },
    { number: 4, title: "Integral del error", moduleName: "modulo_4_integral_error", ideal: true, resultKeys: ["CALC", "COLUMN", "WINDOW_START", "WINDOW_END", "COUNT", "IDEAL", "ERROR_INTEGRAL", "MEAN_ABS_ERROR", "STATUS"] },
    { number: 5, title: "Derivada local", moduleName: "modulo_5_derivada_local", resultKeys: ["CALC", "COLUMN", "WINDOW_START", "WINDOW_END", "COUNT", "WINDOW_SIZE", "MAX_LOCAL_SLOPE_X100", "STATUS"] }
];

let arm64CardsRendered = false;

function opcionesColumnasARM64() {
    return ARM64_COLUMNAS.map(([value, label]) =>
        `<option value="${value}">${label}</option>`
    ).join("");
}

function campoARM64(id, label, type, value, extra = "") {
    return `
        <label class="arm64-field">
            <span>${label}</span>
            <input id="${id}" type="${type}" value="${value}" ${extra}>
        </label>
    `;
}

function selectorColumnaARM64(id) {
    return `
        <label class="arm64-field">
            <span>Columna</span>
            <select id="${id}">${opcionesColumnasARM64()}</select>
        </label>
    `;
}

function crearTarjetaModuloARM64(phase, config) {
    const prefix = `${phase}-${config.number}`;
    const extraFields = [
        config.ideal ? campoARM64(`${prefix}-ideal`, "Ideal", "number", "25", "step=\"1\"") : "",
        config.k ? campoARM64(`${prefix}-k`, "K futuro", "number", "5", "min=\"1\" step=\"1\"") : ""
    ].join("");
    const rows = config.resultKeys.map(key => `
        <div class="arm64-fila">
            <span>${key}</span>
            <strong data-arm64-key="${key}">--</strong>
        </div>
    `).join("");

    return `
        <div class="card arm64-card" data-arm64-card="${prefix}">
            <div class="arm64-header">
                <span class="arm64-num">${phase === "fase1" ? "F1" : "F2"}-${config.number}</span>
                <h3>${config.title}</h3>
            </div>
            <div class="arm64-form-grid">
                ${campoARM64(`${prefix}-file`, "Archivo CSV", "text", "lecturas.csv")}
                ${campoARM64(`${prefix}-start`, "Línea inicial", "number", "1", "min=\"1\" step=\"1\"")}
                ${campoARM64(`${prefix}-end`, "Línea final", "number", "10", "min=\"1\" step=\"1\"")}
                ${selectorColumnaARM64(`${prefix}-column`)}
                ${extraFields}
            </div>
            <button class="btn btn-success arm64-run-btn" type="button" onclick="ejecutarTarjetaARM64('${phase}', ${config.number})">
                Ejecutar
            </button>
            <div class="arm64-datos">${rows}</div>
            <pre class="arm64-result-box arm64-card-result" aria-live="polite">Sin ejecutar.</pre>
        </div>
    `;
}

function crearTarjetaHistoricaARM64() {
    const rows = ["CALC", "COLUMN", "WINDOW_START", "WINDOW_END", "COUNT", "IDEAL", "K", "RMSE", "TREND", "RECOMMENDATION", "STATUS"].map(key => `
        <div class="arm64-fila">
            <span>${key}</span>
            <strong data-arm64-key="${key}">--</strong>
        </div>
    `).join("");

    return `
        <div class="card arm64-card historical-arm64-card" data-arm64-card="historical-full">
            <div class="arm64-header">
                <span class="arm64-num">H</span>
                <h3>Analizador histórico completo</h3>
            </div>
            <div class="arm64-form-grid">
                ${campoARM64("historical-file-path", "Archivo CSV", "text", "lecturas.csv")}
                ${campoARM64("historical-start-line", "Línea inicial", "number", "1", "min=\"1\" step=\"1\"")}
                ${campoARM64("historical-end-line", "Línea final", "number", "10", "min=\"1\" step=\"1\"")}
                ${selectorColumnaARM64("historical-column")}
                ${campoARM64("historical-ideal", "Ideal", "number", "55", "step=\"1\"")}
                ${campoARM64("historical-k", "K futuro", "number", "10", "min=\"1\" step=\"1\"")}
            </div>
            <button class="btn btn-success arm64-run-btn" type="button" id="btn-historical-arm64" onclick="ejecutarAnalisisHistorico()">
                Ejecutar
            </button>
            <div class="arm64-datos">${rows}</div>
            <pre id="resultado-historico-arm64" class="arm64-result-box arm64-card-result" aria-live="polite">Sin ejecutar.</pre>
        </div>
    `;
}

function renderArm64Cards() {
    if (arm64CardsRendered) return;

    const fase1Grid = document.getElementById("grid-arm64-fase1");
    const fase2Grid = document.getElementById("grid-arm64-fase2");
    const historicalGrid = document.getElementById("grid-arm64-historical");

    if (fase1Grid) {
        fase1Grid.innerHTML = ARM64_FASE1_CARDS.map(card =>
            crearTarjetaModuloARM64("fase1", card)
        ).join("");
    }

    if (fase2Grid) {
        fase2Grid.innerHTML = ARM64_FASE2_CARDS.map(card =>
            crearTarjetaModuloARM64("fase2", card)
        ).join("");
    }

    if (historicalGrid) {
        historicalGrid.innerHTML = crearTarjetaHistoricaARM64();
    }

    arm64CardsRendered = true;
}

function getArm64Card(cardId) {
    return document.querySelector(`[data-arm64-card="${cardId}"]`);
}

function valorInputARM64(id, fallback) {
    const elem = document.getElementById(id);
    const value = elem ? elem.value : "";
    return value === "" ? fallback : value;
}

function payloadTarjetaARM64(phase, moduleNumber) {
    const prefix = `${phase}-${moduleNumber}`;
    const config = phase === "fase2"
        ? ARM64_FASE2_CARDS.find(card => card.number === moduleNumber)
        : null;
    const payload = {
        module_number: moduleNumber,
        file_path: valorInputARM64(`${prefix}-file`, "lecturas.csv").trim() || "lecturas.csv",
        start_line: Number(valorInputARM64(`${prefix}-start`, "1")),
        end_line: Number(valorInputARM64(`${prefix}-end`, "10")),
        column: valorInputARM64(`${prefix}-column`, "TEMP")
    };

    if (config?.moduleName) payload.module_name = config.moduleName;
    if (config?.ideal) payload.ideal = Number(valorInputARM64(`${prefix}-ideal`, "25"));
    if (config?.k) payload.k = Number(valorInputARM64(`${prefix}-k`, "5"));

    return payload;
}

function validarPayloadARM64(payload, needs = {}) {
    if (!payload.file_path) return "Archivo CSV no puede estar vacío.";
    if (!Number.isInteger(payload.start_line) || payload.start_line < 1) {
        return "Línea inicial debe ser un entero mayor o igual a 1.";
    }
    if (!Number.isInteger(payload.end_line) || payload.end_line < payload.start_line) {
        return "Línea final debe ser mayor o igual a línea inicial.";
    }
    if (!ARM64_COLUMNAS.some(([value]) => value === payload.column)) {
        return "Columna no válida.";
    }
    if (needs.ideal && !Number.isFinite(payload.ideal)) return "Ideal debe ser numérico.";
    if (needs.k && (!Number.isInteger(payload.k) || payload.k < 1)) {
        return "K futuro debe ser un entero mayor o igual a 1.";
    }
    return "";
}

function pintarResultadoTarjetaARM64(cardId, parsed, rawText = "") {
    const card = getArm64Card(cardId);
    if (!card) return;

    card.querySelectorAll("[data-arm64-key]").forEach(elem => {
        const key = elem.getAttribute("data-arm64-key");
        elem.textContent = parsed[key] ?? "--";
        elem.style.color = parsed.STATUS === "ERROR" ? "#e63946" : "";
    });

    const resultBox = card.querySelector(".arm64-card-result");
    if (resultBox) {
        resultBox.className = "arm64-result-box arm64-card-result " +
            (parsed.STATUS === "ERROR" ? "error" : "success");
        resultBox.textContent = rawText || Object.entries(parsed)
            .map(([key, value]) => `${key}=${value}`)
            .join("\n");
    }
}

function pintarErrorTarjetaARM64(cardId, message, payload = {}) {
    const card = getArm64Card(cardId);
    if (!card) return;

    card.querySelectorAll("[data-arm64-key]").forEach(elem => {
        const key = elem.getAttribute("data-arm64-key");
        elem.textContent = key === "STATUS" ? "ERROR" : "--";
        elem.style.color = key === "STATUS" ? "#e63946" : "";
    });

    const resultBox = card.querySelector(".arm64-card-result");
    if (resultBox) {
        resultBox.className = "arm64-result-box arm64-card-result error";
        resultBox.textContent = [
            "STATUS=ERROR",
            `ERROR=${payload.error || "ERROR"}`,
            `DETAIL=${message}`
        ].join("\n");
    }
}

async function ejecutarTarjetaARM64(phase, moduleNumber) {
    renderArm64Cards();
    const cardId = `${phase}-${moduleNumber}`;
    const card = getArm64Card(cardId);
    const config = phase === "fase2"
        ? ARM64_FASE2_CARDS.find(item => item.number === moduleNumber)
        : {};
    const payload = payloadTarjetaARM64(phase, moduleNumber);
    const validationError = validarPayloadARM64(payload, config || {});

    if (validationError) {
        pintarErrorTarjetaARM64(cardId, validationError, { error: "VALIDATION_ERROR" });
        return;
    }

    const button = card?.querySelector(".arm64-run-btn");
    const previousText = button ? button.textContent : "";

    if (button) {
        button.disabled = true;
        button.textContent = "Ejecutando...";
    }

    const resultBox = card?.querySelector(".arm64-card-result");
    if (resultBox) {
        resultBox.className = "arm64-result-box arm64-card-result loading";
        resultBox.textContent = "Ejecutando módulo ARM64...";
    }

    try {
        const response = await fetch(
            phase === "fase1" ? "/api/arm64/fase1/run" : "/api/arm64/fase2/run",
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            }
        );
        const data = await response.json();
        const parsed = data.data?.parsed || data.parsed || {};
        const rawText = data.data?.output_text || data.raw_output || "";

        if (!response.ok || !data.ok) {
            pintarErrorTarjetaARM64(
                cardId,
                data.detail || parsed.DETAIL || "El módulo ARM64 no pudo ejecutarse.",
                data
            );
            return;
        }

        pintarResultadoTarjetaARM64(cardId, parsed, rawText);
    } catch (error) {
        pintarErrorTarjetaARM64(cardId, error.message || String(error), {
            error: "CONNECTION_ERROR"
        });
    } finally {
        if (button) {
            button.disabled = false;
            button.textContent = previousText;
        }
    }
}

async function ejecutarModulo(moduleNumber) {
    await ejecutarTarjetaARM64("fase1", moduleNumber);
}

async function ejecutarModuloFase2(moduleNumber) {
    await ejecutarTarjetaARM64("fase2", moduleNumber);
}

async function cargarARM64() {
    renderArm64Cards();
}

window.ejecutarModulo = ejecutarModulo;
window.ejecutarModuloFase2 = ejecutarModuloFase2;


// ═══════════════════════════════════════
// INICIO
// ═══════════════════════════════════════

// Cuando carga la página, pedir el estado actual al servidor
window.addEventListener("load", async function() {
    renderArm64Cards();
    try {
        const respuesta = await fetch("/api/estado");
        const datos     = await respuesta.json();
        actualizarPanel(datos);
        await cargarDecisionARM64();
    } catch (error) {
        console.log("Servidor no disponible aún");
    }
});
