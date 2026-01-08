import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import json
from datetime import datetime
import openpyxl

# Ruta de persistencia y exportación
BASE_DIR = r"C:\RICHARD\RB\2025\Taller_mecánica"
DB_FILE = os.path.join(BASE_DIR, "ventas.json")
EXPORT_FILE = os.path.join(BASE_DIR, "ventas_taller.xlsx")
FONDO_PATH = os.path.join(BASE_DIR, "panel_de_inicio_fondo.png")  # imagen opcional

def format_currency(v):
    try:
        return f"${int(v):,}"
    except Exception:
        return f"${v}"

class VentasTaller:
    def __init__(self, root):
        self.root = root
        self.root.title("📊 Registrar Venta - Taller Mecánico")
        self.root.geometry("900x520")
        self.root.minsize(700, 460)
        self.root.resizable(True, True)

        # Datos en memoria
        self.ventas = []
        self.edit_id = None
        self.next_id = 1

        self.bg_orig = None
        self._configurar_estilos()
        self._cargar_fondo()
        self._construir_formulario()
        self._cargar_datos_desde_archivo()

        # Ajuste al redimensionar
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Menu.TButton",
                        background="#f59e0b",
                        foreground="#111827",
                        font=("Segoe UI Semibold", 11),
                        padding=6,
                        relief="flat",
                        borderwidth=0)
        style.map("Menu.TButton", background=[("active", "#fbbf24")])

        style.configure("Form.TEntry",
                        fieldbackground="#ffffff",
                        foreground="#111827",
                        padding=4)

        style.configure("Treeview",
                        background="#ffffff",
                        foreground="#111827",
                        rowheight=24)
        style.configure("Treeview.Heading", font=("Segoe UI Semibold", 10))

    def _cargar_fondo(self):
        try:
            fondo = Image.open(FONDO_PATH)
            self.bg_orig = fondo.convert("RGBA")
            self.canvas = tk.Canvas(self.root, width=900, height=520, highlightthickness=0)
            self.canvas.pack(fill="both", expand=True)
            inicial = self.bg_orig.resize((900, 520), Image.Resampling.LANCZOS)
            self.bg_image = ImageTk.PhotoImage(inicial)
            self.bg_id = self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")
        except Exception:
            # Si falla, usar canvas neutro
            self.canvas = tk.Canvas(self.root, width=900, height=520, highlightthickness=0, bg="#f0f0f0")
            self.canvas.pack(fill="both", expand=True)
            self.bg_id = None

    def _construir_formulario(self):
        # Frame central insertado en canvas
        self.content_frame = tk.Frame(self.root, bg="#ffffff")
        self.window_id = self.canvas.create_window(450, 260, window=self.content_frame, width=820, height=460)

        titulo = tk.Label(self.content_frame, text="📊 Registrar Venta",
                          font=("Segoe UI Semibold", 18),
                          bg="#ffffff", fg="#111827")
        titulo.grid(row=0, column=0, columnspan=3, pady=(8, 14))

        etiquetas = ["Cliente", "Producto", "Cantidad", "Precio"]
        self.entries = {}

        for i, etiqueta in enumerate(etiquetas, start=1):
            lbl = tk.Label(self.content_frame, text=f"{etiqueta}:",
                           font=("Segoe UI", 11),
                           bg="#ffffff", fg="#111827", anchor="e")
            lbl.grid(row=i, column=0, sticky="e", padx=(16, 8), pady=6)

            entry = ttk.Entry(self.content_frame, width=36, style="Form.TEntry")
            entry.grid(row=i, column=1, sticky="w", padx=(8, 12), pady=6)
            self.entries[etiqueta] = entry

        # Mostrar Total calculado
        lbl_total = tk.Label(self.content_frame, text="Total:",
                             font=("Segoe UI", 11),
                             bg="#ffffff", fg="#111827", anchor="e")
        lbl_total.grid(row=5, column=0, sticky="e", padx=(16,8), pady=6)
        self.total_var = tk.StringVar(value=format_currency(0))
        tk.Label(self.content_frame, textvariable=self.total_var, font=("Segoe UI", 11, "bold"),
                 bg="#ffffff", fg="#111827").grid(row=5, column=1, sticky="w")

        # Botones acción
        btn_guardar = ttk.Button(self.content_frame, text="💾 Guardar", style="Menu.TButton",
                                 command=self._guardar_venta)
        btn_guardar.grid(row=6, column=0, padx=12, pady=(12, 6), sticky="e")

        btn_limpiar = ttk.Button(self.content_frame, text="🧹 Limpiar", style="Menu.TButton",
                                 command=self._limpiar_formulario)
        btn_limpiar.grid(row=6, column=1, padx=12, pady=(12, 6), sticky="w")

        # -------------------------
        # Panel derecho: listado
        # -------------------------
        listado_frame = tk.Frame(self.content_frame, bg="#ffffff", bd=0)
        listado_frame.grid(row=1, column=2, rowspan=6, padx=(6, 16), pady=6, sticky="nsew")

        lbl_list = tk.Label(listado_frame, text="Ventas registradas",
                            font=("Segoe UI Semibold", 12),
                            bg="#ffffff", fg="#111827")
        lbl_list.pack(anchor="w", pady=(0, 6))

        cols = ("Cliente", "Producto", "Cantidad", "Precio", "Total")
        self.tree = ttk.Treeview(listado_frame, columns=cols, show="headings", height=14)
        for c in cols:
            self.tree.heading(c, text=c)
            if c == "Cliente" or c == "Producto":
                self.tree.column(c, width=160)
            else:
                self.tree.column(c, width=90, anchor="e")

        scrollbar = ttk.Scrollbar(listado_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y", padx=(0,4))
        self.tree.pack(fill="both", expand=True)

        # Bindings
        self.tree.bind("<Double-1>", lambda e: self._cargar_seleccion_para_editar())
        # actualizar total cuando cambian cantidad/precio
        self.entries["Cantidad"].bind("<FocusOut>", lambda e: self._actualizar_total_display())
        self.entries["Precio"].bind("<FocusOut>", lambda e: self._actualizar_total_display())

        # Botones CRUD para lista
        buttons_row = tk.Frame(listado_frame, bg="#ffffff")
        buttons_row.pack(fill="x", pady=(8, 0))

        btn_nuevo = ttk.Button(buttons_row, text="🆕 Nuevo", style="Menu.TButton", command=self._nuevo)
        btn_nuevo.pack(side="left", padx=4)

        btn_modificar = ttk.Button(buttons_row, text="✏️ Modificar", style="Menu.TButton",
                                   command=self._cargar_seleccion_para_editar)
        btn_modificar.pack(side="left", padx=4)

        btn_eliminar = ttk.Button(buttons_row, text="🗑️ Eliminar", style="Menu.TButton",
                                  command=self._eliminar_venta)
        btn_eliminar.pack(side="left", padx=4)

        btn_export = ttk.Button(buttons_row, text="📤 Exportar Excel", style="Menu.TButton",
                                command=self._exportar_excel)
        btn_export.pack(side="right", padx=4)

        # Ajustes de grid
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_columnconfigure(2, weight=1)

    # -------------------------
    # Persistencia
    # -------------------------
    def _cargar_datos_desde_archivo(self):
        if not os.path.exists(BASE_DIR):
            try:
                os.makedirs(BASE_DIR)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear la carpeta de datos:\n{e}")
                return

        if not os.path.exists(DB_FILE):
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            self.ventas = []
            self.next_id = 1
            return

        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                self.ventas = json.load(f)
            ids = [v.get("id", 0) for v in self.ventas]
            self.next_id = max(ids, default=0) + 1
            self._refrescar_treeview()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer la base de datos:\n{e}")
            self.ventas = []

    def _guardar_a_archivo(self):
        try:
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(self.ventas, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la base de datos:\n{e}")

    # -------------------------
    # Operaciones sobre UI y datos
    # -------------------------
    def _validar_campos(self):
        cliente = self.entries["Cliente"].get().strip()
        producto = self.entries["Producto"].get().strip()
        cantidad = self.entries["Cantidad"].get().strip()
        precio = self.entries["Precio"].get().strip()

        if not cliente:
            messagebox.showwarning("Validación", "El campo Cliente es obligatorio.")
            return False
        if not producto:
            messagebox.showwarning("Validación", "El campo Producto es obligatorio.")
            return False
        try:
            c = float(cantidad)
            if c <= 0:
                raise ValueError()
        except Exception:
            messagebox.showwarning("Validación", "Cantidad debe ser un número mayor que 0.")
            return False
        try:
            p = float(precio)
            if p < 0:
                raise ValueError()
        except Exception:
            messagebox.showwarning("Validación", "Precio debe ser un número válido (>= 0).")
            return False
        return True

    def _calcular_total(self, cantidad, precio):
        try:
            return round(float(cantidad) * float(precio))
        except Exception:
            return 0

    def _actualizar_total_display(self):
        cantidad = self.entries["Cantidad"].get().strip() or "0"
        precio = self.entries["Precio"].get().strip() or "0"
        total = self._calcular_total(cantidad, precio)
        self.total_var.set(format_currency(total))

    def _guardar_venta(self):
        if not self._validar_campos():
            return

        cliente = self.entries["Cliente"].get().strip()
        producto = self.entries["Producto"].get().strip()
        cantidad = float(self.entries["Cantidad"].get().strip())
        precio = float(self.entries["Precio"].get().strip())
        total = int(round(cantidad * precio))

        datos = {
            "Cliente": cliente,
            "Producto": producto,
            "Cantidad": cantidad,
            "Precio": precio,
            "Total": total
        }

        if self.edit_id is None:
            nuevo = {"id": self.next_id, **datos, "created_at": datetime.now().isoformat()}
            self.ventas.append(nuevo)
            self.next_id += 1
            messagebox.showinfo("Venta guardada", "Venta creada correctamente.")
        else:
            for v in self.ventas:
                if v.get("id") == self.edit_id:
                    v.update(datos)
                    v["updated_at"] = datetime.now().isoformat()
                    break
            messagebox.showinfo("Venta actualizada", "Los cambios se guardaron correctamente.")
            self.edit_id = None

        self._guardar_a_archivo()
        self._refrescar_treeview()
        self._limpiar_formulario()

    def _limpiar_formulario(self):
        for k in self.entries:
            self.entries[k].delete(0, tk.END)
        self.total_var.set(format_currency(0))
        self.edit_id = None
        for sel in self.tree.selection():
            self.tree.selection_remove(sel)

    def _nuevo(self):
        self._limpiar_formulario()
        self.entries["Cliente"].focus_set()

    def _refrescar_treeview(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for v in self.ventas:
            iid = str(v.get("id"))
            cantidad = v.get("Cantidad", 0)
            precio = v.get("Precio", 0)
            total = v.get("Total", 0)
            self.tree.insert("", "end", iid=iid,
                             values=(v.get("Cliente", ""), v.get("Producto", ""), f"{cantidad}", format_currency(precio), format_currency(total)))

    def _cargar_seleccion_para_editar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una venta en la lista para modificar.")
            return
        iid = sel[0]
        try:
            vid = int(iid)
        except Exception:
            messagebox.showerror("Error", "ID de venta inválido.")
            return

        venta = next((v for v in self.ventas if v.get("id") == vid), None)
        if venta is None:
            messagebox.showerror("Error", "Venta no encontrada en la base de datos.")
            return

        # cargar en formulario
        self.entries["Cliente"].delete(0, tk.END); self.entries["Cliente"].insert(0, venta.get("Cliente", ""))
        self.entries["Producto"].delete(0, tk.END); self.entries["Producto"].insert(0, venta.get("Producto", ""))
        self.entries["Cantidad"].delete(0, tk.END); self.entries["Cantidad"].insert(0, str(venta.get("Cantidad", "")))
        self.entries["Precio"].delete(0, tk.END); self.entries["Precio"].insert(0, str(venta.get("Precio", "")))
        self.total_var.set(format_currency(venta.get("Total", 0)))
        self.edit_id = vid

    def _eliminar_venta(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una venta para eliminar.")
            return
        iid = sel[0]
        try:
            vid = int(iid)
        except Exception:
            messagebox.showerror("Error", "ID de venta inválido.")
            return

        if not messagebox.askyesno("Confirmar", "¿Desea eliminar la venta seleccionada? Esta acción no se puede deshacer."):
            return

        self.ventas = [v for v in self.ventas if v.get("id") != vid]
        self._guardar_a_archivo()
        self._refrescar_treeview()
        self._limpiar_formulario()
        messagebox.showinfo("Eliminado", "Venta eliminada correctamente.")

    def _exportar_excel(self):
        if not self.ventas:
            messagebox.showwarning("Atención", "No hay ventas para exportar.")
            return

        carpeta = os.path.dirname(EXPORT_FILE)
        if carpeta and not os.path.exists(carpeta):
            try:
                os.makedirs(carpeta)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear la carpeta de exportación:\n{e}")
                return

        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Ventas"

            encabezados = ["ID", "Cliente", "Producto", "Cantidad", "Precio", "Total", "Creado", "Actualizado"]
            ws.append(encabezados)

            for v in self.ventas:
                ws.append([
                    v.get("id"),
                    v.get("Cliente", ""),
                    v.get("Producto", ""),
                    v.get("Cantidad", 0),
                    v.get("Precio", 0),
                    v.get("Total", 0),
                    v.get("created_at", ""),
                    v.get("updated_at", "")
                ])

            wb.save(EXPORT_FILE)
            messagebox.showinfo("Exportado", f"Ventas exportadas correctamente a:\n{EXPORT_FILE}")
        except Exception as e:
            messagebox.showerror("Error al exportar", f"No se pudo crear el Excel.\nDetalle:\n{e}")

    # -------------------------
    # Redimensionamiento y fondo
    # -------------------------
    def _on_canvas_configure(self, event):
        w, h = event.width, event.height
        if self.bg_orig is not None and self.bg_id is not None:
            try:
                resized = self.bg_orig.resize((max(1, w), max(1, h)), Image.Resampling.LANCZOS)
                self.bg_image = ImageTk.PhotoImage(resized)
                self.canvas.itemconfig(self.bg_id, image=self.bg_image)
            except Exception:
                pass

        new_w = min(1000, max(480, w - 60))
        new_h = min(720, max(320, h - 80))
        try:
            self.canvas.coords(self.window_id, w // 2, h // 2)
            self.canvas.itemconfig(self.window_id, width=new_w, height=new_h)
        except Exception:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = VentasTaller(root)
    root.mainloop()