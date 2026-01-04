import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class InventarioTaller:
    def __init__(self, root):
        self.root = root
        self.root.title("📦 Inventario - Taller Mecánico")
        self.root.geometry("800x500")
        self.root.resizable(False, False)

        self._configurar_estilos()
        self._cargar_fondo()
        self._construir_formulario()

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

        style.configure("Form.TEntry",
                        fieldbackground="#ffffff",
                        foreground="#111827",
                        padding=4)

    def _cargar_fondo(self):
        fondo = Image.open(r"C:\RICHARD\RB\2025\Taller_mecánica\panel_de_inicio_fondo.png")
        fondo = fondo.resize((800, 500), Image.Resampling.LANCZOS)
        self.bg_image = ImageTk.PhotoImage(fondo)

        self.canvas = tk.Canvas(self.root, width=800, height=500, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")

    def _construir_formulario(self):
        self.content_frame = tk.Frame(self.root, bg="#ffffff")
        self.canvas.create_window(400, 250, window=self.content_frame, width=600, height=360)

        titulo = tk.Label(self.content_frame, text="📦 Registro de Inventario",
                          font=("Segoe UI Semibold", 18),
                          bg="#ffffff", fg="#111827")
        titulo.grid(row=0, column=0, columnspan=2, pady=(10, 20))

        etiquetas = ["Código:", "Producto:", "Cantidad:", "Precio Unitario:"]
        self.entries = {}

        for i, etiqueta in enumerate(etiquetas, start=1):
            lbl = tk.Label(self.content_frame, text=etiqueta,
                           font=("Segoe UI", 12),
                           bg="#ffffff", fg="#111827", anchor="e")
            lbl.grid(row=i, column=0, sticky="e", padx=(40, 10), pady=8)

            entry = ttk.Entry(self.content_frame, width=32, style="Form.TEntry")
            entry.grid(row=i, column=1, sticky="w", padx=(10, 40), pady=8)
            self.entries[etiqueta] = entry

        btn_guardar = ttk.Button(self.content_frame, text="💾 Guardar Producto",
                                 style="Menu.TButton",
                                 command=self._guardar_producto)
        btn_guardar.grid(row=6, column=0, padx=40, pady=(20, 10), sticky="e")

        btn_salir = ttk.Button(self.content_frame, text="❌ Cerrar",
                               style="Menu.TButton",
                               command=self.root.destroy)
        btn_salir.grid(row=6, column=1, padx=40, pady=(20, 10), sticky="w")

        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)

    def _guardar_producto(self):
        datos = {
            "Código": self.entries["Código:"].get(),
            "Producto": self.entries["Producto:"].get(),
            "Cantidad": self.entries["Cantidad:"].get(),
            "Precio Unitario": self.entries["Precio Unitario:"].get()
        }
        print("✅ Producto registrado en inventario:", datos)
        # Aquí puedes guardar en archivo CSV, Excel o base de datos

if __name__ == "__main__":
    root = tk.Tk()
    app = InventarioTaller(root)
    root.mainloop()

