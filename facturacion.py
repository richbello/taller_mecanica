import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from datetime import datetime
import json, os

# Persistencia
FACTURAS_FILE = r"C:\RICHARD\RB\2025\Taller Mecánica\facturas.json"

def cargar_facturas():
    if not os.path.exists(FACTURAS_FILE):
        return []
    try:
        with open(FACTURAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def guardar_facturas(facturas):
    os.makedirs(os.path.dirname(FACTURAS_FILE), exist_ok=True)
    with open(FACTURAS_FILE, "w", encoding="utf-8") as f:
        json.dump(facturas, f, ensure_ascii=False, indent=2)

def formatear_moneda(v):
    try:
        return f"${float(v):,.0f}"
    except:
        return "$0"

class FacturacionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🧾 Módulo de Facturación - Taller Mecánico")
        self.root.geometry("1150x700")
        self.root.resizable(True, True)

        # Estado
        self.facturas = cargar_facturas()
        self.items = []  # [{descripcion, cantidad, precio, total}]

        # Estilo y fondo
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
        style.configure("TLabel", foreground=self.color_texto, background=self.color_panel, font=("Segoe UI", 10))
        style.configure("Title.TLabel", foreground=self.color_texto, background=self.color_bg, font=("Segoe UI Semibold", 16))
        style.configure("Section.TLabelframe", background=self.color_panel, bordercolor=self.color_acento)
        style.configure("Section.TLabelframe.Label", foreground=self.color_texto, background=self.color_panel, font=("Segoe UI Semibold", 12))
        style.configure("Accent.TButton", background=self.color_acento, foreground="#111827", font=("Segoe UI Semibold", 10))
        style.map("Accent.TButton", background=[("active", "#fbbf24")])
        style.configure("Ok.TButton", background=self.color_ok, foreground="#0b1220", font=("Segoe UI Semibold", 10))
        style.map("Ok.TButton", background=[("active", "#4ade80")])
        style.configure("Treeview", background="#0b1220", foreground=self.color_texto, fieldbackground="#0b1220", rowheight=26)
        style.configure("Treeview.Heading", background=self.color_panel, foreground=self.color_texto, font=("Segoe UI Semibold", 10))

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
        ttk.Label(self.main_frame, text="Módulo de Facturación", style="Title.TLabel").pack(pady=12)

        main = tk.Frame(self.main_frame, bg=self.color_bg)
        main.pack(fill="both", expand=True, padx=12, pady=8)

        # Panel izquierdo: datos factura y cliente
        left = tk.Frame(main, bg=self.color_panel)
        left.pack(side="left", fill="y", padx=(0, 8))

        datos_frame = ttk.LabelFrame(left, text="Datos de la factura", style="Section.TLabelframe")
        datos_frame.pack(fill="x", padx=12, pady=12)

        actions = tk.Frame(left, bg=self.color_panel)
        actions.pack(fill="x", padx=12, pady=8)
        ttk.Button(actions, text="Emitir factura", style="Ok.TButton", command=self.emitir_factura).pack(side="left", padx=6)
        ttk.Button(actions, text="Limpiar", style="Accent.TButton", command=self.limpiar_form).pack(side="left", padx=6)
        
        ttk.Button(actions, text="Guardar orden", style="Accent.TButton", command=self.emitir_factura).pack(side="left", padx=6)


        self.var_num = tk.StringVar()
        self.var_fecha = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.var_cliente = tk.StringVar()
        self.var_ident = tk.StringVar()
        self.var_placa = tk.StringVar()
        self.var_estado = tk.StringVar(value="Emitida")

        def add_row(parent, label, var):
            row = tk.Frame(parent, bg=self.color_panel)
            row.pack(fill="x", padx=8, pady=4)
            tk.Label(row, text=label, bg=self.color_panel, fg=self.color_texto, width=14, anchor="w").pack(side="left")
            ttk.Entry(row, textvariable=var).pack(side="left", fill="x", expand=True)

        add_row(datos_frame, "N° Factura:", self.var_num)
        add_row(datos_frame, "Fecha:", self.var_fecha)
        add_row(datos_frame, "Cliente:", self.var_cliente)
        add_row(datos_frame, "Identificación:", self.var_ident)
        add_row(datos_frame, "Placa:", self.var_placa)

        # Panel items
        items_frame = ttk.LabelFrame(left, text="Ítems de la factura", style="Section.TLabelframe")
        items_frame.pack(fill="x", padx=12, pady=12)

        self.var_desc = tk.StringVar()
        self.var_cant = tk.StringVar(value="1")
        self.var_precio = tk.StringVar(value="0")

        row_item = tk.Frame(items_frame, bg=self.color_panel)
        row_item.pack(fill="x", padx=8, pady=4)
        tk.Label(row_item, text="Descripción:", bg=self.color_panel, fg=self.color_texto, width=12, anchor="w").pack(side="left")
        ttk.Entry(row_item, textvariable=self.var_desc, width=26).pack(side="left", padx=4)
        tk.Label(row_item, text="Cant:", bg=self.color_panel, fg=self.color_texto, width=6, anchor="w").pack(side="left")
        ttk.Entry(row_item, textvariable=self.var_cant, width=6).pack(side="left", padx=4)
        tk.Label(row_item, text="Precio:", bg=self.color_panel, fg=self.color_texto, width=8, anchor="w").pack(side="left")
        ttk.Entry(row_item, textvariable=self.var_precio, width=10).pack(side="left", padx=4)
        ttk.Button(row_item, text="Agregar ítem", style="Accent.TButton", command=self.agregar_item).pack(side="left", padx=6)

        self.items_list = tk.Listbox(items_frame, height=7, bg="#0b1220", fg=self.color_texto)
        self.items_list.pack(fill="x", padx=8, pady=6)
        ttk.Button(items_frame, text="Quitar seleccionado", style="Accent.TButton", command=self.quitar_item).pack(padx=8, pady=6)

        # Totales
        tot_frame = ttk.LabelFrame(left, text="Totales", style="Section.TLabelframe")
        tot_frame.pack(fill="x", padx=12, pady=12)

        self.var_subtotal = tk.StringVar(value="$0")
        self.var_iva = tk.StringVar(value="$0")
        self.var_total = tk.StringVar(value="$0")

        def add_total(label, var):
            row = tk.Frame(tot_frame, bg=self.color_panel)
            row.pack(fill="x", padx=8, pady=4)
            tk.Label(row, text=label, bg=self.color_panel, fg=self.color_texto, width=12, anchor="w").pack(side="left")
            ttk.Label(row, textvariable=var).pack(side="right")

        add_total("Subtotal:", self.var_subtotal)
        add_total("IVA (19%):", self.var_iva)
        add_total("Total:", self.var_total)

        actions = tk.Frame(left, bg=self.color_panel)
        actions.pack(fill="x", padx=12, pady=8)
        ttk.Button(actions, text="Emitir factura", style="Ok.TButton", command=self.emitir_factura).pack(side="left", padx=6)
        ttk.Button(actions, text="Limpiar", style="Accent.TButton", command=self.limpiar_form).pack(side="left", padx=6)

        # Panel derecho: listado de facturas
        right = tk.Frame(main, bg=self.color_panel)
        right.pack(side="right", fill="both", expand=True, padx=(8, 0))

        table_frame = ttk.LabelFrame(right, text="Facturas emitidas", style="Section.TLabelframe")
        table_frame.pack(fill="both", expand=True, padx=12, pady=12)

        cols = ("num", "fecha", "cliente", "placa", "estado", "total")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
        self.tree.column("num", width=120)
        self.tree.column("fecha", width=160)
        self.tree.column("cliente", width=200)
        self.tree.column("placa", width=100)
        self.tree.column("estado", width=120)
        self.tree.column("total", width=120)
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)

        search_frame = tk.Frame(right, bg=self.color_panel)
        search_frame.pack(fill="x", padx=12, pady=6)
        tk.Label(search_frame, text="Buscar (cliente/placa):", bg=self.color_panel, fg=self.color_texto).pack(side="left", padx=6)
        self.search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_var, width=30).pack(side="left", padx=6)
        ttk.Button(search_frame, text="Filtrar", style="Accent.TButton", command=self.filtrar).pack(side="left", padx=6)
        ttk.Button(search_frame, text="Ver todo", style="Accent.TButton", command=self.refrescar_tabla).pack(side="left", padx=6)
        ttk.Button(search_frame, text="Editar seleccionada", style="Accent.TButton", command=self.editar_seleccion).pack(side="right", padx=6)
        ttk.Button(search_frame, text="Eliminar seleccionada", style="Accent.TButton", command=self.eliminar_seleccion).pack(side="right", padx=6)

        self.refrescar_tabla()

    # Ítems y totales
    def agregar_item(self):
        desc = self.var_desc.get().strip()
        try:
            cant = int(self.var_cant.get().strip() or "1")
            precio = float(self.var_precio.get().strip() or "0")
        except:
            messagebox.showwarning("Ítems", "Cantidad y precio deben ser numéricos.")
            return
        if not desc:
            messagebox.showwarning("Ítems", "La descripción es obligatoria.")
            return
        total = cant * precio
        item = {"descripcion": desc, "cantidad": cant, "precio": precio, "total": total}
        self.items.append(item)
        self.items_list.insert("end", f"{desc} | x{cant} | {formatear_moneda(precio)} → {formatear_moneda(total)}")
        self._recalcular_totales()

    def quitar_item(self):
        sel = self.items_list.curselection()
        if not sel:
            return
        idx = sel[0]
        self.items_list.delete(idx)
        del self.items[idx]
        self._recalcular_totales()

    def _recalcular_totales(self):
        subtotal = sum(i["total"] for i in self.items)
        iva = round(subtotal * 0.19)
        total = subtotal + iva
        self.var_subtotal.set(formatear_moneda(subtotal))
        self.var_iva.set(formatear_moneda(iva))
        self.var_total.set(formatear_moneda(total))

    # Acciones de factura
    def emitir_factura(self):
        data = {
            "num": self.var_num.get().strip() or f"F-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "fecha": self.var_fecha.get().strip() or datetime.now().strftime("%Y-%m-%d %H:%M"),
            "cliente": self.var_cliente.get().strip(),
            "ident": self.var_ident.get().strip(),
            "placa": self.var_placa.get().strip().upper(),
            "estado": self.var_estado.get().strip(),
            "items": self.items.copy(),
        }
        # Validación mínima
        for r in ["cliente", "ident", "placa"]:
            if not data[r]:
                messagebox.showerror("Validación", f"El campo '{r}' es obligatorio.")
                return
        if not data["items"]:
            messagebox.showerror("Validación", "Agrega al menos un ítem a la factura.")
            return

        subtotal = sum(i["total"] for i in data["items"])
        iva = round(subtotal * 0.19)
        total = subtotal + iva
        data["subtotal"] = subtotal
        data["iva"] = iva
        data["total"] = total

        self.facturas.append(data)
        guardar_facturas(self.facturas)
        self.refrescar_tabla()
        messagebox.showinfo("Facturación", f"Factura {data['num']} emitida correctamente.")
        self.limpiar_form()

    def limpiar_form(self):
        self.var_num.set("")
        self.var_fecha.set(datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.var_cliente.set("")
        self.var_ident.set("")
        self.var_placa.set("")
        self.var_estado.set("Emitida")
        self.var_desc.set("")
        self.var_cant.set("1")
        self.var_precio.set("0")
        self.items_list.delete(0, "end")
        self.items = []
        self._recalcular_totales()

    # Tabla
    def refrescar_tabla(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for f in self.facturas:
            self.tree.insert("", "end", values=(
                f.get("num", ""),
                f.get("fecha", ""),
                f.get("cliente", ""),
                f.get("placa", ""),
                f.get("estado", ""),
                formatear_moneda(f.get("total", 0))
            ))

    def filtrar(self):
        q = self.search_var.get().strip().lower()
        for i in self.tree.get_children():
            self.tree.delete(i)
        for f in self.facturas:
            if q in f.get("cliente", "").lower() or q in f.get("placa", "").lower():
                self.tree.insert("", "end", values=(
                    f.get("num", ""),
                    f.get("fecha", ""),
                    f.get("cliente", ""),
                    f.get("placa", ""),
                    f.get("estado", ""),
                    formatear_moneda(f.get("total", 0))
                ))

    def eliminar_seleccion(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Eliminar", "Selecciona una factura en la tabla.")
            return
        idx = self.tree.index(sel[0])
        fac = self.facturas[idx]
        if messagebox.askyesno("Confirmar", f"¿Eliminar la factura {fac.get('num','')} de {fac.get('cliente','')}?"):
            del self.facturas[idx]
            guardar_facturas(self.facturas)
            self.refrescar_tabla()
            messagebox.showinfo("Eliminar", "Factura eliminada.")

    def editar_seleccion(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Editar", "Selecciona una factura en la tabla.")
            return
        idx = self.tree.index(sel[0])
        f = self.facturas[idx]

        # Cargar en formulario para edición rápida
        self.var_num.set(f.get("num",""))
        self.var_fecha.set(f.get("fecha",""))
        self.var_cliente.set(f.get("cliente",""))
        self.var_ident.set(f.get("ident",""))
        self.var_placa.set(f.get("placa",""))
        self.var_estado.set(f.get("estado","Emitida"))
        self.items = f.get("items", []).copy()
        self.items_list.delete(0, "end")
        for i in self.items:
            self.items_list.insert("end", f"{i['descripcion']} | x{i['cantidad']} | {formatear_moneda(i['precio'])} → {formatear_moneda(i['total'])}")
        self._recalcular_totales()
        messagebox.showinfo("Editar", "Factura cargada al formulario. Modifica y presiona 'Emitir factura' para actualizar.")

# Lanzamiento
if __name__ == "__main__":
    root = tk.Tk()
    app = FacturacionApp(root)
    root.mainloop()
