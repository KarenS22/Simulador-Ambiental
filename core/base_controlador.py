import time
from models.estacion import EstacionAmbiental

class BaseControlador:
    def __init__(self, num_estaciones=8, carga_computacional=10000):
        # Se asume que self.analizador ya ha sido instanciado por la subclase.
        self.mediciones_acumuladas = []
        self.alertas = []
        

        
        self.metricas = {
            "numero_estaciones": 0,
            "ciclos": 0,
            "tiempo_ejecucion": 0,
            "mediciones_procesadas": 0,
            "alertas_generadas": 0,
            "modo": "Ninguno",
            "ciclo_actual": 0,
            "progreso": 0
        }
        self.estados_estaciones = {} 
        self.callback_ui = None
        
        self.inicializar_estaciones(num_estaciones)

    def inicializar_estaciones(self, num):
        zonas_cuenca = [
            "El Sagrario", "Turi", "Huayna Cápac", "San Sebastián",
            "Challuabamba", "Baños", "Ricaurte", "Monay",
            "Yanuncay", "El Vecino", "San Blas", "Sucre"
        ]
        
        self.estaciones = []
        for i in range(num):
            zona = zonas_cuenca[i % len(zonas_cuenca)]
            self.estaciones.append(EstacionAmbiental(i+1, f"Estación {i+1}", zona))
            self.estados_estaciones[i+1] = "esperando"

    def set_callback_ui(self, callback):
        self.callback_ui = callback

    def set_carga_computacional(self, valor):
        self.analizador.carga_computacional = valor

    def _notificar_estado(self, id_estacion, estado):
        self.estados_estaciones[id_estacion] = estado
        if self.callback_ui:
            self.callback_ui("estado", (id_estacion, estado))

    def registrar_medicion(self, medicion, realizar_analisis=True):
        
        self.mediciones_acumuladas.append(medicion)
        alerta = self.analizador.verificar_alerta(medicion)
        if alerta:
            self.alertas.append(alerta)
            self.metricas["alertas_generadas"] += 1
        
        # Recalcular estadísticas rápidas para KPIs
        # Si realizar_analisis=False (como en Procesos), se usa procesar_mediciones_rapido
        if realizar_analisis:
            stats = self.analizador.procesar_mediciones(self.mediciones_acumuladas[-20:])
        else:
            stats = self.analizador.procesar_mediciones_rapido(self.mediciones_acumuladas[-20:])
            
        if self.callback_ui:
            self.callback_ui("medicion", medicion)
            if alerta:
                self.callback_ui("alerta", alerta)
            if stats:
                self.callback_ui("stats", stats)

    def _preparar_ejecucion(self, modo, ciclos):
        self.metricas["modo"] = modo
        self.metricas["total_ciclos"] = ciclos
        self.mediciones_acumuladas = []
        self.alertas = []
        self.metricas["alertas_generadas"] = 0
        for id_est in self.estados_estaciones:
            self._notificar_estado(id_est, "esperando")

    def _finalizar_ejecucion(self, start_time):
        self.metricas["numero_estaciones"] = len(self.estaciones)
        self.metricas["ciclos"] = self.metricas["total_ciclos"]
        total_time = time.perf_counter() - start_time
        self.metricas["tiempo_ejecucion"] = total_time
        self.metricas["mediciones_procesadas"] = len(self.mediciones_acumuladas)
        
        # Calcular zona de riesgo final
        res_final = self.analizador.procesar_mediciones_rapido(self.mediciones_acumuladas)
        self.metricas["zona_riesgo"] = res_final.get("zona_riesgo", "N/A")
        ciclos = self.metricas.get("total_ciclos", 10)
        self.metricas["tiempo_promedio_ciclo"] = total_time / ciclos if ciclos > 0 else 0

        for id_est in self.estados_estaciones:
            self._notificar_estado(id_est, "finalizada")
