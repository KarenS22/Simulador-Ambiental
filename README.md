# Práctica 4: Monitoreo Ambiental Concurrente en Python

Este proyecto simula un sistema urbano de monitoreo ambiental para la ciudad de Cuenca, aplicando conceptos de paralelismo y concurrencia.

## Requisitos
- Python 3.13.5 o 3.14.5 (Revisar versiones sin GIL)
- Bibliotecas estándar (`tkinter`, `threading`, `multiprocessing`, `time`, `math`)

## Estructura del Proyecto
- `core/`: Lógica central (Controlador, Analizador).
- `models/`: Clases de datos (Estación, Medición, Alerta).
- `gui/`: Interfaz gráfica con Tkinter.
- `main.py`: Punto de entrada del sistema.

## Ejecución
``` bash
python3 main.py
```

## Análisis del GIL
Durante las pruebas se observó que la versión con hilos no presenta una mejora significativa respecto a la secuencial para tareas intensivas en CPU. Esto se debe al **Global Interpreter Lock (GIL)** de Python, que impide que múltiples hilos de ejecución de Python utilicen simultáneamente más de un núcleo del procesador. La versión con procesos sortea esta limitación al crear espacios de memoria independientes.
# Simulador-Ambiental

