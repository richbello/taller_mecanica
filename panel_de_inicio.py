import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import subprocess, sys, os

class PanelInicio:
    def __init__(self, root):
        self.root = root
        self.root.title("Panel de Inicio - Taller Mecánico")
        # ventana redimensionable
        self.root.geometry("800x500")
        self.root.minsize(700, 480)
        self.root.resizable(True, True)

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
        # intentar cargar imagen original (sin escalar aún)
        self.bg_orig = None
        try:
            path = r"C:\RICHARD\RB\2025\Taller_mecánica\panel_de_inicio_fondo.png"
            if os.path.exists(path):
                fondo = Image.open(path)
                self.bg_orig = fondo.convert("RGBA")
        except Exception:
            self.bg_orig = None

        # canvas que ocupa todo y responde al redimensionamiento
        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        if self.bg_orig is None:
            self.canvas.configure(bg="#0f172a")
            self.bg_id = None
        else:
            # crear imagen inicial escalada al tamaño de la ventana actual
            w = self.root.winfo_width() or 800
            h = self.root.winfo_height() or 500
            img = self.bg_orig.resize((max(1, w), max(1, h)), Image.Resampling.LANCZOS)
            self.bg_image = ImageTk.PhotoImage(img)
            self.bg_id = self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")

        # definimos los botones (texto y archivo)
        self.botones_def = [
            ("📋 Órdenes de Trabajo", "python_ordenes_taller.py"),
            ("📊 Ventas", "ventas_taller.py"),
            ("👥 Clientes", "clientes_taller.py"),
            ("🛠 Proveedores", "proveedores_taller.py"),
            ("📦 Inventario", "modulo_inventario.py"),
            ("🔒 Seguridad", "seguridad_taller.py"),
            ("💳 Pasarela de Pagos", "pasarela_pagos.py"),
        ]

        # crear widgets de botones y ventanas en canvas; guardamos referencias para reposicionar
        self.button_windows = []
        self.button_widgets = []
        for texto, archivo in self.botones_def:
            btn = ttk.Button(self.canvas, text=texto, style="Menu.TButton",
                             command=lambda a=archivo: self.abrir_modulo(a))
            # inicialmente colocamos en (0,0); se reposicionarán en el handler configure
            win_id = self.canvas.create_window(0, 0, window=btn, width=260, height=40)
            self.button_windows.append(win_id)
            self.button_widgets.append(btn)

        # bind para redibujar fondo y reposicionar botones al cambiar tamaño
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # posicionamiento inicial
        self.root.update_idletasks()
        self._position_buttons(self.canvas.winfo_width(), self.canvas.winfo_height())

    def abrir_modulo(self, archivo):
        carpeta = os.path.dirname(os.path.abspath(__file__))
        ruta = os.path.join(carpeta, archivo)
        if not os.path.exists(ruta):
            # Intentar también en la ruta base del proyecto
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

    def _on_canvas_configure(self, event):
        w = event.width
        h = event.height
        # actualizar fondo escalado si existe
        if self.bg_orig is not None and self.bg_id is not None:
            try:
                resized = self.bg_orig.resize((max(1, w), max(1, h)), Image.Resampling.LANCZOS)
                self.bg_image = ImageTk.PhotoImage(resized)
                self.canvas.itemconfig(self.bg_id, image=self.bg_image)
            except Exception:
                pass

        # reposicionar botones
        self._position_buttons(w, h)

    def _position_buttons(self, w, h):
        # colocamos los botones centrados horizontalmente y con separación vertical proporcional
        center_x = w // 2
        # top margin y espacio entre botones adaptativos
        top_margin = int(max(60, h * 0.12))
        spacing = int(max(44, h * 0.08))
        # si hay muchos botones, reducimos spacing
        n = len(self.button_windows)
        available_h = h - top_margin - 60
        if n * spacing > available_h:
            spacing = max(36, available_h // max(1, n))

        for idx, win_id in enumerate(self.button_windows):
            y = top_margin + idx * spacing
            try:
                self.canvas.coords(win_id, center_x, y)
            except Exception:
                pass


if __name__ == "__main__":
    root = tk.Tk()
    app = PanelInicio(root)
    root.mainloop()


