# -*- coding: utf-8 -*-
import os, csv
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

APP_TITLE = "Botonera Táctica (Compacta)"
CSV_FILENAME = "eventos_compactos.csv"

# Paleta (RGBA 0-1)
COL = {
    "ATAQUE": (0.13, 0.70, 0.13, 1.0),          # verde
    "DEFENSA": (0.85, 0.20, 0.20, 1.0),         # rojo
    "TRANS_DEF": (1.00, 0.50, 0.50, 1.0),       # rojo claro
    "TRANS_OF": (0.60, 0.90, 0.60, 1.0),        # verde claro
    "ABP_OF": (0.25, 0.60, 0.25, 1.0),
    "ABP_DEF": (0.65, 0.25, 0.25, 1.0),
    "GLOBAL": (0.75, 0.75, 0.75, 1.0),
}

def two_lines(txt: str) -> str:
    parts = txt.split()
    return txt if len(parts) <= 1 else parts[0] + "\n" + " ".join(parts[1:])

def csv_path(app: App) -> str:
    return os.path.join(app.user_data_dir, CSV_FILENAME)

def ensure_csv(path: str):
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
        t = int(self.elapsed * 10)
        m, s, d = t // 600, (t % 600) // 10, t % 10
        self.text = f"{m:02d}:{s:02d}.{d}"
    def ts(self): return self.text

class Section(BoxLayout):
    def __init__(self, titulo, color, zonas, logger, **kw):
        super().__init__(orientation="vertical", spacing=dp(4), **kw)
        head = Label(text=titulo, size_hint_y=None, height=dp(22))
        self.add_widget(head)
        for zona, items in zonas.items():
            self.add_widget(self._zona(zona, items, color, logger, titulo))

    def _zona(self, zona, items, color, logger, bloque):
        cont = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(110))
        lab = Label(text=zona, size_hint_y=None, height=dp(20))
        cont.add_widget(lab)
        grid = GridLayout(cols=6, spacing=dp(4), padding=dp(4))
        for it in items:
            btn = Button(
                text=two_lines(it),
                size_hint_y=None,
                height=dp(40),
                background_normal='',              # color sólido
                background_color=color,            # color por bloque
                halign='center', valign='middle'
            )
            # Centrar y permitir 2 líneas
            btn.bind(size=lambda inst, _=None: setattr(inst, "text_size", (inst.width - dp(6), None)))
            btn.bind(on_press=lambda inst, b=bloque, z=zona, e=it: logger(b, z, e))
            grid.add_widget(btn)
        cont.add_widget(grid)
        return cont

class BotoneraApp(App):
    def build(self):
        self.title = APP_TITLE
        if hasattr(Window, "size"):
            Window.size = (980, 680)  # útil en desktop para ver el layout

        ensure_csv(csv_path(self))

        root = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(6))
        self.status = Label(text="Listo", size_hint_y=None, height=dp(20))

        # Barra superior: Cronómetro + controles + globales (OK/KO/Sistema/Banquillo/Faltas/Offside)
        top = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(6))
        self.sw = Stopwatch(font_size=dp(22), size_hint=(None, 1), width=dp(120))
        top.add_widget(self.sw)
        for t, cb in [("Start", self.sw.start), ("Stop", self.sw.stop), ("Reset", self.sw.reset)]:
            top.add_widget(Button(text=t, size_hint=(None, 1), width=dp(80), on_press=cb))
        for name in ["OK", "KO", "SISTEMA", "BANQUILLO", "FALTA CONTRA", "FALTA FAVOR", "Fuera de\nJuego A", "Fuera de\nJuego R"]:
            btn = Button(text=name, size_hint=(None, 1), width=dp(120),
                         background_normal='', background_color=COL["GLOBAL"],
                         halign='center', valign='middle')
            btn.bind(size=lambda inst, _=None: setattr(inst, "text_size", (inst.width - dp(6), None)))
            btn.bind(on_press=lambda inst, n=name: self.log("GLOBAL", "GLOBAL", n))
            top.add_widget(btn)
        root.add_widget(top)

        # Cuerpo con scroll
        scroll = ScrollView()
        wrap = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8))
        wrap.bind(minimum_height=wrap.setter("height"))

        # Ataque (Inicios / Creación / Finalización)
        ataque = {
            "INICIOS": ["En juego", "Presión", "No presión", "Saque de\npuerta", "Largo"],
            "CREACIÓN": ["Conectan MC", "Por dentro", "Lado a lado", "Diagonal", "Posicionamiento", "Por fuera"],
            "FINALIZACIÓN": ["Centro lateral", "Profundidad", "Tiro", "Duelo", "Desmarque", "Ocasión"],
        }
        wrap.add_widget(Section("Ataque", COL["ATAQUE"], ataque, self.log))

        # Banda “Pérdida”
        wrap.add_widget(Section("Pérdida", COL["TRANS_OF"], {"PÉRDIDA": ["Pérdida"]}, self.log))

        # Defensa (Inicios DEF / Creación DEF / Finalización DEF)
        defensa = {
            "INICIOS DEF": ["B. alto", "No presión", "Portero", "Saque de\npuerta", "Largo"],
            "CREACIÓN DEF": ["Basculación", "Espacios", "Son superados", "Ayudas", "Distancia\nlíneas", "Duelos"],
            "FINALIZACIÓN DEF": ["Continuencia", "Profundidad", "Tiro", "Centro lateral", "Altura/Área", "Ocasión"],
        }
        wrap.add_widget(Section("Defensa", COL["DEFENSA"], defensa, self.log))

        # Banda “Recuperación”
        wrap.add_widget(Section("Recuperación", COL["TRANS_DEF"], {"RECUPERACIÓN": ["Recuperación"]}, self.log))

        # ABP OF
        abp_of = {"ABP OF": ["Corner OF", "F. Frontal OF", "F. Lateral OF"]}
        wrap.add_widget(Section("ABP OFENSIVA", COL["ABP_OF"], abp_of, self.log))

        # ABP DEF
        abp_def = {"ABP DEF": ["Corner DEF", "Falta DEF", "F. Lateral DEF"]}
        wrap.add_widget(Section("ABP DEFENSIVA", COL["ABP_DEF"], abp_def, self.log))

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
    BotoneraApp().run()
