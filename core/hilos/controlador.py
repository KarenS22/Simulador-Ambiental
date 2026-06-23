import time
import threading
from core.base_controlador import BaseControlador
from core.hilos.analizador import AnalizadorHilos

class ControladorHilos(BaseControlador):
    def __init__(self, num_estaciones=8, carga_computacional=10000):
        self.analizador = AnalizadorHilos(carga_computacional)
        super().__init__(num_estaciones, carga_computacional)
        self.barrier = None

    def ejecutar(self, ciclos=10):
        self._preparar_ejecucion("Hilos", ciclos)
        start_time = time.perf_counter()
        
        self.barrier = threading.Barrier(len(self.estaciones))
        threads = []
        for est in self.estaciones:
            t = threading.Thread(target=self._hilo_estacion, args=(est, ciclos))
            threads.append(t)
            t.start()
        
        for t in threads: t.join()
        self._finalizar_ejecucion(start_time)
        return self.metricas

    def _hilo_estacion(self, estacion, ciclos):
        for ciclo in range(ciclos):
            self._notificar_estado(estacion.id_estacion, "activa")
            mediciones = estacion.generar_mediciones_ciclo()
            for medicion in mediciones:
                self.registrar_medicion(medicion, realizar_analisis=True)
            
            self._notificar_estado(estacion.id_estacion, "esperando")
            try:
                self.barrier.wait()
            except (threading.BrokenBarrierError, AssertionError):
                break
            
            if estacion.id_estacion == 1 and self.callback_ui:
                self.callback_ui("ciclo", (ciclo + 1, ciclos))
        
        self._notificar_estado(estacion.id_estacion, "finalizada")
