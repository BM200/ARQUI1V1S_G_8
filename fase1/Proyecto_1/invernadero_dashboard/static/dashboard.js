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

// Cuando el servidor envía una actualización de datos
socket.on("actualizacion", function(datos) {
    actualizarPanel(datos);
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

        // Separar lecturas por tipo de sensor
        const datos = {
            temperatura:            { labels: [], valores: [] },
            humedad_ambiente:       { labels: [], valores: [] },
            humedad_suelo_area1:    { labels: [], valores: [] },
            humedad_suelo_area2:    { labels: [], valores: [] },
            luz:                    { labels: [], valores: [] },
            gas:                    { labels: [], valores: [] }
        };

        // Las lecturas vienen de más reciente a más antigua
        // las invertimos para que la gráfica vaya de izquierda a derecha
        lecturas.reverse().forEach(l => {
            if (datos[l.tipo]) {
                datos[l.tipo].labels.push(l.timestamp);
                datos[l.tipo].valores.push(parseFloat(l.valor));
            }
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
        const respuesta  = await fetch("/api/arm64");
        const resultados = await respuesta.json();

        // Quitar el placeholder de carga
        const placeholder = document.querySelector(".arm64-card.placeholder");
        if (placeholder) placeholder.style.display = "none";

        // Llenar cada módulo con sus datos
        resultados.forEach(r => {
            llenarModuloARM64(r);
        });

    } catch (error) {
        console.error("Error cargando ARM64:", error);
    }
}


function llenarModuloARM64(resultado) {
    const modulo = resultado.modulo || resultado.MODULE || "";

    if (modulo === "WEIGHTED_MEAN") {
        setText("m1-total",  resultado.TOTAL_VALUES);
        setText("m1-pesos",  resultado.WEIGHT_SUM);
        setText("m1-media",  resultado.WEIGHTED_MEAN);

    } else if (modulo === "VARIANCE") {
        setText("m2-media",   resultado.MEAN);
        setText("m2-varianza",resultado.VARIANCE);
        setText("m2-desv",    resultado.STD_DEV);

    } else if (modulo === "ANOMALY_DETECTION") {
        setText("m3-media",    resultado.MEAN);
        setText("m3-anomalias",resultado.ANOMALIES);
        // Colorear el riesgo según nivel
        const elemRiesgo = document.getElementById("m3-riesgo");
        if (elemRiesgo) {
            elemRiesgo.textContent = resultado.SYSTEM_RISK || "--";
            const colores = { HIGH: "#e63946", MEDIUM: "#f4a261", NORMAL: "#2d6a4f" };
            elemRiesgo.style.color = colores[resultado.SYSTEM_RISK] || "#212529";
        }

    } else if (modulo === "PREDICTION") {
        setText("m4-inicial", resultado.INITIAL_VALUE);
        setText("m4-final",   resultado.FINAL_VALUE);
        setText("m4-pred",    resultado.NEXT_VALUE);

    } else if (modulo === "ADVANCED_TREND") {
        setText("m5-inc", resultado.INCREMENTS);
        setText("m5-dec", resultado.DECREMENTS);
        // Colorear la tendencia
        const elemTend = document.getElementById("m5-tendencia");
        if (elemTend) {
            elemTend.textContent = resultado.TREND || "--";
            const colores = { UP: "#2d6a4f", DOWN: "#e63946", STABLE: "#457b9d" };
            elemTend.style.color = colores[resultado.TREND] || "#212529";
        }
    }
}


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
    } catch (error) {
        console.log("Servidor no disponible aún");
    }
});