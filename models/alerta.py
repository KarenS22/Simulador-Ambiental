class AlertaAmbiental:
    def __init__(self, zona, variable, valor, umbral):
        self.zona = zona
        self.variable = variable
        self.valor = valor
        self.umbral = umbral

    def __str__(self):
        return (
            f"!!! ALERTA !!! {self.zona} | "
            f"{self.variable}: {self.valor:.2f} "
            f"(Límite: {self.umbral})"
        )