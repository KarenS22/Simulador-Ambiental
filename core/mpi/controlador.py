import time
from mpi4py import MPI
from core.base_controlador import BaseControlador
from core.mpi.analizador import AnalizadorMPI

class ControladorMPI(BaseControlador):
    def __init__(self, num_estaciones=8, carga_computacional=10000):
        self.analizador = AnalizadorMPI(carga_computacional)
        super().__init__(num_estaciones, carga_computacional)

    def ejecutar(self, ciclos=10):
        self._preparar_ejecucion("MPI", ciclos)
        start_time = time.perf_counter()
        
        comm = MPI.COMM_WORLD
        rank = comm.Get_rank()
        size = comm.Get_size()
        
        # Fallback si size == 1 (ejecución secuencial en el rank 0)
        if size <= 1:
            print("[ControladorMPI] ADVERTENCIA: Corriendo en modo fallback local (un solo proceso).", flush=True)
            for ciclo in range(ciclos):
                self.metricas["ciclo_actual"] = ciclo + 1
                self.metricas["progreso"] = ((ciclo + 1) / ciclos) * 100
                
                for estacion in self.estaciones:
                    self._notificar_estado(estacion.id_estacion, "activa")
                    mediciones = estacion.generar_mediciones_ciclo()
                    self.analizador.realizar_analisis_pesado(mediciones)
                    for medicion in mediciones:
                        self.registrar_medicion(medicion, realizar_analisis=False)
                    self._notificar_estado(estacion.id_estacion, "esperando")
                
                if self.callback_ui:
                    self.callback_ui("ciclo", (ciclo + 1, ciclos))
            
            self._finalizar_ejecucion(start_time)
            return self.metricas

        # Si size > 1, distribuir estaciones entre workers (rank 1 a size - 1)
        num_workers = size - 1
        worker_assignments = {r: [] for r in range(1, size)}
        for i, est in enumerate(self.estaciones):
            w_rank = 1 + (i % num_workers)
            worker_assignments[w_rank].append(est)
            
        # Enviar parámetros de simulación y estaciones asignadas a cada worker
        for r in range(1, size):
            payload = (ciclos, self.analizador.carga_computacional, worker_assignments[r])
            comm.send(("start", payload), dest=r)

        # Recibir mediciones y estados en bucle por cada ciclo
        num_estaciones = len(self.estaciones)
        mediciones_por_ciclo = num_estaciones * 3 # 3 variables por estación

        for ciclo in range(ciclos):
            mediciones_recibidas = 0
            while mediciones_recibidas < mediciones_por_ciclo:
                try:
                    msg = comm.recv(source=MPI.ANY_SOURCE)
                    if msg is None:
                        continue
                    msg_type, data = msg
                    if msg_type == "medicion":
                        self.registrar_medicion(data, realizar_analisis=False)
                        mediciones_recibidas += 1
                    elif msg_type == "estado":
                        id_est, status = data
                        self._notificar_estado(id_est, status)
                except Exception as e:
                    print(f"[ControladorMPI] Error en recepción: {e}", flush=True)
                    break

            if self.callback_ui:
                self.callback_ui("ciclo", (ciclo + 1, ciclos))
            
            # Sincronización mediante barrera al final del ciclo
            try:
                comm.Barrier()
            except Exception as e:
                print(f"[ControladorMPI] Error en barrera: {e}", flush=True)
                break

        self._finalizar_ejecucion(start_time)
        return self.metricas
