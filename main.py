from gui.ventana import VentanaMonitoreo
import tkinter as tk
import sys

def controlador_factory(n, modo, carga_computacional=10000):
    modo = modo.lower()
    if modo == "secuencial":
        from core.secuencial.controlador import ControladorSecuencial
        return ControladorSecuencial(n, carga_computacional)
    elif modo == "hilos":
        from core.hilos.controlador import ControladorHilos
        return ControladorHilos(n, carga_computacional)
    elif modo == "procesos":
        from core.procesos.controlador import ControladorProcesos
        return ControladorProcesos(n, carga_computacional)
    else:
        raise ValueError(f"Modo desconocido: {modo}")

def main():
    if "--cli" in sys.argv:
        run_cli()
    else:
        run_gui()

def run_gui():
    root = tk.Tk()
    print(VentanaMonitoreo)    
    app = VentanaMonitoreo(root, controlador_factory)
    root.mainloop()

def run_cli():
    import platform
    import multiprocessing
    print("--- Sistema de Monitoreo Ambiental Urbano - Cuenca ---")
    print(f"OS: {platform.system()} | Python: {sys.version.split()[0]}")
    print(f"Núcleos detectados: {multiprocessing.cpu_count()}")
    
    for modo in ["secuencial", "hilos", "procesos"]:
        print(f"\nEjecutando versión {modo.upper()} (10 ciclos)...")
        controlador = controlador_factory(4, modo, 10000)
        res = controlador.ejecutar(10)
        
        print(f"Terminado en {res['tiempo_ejecucion']:.4f}s. Mediciones: {res['mediciones_procesadas']}")

if __name__ == "__main__":
    main()
