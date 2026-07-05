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
