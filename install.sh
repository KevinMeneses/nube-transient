#!/bin/zsh
# Instala Nube Transient en REAPER (macOS) como enlace: los cambios del repo se ven al volver a insertar el FX.
set -e
DST="$HOME/Library/Application Support/REAPER/Effects/Nube Transient"
cd "$(dirname "$0")"
mkdir -p "$DST"
ln -sf "$PWD/nube_transient.jsfx" "$DST/nube_transient.jsfx"
echo "Listo: en REAPER busca \"Nube Transient\" en el navegador de FX (JS: Nube Transient)."
