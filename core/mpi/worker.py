import sys
from mpi4py import MPI

def run_mpi_worker():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    
    while True:
        try:
            # Esperar instrucción del Rank 0
            msg = comm.recv(source=0)
            if msg is None:
                break
            
            cmd_type, payload = msg
            if cmd_type == "exit":
                break
            elif cmd_type == "start":
                ciclos, carga_computacional, estaciones = payload
                
                # Obtener PID y hostname resuelto según mpi_hosts
                import os
                import socket
                pid = os.getpid()
                hostname = socket.gethostname()
                display_host = hostname
                
                try:
                    worker_dir = os.path.dirname(os.path.abspath(__file__))
                    project_root = os.path.dirname(os.path.dirname(worker_dir))
                    mpi_hosts_path = os.path.join(project_root, "mpi_hosts")
                    if os.path.exists(mpi_hosts_path):
                        with open(mpi_hosts_path, "r") as f:
                            for line in f:
                                line = line.strip()
                                if not line or line.startswith("#"):
                                    continue
                                parts = line.split(":")
                                host_in_file = parts[0].strip()
                                if host_in_file.lower() in hostname.lower() or hostname.lower() in host_in_file.lower():
                                    display_host = host_in_file
                                    break
                except Exception as e:
                    print(f"[Worker Rank {rank}] Error al resolver host: {e}", flush=True)

                # Notificar a la UI sobre la información de este proceso para cada estación
                for est in estaciones:
                    comm.send(("info_proceso", (est.id_estacion, pid, rank, display_host)), dest=0)
                
                # Instanciar el analizador local para realizar el análisis en paralelo
                from core.mpi.analizador import AnalizadorMPI
                analizador = AnalizadorMPI(carga_computacional)
                
                for ciclo in range(ciclos):
                    # Procesar las estaciones asignadas
                    for est in estaciones:
                        comm.send(("estado", (est.id_estacion, "activa")), dest=0)
                        mediciones = est.generar_mediciones_ciclo()
                        analizador.realizar_analisis_pesado(mediciones)
                        for medicion in mediciones:
                            comm.send(("medicion", medicion), dest=0)
                        comm.send(("estado", (est.id_estacion, "esperando")), dest=0)
                    
                    # Sincronización mediante barrera al final de cada ciclo
                    comm.Barrier()
                    
        except Exception as e:
            print(f"[Worker Rank {rank}] Error en worker: {e}", flush=True)
            break
