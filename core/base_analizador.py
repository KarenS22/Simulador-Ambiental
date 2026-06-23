import math

class BaseAnalizador:
    def __init__(self, carga_computacional=10000):
        self.umbrales = {
            "Temperatura": 30.0,
            "Humedad": 90.0,
            # "Ruido": 70.0,
            "CO2": 1000.0,
            # "PM2.5": 50.0,
            # "PM10": 100.0
        }
        self.carga_computacional = carga_computacional

    def realizar_analisis_pesado(self, mediciones):
        """
        Simula una carga computacional realizando cálculos repetitivos
        sobre las mediciones para que el paralelismo tenga sentido.
        """
        # Cálculos intensivos de CPU ficticios
        for _ in range(self.carga_computacional):
            _ = [math.sqrt(m.valor) * math.log(m.valor + 1) for m in mediciones if m.valor > 0]
            
    def procesar_mediciones(self, mediciones):
        if not mediciones:
            return {}

        self.realizar_analisis_pesado(mediciones)
        return self.procesar_mediciones_rapido(mediciones)

    def procesar_mediciones_rapido(self, mediciones):
        if not mediciones:
            return {}

        stats = {}
        for m in mediciones:
            if m.variable not in stats:
                stats[m.variable] = {"sum": 0, "count": 0, "min": float('inf'), "max": float('-inf')}
            
            s = stats[m.variable]
            s["sum"] += m.valor
            s["count"] += 1
            s["min"] = min(s["min"], m.valor)
            s["max"] = max(s["max"], m.valor)

        resultados = {}
        alertas_por_zona = {}
        for var, data in stats.items():
            resultados[var] = {
                "promedio": data["sum"] / data["count"],
                "min": data["min"],
                "max": data["max"],
                "total": data["count"]
            }
        
        # Identificar zona con más alertas (riesgo)
        for m in mediciones:
            if self.verificar_alerta(m):
                alertas_por_zona[m.zona] = alertas_por_zona.get(m.zona, 0) + 1
        
        zona_riesgo = max(alertas_por_zona, key=alertas_por_zona.get) if alertas_por_zona else "Ninguna"
        
        return {
            "variables": resultados,
            "zona_riesgo": zona_riesgo
        }

    def verificar_alerta(self, medicion):
        umbral = self.umbrales.get(medicion.variable)
        if umbral and medicion.valor > umbral:
            from models.alerta import AlertaAmbiental
            return AlertaAmbiental(medicion.zona, medicion.variable, medicion.valor, umbral)
        return None
