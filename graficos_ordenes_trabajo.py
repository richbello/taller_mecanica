import tkinter as tk
from tkinter import ttk
import json, os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Archivo de órdenes
ORDENES_FILE = "ordenes_taller.json"

def cargar_ordenes():
    if not os.path.exists(ORDENES_FILE):
        return []
    try:
        with open(ORDENES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

class ReporteOrdenesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Reporte de Órdenes de Trabajo - Taller Mecánico")
        self.root.geometry("900x600")
        self.root.configure(bg="#0f172a")

        self._configurar_estilos()
        self._construir_layout()

    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")
        self.color_bg = "#0f172a"
        self.color_panel = "#1e293b"
        self.color_acento = "#f59e0b"
        self.color_ok = "#22c55e"
        self.color_texto = "#e2e8f0"
        style.configure("TLabel", foreground=self.color_texto, background=self.color_panel)
        style.configure("Accent.TButton", background=self.color_acento, foreground="#111827")
        style.configure("Ok.TButton", background=self.color_ok, foreground="#0b1220")

    def _construir_layout(self):
        frame = tk.Frame(self.root, bg=self.color_panel)
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        ttk.Button(frame, text="📊 Órdenes por estado", style="Accent.TButton", command=self.grafico_estados).pack(pady=10)
        ttk.Button(frame, text="🛠️ Órdenes por servicio", style="Accent.TButton", command=self.grafico_servicios).pack(pady=10)

        self.canvas_frame = tk.Frame(frame, bg=self.color_panel)
        self.canvas_frame.pack(fill="both", expand=True)

    def grafico_estados(self):
        ordenes = cargar_ordenes()
        if not ordenes: return

        estados = {"Pendiente":0, "En proceso":0, "Terminado":0}
        for o in ordenes:
            estados[o["estado"]] = estados.get(o["estado"],0) + 1

        fig, ax = plt.subplots(figsize=(6,4))
        ax.pie(estados.values(), labels=estados.keys(), autopct="%1.1f%%",
               colors=["#f59e0b","#3b82f6","#22c55e"])
        ax.set_title("Órdenes por estado")

        self._mostrar_grafico(fig)

    def grafico_servicios(self):
        ordenes = cargar_ordenes()
        if not ordenes: return

        servicios = {}
        for o in ordenes:
            s = o["servicio"]
            servicios[s] = servicios.get(s,0) + 1

        fig, ax = plt.subplots(figsize=(6,4))
        ax.bar(servicios.keys(), servicios.values(), color="#f59e0b")
        ax.set_title("Órdenes por servicio")
        ax.set_ylabel("Cantidad")
        plt.xticks(rotation=45)

        self._mostrar_grafico(fig)

    def _mostrar_grafico(self, fig):
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = ReporteOrdenesApp(root)
    root.mainloop()
