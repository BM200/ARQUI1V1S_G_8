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
    actualizarSensor("suelo1",       datos.humedad_suelo_area1,  30, 70, "%");
    actualizarSensor("suelo2",       datos.humedad_suelo_area2,  30, 70, "%");
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
    if (elemValor) elemValor.textContent = valor || "--";

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
        // Para el suelo la lógica es diferente
        if (num < minNormal) {
            elemEstado.textContent = "SECO";
            elemEstado.className   = "sensor-estado advertencia";
        } else if (num > maxNormal) {
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

        // las lecturas vienen de mas reciente a mas antigua
        // se invierten para graficar de izquierda a derecha
        lecturas.slice().reverse().forEach(l => {
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
    1: "modulo_rmse",
    2: "modulo_2_regresion",
    3: "modulo_3_prediccion",
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
    const idealInput = document.getElementById(`fase2-ideal-${moduleNumber}`);
    const kInput = document.getElementById(`fase2-k-${moduleNumber}`);
    const selectedColumn = columnSelect ? columnSelect.value : "TEMP";
    const column = COLUMNAS_FASE2.has(selectedColumn) ? selectedColumn : "TEMP";

    return {
        module_number: moduleNumber,
        module_name: MODULOS_FASE2[moduleNumber],
        file_path: "lecturas.csv",
        start_line: 1,
        end_line: 30,
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
    const resultBox = document.getElementById(
        "resultado-historico-arm64"
    );
    const button = document.getElementById("btn-historical-arm64");

    const filePath = fileInput ? fileInput.value.trim() : "";
    const startLine = startInput ? Number(startInput.value) : NaN;
    const endLine = endInput ? Number(endInput.value) : NaN;
    const column = columnSelect ? columnSelect.value : "";

    const validColumns = new Set([
        "TEMP",
        "HUM_AIRE",
        "SOIL1",
        "SOIL2",
        "LUZ",
        "GAS"
    ]);

    function showValidationError(message) {
        if (resultBox) {
            resultBox.className =
                "arm64-result-box historical-result-box error";
            resultBox.textContent =
                "ERROR DE VALIDACIÓN\n" + message;
        }
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
                column: column
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

            if (resultBox) {
                resultBox.className =
                    "arm64-result-box historical-result-box error";
                resultBox.textContent =
                    `ERROR: ${errorName}\nDETAIL: ${detail}`;
            }
            return;
        }

        const outputText =
            payload.data?.output_text ||
            payload.raw_output ||
            "";
        const parsed = payload.data?.parsed || {};

        if (resultBox) {
            resultBox.className =
                "arm64-result-box historical-result-box success";
            resultBox.textContent =
                "RESULTADO HISTÓRICO ARM64\n" +
                (outputText || JSON.stringify(parsed, null, 2));
        }

        if (typeof cargarARM64 === "function") {
            await cargarARM64();
        }

    } catch (error) {
        if (resultBox) {
            resultBox.className =
                "arm64-result-box historical-result-box error";
            resultBox.textContent =
                "ERROR DE CONEXIÓN\n" +
                (error.message || String(error));
        }

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
            if (elemModo) elemModo.textContent = modo;
            mostrarNotificacion(`✅ Modo cambiado a: ${modo}`);
        }

    } catch (error) {
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
// INICIO
// ═══════════════════════════════════════

// Cuando carga la página, pedir el estado actual al servidor
window.addEventListener("load", async function() {
    try {
        const respuesta = await fetch("/api/estado");
        const datos     = await respuesta.json();
        actualizarPanel(datos);
        await cargarDecisionARM64();
    } catch (error) {
        console.log("Servidor no disponible aún");
    }
});
