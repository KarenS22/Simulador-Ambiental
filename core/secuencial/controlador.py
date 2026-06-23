import time
from core.base_controlador import BaseControlador
from core.secuencial.analizador import AnalizadorSecuencial

class ControladorSecuencial(BaseControlador):
    def __init__(self, num_estaciones=8, carga_computacional=10000):
        self.analizador = AnalizadorSecuencial(carga_computacional)
        super().__init__(num_estaciones, carga_computacional)

    def ejecutar(self, ciclos=10):
        self._preparar_ejecucion("Secuencial", ciclos)
        start_time = time.perf_counter()

        for ciclo in range(ciclos):
            self.metricas["ciclo_actual"] = ciclo + 1
            self.metricas["progreso"] = ((ciclo + 1) / ciclos) * 100
            
            for estacion in self.estaciones:
                self._notificar_estado(estacion.id_estacion, "activa")
                mediciones = estacion.generar_mediciones_ciclo()
                for medicion in mediciones:
                    self.registrar_medicion(medicion, realizar_analisis=True)
                self._notificar_estado(estacion.id_estacion, "esperando")
            
            if self.callback_ui:
                self.callback_ui("ciclo", (ciclo + 1, ciclos))

        self._finalizar_ejecucion(start_time)
        return self.metricas
