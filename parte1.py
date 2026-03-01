import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt


def evaluar_lagrange(xn, yn, x):
    n = len(xn)
    resultado = 0.0
    for i in range(n):
        Li = 1.0
        for j in range(n):
            if j != i:
                Li *= (x - xn[j]) / (xn[i] - xn[j])
        resultado += yn[i] * Li
    return resultado


def interpolante_por_trozos(nodos_dict, divisiones, a, b):
    limites = [a] + sorted(divisiones) + [b]
    num_tramos = len(limites) - 1

    nodos_prep = {}
    for k in range(num_tramos):
        if k not in nodos_dict or len(nodos_dict[k]) < 2:
            return None
        nodos_prep[k] = list(nodos_dict[k])

    for idx, d in enumerate(divisiones):
        k_izq = idx
        k_der = idx + 1
        ancho_min = min(limites[k_izq+1] - limites[k_izq],
                        limites[k_der+1] - limites[k_der])
        tol = 0.12 * ancho_min

        nodo_frontera = None

        for i, (x, y) in enumerate(nodos_prep[k_izq]):
            if abs(x - d) <= tol:
                nodos_prep[k_izq][i] = (d, y)
                nodo_frontera = (d, y)
                break

        if nodo_frontera is None:
            for i, (x, y) in enumerate(nodos_prep[k_der]):
                if abs(x - d) <= tol:
                    nodos_prep[k_der][i] = (d, y)
                    nodo_frontera = (d, y)
                    break

        if nodo_frontera is not None:
            ya_en_izq = any(abs(p[0] - d) < 1e-10 for p in nodos_prep[k_izq])
            ya_en_der = any(abs(p[0] - d) < 1e-10 for p in nodos_prep[k_der])
            if not ya_en_izq:
                nodos_prep[k_izq].append(nodo_frontera)
            if not ya_en_der:
                nodos_prep[k_der].append(nodo_frontera)
        else:
            pts_izq = sorted(nodos_prep[k_izq], key=lambda p: p[0])
            xn_tmp = np.array([p[0] for p in pts_izq])
            yn_tmp = np.array([p[1] for p in pts_izq])
            xc = max(xn_tmp[0], min(d, xn_tmp[-1]))
            y_virtual = evaluar_lagrange(xn_tmp, yn_tmp, xc)
            nodos_prep[k_izq].append((d, y_virtual))
            nodos_prep[k_der].append((d, y_virtual))

    trozos = []
    for k in range(num_tramos):
        puntos = nodos_prep[k]
        xn = np.array([p[0] for p in puntos])
        yn = np.array([p[1] for p in puntos])
        orden = np.argsort(xn)
        trozos.append((limites[k], limites[k+1], xn[orden], yn[orden]))

    def f(x):
        for ak, bk, xn, yn in trozos:
            if ak - 1e-10 <= x <= bk + 1e-10:
                xc = max(xn[0], min(x, xn[-1]))
                return evaluar_lagrange(xn, yn, xc)
        xn, yn = trozos[-1][2], trozos[-1][3]
        xc = max(xn[0], min(x, xn[-1]))
        return evaluar_lagrange(xn, yn, xc)

    return f


def simpson(f, a, b, n=200):
    if n % 2 != 0:
        n += 1
    h = (b - a) / n
    x = np.linspace(a, b, n + 1)
    y = np.array([f(xi) for xi in x])
    return h / 3.0 * (y[0] + y[-1] + 4.0 * np.sum(y[1:-1:2]) + 2.0 * np.sum(y[2:-2:2]))


def area_entre_curvas(f, g, a, b, n=200):
    return simpson(lambda x: abs(f(x) - g(x)), a, b, n)


class AppParte1:

    def __init__(self, master):
        self.master = master
        master.title("Parte 1 - Area entre curvas (funciones)")
        master.geometry("1150x650")
        master.resizable(True, True)

        self.imagen_pil = None
        self.imagen_tk = None
        self.img_w = 0
        self.img_h = 0
        self.offset_x = 0
        self.offset_y = 0

        self.a, self.b = 0.0, 10.0
        self.c, self.d = 0.0, 10.0

        self.nodos_f = {}
        self.nodos_g = {}
        self.f_interp = None
        self.g_interp = None

        self._crear_panel()
        self._crear_canvas()

    def _crear_panel(self):
        panel = tk.Frame(self.master, width=280)
        panel.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)
        panel.pack_propagate(False)

        tk.Button(panel, text="Cargar imagen", command=self._cargar_imagen).pack(fill=tk.X, pady=3)

        sep1 = tk.Frame(panel, height=2, bg="gray70")
        sep1.pack(fill=tk.X, pady=6)

        tk.Label(panel, text="Limites del dominio", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        fr_lim = tk.Frame(panel)
        fr_lim.pack(fill=tk.X, pady=2)

        self.entries_lim = {}
        for i, (nombre, valor) in enumerate([("a", "0"), ("b", "10"), ("c", "0"), ("d", "10")]):
            tk.Label(fr_lim, text=f"{nombre}=").grid(row=i//2, column=(i%2)*2, sticky=tk.E)
            e = tk.Entry(fr_lim, width=8)
            e.grid(row=i//2, column=(i%2)*2+1, padx=2, pady=1)
            e.insert(0, valor)
            self.entries_lim[nombre] = e

        tk.Button(panel, text="Fijar limites", command=self._fijar_limites).pack(fill=tk.X, pady=3)

        sep2 = tk.Frame(panel, height=2, bg="gray70")
        sep2.pack(fill=tk.X, pady=6)

        tk.Label(panel, text="Curva activa", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        self.var_curva = tk.StringVar(value="f")
        fr_curva = tk.Frame(panel)
        fr_curva.pack(fill=tk.X)
        tk.Radiobutton(fr_curva, text="f (azul)", variable=self.var_curva,
                        value="f", fg="blue").pack(side=tk.LEFT)
        tk.Radiobutton(fr_curva, text="g (verde)", variable=self.var_curva,
                        value="g", fg="#008040").pack(side=tk.LEFT)

        sep3 = tk.Frame(panel, height=2, bg="gray70")
        sep3.pack(fill=tk.X, pady=6)

        tk.Label(panel, text="Divisiones de [a,b]", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        tk.Label(panel, text="Para f (ej: 3.5, 7):").pack(anchor=tk.W)
        self.entry_div_f = tk.Entry(panel, width=22)
        self.entry_div_f.pack(fill=tk.X, pady=1)
        tk.Label(panel, text="Para g (ej: 5):").pack(anchor=tk.W)
        self.entry_div_g = tk.Entry(panel, width=22)
        self.entry_div_g.pack(fill=tk.X, pady=1)

        tk.Label(panel, text="Subintervalo activo:", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(6,0))
        self.var_subint = tk.IntVar(value=0)
        fr_sub = tk.Frame(panel)
        fr_sub.pack(fill=tk.X)
        for i in range(3):
            tk.Radiobutton(fr_sub, text=f"Tramo {i}", variable=self.var_subint,
                            value=i).pack(side=tk.LEFT)

        sep4 = tk.Frame(panel, height=2, bg="gray70")
        sep4.pack(fill=tk.X, pady=6)

        tk.Button(panel, text="Deshacer ultimo nodo",
                  command=self._deshacer).pack(fill=tk.X, pady=2)
        tk.Button(panel, text="Limpiar curva activa",
                  command=self._limpiar).pack(fill=tk.X, pady=2)

        sep5 = tk.Frame(panel, height=2, bg="gray70")
        sep5.pack(fill=tk.X, pady=6)

        tk.Button(panel, text="CALCULAR AREA", command=self._calcular,
                  bg="#2E7D32", fg="white", font=("Arial", 10, "bold")).pack(fill=tk.X, pady=4)

        self.lbl_resultado = tk.Label(panel, text="Area: ---",
                                       font=("Arial", 11, "bold"), fg="#1565C0")
        self.lbl_resultado.pack(pady=4)

        tk.Button(panel, text="Ver graficas",
                  command=self._mostrar_graficas).pack(fill=tk.X, pady=2)

        self.lbl_info = tk.Label(panel, text="", font=("Arial", 8), fg="gray40")
        self.lbl_info.pack(side=tk.BOTTOM, pady=4)

    def _crear_canvas(self):
        self.canvas = tk.Canvas(self.master, bg="#2b2b2b")
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.canvas.bind("<Button-1>", self._click)
        self.canvas.bind("<Motion>", self._movimiento)

    # ---- IMAGEN ----

    def _cargar_imagen(self):
        ruta = filedialog.askopenfilename(
            filetypes=[("Imagenes", "*.png *.jpg *.jpeg *.bmp *.gif")])
        if not ruta:
            return

        img = Image.open(ruta)
        self.master.update_idletasks()
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 50:
            cw, ch = 800, 600

        ratio = min(cw / img.width, ch / img.height, 1.0)
        self.img_w = int(img.width * ratio)
        self.img_h = int(img.height * ratio)
        img = img.resize((self.img_w, self.img_h), Image.LANCZOS)

        self.offset_x = (cw - self.img_w) // 2
        self.offset_y = (ch - self.img_h) // 2

        self.imagen_pil = img
        self.imagen_tk = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.create_image(self.offset_x, self.offset_y,
                                  anchor=tk.NW, image=self.imagen_tk, tags="img")

    def _pixel_a_coord(self, px, py):
        x = self.a + (px - self.offset_x) / self.img_w * (self.b - self.a)
        y = self.d - (py - self.offset_y) / self.img_h * (self.d - self.c)
        return x, y

    def _coord_a_pixel(self, x, y):
        px = self.offset_x + (x - self.a) / (self.b - self.a) * self.img_w
        py = self.offset_y + (self.d - y) / (self.d - self.c) * self.img_h
        return px, py

    def _fijar_limites(self):
        try:
            self.a = float(self.entries_lim["a"].get())
            self.b = float(self.entries_lim["b"].get())
            self.c = float(self.entries_lim["c"].get())
            self.d = float(self.entries_lim["d"].get())
            messagebox.showinfo("Listo", f"Dominio: [{self.a}, {self.b}] x [{self.c}, {self.d}]")
        except ValueError:
            messagebox.showerror("Error", "Ingrese valores numericos validos")

    def _click(self, event):
        if self.imagen_pil is None:
            return
        x, y = self._pixel_a_coord(event.x, event.y)
        if x < self.a or x > self.b or y < self.c or y > self.d:
            return

        curva = self.var_curva.get()
        subint = self.var_subint.get()
        nodos = self.nodos_f if curva == "f" else self.nodos_g

        if subint not in nodos:
            nodos[subint] = []
        nodos[subint].append((x, y))
        self._redibujar_nodos()

    def _deshacer(self):
        curva = self.var_curva.get()
        subint = self.var_subint.get()
        nodos = self.nodos_f if curva == "f" else self.nodos_g
        if subint in nodos and nodos[subint]:
            nodos[subint].pop()
        self._redibujar_nodos()

    def _limpiar(self):
        curva = self.var_curva.get()
        if curva == "f":
            self.nodos_f.clear()
        else:
            self.nodos_g.clear()
        self._redibujar_nodos()

    def _redibujar_nodos(self):
        self.canvas.delete("nodo")
        pares = [("f", self.nodos_f, "#4488FF"), ("g", self.nodos_g, "#00CC66")]
        for nombre, nodos, color in pares:
            for subint, puntos in nodos.items():
                for (x, y) in puntos:
                    px, py = self._coord_a_pixel(x, y)
                    r = 4
                    self.canvas.create_oval(px-r, py-r, px+r, py+r,
                                            fill=color, outline="white", width=1, tags="nodo")
                    self.canvas.create_text(px+10, py-10,
                                            text=f"({x:.2f}, {y:.2f})",
                                            fill=color, font=("Consolas", 7), tags="nodo")

    def _movimiento(self, event):
        if self.imagen_pil is None:
            return
        x, y = self._pixel_a_coord(event.x, event.y)
        self.lbl_info.config(text=f"x = {x:.3f}   y = {y:.3f}")

    def _parsear_divisiones(self, entry):
        texto = entry.get().strip()
        if not texto:
            return []
        return sorted([float(v.strip()) for v in texto.split(",")])

    def _calcular(self):
        try:
            div_f = self._parsear_divisiones(self.entry_div_f)
            div_g = self._parsear_divisiones(self.entry_div_g)
        except ValueError:
            messagebox.showerror("Error", "Formato de divisiones invalido")
            return

        self.f_interp = interpolante_por_trozos(self.nodos_f, div_f, self.a, self.b)
        self.g_interp = interpolante_por_trozos(self.nodos_g, div_g, self.a, self.b)

        if self.f_interp is None:
            messagebox.showerror("Error",
                "Faltan nodos en algun tramo de f (minimo 2 por tramo)")
            return
        if self.g_interp is None:
            messagebox.showerror("Error",
                "Faltan nodos en algun tramo de g (minimo 2 por tramo)")
            return

        area = area_entre_curvas(self.f_interp, self.g_interp, self.a, self.b)
        self.lbl_resultado.config(text=f"Area ≈ {area:.6f}")

    def _mostrar_graficas(self):
        if self.f_interp is None or self.g_interp is None:
            messagebox.showinfo("", "Primero calcule el area")
            return

        xs = np.linspace(self.a, self.b, 500)
        yf = np.array([self.f_interp(x) for x in xs])
        yg = np.array([self.g_interp(x) for x in xs])

        fig, ax = plt.subplots(figsize=(9, 5))
        ax.plot(xs, yf, color="#4488FF", linewidth=2, label="f interpolada")
        ax.plot(xs, yg, color="#00CC66", linewidth=2, label="g interpolada")
        ax.fill_between(xs, yf, yg, alpha=0.25, color="orange", label="Area")

        for nombre, nodos, color in [("f", self.nodos_f, "#4488FF"),
                                      ("g", self.nodos_g, "#00CC66")]:
            for subint, puntos in nodos.items():
                xp = [p[0] for p in puntos]
                yp = [p[1] for p in puntos]
                ax.plot(xp, yp, "o", color=color, markersize=5)

        try:
            div_f = self._parsear_divisiones(self.entry_div_f)
        except ValueError:
            div_f = []
        try:
            div_g = self._parsear_divisiones(self.entry_div_g)
        except ValueError:
            div_g = []

        divisiones_todas = sorted(set(div_f + div_g))
        for d in divisiones_todas:
            ax.axvline(x=d, color="#FF6600", linewidth=1, linestyle="--", alpha=0.6)
            yf_d = self.f_interp(d)
            yg_d = self.g_interp(d)
            ax.plot(d, yf_d, "D", color="#FF6600", markersize=6, zorder=5)
            ax.plot(d, yg_d, "D", color="#FF6600", markersize=6, zorder=5)

        if divisiones_todas:
            ax.plot([], [], "D", color="#FF6600", markersize=6, label="Divisiones")

        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    ventana = tk.Tk()
    app = AppParte1(ventana)
    ventana.mainloop()
