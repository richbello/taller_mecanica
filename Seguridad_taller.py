import os
import json
from datetime import datetime
import base64
import secrets
import string

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from cryptography.fernet import Fernet
import pandas as pd
from openpyxl import Workbook

BASE_DIR = r"C:\RICHARD\RB\2025\Taller_mecánica"
KEY_FILE = os.path.join(BASE_DIR, "security.key")
CREDS_FILE = os.path.join(BASE_DIR, "creds.json.enc")
AUDIT_LOG = os.path.join(BASE_DIR, "security_audit.log")

# -----------------------
# Utilities: key / crypto
# -----------------------
def ensure_base_dir():
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR, exist_ok=True)

def generate_key():
    ensure_base_dir()
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    return key

def load_key():
    ensure_base_dir()
    if not os.path.exists(KEY_FILE):
        return generate_key()
    with open(KEY_FILE, "rb") as f:
        return f.read()

def encrypt_bytes(data_bytes):
    key = load_key()
    f = Fernet(key)
    return f.encrypt(data_bytes)

def decrypt_bytes(enc_bytes):
    key = load_key()
    f = Fernet(key)
    return f.decrypt(enc_bytes)

def audit(action, details=""):
    ensure_base_dir()
    ts = datetime.now().isoformat(sep=" ", timespec="seconds")
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(f"{ts} | {action} | {details}\n")

# -----------------------
# Password helpers
# -----------------------
def generate_password(length=16, symbols=True):
    alphabet = string.ascii_letters + string.digits
    if symbols:
        alphabet += "!@#$%^&*()-_=+[]{};:,.<>?"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def password_strength(pw: str):
    score = 0
    notes = []
    if len(pw) >= 12:
        score += 2
    elif len(pw) >= 8:
        score += 1
    else:
        notes.append("Muy corta (menos de 8 caracteres).")

    if any(c.islower() for c in pw) and any(c.isupper() for c in pw):
        score += 1
    else:
        notes.append("Usar mayúsculas y minúsculas.")

    if any(c.isdigit() for c in pw):
        score += 1
    else:
        notes.append("Agregar números.")

    if any(c in "!@#$%^&*()-_=+[]{};:,.<>?" for c in pw):
        score += 1
    else:
        notes.append("Agregar símbolos especiales.")

    strength = {0: "Muy débil", 1: "Débil", 2: "Moderada", 3: "Fuerte", 4: "Muy fuerte"}.get(score, "Débil")
    return score, strength, notes

# -----------------------
# Credential store (encrypted)
# -----------------------
def load_creds():
    ensure_base_dir()
    if not os.path.exists(CREDS_FILE):
        return []
    try:
        with open(CREDS_FILE, "rb") as f:
            enc = f.read()
        data = decrypt_bytes(enc)
        arr = json.loads(data.decode("utf-8"))
        return arr
    except Exception as e:
        # If decryption fails, return [] and log
        audit("load_creds_failed", str(e))
        return []

def save_creds(arr):
    ensure_base_dir()
    data = json.dumps(arr, ensure_ascii=False, indent=2).encode("utf-8")
    enc = encrypt_bytes(data)
    with open(CREDS_FILE, "wb") as f:
        f.write(enc)

# -----------------------
# GUI: Seguridad
# -----------------------
class SeguridadTaller:
    def __init__(self, root):
        self.root = root
        self.root.title("🔒 Seguridad - Taller Mecánico")
        self.root.geometry("900x600")
        self.root.minsize(780, 520)
        self.root.configure(bg="#0f172a")

        self._setup_styles()
        self._build_ui()
        self._load_list()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Menu.TButton", background="#f59e0b", foreground="#111827", font=("Segoe UI Semibold", 11))
        style.map("Menu.TButton", background=[("active", "#fbbf24")])
        style.configure("TLabel", background="#0f172a", foreground="#e2e8f0")
        style.configure("TEntry", fieldbackground="#ffffff")

    def _build_ui(self):
        frame = tk.Frame(self.root, bg="#0f172a")
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        title = tk.Label(frame, text="Módulo de Seguridad", bg="#0f172a", fg="#e2e8f0", font=("Segoe UI Semibold", 16))
        title.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0,10))

        # Left: form para credenciales
        tk.Label(frame, text="Servicio:", bg="#0f172a", fg="#e2e8f0").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.service_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.service_var, width=30).grid(row=1, column=1, sticky="w")

        tk.Label(frame, text="Usuario:", bg="#0f172a", fg="#e2e8f0").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        self.user_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.user_var, width=30).grid(row=2, column=1, sticky="w")

        tk.Label(frame, text="Contraseña:", bg="#0f172a", fg="#e2e8f0").grid(row=3, column=0, sticky="e", padx=6, pady=6)
        self.pw_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.pw_var, width=30, show="*").grid(row=3, column=1, sticky="w")

        # Password tools
        ttk.Button(frame, text="Generar contraseña", style="Menu.TButton", command=self._on_generate_pw).grid(row=4, column=1, sticky="w", pady=(6,0))
        ttk.Button(frame, text="Mostrar fuerza", style="Menu.TButton", command=self._on_check_strength).grid(row=4, column=0, sticky="e", pady=(6,0))

        self.strength_lbl = tk.Label(frame, text="", bg="#0f172a", fg="#e2e8f0")
        self.strength_lbl.grid(row=5, column=0, columnspan=2, sticky="w", pady=(4,12), padx=6)

        # Buttons: guardar / limpiar
        ttk.Button(frame, text="💾 Guardar credencial", style="Menu.TButton", command=self._on_save_cred).grid(row=6, column=0, pady=6)
        ttk.Button(frame, text="🧹 Limpiar formulario", style="Menu.TButton", command=self._on_clear_form).grid(row=6, column=1, pady=6)

        # Right: listado de credenciales
        tk.Label(frame, text="Credenciales guardadas:", bg="#0f172a", fg="#e2e8f0").grid(row=1, column=2, sticky="w", padx=12)
        self.tree = ttk.Treeview(frame, columns=("service","user"), show="headings", height=12)
        self.tree.heading("service", text="Servicio")
        self.tree.heading("user", text="Usuario")
        self.tree.grid(row=2, column=2, rowspan=5, columnspan=2, padx=(12,0), sticky="nsew")

        # Scrollbar
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        vsb.grid(row=2, column=4, rowspan=5, sticky="nsw")
        self.tree.configure(yscrollcommand=vsb.set)

        # acciones sobre lista
        ttk.Button(frame, text="🔍 Ver (desencriptar)", style="Menu.TButton", command=self._on_view_cred).grid(row=7, column=2, pady=8, sticky="w")
        ttk.Button(frame, text="✏️ Modificar", style="Menu.TButton", command=self._on_load_selected).grid(row=7, column=3, pady=8, sticky="w")
        ttk.Button(frame, text="🗑️ Eliminar", style="Menu.TButton", command=self._on_delete_selected).grid(row=7, column=4, pady=8, sticky="w")

        # Export / audit
        ttk.Button(frame, text="📤 Exportar (CSV)", style="Menu.TButton", command=self._on_export_csv).grid(row=8, column=2, pady=6, sticky="w")
        ttk.Button(frame, text="📘 Ver audit log", style="Menu.TButton", command=self._on_open_audit).grid(row=8, column=3, pady=6, sticky="w")

        # configure resizing behaviour
        frame.grid_columnconfigure(2, weight=1)
        frame.grid_rowconfigure(6, weight=1)

    # -----------------------
    # UI callbacks
    # -----------------------
    def _load_list(self):
        self.tree.delete(*self.tree.get_children())
        creds = load_creds()
        for i, c in enumerate(creds):
            self.tree.insert("", "end", iid=str(i), values=(c.get("service",""), c.get("user","")))

    def _on_generate_pw(self):
        pw = generate_password(16, symbols=True)
        self.pw_var.set(pw)
        self._on_check_strength()
        audit("generate_password", f"len={len(pw)}")
    
    def _on_check_strength(self):
        pw = self.pw_var.get() or ""
        score, label, notes = password_strength(pw)
        note_text = " — ".join(notes) if notes else ""
        self.strength_lbl.config(text=f"Fuerza: {label}. {note_text}")
        audit("check_password_strength", f"score={score}")

    def _on_save_cred(self):
        service = self.service_var.get().strip()
        user = self.user_var.get().strip()
        pw = self.pw_var.get().strip()
        if not service or not user or not pw:
            messagebox.showwarning("Validación", "Completa Servicio, Usuario y Contraseña.")
            return
        creds = load_creds()
        # store as {service,user, password} — password stored in plain inside the JSON before encrypting whole file
        creds.append({"service": service, "user": user, "password": pw, "created_at": datetime.now().isoformat()})
        save_creds(creds)
        audit("save_credential", f"{service}|{user}")
        messagebox.showinfo("Guardado", "Credencial guardada (archivo cifrado).")
        self._load_list()
        self._on_clear_form()

    def _on_clear_form(self):
        self.service_var.set("")
        self.user_var.set("")
        self.pw_var.set("")
        self.strength_lbl.config(text="")

    def _get_selected_index(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return int(sel[0])

    def _on_view_cred(self):
        idx = self._get_selected_index()
        if idx is None:
            messagebox.showwarning("Atención", "Selecciona una credencial para ver.")
            return
        creds = load_creds()
        if idx < 0 or idx >= len(creds):
            messagebox.showerror("Error", "Índice inválido.")
            return
        c = creds[idx]
        # mostrar en ventana (advertencia)
        audit("view_credential", f"{c.get('service')}|{c.get('user')}")
        top = tk.Toplevel(self.root)
        top.title("Ver credencial")
        top.configure(bg="#0f172a")
        tk.Label(top, text=f"Servicio: {c.get('service')}", bg="#0f172a", fg="#e2e8f0").pack(anchor="w", padx=10, pady=4)
        tk.Label(top, text=f"Usuario: {c.get('user')}", bg="#0f172a", fg="#e2e8f0").pack(anchor="w", padx=10, pady=4)
        tk.Label(top, text=f"Contraseña: {c.get('password')}", bg="#0f172a", fg="#e2e8f0").pack(anchor="w", padx=10, pady=8)
        tk.Button(top, text="Cerrar", command=top.destroy).pack(pady=8)

    def _on_load_selected(self):
        idx = self._get_selected_index()
        if idx is None:
            messagebox.showwarning("Atención", "Selecciona una credencial para modificar.")
            return
        creds = load_creds()
        if idx < 0 or idx >= len(creds):
            messagebox.showerror("Error", "Índice inválido.")
            return
        c = creds[idx]
        self.service_var.set(c.get("service",""))
        self.user_var.set(c.get("user",""))
        self.pw_var.set(c.get("password",""))
        # remove the existing one so Save will add updated
        creds.pop(idx)
        save_creds(creds)
        audit("load_for_edit", f"{c.get('service')}|{c.get('user')}")
        self._load_list()

    def _on_delete_selected(self):
        idx = self._get_selected_index()
        if idx is None:
            messagebox.showwarning("Atención", "Selecciona una credencial para eliminar.")
            return
        if not messagebox.askyesno("Confirmar", "¿Eliminar credencial seleccionada?"):
            return
        creds = load_creds()
        if idx < 0 or idx >= len(creds):
            messagebox.showerror("Error", "Índice inválido.")
            return
        removed = creds.pop(idx)
        save_creds(creds)
        audit("delete_credential", f"{removed.get('service')}|{removed.get('user')}")
        messagebox.showinfo("Eliminado", "Credencial eliminada.")
        self._load_list()

    def _on_export_csv(self):
        creds = load_creds()
        if not creds:
            messagebox.showwarning("Sin datos", "No hay credenciales para exportar.")
            return
        fname = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")])
        if not fname:
            return
        df = pd.DataFrame(creds)
        # omit passwords on export by default? include them but warn user:
        if not messagebox.askyesno("Exportar", "¿Incluir contraseñas en el CSV exportado? (archivo no cifrado)"):
            df = df.drop(columns=["password"], errors="ignore")
        df.to_csv(fname, index=False, encoding="utf-8-sig")
        audit("export_credentials", fname)
        messagebox.showinfo("Exportado", f"CSV exportado: {fname}")

    def _on_open_audit(self):
        ensure_base_dir()
        if not os.path.exists(AUDIT_LOG):
            messagebox.showinfo("Audit log", "No hay registros de auditoría aún.")
            return
        # abrir archivo en ventana simple
        with open(AUDIT_LOG, "r", encoding="utf-8") as f:
            data = f.read()
        top = tk.Toplevel(self.root)
        top.title("Audit log")
        txt = tk.Text(top, width=120, height=30)
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", data)
        txt.config(state="disabled")

# -----------------------
# Run standalone for testing
# -----------------------
if __name__ == "__main__":
    ensure_base_dir()
    # ensure key exists
    _ = load_key()
    root = tk.Tk()
    app = SeguridadTaller(root)
    root.mainloop()