function runAnalysis(route) {
    const output = document.getElementById("result-output");

    output.classList.remove("fade-in-fast");
    void output.offsetWidth; // reset animation

    output.innerText = "⏳ Ejecutando análisis... Por favor espere.";

    fetch(route)
        .then(response => response.text())
        .then(textData => {
            output.innerText = textData;
            output.classList.add("fade-in-fast");
        })
        .catch(err => {
            output.innerText = "❌ Error al ejecutar el análisis o al obtener la respuesta.";
            console.error("Error en la ruta:", route, err);
        });
}

function viewMstVisualization() {
    window.open('/visualizar-mst', '_blank');
}

function runAnalysis(route) {
    const output = document.getElementById("result-output");

    // Reiniciar animación y mostrar estado de carga
    output.classList.remove("fade-in-fast");
    void output.offsetWidth; // Trigger reflow for reset
    output.innerText = "⏳ Ejecutando análisis... Por favor espere. Ruta: " + route;

    fetch(route)
        .then(response => response.text())
        .then(textData => {
            output.innerText = textData;
            output.classList.add("fade-in-fast");
            output.scrollTop = output.scrollHeight; // Scroll al final del resultado
        })
        .catch(err => {
            output.innerText = `❌ Error al ejecutar el análisis (${route}). Consulte la consola para detalles.`;
            console.error("Error en la ruta:", route, err);
        });
}

function createRipple(e) {
    const btn = e.currentTarget;
    const circle = document.createElement("span");
    const diameter = Math.max(btn.clientWidth, btn.clientHeight);
    const radius = diameter / 2;

    circle.style.width = circle.style.height = `${diameter}px`;
    circle.classList.add("ripple");

    const rect = btn.getBoundingClientRect();
    circle.style.left = `${e.clientX - rect.left - radius}px`;
    circle.style.top = `${e.clientY - rect.top - radius}px`;

    const ripple = btn.getElementsByClassName("ripple")[0];
    if (ripple) ripple.remove();

    btn.appendChild(circle);
}

document.addEventListener('click', function(e){
    const btn = e.target.closest('.mat-btn, .mat-icon-btn');
    if (!btn) return;
    if (e.button !== 0) return;
    createRipple({ currentTarget: btn, clientX: e.clientX, clientY: e.clientY });
});

function showAnalysisGroup(group) {
    document.querySelectorAll('.analysis-list').forEach(list => {
        list.classList.remove('active');
    });
    document.querySelector('.' + group + '-group').classList.add('active');

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`.tab-btn[onclick*="${group}"]`).classList.add('active');
}


document.addEventListener('DOMContentLoaded', () => {
    showAnalysisGroup('basic');
});