import tkinter as tk
from tkinter import ttk, messagebox
import json, os
from datetime import datetime

# Ruta exacta del archivo de licencias
LICENSE_FILE = r"C:\RICHARD\RB\2025\Taller_mecánica\licencias.json"

def cargar_licencias():
    if not os.path.exists(LICENSE_FILE):
        return []
    try:
        with open(LICENSE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def validar_licencia(usuario, clave):
    licencias = cargar_licencias()
    if not licencias:
        return False, "⚠️ No se encontró ninguna licencia registrada."

    for lic in licencias:
        # Comparación de usuario sin importar mayúsculas/minúsculas
        if lic["usuario"].lower() == usuario.lower() and lic["clave"] == clave:
            try:
                expira = datetime.strptime(lic["expira"], "%Y-%m-%d")
            except:
                return False, "⚠️ Formato de fecha inválido en la licencia."
            if datetime.now() > expira:
                return False, "⚠️ La licencia ha expirado."
            return True, "✅ Licencia válida."
    return False, "⚠️ Usuario o clave incorrectos."

class LicenciaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🔑 Validación de Licencia")
        self.root.geometry("400x250")
        self.root.configure(bg="#0f172a")

        frame = tk.Frame(root, bg="#1e293b")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(frame, text="Usuario:", fg="#e2e8f0", bg="#1e293b").pack(pady=6)
        self.var_usuario = tk.StringVar()
        ttk.Entry(frame, textvariable=self.var_usuario).pack()

        tk.Label(frame, text="Clave:", fg="#e2e8f0", bg="#1e293b").pack(pady=6)
        self.var_clave = tk.StringVar()
        ttk.Entry(frame, textvariable=self.var_clave, show="*").pack()

        ttk.Button(frame, text="Validar", command=self.validar).pack(pady=12)

    def validar(self):
        usuario = self.var_usuario.get().strip()
        clave = self.var_clave.get().strip()
        ok, msg = validar_licencia(usuario, clave)
        if ok:
            messagebox.showinfo("Licencia", msg)
            self.root.destroy()
            # Aquí lanzas tu módulo principal (ejemplo: facturación)
            import facturacion
            facturacion.main()
        else:
            messagebox.showerror("Licencia", msg)

# ---------------------------
# Lanzamiento
# ---------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = LicenciaApp(root)
    root.mainloop()
