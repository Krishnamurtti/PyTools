# -*- coding: utf-8 -*-
import csv
import os
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label

APP_TITLE = "Botonera Táctica"
CSV_FILENAME = "eventos_tacticos.csv"

# Categorías por fases y zonas
CATEGORIAS = {
    "Ofensiva": {
        "Inicio": ["Salida 3", "2+1", "Portero-Lateral", "Directa", "Tercer hombre", "Hombre libre", "Atracción-Cambio"],
        "Creación": ["Superar L1", "Superar L2", "Superar L3", "Fijar-Liberar", "Pared", "Cambio orientación", "Ocupar carriles", "Alturas", "2ª línea"],
        "Finalización": ["Centro 1º palo", "Centro 2º palo", "Centro atrás", "Tiro a puerta", "Tiro fuera", "Tiro bloqueado", "Remate cabeza", "xG alto", "xG bajo"],
    },
    "Transición defensiva": {
        "Inicio": ["Pérdida pase", "Pérdida control", "Pérdida regate"],
        "Creación": ["Presión tras pérdida", "Falta táctica", "Repliegue"],
        "Finalización": ["Recuperación <5s", "Prog rival", "Ocasión en contra", "Tiro concedido"],
    },
    "Defensiva": {
        "Inicio": ["Bloque alto", "Bloque medio", "Bloque bajo", "Gatillo pase atrás", "Gatillo control orientado", "Gatillo espaldas"],
        "Creación": ["Salto", "Cobertura", "Temporización", "Basculación", "Cerrar interior", "Cerrar exterior", "Hombre libre"],
        "Finalización": ["Recuperación", "Forzar atrás", "Despeje", "Falta táctica", "Ocasión concedida", "Tiro concedido"],
    },
    "Transición ofensiva": {
        "Inicio": ["Robo", "Intercepción", "Segundo balón"],
        "Creación": ["Contra directo", "Ataque organizado", "Superioridad", "Igualdad", "Inferioridad", "≤3 pases", "4-7 pases", "≥8 pases"],
        "Finalización": ["Finaliza con tiro", "Finaliza con pase clave", "Pérdida", "Ocasión"],
    },
}

# ABP a favor/en contra con subtipos
ABP = {
    "ABP a favor": {
        "Córner": ["Corto", "Largo", "1º palo", "2º palo"],
        "Falta frontal": ["Directa", "Indirecta", "Bloqueos"],
        "Falta lateral": ["Corto", "Largo", "Pantallas"],
    },
    "ABP en contra": {
        "Córner": ["Zona", "Hombre", "Mixto"],
        "Falta frontal": ["Barreras", "Vigilancias"],
        "Falta lateral": ["Zona", "Hombre", "Mixto"],
    },
}

BOTONES_GLOBALES = ["OK", "KO", "GOL a favor", "GOL en contra", "Offside a favor", "Offside en contra"]

def csv_path():
    # Guardar en almacenamiento interno de la app (user_data_dir) para compatibilidad Android
    return os.path.join(App.get_running_app().user_data_dir, CSV_FILENAME)

def ensure_csv_header(path):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ts_sistema", "cronometro", "grupo", "subgrupo", "boton"])

class Stopwatch(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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
            self._ev.cancel()
            self._ev = None
            self.running = False

    def reset(self, *a):
        self.stop()
        self.elapsed = 0.0
        self.text = "00:00.0"

    def _tick(self, dt):
        self.elapsed += dt
        total = int(self.elapsed * 10)
        m = total // 600
        s = (total % 600) // 10
        t = total % 10
        self.text = f"{m:02d}:{s:02d}.{t}"

    def timestamp(self):
        return self.text

class Botonera(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(6), padding=dp(6), **kwargs)

        # Barra superior: cronómetro y controles
        top = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(6))
        self.sw = Stopwatch(font_size=dp(22), size_hint=(None, 1), width=dp(120))
        top.add_widget(self.sw)
        top.add_widget(Button(text="Start", size_hint=(None, 1), width=dp(80), on_press=self.sw.start))
        top.add_widget(Button(text="Stop", size_hint=(None, 1), width=dp(80), on_press=self.sw.stop))
        top.add_widget(Button(text="Reset", size_hint=(None, 1), width=dp(80), on_press=self.sw.reset))
        self.add_widget(top)

        # Tabs por FASE
        phases_tabs = TabbedPanel(do_default_tab=False, tab_height=dp(40))
        for fase, zonas in CATEGORIAS.items():
            t = TabbedPanelItem(text=fase)
            t.add_widget(self._zone_tabs(fase, zonas))
            phases_tabs.add_widget(t)
        self.add_widget(phases_tabs)

        # Barra global inferior: OK/KO, GOL ±, Offside ±
        global_bar = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(6))
        for name in BOTONES_GLOBALES:
            global_bar.add_widget(Button(text=name, on_press=lambda inst, n=name: self.log("Global", "Global", n)))
        self.add_widget(global_bar)

        # Tabs ABP
        abp_tabs = TabbedPanel(do_default_tab=False, tab_height=dp(40))
        for lado, tipos in ABP.items():
            t = TabbedPanelItem(text=lado)
            t.add_widget(self._abp_types(lado, tipos))
            abp_tabs.add_widget(t)
        self.add_widget(abp_tabs)

        # Estado y CSV
        self.status = Label(text="Listo", size_hint_y=None, height=dp(26))
        self.add_widget(self.status)
        ensure_csv_header(csv_path())

    def _zone_tabs(self, fase, zonas_dict):
        tabs = TabbedPanel(do_default_tab=False, tab_height=dp(36))
        for zona, botones in zonas_dict.items():
            tab = TabbedPanelItem(text=zona)
            tab.add_widget(self._buttons_grid(fase, zona, botones))
            tabs.add_widget(tab)
        return tabs

    def _abp_types(self, lado, tipos_dict):
        tabs = TabbedPanel(do_default_tab=False, tab_height=dp(36))
        for tipo, variantes in tipos_dict.items():
            tab = TabbedPanelItem(text=tipo)
            tab.add_widget(self._buttons_grid(lado, tipo, variantes))
            tabs.add_widget(tab)
        return tabs

    def _buttons_grid(self, grupo, subgrupo, items):
        scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        grid = GridLayout(cols=3, spacing=dp(6), padding=dp(6), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        for txt in items:
            btn = Button(text=txt, size_hint_y=None, height=dp(44))
            btn.bind(on_press=lambda inst, g=grupo, s=subgrupo, x=txt: self.log(g, s, x))
            grid.add_widget(btn)
        scroll.add_widget(grid)
        return scroll

    def log(self, grupo, subgrupo, boton):
        ts_sys = datetime.now().isoformat(timespec="seconds")
        ts_chr = self.sw.timestamp() if self.sw else ""
        row = [ts_sys, ts_chr, grupo, subgrupo, boton]
        try:
            with open(csv_path(), "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(row)
            self.status.text = f"OK {ts_chr} | {grupo} > {subgrupo} > {boton}"
        except Exception as e:
            self.status.text = f"Error guardando: {e}"

class BotoneraApp(App):
    def build(self):
        self.title = APP_TITLE
        if hasattr(Window, "size"):
            Window.size = (430, 820)
        return Botonera()

if __name__ == "__main__":
    BotoneraApp().run()
