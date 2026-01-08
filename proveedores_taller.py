import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import json
from datetime import datetime
import openpyxl

# Ruta de persistencia y exportación
BASE_DIR = r"C:\RICHARD\RB\2025\Taller_mecánica"
DB_FILE = os.path.join(BASE_DIR, "proveedores.json")
EXPORT_FILE = os.path.join(BASE_DIR, "proveedores_taller.xlsx")
FONDO_PATH = os.path.join(BASE_DIR, "panel_de_inicio_fondo.png")  # conserva la ruta que usabas

class ProveedoresTaller:
    def __init__(self, root):
        self.root = root
        self.root.title("🛠 Registro de Proveedores - Taller Mecánico")
        self.root.geometry("900x520")
        self.root.minsize(700, 480)
        self.root.resizable(True, True)

        # Datos en memoria
        self.proveedores = []
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
                        font=("Segoe UI Semibold", 12),
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

        titulo = tk.Label(self.content_frame, text="🛠 Registro de Proveedores",
                          font=("Segoe UI Semibold", 18),
                          bg="#ffffff", fg="#111827")
        titulo.grid(row=0, column=0, columnspan=3, pady=(8, 14))

        etiquetas = ["Nombre", "Teléfono", "Correo", "Empresa"]
        self.entries = {}

        for i, etiqueta in enumerate(etiquetas, start=1):
            lbl = tk.Label(self.content_frame, text=f"{etiqueta}:",
                           font=("Segoe UI", 11),
                           bg="#ffffff", fg="#111827", anchor="e")
            lbl.grid(row=i, column=0, sticky="e", padx=(16, 8), pady=6)

            entry = ttk.Entry(self.content_frame, width=36, style="Form.TEntry")
            entry.grid(row=i, column=1, sticky="w", padx=(8, 12), pady=6)
            self.entries[etiqueta] = entry

        # Botones acción
        btn_guardar = ttk.Button(self.content_frame, text="💾 Guardar", style="Menu.TButton",
                                 command=self._guardar_proveedor)
        btn_guardar.grid(row=6, column=0, padx=12, pady=(12, 6), sticky="e")

        btn_limpiar = ttk.Button(self.content_frame, text="🧹 Limpiar", style="Menu.TButton",
                                 command=self._limpiar_formulario)
        btn_limpiar.grid(row=6, column=1, padx=12, pady=(12, 6), sticky="w")

        # -------------------------
        # Panel derecho: listado
        # -------------------------
        listado_frame = tk.Frame(self.content_frame, bg="#ffffff", bd=0)
        listado_frame.grid(row=1, column=2, rowspan=6, padx=(6, 16), pady=6, sticky="nsew")

        lbl_list = tk.Label(listado_frame, text="Proveedores registrados",
                            font=("Segoe UI Semibold", 12),
                            bg="#ffffff", fg="#111827")
        lbl_list.pack(anchor="w", pady=(0, 6))

        cols = ("Nombre", "Teléfono", "Correo", "Empresa")
        self.tree = ttk.Treeview(listado_frame, columns=cols, show="headings", height=14)
        for c in cols:
            self.tree.heading(c, text=c)
            if c == "Nombre":
                self.tree.column(c, width=180)
            else:
                self.tree.column(c, width=120)

        scrollbar = ttk.Scrollbar(listado_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y", padx=(0,4))
        self.tree.pack(fill="both", expand=True)

        # Bindings
        self.tree.bind("<Double-1>", lambda e: self._cargar_seleccion_para_editar())

        # Botones CRUD para lista
        buttons_row = tk.Frame(listado_frame, bg="#ffffff")
        buttons_row.pack(fill="x", pady=(8, 0))

        btn_nuevo = ttk.Button(buttons_row, text="🆕 Nuevo", style="Menu.TButton", command=self._nuevo)
        btn_nuevo.pack(side="left", padx=4)

        btn_modificar = ttk.Button(buttons_row, text="✏️ Modificar", style="Menu.TButton",
                                   command=self._cargar_seleccion_para_editar)
        btn_modificar.pack(side="left", padx=4)

        btn_eliminar = ttk.Button(buttons_row, text="🗑️ Eliminar", style="Menu.TButton",
                                  command=self._eliminar_proveedor)
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
            self.proveedores = []
            self.next_id = 1
            return

        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                self.proveedores = json.load(f)
            ids = [p.get("id", 0) for p in self.proveedores]
            self.next_id = max(ids, default=0) + 1
            self._refrescar_treeview()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer la base de datos:\n{e}")
            self.proveedores = []

    def _guardar_a_archivo(self):
        try:
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(self.proveedores, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la base de datos:\n{e}")

    # -------------------------
    # Operaciones sobre UI y datos
    # -------------------------
    def _validar_campos(self):
        nombre = self.entries["Nombre"].get().strip()
        telefono = self.entries["Teléfono"].get().strip()
        if not nombre:
            messagebox.showwarning("Validación", "El campo Nombre es obligatorio.")
            return False
        if not telefono:
            messagebox.showwarning("Validación", "El campo Teléfono es obligatorio.")
            return False
        return True

    def _guardar_proveedor(self):
        if not self._validar_campos():
            return

        datos = {
            "Nombre": self.entries["Nombre"].get().strip(),
            "Teléfono": self.entries["Teléfono"].get().strip(),
            "Correo": self.entries["Correo"].get().strip(),
            "Empresa": self.entries["Empresa"].get().strip(),
        }

        if self.edit_id is None:
            nuevo = {"id": self.next_id, **datos, "created_at": datetime.now().isoformat()}
            self.proveedores.append(nuevo)
            self.next_id += 1
            messagebox.showinfo("Proveedor guardado", "Proveedor creado correctamente.")
        else:
            for p in self.proveedores:
                if p.get("id") == self.edit_id:
                    p.update(datos)
                    p["updated_at"] = datetime.now().isoformat()
                    break
            messagebox.showinfo("Proveedor actualizado", "Los cambios se guardaron correctamente.")
            self.edit_id = None

        self._guardar_a_archivo()
        self._refrescar_treeview()
        self._limpiar_formulario()

    def _limpiar_formulario(self):
        for k in self.entries:
            self.entries[k].delete(0, tk.END)
        self.edit_id = None
        for sel in self.tree.selection():
            self.tree.selection_remove(sel)

    def _nuevo(self):
        self._limpiar_formulario()
        self.entries["Nombre"].focus_set()

    def _refrescar_treeview(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for p in self.proveedores:
            iid = str(p.get("id"))
            self.tree.insert("", "end", iid=iid,
                             values=(p.get("Nombre", ""), p.get("Teléfono", ""), p.get("Correo", ""), p.get("Empresa", "")))

    def _cargar_seleccion_para_editar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un proveedor en la lista para modificar.")
            return
        iid = sel[0]
        try:
            pid = int(iid)
        except Exception:
            messagebox.showerror("Error", "ID de proveedor inválido.")
            return

        proveedor = next((p for p in self.proveedores if p.get("id") == pid), None)
        if proveedor is None:
            messagebox.showerror("Error", "Proveedor no encontrado en la base de datos.")
            return

        # cargar en formulario
        self.entries["Nombre"].delete(0, tk.END); self.entries["Nombre"].insert(0, proveedor.get("Nombre", ""))
        self.entries["Teléfono"].delete(0, tk.END); self.entries["Teléfono"].insert(0, proveedor.get("Teléfono", ""))
        self.entries["Correo"].delete(0, tk.END); self.entries["Correo"].insert(0, proveedor.get("Correo", ""))
        self.entries["Empresa"].delete(0, tk.END); self.entries["Empresa"].insert(0, proveedor.get("Empresa", ""))

        self.edit_id = pid

    def _eliminar_proveedor(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un proveedor para eliminar.")
            return
        iid = sel[0]
        try:
            pid = int(iid)
        except Exception:
            messagebox.showerror("Error", "ID de proveedor inválido.")
            return

        if not messagebox.askyesno("Confirmar", "¿Desea eliminar el proveedor seleccionado? Esta acción no se puede deshacer."):
            return

        self.proveedores = [p for p in self.proveedores if p.get("id") != pid]
        self._guardar_a_archivo()
        self._refrescar_treeview()
        self._limpiar_formulario()
        messagebox.showinfo("Eliminado", "Proveedor eliminado correctamente.")

    def _exportar_excel(self):
        if not self.proveedores:
            messagebox.showwarning("Atención", "No hay proveedores para exportar.")
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
            ws.title = "Proveedores"

            encabezados = ["ID", "Nombre", "Teléfono", "Correo", "Empresa", "Creado", "Actualizado"]
            ws.append(encabezados)

            for p in self.proveedores:
                ws.append([
                    p.get("id"),
                    p.get("Nombre", ""),
                    p.get("Teléfono", ""),
                    p.get("Correo", ""),
                    p.get("Empresa", ""),
                    p.get("created_at", ""),
                    p.get("updated_at", ""),
                ])

            wb.save(EXPORT_FILE)
            messagebox.showinfo("Exportado", f"Proveedores exportados correctamente a:\n{EXPORT_FILE}")
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
    app = ProveedoresTaller(root)
    root.mainloop()