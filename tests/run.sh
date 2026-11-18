#!/bin/zsh
# Renderiza los casos en REAPER (pestaña temporal) y verifica la respuesta. NUBE_CASE=a,b filtra casos.
cd "$(dirname "$0")/.."
PY=${NUBE_PY:-python3}   # necesita numpy, scipy y soundfile
[ -f tests/signals/hits.wav ] || $PY tests/make_signals.py
mkdir -p tests/out; rm -f tests/out/log.txt tests/out/only.txt
[ -n "$NUBE_CASE" ] && echo "$NUBE_CASE" > tests/out/only.txt
/Applications/REAPER.app/Contents/MacOS/REAPER -nonewinst "$PWD/tests/render_cases.lua" >/dev/null 2>&1 &
for i in $(seq 1 300); do grep -q done tests/out/log.txt 2>/dev/null && break; sleep 1; done
grep -q done tests/out/log.txt || { echo "REAPER no terminó (¿diálogo abierto?)"; exit 1; }
grep -i error tests/out/log.txt
$PY tests/check.py
