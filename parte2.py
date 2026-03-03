import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt


def evaluar_lagrange(tn, vn, t):
    n = len(tn)
    resultado = 0.0
    for i in range(n):
        Li = 1.0
        for j in range(n):
            if j != i:
                Li *= (t - tn[j]) / (tn[i] - tn[j])
        resultado += vn[i] * Li
    return resultado


def derivada_lagrange(tn, vn, t):
    n = len(tn)
    resultado = 0.0
    for i in range(n):
        suma = 0.0
        for k in range(n):
            if k == i:
                continue
            prod = 1.0
            for j in range(n):
                if j != i and j != k:
                    prod *= (t - tn[j]) / (tn[i] - tn[j])
            suma += prod / (tn[i] - tn[k])
        resultado += vn[i] * suma
    return resultado


def simpson(f, a, b, n=200):
    if n % 2 != 0:
        n += 1
    h = (b - a) / n
    x = np.linspace(a, b, n + 1)
    y = np.array([f(xi) for xi in x])
    return h / 3.0 * (y[0] + y[-1] + 4.0 * np.sum(y[1:-1:2]) + 2.0 * np.sum(y[2:-2:2]))

def area_integral_linea(puntos, grado=3, ns_seg=60):
    n = len(puntos)
    if n < 3:
        return 0.0

    pts = list(puntos) + [puntos[0]]
    m = len(pts)
    area_total = 0.0

    for i in range(m - 1):
        mitad = grado // 2
        ini = max(0, i - mitad)
        fin = min(m, ini + grado + 1)
        if fin - ini < grado + 1:
            ini = max(0, fin - grado - 1)

        seg = pts[ini:fin]
        ts_loc = np.array([float(ini + j) for j in range(len(seg))])
        xs_loc = np.array([p[0] for p in seg])
        ys_loc = np.array([p[1] for p in seg])

        ta, tb = float(i), float(i + 1)

        def integrando(t, ts=ts_loc, xs=xs_loc, ys=ys_loc):
            xt = evaluar_lagrange(ts, xs, t)
            yt = evaluar_lagrange(ts, ys, t)
            dyt = derivada_lagrange(ts, ys, t)
            dxt = derivada_lagrange(ts, xs, t)
            return xt * dyt - yt * dxt

        area_total += simpson(integrando, ta, tb, ns_seg)

    return 0.5 * abs(area_total)


def shoelace(puntos):
    n = len(puntos)
    if n < 3:
        return 0.0
    s = 0.0
    for i in range(n):
        j = (i + 1) % n
        s += puntos[i][0] * puntos[j][1] - puntos[j][0] * puntos[i][1]
    return 0.5 * abs(s)

class AppParte2:

    def __init__(self, master):
        self.master = master
        master.title("Parte 2 - Area entre curvas cerradas")
        master.geometry("1200x700")
        master.resizable(True, True)

        self.imagen_pil = None
        self.imagen_tk = None
        self.img_w = 0
        self.img_h = 0
        self.offset_x = 0
        self.offset_y = 0

        self.a, self.b = 0.0, 10.0
        self.c, self.d = 0.0, 10.0

        self.lim_px_a = None
        self.lim_px_b = None
        self.lim_px_c = None
        self.lim_px_d = None

        self.nodos_c1_px = []
        self.nodos_c2_px = []
        self.area_c1 = None
        self.area_c2 = None
        self.area_entre = None
        self.metodo_usado = "trozos"

        self._crear_panel()
        self._crear_canvas()

    def _crear_panel(self):
        panel = tk.Frame(self.master, width=300)
        panel.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)
        panel.pack_propagate(False)

        tk.Button(panel, text="Cargar imagen", command=self._cargar_imagen).pack(fill=tk.X, pady=3)

        self._separador(panel)

        tk.Label(panel, text="Curva activa", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        self.var_curva = tk.StringVar(value="C1")
        fr_curva = tk.Frame(panel)
        fr_curva.pack(fill=tk.X)
        tk.Radiobutton(fr_curva, text="C1 exterior (azul)", variable=self.var_curva,
                        value="C1", fg="blue").pack(side=tk.LEFT)
        tk.Radiobutton(fr_curva, text="C2 interior (rojo)", variable=self.var_curva,
                        value="C2", fg="#CC0000").pack(side=tk.LEFT)

        self._separador(panel)

        tk.Label(panel, text="Modo de click", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        self.var_modo = tk.StringVar(value="limites")
        fr_modo = tk.Frame(panel)
        fr_modo.pack(fill=tk.X)
        tk.Radiobutton(fr_modo, text="Colocar nodos",
                        variable=self.var_modo, value="nodos",
                        command=self._actualizar_modo).pack(anchor=tk.W)
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

        tk.Label(panel, text="Metodo de calculo", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        self.var_metodo = tk.StringVar(value="trozos")
        fr_met = tk.Frame(panel)
        fr_met.pack(fill=tk.X)
        tk.Radiobutton(fr_met, text="Lagrange por trozos",
                        variable=self.var_metodo, value="trozos").pack(anchor=tk.W)
        tk.Radiobutton(fr_met, text="Shoelace (poligonal)",
                        variable=self.var_metodo, value="shoelace").pack(anchor=tk.W)

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

        self.lbl_area_c1 = tk.Label(panel, text="Area C1: ---",
                                     font=("Arial", 9), fg="#1565C0")
        self.lbl_area_c1.pack(anchor=tk.W)
        self.lbl_area_c2 = tk.Label(panel, text="Area C2: ---",
                                     font=("Arial", 9), fg="#CC0000")
        self.lbl_area_c2.pack(anchor=tk.W)
        self.lbl_resultado = tk.Label(panel, text="Area entre curvas: ---",
                                       font=("Arial", 11, "bold"), fg="#6A1B9A")
        self.lbl_resultado.pack(pady=6)

        tk.Button(panel, text="Ver graficas",
                  command=self._mostrar_graficas).pack(fill=tk.X, pady=2)

        self.lbl_nodos = tk.Label(panel, text="C1: 0 nodos | C2: 0 nodos",
                                   font=("Arial", 8), fg="gray40")
        self.lbl_nodos.pack(side=tk.BOTTOM, pady=2)

        self.lbl_info = tk.Label(panel, text="", font=("Arial", 8), fg="gray40")
        self.lbl_info.pack(side=tk.BOTTOM, pady=2)

        self._actualizar_modo()

    def _separador(self, parent):
        tk.Frame(parent, height=2, bg="gray70").pack(fill=tk.X, pady=6)

    def _actualizar_modo(self):
        modo = self.var_modo.get()
        if modo == "limites":
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
            cw, ch = 850, 650

        ratio = min(cw / img.width, ch / img.height, 1.0)
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
        dx = self.lim_px_b - self.lim_px_a
        dy = self.lim_px_c - self.lim_px_d
        if abs(dx) < 1:
            dx = 1
        if abs(dy) < 1:
            dy = 1
        x = self.a + (px - self.lim_px_a) / dx * (self.b - self.a)
        y = self.d - (py - self.lim_px_d) / dy * (self.d - self.c)
        return x, y

    def _coord_a_pixel(self, x, y):
        dx = self.lim_px_b - self.lim_px_a
        dy = self.lim_px_c - self.lim_px_d
        px = self.lim_px_a + (x - self.a) / (self.b - self.a) * dx
        py = self.lim_px_d + (self.d - y) / (self.d - self.c) * dy
        return px, py

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

        nodos = self.nodos_c1_px if self.var_curva.get() == "C1" else self.nodos_c2_px
        nodos.append((event.x, event.y))
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

        nodos = self.nodos_c1_px if self.var_curva.get() == "C1" else self.nodos_c2_px
        if nodos:
            nodos.pop()
        self._redibujar()

    def _limpiar(self):
        if self.var_curva.get() == "C1":
            self.nodos_c1_px.clear()
        else:
            self.nodos_c2_px.clear()
        self._redibujar()

    def _limpiar_todo(self):
        self.nodos_c1_px.clear()
        self.nodos_c2_px.clear()
        self.area_c1 = None
        self.area_c2 = None
        self.area_entre = None
        self.lbl_area_c1.config(text="Area C1: ---")
        self.lbl_area_c2.config(text="Area C2: ---")
        self.lbl_resultado.config(text="Area entre curvas: ---")
        self._redibujar()

    def _redibujar(self):
        self.canvas.delete("nodo")
        self.canvas.delete("linea")
        self.canvas.delete("limite")

        if self.lim_px_a is not None:
            self.canvas.create_line(self.lim_px_a, self.offset_y,
                                    self.lim_px_a, self.offset_y + self.img_h,
                                    fill="#FF0000", width=2, dash=(8, 4), tags="limite")
            self.canvas.create_oval(self.lim_px_a - 4, self.offset_y + self.img_h // 2 - 4,
                                    self.lim_px_a + 4, self.offset_y + self.img_h // 2 + 4,
                                    fill="#FF0000", outline="white", width=1, tags="limite")
            self.canvas.create_text(self.lim_px_a, self.offset_y - 12,
                                    text=f"a={self.a:.1f}", fill="#FF0000",
                                    font=("Consolas", 8, "bold"), tags="limite")

        if self.lim_px_b is not None:
            self.canvas.create_line(self.lim_px_b, self.offset_y,
                                    self.lim_px_b, self.offset_y + self.img_h,
                                    fill="#FF0000", width=2, dash=(8, 4), tags="limite")
            self.canvas.create_oval(self.lim_px_b - 4, self.offset_y + self.img_h // 2 - 4,
                                    self.lim_px_b + 4, self.offset_y + self.img_h // 2 + 4,
                                    fill="#FF0000", outline="white", width=1, tags="limite")
            self.canvas.create_text(self.lim_px_b, self.offset_y - 12,
                                    text=f"b={self.b:.1f}", fill="#FF0000",
                                    font=("Consolas", 8, "bold"), tags="limite")

        if self.lim_px_c is not None:
            self.canvas.create_line(self.offset_x, self.lim_px_c,
                                    self.offset_x + self.img_w, self.lim_px_c,
                                    fill="#FF0000", width=2, dash=(8, 4), tags="limite")
            self.canvas.create_oval(self.offset_x + self.img_w // 2 - 4, self.lim_px_c - 4,
                                    self.offset_x + self.img_w // 2 + 4, self.lim_px_c + 4,
                                    fill="#FF0000", outline="white", width=1, tags="limite")
            self.canvas.create_text(self.offset_x - 5, self.lim_px_c,
                                    text=f"c={self.c:.1f}", fill="#FF0000",
                                    font=("Consolas", 8, "bold"), anchor=tk.E, tags="limite")

        if self.lim_px_d is not None:
            self.canvas.create_line(self.offset_x, self.lim_px_d,
                                    self.offset_x + self.img_w, self.lim_px_d,
                                    fill="#FF0000", width=2, dash=(8, 4), tags="limite")
            self.canvas.create_oval(self.offset_x + self.img_w // 2 - 4, self.lim_px_d - 4,
                                    self.offset_x + self.img_w // 2 + 4, self.lim_px_d + 4,
                                    fill="#FF0000", outline="white", width=1, tags="limite")
            self.canvas.create_text(self.offset_x - 5, self.lim_px_d,
                                    text=f"d={self.d:.1f}", fill="#FF0000",
                                    font=("Consolas", 8, "bold"), anchor=tk.E, tags="limite")

        pares = [("C1", self.nodos_c1_px, "#4488FF"), ("C2", self.nodos_c2_px, "#FF4444")]
        for nombre, nodos, color in pares:
            if len(nodos) < 1:
                continue

            for k, (px, py) in enumerate(nodos):
                r = 4
                self.canvas.create_oval(px-r, py-r, px+r, py+r,
                                        fill=color, outline="white", width=1, tags="nodo")
                self.canvas.create_text(px+12, py-10,
                                        text=f"{k}",
                                        fill=color, font=("Consolas", 7), tags="nodo")

            if len(nodos) >= 2:
                for k in range(len(nodos) - 1):
                    px1, py1 = nodos[k]
                    px2, py2 = nodos[k+1]
                    self.canvas.create_line(px1, py1, px2, py2,
                                            fill=color, width=1, dash=(4, 3), tags="linea")

                if len(nodos) >= 3:
                    px1, py1 = nodos[-1]
                    px2, py2 = nodos[0]
                    self.canvas.create_line(px1, py1, px2, py2,
                                            fill=color, width=1, dash=(2, 4), tags="linea")

        self.lbl_nodos.config(
            text=f"C1: {len(self.nodos_c1_px)} nodos | C2: {len(self.nodos_c2_px)} nodos")

    def _movimiento(self, event):
        if self.imagen_pil is None:
            return
        x, y = self._pixel_a_coord(event.x, event.y)
        self.lbl_info.config(text=f"x = {x:.3f}   y = {y:.3f}")

    def _convertir_a_dominio(self):
        c1 = [self._pixel_a_coord(px, py) for (px, py) in self.nodos_c1_px]
        c2 = [self._pixel_a_coord(px, py) for (px, py) in self.nodos_c2_px]
        return c1, c2

    def _calcular(self):
        if len(self.nodos_c1_px) < 3:
            messagebox.showerror("Error", "C1 necesita al menos 3 nodos")
            return
        if len(self.nodos_c2_px) < 3:
            messagebox.showerror("Error", "C2 necesita al menos 3 nodos")
            return

        c1_dom, c2_dom = self._convertir_a_dominio()
        self.metodo_usado = self.var_metodo.get()

        if self.metodo_usado == "shoelace":
            a1 = shoelace(c1_dom)
            a2 = shoelace(c2_dom)
        else:
            a1 = area_integral_linea(c1_dom)
            a2 = area_integral_linea(c2_dom)

        self.area_c1 = a1
        self.area_c2 = a2
        self.area_entre = abs(a1 - a2)

        self.lbl_area_c1.config(text=f"Area C1: {self.area_c1:.6f}")
        self.lbl_area_c2.config(text=f"Area C2: {self.area_c2:.6f}")
        self.lbl_resultado.config(text=f"Area entre curvas: {self.area_entre:.6f}")

    def _curva_interpolada(self, nodos_dom, grado=3, npts=300):
        pts = list(nodos_dom) + [nodos_dom[0]]
        m = len(pts)
        npt_seg = max(15, npts // (m - 1))
        xc_list, yc_list = [], []

        for i in range(m - 1):
            mitad = grado // 2
            ini = max(0, i - mitad)
            fin = min(m, ini + grado + 1)
            if fin - ini < grado + 1:
                ini = max(0, fin - grado - 1)

            seg = pts[ini:fin]
            ts_loc = np.array([float(ini + j) for j in range(len(seg))])
            xs_loc = np.array([p[0] for p in seg])
            ys_loc = np.array([p[1] for p in seg])

            tt = np.linspace(float(i), float(i + 1), npt_seg, endpoint=(i == m - 2))
            for t in tt:
                xc_list.append(evaluar_lagrange(ts_loc, xs_loc, t))
                yc_list.append(evaluar_lagrange(ts_loc, ys_loc, t))

        return np.array(xc_list), np.array(yc_list)

    def _mostrar_graficas(self):
        if len(self.nodos_c1_px) < 3 or len(self.nodos_c2_px) < 3:
            messagebox.showinfo("", "Se necesitan al menos 3 nodos en cada curva")
            return

        c1_dom, c2_dom = self._convertir_a_dominio()
        fig, ax = plt.subplots(figsize=(8, 7))

        metodo = self.metodo_usado

        if metodo == "shoelace":
            xc1 = np.array([p[0] for p in c1_dom] + [c1_dom[0][0]])
            yc1 = np.array([p[1] for p in c1_dom] + [c1_dom[0][1]])
            xc2 = np.array([p[0] for p in c2_dom] + [c2_dom[0][0]])
            yc2 = np.array([p[1] for p in c2_dom] + [c2_dom[0][1]])
            lbl1, lbl2 = "C1 poligonal", "C2 poligonal"
        else:
            xc1, yc1 = self._curva_interpolada(c1_dom)
            xc2, yc2 = self._curva_interpolada(c2_dom)
            lbl1, lbl2 = "C1 interpolada", "C2 interpolada"

        ax.plot(xc1, yc1, color="#4488FF", linewidth=2, label=lbl1)
        ax.plot(xc2, yc2, color="#FF4444", linewidth=2, label=lbl2)

        ax.fill(xc1, yc1, alpha=0.12, color="#4488FF")
        ax.fill(xc2, yc2, alpha=0.12, color="#FF4444")

        for k, (x, y) in enumerate(c1_dom):
            ax.plot(x, y, "o", color="#4488FF", markersize=5, zorder=5)
            ax.annotate(str(k), (x, y), textcoords="offset points",
                        xytext=(6, 6), fontsize=7, color="#336699")

        for k, (x, y) in enumerate(c2_dom):
            ax.plot(x, y, "o", color="#FF4444", markersize=5, zorder=5)
            ax.annotate(str(k), (x, y), textcoords="offset points",
                        xytext=(6, 6), fontsize=7, color="#993333")

        if self.area_c1 is not None:
            met_txt = "Lagrange por trozos" if metodo == "trozos" else "Shoelace"
            ax.set_title(
                f"{met_txt}  |  A(C1)={self.area_c1:.4f}   "
                f"A(C2)={self.area_c2:.4f}   "
                f"Entre={self.area_entre:.4f}", fontsize=9)

        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_aspect("equal")
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    ventana = tk.Tk()
    app = AppParte2(ventana)
    ventana.mainloop()
