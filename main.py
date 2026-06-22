from core.controlador import ControladorMonitoreo
from gui.ventana import VentanaMonitoreo
import tkinter as tk
import sys

def main():
    if "--cli" in sys.argv:
        run_cli()
    else:
        run_gui()

def run_gui():
    root = tk.Tk()
    
    # Factory para reiniciar el controlador con diferente número de estaciones
    def controlador_factory(n):
        return ControladorMonitoreo(n)
        
    app = VentanaMonitoreo(root, controlador_factory)
    root.mainloop()

def run_cli():
    import platform
    import multiprocessing
    print("--- Sistema de Monitoreo Ambiental Urbano - Cuenca ---")
    print(f"OS: {platform.system()} | Python: {sys.version.split()[0]}")
    print(f"Núcleos detectados: {multiprocessing.cpu_count()}")
    
    # Configuración por defecto para CLI
    controlador = ControladorMonitoreo(4)
    
    for modo in ["secuencial", "hilos", "procesos"]:
        print(f"\nEjecutando versión {modo.upper()} (10 ciclos)...")
        if modo == "secuencial": res = controlador.ejecutar_secuencial(10)
        elif modo == "hilos": res = controlador.ejecutar_hilos(10)
        else: res = controlador.ejecutar_procesos(10)
        
        print(f"Terminado en {res['tiempo_ejecucion']:.4f}s. Mediciones: {res['mediciones_procesadas']}")

if __name__ == "__main__":
    main()
