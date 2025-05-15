import json
import os
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

from utils.worker import RequestWorker
from utils.dialog import AccountDialog
from utils.consolelog import ConsoleLogger
from utils.accmanager import AccountManager

CONFIG_FILE = "config.json"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Multi-Account Code Tester")
        self.geometry("860x660")

        self.config_data = {
            "accounts": {},
            "discord_webhook_url": "",
            "num_threads": 23,
            "delay_between_requests": 1.5
        }
        self.load_config()

        self.stop_event = threading.Event()
        self.workers = []
        self.output_lock = threading.Lock() # ConsoleLogger and AccountManager might need this or handle their own

        # Console output area (must be created before ConsoleLogger)
        self.output_console = tk.Text(self, height=20)
        self.output_console.pack(fill="both", expand=True, padx=10, pady=5)
        self.output_console.configure(state="disabled", wrap="none")

        # Initialize ConsoleLogger
        self.console_logger = ConsoleLogger(self.output_console, self.output_lock)

        # Top frame for accounts
        frm_top = ttk.Frame(self)
        frm_top.pack(fill="x", padx=10, pady=5)

        ttk.Label(frm_top, text="Accounts:").grid(row=0, column=0, sticky="w")
        self.accounts_listbox = tk.Listbox(frm_top, height=8)
        self.accounts_listbox.grid(row=1, column=0, rowspan=5, sticky="ns")

        # Initialize AccountManager
        self.account_manager = AccountManager(self, self.accounts_listbox, self.config_data)

        btn_add = ttk.Button(frm_top, text="Add Account", command=self.account_manager.add_account_dialog)
        btn_add.grid(row=1, column=1, padx=5, sticky="ew")

        btn_edit = ttk.Button(frm_top, text="Edit Selected", command=self.account_manager.edit_account_dialog)
        btn_edit.grid(row=2, column=1, padx=5, sticky="ew")

        btn_remove = ttk.Button(frm_top, text="Remove Selected", command=self.account_manager.remove_selected_account)
        btn_remove.grid(row=3, column=1, padx=5, sticky="ew")

        # Settings
        frm_settings = ttk.Frame(self)
        frm_settings.pack(fill="x", padx=10, pady=5)

        ttk.Label(frm_settings, text="Discord Webhook URL:").grid(row=0, column=0, sticky="w")
        self.webhook_var = tk.StringVar(value=self.config_data.get("discord_webhook_url", ""))
        ttk.Entry(frm_settings, textvariable=self.webhook_var, width=80).grid(row=0, column=1, sticky="ew")

        ttk.Label(frm_settings, text="Threads per account:").grid(row=1, column=0, sticky="w")
        self.threads_var = tk.IntVar(value=self.config_data.get("num_threads", 23))
        ttk.Entry(frm_settings, textvariable=self.threads_var, width=10).grid(row=1, column=1, sticky="w")

        ttk.Label(frm_settings, text="Base delay between requests (seconds):").grid(row=2, column=0, sticky="w")
        self.delay_var = tk.DoubleVar(value=self.config_data.get("delay_between_requests", 1.5))
        ttk.Entry(frm_settings, textvariable=self.delay_var, width=10).grid(row=2, column=1, sticky="w")

        frm_settings.columnconfigure(1, weight=1)

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        self.start_btn = ttk.Button(btn_frame, text="Start", command=self.start_workers)
        self.start_btn.pack(side="left", padx=5)

        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self.stop_workers, state="disabled")
        self.stop_btn.pack(side="left", padx=5)

        ttk.Button(btn_frame, text="Save Config", command=self.save_config).pack(side="left", padx=5)

        ttk.Button(btn_frame, text="Reload Config", command=self.reload_config).pack(side="left", padx=5)

        # Instructions
        instr = (
            "Instructions:\n"
            "- Add accounts using 'Add Account'. Provide bearer token, phone number, and region code.\n"
            "- Edit or remove accounts as needed.\n"
            "- Set your Discord webhook URL, threads per account, and base delay between requests.\n"
            "- Click Start to run all accounts simultaneously.\n"
            "- Console shows real-time progress, updating in-place.\n"
            "- If 429 errors occur, delay between requests auto-increases exponentially, resetting after 30s without 429.\n"
            "- Click Stop to stop all running threads safely.\n"
            "- Use Save Config to save settings to config.json, Reload Config to reload.\n"
        )
        self.console_logger.log(instr + "\n", new=True)

        self.account_manager.refresh_accounts_list()

    def load_config(self):
        if os.path.isfile(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    loaded_config = json.load(f)
                    # Ensure all expected keys are present
                    self.config_data["accounts"] = loaded_config.get("accounts", {})
                    self.config_data["discord_webhook_url"] = loaded_config.get("discord_webhook_url", "")
                    self.config_data["num_threads"] = loaded_config.get("num_threads", 23)
                    self.config_data["delay_between_requests"] = loaded_config.get("delay_between_requests", 1.5)
            except Exception:
                # Keep default config if loading fails
                self.config_data = {
                    "accounts": {},
                    "discord_webhook_url": "",
                    "num_threads": 23,
                    "delay_between_requests": 1.5
                }
        # Update GUI elements if they exist already (might be called before full init)
        if hasattr(self, 'webhook_var'):
            self.webhook_var.set(self.config_data.get("discord_webhook_url", ""))
            self.threads_var.set(self.config_data.get("num_threads", 23))
            self.delay_var.set(self.config_data.get("delay_between_requests", 1.5))
        if hasattr(self, 'account_manager'):
            self.account_manager.refresh_accounts_list()

    def save_config(self):
        self.config_data["discord_webhook_url"] = self.webhook_var.get().strip()
        self.config_data["num_threads"] = self.threads_var.get()
        self.config_data["delay_between_requests"] = self.delay_var.get()
        # Accounts are already updated in self.config_data by AccountManager

        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config_data, f, indent=4)
            messagebox.showinfo("Saved", "Configuration saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")

    def reload_config(self):
        self.load_config() # This will also update GUI vars and refresh list
        self.console_logger.log("Config reloaded.", new=True)

    def start_workers(self):
        if self.stop_event.is_set():
            self.stop_event.clear()

        webhook = self.webhook_var.get().strip()
        if not webhook:
            messagebox.showwarning("Missing Webhook", "Please enter Discord webhook URL.")
            return
        if not self.config_data["accounts"]:
            messagebox.showwarning("No accounts", "Add at least one account.")
            return

        self.save_config()

        self.stop_event.clear()
        self.workers.clear()
        self.console_logger.clear_console()

        base_delay = self.delay_var.get()
        num_threads = self.threads_var.get()

        for acc_id, acc_data in self.config_data["accounts"].items():
            worker = RequestWorker(acc_id, acc_data, webhook, num_threads, base_delay, self.console_logger.log, self.stop_event)
            self.workers.append(worker)
            worker.start()

        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.console_logger.log("Started all workers.\n", new=True)

        threading.Thread(target=self.monitor_workers, daemon=True).start()

    def stop_workers(self):
        self.console_logger.log("\nStopping all workers...")
        self.stop_event.set()
        for worker in self.workers:
            if worker.is_alive():
                 worker.join()
        self.console_logger.log("All workers stopped.\n", new=True)
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    def monitor_workers(self):
        while any(w.is_alive() for w in self.workers):
            time.sleep(0.5)
        if not self.stop_event.is_set(): 
            self.console_logger.log("\nAll workers completed their tasks (either success or all codes tried).\n", new=True)
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

# The following methods are now part of AccountManager or ConsoleLogger
# def output(self, msg, new=False, replace=False): ...
# def add_account_dialog(self): ...
# def edit_account_dialog(self): ...
# def remove_selected_account(self): ...
# def refresh_accounts_list(self): ...


