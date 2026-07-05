import os
import sys

# Asegurar que el directorio raíz esté en sys.path para importaciones correctas en entornos MPI distribuidos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.ventana import VentanaMonitoreo
import tkinter as tk

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
    elif modo == "mpi":
        from core.mpi.controlador import ControladorMPI
        return ControladorMPI(n, carga_computacional)
    else:
        raise ValueError(f"Modo desconocido: {modo}")

def main():
    try:
        from mpi4py import MPI
        comm = MPI.COMM_WORLD
        rank = comm.Get_rank()
        size = comm.Get_size()
    except ImportError:
        rank = 0
        size = 1

    # Redirigir a los procesos trabajadores de MPI a su bucle de ejecución
    if size > 1 and rank > 0:
        from core.mpi.worker import run_mpi_worker
        run_mpi_worker()
        sys.exit(0)

    # Registrar el apagado limpio de los workers al cerrar el programa principal
    if size > 1 and rank == 0:
        import atexit
        def limpiar_workers_mpi():
            from mpi4py import MPI
            comm = MPI.COMM_WORLD
            size = comm.Get_size()
            for r in range(1, size):
                try:
                    comm.send(("exit", None), dest=r)
                except Exception:
                    pass
        atexit.register(limpiar_workers_mpi)

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
    
    for modo in ["secuencial", "hilos", "procesos", "mpi"]:
        print(f"\nEjecutando versión {modo.upper()} (10 ciclos)...")
        controlador = controlador_factory(4, modo, 10000)
        res = controlador.ejecutar(10)
        
        print(f"Terminado en {res['tiempo_ejecucion']:.4f}s. Mediciones: {res['mediciones_procesadas']}")

if __name__ == "__main__":
    main()

