import tkinter as tk
import math
import os
from PIL import Image, ImageTk

# ── Colores ────────────────────────────────────────────────────────────────
COLOR_FONDO          = "#E3C39D"
COLOR_GRID           = "#CDD5DB"
COLOR_PUNTO          = "#071739"
COLOR_PANEL_SUP      = "#071739"
COLOR_PANEL_DER      = "#CDD5DB"
TIPO_FUENTE          = "Arial"

# Automático → Blanco titanio
CAUTO = ("#1D325C", "#1C3164", "#071739")

# Manual → Negro grafito azulado
CMAN = ("#A68868", "#8C6E52", "#7A5C42")


class SimuladorMapa:

    def __init__(self, root):
        self.root = root
        self.root.title("✈ Simulador Aéreo (Auto vs Manual) - UNEMI")
        self.root.geometry("1400x850")
        self.root.configure(bg=COLOR_FONDO)

        self.animacion_id  = None
        self.en_vuelo      = False
        self.dragging      = False
        self._drag_last    = (0, 0)
        self.angulo_manual = 0.0

        self._construir_ui(root)
        self.inicializar()

        for k in ("w", "s", "a", "d"):
            root.bind(f"<{k}>", self.mover_manual)

        self.canvas.tag_bind("avion_manual", "<ButtonPress-1>",   self.start_drag)
        self.canvas.tag_bind("avion_manual", "<B1-Motion>",       self.drag)
        self.canvas.tag_bind("avion_manual", "<ButtonRelease-1>",
                             lambda e: setattr(self, "dragging", False))

    # ── Construcción de la UI ──────────────────────────────────────────────
    def _construir_ui(self, root):
        # Panel superior
        ps = tk.Frame(root, bg=COLOR_PANEL_SUP, pady=10, padx=20)
        ps.pack(side="top", fill="x")

        tf = tk.Frame(ps, bg=COLOR_PANEL_SUP)
        tf.pack(side="left", expand=True, fill="x", padx=(10, 30))
        tk.Label(tf, text="UNIVERSIDAD ESTATAL DE MILAGRO",
                 font=("Tahoma", 24, "bold"), bg=COLOR_PANEL_SUP, fg="#E3C39D").pack(anchor="center", pady=(6, 2))
        tk.Label(tf, text="FACULTAD DE CIENCIAS E INGENIERÍA - TECNOLOGÍAS DE LA INFORMACIÓN",
                 font=("Tahoma", 16), bg=COLOR_PANEL_SUP, fg="#CDD5DB").pack(anchor="center")
        tk.Label(tf, text="MODALIDAD EN LÍNEA - GRUPO H",
                 font=("Tahoma", 10, "bold", "italic"), bg=COLOR_PANEL_SUP, fg="#A4B5C4").pack(anchor="center", pady=1)

        fi = tk.Frame(ps, bg=COLOR_PANEL_SUP)
        fi.pack(side="right", padx=20)
        tk.Label(fi, text="INTEGRANTES:", fg="#E3C39D", bg=COLOR_PANEL_SUP,
                 font=("Tahoma", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=2)
        integrantes = [
            "Mena Vélez Mateo Nikolas",      "Pontón Peña Priscila Indira",
            "Preciado Nazareno Shirley Yasmin", "Valarezo Ruíz Germania Cecibel",
            "Zambrano Arrobo Steven Joel",    "Zapata Delgado Santiago Alexander",
        ]
        for i, n in enumerate(integrantes):
            tk.Label(fi, text=f"• {n}", fg="#CDD5DB", bg=COLOR_PANEL_SUP,
                     font=(TIPO_FUENTE, 9, "bold"), anchor="w").grid(
                row=(i % 3) + 1, column=i // 3, sticky="w", padx=15, pady=1)

        # Canvas / mapa
        pc = tk.Frame(root, bg=COLOR_FONDO)
        pc.pack(side="left", expand=True, fill="both", padx=15, pady=15)
        ruta_img = os.path.join(os.path.dirname(os.path.abspath(__file__)), "imagen.png")
        img = Image.open(ruta_img).resize((1200, 700)) if os.path.exists(ruta_img) \
              else Image.new("RGB", (1200, 700), COLOR_FONDO)
        self.bg_img = ImageTk.PhotoImage(img)
        self.canvas = tk.Canvas(pc, width=1200, height=700,
                                bg=COLOR_FONDO, highlightthickness=0)
        self.canvas.pack(expand=True)
        self.canvas.create_image(600, 350, anchor="center", image=self.bg_img)

        self.paises = {
            "Ecuador":   (330, 350), "USA":       (300, 200),
            "Argentina": (400, 500), "Brazil":    (450, 400),
            "Canada":    (300, 100), "China":     (950, 225),
            "Rusia":     (800, 100), "Australia": (1050, 450),
        }

        # Panel derecho
        pd = tk.Frame(root, bg=COLOR_PANEL_DER, width=250, padx=15, pady=20)
        pd.pack(side="right", fill="y", padx=(0, 15), pady=15)
        pd.pack_propagate(False)
        tk.Label(pd, text="PANEL DE CONTROL", fg=COLOR_PUNTO, bg=COLOR_PANEL_DER,
                 font=(TIPO_FUENTE, 11, "bold")).pack(pady=(0, 15))

        self.lbl_auto = tk.Label(pd, fg="#E3C39D", bg="#071739",
                                 font=("Consolas", 10, "bold"),
                                 justify="left", padx=10, pady=10)
        self.lbl_auto.pack(fill="x", pady=10)

        self.lbl_manual = tk.Label(pd, fg="#A4B5C4", bg="#071739",
                                   font=("Consolas", 10, "bold"),
                                   justify="left", padx=10, pady=10)
        self.lbl_manual.pack(fill="x", pady=10)

        bf = tk.Frame(pd, bg=COLOR_PANEL_DER)
        bf.pack(fill="x", pady=(15, 0))
        self.btn_ini = tk.Button(bf, text="▶ Iniciar Vuelo Auto",
                                 command=self.iniciar_vuelo, bg="#4B6382", fg="white",
                                 font=(TIPO_FUENTE, 10, "bold"), height=2, relief="flat")
        self.btn_ini.pack(fill="x", pady=5)
        tk.Button(bf, text="🔄 Resetear Simulador", command=self.reset,
                  bg="#A68868", fg="white", font=(TIPO_FUENTE, 10, "bold"),
                  height=2, relief="flat").pack(fill="x", pady=5)

    # ── Geometría local del avión ──────────────────────────────────────────
    @staticmethod
    def _forma():
        def s(pts): return pts
        return [
            (s([(0,-12),(-2.5,-9),(-3,6),(-2,10),(0,9),(2,10),(3,6),(2.5,-9)]), "base"),
            (s([(0,-12),(-2,-8),(2,-8)]),                                         "dark"),
            (s([(-1,0),(-1,4),(-17,11),(-14,14),(0,7),(14,14),(17,11),(1,4),(1,0)]), "base"),
            (s([(-14,14),(-17,11),(-15,15)]),                                     "dark"),
            (s([(14,14),(17,11),(15,15)]),                                         "dark"),
            (s([(-10,5),(-12,5),(-13,10),(-12,14),(-10,14),(-9,10)]),            "dark"),
            (s([(10,5),(12,5),(13,10),(12,14),(10,14),(9,10)]),                   "dark"),
            (s([(-1,10),(-1,12),(-8,15),(-6,17),(0,13)]),                         "base"),
            (s([(1,10),(1,12),(8,15),(6,17),(0,13)]),                             "base"),
            (s([(0,8),(-2,13),(2,13)]),                                           "dark"),
        ] + [([(-1.2, y-1.2),(1.2, y-1.2),(1.2, y+1.2),(-1.2, y+1.2)], "vent")
             for y in (-7, -3, 1)]

    @staticmethod
    def _rotar(pts, ang):
        r = math.radians(ang)
        c, s = math.cos(r), math.sin(r)
        return [(x*c - y*s, x*s + y*c) for x, y in pts]

    @staticmethod
    def _ang(dx, dy):
        return math.degrees(math.atan2(dx, -dy))

    def _dibujar(self, tag, cx, cy, colores, ang=0.0):
        base, dark, _ = colores
        t = ("dinamico", tag)
        self.canvas.delete(tag)
        for pts, tipo in self._forma():
            rot  = self._rotar(pts, ang)
            flat = [v for xy in rot for v in (cx + xy[0], cy + xy[1])]
            if tipo == "vent":
                self.canvas.create_polygon(flat, fill="white", outline="", tags=t)
            elif tipo == "dark":
                self.canvas.create_polygon(flat, fill=dark, outline=dark, width=0.5, tags=t)
            else:
                self.canvas.create_polygon(flat, fill=base, outline=dark, width=1, tags=t)
        self.canvas.tag_raise(tag)

    def _centro(self, tag):
        items = self.canvas.find_withtag(tag)
        if not items:
            return (0, 0)
        x1, y1, x2, y2 = self.canvas.bbox(items[0])
        return ((x1+x2)/2, (y1+y2)/2)

    def distancia(self, x1, y1, x2, y2):
        return math.sqrt((x2-x1)**2 + (y2-y1)**2) * 0.621

    # ── Inicializar simulación ─────────────────────────────────────────────
    def inicializar(self):
        self.canvas.delete("dinamico")
        for i in range(0, 1200, 50):
            self.canvas.create_line(i, 0, i, 700, fill=COLOR_GRID, tags="dinamico")
        for j in range(0, 700, 50):
            self.canvas.create_line(0, j, 1200, j, fill=COLOR_GRID, tags="dinamico")
        for n, (x, y) in self.paises.items():
            self.canvas.create_oval(x-6, y-6, x+6, y+6,
                                    fill=COLOR_PUNTO, outline="white", tags="dinamico")
            self.canvas.create_text(x, y-12, text=n, fill=COLOR_PUNTO,
                                    font=(TIPO_FUENTE, 10, "bold"), tags="dinamico")

        x, y = self.paises["Ecuador"]
        self._dibujar("avion_auto",   x,   y,   CAUTO)
        self._dibujar("avion_manual", x+6, y+2, CMAN)

        self.d_auto = 0.0; self.t_auto = 0.0
        self.d_man  = 0.0; self.last_pos = (x+6, y+2)
        self.angulo_manual = 0.0

        self.lbl_auto.config(
            text="\n✈ AUTOMÁTICO\n\n Status: En Espera\n📏 0.00 mi\n🌍 Total: 0.00 mi\n⏱ 0.00s\n")
        self.lbl_manual.config(
            text=f"\n🎮 MANUAL\n\n📏 Movimiento: 0.00 mi\n🌍 Total: 0.00 mi\n📍 Pos: ({int(x+6)}, {int(y+2)})\n")

    # ── Vuelo automático ───────────────────────────────────────────────────
    def iniciar_vuelo(self):
        if self.en_vuelo:
            return
        self.en_vuelo = True
        self.btn_ini.config(state="disabled")
        self._tramo(list(self.paises.keys()), 0, 0)

    def _tramo(self, ruta, idx, paso):
        if not self.en_vuelo:
            return
        if idx >= len(ruta) - 1:
            self.en_vuelo = False
            self.btn_ini.config(state="normal")
            return

        o, d   = ruta[idx], ruta[idx+1]
        x1, y1 = self.paises[o]
        x2, y2 = self.paises[d]

        if paso == 0:
            self.canvas.create_line(x1, y1, x2, y2,
                                    fill="#5A1FDB", width=3, tags="dinamico")

        nx  = x1 + (x2-x1) * paso / 100
        ny  = y1 + (y2-y1) * paso / 100
        ang = self._ang(x2-x1, y2-y1)
        self._dibujar("avion_auto", nx, ny, CAUTO, ang)

        self.d_auto += self.distancia(x1, y1, x2, y2) / 100
        self.t_auto += 0.03
        self.lbl_auto.config(
            text=f"\n✈ AUTOMÁTICO\n{o} → {d}\n\n"
                 f"📏 {self.distancia(x1,y1,nx,ny):.2f} mi\n"
                 f"🌍 Total: {self.d_auto:.2f} mi\n"
                 f"⏱ {self.t_auto:.2f}s\n")

        if paso < 100:
            self.animacion_id = self.root.after(30, lambda: self._tramo(ruta, idx, paso+1))
        else:
            self.animacion_id = self.root.after(30, lambda: self._tramo(ruta, idx+1, 0))

    # ── Control manual ─────────────────────────────────────────────────────
    def _mover_man(self, nx, ny, ang):
        self._dibujar("avion_manual", nx, ny, CMAN, ang)
        self.angulo_manual = ang
        lx, ly = self.last_pos
        d = self.distancia(lx, ly, nx, ny)
        self.d_man  += d
        self.last_pos = (nx, ny)
        self.lbl_manual.config(
            text=f"\n🎮 MANUAL\n\n"
                 f"📏 Movimiento: {d:.2f} mi\n"
                 f"🌍 Total: {self.d_man:.2f} mi\n"
                 f"📍 Pos: ({int(nx)}, {int(ny)})\n")

    def mover_manual(self, event):
        paso = 10
        dx = -paso if event.keysym == "a" else paso if event.keysym == "d" else 0
        dy = -paso if event.keysym == "w" else paso if event.keysym == "s" else 0
        if dx == 0 and dy == 0:
            return
        cx, cy = self._centro("avion_manual")
        self._mover_man(cx+dx, cy+dy, self._ang(dx, dy))

    def start_drag(self, event):
        self.dragging   = True
        self._drag_last = (event.x, event.y)

    def drag(self, event):
        if not self.dragging:
            return
        x, y = max(0, min(event.x, 1200)), max(0, min(event.y, 700))
        lx, ly = self._drag_last
        dx, dy  = x - lx, y - ly
        ang = self._ang(dx, dy) if abs(dx) > 0.5 or abs(dy) > 0.5 else self.angulo_manual
        self._mover_man(x, y, ang)
        self._drag_last = (x, y)

    # ── Reset ──────────────────────────────────────────────────────────────
    def reset(self):
        if self.animacion_id:
            self.root.after_cancel(self.animacion_id)
        self.animacion_id = None
        self.en_vuelo     = False
        self.btn_ini.config(state="normal")
        self.inicializar()


if __name__ == "__main__":
    root = tk.Tk()
    SimuladorMapa(root)
    root.mainloop()
