"""Pruebas de la interfaz con el mouse (cliclick). Abre antes la demo: tests/reopen.sh 24 (preset "Por defecto").
OJO: mueve el mouse de verdad; no usar la Mac mientras corre. Con otras sesiones, envolver con /tmp/nube-reaper.lock."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from ui import *

fails = 0


def check(name, got, want):
    global fails
    ok = want(got) if callable(want) else got == want
    fails += not ok
    print(f"{'OK ' if ok else 'MAL'} {name:52s} {got!r}")


def num(s): return float(s.split()[0]) if s else float("nan")


focus()
check("arranca con Por defecto (ataque 0, cola 0)", (num(param("Ataque")), num(param("Cola"))), (0, 0))

# ---- botones
for k, want in ((1, "Continuo"), (0, "Golpe")):
    cc(f"c:{pt(*MODE(k))}"); check(f"modo: clic en {want}", param("Modo"), want)
for k, want in ((1, "Solo graves"), (2, "Solo agudos"), (0, "Todo")):
    cc(f"c:{pt(*BAND(k))}"); check(f"banda: clic en {want}", param("Banda"), want)
for k, want in ((2, "Solo lo que cambia"), (1, "Solo la banda"), (0, "Normal")):
    cc(f"c:{pt(*LISTEN(k))}"); check(f"escuchar: clic en {want}", param("Escuchar"), want)

# ---- perillas
x, y = KNOB(0); drag(x, y, x, y - 44)
check("arrastrar Ataque hacia arriba: sube (~ +9.6 dB)", num(param("Ataque")), lambda v: 7 < v < 12)
cc(f"dc:{pt(x, y)}"); check("doble clic en Ataque = 0", num(param("Ataque")), 0.0)
time.sleep(1.0)   # tras un doble clic + script de REAPER se puede perder el arrastre siguiente
x, y = KNOB(1); cc(f"m:{pt(x, y)}"); drag(x, y, x, y + 44)
check("arrastrar Cola hacia abajo: baja (~ -12 dB)", num(param("Cola")), lambda v: -14 < v < -9)
x, y = KNOB(5); cc(f"m:{pt(x, y)}"); c0 = num(param("Caida")); wheel(5)
check("rueda sobre Caida: cambia", num(param("Caida")), lambda v: v != c0)
x, y = SMALL(1); drag(x, y, x, y + 110)
check("arrastrar Mezcla hacia abajo: 50 %", num(param("Mezcla")), lambda v: 45 <= v <= 55)
cc(f"dc:{pt(x, y)}"); check("doble clic en Mezcla = 100", num(param("Mezcla")), 100.0)

# ---- gráficas
c0 = num(param("Cola")); drag(FORMA[0], FORMA[1], FORMA[0], FORMA[1] + 40)
check("forma: arrastrar 40 px abajo baja la Cola ~9.6 dB", num(param("Cola")), lambda v: c0 - 12 < v < c0 - 7)
m0 = num(param("Mantener")); drag(FORMA[0], FORMA[1], FORMA[0] + 64, FORMA[1])
check("forma: arrastrar a la derecha alarga Mantener", num(param("Mantener")), lambda v: v > m0 + 50)
cc(f"m:{pt(*HIST)}"); a0 = num(param("Ataque")); wheel(4)
# macOS acelera la rueda: no siempre llegan 120 por muesca (0.5 dB); basta con que suba
check("rueda arriba sobre el historial: sube el Ataque", num(param("Ataque")), lambda v: v > a0 + 0.4)

# ---- presets
cc(f"c:{pt(*PRESETS)}", wait=0.9); menu_item(1, *PRESETS)
check("menú de presets: Snare (Nube baja)", (num(param("Cola")), num(param("Mantener")), num(param("Caida"))), (-4, 70, 130))
print("FALLAS:", fails)
sys.exit(1 if fails else 0)
