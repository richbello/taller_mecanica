import tkinter as tk
from tkinter import ttk, messagebox
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
        try:
            fondo = Image.open(r"C:\RICHARD\RB\2025\Taller_mecánica\panel_de_inicio_fondo.png")
            fondo = fondo.resize((800, 500), Image.Resampling.LANCZOS)
            self.bg_image = ImageTk.PhotoImage(fondo)
        except Exception:
            # Si falla la imagen, usar un fondo simple
            self.bg_image = None

        canvas = tk.Canvas(self.root, width=800, height=500)
        canvas.pack(fill="both", expand=True)
        if self.bg_image:
            canvas.create_image(0, 0, image=self.bg_image, anchor="nw")
        else:
            canvas.configure(bg="#0f172a")

        # Lista de botones/ módulos (texto, archivo a ejecutar, x, y, w, h)
        botones = [
            ("📋 Órdenes de Trabajo", "python_ordenes_taller.py", 275, 112, 250, 40),
            ("📊 Ventas", "ventas_taller.py", 275, 162, 250, 40),
            ("👥 Clientes", "clientes_taller.py", 275, 212, 250, 40),
            ("🛠 Proveedores", "proveedores_taller.py", 275, 262, 250, 40),
            ("📦 Inventario", "modulo_inventario.py", 275, 312, 250, 40),
            ("🔒 Seguridad", "seguridad_taller.py", 275, 362, 250, 40),  # Nuevo módulo de seguridad
        ]

        for texto, archivo, x, y, w, h in botones:
            btn = ttk.Button(canvas, text=texto, style="Menu.TButton",
                             command=lambda a=archivo: self.abrir_modulo(a))
            canvas.create_window(x, y, window=btn, width=w, height=h)

    def abrir_modulo(self, archivo):
        carpeta = os.path.dirname(os.path.abspath(__file__))
        ruta = os.path.join(carpeta, archivo)
        if not os.path.exists(ruta):
            # Intentar también en la ruta base del proyecto (por si los módulos están en la carpeta especificada)
            posible = os.path.join(r"C:\RICHARD\RB\2025\Taller_mecánica", archivo)
            if os.path.exists(posible):
                ruta = posible
            else:
                messagebox.showerror("Archivo no encontrado", f"No se encontró el módulo:\n{archivo}\n\nBuscado en:\n{ruta}")
                return
        try:
            subprocess.Popen([sys.executable, ruta])
        except Exception as e:
            messagebox.showerror("Error al abrir módulo", f"No se pudo ejecutar {archivo}.\n\nDetalle:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PanelInicio(root)
    root.mainloop()



