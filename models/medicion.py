from datetime import datetime

class Medicion:
    def __init__(self, id_estacion, zona, variable, valor, timestamp=None):
        self.id_estacion = id_estacion
        self.zona = zona
        self.variable = variable
        self.valor = valor
        self.timestamp = timestamp or datetime.now()

    def __str__(self):
        return f"[{self.timestamp.strftime('%H:%M:%S')}] {self.zona} - {self.variable}: {self.valor:.2f}"