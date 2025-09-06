let dias = 0;
const fogata = document.getElementById('fogata');
const diasCounter = document.getElementById('contador-dias');
const faseCounter = document.getElementById('contador-fase');

document.getElementById('subirRacha').addEventListener('click', () => {
  dias++;
  diasCounter.textContent = dias;
  
  // Calcular fase (cada 10 días se avanza una fase)
  const fase = Math.min(Math.floor(dias / 10), 19);
  faseCounter.textContent = fase;
  
  // Actualizar etapa de la fogata
  fogata.className = `fogata etapa-${fase}`;
  
  // Efecto especial cada 10 días (nueva fase)
  if (dias % 10 === 0) {
    fogata.classList.add('saludar');
    setTimeout(() => fogata.classList.remove('saludar'), 2000);
    crearChispas(15 + fase);
  }
});

function crearChispas(cantidad) {
  const chispasContainer = fogata.querySelector('.chispas');
  chispasContainer.innerHTML = '';
  
  const fase = Math.min(Math.floor(dias / 10), 19);
  
  for (let i = 0; i < cantidad; i++) {
    const spark = document.createElement('div');
    spark.className = 'spark';
    
    // Posición y animación aleatoria
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
      animation: spark-fly ${duration}s ease-in ${delay}s forwards;
    `;
    
    // Animación de la chispa
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