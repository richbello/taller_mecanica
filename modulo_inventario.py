import tkinter as tk
from tkinter import ttk, messagebox
import json, os

DATA_FILE = "inventario.json"

def cargar_inventario():
    if not os.path.exists(DATA_FILE): return []
    try:
        with open(DATA_FILE,"r",encoding="utf-8") as f: return json.load(f)
    except: return []

def guardar_inventario(inventario):
    with open(DATA_FILE,"w",encoding="utf-8") as f: json.dump(inventario,f,ensure_ascii=False,indent=2)

class InventarioApp:
    def __init__(self,root):
        self.root=root
        self.root.title("Inventario de Repuestos - Taller Mecánico")
        self.root.geometry("1900x1500")
        self.root.configure(bg="#0f172a")

        self.inventario=cargar_inventario()
        self._configurar_estilos()
        self._construir_layout()

    def _configurar_estilos(self):
        style=ttk.Style(); style.theme_use("clam")
        self.color_bg="#0f172a"; self.color_panel="#1e293b"
        self.color_acento="#f59e0b"; self.color_ok="#22c55e"; self.color_texto="#e2e8f0"
        style.configure("TLabel",foreground=self.color_texto,background=self.color_panel)
        style.configure("Accent.TButton",background=self.color_acento,foreground="#111827")
        style.configure("Ok.TButton",background=self.color_ok,foreground="#0b1220")

    def _construir_layout(self):
        frame=tk.Frame(self.root,bg=self.color_panel); frame.pack(fill="both",expand=True,padx=150,pady=150)

        self.nombre_var=tk.StringVar(); self.cantidad_var=tk.IntVar(); self.precio_var=tk.IntVar()
        ttk.Label(frame,text="Repuesto:").grid(row=0,column=0,padx=6,pady=6); ttk.Entry(frame,textvariable=self.nombre_var).grid(row=0,column=1,padx=6,pady=6)
        ttk.Label(frame,text="Cantidad:").grid(row=1,column=0,padx=6,pady=6); ttk.Entry(frame,textvariable=self.cantidad_var).grid(row=1,column=1,padx=6,pady=6)
        ttk.Label(frame,text="Precio unitario:").grid(row=2,column=0,padx=6,pady=6); ttk.Entry(frame,textvariable=self.precio_var).grid(row=2,column=1,padx=6,pady=6)

        ttk.Button(frame,text="Agregar repuesto",style="Ok.TButton",command=self.guardar_repuesto).grid(row=3,column=0,padx=6,pady=6)
        ttk.Button(frame,text="Eliminar seleccionado",style="Accent.TButton",command=self.eliminar_repuesto).grid(row=3,column=1,padx=6,pady=6)

        self.tree=ttk.Treeview(frame,columns=("nombre","cantidad","precio"),show="headings")
        for c in ("nombre","cantidad","precio"): self.tree.heading(c,text=c.capitalize())
        self.tree.grid(row=4,column=0,columnspan=2,sticky="nsew",padx=6,pady=6)

        self.refrescar_tabla()

    def guardar_repuesto(self):
        data={"nombre":self.nombre_var.get(),"cantidad":self.cantidad_var.get(),"precio":self.precio_var.get()}
        if not data["nombre"]: messagebox.showwarning("Validación","El nombre es obligatorio"); return
        self.inventario.append(data); guardar_inventario(self.inventario); self.refrescar_tabla()
        messagebox.showinfo("Éxito","Repuesto agregado"); self.nombre_var.set(""); self.cantidad_var.set(0); self.precio_var.set(0)

    def eliminar_repuesto(self):
        sel=self.tree.selection()
        if not sel: return
        idx=self.tree.index(sel[0]); del self.inventario[idx]; guardar_inventario(self.inventario); self.refrescar_tabla()

    def refrescar_tabla(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in self.inventario:
            color="red" if r["cantidad"]<5 else "black"
            self.tree.insert("", "end", values=(r["nombre"],r["cantidad"],f"${r['precio']:,}"), tags=("low",))
            self.tree.tag_configure("low", foreground=color)

if __name__=="__main__":
    root=tk.Tk(); app=InventarioApp(root); root.mainloop()
