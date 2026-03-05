import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from scipy.interpolate import CubicSpline
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt


def preparar_nodos_unicos(xn, yn, tol=1e-10):
    # Ordena por x y fusiona abscisas repetidas promediando y
    pares = sorted(zip(np.asarray(xn, dtype=float), np.asarray(yn, dtype=float)), key=lambda p: p[0])
    x_uni, y_uni = [], []
    i = 0
    n = len(pares)
    while i < n:
        x0 = pares[i][0]
        ys = [pares[i][1]]
        j = i + 1
        while j < n and abs(pares[j][0] - x0) <= tol:
            ys.append(pares[j][1])
            j += 1
        x_uni.append(x0)
        y_uni.append(float(np.mean(ys)))
        i = j
    return np.array(x_uni, dtype=float), np.array(y_uni, dtype=float)


def simpson(f, a, b, n=200):
    # Regla de Simpson compuesta para integrar en [a,b]
    if n % 2 != 0:
        n += 1
    h = (b - a) / n
    x = np.linspace(a, b, n + 1)
    y = np.array([f(xi) for xi in x])
    return h / 3.0 * (y[0] + y[-1] + 4.0 * np.sum(y[1:-1:2]) + 2.0 * np.sum(y[2:-2:2]))


def area_entre_curvas(f, g, a, b, n=200):
    return simpson(lambda x: abs(f(x) - g(x)), a, b, n)


def construir_spline_natural(nodos_dom):
    # Interpolante por spline cubico natural
    if len(nodos_dom) < 2:
        return None, None

    x_raw = np.array([p[0] for p in nodos_dom], dtype=float)
    y_raw = np.array([p[1] for p in nodos_dom], dtype=float)
    x_uni, y_uni = preparar_nodos_unicos(x_raw, y_raw)

    if len(x_uni) < 2:
        return None, None

    x_min = float(x_uni[0])
    x_max = float(x_uni[-1])
    if x_max - x_min <= 1e-12:
        return None, None

    if len(x_uni) == 2:
        y0 = float(y_uni[0])
        y1 = float(y_uni[1])
        m = (y1 - y0) / (x_max - x_min)

        def f_lin(x):
            return y0 + m * (x - x_min)

        return f_lin, (x_min, x_max)

    spline = CubicSpline(x_uni, y_uni, bc_type="natural")

    def f_spline(x):
        return float(spline(x))

    return f_spline, (x_min, x_max)


def asignar_nodos_a_tramos(nodos_dom, limites, tol=1e-10):
    # Asigna nodos a cada tramo; un nodo en frontera se comparte entre tramos adyacentes
    nodos_dict = {k: [] for k in range(len(limites) - 1)}
    for x, y in nodos_dom:
        for k in range(len(limites) - 1):
            ak, bk = limites[k], limites[k + 1]
            if ak - tol <= x <= bk + tol:
                nodos_dict[k].append((x, y))
    return nodos_dict


def construir_interpolante_por_trozos_spline(nodos_dom, divisiones_dom, a, b):
    # Construye un interpolante por tramos
    if len(nodos_dom) < 2:
        return None, None, []

    xs = [x for x, _ in nodos_dom]
    x_min = min(xs)
    x_max = max(xs)
    if x_max - x_min <= 1e-12:
        return None, None, []

    divisiones_validas = sorted([d for d in divisiones_dom if x_min < d < x_max])
    limites = [x_min] + divisiones_validas + [x_max]
    nodos_dict = asignar_nodos_a_tramos(nodos_dom, limites)

    trozos = []
    for k in range(len(limites) - 1):
        ak, bk = limites[k], limites[k + 1]
        pts = nodos_dict[k]
        if len(pts) < 2:
            return None, None, divisiones_validas

        f_seg, rango_seg = construir_spline_natural(pts)
        if f_seg is None or rango_seg is None:
            return None, None, divisiones_validas
        x_lo, x_hi = rango_seg
        trozos.append((ak, bk, x_lo, x_hi, f_seg))

    def f(x):
        for ak, bk, x_lo, x_hi, f_seg in trozos:
            if ak - 1e-10 <= x <= bk + 1e-10 and x_lo - 1e-10 <= x <= x_hi + 1e-10:
                return f_seg(x)
        raise ValueError("x fuera de los tramos definidos por nodos")

    x_min = min(t[2] for t in trozos)
    x_max = max(t[3] for t in trozos)
    return f, (x_min, x_max), divisiones_validas


def area_entre_curvas_por_subintervalos(f, g, puntos_corte, n=200):
    # Integra |f-g| por cada subintervalo y acumula solo donde ambas curvas esten definidas
    area_total = 0.0
    n_usados = 0
    cortes = sorted(set(float(x) for x in puntos_corte))
    for i in range(len(cortes) - 1):
        ai, bi = cortes[i], cortes[i + 1]
        if bi - ai <= 1e-12:
            continue
        xs_probe = np.linspace(ai, bi, 41)
        valid_idx = []
        for k, x in enumerate(xs_probe):
            try:
                f(x)
                g(x)
                valid_idx.append(k)
            except Exception:
                pass

        if not valid_idx:
            continue

        li = float(xs_probe[valid_idx[0]])
        ri = float(xs_probe[valid_idx[-1]])
        if ri - li <= 1e-12:
            continue

        try:
            area_total += area_entre_curvas(f, g, li, ri, n=n)
            n_usados += 1
        except Exception:
            continue
    return area_total, n_usados


class AppFunciones:

    def __init__(self, master):
        self.master = master
        master.title("Parte 1 - Area entre curvas (funciones)")
        master.geometry("1360x760")
        master.resizable(True, True)

        self.imagen_pil = None
        self.imagen_tk = None
        self.img_w = 0
        self.img_h = 0
        self.offset_x = 0
        self.offset_y = 0

        self.lim_px_a = None
        self.lim_px_b = None
        self.lim_px_c = None
        self.lim_px_d = None

        self.nodos_f_px = []
        self.nodos_g_px = []
        self.divisiones_f_px = []
        self.divisiones_g_px = []
        self.f_interp = None
        self.g_interp = None
        self.rango_f = None
        self.rango_g = None
        self.rango_area = None
        self.max_zoom_imagen = 1.6
        self.factor_llenado_canvas = 0.92
        self.radio_nodo_px = 6

        self._crear_panel()
        self._crear_canvas()

    def _crear_panel(self):
        panel = tk.Frame(self.master, width=250)
        panel.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)
        panel.pack_propagate(False)

        tk.Button(panel, text="Cargar imagen", command=self._cargar_imagen).pack(fill=tk.X, pady=3)

        self._separador(panel)

        tk.Label(panel, text="Definir limites en radios rojos de abajo", font=("Arial", 9, "bold")).pack(anchor=tk.W)

        self._separador(panel)

        tk.Label(panel, text="Curva activa", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        self.var_curva = tk.StringVar(value="f")
        fr_curva = tk.Frame(panel)
        fr_curva.pack(fill=tk.X)
        tk.Radiobutton(fr_curva, text="curva f", variable=self.var_curva,
                        value="f", fg="blue").pack(side=tk.LEFT)
        tk.Radiobutton(fr_curva, text="curva g", variable=self.var_curva,
                        value="g", fg="#008040").pack(side=tk.LEFT)

        self._separador(panel)

        tk.Label(panel, text="Modo de click", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        self.var_modo = tk.StringVar(value="limites")
        fr_modo = tk.Frame(panel)
        fr_modo.pack(fill=tk.X)
        tk.Radiobutton(fr_modo, text="Colocar nodos",
                        variable=self.var_modo, value="nodos",
                        command=self._actualizar_modo).pack(anchor=tk.W)
        tk.Radiobutton(fr_modo, text="Colocar divisiones de tramo (max 2)",
                        variable=self.var_modo, value="divisiones",
                        fg="#FF6600", command=self._actualizar_modo).pack(anchor=tk.W)
        tk.Radiobutton(fr_modo, text="Fijar limites en imagen",
                        variable=self.var_modo, value="limites",
                        fg="#CC0000", command=self._actualizar_modo).pack(anchor=tk.W)

        self.fr_limite_sel = tk.Frame(panel)
        self.fr_limite_sel.pack(fill=tk.X, pady=2)

        self.var_limite = tk.StringVar(value="a")

        tk.Label(self.fr_limite_sel, text="Eje X:", font=("Arial", 8, "bold")).grid(
            row=0, column=0, sticky=tk.W, padx=(10, 2))
        tk.Radiobutton(self.fr_limite_sel, text="a (izq)", variable=self.var_limite,
                        value="a", fg="#CC0000", font=("Arial", 8),
                        command=self._actualizar_lbl_limite).grid(row=0, column=1)
        tk.Radiobutton(self.fr_limite_sel, text="b (der)", variable=self.var_limite,
                        value="b", fg="#CC0000", font=("Arial", 8),
                        command=self._actualizar_lbl_limite).grid(row=0, column=2)

        tk.Label(self.fr_limite_sel, text="Eje Y:", font=("Arial", 8, "bold")).grid(
            row=1, column=0, sticky=tk.W, padx=(10, 2))
        tk.Radiobutton(self.fr_limite_sel, text="c (inf)", variable=self.var_limite,
                        value="c", fg="#CC0000", font=("Arial", 8),
                        command=self._actualizar_lbl_limite).grid(row=1, column=1)
        tk.Radiobutton(self.fr_limite_sel, text="d (sup)", variable=self.var_limite,
                        value="d", fg="#CC0000", font=("Arial", 8),
                        command=self._actualizar_lbl_limite).grid(row=1, column=2)

        self.lbl_modo = tk.Label(panel, text="Click = colocar nodo sobre la curva",
                                  font=("Arial", 8), fg="gray40")
        self.lbl_modo.pack(anchor=tk.W, pady=2)

        self._separador(panel)

        tk.Button(panel, text="Deshacer ultimo cambio",
                  command=self._deshacer).pack(fill=tk.X, pady=2)
        tk.Button(panel, text="Limpiar curva activa",
                  command=self._limpiar).pack(fill=tk.X, pady=2)
        tk.Button(panel, text="Limpiar todo",
                  command=self._limpiar_todo).pack(fill=tk.X, pady=2)

        self._separador(panel)

        tk.Button(panel, text="CALCULAR AREA", command=self._calcular,
                  bg="#2E7D32", fg="white", font=("Arial", 10, "bold")).pack(fill=tk.X, pady=4)

        self.lbl_resultado = tk.Label(panel, text="Area: --- px^2",
                                       font=("Arial", 11, "bold"), fg="#1565C0")
        self.lbl_resultado.pack(pady=4)

        tk.Button(panel, text="Ver graficas",
                  command=self._mostrar_graficas).pack(fill=tk.X, pady=2)

        self.lbl_estado = tk.Label(panel, text="f: 0 nodos, 0 div | g: 0 nodos, 0 div",
                                    font=("Arial", 8), fg="gray40")
        self.lbl_estado.pack(side=tk.BOTTOM, pady=2)

        self.lbl_info = tk.Label(panel, text="", font=("Arial", 8), fg="gray40")
        self.lbl_info.pack(side=tk.BOTTOM, pady=4)

        self._actualizar_modo()

    def _separador(self, parent):
        tk.Frame(parent, height=2, bg="gray70").pack(fill=tk.X, pady=6)

    def _actualizar_modo(self):
        modo = self.var_modo.get()
        if modo == "divisiones":
            self.lbl_modo.config(
                text="Click = colocar division de tramo en la imagen",
                fg="#FF6600")
        elif modo == "limites":
            self._actualizar_lbl_limite()
        else:
            self.lbl_modo.config(
                text="Click = colocar nodo sobre la curva",
                fg="gray40")

    def _actualizar_lbl_limite(self):
        cual = self.var_limite.get()
        nombres = {"a": "a (vertical izq)", "b": "b (vertical der)",
                    "c": "c (horizontal inf)", "d": "d (horizontal sup)"}
        self.lbl_modo.config(text=f"Click para fijar {nombres[cual]}", fg="#CC0000")

    def _crear_canvas(self):
        self.canvas = tk.Canvas(self.master, bg="#2b2b2b")
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.canvas.bind("<Button-1>", self._click)
        self.canvas.bind("<Motion>", self._movimiento)

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

        ratio = min(cw / img.width, ch / img.height)
        ratio *= self.factor_llenado_canvas
        ratio = min(ratio, self.max_zoom_imagen)
        ratio = max(ratio, 0.05)
        self.img_w = int(img.width * ratio)
        self.img_h = int(img.height * ratio)
        img = img.resize((self.img_w, self.img_h), Image.LANCZOS)

        self.offset_x = (cw - self.img_w) // 2
        self.offset_y = (ch - self.img_h) // 2

        self.lim_px_a = self.offset_x
        self.lim_px_b = self.offset_x + self.img_w
        self.lim_px_c = self.offset_y + self.img_h
        self.lim_px_d = self.offset_y

        self.imagen_pil = img
        self.imagen_tk = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.create_image(self.offset_x, self.offset_y,
                                  anchor=tk.NW, image=self.imagen_tk, tags="img")
        self._redibujar()

    def _pixel_a_coord(self, px, py):
        return float(px), float(py)

    def _click(self, event):
        if self.imagen_pil is None:
            return
        if (event.x < self.offset_x or event.x > self.offset_x + self.img_w or
                event.y < self.offset_y or event.y > self.offset_y + self.img_h):
            return

        modo = self.var_modo.get()

        if modo == "limites":
            cual = self.var_limite.get()
            if cual == "a":
                self.lim_px_a = event.x
            elif cual == "b":
                self.lim_px_b = event.x
            elif cual == "c":
                self.lim_px_c = event.y
            elif cual == "d":
                self.lim_px_d = event.y
            self._redibujar()
            return

        if modo == "divisiones":
            curva = self.var_curva.get()
            divisiones = self.divisiones_f_px if curva == "f" else self.divisiones_g_px
            nodos = self.nodos_f_px if curva == "f" else self.nodos_g_px
            if len(divisiones) >= 2:
                messagebox.showinfo("", "Maximo 2 divisiones por curva (3 tramos)")
                return
            div_px = event.x
            div_py = event.y
            divisiones.append((div_px, div_py))
            if not any(abs(px - div_px) <= 2 for (px, _) in nodos):
                nodos.append((div_px, div_py))
        else:
            curva = self.var_curva.get()
            nodos = self.nodos_f_px if curva == "f" else self.nodos_g_px
            divisiones = self.divisiones_f_px if curva == "f" else self.divisiones_g_px
            px_click = event.x
            for div_px, _ in divisiones:
                if abs(px_click - div_px) <= 5:
                    px_click = div_px
                    break
            nodos.append((px_click, event.y))

        self._redibujar()

    def _deshacer(self):
        modo = self.var_modo.get()

        if modo == "limites":
            cual = self.var_limite.get()
            if cual == "a":
                self.lim_px_a = self.offset_x
            elif cual == "b":
                self.lim_px_b = self.offset_x + self.img_w
            elif cual == "c":
                self.lim_px_c = self.offset_y + self.img_h
            elif cual == "d":
                self.lim_px_d = self.offset_y
            self._redibujar()
            return

        curva = self.var_curva.get()
        if modo == "divisiones":
            divisiones = self.divisiones_f_px if curva == "f" else self.divisiones_g_px
            nodos = self.nodos_f_px if curva == "f" else self.nodos_g_px
            if divisiones:
                div_px, div_py = divisiones.pop()
                for i in range(len(nodos) - 1, -1, -1):
                    px, py = nodos[i]
                    if abs(px - div_px) <= 2 and abs(py - div_py) <= 6:
                        nodos.pop(i)
                        break
        else:
            nodos = self.nodos_f_px if curva == "f" else self.nodos_g_px
            if nodos:
                nodos.pop()

        self._redibujar()

    def _limpiar(self):
        if self.var_curva.get() == "f":
            self.nodos_f_px.clear()
            self.divisiones_f_px.clear()
        else:
            self.nodos_g_px.clear()
            self.divisiones_g_px.clear()
        self._redibujar()

    def _limpiar_todo(self):
        self.nodos_f_px.clear()
        self.nodos_g_px.clear()
        self.divisiones_f_px.clear()
        self.divisiones_g_px.clear()
        self.f_interp = None
        self.g_interp = None
        self.rango_f = None
        self.rango_g = None
        self.rango_area = None
        self.lbl_resultado.config(text="Area: --- px^2")
        self._redibujar()

    def _redibujar(self):
        self.canvas.delete("nodo")
        self.canvas.delete("division")
        self.canvas.delete("limite")

        if self.lim_px_a is not None:
            self.canvas.create_line(self.lim_px_a, self.offset_y,
                                    self.lim_px_a, self.offset_y + self.img_h,
                                    fill="#FF0000", width=3, dash=(8, 4), tags="limite")
            self.canvas.create_oval(self.lim_px_a - 6, self.offset_y + self.img_h // 2 - 6,
                                    self.lim_px_a + 6, self.offset_y + self.img_h // 2 + 6,
                                    fill="#FF0000", outline="white", width=1, tags="limite")
            self.canvas.create_text(self.lim_px_a, self.offset_y - 14,
                                    text=f"a={self.lim_px_a:.1f}px", fill="#FF0000",
                                    font=("Consolas", 10, "bold"), tags="limite")

        if self.lim_px_b is not None:
            self.canvas.create_line(self.lim_px_b, self.offset_y,
                                    self.lim_px_b, self.offset_y + self.img_h,
                                    fill="#FF0000", width=3, dash=(8, 4), tags="limite")
            self.canvas.create_oval(self.lim_px_b - 6, self.offset_y + self.img_h // 2 - 6,
                                    self.lim_px_b + 6, self.offset_y + self.img_h // 2 + 6,
                                    fill="#FF0000", outline="white", width=1, tags="limite")
            self.canvas.create_text(self.lim_px_b, self.offset_y - 14,
                                    text=f"b={self.lim_px_b:.1f}px", fill="#FF0000",
                                    font=("Consolas", 10, "bold"), tags="limite")

        if self.lim_px_c is not None:
            self.canvas.create_line(self.offset_x, self.lim_px_c,
                                    self.offset_x + self.img_w, self.lim_px_c,
                                    fill="#FF0000", width=3, dash=(8, 4), tags="limite")
            self.canvas.create_oval(self.offset_x + self.img_w // 2 - 6, self.lim_px_c - 6,
                                    self.offset_x + self.img_w // 2 + 6, self.lim_px_c + 6,
                                    fill="#FF0000", outline="white", width=1, tags="limite")
            self.canvas.create_text(self.offset_x - 5, self.lim_px_c,
                                    text=f"c={self.lim_px_c:.1f}px", fill="#FF0000",
                                    font=("Consolas", 10, "bold"), anchor=tk.E, tags="limite")

        if self.lim_px_d is not None:
            self.canvas.create_line(self.offset_x, self.lim_px_d,
                                    self.offset_x + self.img_w, self.lim_px_d,
                                    fill="#FF0000", width=3, dash=(8, 4), tags="limite")
            self.canvas.create_oval(self.offset_x + self.img_w // 2 - 6, self.lim_px_d - 6,
                                    self.offset_x + self.img_w // 2 + 6, self.lim_px_d + 6,
                                    fill="#FF0000", outline="white", width=1, tags="limite")
            self.canvas.create_text(self.offset_x - 5, self.lim_px_d,
                                    text=f"d={self.lim_px_d:.1f}px", fill="#FF0000",
                                    font=("Consolas", 10, "bold"), anchor=tk.E, tags="limite")

        for curva, divisiones, nodos in [("f", self.divisiones_f_px, self.nodos_f_px),
                                          ("g", self.divisiones_g_px, self.nodos_g_px)]:
            color_div = "#FF8800" if curva == "f" else "#FFAA00"
            
            for div_px, div_py in divisiones:
                py_top = max(self.offset_y, div_py - 40)
                py_bot = min(self.offset_y + self.img_h, div_py + 40)

                self.canvas.create_line(div_px, py_top, div_px, py_bot,
                                        fill=color_div, width=3, dash=(5, 3), tags="division")
                x_dom, _ = self._pixel_a_coord(div_px, 0)
                self.canvas.create_text(div_px, py_top - 10,
                                        text=f"{curva} div ({x_dom:.1f}px)",
                                        fill=color_div, font=("Consolas", 9), tags="division")

        pares = [("f", self.nodos_f_px, "#4488FF"), ("g", self.nodos_g_px, "#00CC66")]
        for nombre, nodos, color in pares:
            for (px, py) in nodos:
                r = self.radio_nodo_px
                self.canvas.create_oval(px-r, py-r, px+r, py+r,
                                        fill=color, outline="white", width=1, tags="nodo")
                x_dom, y_dom = self._pixel_a_coord(px, py)
                self.canvas.create_text(px+10, py-10,
                                        text=f"({x_dom:.1f}px, {y_dom:.1f}px)",
                                        fill=color, font=("Consolas", 9), tags="nodo")

        self.lbl_estado.config(
            text=f"f: {len(self.nodos_f_px)} nodos, {len(self.divisiones_f_px)} div | "
                 f"g: {len(self.nodos_g_px)} nodos, {len(self.divisiones_g_px)} div")

    def _movimiento(self, event):
        if self.imagen_pil is None:
            return
        x, y = self._pixel_a_coord(event.x, event.y)
        self.lbl_info.config(text=f"x = {x:.1f}px   y = {y:.1f}px")

    def _obtener_datos_px(self):
        # Retorna nodos y divisiones en pixeles.
        nf = [self._pixel_a_coord(px, py) for (px, py) in self.nodos_f_px]
        ng = [self._pixel_a_coord(px, py) for (px, py) in self.nodos_g_px]
        df = sorted([self._pixel_a_coord(dpx, 0)[0] for (dpx, _) in self.divisiones_f_px])
        dg = sorted([self._pixel_a_coord(dpx, 0)[0] for (dpx, _) in self.divisiones_g_px])
        return nf, ng, df, dg

    def _calcular(self):
        # Interpolacion por tramos (hasta 3) para cada curva y suma de area por subintervalos.
        if self.imagen_pil is None:
            messagebox.showerror("Error", "Primero cargue una imagen")
            return
        if None in (self.lim_px_a, self.lim_px_b, self.lim_px_c, self.lim_px_d):
            messagebox.showerror("Error", "Faltan limites en imagen (a,b,c,d)")
            return

        x_left = float(min(self.lim_px_a, self.lim_px_b))
        x_right = float(max(self.lim_px_a, self.lim_px_b))
        if x_right - x_left <= 1e-9:
            messagebox.showerror("Error", "Limites a y b invalidos")
            return

        nf, ng, df, dg = self._obtener_datos_px()
        nf = [p for p in nf if x_left <= p[0] <= x_right]
        ng = [p for p in ng if x_left <= p[0] <= x_right]
        self.f_interp, rango_f, df_calc = construir_interpolante_por_trozos_spline(
            nf, df, x_left, x_right
        )
        self.g_interp, rango_g, dg_calc = construir_interpolante_por_trozos_spline(
            ng, dg, x_left, x_right
        )

        if self.f_interp is None or rango_f is None:
            messagebox.showerror(
                "Error",
                "f necesita al menos 2 nodos por cada tramo definido por sus divisiones")
            return
        if self.g_interp is None or rango_g is None:
            messagebox.showerror(
                "Error",
                "g necesita al menos 2 nodos por cada tramo definido por sus divisiones")
            return

        self.rango_f = rango_f
        self.rango_g = rango_g

        x_ini = max(rango_f[0], rango_g[0])
        x_fin = min(rango_f[1], rango_g[1])
        if x_fin - x_ini <= 1e-12:
            messagebox.showerror(
                "Error",
                "No hay coincidencia en x entre f y g (segun sus nodos)")
            self.f_interp = None
            self.g_interp = None
            self.rango_f = None
            self.rango_g = None
            self.rango_area = None
            self.lbl_resultado.config(text="Area: --- px^2")
            return

        cortes = [x_ini, x_fin] + [d for d in (df_calc + dg_calc) if x_ini < d < x_fin]
        area, n_usados = area_entre_curvas_por_subintervalos(self.f_interp, self.g_interp, cortes, n=200)
        if n_usados == 0 or not np.isfinite(area):
            messagebox.showerror(
                "Error",
                "No hay subintervalos con coincidencia valida entre f y g")
            self.f_interp = None
            self.g_interp = None
            self.rango_f = None
            self.rango_g = None
            self.rango_area = None
            self.lbl_resultado.config(text="Area: --- px^2")
            return

        self.rango_area = (x_ini, x_fin)
        self.lbl_resultado.config(text=f"Area ~ {area:.6f} px^2")

    def _mostrar_graficas(self):
        if self.f_interp is None or self.g_interp is None:
            messagebox.showinfo("", "Primero calcule el area")
            return

        nf, ng, df, dg = self._obtener_datos_px()

        if self.rango_f is None or self.rango_g is None or self.rango_area is None:
            messagebox.showinfo("", "Primero calcule el area")
            return

        def evaluar_seguro(fun, xs):
            vals = []
            for x in xs:
                try:
                    vals.append(fun(x))
                except Exception:
                    vals.append(np.nan)
            return np.array(vals, dtype=float)

        x_left = float(min(self.lim_px_a, self.lim_px_b))
        x_right = float(max(self.lim_px_a, self.lim_px_b))
        xs_f = np.linspace(x_left, x_right, 700)
        ys_f = evaluar_seguro(self.f_interp, xs_f)
        xs_g = np.linspace(x_left, x_right, 700)
        ys_g = evaluar_seguro(self.g_interp, xs_g)
        xs_area = np.linspace(x_left, x_right, 800)
        yf_area = evaluar_seguro(self.f_interp, xs_area)
        yg_area = evaluar_seguro(self.g_interp, xs_area)
        mask_area = np.isfinite(yf_area) & np.isfinite(yg_area)

        fig, ax = plt.subplots(figsize=(9, 5))
        ax.plot(xs_f, ys_f, color="#4488FF", linewidth=2, label="f interpolada")
        ax.plot(xs_g, ys_g, color="#00CC66", linewidth=2, label="g interpolada")
        ax.fill_between(
            xs_area, yf_area, yg_area, where=mask_area,
            alpha=0.25, color="orange", label="Area")

        xp_f = [p[0] for p in nf]
        yp_f = [p[1] for p in nf]
        xp_g = [p[0] for p in ng]
        yp_g = [p[1] for p in ng]
        ax.plot(xp_f, yp_f, "o", color="#4488FF", markersize=5)
        ax.plot(xp_g, yp_g, "o", color="#00CC66", markersize=5)

        for d in [d for d in df if x_left < d < x_right]:
            ax.axvline(x=d, color="#FF6600", linewidth=1, linestyle="--", alpha=0.6)
            try:
                ax.plot(d, self.f_interp(d), "D", color="#FF6600", markersize=6, zorder=5)
            except Exception:
                pass

        for d in [d for d in dg if x_left < d < x_right]:
            ax.axvline(x=d, color="#CC9900", linewidth=1, linestyle="--", alpha=0.6)
            try:
                ax.plot(d, self.g_interp(d), "D", color="#CC9900", markersize=6, zorder=5)
            except Exception:
                pass

        if df or dg:
            ax.plot([], [], "D", color="#FF6600", markersize=6, label="Divisiones")

        ax.set_xlabel("x (px)")
        ax.set_ylabel("y (px)")
        # En pixeles el eje Y crece hacia abajo; invertimos para que coincida con la imagen.
        ax.invert_yaxis()
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    ventana = tk.Tk()
    app = AppFunciones(ventana)
    ventana.mainloop()

