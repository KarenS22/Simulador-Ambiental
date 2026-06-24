import random
from models.medicion import Medicion

class EstacionAmbiental:
    def __init__(self, id_estacion, nombre, zona):
        self.id_estacion = id_estacion
        self.nombre = nombre
        self.zona = zona
        self.variables_fijas = ["Temperatura", "Humedad", "CO2"]

    def generar_mediciones_ciclo(self):
        """Genera una medición por cada variable"""
        mediciones = []
        for var in self.variables_fijas:
            mediciones.append(self.generar_medicion(var))
        return mediciones

    def generar_medicion(self, variable=None):
        if variable is None:
            variable = random.choice(self.variables_fijas)
        
        # Simulación de valores realistas 
        valores = {
            "Temperatura": random.uniform(8, 26), 
            "Humedad": random.uniform(30, 95),
            "CO2": random.uniform(300, 1500),
            "Ruido": random.uniform(30, 90),
            "PM2.5": random.uniform(0, 100),
            "PM10": random.uniform(0, 200)
        }
        
        return Medicion(
            id_estacion=self.id_estacion,
            zona=self.zona,
            variable=variable,
            valor=valores.get(variable, 0)
        )

    def __str__(self):
        return f"Estación {self.nombre} en zona {self.zona}"