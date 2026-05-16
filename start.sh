#!/bin/bash
set -e

echo "=== Iniciando Xvfb ==="
Xvfb :99 -screen 0 1024x768x24 -nolisten tcp &
XVFB_PID=$!
sleep 5

export DISPLAY=:99

echo "=== Verificando display ==="
xdpyinfo >/dev/null 2>&1 && echo "Display OK" || echo "Display FAIL"

echo "=== Iniciando VNC ==="
x11vnc -display :99 -nopw -listen 0.0.0.0 -xkb -forever -bg
sleep 2

echo "=== Iniciando noVNC ==="
websockify --web /usr/share/novnc 6080 localhost:5900 &
sleep 2

echo "=== Inicializando Wine ==="
export WINEPREFIX=/root/.wine
export WINEDEBUG=-all
wineboot --init 2>/dev/null || true
sleep 10

MT5_EXE="$WINEPREFIX/drive_c/Program Files/MetaTrader 5/terminal64.exe"

if [ ! -f "$MT5_EXE" ]; then
    echo "=== Instalando MetaTrader 5 ==="
    wine /tmp/mt5setup.exe /auto
    sleep 60
fi

echo "=== Iniciando MetaTrader 5 ==="
wine "$MT5_EXE" &

echo "=== Contenedor corriendo, esperando... ==="
wait $XVFB_PID
