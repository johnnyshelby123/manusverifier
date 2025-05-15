import tkinter as tk
from tkinter import ttk, messagebox

class AccountDialog(tk.Toplevel):
    def __init__(self, parent, acc_id="", bearer="", phone="", region_code="+1"):
        super().__init__(parent)
        self.title("Account Details")
        self.result = None

        self.geometry("400x220")
        self.resizable(False, False)

        ttk.Label(self, text="Account ID (unique):").pack(pady=5, anchor="w", padx=10)
        self.acc_id_var = tk.StringVar(value=acc_id)
        ttk.Entry(self, textvariable=self.acc_id_var).pack(fill="x", padx=10)

        ttk.Label(self, text="Bearer Token:").pack(pady=5, anchor="w", padx=10)
        self.bearer_var = tk.StringVar(value=bearer)
        ttk.Entry(self, textvariable=self.bearer_var).pack(fill="x", padx=10)

        ttk.Label(self, text="Phone Number:").pack(pady=5, anchor="w", padx=10)
        self.phone_var = tk.StringVar(value=phone)
        ttk.Entry(self, textvariable=self.phone_var).pack(fill="x", padx=10)

        ttk.Label(self, text="Region Code (e.g. +1):").pack(pady=5, anchor="w", padx=10)
        self.region_var = tk.StringVar(value=region_code)
        ttk.Entry(self, textvariable=self.region_var).pack(fill="x", padx=10)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="OK", command=self.on_ok).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="left", padx=5)

        self.bind("<Return>", lambda e: self.on_ok())
        self.bind("<Escape>", lambda e: self.destroy())

    def on_ok(self):
        acc_id = self.acc_id_var.get().strip()
        bearer = self.bearer_var.get().strip()
        phone = self.phone_var.get().strip()
        region_code = self.region_var.get().strip() or "+1"

        if not acc_id or not bearer or not phone:
            messagebox.showwarning("Invalid", "Account ID, Bearer Token, and Phone Number cannot be empty.")
            return

        self.result = (acc_id, bearer, phone, region_code)
        self.destroy()

