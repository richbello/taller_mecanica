import os
import json
import uuid
import secrets
import time
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from cryptography.fernet import Fernet
import openpyxl

# Mantener la misma ruta base que los otros módulos
BASE_DIR = r"C:\RICHARD\RB\2025\Taller_mecánica"
PAYMENT_FILE = os.path.join(BASE_DIR, "payment_methods.json.enc")
TRANSACTIONS_FILE = os.path.join(BASE_DIR, "transactions.json")
KEY_FILE = os.path.join(BASE_DIR, "security.key")  # usa la misma key que el módulo de seguridad
AUDIT_LOG = os.path.join(BASE_DIR, "security_audit.log")


# -------------------------
# Crypto / utilidades
# -------------------------
def ensure_base_dir():
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR, exist_ok=True)

def load_key():
    ensure_base_dir()
    if not os.path.exists(KEY_FILE):
        # crear una key temporal si no existe (mejor usar seguridad_taller para generar)
        k = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(k)
        return k
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


# -------------------------
# Almacenamiento de métodos de pago (tarjetas tokenizadas)
# -------------------------
def load_payment_methods():
    ensure_base_dir()
    if not os.path.exists(PAYMENT_FILE):
        return []
    try:
        with open(PAYMENT_FILE, "rb") as f:
            enc = f.read()
        data = decrypt_bytes(enc)
        return json.loads(data.decode("utf-8"))
    except Exception as e:
        audit("load_payment_methods_failed", str(e))
        return []

def save_payment_methods(arr):
    ensure_base_dir()
    data = json.dumps(arr, ensure_ascii=False, indent=2).encode("utf-8")
    enc = encrypt_bytes(data)
    with open(PAYMENT_FILE, "wb") as f:
        f.write(enc)


# -------------------------
# Transacciones (registro)
# -------------------------
def load_transactions():
    ensure_base_dir()
    if not os.path.exists(TRANSACTIONS_FILE):
        return []
    try:
        with open(TRANSACTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_transaction(tx):
    ensure_base_dir()
    txs = load_transactions()
    txs.append(tx)
    with open(TRANSACTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(txs, f, ensure_ascii=False, indent=2)


# -------------------------
# Validaciones y util
# -------------------------
def luhn_checksum(card_number: str) -> bool:
    # retirar espacios
    s = ''.join(filter(str.isdigit, card_number))
    if not s:
        return False
    total = 0
    reverse_digits = s[::-1]
    for i, ch in enumerate(reverse_digits):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0

def mask_card(card_number: str) -> str:
    s = ''.join(filter(str.isdigit, card_number))
    if len(s) <= 4:
        return s
    return "**** **** **** " + s[-4:]


# -------------------------
# Simulación de procesamiento
# -------------------------
def simulate_charge(card_full: str, amount: float) -> (bool, dict):
    """
    Simula un cargo. No realiza ningún cobro real.
    Devuelve (success, resultado)
    """
    # pequeños delays para simular la red/procesador
    time.sleep(0.6)
    # generar id de transacción
    tx_id = str(uuid.uuid4())
    # probabilistic success
    ok = secrets.randbelow(100) >= 5  # 95% éxito por defecto
    result = {
        "id": tx_id,
        "status": "approved" if ok else "declined",
        "processor_code": "00" if ok else "05",
        "message": "Aprobado" if ok else "Rechazado por emisor",
        "amount": amount
    }
    return ok, result


# -------------------------
# UI: Pasarela de Pagos
# -------------------------
class PasarelaPagos:
    def __init__(self, root):
        self.root = root
        self.root.title("💳 Pasarela de Pagos - Taller Mecánico (Sandbox)")
        self.root.geometry("980x640")
        self.root.minsize(880, 560)
        self._setup_styles()
        self._build_ui()
        self._load_data()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Menu.TButton", background="#f59e0b", foreground="#111827", font=("Segoe UI Semibold", 11), padding=6)
        style.map("Menu.TButton", background=[("active", "#fbbf24")])
        style.configure("TLabel", background="#0f172a", foreground="#e2e8f0")

    def _build_ui(self):
        frame = tk.Frame(self.root, bg="#0f172a")
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        title = tk.Label(frame, text="Pasarela de Pagos (Sandbox)", bg="#0f172a", fg="#e2e8f0", font=("Segoe UI Semibold", 16))
        title.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0,10))

        # Form: cliente y monto
        tk.Label(frame, text="Cliente:", bg="#0f172a", fg="#e2e8f0").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.client_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.client_var, width=30).grid(row=1, column=1, sticky="w")

        tk.Label(frame, text="Monto (USD):", bg="#0f172a", fg="#e2e8f0").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        self.amount_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.amount_var, width=20).grid(row=2, column=1, sticky="w")

        # Método de pago: elegir tarjeta guardada o nueva
        tk.Label(frame, text="Tarjeta guardada:", bg="#0f172a", fg="#e2e8f0").grid(row=3, column=0, sticky="e", padx=6, pady=6)
        self.saved_cards_cb = ttk.Combobox(frame, values=[], state="readonly", width=36)
        self.saved_cards_cb.grid(row=3, column=1, sticky="w")

        ttk.Button(frame, text="Usar tarjeta seleccionada", style="Menu.TButton", command=self._use_selected_card).grid(row=3, column=2, padx=6)

        # Nuevo método: tarjeta completa
        tk.Label(frame, text="Número de tarjeta:", bg="#0f172a", fg="#e2e8f0").grid(row=4, column=0, sticky="e", padx=6, pady=6)
        self.card_number_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.card_number_var, width=36).grid(row=4, column=1, sticky="w")

        tk.Label(frame, text="MM/AA:", bg="#0f172a", fg="#e2e8f0").grid(row=5, column=0, sticky="e", padx=6, pady=6)
        self.expiry_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.expiry_var, width=12).grid(row=5, column=1, sticky="w")

        tk.Label(frame, text="CVV:", bg="#0f172a", fg="#e2e8f0").grid(row=6, column=0, sticky="e", padx=6, pady=6)
        self.cvv_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.cvv_var, width=8, show="*").grid(row=6, column=1, sticky="w")

        self.save_card_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Guardar tarjeta tokenizada para futuros pagos", variable=self.save_card_var).grid(row=7, column=1, sticky="w", pady=(4,8))

        # Acciones
        ttk.Button(frame, text="Procesar pago", style="Menu.TButton", command=self._on_process_payment).grid(row=8, column=1, pady=10, sticky="w")
        ttk.Button(frame, text="Tokenizar tarjeta (guardar)", style="Menu.TButton", command=self._on_tokenize_card).grid(row=8, column=2, pady=10, sticky="w")

        # Right side: listas
        tk.Label(frame, text="Métodos tokenizados:", bg="#0f172a", fg="#e2e8f0").grid(row=1, column=3, sticky="w", padx=12)
        self.methods_tree = ttk.Treeview(frame, columns=("token","mask","brand"), show="headings", height=8)
        self.methods_tree.heading("token", text="Token")
        self.methods_tree.heading("mask", text="Tarjeta")
        self.methods_tree.heading("brand", text="Marca")
        self.methods_tree.grid(row=2, column=3, rowspan=4, padx=12, sticky="nsew")

        tk.Label(frame, text="Transacciones:", bg="#0f172a", fg="#e2e8f0").grid(row=6, column=3, sticky="w", padx=12, pady=(8,0))
        self.tx_tree = ttk.Treeview(frame, columns=("id","cliente","amount","status","time"), show="headings", height=8)
        for c, txt in [("id","ID"),("cliente","Cliente"),("amount","Monto"),("status","Estado"),("time","Fecha")]:
            self.tx_tree.heading(c, text=txt)
            self.tx_tree.column(c, width=120)
        self.tx_tree.grid(row=7, column=3, rowspan=4, padx=12, sticky="nsew")

        # Buttons for methods & tx
        ttk.Button(frame, text="Ver tarjeta (temporal)", style="Menu.TButton", command=self._on_view_card).grid(row=11, column=3, sticky="w", padx=12, pady=6)
        ttk.Button(frame, text="Eliminar método", style="Menu.TButton", command=self._on_delete_method).grid(row=11, column=3, sticky="e", padx=12, pady=6)

        ttk.Button(frame, text="Exportar transacciones (Excel)", style="Menu.TButton", command=self._on_export_transactions).grid(row=12, column=3, sticky="w", padx=12, pady=6)
        ttk.Button(frame, text="Ver audit log", style="Menu.TButton", command=lambda: self._open_audit()).grid(row=12, column=3, sticky="e", padx=12, pady=6)

        frame.grid_columnconfigure(3, weight=1)
        frame.grid_rowconfigure(7, weight=1)

    def _load_data(self):
        # cargar métodos tokenizados y transacciones
        self.methods = load_payment_methods()
        self._refresh_methods_ui()
        self._refresh_transactions_ui()

    def _refresh_methods_ui(self):
        self.methods_tree.delete(*self.methods_tree.get_children())
        entries = []
        for m in self.methods:
            entries.append(f"{m.get('token')}|{m.get('mask')}")
            self.methods_tree.insert("", "end", iid=m.get("token"), values=(m.get("token"), m.get("mask"), m.get("brand","")))
        # actualizar combobox valores con máscara + token
        cb_vals = [f"{m.get('mask')}  ({m.get('token')[:8]})" for m in self.methods]
        self.saved_cards_cb['values'] = cb_vals

    def _refresh_transactions_ui(self):
        self.tx_tree.delete(*self.tx_tree.get_children())
        txs = load_transactions()
        for t in txs[-200:]:
            self.tx_tree.insert("", "end", values=(t.get("id"), t.get("cliente"), f"{t.get('amount'):.2f}", t.get("status"), t.get("time")))

    def _on_tokenize_card(self):
        # validar campos mínimos
        card = self.card_number_var.get().strip()
        exp = self.expiry_var.get().strip()
        cvv = self.cvv_var.get().strip()
        if not card or not exp or not cvv:
            messagebox.showwarning("Validación", "Completa número, expiración y CVV para tokenizar.")
            return
        if not luhn_checksum(card):
            messagebox.showwarning("Validación", "Número de tarjeta inválido (Luhn).")
            return
        # crear token y almacenar cifrado el número completo y cvv (no recomendado en producción)
        token = str(uuid.uuid4())
        masked = mask_card(card)
        brand = "CARD"
        # Guardar cifrado full card y cvv
        payload = {"card": card, "cvv": cvv, "exp": exp}
        enc = encrypt_bytes(json.dumps(payload).encode("utf-8"))
        self.methods.append({
            "token": token,
            "mask": masked,
            "brand": brand,
            "enc": enc.decode("utf-8"),
            "created_at": datetime.now().isoformat()
        })
        save_payment_methods(self.methods)
        audit("tokenize_card", f"token={token} mask={masked}")
        messagebox.showinfo("Tokenizado", f"Tarjeta tokenizada: {masked}")
        self._load_data()
        # opcional: limpiar campos
        self.card_number_var.set("")
        self.cvv_var.set("")
        self.expiry_var.set("")

    def _get_selected_method_token(self):
        sel = self.methods_tree.selection()
        if not sel:
            return None
        return sel[0]

    def _on_view_card(self):
        token = self._get_selected_method_token()
        if token is None:
            messagebox.showwarning("Selecciona", "Selecciona un método tokenizado.")
            return
        m = next((x for x in self.methods if x.get("token") == token), None)
        if not m:
            messagebox.showerror("Error", "Método no encontrado.")
            return
        # desencriptar temporalmente y mostrar (advertencia)
        try:
            dec = decrypt_bytes(m.get("enc").encode("utf-8"))
            payload = json.loads(dec.decode("utf-8"))
            audit("view_card", f"token={token}")
            top = tk.Toplevel(self.root)
            top.title("Tarjeta (temporal)")
            top.configure(bg="#0f172a")
            tk.Label(top, text=f"Token: {token}", bg="#0f172a", fg="#e2e8f0").pack(anchor="w", padx=10, pady=4)
            tk.Label(top, text=f"Tarjeta: {payload.get('card')}", bg="#0f172a", fg="#e2e8f0").pack(anchor="w", padx=10, pady=2)
            tk.Label(top, text=f"Exp: {payload.get('exp')}", bg="#0f172a", fg="#e2e8f0").pack(anchor="w", padx=10, pady=2)
            tk.Button(top, text="Copiar número", command=lambda: (self.root.clipboard_clear(), self.root.clipboard_append(payload.get("card")), audit("copy_card_from_view", token))).pack(pady=6)
            tk.Button(top, text="Cerrar", command=top.destroy).pack(pady=6)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo desencriptar la tarjeta: {e}")

    def _on_delete_method(self):
        token = self._get_selected_method_token()
        if token is None:
            messagebox.showwarning("Selecciona", "Selecciona un método tokenizado.")
            return
        if not messagebox.askyesno("Confirmar", "Eliminar método tokenizado seleccionado?"):
            return
        self.methods = [m for m in self.methods if m.get("token") != token]
        save_payment_methods(self.methods)
        audit("delete_method", f"token={token}")
        messagebox.showinfo("Eliminado", "Método eliminado.")
        self._load_data()

    def _use_selected_card(self):
        # cargar tarjeta seleccionada en los campos (sólo máscara visible)
        idx = self.saved_cards_cb.current()
        if idx < 0:
            messagebox.showwarning("Selecciona", "Selecciona una tarjeta en el desplegable.")
            return
        m = self.methods[idx]
        # colocar la máscara en campo número (como guía)
        self.card_number_var.set(m.get("mask"))
        self.expiry_var.set("")
        self.cvv_var.set("")
        self.save_card_var.set(False)
        messagebox.showinfo("Tarjeta cargada", "La tarjeta tokenizada se ha cargado para uso. Para ver el número real use 'Ver tarjeta (temporal)'.")
        audit("use_token_loaded", f"token={m.get('token')}")

    def _on_process_payment(self):
        client = self.client_var.get().strip()
        try:
            amount = float(self.amount_var.get())
        except Exception:
            messagebox.showwarning("Validación", "Ingresa un monto numérico válido.")
            return
        if amount <= 0:
            messagebox.showwarning("Validación", "El monto debe ser mayor que 0.")
            return

        # prefer tokenizada si la usuario cargó una máscara que coincide con método
        token = None
        entered = self.card_number_var.get().strip()
        selected_method = None

        # if user left card_number as a token mask pattern, detect
        for m in self.methods:
            if entered and m.get("mask") == entered:
                token = m.get("token")
                selected_method = m
                break

        full_card = None
        if token:
            # decrypt
            try:
                dec = decrypt_bytes(selected_method.get("enc").encode("utf-8"))
                payload = json.loads(dec.decode("utf-8"))
                full_card = payload.get("card")
            except Exception as e:
                messagebox.showerror("Error", "No se pudo acceder a la tarjeta tokenizada.")
                audit("process_failed_decrypt", str(e))
                return
        else:
            # use directly fields (only for sandbox)
            full_card = ''.join(filter(str.isdigit, self.card_number_var.get()))
            if not luhn_checksum(full_card):
                messagebox.showwarning("Validación", "Número de tarjeta inválido (Luhn).")
                return
            # verificar expiración simple (MM/AA)
            exp = self.expiry_var.get().strip()
            if "/" in exp:
                mm, yy = exp.split("/", 1)
                try:
                    mm = int(mm); yy = int(yy)
                    if mm < 1 or mm > 12:
                        raise ValueError()
                except Exception:
                    messagebox.showwarning("Validación", "Formato de expiración inválido (MM/AA).")
                    return

        # Simular proceso
        audit("process_payment_attempt", f"client={client} amount={amount} token={token or 'direct'}")
        ok, result = simulate_charge(full_card, amount)
        tx = {
            "id": result.get("id"),
            "cliente": client,
            "amount": amount,
            "status": result.get("status"),
            "processor_code": result.get("processor_code"),
            "message": result.get("message"),
            "time": datetime.now().isoformat(),
            "method_token": token,
            "card_mask": mask_card(full_card)
        }
        save_transaction(tx)
        audit("process_payment_result", f"id={tx['id']} status={tx['status']} client={client} amount={amount}")
        self._refresh_transactions_ui()
        if ok:
            messagebox.showinfo("Pago aprobado", f"Pago aprobado. ID: {tx['id']}")
        else:
            messagebox.showwarning("Pago rechazado", f"Pago rechazado: {result.get('message')}")

        # si la checkbox de guardar está marcada y no se usó tokenizada, tokenizar y guardar
        if self.save_card_var.get() and not token:
            # tokenizar y almacenar (copy of _on_tokenize_card but using full_card)
            token = str(uuid.uuid4())
            masked = mask_card(full_card)
            brand = "CARD"
            payload = {"card": full_card, "cvv": self.cvv_var.get().strip(), "exp": self.expiry_var.get().strip()}
            enc = encrypt_bytes(json.dumps(payload).encode("utf-8"))
            self.methods.append({
                "token": token,
                "mask": masked,
                "brand": brand,
                "enc": enc.decode("utf-8"),
                "created_at": datetime.now().isoformat()
            })
            save_payment_methods(self.methods)
            audit("tokenize_card_on_charge", f"token={token} mask={masked}")
            messagebox.showinfo("Guardado", f"Tarjeta guardada tokenizada como {masked}")
            self._load_data()

    def _on_export_transactions(self):
        txs = load_transactions()
        if not txs:
            messagebox.showwarning("Sin datos", "No hay transacciones para exportar.")
            return
        fname = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel","*.xlsx")])
        if not fname:
            return
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Transacciones"
        ws.append(["ID","Cliente","Monto","Estado","Mensaje","Fecha","Token","Tarjeta enmascarada"])
        for t in txs:
            ws.append([t.get("id"), t.get("cliente"), t.get("amount"), t.get("status"), t.get("message"), t.get("time"), t.get("method_token"), t.get("card_mask")])
        wb.save(fname)
        audit("export_transactions", fname)
        messagebox.showinfo("Exportado", f"Transacciones exportadas a:\n{fname}")

    def _open_audit(self):
        ensure_base_dir()
        if not os.path.exists(AUDIT_LOG):
            messagebox.showinfo("Audit log", "No hay registros de auditoría aún.")
            return
        with open(AUDIT_LOG, "r", encoding="utf-8") as f:
            data = f.read()
        top = tk.Toplevel(self.root)
        top.title("Audit log")
        txt = tk.Text(top, width=120, height=30)
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", data)
        txt.config(state="disabled")


if __name__ == "__main__":
    ensure_base_dir()
    # asegura que exista la key de cifrado (la genera si hace falta)
    _ = load_key()
    root = tk.Tk()
    app = PasarelaPagos(root)
    root.mainloop()