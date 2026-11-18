#!/bin/zsh
# Cierra la demo de la interfaz (si hay) y la vuelve a abrir con el código nuevo. Uso: tests/reopen.sh [preset [audio]]
cd "$(dirname "$0")"
R=/Applications/REAPER.app/Contents/MacOS/REAPER
mkdir -p out
rm -f out/ui.txt; $R -nonewinst "$PWD/ui_close.lua" >/dev/null 2>&1 &
for i in $(seq 1 20); do grep -q closed out/ui.txt 2>/dev/null && break; sleep 0.5; done
echo "${1:-22} ${2:-}" > out/demo_opts.txt   # REAPER no hereda las variables de entorno
rm -f out/ui.txt; $R -nonewinst "$PWD/ui_demo.lua" >/dev/null 2>&1 &
for i in $(seq 1 30); do grep -q done out/ui.txt 2>/dev/null && break; sleep 0.5; done; sleep 2
echo listo
