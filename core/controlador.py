import random
import time
import threading
import multiprocessing
from models.estacion import EstacionAmbiental
from core.analizador import AnalizadorDatos


class ControladorMonitoreo:
    def __init__(self, num_estaciones=4):
        self.analizador = AnalizadorDatos()
        self.mediciones_acumuladas = []
        self.alertas = []
        self.lock = threading.Lock()
        self.barrier = None
        
        # Banderas de control
        self.event_pausa = threading.Event()
        self.event_pausa.set() 
        self.stop_requested = False
        
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

    def _notificar_estado(self, id_estacion, estado):
        self.estados_estaciones[id_estacion] = estado
        if self.callback_ui:
            self.callback_ui("estado", (id_estacion, estado))

    def registrar_medicion(self, medicion):
        # Manejo de pausa
        self.event_pausa.wait()
        
        with self.lock:
            self.mediciones_acumuladas.append(medicion)
            alerta = self.analizador.verificar_alerta(medicion)
            if alerta:
                self.alertas.append(alerta)
                self.metricas["alertas_generadas"] += 1
            
            # Recalcular estadísticas rápidas para KPIs
            stats = self.analizador.procesar_mediciones(self.mediciones_acumuladas[-20:])
            
        if self.callback_ui:
            self.callback_ui("medicion", medicion)
            if alerta:
                self.callback_ui("alerta", alerta)
            if stats:
                self.callback_ui("stats", stats)

    def detener(self):
        self.stop_requested = True
        self.event_pausa.set() # Salir de pausa si estaba bloqueado

    def pausar(self):
        if self.event_pausa.is_set():
            self.event_pausa.clear()
        else:
            self.event_pausa.set()

    def ejecutar_secuencial(self, ciclos=10):
        self._preparar_ejecucion("Secuencial", ciclos)
        start_time = time.perf_counter()

        for ciclo in range(ciclos):
            if self.stop_requested: break
            self.metricas["ciclo_actual"] = ciclo + 1
            self.metricas["progreso"] = ((ciclo + 1) / ciclos) * 100
            
            for estacion in self.estaciones:
                if self.stop_requested: break
                self.event_pausa.wait()
                
                self._notificar_estado(estacion.id_estacion, "activa")
                # Generar las 3 variables obligatorias
                mediciones = estacion.generar_mediciones_ciclo()
                for medicion in mediciones:
                    time.sleep(0.05) # Pequeño delay para visualización
                    self.registrar_medicion(medicion)
                self._notificar_estado(estacion.id_estacion, "esperando")
            
            if self.callback_ui:
                self.callback_ui("ciclo", (ciclo + 1, ciclos))

        self._finalizar_ejecucion(start_time)
        return self.metricas

    def _hilo_estacion(self, estacion, ciclos):
        for ciclo in range(ciclos):
            if self.stop_requested: break
            self.event_pausa.wait()
            
            self._notificar_estado(estacion.id_estacion, "activa")
            mediciones = estacion.generar_mediciones_ciclo()
            for medicion in mediciones:
                time.sleep(random.uniform(0.05, 0.1))
                self.registrar_medicion(medicion)
            
            self._notificar_estado(estacion.id_estacion, "esperando")
            self.barrier.wait()
            
            if estacion.id_estacion == 1 and self.callback_ui:
                self.callback_ui("ciclo", (ciclo + 1, ciclos))
        
        self._notificar_estado(estacion.id_estacion, "finalizada")

    def ejecutar_hilos(self, ciclos=10):
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

    def ejecutar_procesos(self, ciclos=10):
        self._preparar_ejecucion("Procesos", ciclos)
        start_time = time.perf_counter()
        
        queue = multiprocessing.Queue()
        barrier = multiprocessing.Barrier(len(self.estaciones))
        event_stop = multiprocessing.Event() # Para detener procesos
        
        processes = []
        for est in self.estaciones:
            p = multiprocessing.Process(target=self._proceso_estacion, args=(est, ciclos, queue, barrier, event_stop))
            processes.append(p)
            p.start()

        total_esperado = len(self.estaciones) * ciclos * 3
        count = 0
        while count < total_esperado and not self.stop_requested:
            self.event_pausa.wait()
            try:
                msg_type, data = queue.get(timeout=0.5)
                if msg_type == "medicion":
                    self.registrar_medicion(data)
                    count += 1
                    if count % (len(self.estaciones) * 3) == 0:
                        ciclo = count // (len(self.estaciones) * 3)
                        if self.callback_ui: self.callback_ui("ciclo", (ciclo, ciclos))
                elif msg_type == "estado":
                    self._notificar_estado(data[0], data[1])
            except:
                if self.stop_requested: break
                continue
        
        event_stop.set()
        for p in processes: p.join()
        self._finalizar_ejecucion(start_time)
        return self.metricas

    @staticmethod
    def _proceso_estacion(estacion, ciclos, queue, barrier, event_stop):
        for _ in range(ciclos):
            if event_stop.is_set(): break
            queue.put(("estado", (estacion.id_estacion, "activa")))
            mediciones = estacion.generar_mediciones_ciclo()
            for medicion in mediciones:
                time.sleep(random.uniform(0.05, 0.1))
                queue.put(("medicion", medicion))
            queue.put(("estado", (estacion.id_estacion, "esperando")))
            barrier.wait()
        queue.put(("estado", (estacion.id_estacion, "finalizada")))

    def _preparar_ejecucion(self, modo, ciclos):
        self.metricas["modo"] = modo
        self.metricas["total_ciclos"] = ciclos
        self.mediciones_acumuladas = []
        self.alertas = []
        self.metricas["alertas_generadas"] = 0
        self.stop_requested = False
        self.event_pausa.set()
        for id_est in self.estados_estaciones:
            self._notificar_estado(id_est, "esperando")

    def _finalizar_ejecucion(self, start_time):
        self.metricas["numero_estaciones"] = len(self.estaciones)
        self.metricas["ciclos"] = self.metricas["total_ciclos"]
        total_time = time.perf_counter() - start_time
        self.metricas["tiempo_ejecucion"] = total_time
        self.metricas["mediciones_procesadas"] = len(self.mediciones_acumuladas)
        
        # Calcular zona de riesgo final y tiempo promedio por ciclo
        res_final = self.analizador.procesar_mediciones(self.mediciones_acumuladas)
        self.metricas["zona_riesgo"] = res_final.get("zona_riesgo", "N/A")
        ciclos = self.metricas.get("total_ciclos", 10)
        self.metricas["tiempo_promedio_ciclo"] = total_time / ciclos if ciclos > 0 else 0

        for id_est in self.estados_estaciones:
            self._notificar_estado(id_est, "finalizada")
