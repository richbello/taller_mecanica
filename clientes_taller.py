import tkinter as tk
from tkinter import ttk, messagebox
import json, os

DATA_FILE = "clientes.json"

def cargar_clientes():
    if not os.path.exists(DATA_FILE): return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return []

def guardar_clientes(clientes):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(clientes, f, ensure_ascii=False, indent=2)

class ClientesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Módulo de Clientes - Taller Mecánico")
        self.root.geometry("800x500")
        self.root.configure(bg="#0f172a")

        self.clientes = cargar_clientes()
        self._configurar_estilos()
        self._construir_layout()

    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")
        self.color_bg="#0f172a"; self.color_panel="#1e293b"
        self.color_acento="#f59e0b"; self.color_ok="#22c55e"; self.color_texto="#e2e8f0"
        style.configure("TLabel", foreground=self.color_texto, background=self.color_panel)
        style.configure("Accent.TButton", background=self.color_acento, foreground="#111827")
        style.configure("Ok.TButton", background=self.color_ok, foreground="#0b1220")

    def _construir_layout(self):
        frame = tk.Frame(self.root, bg=self.color_panel); frame.pack(fill="both", expand=True, padx=12, pady=12)

        self.nombre_var = tk.StringVar(); self.telefono_var = tk.StringVar(); self.email_var = tk.StringVar()
        ttk.Label(frame, text="Nombre:").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        ttk.Entry(frame, textvariable=self.nombre_var).grid(row=0, column=1, padx=6, pady=6)
        ttk.Label(frame, text="Teléfono:").grid(row=1, column=0, padx=6, pady=6, sticky="w")
        ttk.Entry(frame, textvariable=self.telefono_var).grid(row=1, column=1, padx=6, pady=6)
        ttk.Label(frame, text="Email:").grid(row=2, column=0, padx=6, pady=6, sticky="w")
        ttk.Entry(frame, textvariable=self.email_var).grid(row=2, column=1, padx=6, pady=6)

        ttk.Button(frame, text="Guardar cliente", style="Ok.TButton", command=self.guardar_cliente).grid(row=3, column=0, padx=6, pady=6)
        ttk.Button(frame, text="Eliminar seleccionado", style="Accent.TButton", command=self.eliminar_cliente).grid(row=3, column=1, padx=6, pady=6)

        self.tree = ttk.Treeview(frame, columns=("nombre","telefono","email"), show="headings")
        for c in ("nombre","telefono","email"): self.tree.heading(c, text=c.capitalize())
        self.tree.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=6, pady=6)
        self.refrescar_tabla()

    def guardar_cliente(self):
        data={"nombre":self.nombre_var.get(),"telefono":self.telefono_var.get(),"email":self.email_var.get()}
        if not data["nombre"]: messagebox.showwarning("Validación","El nombre es obligatorio"); return
        self.clientes.append(data); guardar_clientes(self.clientes); self.refrescar_tabla()
        messagebox.showinfo("Éxito","Cliente guardado"); self.nombre_var.set(""); self.telefono_var.set(""); self.email_var.set("")

    def eliminar_cliente(self):
        sel=self.tree.selection()
        if not sel: return
        idx=self.tree.index(sel[0]); del self.clientes[idx]; guardar_clientes(self.clientes); self.refrescar_tabla()

    def refrescar_tabla(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for c in self.clientes: self.tree.insert("", "end", values=(c["nombre"],c["telefono"],c["email"]))

if __name__=="__main__":
    root=tk.Tk(); app=ClientesApp(root); root.mainloop()
