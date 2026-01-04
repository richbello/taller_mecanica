import tkinter as tk
from tkinter import ttk
import json, os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Archivo de ventas
VENTAS_FILE = "ventas.json"

def cargar_ventas():
    if not os.path.exists(VENTAS_FILE):
        return []
    try:
        with open(VENTAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

class ReporteVentasApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Reporte de Ventas - Taller Mecánico")
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

        ttk.Button(frame, text="📊 Ventas por mes", style="Accent.TButton", command=self.grafico_ventas).pack(pady=10)

        self.canvas_frame = tk.Frame(frame, bg=self.color_panel)
        self.canvas_frame.pack(fill="both", expand=True)

    def grafico_ventas(self):
        ventas = cargar_ventas()
        if not ventas:
            return

        # Agrupar ventas por mes
        meses = {}
        for v in ventas:
            fecha = v["fecha"].split()[0]  # YYYY-MM-DD
            mes = fecha[:7]                # YYYY-MM
            meses[mes] = meses.get(mes, 0) + v["total"]

        fig, ax = plt.subplots(figsize=(6,4))
        ax.bar(meses.keys(), meses.values(), color="#22c55e")
        ax.set_title("Ventas por mes")
        ax.set_ylabel("Total ($)")
        ax.set_xlabel("Mes")
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
    app = ReporteVentasApp(root)
    root.mainloop()
