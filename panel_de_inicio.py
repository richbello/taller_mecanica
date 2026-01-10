# panel_inicio.py — Panel moderno con fondo elegante, grid 3x4 y botones con íconos
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw
import subprocess, sys, os

from security_core import module_opened, start_user_session, end_user_session, button_clicked

BASE_DIR = r"C:\RICHARD\RB\2025\Taller_mecánica"
BG_IMAGE_PATH = os.path.join(BASE_DIR, "panel_de_inicio_fondo.png")  # si existe, se usa
ICONS_DIR = os.path.join(BASE_DIR, "icons")  # carpeta sugerida para íconos PNG

# Definición de módulos (texto, archivo, icono sugerido)
MODULOS = [
    ("📋 Órdenes de Trabajo", "python_ordenes_taller.py", "orders.png"),
    ("📊 Ventas", "ventas_taller.py", "sales.png"),
    ("👥 Clientes", "clientes_taller.py", "clients.png"),
    ("🛠 Proveedores", "proveedores_taller.py", "providers.png"),
    ("📦 Inventario", "modulo_inventario.py", "inventory.png"),
    ("🔒 Seguridad", "seguridad_taller.py", "security.png"),
    ("💳 Pasarela de Pagos", "pasarela_pagos.py", "payments.png"),
    ("🧾 Nómina", "nomina_taller.py", "payroll.png"),
    ("🛒 Compras", "compras_taller.py", "purchases.png"),
    ("💼 Cartera", "cartera_taller.py", "portfolio.png"),
    ("📈 Reportes", "reportes_taller.py", "reports.png"),
    ("⚙️ Configuración", "config_taller.py", "settings.png"),
    # Opcionales extra si los tienes:
    ("🧮 Facturación DIAN", "facturacion_dian.py", "dian.png"),
    ("🏦 PSE / Débito", "pagos_pse.py", "pse.png"),
    ("📈 Reportes", "reportes_taller.py", "reports.png"),
    ("⚙️ Configuración", "config_taller.py", "settings.png"),

]

class PanelInicio:
    def __init__(self, root):
        self.root = root
        self.root.title("Panel de Inicio - Taller Mecánico")
        self.root.geometry("1100x720")
        self.root.minsize(960, 600)
        self.root.resizable(True, True)

        self._configurar_estilos()
        self._construir_layout()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Botón principal (naranja)
        style.configure("Menu.TButton",
                        background="#f59e0b",
                        foreground="#111827",
                        font=("Segoe UI Semibold", 13),
                        padding=10,
                        relief="flat",
                        borderwidth=0)
        style.map("Menu.TButton",
                  background=[("active", "#fbbf24")],
                  foreground=[("active", "#111827")])

        # Card contenedor (oscuro)
        style.configure("Card.TFrame", background="#1e293b")
        style.configure("Title.TLabel", background="#0f172a", foreground="#e2e8f0", font=("Segoe UI", 18, "bold"))
        style.configure("Sub.TLabel", background="#0f172a", foreground="#94a3b8", font=("Segoe UI", 11))

    def _construir_layout(self):
        # Canvas principal
        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Fondo: imagen si existe, si no gradiente con overlay
        self._build_background()

        # Título superior
        title_frame = tk.Frame(self.canvas, bg="#0f172a")
        self.title_window = self.canvas.create_window(0, 0, window=title_frame, anchor="n")
        ttk.Label(title_frame, text="Panel de Inicio", style="Title.TLabel").pack(anchor="w", padx=24, pady=(16, 4))
        ttk.Label(title_frame, text="Taller Mecánico — Operación integral", style="Sub.TLabel").pack(anchor="w", padx=24, pady=(0, 12))

        # Grid central de módulos (3 columnas x 4 filas)
        self.grid_frame = tk.Frame(self.canvas, bg="#0f172a")
        self.grid_window = self.canvas.create_window(0, 0, window=self.grid_frame, anchor="center")

        # Crear cards con botón + icono
        self.cards = []
        self.icons_cache = {}
        cols = 3
        for idx, (texto, archivo, icon_name) in enumerate(MODULOS[:12]):  # muestra 12 principales
            card = ttk.Frame(self.grid_frame, style="Card.TFrame")
            card.grid(row=idx // cols, column=idx % cols, padx=18, pady=18, sticky="nsew")
            self._build_card(card, texto, archivo, icon_name)
            self.cards.append(card)

        # Ajuste de columnas para expandir
        for c in range(cols):
            self.grid_frame.grid_columnconfigure(c, weight=1)

        # Bind para redimensionar
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _build_background(self):
        w = self.root.winfo_width() or 1100
        h = self.root.winfo_height() or 720

        # Intentar cargar imagen
        bg_img = None
        if os.path.exists(BG_IMAGE_PATH):
            try:
                bg_img = Image.open(BG_IMAGE_PATH).convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
            except Exception:
                bg_img = None

        if bg_img is None:
            # Crear gradiente oscuro
            bg_img = Image.new("RGBA", (w, h), "#0f172a")
            draw = ImageDraw.Draw(bg_img)
            for i in range(h):
                # gradiente vertical sutil
                ratio = i / max(1, h)
                color = (
                    int(15 + (30 - 15) * ratio),   # R
                    int(23 + (41 - 23) * ratio),   # G
                    int(42 + (59 - 42) * ratio),   # B
                    255
                )
                draw.line([(0, i), (w, i)], fill=color)
        # Overlay suave para resaltar contenido
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 80))
        bg_img = Image.alpha_composite(bg_img, overlay)

        self.bg_image = ImageTk.PhotoImage(bg_img)
        self.bg_id = self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")

    def _load_icon(self, icon_name, size=(28, 28)):
        # Carga ícono desde carpeta; si no existe, devuelve None
        path = os.path.join(ICONS_DIR, icon_name)
        if path in self.icons_cache:
            return self.icons_cache[path]
        if os.path.exists(path):
            try:
                img = Image.open(path).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
                tkimg = ImageTk.PhotoImage(img)
                self.icons_cache[path] = tkimg
                return tkimg
            except Exception:
                return None
        return None

    def _build_card(self, parent, texto, archivo, icon_name):
        # Contenido del card
        inner = tk.Frame(parent, bg="#1e293b")
        inner.pack(fill="both", expand=True, padx=12, pady=12)

        # Ícono + botón compuesto
        icon = self._load_icon(icon_name)
        if icon:
            btn = ttk.Button(inner, text=texto, style="Menu.TButton",
                             command=lambda a=archivo, t=texto: self.abrir_modulo(a, t))
            btn.configure(compound="left")
            # Label con imagen a la izquierda
            img_lbl = tk.Label(inner, image=icon, bg="#1e293b")
            img_lbl.image = icon
            img_lbl.pack(side="left", padx=(4, 10))
            btn.pack(side="left", fill="x", expand=True, padx=(0, 4), pady=2)
        else:
            # Fallback sin imagen (emoji ya en texto)
            btn = ttk.Button(inner, text=texto, style="Menu.TButton",
                             command=lambda a=archivo, t=texto: self.abrir_modulo(a, t))
            btn.pack(fill="x", expand=True, padx=4, pady=2)

        # Hover visual del card (ligero)
        def on_enter(e):
            parent.configure(style="Card.TFrame")
            inner.configure(bg="#223047")
        def on_leave(e):
            parent.configure(style="Card.TFrame")
            inner.configure(bg="#1e293b")
        inner.bind("<Enter>", on_enter)
        inner.bind("<Leave>", on_leave)

    def abrir_modulo(self, archivo, texto):
        carpeta = os.path.dirname(os.path.abspath(__file__))
        ruta = os.path.join(carpeta, archivo)
        module_opened(archivo, "opened_from_panel")
        button_clicked("PanelInicio", texto, f"open:{archivo}")
        if not os.path.exists(ruta):
            posible = os.path.join(BASE_DIR, archivo)
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
        w, h = event.width, event.height
        # Redibujar fondo (imagen o gradiente + overlay)
        try:
            if os.path.exists(BG_IMAGE_PATH):
                bg_img = Image.open(BG_IMAGE_PATH).convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
            else:
                bg_img = Image.new("RGBA", (w, h), "#0f172a")
                draw = ImageDraw.Draw(bg_img)
                for i in range(h):
                    ratio = i / max(1, h)
                    color = (
                        int(15 + (30 - 15) * ratio),
                        int(23 + (41 - 23) * ratio),
                        int(42 + (59 - 42) * ratio),
                        255
                    )
                    draw.line([(0, i), (w, i)], fill=color)
            overlay = Image.new("RGBA", (w, h), (0, 0, 0, 80))
            bg_img = Image.alpha_composite(bg_img, overlay)
            self.bg_image = ImageTk.PhotoImage(bg_img)
            self.canvas.itemconfig(self.bg_id, image=self.bg_image)
        except Exception:
            pass

        # Reposicionar título y grid
        self.canvas.coords(self.title_window, w // 2 - 420, 0)  # título alineado a la izquierda del centro
        grid_top = int(h * 0.18)
        self.canvas.coords(self.grid_window, w // 2, grid_top + (h - grid_top) // 2)

    def _on_close(self):
        end_user_session()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    start_user_session()
    app = PanelInicio(root)
    root.mainloop()




