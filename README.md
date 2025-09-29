# Snake AI – Universidad Nacional de Colombia

Proyecto de la materia **Introducción a los sistemas inteligentes**  
Semestre 2025-2  
Profesor: **Jonatan Gómez Perdomo**

---

## Integrantes

- **Camilo Londoño Moreno**
- **Guillermo Alberto Correa C.**
- **Juan Mateo Rozo**

---

## Descripción

Este proyecto implementa el juego clásico **Snake** de dos maneras:

1. **Simulación local en Pygame**: se desarrolló una versión del juego en Python para pruebas controladas.
2. **Reconocimiento del Snake de Google**: se diseñó un sistema de visión por computador que captura y procesa la pantalla del navegador, permitiendo al agente interactuar con el juego real.

El agente utiliza algoritmos de búsqueda y heurísticas para decidir sus movimientos, con el objetivo de maximizar la supervivencia y la recolección de comida.

---

## Módulos principales

1. **Snake (`snake.py`)**  
   Implementa la lógica del juego y el modelo de la serpiente, incluyendo posición, dirección, cuerpo y reglas de movimiento:contentReference[oaicite:0]{index=0}.

2. **GreedySolver (`greedy.py`)**  
   Estrategia de búsqueda **voraz**.

   - Busca el camino más corto hacia la comida si es seguro.
   - Si no, intenta llegar a la cola.
   - En última instancia entra en modo de supervivencia.  
     Explicación inspirada en: 👉 [chuyangliu/snake](https://github.com/chuyangliu/snake/tree/main) :contentReference[oaicite:1]{index=1}.

3. **Actuator (`actuator.py`)**  
   Actuador externo que envía las acciones del agente al juego real mediante **PyAutoGUI**, simulando teclas de flechas:contentReference[oaicite:2]{index=2}.

4. **Scanner (`scanner.py`)**  
   Módulo de visión que usa **OpenCV** para:
   - Detectar la cuadrícula del juego en la pantalla.
   - Reconocer elementos como la serpiente, la comida y los muros.
   - Proveer el estado en forma de grilla al agente.

---

## Librerías principales

- **Pygame** → Simulación del juego local.
- **OpenCV** → Procesamiento de imágenes y lectura de la pantalla del navegador.
- **PyAutoGUI** → Interacción con el juego real enviando teclas al navegador.
- **NumPy** → Manejo de estructuras y operaciones matriciales.

---

## Ejecución

1. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Para probar el juego localmente con pygame
   ```bash
   python game.py
   ```
3. Para probar el juego en linea hay que tener abierto el juego en el navegador y correr
   ```bash
   python main.py
   ```

## Estructura del proyecto

```bash
.
├── assets/           # Archivos de imagen del juego de Snake en Google
├── base/             # Clases base y logica del juego
├── solver/           # Algoritmos de búsqueda (GreedySolver, PathSolver, etc.)
├── game.py           # Simulador del juego en Pygame
├── actuator.py       # Actuador externo con PyAutoGUI
├── scanner.py        # Módulo de visión con OpenCV
└── README.md
```
