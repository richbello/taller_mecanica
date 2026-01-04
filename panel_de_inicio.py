import tkinter as tk
from tkinter import ttk
import subprocess, sys

class PanelInicio:
    def __init__(self,root):
        self.root=root
        self.root.title("Panel de Inicio - Taller Mecánico")
        self.root.geometry("600x400")
        self.root.configure(bg="#0f172a")

        self._configurar_estilos()
        self._construir_layout()

    def _configurar_estilos(self):
        style=ttk.Style(); style.theme_use("clam")
        self.color_bg="#0f172a"; self.color_panel="#1e293b"
        self.color_acento="#f59e0b"; self.color_ok="#22c55e"; self.color_texto="#e2e8f0"
        style.configure("Menu.TButton",background=self.color_acento,foreground="#111827",font=("Segoe UI Semibold",12))
        style.map("Menu.TButton",background=[("active","#fbbf24")])

    def _construir_layout(self):
        frame=tk.Frame(self.root,bg=self.color_panel); frame.pack(fill="both",expand=True,padx=12,pady=12)

        ttk.Button(frame,text="📋 Órdenes de Trabajo",style="Menu.TButton",command=lambda:self.abrir_modulo("ordenes_taller.py")).pack(fill="x",pady=10)
        ttk.Button(frame,text="💰 Ventas",style="Menu.TButton",command=lambda:self.abrir_modulo("ventas_taller.py")).pack(fill="x",pady=10)
        ttk.Button(frame,text="👥 Clientes",style="Menu.TButton",command=lambda:self.abrir_modulo("clientes_taller.py")).pack(fill="x",pady=10)
        ttk.Button(frame,text="🛠️ Proveedores",style="Menu.TButton",command=lambda:self.abrir_modulo("proveedores_taller.py")).pack(fill="x",pady=10)
        ttk.Button(frame,text="📦 Inventario",style="Menu.TButton",command=lambda:self.abrir_modulo("inventario_taller.py")).pack(fill="x",pady=10)

    def abrir_modulo(self,archivo):
        subprocess.Popen([sys.executable,archivo])

if __name__=="__main__":
    root=tk.Tk(); app=PanelInicio(root); root.mainloop()
