import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import math
import sympy as sp
from functools import partial
import matplotlib.pyplot as plt
import numpy as np
import re

class ScientificCalculator:
    def __init__(self, master):
        self.master = master
        master.title("Scientific Calculator")
        master.geometry("1050x700")
        self.theme = "dark"
        self.expression = ""
        self.input_text = tk.StringVar()

        self.bg_dark = "#1e1e2e"
        self.bg_light = "#ffffff"
        self.fg_light = "#ffffff"
        self.fg_dark = "#000000"
        self.accent_color = "#00bcd4"
        self.last_result = None
        self.should_clear_on_next_input = False 

        master.configure(bg=self.bg_dark)
        master.rowconfigure(0, weight=1)
        master.columnconfigure(1, weight=1)
        master.columnconfigure(2, weight=2)

        self.sidebar_frame = tk.Frame(master, bg="#2e2e2e", width=200)
        self.sidebar_frame.pack(side='left', fill='y')
        self.theme_btn = tk.Button(self.sidebar_frame, text="⛅ Toggle Theme",
                                   bg=self.accent_color, fg=self.fg_light, relief="ridge",
                                   font=("Arial", 12, "bold"), bd=0,
                                   anchor="w", padx=20,
                                   command=self.toggle_theme)
        self.theme_btn.pack(fill="x", pady=(8,4), padx=0)
        self.sidebar_items = [
            "\U0001F4C8 Graphique", "\U0001F4E6 Volume", "\U0001F4CF Longueur", "\u2696\ufe0f Poids",
            "🌡Température", 
            "\u26a1 Énergie", "\U0001F9F1 Surface", "\U0001F680 Vitesse",
            "\u23F0 Heure", "\U0001F4BE Données", "\U0001F4CA Pression", "\U0001F50C Puissance"
        ]
        for name in self.sidebar_items:
            btn = tk.Button(self.sidebar_frame, text=name, bg="#2e2e2e", fg="white",
                            bd=0, anchor="w", padx=20, font=("Arial", 12),
                            command=partial(self.sidebar_action, name))
            btn.pack(fill="x", pady=2)

        right_frame = tk.Frame(master, bg=self.bg_dark)
        right_frame.pack(side="right", fill="both", expand=True)
        right_frame.rowconfigure(0, weight=0)
        right_frame.rowconfigure(1, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.columnconfigure(1, weight=1)

        self.input_frame = tk.Frame(right_frame, height=54, bg=self.bg_dark)
        self.input_frame.grid(row=0, column=0, sticky="ew", columnspan=2)
        self.input_frame.columnconfigure(0, weight=1)
        self.input_field = tk.Entry(
            self.input_frame, font=('arial', 20, 'bold'),
            textvariable=self.input_text, width=35,
            bg="#2e2e3e", fg=self.fg_light,
            bd=0, justify="right"
        )
        self.input_field.grid(row=0, column=0, ipady=10, padx=15, pady=9, sticky="ew")

        self.history = tk.Text(right_frame, width=10, bg="#2e2e3e", fg=self.fg_light, state='disabled')
        self.history.grid(row=1, column=1, sticky="nswe", padx=(4,6), pady=(0,3))

        calc_frame = tk.Frame(right_frame, bg=self.bg_dark)
        calc_frame.grid(row=1, column=0, sticky="nswe", padx=(0,6), pady=(0,3))
        calc_frame.rowconfigure(0, weight=1)
        calc_frame.columnconfigure(0, weight=1)
        canvas = tk.Canvas(calc_frame, bg=self.bg_dark, highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar = ttk.Scrollbar(calc_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=v_scrollbar.set)
        v_scrollbar.pack(side="right", fill="y")
        self.scrollable_frame = tk.Frame(canvas, bg=self.bg_dark)
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        self.section_map = {}
        self.create_section("Trigonometry", ['sin', 'cos', 'tan', 'sinh', 'cosh', 'tanh'])
        self.create_section("Advanced Math", ['∂f(x)', '∫f(x)', 'fact', 'sqrt', 'exp', 'log', 'ln'])
        self.create_section("Constants & Other", ['pi', 'e', 'floor', 'abs'])
        self.create_section("Conversions", ['bin/oct/hex'])

        self.create_basic_calculator()

        master.bind('<Return>', lambda event: self.on_click('='))
        master.bind('<BackSpace>', lambda event: self.on_click('CE'))
        for key in '0123456789+-*/().':
            master.bind(key, lambda event, ch=key: self.on_click(ch))

    def create_section(self, title, functions, buttons_per_row=6):
        btn = tk.Button(self.scrollable_frame, text=f"\u25B6 {title}",
                        bg=self.accent_color, fg=self.fg_light, relief="flat", anchor="w", font=("Arial", 12, "bold"),
                        command=partial(self.toggle_section, title))
        btn.pack(fill="x", padx=10, pady=2)
        frame = tk.Frame(self.scrollable_frame, bg=self.bg_dark)
        setattr(self, f"{title}_frame", frame)
        self.section_map[title] = frame
        if title == "Conversions":
            convert_btn = tk.Button(frame, text="Binary/Octal/Hex Converter", width=24, height=2,
                                    bg="#333344", fg=self.fg_light, relief="flat",
                                    command=self.open_bin_oct_hex_converter)
            convert_btn.pack(padx=10, pady=4, fill="x")
        else:
            for i, func in enumerate(functions):
                if i % buttons_per_row == 0:
                    row = tk.Frame(frame, bg=self.bg_dark)
                    row.pack(pady=2)
                tk.Button(row, text=func, width=8, height=2,
                          bg="#333344", fg=self.fg_light, relief="flat",
                          command=lambda f=func: self.on_click(f)).pack(side="left", padx=5)
        frame.pack_forget()

    def create_basic_calculator(self):
        frame = tk.Frame(self.scrollable_frame, bg=self.bg_dark)
        frame.pack(pady=20, fill="both", expand=True)
        center_wrapper = tk.Frame(frame, bg=self.bg_dark)
        center_wrapper.grid(row=0, column=0)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        calc_buttons = [
            ['7', '8', '9', '/', 'C','('],
            ['4', '5', '6', '*', 'CE',')'],
            ['1', '2', '3', '-', 'ans'],
            ['.', '0', '=', '+']
        ]
        for r, row_vals in enumerate(calc_buttons):
            for c, val in enumerate(row_vals):
                btn = tk.Button(center_wrapper, text=val, width=6, height=2,
                                bg="#333344", fg=self.fg_light, relief="flat",
                                font=("Arial", 14, "bold"),
                                command=lambda v=val: self.on_click(v))
                btn.grid(row=r, column=c, padx=8, pady=8)

    def toggle_section(self, section_name):
        frame = self.section_map[section_name]
        if frame.winfo_ismapped():
            frame.pack_forget()
        else:
            frame.pack(fill="x", padx=20)

    def sidebar_action(self, name):
        if "Graphique" in name:
            self.open_graph_window()
        elif "Longueur" in name:
            self.open_conversion_window("length")
        elif "Volume" in name:
            self.open_conversion_window("volume")
        elif "Poids" in name:
            self.open_conversion_window("weight")
        elif "Température" in name:
            self.open_conversion_window("temperature")
        elif "Énergie" in name:
            self.open_conversion_window("energy")
        elif "Surface" in name:
            self.open_conversion_window("area")
        elif "Vitesse" in name:
            self.open_conversion_window("speed")
        elif "Heure" in name:
            self.open_conversion_window("time")
        elif "Données" in name:
            self.open_conversion_window("data")
        elif "Pression" in name:
            self.open_conversion_window("pressure")
        elif "Puissance" in name:
            self.open_conversion_window("power")
        else:
            self.input_text.set(f"{name} coming soon...")

    def toggle_theme(self):
        if self.theme == "light":
            self.theme = "dark"
            bg = self.bg_dark
            fg = self.fg_light
            screen_bg = "#2e2e3e"
            sidebar_bg = "#2e2e2e"
        else:
            self.theme = "light"
            bg = self.bg_light
            fg = self.fg_dark
            screen_bg = "#eeeeee"
            sidebar_bg = "#e0e0e0"
        self.master.configure(bg=bg)
        self.input_frame.configure(bg=bg)
        self.input_field.configure(bg=screen_bg, fg=fg)
        self.history.configure(bg=bg, fg=fg)
        self.theme_btn.configure(bg=self.accent_color, fg=self.fg_light)
        for idx, btnname in enumerate(self.section_map):
            btn = self.scrollable_frame.winfo_children()[idx]
            btn.configure(bg=self.accent_color, fg=self.fg_light, anchor="w")
        self.sidebar_frame.configure(bg=sidebar_bg)
        for child in self.sidebar_frame.winfo_children():
            if isinstance(child, tk.Button):
                child.configure(bg=sidebar_bg, fg=fg, anchor="w", padx=20)
        for widget in self.scrollable_frame.winfo_children():
            if isinstance(widget, (tk.Button, tk.LabelFrame, tk.Frame)):
                try:
                    widget.configure(bg=bg, fg=fg)
                except:
                    pass
            for child in widget.winfo_children():
                if isinstance(child, tk.Button):
                    child.configure(bg=bg, fg=self.fg_light if bg == self.bg_dark else fg)

    def open_graph_window(self):
        graph_win = tk.Toplevel(self.master)
        graph_win.title("Tracer une fonction")
        graph_win.geometry("420x170")
        tk.Label(graph_win, text="Entrez une fonction f(x):").pack(pady=5)
        func_entry = tk.Entry(graph_win, width=40)
        func_entry.pack(pady=5)

        def plot():
            user_input = func_entry.get().replace('^', '**')

            user_input = re.sub(r'\bln\s*\(', '@L#N@(', user_input)
            user_input = re.sub(r'\blog\s*\(', '@L#O#G@(', user_input)
            user_input = re.sub(r'\bexp\s*\(', '@E#X#P@(', user_input)

            user_input = re.sub(r'\bsqrt\s*\(', 'np.sqrt(', user_input)
            user_input = re.sub(r'\bsin\s*\(', 'np.sin(', user_input)
            user_input = re.sub(r'\bcos\s*\(', 'np.cos(', user_input)
            user_input = re.sub(r'\btan\s*\(', 'np.tan(', user_input)
            user_input = re.sub(r'\bsinh\s*\(', 'np.sinh(', user_input)
            user_input = re.sub(r'\bcosh\s*\(', 'np.cosh(', user_input)
            user_input = re.sub(r'\btanh\s*\(', 'np.tanh(', user_input)
            user_input = re.sub(r'\babs\s*\(', 'np.abs(', user_input)
            user_input = re.sub(r'\bpi\b', 'np.pi', user_input)
            user_input = re.sub(r'\be\b', 'np.e', user_input)

            user_input = user_input.replace('@L#N@(', 'np.log(')
            user_input = user_input.replace('@L#O#G@(', 'np.log10(')
            user_input = user_input.replace('@E#X#P@(', 'np.exp(')

            
            print("TO EVAL:", user_input)

            
            if re.search(r'np\.log10\(|np\.log\(', user_input):
                x = np.linspace(0.001, 10, 400)
            elif re.search(r'np\.sqrt\(', user_input):
                x = np.linspace(0, 10, 400)
            else:
                x = np.linspace(-10, 10, 400)
            try:
                context = {"np": np, "x": x}
                y = eval(user_input, {"__builtins__": {}}, context)
                y = np.array(y)
                valid = np.isfinite(y)
                if not np.any(valid):
                    messagebox.showinfo("Domaine invalide", "Aucune valeur valide à tracer (essayez une autre fonction ou domaine)")
                    return
                plt.figure("Graphique de f(x)")
                plt.clf()
                plt.plot(x[valid], y[valid], label=f"f(x) = {func_entry.get()}")
                plt.axhline(0, color='black', linewidth=0.5)
                plt.axvline(0, color='black', linewidth=0.5)
                plt.grid(True)
                plt.legend()
                plt.xlabel("x")
                plt.ylabel("f(x)")
                plt.tight_layout()
                plt.show()
            except Exception as e:
                messagebox.showerror(
                    "Erreur",
                    "Fonction invalide: {}\n\nExemples valides:\nx**2, sin(x), ln(x), exp(x), sqrt(x)\n\nError: {}".format(str(e))
                )


        tk.Button(graph_win, text="Afficher", command=plot).pack(pady=10)

    def open_conversion_window(self, conv_type):
        units = {
            "length": {"mètre": 1.0, "kilomètre": 1000.0, "centimètre": 0.01,
                       "pouce": 0.0254, "pied": 0.3048, "yard": 0.9144, "mile": 1609.34},
            "volume": {"litre": 1.0, "millilitre": 0.001, "gallon (US)": 3.78541,
                       "pinte (US)": 0.473176, "mètre cube": 1000.0},
            "weight": {"kilogramme": 1.0, "gramme": 0.001, "tonne": 1000.0,
                       "livre": 0.453592, "once": 0.0283495},
            "temperature": {"Celsius": None, "Fahrenheit": None, "Kelvin": None},
            "energy": {"joule": 1.0, "kilojoule": 1000.0, "calorie": 4.184,
                       "kilocalorie": 4184.0, "watt-heure": 3600.0, "kilowatt-heure": 3.6e6},
            "area": {"m²": 1.0, "cm²": 0.0001, "km²": 1e6, "pouce²": 0.00064516,
                     "pied²": 0.092903, "acre": 4046.86},
            "speed": {"m/s": 1.0, "km/h": 0.277778, "mph": 0.44704, "nœud": 0.514444},
            "time": {"seconde": 1.0, "minute": 60.0, "heure": 3600.0, "jour": 86400.0},
            "data": {
                "bit": 1.0,
                "octet": 8.0,
                "kilobit": 1e3,
                "kilobyte": 8e3,
                "megabit": 1e6,
                "megabyte": 8e6,
                "gigabit": 1e9,
                "gigabyte": 8e9,
                "terabit": 1e12,
                "terabyte": 8e12,
                "petabit": 1e15,
                "petabyte": 8e15,
                "exabit": 1e18,
                "exabyte": 8e18,
                "zettabit": 1e21,
                "zettabyte": 8e21,
                "yottabit": 1e24,
                "yottabyte": 8e24
            },
            "pressure": {"pascal": 1.0, "bar": 1e5, "atmosphère": 101325.0, "psi": 6894.76},
            "power": {"watt": 1.0, "kilowatt": 1000.0, "cheval vapeur": 735.5, "horsepower (US)": 745.7}
        }
        win = tk.Toplevel(self.master)
        win.title(f"Conversion de {conv_type.capitalize()}")
        win.geometry("400x250")
        tk.Label(win, text="Valeur :").pack(pady=5)
        val_entry = tk.Entry(win)
        val_entry.pack()
        tk.Label(win, text="De :").pack(pady=5)
        from_unit = ttk.Combobox(win, values=list(units[conv_type].keys()))
        from_unit.current(0)
        from_unit.pack()
        tk.Label(win, text="À :").pack(pady=5)
        to_unit = ttk.Combobox(win, values=list(units[conv_type].keys()))
        to_unit.current(1 if len(units[conv_type].keys()) > 1 else 0)
        to_unit.pack()
        result_label = tk.Label(win, text="", font=("Arial", 12))
        result_label.pack(pady=10)
        def convert():
            try:
                value = float(val_entry.get())
                from_u = from_unit.get()
                to_u = to_unit.get()
                if conv_type == "temperature":
                    result = self.convert_temperature(value, from_u, to_u)
                else:
                    base = value * units[conv_type][from_u]
                    result = base / units[conv_type][to_u]
                result_label.config(text=f"{value} {from_u} = {result:.4f} {to_u}")
            except Exception:
                result_label.config(text="Erreur de conversion.")
        tk.Button(win, text="Convertir", command=convert).pack(pady=10)

    def open_bin_oct_hex_converter(self):
        win = tk.Toplevel(self.master)
        win.title("Binary/Octal/Hex Converter")
        win.geometry("450x230")
        tk.Label(win, text="Valeur de départ :").pack(pady=5)
        val_entry = tk.Entry(win)
        val_entry.pack()
        tk.Label(win, text="Base de départ :").pack(pady=5)
        from_base = ttk.Combobox(win, values=["Binary", "Octal", "Decimal", "Hexadecimal"])
        from_base.current(2)
        from_base.pack()
        tk.Label(win, text="Base de sortie :").pack(pady=5)
        to_base = ttk.Combobox(win, values=["Binary", "Octal", "Decimal", "Hexadecimal"])
        to_base.current(0)
        to_base.pack()
        result_label = tk.Label(win, text="", font=("Arial", 12))
        result_label.pack(pady=10)
        def convert():
            try:
                value = val_entry.get().strip()
                if not value:
                    raise ValueError("Entrée vide")
                base_dict = {"Binary": 2, "Octal": 8, "Decimal": 10, "Hexadecimal": 16}
                f_base = base_dict[from_base.get()]
                t_base = base_dict[to_base.get()]
                dec_val = int(value, f_base)
                if t_base == 2:
                    out = bin(dec_val)
                elif t_base == 8:
                    out = oct(dec_val)
                elif t_base == 10:
                    out = str(dec_val)
                elif t_base == 16:
                    out = hex(dec_val)
                else:
                    out = str(dec_val)
                result_label.config(text=f"Résultat : {out}")
            except Exception as e:
                result_label.config(text=f"Erreur : {e}")
        tk.Button(win, text="Convertir", command=convert).pack(pady=10)

    def convert_temperature(self, value, from_unit, to_unit):
        if from_unit == to_unit:
            return value
        if from_unit == "Celsius":
            temp_c = value
        elif from_unit == "Fahrenheit":
            temp_c = (value - 32) * 5/9
        elif from_unit == "Kelvin":
            temp_c = value - 273.15
        else:
            raise ValueError("Unité inconnue")
        if to_unit == "Celsius":
            return temp_c
        elif to_unit == "Fahrenheit":
            return temp_c * 9/5 + 32
        elif to_unit == "Kelvin":
            return temp_c + 273.15
        else:
            raise ValueError("Unité inconnue")

    def add_to_history(self, expression, result):
        self.history.config(state='normal')
        self.history.insert('end', f"{expression} = {result}\n")
        self.history.config(state='disabled')
        self.history.see('end')

    def on_click(self, char):
        if self.should_clear_on_next_input and char not in ['=', 'ans', 'C', 'CE']:
            self.expression = ""
            self.input_text.set("")
            self.should_clear_on_next_input = False

        if char == '=':
            try:
                expr = self.expression
                
                expr = expr.replace('sinh', '@S!N#H@')
                expr = expr.replace('cosh', '@C!O#S#H@')
                expr = expr.replace('tanh', '@T!A#N#H@')
                expr = expr.replace('sin', '@S!I#N@')
                expr = expr.replace('cos', '@C!O#S@')
                expr = expr.replace('tan', '@T!A#N@')
                expr = re.sub(r'\bexp\s*\(', '@E#X#P@(', expr)

                
                expr = expr.replace('@S!N#H@', 'math.sinh')
                expr = expr.replace('@C!O#S#H@', 'math.cosh')
                expr = expr.replace('@T!A#N#H@', 'math.tanh')
                expr = expr.replace('@S!I#N@', 'math.sin')
                expr = expr.replace('@C!O#S@', 'math.cos')
                expr = expr.replace('@T!A#N@', 'math.tan')
                expr = expr.replace('@E#X#P@', 'math.exp')

                
                expr = expr.replace('sqrt', 'math.sqrt')
                expr = expr.replace('log', 'math.log10')
                expr = expr.replace('ln', 'math.log')
                expr = expr.replace('floor', 'math.floor')
                expr = expr.replace('abs', 'abs')
                expr = expr.replace('pi', str(math.pi))
                expr = re.sub(r'\be\b', str(math.e), expr)

                print('EXPR TO EVAL:', expr)
                result = eval(expr, {"math": math, "abs": abs})

                def is_very_close(val, tol=1e-8):
                        nearest = round(val)
                        return abs(val - nearest) < tol

                if isinstance(result, float) and is_very_close(result):
                        result = int(round(result)) 
                elif isinstance(result, float):
                    # Optionally, also round all floats to a certain precision for display
                    result = round(result, 8)      
                     
                def is_close(val, target, tol=1e-8):
                    return abs(val - target) < tol
                if is_close(result, 0.0):
                    result = 0.0
                elif is_close(result, 1.0):
                    result = 1.0
                elif is_close(result, -1.0):
                    result = -1.0

                self.last_result = result  
                self.input_text.set(str(result))
                self.add_to_history(self.expression, result)
                self.expression = str(result)
                self.should_clear_on_next_input = True
            except Exception as e:
                self.input_text.set(f"Error: {e}")
                self.expression = ""
                self.should_clear_on_next_input = False

        elif char == 'C':
            self.expression = ""
            self.input_text.set("")
            self.should_clear_on_next_input = False

        elif char == 'ans':
            if self.last_result is not None:
                self.expression += str(self.last_result)
                self.input_text.set(self.expression)

        elif char == 'CE':
            self.expression = self.expression[:-1]
            self.input_text.set(self.expression)

        elif char == 'exp':
            self.expression += 'exp'
            self.input_text.set(self.expression)

        elif char == '∂f(x)':
            func_str = simpledialog.askstring("Input", "Enter a function f(x):")
            x_val = simpledialog.askfloat("Input", "Enter a value for x:")
            try:
                x = sp.symbols('x')
                f = sp.sympify(func_str)
                df = sp.diff(f, x)
                result = df.subs(x, x_val)
                self.input_text.set(f"f'({x_val}) = {result}")
                self.expression = ""
                self.add_to_history(f"f'({x_val})", result)
            except Exception:
                self.input_text.set("Invalid input")
                self.expression = ""

        elif char == '∫f(x)':
            func_str = simpledialog.askstring("Input", "Enter a function f(x):")
            a = simpledialog.askfloat("Lower Bound", "Enter the lower bound:")
            b = simpledialog.askfloat("Upper Bound", "Enter the upper bound:")
            try:
                x = sp.symbols('x')
                f = sp.sympify(func_str)
                integral = sp.integrate(f, (x, a, b))
                self.input_text.set(f"∫[{a},{b}] = {integral}")
                self.expression = ""
                self.add_to_history(f"∫[{a},{b}] f(x)", integral)
            except Exception:
                self.input_text.set("Invalid input")
                self.expression = ""

        elif char == 'fact':
            try:
                val = int(eval(self.expression, {"math": math}))
                result = math.factorial(val)
                self.input_text.set(str(result))
                self.expression = str(result)
                self.add_to_history(f"{val}!", result)
            except Exception:
                self.input_text.set("Error")
                self.expression = ""

        else:
            self.expression += str(char)
            self.input_text.set(self.expression)


if __name__ == "__main__":
    root = tk.Tk()
    app = ScientificCalculator(root)
    root.mainloop()

