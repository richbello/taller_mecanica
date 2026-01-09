# -*- coding: utf-8 -*-
"""
Pasarela de Pagos (sandbox) reforzada — ahora usa derivación de clave
desde la contraseña maestra (PBKDF2) para cifrar métodos tokenizados,
limpieza automática de portapapeles, límites de intentos para la maestra,
no almacenar CVV, y migración desde key legacy (security.key) si existe.

Requisitos:
  pip install cryptography openpyxl

Ubicación por defecto de datos:
  BASE_DIR = r"C:\RICHARD\RB\2025\Taller_mecánica"

Importante:
 - Esto sigue siendo un sandbox. Para producción debes usar un PSP (Stripe, etc.)
   y no almacenar PAN/CVV localmente.
 - Si habilitas la contraseña maestra, recuerda que si la olvidas los datos
   re-encriptados serán irrecuperables a menos que mantengas backups seguros.
"""

import os
import json
import uuid
import secrets
import time
import threading
import base64
import hashlib
from datetime import datetime, timedelta

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

import openpyxl

# ---- Config ----
BASE_DIR = r"C:\RICHARD\RB\2025\Taller_mecánica"
PAYMENT_FILE = os.path.join(BASE_DIR, "payment_methods.json.enc")
TRANSACTIONS_FILE = os.path.join(BASE_DIR, "transactions.json")
MASTER_FILE = os.path.join(BASE_DIR, "master_auth.json")  # stores salt/hash and enc_salt
LEGACY_KEY_FILE = os.path.join(BASE_DIR, "security.key")  # legacy key (if present)
AUDIT_LOG = os.path.join(BASE_DIR, "security_audit.log")

# KDF iterations (can be increased for more hardness)
KDF_ITERATIONS = 300_000

# Lockout policy
MAX_MASTER_ATTEMPTS = 5
LOCKOUT_SECONDS = 300  # 5 minutes

# Clipboard clear seconds
CLIPBOARD_CLEAR_SECONDS = 15

# ---- Utilities ----
def ensure_base_dir():
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR, exist_ok=True)

def audit(action, details=""):
    ensure_base_dir()
    ts = datetime.now().isoformat(sep=" ", timespec="seconds")
    try:
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(f"{ts} | {action} | {details}\n")
    except Exception:
        pass

def _set_private_file_permissions(path):
    # Best effort: set owner-only permissions on Unix; on Windows this is best-effort.
    try:
        if os.name == "posix":
            os.chmod(path, 0o600)
        else:
            # On Windows, os.chmod is limited; leave as-is or user can set ACLs manually
            pass
    except Exception:
        pass

# ---- Master password + KDF / key derivation ----
def master_exists():
    return os.path.exists(MASTER_FILE)

def create_master_interactive(parent):
    """
    Create master_auth.json storing:
      - salt (for verifying)
      - hash (PBKDF2 of password)
      - enc_salt (salt for deriving encryption key)
      - iterations
    """
    ensure_base_dir()
    p1 = simpledialog.askstring("Crear contraseña maestra", "Ingrese contraseña maestra:", show="*", parent=parent)
    if not p1:
        return False
    p2 = simpledialog.askstring("Confirmar contraseña maestra", "Reingrese la contraseña maestra:", show="*", parent=parent)
    if p1 != p2:
        messagebox.showerror("Error", "Las contraseñas no coinciden.")
        return False

    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", p1.encode("utf-8"), salt, KDF_ITERATIONS)
    enc_salt = secrets.token_bytes(16)

    data = {
        "salt": base64.b64encode(salt).decode("ascii"),
        "hash": base64.b64encode(dk).decode("ascii"),
        "enc_salt": base64.b64encode(enc_salt).decode("ascii"),
        "iterations": KDF_ITERATIONS
    }
    with open(MASTER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)
    _set_private_file_permissions(MASTER_FILE)
    audit("master_created", "")
    messagebox.showinfo("Creada", "Contraseña maestra creada correctamente.")
    return True

def _derive_fernet_key(password: str, enc_salt_b64: str, iterations: int):
    enc_salt = base64.b64decode(enc_salt_b64)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=enc_salt,
        iterations=iterations,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
    return key

# ---- Master verification with lockout + session ----
_master_failed_count = 0
_lockout_until = None
_session_fernet = None
_session_expires = None
SESSION_TIMEOUT_SECONDS = 600  # default 10 minutes

def verify_master_and_get_fernet(parent, purpose="acción sensible", require_create=True):
    """
    Verify master password, apply lockout policy, and return a Fernet instance derived from master.
    Caches a session key in memory for SESSION_TIMEOUT_SECONDS.
    """
    global _master_failed_count, _lockout_until, _session_fernet, _session_expires

    ensure_base_dir()

    now = datetime.now()
    if _session_fernet is not None and _session_expires and now < _session_expires:
        # reuse session key
        return _session_fernet

    # Check lockout
    if _lockout_until and now < _lockout_until:
        secs = int((_lockout_until - now).total_seconds())
        messagebox.showerror("Bloqueado", f"Demasiados intentos fallidos. Intenta nuevamente en {secs} segundos.")
        return None

    if not master_exists():
        if require_create and messagebox.askyesno("Contraseña maestra no encontrada", "No existe una contraseña maestra. ¿Desea crearla ahora?"):
            ok = create_master_interactive(parent)
            if not ok:
                return None
        else:
            return None

    # Load master data
    try:
        with open(MASTER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        salt = base64.b64decode(data["salt"])
        stored_hash = base64.b64decode(data["hash"])
        enc_salt_b64 = data["enc_salt"]
        iterations = int(data.get("iterations", KDF_ITERATIONS))
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo leer configuración de la maestra: {e}")
        audit("master_read_failed", str(e))
        return None

    attempt = simpledialog.askstring("Contraseña maestra", f"Ingrese la contraseña maestra para {purpose}:", show="*", parent=parent)
    if attempt is None:
        return None

    # verify using PBKDF2HMAC (same algorithm used to create)
    dk = hashlib.pbkdf2_hmac("sha256", attempt.encode("utf-8"), salt, iterations)

    if not secrets.compare_digest(dk, stored_hash):
        _master_failed_count += 1
        audit("master_failed", purpose)
        if _master_failed_count >= MAX_MASTER_ATTEMPTS:
            _lockout_until = datetime.now() + timedelta(seconds=LOCKOUT_SECONDS)
            _master_failed_count = 0
            messagebox.showerror("Bloqueado", f"Demasiados intentos fallidos. Bloqueado por {LOCKOUT_SECONDS} segundos.")
        else:
            remaining = MAX_MASTER_ATTEMPTS - _master_failed_count
            messagebox.showerror("Error", f"Contraseña maestra incorrecta. Intentos restantes: {remaining}")
        return None

    # Verified -> derive Fernet key for encryption/decryption
    try:
        key = _derive_fernet_key(attempt, enc_salt_b64, iterations)
        f = Fernet(key)
        # start session cache
        _session_fernet = f
        _session_expires = datetime.now() + timedelta(seconds=SESSION_TIMEOUT_SECONDS)
        _master_failed_count = 0
        audit("master_verified", purpose)
        return f
    except Exception as e:
        audit("master_derive_failed", str(e))
        messagebox.showerror("Error", f"No se pudo derivar la clave: {e}")
        return None

# ---- Legacy key migration helpers ----
def _legacy_key_exists():
    return os.path.exists(LEGACY_KEY_FILE)

def _load_legacy_fernet():
    try:
        with open(LEGACY_KEY_FILE, "rb") as f:
            key = f.read()
        return Fernet(key)
    except Exception:
        return None

def _migrate_payment_file_if_needed(fernet_new):
    """
    If PAYMENT_FILE exists and was encrypted with legacy key, try to decrypt with legacy key,
    then re-encrypt with fernet_new. Back up the old encrypted file first.
    """
    if not os.path.exists(PAYMENT_FILE):
        return
    # try decrypt with new key first (if already migrated)
    try:
        with open(PAYMENT_FILE, "rb") as f:
            enc = f.read()
        _ = fernet_new.decrypt(enc)  # if succeeds, already migrated
        return
    except Exception:
        pass

    # try legacy
    if _legacy_key_exists():
        legacy_f = _load_legacy_fernet()
        if legacy_f:
            try:
                with open(PAYMENT_FILE, "rb") as f:
                    enc = f.read()
                data = legacy_f.decrypt(enc)
                # success — back up and re-encrypt with new fernet
                bak = PAYMENT_FILE + ".bak-" + datetime.now().strftime("%Y%m%d%H%M%S")
                try:
                    os.replace(PAYMENT_FILE, bak)
                except Exception:
                    # fallback copy
                    try:
                        import shutil
                        shutil.copy2(PAYMENT_FILE, bak)
                    except Exception:
                        pass
                # write new encrypted file
                new_enc = fernet_new.encrypt(data)
                with open(PAYMENT_FILE, "wb") as f:
                    f.write(new_enc)
                _set_private_file_permissions(PAYMENT_FILE)
                audit("migrated_payment_file", f"backup={os.path.basename(bak)}")
                # optional: remove legacy key file to reduce risk
                try:
                    os.remove(LEGACY_KEY_FILE)
                    audit("legacy_key_removed", "")
                except Exception:
                    pass
            except Exception as e:
                audit("migration_failed", str(e))
                # leave as-is; decryption with new key failed and legacy didn't help
                return

# ---- Storage helpers (use session Fernet when possible) ----
def _fernet_for_storage(parent):
    """
    Return Fernet instance derived from master session (prompt if needed).
    """
    f = verify_master_and_get_fernet(parent, "operaciones de la pasarela")
    return f

def load_payment_methods(parent):
    ensure_base_dir()
    if not os.path.exists(PAYMENT_FILE):
        return []
    # get fernet (session)
    f = _fernet_for_storage(parent)
    if f is None:
        # cannot decrypt without master; return empty or alert
        messagebox.showwarning("Acceso denegado", "No se proporcionó la contraseña maestra. No se pueden cargar métodos tokenizados.")
        return []
    try:
        with open(PAYMENT_FILE, "rb") as fh:
            enc = fh.read()
        data = f.decrypt(enc)
        arr = json.loads(data.decode("utf-8"))
        return arr
    except InvalidToken:
        # possibly not migrated — try migration using legacy key flow
        # attempt migration using a prompt-derived fernet (already have f) - attempt migration helper
        try:
            _migrate_payment_file_if_needed(f)
            # retry load
            with open(PAYMENT_FILE, "rb") as fh:
                enc = fh.read()
            data = f.decrypt(enc)
            arr = json.loads(data.decode("utf-8"))
            return arr
        except Exception as e:
            audit("load_payment_methods_failed", str(e))
            messagebox.showerror("Error", "No se pudo desencriptar métodos tokenizados. Verifica la contraseña maestra o la existencia de la key legacy.")
            return []
    except Exception as e:
        audit("load_payment_methods_failed", str(e))
        return []

def save_payment_methods(parent, arr):
    ensure_base_dir()
    f = _fernet_for_storage(parent)
    if f is None:
        messagebox.showwarning("Acceso denegado", "No se proporcionó la contraseña maestra. No se pueden guardar métodos tokenizados.")
        return False
    try:
        data = json.dumps(arr, ensure_ascii=False, indent=2).encode("utf-8")
        enc = f.encrypt(data)
        with open(PAYMENT_FILE, "wb") as fh:
            fh.write(enc)
        _set_private_file_permissions(PAYMENT_FILE)
        return True
    except Exception as e:
        audit("save_payment_methods_failed", str(e))
        messagebox.showerror("Error", f"No se pudo guardar métodos tokenizados: {e}")
        return False

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
    _set_private_file_permissions(TRANSACTIONS_FILE)

# ---- Other utilities ----
def luhn_checksum(card_number: str) -> bool:
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

def simulate_charge(card_full: str, amount: float):
    time.sleep(0.6)
    tx_id = str(uuid.uuid4())
    ok = secrets.randbelow(100) >= 5
    result = {
        "id": tx_id,
        "status": "approved" if ok else "declined",
        "processor_code": "00" if ok else "05",
        "message": "Aprobado" if ok else "Rechazado por emisor",
        "amount": amount
    }
    return ok, result

def copy_to_clipboard_then_clear(root, text, seconds=CLIPBOARD_CLEAR_SECONDS):
    try:
        root.clipboard_clear()
        root.clipboard_append(text)
        audit("copy_to_clipboard", f"len={len(text)}")
    except Exception:
        pass

    def clear():
        try:
            root.clipboard_clear()
            audit("clipboard_cleared", "")
        except Exception:
            pass
    t = threading.Timer(seconds, clear)
    t.daemon = True
    t.start()

# ---- Modern button ----
def _lighten(hex_color, factor=1.12):
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = min(255, int(r * factor))
    g = min(255, int(g * factor))
    b = min(255, int(b * factor))
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

class ModernButton(tk.Button):
    def __init__(self, master=None, text="", command=None, bg="#f59e0b", fg="#111827", font=("Segoe UI Semibold", 10), padx=10, pady=6, **kwargs):
        hover = _lighten(bg, 1.12)
        super().__init__(master,
                         text=text,
                         command=command,
                         bg=bg,
                         fg=fg,
                         activebackground=hover,
                         activeforeground=fg,
                         bd=0,
                         relief="flat",
                         highlightthickness=0,
                         cursor="hand2",
                         font=font,
                         padx=padx,
                         pady=pady,
                         **kwargs)
        self._bg = bg
        self._hover = hover
        self.bind("<Enter>", lambda e: self.configure(bg=self._hover))
        self.bind("<Leave>", lambda e: self.configure(bg=self._bg))

# ---- UI: Pasarela de Pagos ----
class PasarelaPagos:
    def __init__(self, root):
        ensure_base_dir()
        self.root = root
        self.root.title("💳 Pasarela de Pagos - Taller Mecánico (Sandbox)")
        self.root.geometry("980x640")
        self.root.minsize(880, 560)
        self._setup_styles()
        self._build_ui()
        # Try to ensure migration if legacy key exists and master available
        # Note: we do not auto-prompt here; load_data will prompt when needed.
        self._load_data()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#0f172a", foreground="#e2e8f0")

    def _build_ui(self):
        frame = tk.Frame(self.root, bg="#0f172a")
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        title = tk.Label(frame, text="Pasarela de Pagos (Sandbox)", bg="#0f172a", fg="#e2e8f0", font=("Segoe UI Semibold", 16))
        title.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0,10))

        # Form fields
        tk.Label(frame, text="Cliente:", bg="#0f172a", fg="#e2e8f0").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.client_var = tk.StringVar(); ttk.Entry(frame, textvariable=self.client_var, width=30).grid(row=1, column=1, sticky="w")

        tk.Label(frame, text="Monto (USD):", bg="#0f172a", fg="#e2e8f0").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        self.amount_var = tk.StringVar(); ttk.Entry(frame, textvariable=self.amount_var, width=20).grid(row=2, column=1, sticky="w")

        tk.Label(frame, text="Tarjeta guardada:", bg="#0f172a", fg="#e2e8f0").grid(row=3, column=0, sticky="e", padx=6, pady=6)
        self.saved_cards_cb = ttk.Combobox(frame, values=[], state="readonly", width=36); self.saved_cards_cb.grid(row=3, column=1, sticky="w")
        ModernButton(frame, text="Usar tarjeta seleccionada", command=self._use_selected_card).grid(row=3, column=2, padx=6)

        tk.Label(frame, text="Número de tarjeta:", bg="#0f172a", fg="#e2e8f0").grid(row=4, column=0, sticky="e", padx=6, pady=6)
        self.card_number_var = tk.StringVar(); ttk.Entry(frame, textvariable=self.card_number_var, width=36).grid(row=4, column=1, sticky="w")

        tk.Label(frame, text="MM/AA:", bg="#0f172a", fg="#e2e8f0").grid(row=5, column=0, sticky="e", padx=6, pady=6)
        self.expiry_var = tk.StringVar(); ttk.Entry(frame, textvariable=self.expiry_var, width=12).grid(row=5, column=1, sticky="w")

        tk.Label(frame, text="CVV:", bg="#0f172a", fg="#e2e8f0").grid(row=6, column=0, sticky="e", padx=6, pady=6)
        self.cvv_var = tk.StringVar(); ttk.Entry(frame, textvariable=self.cvv_var, width=8, show="*").grid(row=6, column=1, sticky="w")

        self.save_card_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Guardar tarjeta tokenizada para futuros pagos", variable=self.save_card_var).grid(row=7, column=1, sticky="w", pady=(4,8))

        ModernButton(frame, text="Procesar pago", command=self._on_process_payment).grid(row=8, column=1, pady=10, sticky="w")
        ModernButton(frame, text="Tokenizar tarjeta (guardar)", command=self._on_tokenize_card).grid(row=8, column=2, pady=10, sticky="w")

        # Right: tokenized methods & transactions
        tk.Label(frame, text="Métodos tokenizados:", bg="#0f172a", fg="#e2e8f0").grid(row=1, column=3, sticky="w", padx=12)
        self.methods_tree = ttk.Treeview(frame, columns=("token","mask","brand"), show="headings", height=8)
        self.methods_tree.heading("token", text="Token"); self.methods_tree.heading("mask", text="Tarjeta"); self.methods_tree.heading("brand", text="Marca")
        self.methods_tree.grid(row=2, column=3, rowspan=4, padx=12, sticky="nsew")

        tk.Label(frame, text="Transacciones:", bg="#0f172a", fg="#e2e8f0").grid(row=6, column=3, sticky="w", padx=12, pady=(8,0))
        self.tx_tree = ttk.Treeview(frame, columns=("id","cliente","amount","status","time"), show="headings", height=8)
        for c, txt in [("id","ID"),("cliente","Cliente"),("amount","Monto"),("status","Estado"),("time","Fecha")]:
            self.tx_tree.heading(c, text=txt); self.tx_tree.column(c, width=120)
        self.tx_tree.grid(row=7, column=3, rowspan=4, padx=12, sticky="nsew")

        ModernButton(frame, text="Ver tarjeta (temporal)", command=self._on_view_card).grid(row=11, column=3, sticky="w", padx=12, pady=6)
        ModernButton(frame, text="Eliminar método", command=self._on_delete_method).grid(row=11, column=3, sticky="e", padx=12, pady=6)

        ModernButton(frame, text="Exportar transacciones (Excel)", command=self._on_export_transactions).grid(row=12, column=3, sticky="w", padx=12, pady=6)
        ModernButton(frame, text="Ver audit log", command=lambda: self._open_audit()).grid(row=12, column=3, sticky="e", padx=12, pady=6)

        frame.grid_columnconfigure(3, weight=1)
        frame.grid_rowconfigure(7, weight=1)

    def _load_data(self):
        # Attempt to load methods and txs.
        # Note: load_payment_methods will prompt master if needed.
        try:
            # If not master yet, user will be prompted inside load_payment_methods
            self.methods = load_payment_methods(self.root)
        except Exception as e:
            audit("load_methods_exception", str(e))
            self.methods = []
        self._refresh_methods_ui()
        self._refresh_transactions_ui()

    def _refresh_methods_ui(self):
        self.methods_tree.delete(*self.methods_tree.get_children())
        for m in self.methods:
            self.methods_tree.insert("", "end", iid=m.get("token"), values=(m.get("token"), m.get("mask"), m.get("brand","")))
        cb_vals = [f"{m.get('mask')}  ({m.get('token')[:8]})" for m in self.methods]
        self.saved_cards_cb['values'] = cb_vals

    def _refresh_transactions_ui(self):
        self.tx_tree.delete(*self.tx_tree.get_children())
        txs = load_transactions()
        for t in txs[-200:]:
            self.tx_tree.insert("", "end", values=(t.get("id"), t.get("cliente"), f"{t.get('amount'):.2f}", t.get('status'), t.get('time')))

    def _on_tokenize_card(self):
        card = self.card_number_var.get().strip()
        exp = self.expiry_var.get().strip()
        if not card or not exp:
            messagebox.showwarning("Validación", "Completa número y expiración para tokenizar.")
            return
        if not luhn_checksum(card):
            messagebox.showwarning("Validación", "Número de tarjeta inválido (Luhn).")
            return
        # Ask for master and derive fernet (this also creates master if not existing)
        f = verify_master_and_get_fernet(self.root, "tokenizar tarjeta")
        if f is None:
            return
        token = str(uuid.uuid4())
        masked = mask_card(card)
        brand = "CARD"
        # Store payload without CVV (do not store CVV)
        payload = {"card": card, "exp": exp}
        try:
            enc = f.encrypt(json.dumps(payload).encode("utf-8"))
            # load current methods (use storage helper)
            methods = load_payment_methods(self.root) or []
            methods.append({
                "token": token,
                "mask": masked,
                "brand": brand,
                "enc": enc.decode("utf-8"),
                "created_at": datetime.now().isoformat()
            })
            ok = save_payment_methods(self.root, methods)
            if ok:
                audit("tokenize_card", f"token={token} mask={masked}")
                messagebox.showinfo("Tokenizado", f"Tarjeta tokenizada: {masked}")
                self.card_number_var.set("")
                self.cvv_var.set("")
                self.expiry_var.set("")
                self.methods = methods
                self._refresh_methods_ui()
            else:
                messagebox.showerror("Error", "No se pudo guardar la tarjeta tokenizada.")
        except Exception as e:
            audit("tokenize_failed", str(e))
            messagebox.showerror("Error", f"No se pudo tokenizar la tarjeta: {e}")

    def _get_selected_method_token(self):
        sel = self.methods_tree.selection()
        if not sel:
            return None
        return sel[0]

    def _on_view_card(self):
        # Require master before showing PAN
        f = verify_master_and_get_fernet(self.root, "ver tarjeta tokenizada")
        if f is None:
            return
        token = self._get_selected_method_token()
        if token is None:
            messagebox.showwarning("Selecciona", "Selecciona un método tokenizado.")
            return
        m = next((x for x in (self.methods or []) if x.get("token") == token), None)
        if not m:
            messagebox.showerror("Error", "Método no encontrado.")
            return
        try:
            dec = f.decrypt(m.get("enc").encode("utf-8"))
            payload = json.loads(dec.decode("utf-8"))
            audit("view_card", f"token={token}")
            top = tk.Toplevel(self.root)
            top.title("Tarjeta (temporal)")
            top.configure(bg="#0f172a")
            tk.Label(top, text=f"Token: {token}", bg="#0f172a", fg="#e2e8f0").pack(anchor="w", padx=10, pady=4)
            tk.Label(top, text=f"Tarjeta: {payload.get('card')}", bg="#0f172a", fg="#e2e8f0").pack(anchor="w", padx=10, pady=2)
            tk.Label(top, text=f"Exp: {payload.get('exp')}", bg="#0f172a", fg="#e2e8f0").pack(anchor="w", padx=10, pady=2)
            ModernButton(top, text="Copiar número", command=lambda: copy_to_clipboard_then_clear(self.root, payload.get("card"))).pack(pady=6)
            ModernButton(top, text="Cerrar", command=top.destroy).pack(pady=6)
        except InvalidToken:
            audit("view_card_failed_invalidtoken", f"token={token}")
            messagebox.showerror("Error", "No fue posible desencriptar la tarjeta (token inválido).")
        except Exception as e:
            audit("view_card_failed", str(e))
            messagebox.showerror("Error", f"No se pudo desencriptar la tarjeta: {e}")

    def _on_delete_method(self):
        # Require master for deletion
        f = verify_master_and_get_fernet(self.root, "eliminar método tokenizado")
        if f is None:
            return
        token = self._get_selected_method_token()
        if token is None:
            messagebox.showwarning("Selecciona", "Selecciona un método tokenizado.")
            return
        if not messagebox.askyesno("Confirmar", "Eliminar método tokenizado seleccionado?"):
            return
        try:
            methods = load_payment_methods(self.root) or []
            methods = [m for m in methods if m.get("token") != token]
            ok = save_payment_methods(self.root, methods)
            if ok:
                audit("delete_method", f"token={token}")
                messagebox.showinfo("Eliminado", "Método eliminado.")
                self.methods = methods
                self._refresh_methods_ui()
            else:
                messagebox.showerror("Error", "No se pudo eliminar el método.")
        except Exception as e:
            audit("delete_method_failed", str(e))
            messagebox.showerror("Error", f"No se pudo eliminar el método: {e}")

    def _use_selected_card(self):
        idx = self.saved_cards_cb.current()
        if idx < 0:
            messagebox.showwarning("Selecciona", "Selecciona una tarjeta en el desplegable.")
            return
        m = self.methods[idx]
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

        token = None
        entered = self.card_number_var.get().strip()
        selected_method = None

        for m in (self.methods or []):
            if entered and m.get("mask") == entered:
                token = m.get("token")
                selected_method = m
                break

        full_card = None
        if token:
            # decrypt with session fernet
            f = verify_master_and_get_fernet(self.root, "procesar pago con tarjeta tokenizada")
            if f is None:
                return
            try:
                dec = f.decrypt(selected_method.get("enc").encode("utf-8"))
                payload = json.loads(dec.decode("utf-8"))
                full_card = payload.get("card")
            except Exception as e:
                audit("process_failed_decrypt", str(e))
                messagebox.showerror("Error", "No se pudo acceder a la tarjeta tokenizada.")
                return
        else:
            # direct entry (only for sandbox)
            full_card = ''.join(filter(str.isdigit, self.card_number_var.get()))
            if not luhn_checksum(full_card):
                messagebox.showwarning("Validación", "Número de tarjeta inválido (Luhn).")
                return
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

        # If user wanted to save card, tokenize but DO NOT store CVV
        if self.save_card_var.get() and not token:
            # reuse tokenization but without storing CVV
            f = verify_master_and_get_fernet(self.root, "guardar tarjeta tras cobro")
            if f is None:
                return
            token_new = str(uuid.uuid4())
            masked = mask_card(full_card)
            brand = "CARD"
            payload = {"card": full_card, "exp": self.expiry_var.get().strip()}
            try:
                enc = f.encrypt(json.dumps(payload).encode("utf-8"))
                methods = load_payment_methods(self.root) or []
                methods.append({
                    "token": token_new,
                    "mask": masked,
                    "brand": brand,
                    "enc": enc.decode("utf-8"),
                    "created_at": datetime.now().isoformat()
                })
                ok2 = save_payment_methods(self.root, methods)
                if ok2:
                    audit("tokenize_card_on_charge", f"token={token_new} mask={masked}")
                    messagebox.showinfo("Guardado", f"Tarjeta guardada tokenizada como {masked}")
                    self.methods = methods
                    self._refresh_methods_ui()
                else:
                    messagebox.showerror("Error", "No se pudo guardar la tarjeta tokenizada.")
            except Exception as e:
                audit("tokenize_on_charge_failed", str(e))

    def _on_export_transactions(self):
        # Require master for export since file may contain sensitive metadata
        f = verify_master_and_get_fernet(self.root, "exportar transacciones")
        if f is None:
            return
        txs = load_transactions()
        if not txs:
            messagebox.showwarning("Sin datos", "No hay transacciones para exportar.")
            return
        fname = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel","*.xlsx")])
        if not fname:
            return
        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Transacciones"
            ws.append(["ID","Cliente","Monto","Estado","Mensaje","Fecha","Token","Tarjeta enmascarada"])
            for t in txs:
                ws.append([t.get("id"), t.get("cliente"), t.get("amount"), t.get("status"), t.get("message"), t.get("time"), t.get("method_token"), t.get("card_mask")])
            wb.save(fname)
            audit("export_transactions", fname)
            messagebox.showinfo("Exportado", f"Transacciones exportadas a:\n{fname}")
        except Exception as e:
            audit("export_failed", str(e))
            messagebox.showerror("Error", f"No se pudo exportar: {e}")

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

# ---- Run standalone ----
if __name__ == "__main__":
    ensure_base_dir()
    root = tk.Tk()
    app = PasarelaPagos(root)
    root.mainloop()