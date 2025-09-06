const checkboxes = document.querySelectorAll('.tarea-checkbox');

checkboxes.forEach(checkbox => {
    checkbox.addEventListener('change', function() {
        const tarea_completada = Array.from(checkboxes)
            .filter(cbx => cbx.checked)
            .map(cbx => cbx.getAttribute('data-idx'));

        fetch('/actualizar_tarea', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ tarea_completada: tarea_completada })
        })
        .then(response => response.json())
        .then(data => {
            document.querySelector('#dias-racha').innerText = data.racha;
            actualizarFogata(data.racha);
        });
    });
});

function actualizarFogata(racha) {
    const fogata = document.getElementById('fogata');
    const fase = Math.min(Math.floor(racha / 10), 19);
    fogata.className = `fogata etapa-${fase}`;
    
    if (racha % 10 === 0 && racha > 0) {
        fogata.classList.add('saludar');
        setTimeout(() => fogata.classList.remove('saludar'), 2000);
        crearChispas(15 + fase);
    }
}

function crearChispas(cantidad) {
    const fogata = document.getElementById('fogata');
    const chispasContainer = fogata.querySelector('.chispas');
    if (!chispasContainer) return;
    
    chispasContainer.innerHTML = '';
    
    const racha = parseInt(document.querySelector('#dias-racha').innerText);
    const fase = Math.min(Math.floor(racha / 10), 19);
    
    for (let i = 0; i < cantidad; i++) {
        const spark = document.createElement('div');
        spark.className = 'spark';
        
        const posX = (Math.random() - 0.5) * 100;
        const duration = 0.8 + Math.random() * 1.2;
        const delay = Math.random() * 0.5;
        const color = fase >= 15 ? 
            (Math.random() > 0.5 ? '#4fc3f7' : '#81d4fa') : 
            (fase >= 10 ? 
                (Math.random() > 0.5 ? '#ff8a65' : '#ff5722') : 
                (Math.random() > 0.5 ? '#ffecb3' : '#ffcc80'));
        
        spark.style.cssText = `
            position: absolute;
            width: ${2 + Math.random() * 3}px;
            height: ${2 + Math.random() * 3}px;
            background: ${color};
            border-radius: 50%;
            bottom: 40%;
            left: 50%;
            opacity: 0;
            box-shadow: 0 0 5px ${fase >= 15 ? '#00bcd4' : (fase >= 10 ? '#ff3d00' : '#ff9800')};
        `;
        
        const keyframes = `
            @keyframes spark-fly-${i} {
                0% { 
                    transform: translate(0, 0); 
                    opacity: 1;
                }
                100% { 
                    transform: translate(${posX}px, -${200 + Math.random() * 100}px); 
                    opacity: 0;
                }
            }
        `;
        
        const style = document.createElement('style');
        style.textContent = keyframes;
        document.head.appendChild(style);
        
        spark.style.animation = `spark-fly-${i} ${duration}s ease-in ${delay}s forwards`;
        chispasContainer.appendChild(spark);
    }
}

// Inicializar fogata con la racha actual
const rachaInicial = parseInt(document.querySelector('#dias-racha').innerText);
actualizarFogata(rachaInicial);