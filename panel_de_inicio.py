import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import subprocess, sys, os

class PanelInicio:
    def __init__(self, root):
        self.root = root
        self.root.title("Panel de Inicio - Taller Mecánico")
        self.root.geometry("800x500")
        self.root.resizable(False, False)

        self._configurar_estilos()
        self._construir_layout()

    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Menu.TButton",
                        background="#f59e0b",
                        foreground="#111827",
                        font=("Segoe UI Semibold", 12),
                        padding=6,
                        relief="flat",
                        borderwidth=0)
        style.map("Menu.TButton", background=[("active", "#fbbf24")])

    def _construir_layout(self):
        fondo = Image.open(r"C:\RICHARD\RB\2025\Taller_mecánica\panel_de_inicio_fondo.png")
        fondo = fondo.resize((800, 500), Image.Resampling.LANCZOS)
        self.bg_image = ImageTk.PhotoImage(fondo)

        canvas = tk.Canvas(self.root, width=800, height=500)
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, image=self.bg_image, anchor="nw")

        botones = [
            ("📋 Órdenes de Trabajo", "python_ordenes_taller.py", 275, 122, 250, 48),
            ("📊 Ventas", "ventas_taller.py", 275, 182, 250, 48),
            ("👥 Clientes", "clientes_taller.py", 275, 242, 250, 48),
            ("🛠 Proveedores", "proveedores_taller.py", 275, 302, 250, 48),
            ("📦 Inventario", "modulo_inventario.py", 275, 362, 250, 48)
        ]

        for texto, archivo, x, y, w, h in botones:
            btn = ttk.Button(canvas, text=texto, style="Menu.TButton",
                             command=lambda a=archivo: self.abrir_modulo(a))
            canvas.create_window(x, y, window=btn, width=w, height=h)

    def abrir_modulo(self, archivo):
        carpeta = os.path.dirname(os.path.abspath(__file__))
        ruta = os.path.join(carpeta, archivo)
        subprocess.Popen([sys.executable, ruta])

if __name__ == "__main__":
    root = tk.Tk()
    app = PanelInicio(root)
    root.mainloop()



