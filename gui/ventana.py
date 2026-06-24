import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import platform
import sys
import multiprocessing
import time

class VentanaMonitoreo:
    def __init__(self, root, controlador_factory):
        self.root = root
        self.controlador_factory = controlador_factory
        self.controlador = self.controlador_factory(4, "procesos", 10000)
        
        self.root.title("EcoMonitor v3.5 - Cuenca")
        self.root.geometry("1400x900")
        self.root.configure(bg="#0a0a0a") # Negro profundo
        
        self.running = False
        self.start_simulation_time = 0
        
        self._definir_estilos()
        self._crear_interfaz()
        self._configurar_controlador()
        self._update_clock()

    def _definir_estilos(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        self.colors = {
            "bg": "#0a0a0a",
            "card": "#161616",
            "accent": "#00d2ff",
            "text": "#e0e0e0",
            "text_dim": "#707070",
            "success": "#2ecc71",
            "warning": "#f1c40f",
            "danger": "#e74c3c",
            "process": "#3498db"
        }
        
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["text"])
        style.configure("Header.TLabel", font=("Segoe UI", 20, "bold"), foreground=self.colors["accent"])
        style.configure("TCombobox", fieldbackground=self.colors["card"], background=self.colors["card"])

    def _crear_interfaz(self):
        # 1. BARRA DE CONFIGURACIÓN (TOP)
        top_bar = tk.Frame(self.root, bg=self.colors["card"], height=70)
        top_bar.pack(fill="x", side="top")
        
        tk.Label(top_bar, text=" CONFIGURACIÓN ", bg=self.colors["card"], fg=self.colors["accent"], font=("Segoe UI", 10, "bold")).pack(side="left", padx=20)
        
        # Selectores Obligatorios
        ttk.Label(top_bar, text="Estaciones:", background=self.colors["card"]).pack(side="left", padx=5)
        self.sel_estaciones = ttk.Combobox(top_bar, values=["4", "8", "12"], width=7, state="readonly")
        self.sel_estaciones.current(0)
        self.sel_estaciones.pack(side="left", padx=5)
        
        ttk.Label(top_bar, text="Ciclos:", background=self.colors["card"]).pack(side="left", padx=5)
        self.sel_ciclos = ttk.Combobox(top_bar, values=["10", "20", "30"], width=7, state="readonly")
        self.sel_ciclos.current(0)
        self.sel_ciclos.pack(side="left", padx=5)
        
        ttk.Label(top_bar, text="Modo:", background=self.colors["card"]).pack(side="left", padx=5)
        self.sel_modo = ttk.Combobox(top_bar, values=["Secuencial", "Hilos", "Procesos"], width=15, state="readonly")
        self.sel_modo.current(2)
        self.sel_modo.pack(side="left", padx=5)
        
        ttk.Label(top_bar, text="Carga Comp.:", background=self.colors["card"]).pack(side="left", padx=5)
        self.slider_carga = tk.Scale(
            top_bar,
            from_=0,
            to=50000,
            orient="horizontal",
            bg=self.colors["card"],
            fg=self.colors["text"],
            troughcolor="#2b2b2b",
            activebackground=self.colors["accent"],
            highlightthickness=0,
            bd=0,
            length=150,
            font=("Segoe UI", 9),
            command=self._actualizar_carga_dinamica
        )
        self.slider_carga.set(10000)
        self.slider_carga.pack(side="left", padx=10)
        
        self.btn_run = tk.Button(top_bar, text="INICIAR SIMULACIÓN", bg=self.colors["success"], fg="#000", font=("Segoe UI", 11, "bold"), command=self._iniciar_simulacion, relief="flat", padx=25)
        self.btn_run.pack(side="left", padx=40)
        
        # 2. BARRA DE ESTADO
        status_bar = tk.Frame(self.root, bg="#000", height=30)
        status_bar.pack(fill="x")
        self.lbl_timer = tk.Label(status_bar, text="TIEMPO: 00:00:00", bg="#000", fg=self.colors["text_dim"], font=("Consolas", 10))
        self.lbl_timer.pack(side="left", padx=20)
        
        env = f"{platform.system()} | Python {sys.version.split()[0]} | {multiprocessing.cpu_count()} Cores | GIL: {sys._is_gil_enabled()}"
        tk.Label(status_bar, text=env, bg="#000", fg=self.colors["text_dim"], font=("Segoe UI", 9)).pack(side="right", padx=20)

        # 3. CUERPO (3 PANELES)
        body = tk.Frame(self.root, bg=self.colors["bg"])
        body.pack(fill="both", expand=True, padx=15, pady=15)
        
        # PANEL IZQ: Estaciones (Grid)
        left = tk.Frame(body, bg=self.colors["bg"])
        left.pack(side="left", fill="both", expand=True)
        tk.Label(left, text="CANALES DE MONITOREO", bg=self.colors["bg"], fg=self.colors["text_dim"], font=("Segoe UI", 10, "bold")).pack(anchor="w")
        
        self.canvas_est = tk.Canvas(left, bg=self.colors["bg"], highlightthickness=0)
        self.grid_est = tk.Frame(self.canvas_est, bg=self.colors["bg"])
        self.canvas_est.create_window((0,0), window=self.grid_est, anchor="nw")
        self.canvas_est.pack(fill="both", expand=True, pady=10)
        
        # PANEL CENTRAL: KPIs + Métricas Finales
        center = tk.Frame(body, bg=self.colors["bg"], width=400)
        center.pack(side="left", fill="both", padx=20)
        
        tk.Label(center, text="MÉTRICAS DE RENDIMIENTO", bg=self.colors["bg"], fg=self.colors["text_dim"], font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.kpi_frame = tk.Frame(center, bg=self.colors["bg"])
        self.kpi_frame.pack(fill="both", pady=10)
        self.kpi_widgets = {}

        # Tarjeta de Métricas Finales
        self.metrics_card = tk.Frame(center, bg="#1a1a1a", padx=20, pady=20, relief="ridge", borderwidth=1)
        self.metrics_card.pack(fill="x", pady=20)
        tk.Label(self.metrics_card, text="MÉTRICAS FINALES", bg="#1a1a1a", fg=self.colors["accent"], font=("Segoe UI", 11, "bold")).pack()
        self.lbl_final_stats = tk.Label(self.metrics_card, text="Tiempo Total: -\nVelocidad: - med/seg\nAlertas: -\nModo: -", bg="#1a1a1a",fg="#b3b3b3" ,justify="left")
        self.lbl_final_stats.pack(pady=10)

        # PANEL DER: Alertas
        right = tk.Frame(body, bg=self.colors["bg"], width=300)
        right.pack(side="left", fill="both")
        tk.Label(right, text="HISTORIAL DE ALERTAS", bg=self.colors["bg"], fg=self.colors["danger"], font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.txt_alertas = scrolledtext.ScrolledText(right, bg=self.colors["card"], fg=self.colors["danger"], font=("Consolas", 10), borderwidth=0)
        self.txt_alertas.pack(fill="both", expand=True, pady=10)

        # 4. FOOTER
        footer = tk.Frame(self.root, bg=self.colors["card"], height=80)
        footer.pack(fill="x", side="bottom")
        
        self.lbl_pct = tk.Label(footer, text="Ciclo 0/0 (0%)", bg=self.colors["card"], fg="#b3b3b3", font=("Segoe UI", 10, "bold"))
        self.lbl_pct.pack(pady=5)
        self.progress = ttk.Progressbar(footer, orient="horizontal", mode="determinate", length=800)
        self.progress.pack(padx=100, fill="x")
        


        self._dibujar_estaciones()
        self._dibujar_kpis()

    def _dibujar_estaciones(self):
        for w in self.grid_est.winfo_children(): w.destroy()
        self.station_widgets = {}
        cols = 3 if len(self.controlador.estaciones) > 6 else 2
        for i, est in enumerate(self.controlador.estaciones):
            f = tk.Frame(self.grid_est, bg=self.colors["card"], padx=15, pady=10, borderwidth=1, relief="flat")
            f.grid(row=i//cols, column=i%cols, padx=5, pady=5, sticky="nsew")
            
            badge = tk.Label(f, text="ESPERANDO", bg="#333", fg="#fff", font=("Segoe UI", 7, "bold"), padx=6)
            badge.pack(anchor="e")
            
            tk.Label(f, text=est.nombre, bg=self.colors["card"], fg=self.colors["accent"], font=("Segoe UI", 11, "bold")).pack(anchor="w")
            tk.Label(f, text=est.zona, bg=self.colors["card"], fg=self.colors["text_dim"], font=("Segoe UI", 8)).pack(anchor="w")
            
            vars_frame = tk.Frame(f, bg=self.colors["card"])
            vars_frame.pack(fill="x", pady=5)
            
            labels = {}
            for v in ["Temperatura", "Humedad", "CO2"]:
                l = tk.Label(vars_frame, text=f"{v}: --", bg=self.colors["card"], fg=self.colors["text"], font=("Segoe UI", 9))
                l.pack(anchor="w")
                labels[v] = l
            
            self.station_widgets[est.id_estacion] = {"badge": badge, "vars": labels}

    def _dibujar_kpis(self):
        for w in self.kpi_frame.winfo_children(): w.destroy()
        for i, v in enumerate(["Temperatura", "Humedad", "CO2"]):
            card = tk.Frame(self.kpi_frame, bg=self.colors["card"], padx=15, pady=10)
            card.pack(fill="x", pady=5)
            
            tk.Label(card, text=v.upper(), bg=self.colors["card"], fg=self.colors["text_dim"], font=("Segoe UI", 8, "bold")).pack(side="left")
            avg = tk.Label(card, text="0.0", bg=self.colors["card"], fg=self.colors["accent"], font=("Segoe UI", 16, "bold"))
            avg.pack(side="right")
            
            mm = tk.Label(card, text="Min: 0.0 | Max: 0.0", bg=self.colors["card"], fg=self.colors["text_dim"], font=("Segoe UI", 8))
            mm.pack(side="bottom", anchor="e")
            self.kpi_widgets[v] = {"avg": avg, "minmax": mm}

    def _configurar_controlador(self):
        self.controlador.set_callback_ui(self._callback_ui)

    def _callback_ui(self, tipo, data):
        self.root.after(0, self._process_update, tipo, data)

    def _process_update(self, tipo, data):
        if tipo == "medicion":
            w = self.station_widgets.get(data.id_estacion)
            if w and data.variable in w["vars"]:
                lbl = w["vars"][data.variable]
                lbl.config(text=f"{data.variable}: {data.valor:.1f}", fg=self.colors["text"])
                # Verificar si es alerta para poner en ROJO
                if self.controlador.analizador.verificar_alerta(data):
                    lbl.config(fg=self.colors["danger"])

        elif tipo == "estado":
            id_est, est = data
            if id_est in self.station_widgets:
                colors = {"activa": self.colors["success"], "esperando": self.colors["warning"], "finalizada": "#444", "procesando": self.colors["process"]}
                self.station_widgets[id_est]["badge"].config(text=est.upper(), bg=colors.get(est, "#333"))

        elif tipo == "alerta":
            self.txt_alertas.insert(tk.END, f"⚠ {time.strftime('%H:%M:%S')} - {data}\n")
            self.txt_alertas.see(tk.END)

        elif tipo == "stats":
            variables = data.get("variables", {})
            for v, res in variables.items():
                if v in self.kpi_widgets:
                    self.kpi_widgets[v]["avg"].config(text=f"{res['promedio']:.1f}")
                    self.kpi_widgets[v]["minmax"].config(text=f"Min: {res['min']:.1f} | Max: {res['max']:.1f}")

        elif tipo == "ciclo":
            curr, total = data
            pct = (curr / total) * 100
            self.lbl_pct.config(text=f"Ciclo {curr}/{total} ({pct:.1f}%)")
            self.progress["value"] = pct

    def _update_clock(self):
        if self.running:
            elapsed = int(time.perf_counter() - self.start_simulation_time)
            m, s = divmod(elapsed, 60)
            h, m = divmod(m, 60)
            self.lbl_timer.config(text=f"TIEMPO: {h:02}:{m:02}:{s:02}")
        self.root.after(1000, self._update_clock)

    def _iniciar_simulacion(self):
        if self.running: return
        n_est = int(self.sel_estaciones.get())
        ciclos = int(self.sel_ciclos.get())
        modo = self.sel_modo.get().lower()
        carga = int(self.slider_carga.get())
        
        self.controlador = self.controlador_factory(n_est, modo, carga)
        self._configurar_controlador()
        self._dibujar_estaciones()
        self.txt_alertas.delete(1.0, tk.END)
        self.lbl_final_stats.config(text="Procesando simulación...")
        
        self.running = True
        self.start_simulation_time = time.perf_counter()
        self.btn_run.config(state="disabled")
        
        def run():
            res = self.controlador.ejecutar(ciclos)
            self.root.after(0, self._mostrar_final, res)
            
        threading.Thread(target=run, daemon=True).start()

    def _mostrar_final(self, res):
        self.running = False
        self.btn_run.config(state="normal")
        med_sec = res['mediciones_procesadas'] / res['tiempo_ejecucion'] if res['tiempo_ejecucion'] > 0 else 0
        txt = (f"Tiempo Total: {res['tiempo_ejecucion']:.3f}s\n"
               f"Tiempo Promedio/Ciclo: {res.get('tiempo_promedio_ciclo', 0):.3f}s\n"
               f"Velocidad: {med_sec:.1f} med/seg\n"
               f"Alertas: {res['alertas_generadas']}\n"
               f"Zona de Riesgo: {res.get('zona_riesgo', 'N/A')}\n")
        self.lbl_final_stats.config(text=txt)
        print(f"\n--- RESULTADOS FINALES ---")
        print(f"Estaciones: {res['numero_estaciones']} Ciclos: {res['ciclos']} Modo: {res['modo']}")
        print(txt)



    def _actualizar_carga_dinamica(self, valor):
        if hasattr(self, 'controlador') and self.controlador:
            self.controlador.set_carga_computacional(int(valor))
