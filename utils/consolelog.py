import tkinter as tk
from threading import Lock

class ConsoleLogger:
    def __init__(self, output_console_widget, output_lock: Lock):
        self.output_console = output_console_widget
        self.output_lock = output_lock

    def log(self, msg, new=False, replace=False):
        with self.output_lock:
            self.output_console.configure(state="normal")
            self.output_console.insert("end", msg + "\n")
            self.output_console.see("end")
            self.output_console.configure(state="disabled")


    def clear_console(self):
        with self.output_lock:
            self.output_console.configure(state="normal")
            self.output_console.delete("1.0", "end")
            self.output_console.configure(state="disabled")
