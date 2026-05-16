#!/bin/bash

# Limpiar locks anteriores
rm -f /tmp/.X99-lock /tmp/.X11-unix/X99

# Iniciar display virtual
Xvfb :99 -screen 0 1920x1080x24 &
sleep 5

# Exportar display - CRÍTICO para Wine
export DISPLAY=:99

echo "Display: $DISPLAY"

# Iniciar VNC
x11vnc -display :99 -passwd ${VNC_PASSWORD} -listen 0.0.0.0 -xkb -forever -noxdamage &
sleep 2

# Iniciar noVNC
websockify --web /usr/share/novnc 6080 localhost:5900 &
sleep 2

# Configurar Wine
export WINEPREFIX=/root/.wine
export WINEDEBUG=-all

wineboot --init &
sleep 15

MT5_EXE="$WINEPREFIX/drive_c/Program Files/MetaTrader 5/terminal64.exe"

if [ ! -f "$MT5_EXE" ]; then
    echo "Instalando MetaTrader 5..."
    DISPLAY=:99 wine /tmp/mt5setup.exe /auto
    sleep 60
fi

echo "Iniciando MetaTrader 5..."
DISPLAY=:99 wine "$MT5_EXE" &

# Mantener contenedor vivo
tail -f /dev/null
