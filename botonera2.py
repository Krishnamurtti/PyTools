# -*- coding: utf-8 -*-
import csv, os
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window

APP_TITLE = "Botonera Compacta"
CSV_FILENAME = "eventos_compactos.csv"

# Colores por bloque/fase
C = {
    "ataque": (0.13, 0.7, 0.13, 1),           # verde
    "defensa": (0.85, 0.2, 0.2, 1),           # rojo
    "trans_def": (1.0, 0.5, 0.5, 1),          # rojo claro
    "trans_of": (0.6, 0.9, 0.6, 1),           # verde claro
    "abp_of": (0.2, 0.55, 0.2, 1),            # verde ABP of.
    "abp_def": (0.6, 0.2, 0.2, 1),            # rojo ABP def.
    "global": (0.7, 0.7, 0.7, 1),
}

def two_lines(txt: str) -> str:
    p = txt.split()
    return txt if len(p) <= 1 else p[0] + "\n" + " ".join(p[1:])

def csv_path(app):
    return os.path.join(app.user_data_dir, CSV_FILENAME)

def ensure_csv(path):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["ts", "cronometro", "bloque", "zona", "evento"])

class Stopwatch(Label):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.elapsed = 0.0
        self.running = False
        self.text = "00:00.0"
        self._ev = None
    def start(self, *a):
        if not self.running:
            self.running = True
            self._ev = Clock.schedule_interval(self._tick, 0.1)
    def stop(self, *a):
        if self.running and self._ev:
            self._ev.cancel(); self._ev = None; self.running = False
    def reset(self, *a):
        self.stop(); self.elapsed = 0.0; self.text = "00:00.0"
    def _tick(self, dt):
        self.elapsed += dt
        t = int(self.elapsed * 10); m = t // 600; s = (t % 600) // 10; d = t % 10
        self.text = f"{m:02d}:{s:02d}.{d}"
    def ts(self): return self.text

class Section(BoxLayout):
    def __init__(self, title, color, zones_dict, logger, **kw):
        super().__init__(orientation="vertical", spacing=dp(6), **kw)
        # Cabecera
        header = Label(text=title, size_hint_y=None, height=dp(28))
        self.add_widget(header)
        # Zonas: cada una en caja con grid
        for zona, items in zones_dict.items():
            self.add_widget(self._zone_box(title, zona, items, color, logger))

    def _zone_box(self, bloque, zona, items, color, logger):
        box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(120))
        title = Label(text=zona.upper(), size_hint_y=None, height=dp(22))
        box.add_widget(title)
        grid = GridLayout(cols=4, spacing=dp(6), padding=dp(6))
        for it in items:
            btn = Button(
                text=two_lines(it),
                size_hint_y=None,
                height=dp(44),
                background_normal='',
                background_color=color,
                halign='center', valign='middle'
            )
            btn.bind(size=lambda inst, _=None: setattr(inst, "text_size", (inst.width-dp(8), None)))
            btn.bind(on_press=lambda inst, b=bloque, z=zona, e=it: logger(b, z, e))
            grid.add_widget(btn)
        box.add_widget(grid)
        return box

class BotoneraCompacta(App):
    def build(self):
        self.title = APP_TITLE
        if hasattr(Window, "size"): Window.size = (950, 720)

        root = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(6))

        # Estado + CSV
        ensure_csv(csv_path(self))
        self.status = Label(text="Listo", size_hint_y=None, height=dp(22))

        # Cronómetro + barra global (OK/KO/Sistema/Banquillo/Faltas/Offside)
        top = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(6))
        self.sw = Stopwatch(font_size=dp(22), size_hint=(None, 1), width=dp(120))
        top.add_widget(self.sw)
        for t, cb in [("Start", self.sw.start), ("Stop", self.sw.stop), ("Reset", self.sw.reset)]:
            top.add_widget(Button(text=t, size_hint=(None, 1), width=dp(80), on_press=cb))
        # Botones globales
        for name in ["OK", "KO", "SISTEMA", "BANQUILLO", "FALTA FAVOR", "FALTA CONTRA", "OFFSIDE FAVOR", "OFFSIDE CONTRA"]:
            btn = Button(text=two_lines(name), size_hint=(None, 1), width=dp(120),
                         background_normal='', background_color=C["global"])
            btn.bind(size=lambda inst, _=None: setattr(inst, "text_size", (inst.width-dp(6), None)))
            btn.bind(on_press=lambda inst, n=name: self.log("GLOBAL", "GLOBAL", n))
            top.add_widget(btn)
        root.add_widget(top)

        # Scroll principal
        scroll = ScrollView()
        wrap = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8))
        wrap.bind(minimum_height=wrap.setter("height"))

        # ATAQUE (Inicios / Creación / Finalización)
        ataque = {
            "INICIOS": ["En juego", "Presión", "No presión", "Saque puerta", "Largo"],
            "CREACIÓN": ["Conectan MC", "Por dentro", "Lado a lado", "Diagonal", "Posicionamiento", "Por fuera"],
            "FINALIZACIÓN": ["Centro lateral", "Profundidad", "Tiro", "Duelo", "Desmarque", "Ocasión"],
        }
        wrap.add_widget(Section("Ataque", C["ataque"], ataque, self.log))

        # DEFENSA (Inicios / Creación DEF / Finalización DEF)
        defensa = {
            "INICIOS DEF": ["B. alto", "No presión", "Portero", "Saque puerta", "Largo"],
            "CREACIÓN DEF": ["Basculación", "Espacios", "Son superados", "Ayudas", "Distancia líneas", "Duelos"],
            "FINALIZACIÓN DEF": ["Continuencia", "Profundidad", "Tiro", "Centro lateral", "Altura/Área", "Ocasión"],
        }
        wrap.add_widget(Section("Defensa", C["defensa"], defensa, self.log))

        # RECUPERACIÓN / TRANSICIONES (dos tiras como en la imagen)
        trans_rec = {
            "PÉRDIDA": ["Pérdida"],
            "RECUPERACIÓN": ["Recuperación"],
        }
        # Para simplificar visual, dos zonas con 1 botón cada una y colores de transición
        wrap.add_widget(Section("Transición Defensiva", C["trans_def"], {"RECUPERACIÓN": ["Recuperación"]}, self.log))
        wrap.add_widget(Section("Transición Ofensiva", C["trans_of"], {"PÉRDIDA": ["Pérdida"]}, self.log))

        # ABP OF y ABP DEF (dos franjas)
        abp_of = {"ABP OF": ["Corner OF", "F. Frontal OF", "F. Lateral OF"]}
        abp_def = {"ABP DEF": ["Corner DEF", "Falta DEF", "F. Lateral DEF"]}
        wrap.add_widget(Section("ABP OFENSIVA", C["abp_of"], abp_of, self.log))
        wrap.add_widget(Section("ABP DEFENSIVA", C["abp_def"], abp_def, self.log))

        scroll.add_widget(wrap)
        root.add_widget(scroll)

        root.add_widget(self.status)
        return root

    def log(self, bloque, zona, evento):
        ts = datetime.now().isoformat(timespec="seconds")
        with open(csv_path(self), "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([ts, self.sw.ts(), bloque, zona, evento])
        self.status.text = f"{self.sw.ts()} | {bloque} > {zona} > {evento}"

if __name__ == "__main__":
    BotoneraCompacta().run()
