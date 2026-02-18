import tkinter as tk
from tkinter import ttk, messagebox
import math
import matplotlib.pyplot as plt

VT_DEFAULT = 0.0259


# -------------------------
# Models
# -------------------------

def constant_voltage_model(Vs, R, Vd_const):
    I = (Vs - Vd_const) / R
    if I < 0:
        return Vs, 0
    return Vd_const, I


def linear_model(Vs, R, Vg, rd):
    I = (Vs - Vg) / (R + rd)
    if I < 0:
        return Vs, 0
    Vd = Vg + I * rd
    return Vd, I


def iterative_model(Vs, R, Is, n, Vt, Vd_guess=0.7):

    Vd = Vd_guess
    for _ in range(100):

        I = (Vs - Vd) / R
        if I <= 0:
            return Vs, 0

        new_Vd = n * Vt * math.log(I / Is)

        if abs(new_Vd - Vd) < 1e-6:
            break

        Vd = new_Vd

    I = (Vs - Vd) / R
    return Vd, I


# -------------------------
# GUI
# -------------------------

class DiodeApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Diode Analysis Tool - powered by Nhyirax")
        self.root.state("zoomed")  # full screen

        self.model = tk.StringVar(value="constant")

        self.setup_style()
        self.build_ui()

    # -------------------------

    def setup_style(self):

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background="#0f172a")
        style.configure("TLabel", background="#0f172a",
                        foreground="white", font=("Segoe UI", 12))

        style.configure("Header.TLabel",
                        font=("Segoe UI", 22, "bold"),
                        foreground="#38bdf8")

        style.configure("Card.TFrame",
                        background="#1e293b",
                        relief="flat")

        style.configure("TButton",
                        font=("Segoe UI", 12, "bold"),
                        padding=10)

        style.map("TButton",
                  background=[("active", "#38bdf8")])

    # -------------------------

    def build_ui(self):

        main = ttk.Frame(self.root)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        ttk.Label(main,
                  text="Real Diode Analysis",
                  style="Header.TLabel").pack(pady=10)

        content = ttk.Frame(main)
        content.pack(fill="both", expand=True)

        # LEFT PANEL
        left = ttk.Frame(content, style="Card.TFrame", padding=20)
        left.pack(side="left", fill="both", expand=True, padx=10)

        ttk.Label(left, text="Model Selection",
                  font=("Segoe UI", 16, "bold")).pack(pady=10)

        for text, val in [
            ("Constant Voltage Model", "constant"),
            ("Linear Model", "linear"),
            ("Iterative (Exponential) Model", "iterative")
        ]:
            ttk.Radiobutton(left, text=text,
                            variable=self.model,
                            value=val).pack(anchor="w", pady=5)

        # INPUT GRID
        self.entries = {}

        fields = [
            "Supply Voltage Vs (V)",
            "Series Resistance R (ohm)",
            "Constant Vd (V)",
            "Threshold Vγ (V)",
            "Dynamic rd (ohm)",
            "Is (A)",
            "n",
            "Thermal Voltage Vt (V)"
        ]

        form = ttk.Frame(left, style="Card.TFrame")
        form.pack(pady=20)

        for i, name in enumerate(fields):
            ttk.Label(form, text=name).grid(row=i, column=0, sticky="w", pady=6)
            e = ttk.Entry(form, width=18, font=("Segoe UI", 12))
            e.grid(row=i, column=1, padx=10)
            self.entries[name] = e

        self.entries["Thermal Voltage Vt (V)"].insert(0, str(VT_DEFAULT))
        self.entries["Constant Vd (V)"].insert(0, "0.7")
        self.entries["Threshold Vγ (V)"].insert(0, "0.7")

        # BUTTONS
        btn_frame = ttk.Frame(left)
        btn_frame.pack(pady=15)

        ttk.Button(btn_frame, text="Compute",
                   command=self.compute).grid(row=0, column=0, padx=10)

        ttk.Button(btn_frame, text="Plot Operating Point",
                   command=self.plot_point).grid(row=0, column=1, padx=10)

        # RIGHT PANEL — OUTPUT
        right = ttk.Frame(content, style="Card.TFrame", padding=20)
        right.pack(side="right", fill="both", expand=True, padx=10)

        ttk.Label(right, text="Results",
                  font=("Segoe UI", 16, "bold")).pack(pady=10)

        self.output = tk.Text(right,
                              font=("Consolas", 13),
                              bg="#020617",
                              fg="#e2e8f0",
                              insertbackground="white",
                              height=20)
        self.output.pack(fill="both", expand=True)

    # -------------------------

    def get(self, key, default=None):
        v = self.entries[key].get()
        if v == "":
            return default
        return float(v)

    # -------------------------

    def compute(self):

        try:
            Vs = self.get("Supply Voltage Vs (V)")
            R = self.get("Series Resistance R (ohm)")

            if self.model.get() == "constant":
                Vd, I = constant_voltage_model(
                    Vs, R, self.get("Constant Vd (V)", 0.7))

            elif self.model.get() == "linear":
                Vd, I = linear_model(
                    Vs, R,
                    self.get("Threshold Vγ (V)", 0.7),
                    self.get("Dynamic rd (ohm)", 10))

            else:
                Vd, I = iterative_model(
                    Vs, R,
                    self.get("Is (A)", 1e-12),
                    self.get("n", 2),
                    self.get("Thermal Voltage Vt (V)", VT_DEFAULT))

            self.last_Vd = Vd
            self.last_I = I

            self.output.delete("1.0", tk.END)
            self.output.insert(tk.END,
                               f"Diode Voltage : {Vd:.6f} V\n"
                               f"Diode Current : {I:.6e} A\n"
                               f"Power Dissipation : {Vd*I:.6f} W\n")

        except Exception:
            messagebox.showerror("Error", "Invalid input values")

    # -------------------------

    def plot_point(self):

        if not hasattr(self, "last_I"):
            messagebox.showinfo("Info", "Run Compute first")
            return

        plt.figure()
        plt.scatter(self.last_Vd, self.last_I)
        plt.xlabel("Diode Voltage (V)")
        plt.ylabel("Diode Current (A)")
        plt.title("Operating Point")
        plt.show()


# -------------------------
# Run
# -------------------------

root = tk.Tk()
app = DiodeApp(root)
root.mainloop()
