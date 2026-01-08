# -*- coding: utf-8 -*-
"""
Analizador y visualizador unificado para módulos del Taller Mecánico
(conservando colores y estilo de los otros módulos).

Lee los JSON generados por los módulos:
 - clientes.json
 - proveedores.json
 - ventas.json
 - inventario.json
 - ordenes_taller.json

Ubicación por defecto: C:\RICHARD\RB\2025\Taller_mecánica

Requisitos:
 - pandas
 - matplotlib
 - pillow
 - openpyxl (opcional si exportas desde pandas a Excel)

Instalación rápida:
    pip install pandas matplotlib pillow openpyxl
"""

import os
import json
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Visualización
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Data
import pandas as pd

from PIL import Image, ImageTk

BASE_DIR = r"C:\RICHARD\RB\2025\Taller_mecánica"
FONDO_PATH = os.path.join(BASE_DIR, "panel_de_inicio_fondo.png")

FILES = {
    "clientes": os.path.join(BASE_DIR, "clientes.json"),
    "proveedores": os.path.join(BASE_DIR, "proveedores.json"),
    "ventas": os.path.join(BASE_DIR, "ventas.json"),
    "inventario": os.path.join(BASE_DIR, "inventario.json"),
    "ordenes": os.path.join(BASE_DIR, "ordenes_taller.json"),
}


def safe_load_json(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error leyendo {path}: {e}")
        return []


def df_from_json(path):
    arr = safe_load_json(path)
    if not arr:
        return pd.DataFrame()
    # Ensure it's a list of dicts
    if isinstance(arr, dict):
        arr = list(arr.values())
    return pd.json_normalize(arr)


class AnalisisTallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Análisis Taller Mecánico")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)
        self.root.resizable(True, True)

        # Style: conservar colores y estilo de los otros módulos
        self._configurar_estilos()

        # Fondo (imagen escalable) y canvas
        self.bg_orig = None
        self._cargar_fondo()

        # Contenido centrado (content_frame) insertado en canvas
        self.content_frame = tk.Frame(self.root, bg="#ffffff")
        self.window_id = self.canvas.create_window( self.canvas.winfo_reqwidth()//2,
                                                    self.canvas.winfo_reqheight()//2,
                                                    window=self.content_frame,
                                                    width=1000, height=640)

        # Construir la UI dentro del content_frame (mismo look que los otros módulos)
        self._build_ui()

        # Cargar datos
        self._load_dataframes()

        # Ajustar cuando el canvas cambie de tamaño (re-dibuja fondo y reubica content_frame)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Botón de menú / acción (mismo color naranja que en módulos anteriores)
        style.configure("Menu.TButton",
                        background="#f59e0b",
                        foreground="#111827",
                        font=("Segoe UI Semibold", 11),
                        padding=6,
                        relief="flat",
                        borderwidth=0)
        style.map("Menu.TButton", background=[("active", "#fbbf24")])

        # Entradas de formulario
        style.configure("Form.TEntry",
                        fieldbackground="#ffffff",
                        foreground="#111827",
                        padding=4)

        # Treeview estilo similar
        style.configure("Treeview",
                        background="#ffffff",
                        foreground="#111827",
                        rowheight=22)
        style.configure("Treeview.Heading", font=("Segoe UI Semibold", 10))

        # Etiquetas generales (usar colores oscuros para texto sobre contenido blanco)
        style.configure("TLabel", background="#ffffff", foreground="#111827")

    def _cargar_fondo(self):
        # intenta cargar fondo; si falla, canvas con color neutro
        try:
            fondo = Image.open(FONDO_PATH)
            self.bg_orig = fondo.convert("RGBA")
            self.canvas = tk.Canvas(self.root, width=1100, height=700, highlightthickness=0)
            self.canvas.pack(fill="both", expand=True)
            inicial = self.bg_orig.resize((1100, 700), Image.Resampling.LANCZOS)
            self.bg_image = ImageTk.PhotoImage(inicial)
            self.bg_id = self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")
        except Exception:
            self.canvas = tk.Canvas(self.root, width=1100, height=700, highlightthickness=0, bg="#0f172a")
            self.canvas.pack(fill="both", expand=True)
            self.bg_id = None

    def _build_ui(self):
        # título
        titulo = tk.Label(self.content_frame, text="Analizador del Taller Mecánico",
                          font=("Segoe UI Semibold", 16),
                          bg="#ffffff", fg="#111827")
        titulo.pack(pady=(10,6))

        # Top control frame
        top = tk.Frame(self.content_frame, bg="#ffffff")
        top.pack(fill="x", padx=10, pady=(0,6))

        ttk.Button(top, text="Recargar datos", style="Menu.TButton", command=self._load_dataframes).pack(side="left", padx=4)
        ttk.Button(top, text="Exportar tabla seleccionada (CSV)", style="Menu.TButton", command=self._export_selected_table).pack(side="left", padx=4)

        # Notebook para pestañas (datos / gráficas)
        self.nb = ttk.Notebook(self.content_frame)
        self.nb.pack(fill="both", expand=True, padx=10, pady=8)

        # Pestaña Datos
        self.tab_data = tk.Frame(self.nb, bg="#ffffff")
        self.nb.add(self.tab_data, text="Datos")
        self._build_data_tab()

        # Pestaña Gráficas
        self.tab_charts = tk.Frame(self.nb, bg="#ffffff")
        self.nb.add(self.tab_charts, text="Gráficas")
        self._build_charts_tab()

    def _build_data_tab(self):
        left = tk.Frame(self.tab_data, bg="#ffffff")
        left.pack(side="left", fill="y", padx=8, pady=8)

        ttk.Label(left, text="Dataset:", background="#ffffff").pack(anchor="nw")
        self.data_list = tk.Listbox(left, height=6)
        for k in FILES.keys():
            self.data_list.insert(tk.END, k)
        self.data_list.pack(fill="y", pady=6)
        self.data_list.bind("<<ListboxSelect>>", lambda e: self._show_selected_table())

        ttk.Button(left, text="Refrescar tabla", style="Menu.TButton", command=self._show_selected_table).pack(pady=(6, 0))
        ttk.Button(left, text="Guardar tabla (Excel)", style="Menu.TButton", command=self._export_selected_table_excel).pack(pady=(6, 0))

        # Right: treeview para vista previa de tabla
        right = tk.Frame(self.tab_data, bg="#ffffff")
        right.pack(side="right", fill="both", expand=True, padx=8, pady=8)

        self.table_tree = ttk.Treeview(right)
        # scrollbars
        vsb = ttk.Scrollbar(right, orient="vertical", command=self.table_tree.yview)
        hsb = ttk.Scrollbar(right, orient="horizontal", command=self.table_tree.xview)
        self.table_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.table_tree.pack(fill="both", expand=True)

        # estado
        self.data_status = ttk.Label(self.tab_data, text="", background="#ffffff")
        self.data_status.pack(side="bottom", anchor="w", padx=8, pady=4)

    def _build_charts_tab(self):
        control = tk.Frame(self.tab_charts, bg="#ffffff")
        control.pack(side="top", fill="x", padx=8, pady=8)

        ttk.Label(control, text="Dataset:", background="#ffffff").grid(row=0, column=0, sticky="w")
        self.chart_dataset = ttk.Combobox(control, values=list(FILES.keys()), state="readonly", width=18)
        # default ventas if exists
        try:
            self.chart_dataset.current(list(FILES.keys()).index("ventas"))
        except Exception:
            self.chart_dataset.current(0)
        self.chart_dataset.grid(row=0, column=1, padx=6)

        ttk.Label(control, text="Tipo gráfica:", background="#ffffff").grid(row=0, column=2, sticky="w", padx=(12, 0))
        self.chart_type = ttk.Combobox(control, values=[
            "Ventas - tiempo (diario)",
            "Ventas - tiempo (mensual)",
            "Top productos (cantidad)",
            "Top productos (total)",
            "Valor inventario por producto",
            "Clientes vs Proveedores (conteo)",
            "Ingresos por servicio (ordenes_taller)"
        ], state="readonly", width=30)
        self.chart_type.current(0)
        self.chart_type.grid(row=0, column=3, padx=6)

        ttk.Label(control, text="Desde (YYYY-MM-DD):", background="#ffffff").grid(row=1, column=0, sticky="w", pady=(6,0))
        self.date_from = ttk.Entry(control, width=12, style="Form.TEntry")
        self.date_from.grid(row=1, column=1, sticky="w", pady=(6,0), padx=6)

        ttk.Label(control, text="Hasta (YYYY-MM-DD):", background="#ffffff").grid(row=1, column=2, sticky="w", pady=(6,0))
        self.date_to = ttk.Entry(control, width=12, style="Form.TEntry")
        self.date_to.grid(row=1, column=3, sticky="w", pady=(6,0), padx=6)

        ttk.Button(control, text="Generar gráfica", style="Menu.TButton", command=self._on_generate_chart).grid(row=0, column=4, rowspan=2, padx=12)
        ttk.Button(control, text="Guardar gráfica", style="Menu.TButton", command=self._save_current_plot).grid(row=0, column=5, rowspan=2, padx=6)

        # Área de figura (matplotlib)
        self.figure = Figure(figsize=(9,5), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas_fig = FigureCanvasTkAgg(self.figure, master=self.tab_charts)
        self.canvas_fig.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    def _load_dataframes(self):
        # Load all datasets into pandas DataFrames
        self.dfs = {}
        for name, path in FILES.items():
            df = df_from_json(path)
            # Normalizaciones específicas
            if name == "ventas" and not df.empty:
                if "fecha" in df.columns:
                    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
                elif "created_at" in df.columns:
                    df["fecha"] = pd.to_datetime(df["created_at"], errors="coerce")
                # numeric conversions
                for col in ["Cantidad", "cantidad"]:
                    if col in df.columns:
                        df["Cantidad"] = pd.to_numeric(df[col], errors="coerce")
                        break
                for col in ["Precio", "precio", "Precio Unitario"]:
                    if col in df.columns:
                        df["Precio"] = pd.to_numeric(df[col], errors="coerce")
                        break
                if "Total" not in df.columns:
                    if "Cantidad" in df.columns and "Precio" in df.columns:
                        df["Total"] = (df["Cantidad"].astype(float) * df["Precio"].astype(float)).round().astype("Int64")
            if name == "inventario" and not df.empty:
                for col in ["Cantidad", "cantidad"]:
                    if col in df.columns:
                        df["Cantidad"] = pd.to_numeric(df[col], errors="coerce")
                        break
                for col in ["Precio Unitario", "Precio", "precio"]:
                    if col in df.columns:
                        df["Precio Unitario"] = pd.to_numeric(df[col], errors="coerce")
                        break
                if "Valor Total" not in df.columns and "Cantidad" in df.columns and "Precio Unitario" in df.columns:
                    df["Valor Total"] = (df["Cantidad"].astype(float) * df["Precio Unitario"].astype(float)).round().astype("Int64")
            if name == "ordenes" and not df.empty:
                if "fecha" in df.columns:
                    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
                elif "created_at" in df.columns:
                    df["fecha"] = pd.to_datetime(df["created_at"], errors="coerce")
                for col in ["total", "Total", "total_final"]:
                    if col in df.columns:
                        df["total"] = pd.to_numeric(df[col], errors="coerce")
                        break
                if "servicio" not in df.columns:
                    for c in df.columns:
                        if "servicio" in c.lower() or "service" in c.lower():
                            df = df.rename(columns={c: "servicio"})
                            break
            self.dfs[name] = df

        # Update UI preview and status
        self._show_selected_table()
        self.data_status.config(text=", ".join([f"{k}: {len(df)}" for k, df in self.dfs.items()]))
        messagebox.showinfo("Datos recargados", "Los datos se han recargado desde los archivos JSON (si existen).")

    def _show_selected_table(self):
        sel = self.data_list.curselection()
        if not sel:
            return
        name = self.data_list.get(sel[0])
        df = self.dfs.get(name, pd.DataFrame())

        # Clear tree
        for c in self.table_tree.get_children():
            self.table_tree.delete(c)
        cols = list(df.columns) if not df.empty else ["(vacío)"]
        self.table_tree["columns"] = cols
        self.table_tree["show"] = "headings"
        for col in cols:
            self.table_tree.heading(col, text=col)
            self.table_tree.column(col, width=140, anchor="w")

        if df.empty:
            return

        max_rows = 200
        for i, row in df.head(max_rows).iterrows():
            vals = []
            for col in df.columns:
                v = row[col]
                if pd.isna(v):
                    vals.append("")
                else:
                    if isinstance(v, (pd.Timestamp, datetime)):
                        vals.append(str(v))
                    else:
                        vals.append(str(v))
            try:
                self.table_tree.insert("", "end", values=vals)
            except Exception:
                pass

    def _apply_date_filter(self, df, date_col_name="fecha"):
        if df.empty:
            return df
        dfrom = self.date_from.get().strip()
        dto = self.date_to.get().strip()
        if not dfrom and not dto:
            return df
        local_df = df.copy()
        if date_col_name not in local_df.columns:
            for c in local_df.columns:
                if "fecha" in c.lower() or "date" in c.lower() or "created_at" in c.lower():
                    local_df[c] = pd.to_datetime(local_df[c], errors="coerce")
                    date_col_name = c
                    break
        if date_col_name not in local_df.columns:
            return df
        try:
            if dfrom:
                d0 = pd.to_datetime(dfrom)
                local_df = local_df[local_df[date_col_name] >= d0]
            if dto:
                d1 = pd.to_datetime(dto)
                local_df = local_df[local_df[date_col_name] <= d1]
        except Exception:
            pass
        return local_df

    def _on_generate_chart(self):
        typ = self.chart_type.get()
        dataset = self.chart_dataset.get()
        df = self.dfs.get(dataset, pd.DataFrame()).copy()

        # Clear axis
        self.ax.clear()

        try:
            if typ.startswith("Ventas - tiempo"):
                if df.empty and dataset != "ventas":
                    messagebox.showwarning("Sin datos", "No hay datos de ventas en el dataset seleccionado.")
                    return
                if dataset != "ventas":
                    df = self.dfs.get("ventas", pd.DataFrame()).copy()
                if df.empty:
                    messagebox.showwarning("Sin datos", "No hay registros de ventas.")
                    return
                if "fecha" not in df.columns:
                    df["fecha"] = pd.to_datetime(df.get("created_at", None), errors="coerce")
                df = df.dropna(subset=["fecha"])
                df = self._apply_date_filter(df, "fecha")
                if df.empty:
                    messagebox.showinfo("Sin resultados", "No hay ventas en el rango seleccionado.")
                    return
                if "diario" in typ.lower():
                    df["day"] = df["fecha"].dt.date
                    agg = df.groupby("day")["Total"].sum().reset_index()
                    x = pd.to_datetime(agg["day"])
                    y = agg["Total"]
                    self.ax.plot(x, y, marker="o")
                    self.ax.set_title("Ventas - total diario")
                    self.ax.set_xlabel("Fecha")
                    self.ax.set_ylabel("Total")
                else:
                    df["month"] = df["fecha"].dt.to_period("M").dt.to_timestamp()
                    agg = df.groupby("month")["Total"].sum().reset_index()
                    x = pd.to_datetime(agg["month"])
                    y = agg["Total"]
                    self.ax.bar(x, y, width=20)
                    self.ax.set_title("Ventas - total mensual")
                    self.ax.set_xlabel("Mes")
                    self.ax.set_ylabel("Total")
                self.ax.grid(True)

            elif typ == "Top productos (cantidad)" or typ == "Top productos (total)":
                vdf = self.dfs.get("ventas", pd.DataFrame()).copy()
                if vdf.empty:
                    messagebox.showwarning("Sin datos", "No hay datos de ventas para calcular top productos.")
                    return
                vdf = self._apply_date_filter(vdf, "fecha")
                if vdf.empty:
                    messagebox.showinfo("Sin resultados", "No hay ventas en el rango seleccionado.")
                    return
                prod_col = None
                for c in ["Producto", "producto", "product"]:
                    if c in vdf.columns:
                        prod_col = c
                        break
                if prod_col is None:
                    messagebox.showerror("Sin columna Producto", "No se encontró columna de producto en ventas.")
                    return
                if typ.endswith("cantidad"):
                    if "Cantidad" not in vdf.columns:
                        for c in vdf.columns:
                            if "cant" in c.lower():
                                vdf["Cantidad"] = pd.to_numeric(vdf[c], errors="coerce")
                                break
                    agg = vdf.groupby(prod_col)["Cantidad"].sum().sort_values(ascending=False).head(15)
                    agg.plot(kind="bar", ax=self.ax)
                    self.ax.set_title("Top productos por cantidad (Top 15)")
                    self.ax.set_ylabel("Cantidad")
                else:
                    if "Total" not in vdf.columns:
                        if "Cantidad" in vdf.columns and "Precio" in vdf.columns:
                            vdf["Total"] = vdf["Cantidad"].astype(float) * vdf["Precio"].astype(float)
                    agg = vdf.groupby(prod_col)["Total"].sum().sort_values(ascending=False).head(15)
                    agg.plot(kind="bar", ax=self.ax, color="tab:orange")
                    self.ax.set_title("Top productos por ventas (Top 15)")
                    self.ax.set_ylabel("Total")

            elif typ == "Valor inventario por producto":
                inv = self.dfs.get("inventario", pd.DataFrame()).copy()
                if inv.empty:
                    messagebox.showwarning("Sin datos", "No hay datos de inventario.")
                    return
                prod_col = None
                for c in ["Producto", "producto", "name", "Código"]:
                    if c in inv.columns:
                        prod_col = c
                        break
                if prod_col is None:
                    prod_col = inv.columns[0]
                if "Valor Total" not in inv.columns:
                    if "Cantidad" in inv.columns and "Precio Unitario" in inv.columns:
                        inv["Valor Total"] = inv["Cantidad"].astype(float) * inv["Precio Unitario"].astype(float)
                    else:
                        messagebox.showerror("Datos insuficientes", "No se puede calcular Valor Total (falta Cantidad o Precio Unitario).")
                        return
                agg = inv.groupby(prod_col)["Valor Total"].sum().sort_values(ascending=False).head(20)
                agg.plot(kind="bar", ax=self.ax, color="tab:green")
                self.ax.set_title("Valor inventario por producto (Top 20)")
                self.ax.set_ylabel("Valor")

            elif typ == "Clientes vs Proveedores (conteo)":
                ccount = len(self.dfs.get("clientes", pd.DataFrame()))
                pcount = len(self.dfs.get("proveedores", pd.DataFrame()))
                self.ax.pie([ccount, pcount], labels=["Clientes", "Proveedores"], autopct="%1.0f%%", colors=["#4c78a8", "#f59e0b"])
                self.ax.set_title("Clientes vs Proveedores (conteo)")

            elif typ == "Ingresos por servicio (ordenes_taller)":
                odf = self.dfs.get("ordenes", pd.DataFrame()).copy()
                if odf.empty:
                    messagebox.showwarning("Sin datos", "No hay datos de órdenes (ordenes_taller.json).")
                    return
                odf = self._apply_date_filter(odf, "fecha")
                serv_col = None
                for c in odf.columns:
                    if "servicio" in c.lower() or "service" in c.lower():
                        serv_col = c
                        break
                if serv_col is None:
                    messagebox.showerror("Sin columna servicio", "No se encontró columna de servicio en órdenes.")
                    return
                total_col = None
                for c in ["total", "Total", "total"]:
                    if c in odf.columns:
                        total_col = c
                        break
                if total_col is None:
                    if "subtotal" in odf.columns and "iva" in odf.columns:
                        odf["total_calc"] = odf["subtotal"].astype(float) + odf["iva"].astype(float)
                        total_col = "total_calc"
                if total_col is None:
                    messagebox.showerror("Sin total", "No hay columna de total en órdenes.")
                    return
                agg = odf.groupby(serv_col)[total_col].sum().sort_values(ascending=False).head(20)
                agg.plot(kind="bar", ax=self.ax, color="tab:purple")
                self.ax.set_title("Ingresos por servicio (Top 20)")
                self.ax.set_ylabel("Ingresos")

            else:
                messagebox.showinfo("No implementado", "Tipo de gráfica no soportado aún.")
                return

            self.ax.tick_params(axis="x", rotation=25)
            self.figure.tight_layout()
            self.canvas_fig.draw()
        except Exception as e:
            messagebox.showerror("Error al generar gráfica", f"Ocurrió un error al generar la gráfica:\n{e}")

    def _save_current_plot(self):
        fname = filedialog.asksaveasfilename(defaultextension=".png",
                                             filetypes=[("PNG image", "*.png"), ("PDF", "*.pdf"), ("All files", "*.*")])
        if not fname:
            return
        try:
            self.figure.savefig(fname)
            messagebox.showinfo("Guardado", f"Gráfica guardada en:\n{fname}")
        except Exception as e:
            messagebox.showerror("Error al guardar", f"No se pudo guardar la gráfica:\n{e}")

    def _export_selected_table(self):
        sel = self.data_list.curselection()
        if not sel:
            messagebox.showwarning("Atención", "Selecciona primero un dataset en la pestaña Datos.")
            return
        name = self.data_list.get(sel[0])
        df = self.dfs.get(name, pd.DataFrame())
        if df.empty:
            messagebox.showwarning("Sin datos", "La tabla seleccionada está vacía.")
            return
        fname = filedialog.asksaveasfilename(defaultextension=".csv",
                                             filetypes=[("CSV", "*.csv"), ("All files", "*.*")])
        if not fname:
            return
        try:
            df.to_csv(fname, index=False, encoding="utf-8-sig")
            messagebox.showinfo("Exportado", f"Tabla exportada a CSV:\n{fname}")
        except Exception as e:
            messagebox.showerror("Error exportar", f"No se pudo exportar:\n{e}")

    def _export_selected_table_excel(self):
        sel = self.data_list.curselection()
        if not sel:
            messagebox.showwarning("Atención", "Selecciona primero un dataset en la pestaña Datos.")
            return
        name = self.data_list.get(sel[0])
        df = self.dfs.get(name, pd.DataFrame())
        if df.empty:
            messagebox.showwarning("Sin datos", "La tabla seleccionada está vacía.")
            return
        fname = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                             filetypes=[("Excel workbook", "*.xlsx"), ("All files", "*.*")])
        if not fname:
            return
        try:
            df.to_excel(fname, index=False)
            messagebox.showinfo("Exportado", f"Tabla exportada a Excel:\n{fname}")
        except Exception as e:
            messagebox.showerror("Error exportar", f"No se pudo exportar:\n{e}")

    # Ajuste del fondo y reposicionamiento del content_frame cuando cambia el canvas
    def _on_canvas_configure(self, event):
        w, h = event.width, event.height
        # actualizar fondo escalado si existe
        if self.bg_orig is not None and self.bg_id is not None:
            try:
                resized = self.bg_orig.resize((max(1, w), max(1, h)), Image.Resampling.LANCZOS)
                self.bg_image = ImageTk.PhotoImage(resized)
                self.canvas.itemconfig(self.bg_id, image=self.bg_image)
            except Exception:
                pass

        # ajustar tamaño del content_frame (ventana interna) manteniendo márgenes
        new_w = min(1060, max(720, w - 80))
        new_h = min(900, max(560, h - 80))
        try:
            self.canvas.coords(self.window_id, w // 2, h // 2)
            self.canvas.itemconfig(self.window_id, width=new_w, height=new_h)
        except Exception:
            pass


if __name__ == "__main__":
    root = tk.Tk()
    app = AnalisisTallerApp(root)
    root.mainloop()