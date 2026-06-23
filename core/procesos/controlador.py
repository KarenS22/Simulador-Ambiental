import time
import multiprocessing
from core.base_controlador import BaseControlador
from core.procesos.analizador import AnalizadorProcesos

class ControladorProcesos(BaseControlador):
    def __init__(self, num_estaciones=8, carga_computacional=10000):
        self.analizador = AnalizadorProcesos(carga_computacional)
        super().__init__(num_estaciones, carga_computacional)


    def ejecutar(self, ciclos=10):
        self._preparar_ejecucion("Procesos", ciclos)
        start_time = time.perf_counter()
        
        queue = multiprocessing.Queue()
        barrier = multiprocessing.Barrier(len(self.estaciones))
        
        processes = []
        for est in self.estaciones:
            p = multiprocessing.Process(
                target=self._proceso_estacion, 
                args=(est, ciclos, queue, barrier, self.analizador.carga_computacional)
            )
            processes.append(p)
            p.start()

        total_esperado = len(self.estaciones) * ciclos * 3
        count = 0
        while count < total_esperado:
            try:
                msg_type, data = queue.get(timeout=0.5)
                if msg_type == "medicion":
                    # El subproceso ya hizo la carga pesada, así que registramos sin analizar de nuevo
                    self.registrar_medicion(data, realizar_analisis=False)
                    count += 1
                    if count % (len(self.estaciones) * 3) == 0:
                        ciclo = count // (len(self.estaciones) * 3)
                        if self.callback_ui: self.callback_ui("ciclo", (ciclo, ciclos))
                elif msg_type == "estado":
                    self._notificar_estado(data[0], data[1])
            except:
                continue
        
        try:
            barrier.abort()
        except:
            pass
        for p in processes: p.join()
        self._finalizar_ejecucion(start_time)
        return self.metricas

    @staticmethod
    def _proceso_estacion(estacion, ciclos, queue, barrier, carga_computacional):
        # Instanciar un analizador en el subproceso para correr el análisis pesado en paralelo
        analizador = AnalizadorProcesos(carga_computacional)
        
        for _ in range(ciclos):
            queue.put(("estado", (estacion.id_estacion, "activa")))
            mediciones = estacion.generar_mediciones_ciclo()
            
            # Realizar el análisis pesado en paralelo en este núcleo de CPU
            analizador.realizar_analisis_pesado(mediciones)
            
            for medicion in mediciones:
                queue.put(("medicion", medicion))
            queue.put(("estado", (estacion.id_estacion, "esperando")))
            try:
                barrier.wait()
            except:
                break
        queue.put(("estado", (estacion.id_estacion, "finalizada")))
