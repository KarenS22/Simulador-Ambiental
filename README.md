# Práctica 4: Monitoreo Ambiental Concurrente en Python

Este proyecto simula un sistema urbano de monitoreo ambiental para la ciudad de Cuenca, aplicando conceptos de paralelismo y concurrencia.

Simula estaciones distribuidas que miden Temperatura, Humedad y CO2, utilizando tres paradigmas de programación en Python: **Secuencial**, **Multiprocessing** (Paralelismo) y **Threading** (Concurrencia).

## Instalación y Requisitos

### Requisitos 
- Python 3.13.5 o 3.14.5 (Revisar versiones sin GIL)
- Bibliotecas estándar (`tkinter`, `threading`, `multiprocessing`, `time`, `math`)

### Instrucciones de Instalación
1. Clonar el repositorio:
   ```bash
   git clone https://github.com/KarenS22/Simulador-Ambiental.git
   cd Simulador-Ambiental
   ```
2. Verificar la versión de Python:
   ```bash
   python3 --version
   ```

## Ejecución

```bash
python3 main.py
```

## Interfaz de Usuario
A continuación se muestra la interfaz gráfica del sistema:

| Dashboard Principal | Estadísticas y Alertas |
| :---: | :---: | 
| ![Dashboard](screenshots/gui_main.png) | ![Alertas](screenshots/gui_alerts.png) |

## Comparativa de Rendimiento

Los resultados obtenidos muestran la escalabilidad del sistema en tres niveles de prueba (16 núcleos, Carga 10,000):

| Simulación | Secuencial | Hilos (Threading) | Procesos (Multproc.) |
| :--- | :---: | :---: | :---: |
| **4 Est. / 10 Ciclos** | 4.05s | **0.19s** | 0.28s |
| **8 Est. / 20 Ciclos** | 17.23s | **0.78s** | 0.86s |
| **12 Est. / 30 Ciclos** | 39.61s | **1.75s** | 1.97s |


> **Análisis del GIL:** Al utilizar Python (Free-threaded), la versión de hilos no se ve penalizada por el GIL. En las pruebas, Hilos fue más rápido que Procesos, ya que aprovechan el paralelismo real de CPU sin el costo adicional de crear procesos o pasar datos por colas (IPC).

## Arquitectura del Proyecto

```mermaid
graph TD
    UI[Interfaz Tkinter] -->|Configuración| Ctrl[Controlador Monitoreo]
    Ctrl -->|Strategy| M[Modos: Secuencial / Hilos / Procesos]
    M -->|Instancia| Est[Estaciones Ambientales]
    Est -->|Genera| Med[Mediciones]
    Med -->|Análisis Pesado| Ana[Analizador de Datos]
    Ana -->|Si supera umbral| Ale[Alertas Ambientales]
    Ana -->|Retorna| Stats[Estadísticas KPIs]
    Stats --> UI
```

## Estructura del Proyecto
- `core/`: Lógica central (Controlador, Analizador).
- `models/`: Clases de datos (Estación, Medición, Alerta).
- `gui/`: Interfaz gráfica con Tkinter.
- `main.py`: Punto de entrada del sistema.



## Comando de ejecución

mpiexec -f mpi_hosts -n 11 python /home/flamenco/home/main.py