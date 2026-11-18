"""Ayudante para probar la interfaz con cliclick. Las coordenadas son las de la interfaz en puntos (gfx con
SC = 2 en retina = puntos de pantalla); el origen se toma de la ventana real del FX (tests/winid.swift)."""
import pathlib, subprocess, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
GY0 = 53            # alto de la barra de título + barra de presets de REAPER sobre el área gráfica (puntos)


def window():
    out = subprocess.run(["swift", str(ROOT / "tests/winid.swift")], capture_output=True, text=True).stdout.split()
    if not out: raise SystemExit("no está abierta la ventana del FX (tests/reopen.sh)")
    wid, x, y, w, h = (float(v) for v in out[:5])
    return int(wid), x, y, w, h


WID, WX, WY, WW, WH = window()
OX, OY = WX, WY + GY0
W, H = WW, WH - GY0                                    # tamaño del área de la interfaz

# layout (mismas fórmulas que el JSFX, SC = 1)
TOPH, PANH, FOOTH = 44, 228, 26
DY = TOPH + 10
DH = max(H - TOPH - PANH - FOOTH - 20, 140)
MX0 = W - 14 - 96
TS = min(DH, (W - 96 - 90) * 0.42)
TX, TY = MX0 - 16 - TS, DY + (DH - TS) * 0.5
HX, HGW = 40, TX - 16 - 40
PY = DY + DH + 10
FLH = int(TS * 0.62)

PRESETS = (230, 22)
LISTEN = lambda k: ((407, 488, 572)[k], 22)
MODE = lambda k: ((125, 239)[k], PY + 20)
BAND = lambda k: ((405, 496, 604)[k], PY + 20)
KNOB = lambda i: (52 + 80 * i, PY + 92)            # Ataque, Cola, Sensibilidad, Duracion, Mantener, Caida, Lookahead
SMALL = lambda i: (46 + 72 * i, PY + 184)          # Corte, Mezcla, Ganancia
FORMA = (TX + TS / 2, TY + TS / 2)
HIST = (HX + HGW / 2, DY + DH / 2)


def pt(x, y): return f"{round(OX + x)},{round(OY + y)}"
def _cl(*a): subprocess.run(["cliclick", *a], check=True)


def cc(*args, wait=0.45):
    """como cliclick, pero c: y dc: son presiones explícitas (con REAPER cargado se pierden los clics muy cortos)
    y antes de apretar en un punto nuevo se mueve el mouse ahí y se espera un cuadro de la interfaz."""
    for a in args:
        k, _, p = a.partition(":")
        if k in ("c", "dc", "rc", "dd"):
            _cl("m:" + p); time.sleep(0.25)
        if k == "c":
            _cl("dd:" + p); time.sleep(0.12); _cl("du:" + p)
        elif k == "dc":
            _cl("dd:" + p); time.sleep(0.07); _cl("du:" + p); time.sleep(0.07)
            _cl("dd:" + p); time.sleep(0.07); _cl("du:" + p)
            time.sleep(1.0)   # si enseguida corre un script de REAPER (dump) se puede perder el arrastre siguiente
        else:
            _cl("-w", "200", a)
    time.sleep(wait)


def wheel(n): subprocess.run(["swift", str(ROOT / "tests/scroll.swift"), str(n)], check=True); time.sleep(0.5)
def shot(path): subprocess.run(["screencapture", "-x", "-o", f"-l{WID}", path], check=True); return path
def focus(): subprocess.run(["osascript", "-e", 'tell application "REAPER" to activate']); time.sleep(0.6); cc(f"c:{round(WX + 300)},{round(WY + 12)}")


def drag(x0, y0, x1, y1, steps=8):
    cc(f"dd:{pt(x0, y0)}", wait=0.15)
    for k in range(1, steps + 1): cc(f"dm:{pt(x0 + (x1 - x0) * k / steps, y0 + (y1 - y0) * k / steps)}", wait=0.08)
    cc(f"du:{pt(x1, y1)}")


def dump():
    p = ROOT / "tests/out/dump.txt"; p.unlink(missing_ok=True)
    subprocess.Popen(["/Applications/REAPER.app/Contents/MacOS/REAPER", "-nonewinst", str(ROOT / "tests/ui_dump.lua")],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        if p.exists() and "done" in p.read_text(): break
        time.sleep(0.25)
    d = {}
    for line in p.read_text().splitlines():
        if "|" in line:
            i, n, f, v = line.split("|"); d[n] = (f, float(v))
    return d


def param(name, raw=False):
    """valor de un parámetro por su nombre (p. ej. 'Ataque'): texto formateado o valor crudo."""
    for n, (f, v) in dump().items():
        if n.startswith(name): return v if raw else f
    return None


def menu_item(k, x, y, row=24, top=3):
    """clic en la fila k (0 = primera) de un menú que se abrió con el mouse en (x, y)."""
    cc(f"c:{pt(x + 30, y + top + row * k + row / 2)}", wait=0.7)
