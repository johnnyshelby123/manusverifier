import tkinter as tk
from tkinter import ttk, messagebox
from .dialog import AccountDialog # Relative import for dialog within utils

class AccountManager:
    def __init__(self, parent_app, accounts_listbox, config_data):
        self.parent_app = parent_app # To call wait_window
        self.accounts_listbox = accounts_listbox
        self.config_data = config_data

    def add_account_dialog(self):
        dlg = AccountDialog(self.parent_app) # Pass the main app window as parent
        self.parent_app.wait_window(dlg)
        if dlg.result:
            acc_id, bearer, phone, region_code = dlg.result
            self.config_data["accounts"][acc_id] = {
                "bearer": bearer,
                "phone": phone,
                "region_code": region_code
            }
            self.refresh_accounts_list()

    def edit_account_dialog(self):
        sel = self.accounts_listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "Select an account first.")
            return
        acc_id = self.accounts_listbox.get(sel[0])
        acc_data = self.config_data["accounts"].get(acc_id, {})
        dlg = AccountDialog(self.parent_app, acc_id=acc_id,
                            bearer=acc_data.get("bearer", ""),
                            phone=acc_data.get("phone", ""),
                            region_code=acc_data.get("region_code", "+1"))
        self.parent_app.wait_window(dlg)
        if dlg.result:
            new_acc_id, bearer, phone, region_code = dlg.result
            if new_acc_id != acc_id and acc_id in self.config_data["accounts"]:
                del self.config_data["accounts"][acc_id]
            self.config_data["accounts"][new_acc_id] = {
                "bearer": bearer,
                "phone": phone,
                "region_code": region_code
            }
            self.refresh_accounts_list()

    def remove_selected_account(self):
        sel = self.accounts_listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "Select an account first.")
            return
        acc_id = self.accounts_listbox.get(sel[0])
        if messagebox.askyesno("Confirm", f"Remove account \'{acc_id}\'?"):
            if acc_id in self.config_data["accounts"]:
                del self.config_data["accounts"][acc_id]
                self.refresh_accounts_list()

    def refresh_accounts_list(self):
        self.accounts_listbox.delete(0, "end")
        for acc_id in self.config_data["accounts"]:
            self.accounts_listbox.insert("end", acc_id)

