import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime

DATA_FILE = "ordenes_taller.json"

SERVICIOS = [
    "Cambio de aceite",
    "Alineación y balanceo",
    "Frenos (pastillas/discos)",
    "Diagnóstico eléctrico",
    "Cambio de batería",
    "Suspensión",
    "Afinación general",
]

REPUESTOS = [
    {"nombre": "Aceite 10W-40", "precio": 45000},
    {"nombre": "Filtro de aceite", "precio": 25000},
    {"nombre": "Pastillas de freno", "precio": 90000},
    {"nombre": "Batería 12V", "precio": 320000},
    {"nombre": "Amortiguador", "precio": 180000},
    {"nombre": "Filtro de aire", "precio": 30000},
    {"nombre": "Líquido de frenos", "precio": 28000},
]

ESTADOS = ["Pendiente", "En proceso", "Terminado"]

# ---------------------------
# Utilidades de persistencia
# ---------------------------
def cargar_ordenes():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def guardar_ordenes(ordenes):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(ordenes, f, ensure_ascii=False, indent=2)

# ---------------------------
# Validaciones y helpers
# ---------------------------
def validar_campos(data):
    requeridos = ["placa", "marca", "modelo", "anio", "cliente", "telefono", "diagnostico", "servicio", "estado"]
    for r in requeridos:
        if not data.get(r):
            return False, f"El campo '{r}' es obligatorio."
    # Año numérico y razonable
    try:
        anio = int(data["anio"])
        if anio < 1960 or anio > datetime.now().year + 1:
            return False, "El año del vehículo es inválido."
    except ValueError:
        return False, "El año del vehículo debe ser numérico."
    # Teléfono básico
    if len(data["telefono"]) < 7:
        return False, "El teléfono parece incompleto."
    return True, ""

def calcular_totales(repuestos_seleccionados):
    subtotal = sum(r["precio"] for r in repuestos_seleccionados)
    iva = round(subtotal * 0.19)
    total = subtotal + iva
    return subtotal, iva, total

# ---------------------------
# Aplicación principal
# ---------------------------
class OrdenesTallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Órdenes de Trabajo - Taller Mecánico")
        self.root.geometry("1150x700")
        self.root.configure(bg="#0f172a")  # Azul oscuro

        self.ordenes = cargar_ordenes()
        self.repuestos_seleccionados = []

        self._configurar_estilos()
        self._construir_layout()

    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Paleta
        self.color_bg = "#0f172a"      # Azul oscuro
        self.color_panel = "#1e293b"   # Azul gris
        self.color_acento = "#f59e0b"  # Naranja
        self.color_ok = "#22c55e"      # Verde
        self.color_texto = "#e2e8f0"   # Gris claro

        style.configure("TLabel", foreground=self.color_texto, background=self.color_panel, font=("Segoe UI", 10))
        style.configure("Title.TLabel", foreground=self.color_texto, background=self.color_bg, font=("Segoe UI Semibold", 16))
        style.configure("Section.TLabelframe", background=self.color_panel, bordercolor=self.color_acento)
        style.configure("Section.TLabelframe.Label", foreground=self.color_texto, background=self.color_panel, font=("Segoe UI Semibold", 12))
        style.configure("TEntry", fieldbackground="#0b1220", foreground=self.color_texto)
        style.configure("TCombobox", fieldbackground="#0b1220", foreground=self.color_texto)
        style.configure("Accent.TButton", background=self.color_acento, foreground="#111827", font=("Segoe UI Semibold", 10))
        style.map("Accent.TButton", background=[("active", "#fbbf24")])
        style.configure("Ok.TButton", background=self.color_ok, foreground="#0b1220", font=("Segoe UI Semibold", 10))
        style.map("Ok.TButton", background=[("active", "#4ade80")])

        style.configure("Treeview", background="#0b1220", foreground=self.color_texto, fieldbackground="#0b1220", rowheight=26)
        style.configure("Treeview.Heading", background=self.color_panel, foreground=self.color_texto, font=("Segoe UI Semibold", 10))

    def _construir_layout(self):
        # Título
        title = ttk.Label(self.root, text="Módulo de Órdenes de Trabajo", style="Title.TLabel")
        title.pack(pady=12)

        # Contenedor principal
        main = tk.Frame(self.root, bg=self.color_bg)
        main.pack(fill="both", expand=True, padx=12, pady=8)

        # Panel izquierdo (formulario)
        left = tk.Frame(main, bg=self.color_panel, bd=0, highlightthickness=0)
        left.pack(side="left", fill="y", padx=(0, 8), pady=0)

        # Panel derecho (tabla y acciones)
        right = tk.Frame(main, bg=self.color_panel, bd=0, highlightthickness=0)
        right.pack(side="right", fill="both", expand=True, padx=(8, 0), pady=0)

        # --- Sección vehículo y cliente ---
        veh_frame = ttk.LabelFrame(left, text="Datos del vehículo y cliente", style="Section.TLabelframe")
        veh_frame.pack(fill="x", padx=12, pady=12)

        self.placa_var = tk.StringVar()
        self.marca_var = tk.StringVar()
        self.modelo_var = tk.StringVar()
        self.anio_var = tk.StringVar()
        self.cliente_var = tk.StringVar()
        self.telefono_var = tk.StringVar()

        self._add_labeled_entry(veh_frame, "Placa", self.placa_var, 0, 0)
        self._add_labeled_entry(veh_frame, "Marca", self.marca_var, 0, 1)
        self._add_labeled_entry(veh_frame, "Modelo", self.modelo_var, 1, 0)
        self._add_labeled_entry(veh_frame, "Año", self.anio_var, 1, 1)
        self._add_labeled_entry(veh_frame, "Cliente", self.cliente_var, 2, 0)
        self._add_labeled_entry(veh_frame, "Teléfono", self.telefono_var, 2, 1)

        # --- Diagnóstico y servicio ---
        diag_frame = ttk.LabelFrame(left, text="Diagnóstico y servicio", style="Section.TLabelframe")
        diag_frame.pack(fill="x", padx=12, pady=12)

        self.diagnostico_txt = tk.Text(diag_frame, height=4, width=40, bg="#0b1220", fg=self.color_texto, insertbackground=self.color_texto)
        self._add_labeled_widget(diag_frame, "Diagnóstico", self.diagnostico_txt, 0, 0, colspan=2)

        self.servicio_var = tk.StringVar()
        servicio_cb = ttk.Combobox(diag_frame, textvariable=self.servicio_var, values=SERVICIOS, state="readonly")
        servicio_cb.current(0)
        self._add_labeled_widget(diag_frame, "Servicio", servicio_cb, 1, 0)

        self.estado_var = tk.StringVar()
        estado_cb = ttk.Combobox(diag_frame, textvariable=self.estado_var, values=ESTADOS, state="readonly")
        estado_cb.current(0)
        self._add_labeled_widget(diag_frame, "Estado", estado_cb, 1, 1)

        # --- Repuestos ---
        rep_frame = ttk.LabelFrame(left, text="Repuestos utilizados", style="Section.TLabelframe")
        rep_frame.pack(fill="x", padx=12, pady=12)

        self.repuesto_cb_var = tk.StringVar()
        repuesto_cb = ttk.Combobox(rep_frame, textvariable=self.repuesto_cb_var, values=[r["nombre"] for r in REPUESTOS], state="readonly", width=28)
        repuesto_cb.current(0)
        repuesto_cb.grid(row=0, column=0, padx=6, pady=6, sticky="ew")

        add_rep_btn = ttk.Button(rep_frame, text="Agregar repuesto", style="Accent.TButton", command=self.agregar_repuesto)
        add_rep_btn.grid(row=0, column=1, padx=6, pady=6)

        self.rep_list = tk.Listbox(rep_frame, height=6, bg="#0b1220", fg=self.color_texto)
        self.rep_list.grid(row=1, column=0, columnspan=2, padx=6, pady=6, sticky="ew")

        remove_rep_btn = ttk.Button(rep_frame, text="Quitar seleccionado", style="Accent.TButton", command=self.quitar_repuesto)
        remove_rep_btn.grid(row=2, column=0, padx=6, pady=6, sticky="w")

        # Totales
        tot_frame = ttk.LabelFrame(left, text="Totales", style="Section.TLabelframe")
        tot_frame.pack(fill="x", padx=12, pady=12)

        self.subtotal_var = tk.StringVar(value="$0")
        self.iva_var = tk.StringVar(value="$0")
        self.total_var = tk.StringVar(value="$0")

        ttk.Label(tot_frame, text="Subtotal:").grid(row=0, column=0, padx=6, pady=4, sticky="w")
        ttk.Label(tot_frame, textvariable=self.subtotal_var).grid(row=0, column=1, padx=6, pady=4, sticky="e")

        ttk.Label(tot_frame, text="IVA (19%):").grid(row=1, column=0, padx=6, pady=4, sticky="w")
        ttk.Label(tot_frame, textvariable=self.iva_var).grid(row=1, column=1, padx=6, pady=4, sticky="e")

        ttk.Label(tot_frame, text="Total:").grid(row=2, column=0, padx=6, pady=4, sticky="w")
        ttk.Label(tot_frame, textvariable=self.total_var).grid(row=2, column=1, padx=6, pady=4, sticky="e")

        # Botones acción
        actions = tk.Frame(left, bg=self.color_panel)
        actions.pack(fill="x", padx=12, pady=8)

        save_btn = ttk.Button(actions, text="Guardar orden", style="Ok.TButton", command=self.guardar_orden)
        save_btn.pack(side="left", padx=6, pady=6)

        clear_btn = ttk.Button(actions, text="Limpiar", style="Accent.TButton", command=self.limpiar_formulario)
        clear_btn.pack(side="left", padx=6, pady=6)

        # --- Tabla de órdenes ---
        table_frame = ttk.LabelFrame(right, text="Órdenes registradas", style="Section.TLabelframe")
        table_frame.pack(fill="both", expand=True, padx=12, pady=12)

        cols = ("fecha", "placa", "cliente", "servicio", "estado", "total")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
        self.tree.column("fecha", width=140)
        self.tree.column("placa", width=100)
        self.tree.column("cliente", width=180)
        self.tree.column("servicio", width=180)
        self.tree.column("estado", width=120)
        self.tree.column("total", width=120)
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)

        # Barra de búsqueda y edición
        search_frame = tk.Frame(right, bg=self.color_panel)
        search_frame.pack(fill="x", padx=12, pady=6)

        tk.Label(search_frame, text="Buscar (placa/cliente):", bg=self.color_panel, fg=self.color_texto).pack(side="left", padx=6)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", padx=6)
        ttk.Button(search_frame, text="Filtrar", style="Accent.TButton", command=self.filtrar).pack(side="left", padx=6)
        ttk.Button(search_frame, text="Ver todo", style="Accent.TButton", command=self.refrescar_tabla).pack(side="left", padx=6)
        ttk.Button(search_frame, text="Editar seleccionada", style="Accent.TButton", command=self.editar_seleccion).pack(side="right", padx=6)
        ttk.Button(search_frame, text="Eliminar seleccionada", style="Accent.TButton", command=self.eliminar_seleccion).pack(side="right", padx=6)

        self.refrescar_tabla()

    # ---------------------------
    # Construcción de widgets
    # ---------------------------
    def _add_labeled_entry(self, parent, label, var, row, col):
        ttk.Label(parent, text=label).grid(row=row, column=col*2, padx=6, pady=6, sticky="w")
        entry = ttk.Entry(parent, textvariable=var, width=24)
        entry.grid(row=row, column=col*2+1, padx=6, pady=6, sticky="ew")

    def _add_labeled_widget(self, parent, label, widget, row, col, colspan=1):
        ttk.Label(parent, text=label).grid(row=row, column=col*2, padx=6, pady=6, sticky="w")
        widget.grid(row=row, column=col*2+1, padx=6, pady=6, sticky="ew", columnspan=colspan)

    # ---------------------------
    # Lógica de repuestos
    # ---------------------------
    def agregar_repuesto(self):
        nombre = self.repuesto_cb_var.get()
        rep = next((r for r in REPUESTOS if r["nombre"] == nombre), None)
        if rep:
            self.repuestos_seleccionados.append(rep)
            self.rep_list.insert("end", f"{rep['nombre']} - ${rep['precio']:,}")
            self._actualizar_totales()

    def quitar_repuesto(self):
        sel = self.rep_list.curselection()
        if not sel:
            return
        idx = sel[0]
        self.rep_list.delete(idx)
        del self.repuestos_seleccionados[idx]
        self._actualizar_totales()

    def _actualizar_totales(self):
        subtotal, iva, total = calcular_totales(self.repuestos_seleccionados)
        self.subtotal_var.set(f"${subtotal:,}")
        self.iva_var.set(f"${iva:,}")
        self.total_var.set(f"${total:,}")

    # ---------------------------
    # Guardar, limpiar y tabla
    # ---------------------------
    def guardar_orden(self):
        data = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "placa": self.placa_var.get().strip().upper(),
            "marca": self.marca_var.get().strip(),
            "modelo": self.modelo_var.get().strip(),
            "anio": self.anio_var.get().strip(),
            "cliente": self.cliente_var.get().strip(),
            "telefono": self.telefono_var.get().strip(),
            "diagnostico": self.diagnostico_txt.get("1.0", "end").strip(),
            "servicio": self.servicio_var.get(),
            "estado": self.estado_var.get(),
            "repuestos": self.repuestos_seleccionados.copy(),
        }
        ok, msg = validar_campos(data)
        if not ok:
            messagebox.showwarning("Validación", msg)
            return

        subtotal, iva, total = calcular_totales(self.repuestos_seleccionados)
        data["subtotal"] = subtotal
        data["iva"] = iva
        data["total"] = total

        self.ordenes.append(data)
        guardar_ordenes(self.ordenes)
        self.refrescar_tabla()
        messagebox.showinfo("Éxito", "Orden guardada correctamente.")
        self.limpiar_formulario()

    def limpiar_formulario(self):
        self.placa_var.set("")
        self.marca_var.set("")
        self.modelo_var.set("")
        self.anio_var.set("")
        self.cliente_var.set("")
        self.telefono_var.set("")
        self.diagnostico_txt.delete("1.0", "end")
        self.servicio_var.set(SERVICIOS[0])
        self.estado_var.set(ESTADOS[0])
        self.rep_list.delete(0, "end")
        self.repuestos_seleccionados = []
        self._actualizar_totales()

    def refrescar_tabla(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for o in self.ordenes:
            self.tree.insert("", "end", values=(
                o.get("fecha", ""),
                o.get("placa", ""),
                o.get("cliente", ""),
                o.get("servicio", ""),
                o.get("estado", ""),
                f"${o.get('total', 0):,}"
            ))

    def filtrar(self):
        query = self.search_var.get().strip().lower()
        for i in self.tree.get_children():
            self.tree.delete(i)
        for o in self.ordenes:
            if query in o.get("placa", "").lower() or query in o.get("cliente", "").lower():
                self.tree.insert("", "end", values=(
                    o.get("fecha", ""),
                    o.get("placa", ""),
                    o.get("cliente", ""),
                    o.get("servicio", ""),
                    o.get("estado", ""),
                    f"${o.get('total', 0):,}"
                ))

    def editar_seleccion(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Edición", "Selecciona una orden en la tabla.")
            return
        idx = self.tree.index(sel[0])
        orden = self.ordenes[idx]

        # Cargar en formulario
        self.placa_var.set(orden["placa"])
        self.marca_var.set(orden["marca"])
        self.modelo_var.set(orden["modelo"])
        self.anio_var.set(str(orden["anio"]))
        self.cliente_var.set(orden["cliente"])
        self.telefono_var.set(orden["telefono"])
        self.diagnostico_txt.delete("1.0", "end")
        self.diagnostico_txt.insert("end", orden["diagnostico"])
        self.servicio_var.set(orden["servicio"])
        self.estado_var.set(orden["estado"])

        self.rep_list.delete(0, "end")
        self.repuestos_seleccionados = orden.get("repuestos", []).copy()
        for r in self.repuestos_seleccionados:
            self.rep_list.insert("end", f"{r['nombre']} - ${r['precio']:,}")
        self._actualizar_totales()

        messagebox.showinfo("Edición", "La orden se cargó al formulario. Modifica y presiona 'Guardar orden' para actualizar.")

    def eliminar_seleccion(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Eliminar", "Selecciona una orden en la tabla.")
            return
        idx = self.tree.index(sel[0])
        confirm = messagebox.askyesno("Confirmar", "¿Eliminar la orden seleccionada?")
        if confirm:
            del self.ordenes[idx]
            guardar_ordenes(self.ordenes)
            self.refrescar_tabla()
            messagebox.showinfo("Eliminar", "Orden eliminada.")

# ---------------------------
# Lanzamiento
# ---------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = OrdenesTallerApp(root)
    root.mainloop()
