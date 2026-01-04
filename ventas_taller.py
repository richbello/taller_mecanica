import tkinter as tk
from tkinter import ttk, messagebox
import json, os, datetime

DATA_FILE = "ventas.json"

def cargar_ventas():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def guardar_ventas(ventas):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(ventas, f, ensure_ascii=False, indent=2)

class VentasApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Módulo de Ventas - Taller Mecánico")
        self.root.geometry("900x500")
        self.root.configure(bg="#0f172a")

        self.ventas = cargar_ventas()
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

        self.cliente_var = tk.StringVar()
        self.producto_var = tk.StringVar()
        self.cantidad_var = tk.IntVar()
        self.precio_var = tk.IntVar()

        ttk.Label(frame, text="Cliente:").grid(row=0, column=0, padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.cliente_var).grid(row=0, column=1, padx=6, pady=6)

        ttk.Label(frame, text="Producto:").grid(row=1, column=0, padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.producto_var).grid(row=1, column=1, padx=6, pady=6)

        ttk.Label(frame, text="Cantidad:").grid(row=2, column=0, padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.cantidad_var).grid(row=2, column=1, padx=6, pady=6)

        ttk.Label(frame, text="Precio unitario:").grid(row=3, column=0, padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.precio_var).grid(row=3, column=1, padx=6, pady=6)

        ttk.Button(frame, text="Registrar venta", style="Ok.TButton", command=self.guardar_venta).grid(row=4, column=0, padx=6, pady=6)
        ttk.Button(frame, text="Eliminar seleccionada", style="Accent.TButton", command=self.eliminar_venta).grid(row=4, column=1, padx=6, pady=6)

        self.tree = ttk.Treeview(frame, columns=("fecha", "cliente", "producto", "cantidad", "total"), show="headings")
        for c in ("fecha", "cliente", "producto", "cantidad", "total"):
            self.tree.heading(c, text=c.capitalize())
        self.tree.grid(row=5, column=0, columnspan=2, sticky="nsew", padx=6, pady=6)

        self.refrescar_tabla()

    def guardar_venta(self):
        total = self.cantidad_var.get() * self.precio_var.get()
        data = {
            "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "cliente": self.cliente_var.get(),
            "producto": self.producto_var.get(),
            "cantidad": self.cantidad_var.get(),
            "total": total
        }
        if not data["cliente"] or not data["producto"]:
            messagebox.showwarning("Validación", "Cliente y producto son obligatorios")
            return
        self.ventas.append(data)
        guardar_ventas(self.ventas)
        self.refrescar_tabla()
        messagebox.showinfo("Éxito", "Venta registrada")
        self.cliente_var.set("")
        self.producto_var.set("")
        self.cantidad_var.set(0)
        self.precio_var.set(0)

    def eliminar_venta(self):
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        del self.ventas[idx]
        guardar_ventas(self.ventas)
        self.refrescar_tabla()

    def refrescar_tabla(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for v in self.ventas:
            self.tree.insert("", "end", values=(v["fecha"], v["cliente"], v["producto"], v["cantidad"], f"${v['total']:,}"))

if __name__ == "__main__":
    root = tk.Tk()
    app = VentasApp(root)
    root.mainloop()
