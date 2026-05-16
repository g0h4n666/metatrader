#!/bin/bash
set -e

Xvfb :99 -screen 0 1024x768x16 &
sleep 3

x11vnc -display :99 -nopw -listen 0.0.0.0 -xkb -forever &

websockify --web /usr/share/novnc 6080 localhost:5900 &

winecfg /v win10 2>/dev/null || true
sleep 5

MT5_EXE="$HOME/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe"

if [ ! -f "$MT5_EXE" ]; then
    echo "Instalando MetaTrader 5..."
    wine /tmp/mt5setup.exe /auto
    sleep 30
fi

echo "Iniciando MetaTrader 5..."
wine "$MT5_EXE"
