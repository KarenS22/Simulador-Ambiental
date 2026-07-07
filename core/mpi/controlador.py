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
            
            # Notificar información del proceso para el modo local fallback
            import os
            import socket
            pid = os.getpid()
            hostname = socket.gethostname()
            display_host = hostname
            try:
                controlador_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(os.path.dirname(controlador_dir))
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
            except Exception:
                pass
                
            for est in self.estaciones:
                if self.callback_ui:
                    self.callback_ui("info_proceso", (est.id_estacion, pid, 0, display_host))

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

        # Si size > 1, distribuir estaciones entre TODOS los procesos (incluyendo Rank 0)
        worker_assignments = {r: [] for r in range(1, size)}
        local_assignments = []
        for i, est in enumerate(self.estaciones):
            r = i % size
            if r == 0:
                local_assignments.append(est)
            else:
                worker_assignments[r].append(est)

        # Notificar información del proceso local (Rank 0) para las estaciones asignadas a él
        import os
        import socket
        pid = os.getpid()
        hostname = socket.gethostname()
        display_host = hostname
        try:
            controlador_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(controlador_dir))
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
        except Exception:
            pass

        for est in local_assignments:
            if self.callback_ui:
                self.callback_ui("info_proceso", (est.id_estacion, pid, 0, display_host))
            
        # Enviar parámetros de simulación y estaciones asignadas a cada worker
        for r in range(1, size):
            payload = (ciclos, self.analizador.carga_computacional, worker_assignments[r])
            comm.send(("start", payload), dest=r)

        # Recibir mediciones y estados en bucle por cada ciclo
        num_estaciones = len(self.estaciones)
        mediciones_esperadas = (num_estaciones - len(local_assignments)) * 3

        for ciclo in range(ciclos):
            # Procesar estaciones asignadas localmente a Rank 0
            for est in local_assignments:
                self._notificar_estado(est.id_estacion, "activa")
                mediciones = est.generar_mediciones_ciclo()
                self.analizador.realizar_analisis_pesado(mediciones)
                for medicion in mediciones:
                    self.registrar_medicion(medicion, realizar_analisis=False)
                self._notificar_estado(est.id_estacion, "esperando")

            # Recibir mediciones de los workers
            mediciones_recibidas = 0
            while mediciones_recibidas < mediciones_esperadas:
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
                    elif msg_type == "info_proceso":
                        id_est, pid, rank, host = data
                        if self.callback_ui:
                            self.callback_ui("info_proceso", (id_est, pid, rank, host))
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
