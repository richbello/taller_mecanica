import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import json, os
import openpyxl

# Archivo JSON donde se guardan las órdenes
DATA_FILE = r"C:\RICHARD\RB\2025\Taller Mecánica\ordenes_taller.json"

# Archivo Excel de salida
OUTPUT_FILE = r"C:\RICHARD\RB\2025\Taller Mecánica\ordenes_taller.xlsx"

def cargar_ordenes():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

class ExportarExcelApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📤 Exportar Órdenes a Excel - Taller Mecánico")
        self.root.geometry("1150x700")
        self.root.resizable(False, False)

        self._configurar_estilos()
        self._cargar_fondo()
        self._construir_layout()

    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")
        self.color_bg = "#0f172a"
        self.color_panel = "#1e293b"
        self.color_acento = "#f59e0b"
        self.color_ok = "#22c55e"
        self.color_texto = "#e2e8f0"
        style.configure("Title.TLabel", foreground=self.color_texto, background=self.color_bg, font=("Segoe UI Semibold", 16))
        style.configure("Accent.TButton", background=self.color_acento, foreground="#111827", font=("Segoe UI Semibold", 10))
        style.map("Accent.TButton", background=[("active", "#fbbf24")])
        style.configure("Ok.TButton", background=self.color_ok, foreground="#0b1220", font=("Segoe UI Semibold", 10))
        style.map("Ok.TButton", background=[("active", "#4ade80")])

    def _cargar_fondo(self):
        fondo = Image.open(r"C:\RICHARD\RB\2025\Taller_mecánica\panel_de_inicio_fondo.png")
        fondo = fondo.resize((1150, 700), Image.Resampling.LANCZOS)
        self.bg_image = ImageTk.PhotoImage(fondo)

        self.canvas = tk.Canvas(self.root, width=1150, height=700, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")

        self.main_frame = tk.Frame(self.root, bg=self.color_bg)
        self.canvas.create_window(575, 350, window=self.main_frame, width=1120, height=660)

    def _construir_layout(self):
        title = ttk.Label(self.main_frame, text="Exportar Órdenes a Excel", style="Title.TLabel")
        title.pack(pady=12)

        frame = tk.Frame(self.main_frame, bg=self.color_panel)
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        ttk.Button(frame, text="📤 Exportar a Excel", style="Ok.TButton", command=self.exportar_a_excel).pack(pady=20)

    def exportar_a_excel(self):
        ordenes = cargar_ordenes()
        if not ordenes:
            messagebox.showwarning("Exportar", "⚠️ No se encontró el archivo ordenes_taller.json o está vacío.")
            return

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Órdenes de Trabajo"

        headers = ["Fecha", "Placa", "Cliente", "Servicio", "Estado", "Subtotal", "IVA", "Total"]
        ws.append(headers)

        for o in ordenes:
            ws.append([
                o.get("fecha", ""),
                o.get("placa", ""),
                o.get("cliente", ""),
                o.get("servicio", ""),
                o.get("estado", ""),
                o.get("subtotal", 0),
                o.get("iva", 0),
                o.get("total", 0)
            ])

        try:
            wb.save(OUTPUT_FILE)
            messagebox.showinfo("Exportar", f"✅ Órdenes exportadas correctamente a:\n{OUTPUT_FILE}")
        except PermissionError:
            messagebox.showerror("Exportar", "⚠️ No se pudo guardar el archivo porque está abierto en Excel.\nCiérralo y vuelve a intentar.")

# ---------------------------
# Lanzamiento
# ---------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = ExportarExcelApp(root)
    root.mainloop()


