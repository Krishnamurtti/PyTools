# main.py
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.clock import Clock
from kivy.utils import platform
import sqlite3, os
from datetime import datetime

KV = """
#:import MDSeparator kivymd.uix.separator.MDSeparator

<Header@MDLabel>:
    halign: "center"
    bold: True
    theme_text_color: "Custom"
    text_color: 1,1,1,1
    padding: 0, 8

<Slot@MDRaisedButton>:
    size_hint_y: None
    height: "48dp"
    on_release: app.log_descriptor(self.text)

BoxLayout:
    orientation: "vertical"

    MDToolbar:
        title: "Botonera Fútbol"
        elevation: 4

    # Cronómetro
    BoxLayout:
        size_hint_y: None
        height: "60dp"
        padding: "10dp"
        spacing: "10dp"
        MDLabel:
            id: timer_label
            text: "00:00.00"
            halign: "center"
            font_style: "H4"
        MDRaisedButton:
            id: start_btn
            text: "Start"
            on_release: app.toggle_timer()
        MDFlatButton:
            text: "Lap"
            on_release: app.add_lap()
        MDFlatButton:
            text: "Reset"
            on_release: app.reset_timer()

    ScrollView:
        do_scroll_x: False
        do_scroll_y: True

        MDBoxLayout:
            orientation: "vertical"
            adaptive_height: True

            # ENCABEZADOS DEF/ATQ
            BoxLayout:
                size_hint_y: None
                height: "48dp"
                canvas.before:
                    Color:
                        rgba: 0.85,0.25,0.2,1
                    Rectangle:
                        pos: self.pos
                        size: self.width/2, self.height
                    Color:
                        rgba: 0.2,0.7,0.3,1
                    Rectangle:
                        pos: self.x+self.width/2, self.y
                        size: self.width/2, self.height
                Header:
                    text: "DEFENSA"
                Header:
                    text: "ATAQUE"

            # Fila Inicio/Creación/Finalización para DEF y ATQ
            GridLayout:
                cols: 6
                size_hint_y: None
                height: self.minimum_height
                spacing: "2dp"
                # DEF
                Slot: text: "Inicio"
                Slot: text: "Creacion"
                Slot:
                    text: "Finalizacion"
                    md_bg_color: 0.5,0.5,0.5,1
                    text_color: 1,1,1,1
                # ATQ
                Slot: text: "Inicio"
                Slot: text: "Creacion"
                Slot:
                    text: "Finalizacion"
                    md_bg_color: 0.5,0.5,0.5,1
                    text_color: 1,1,1,1

            # Segunda fila (bloque alto, press, puerta, bascular, recuperar, combo)
            GridLayout:
                cols: 6
                spacing: "2dp"
                size_hint_y: None
                height: self.minimum_height
                Slot: text: "Bloque Alto"
                Slot: text: "Press"
                Slot: text: "Puerta"
                Slot: text: "Bascular"
                Slot: text: "Recuperar"
                Slot: text: "Centro / tiro / Duelo"

            # Tercera fila (corto/largo/corto, cambio orient, tiro, centro, desmarque)
            GridLayout:
                cols: 7
                spacing: "2dp"
                size_hint_y: None
                height: self.minimum_height
                Slot: text: "Corto"
                Slot: text: "Largo"
                Slot: text: "Corto"
                Slot: text: "Cambio Orient"
                Slot: text: "Tiro"
                Slot: text: "Centro"
                Slot: text: "Desmarque"

            # Cuarta fila (agresivo, pasivo, interior/exterior)
            GridLayout:
                cols: 5
                spacing: "2dp"
                size_hint_y: None
                height: self.minimum_height
                Slot: text: "Agresivo"
                Slot: text: "Pasivo"
                Slot: text: "Interior"
                Slot: text: "Exterior"
                Widget:

            # Franja OK / KO
            BoxLayout:
                size_hint_y: None
                height: "56dp"
                spacing: "2dp"
                MDRaisedButton:
                    text: "OK"
                    md_bg_color: 0.98,0.82,0.1,1
                    on_release: app.log_descriptor("OK")
                MDRaisedButton:
                    text: "KO"
                    md_bg_color: 0.35,0.2,0.05,1
                    text_color: 1,1,1,1
                    on_release: app.log_descriptor("KO")

            # Banda inferior categorías (TR/ABP) con colores
            GridLayout:
                cols: 4
                spacing: "2dp"
                size_hint_y: None
                height: self.minimum_height
                MDRaisedButton:
                    text: "TR. OF\\nRecuperacion"
                    md_bg_color: 0.8,0.95,0.8,1
                    on_release: app.set_category("TR. OF")
                MDRaisedButton:
                    text: "ABP DEF"
                    md_bg_color: 0.75,0.85,1,1
                    on_release: app.set_category("ABP DEF")
                MDRaisedButton:
                    text: "TR. DEF\\nPerdida"
                    md_bg_color: 0.95,0.8,0.8,1
                    on_release: app.set_category("TR. DEF")
                MDRaisedButton:
                    text: "ABP OF"
                    md_bg_color: 0.75,0.9,0.75,1
                    on_release: app.set_category("ABP OF")

            # Línea de ABP: izquierda y derecha
            GridLayout:
                cols: 6
                spacing: "2dp"
                size_hint_y: None
                height: self.minimum_height
                # Lado izquierdo
                Slot: text: "CORNER"
                Slot: text: "FALTA LAT"
                Slot: text: "FALTA FRONT"
                # Separador central invisible
                Widget:
                # Lado derecho
                Slot: text: "CORNER"
                Slot: text: "FALTA LAT"
                Slot: text: "FALTA FRONT"

            MDSeparator:
            MDLabel:
                id: current_cat
                text: "Categoría activa: -"
                halign: "center"
                theme_text_color: "Secondary"

            # Botones de categoría principales arriba (para modo rápido)
            GridLayout:
                cols: 3
                spacing: "6dp"
                size_hint_y: None
                height: self.minimum_height
                MDRaisedButton:
                    text: "DEFENSA"
                    md_bg_color: 0.9,0.2,0.2,1
                    text_color: 1,1,1,1
                    on_release: app.set_category("DEFENSA")
                MDRaisedButton:
                    text: "ATAQUE"
                    md_bg_color: 0.1,0.7,0.2,1
                    text_color: 1,1,1,1
                    on_release: app.set_category("ATAQUE")
                Widget:
"""

DB_NAME = "events.db"

class BotoneraApp(MDApp):
    sw_started = False
    sw_seconds = 0.0
    last_category = None
    _tick_event = None

    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Green"
        self._ensure_db()
        return Builder.load_string(KV)

    # --- DB ---
    def _db_path(self):
        if platform == "android":
            from android.storage import app_storage_path
            return os.path.join(app_storage_path(), DB_NAME)
        return DB_NAME

    def _ensure_db(self):
        conn = sqlite3.connect(self._db_path())
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT,
            half INTEGER,
            ms_from_start INTEGER,
            category TEXT,
            descriptor TEXT
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS laps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT,
            ms_from_start INTEGER,
            label TEXT
        )""")
        conn.commit(); conn.close()

    def _insert_click(self, category, descriptor):
        conn = sqlite3.connect(self._db_path())
        c = conn.cursor()
        now = datetime.utcnow().isoformat()
        ms = int(self.sw_seconds * 1000)
        half = 1 if ms < 45*60*1000 else 2
        c.execute("INSERT INTO clicks (ts, half, ms_from_start, category, descriptor) VALUES (?,?,?,?,?)",
                  (now, half, ms, category, descriptor))
        conn.commit(); conn.close()

    def _insert_lap(self, label):
        conn = sqlite3.connect(self._db_path())
        c = conn.cursor()
        now = datetime.utcnow().isoformat()
        ms = int(self.sw_seconds * 1000)
        c.execute("INSERT INTO laps (ts, ms_from_start, label) VALUES (?,?,?)", (now, ms, label))
        conn.commit(); conn.close()

    # --- Cronómetro ---
    def toggle_timer(self):
        self.sw_started = not self.sw_started
        self.root.ids.start_btn.text = "Stop" if self.sw_started else "Start"
        if self._tick_event is None:
            self._tick_event = Clock.schedule_interval(self._tick, 0.01)

    def _tick(self, dt):
        if self.sw_started:
            self.sw_seconds += dt
            self._render_time()

    def _render_time(self):
        total = self.sw_seconds
        minutes = int(total // 60)
        seconds = int(total % 60)
        hundredths = int((total - int(total)) * 100)
        self.root.ids.timer_label.text = f"{minutes:02d}:{seconds:02d}.{hundredths:02d}"

    def reset_timer(self):
        self.sw_started = False
        self.sw_seconds = 0.0
        self.root.ids.start_btn.text = "Start"
        self._render_time()

    def add_lap(self, label="Lap"):
        self._insert_lap(label)

    # --- Interacción ---
    def set_category(self, cat):
        self.last_category = cat
        self.root.ids.current_cat.text = f"Categoría activa: {cat}"
        self._insert_click(category=cat, descriptor=None)

    def log_descriptor(self, text):
        category = self.last_category if self.last_category else "SIN_CATEGORIA"
        self._insert_click(category=category, descriptor=text)

if __name__ == "__main__":
    BotoneraApp().run()
