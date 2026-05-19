FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99

# Dependencias base + Python + Flask
RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y \
        wine \
        wine32 \
        wine64 \
        wget \
        xvfb \
        x11vnc \
        novnc \
        websockify \
        cabextract \
        winbind \
        python3 \
        python3-pip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Instalar Flask y dependencias de la API
RUN pip3 install flask==3.0.3

# Instalar winetricks
RUN wget -q https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks \
    -O /usr/local/bin/winetricks && \
    chmod +x /usr/local/bin/winetricks

# Descargar instalador MT5
RUN wget -q https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe \
    -O /tmp/mt5setup.exe

# Copiar scripts y API
COPY start.sh /start.sh
COPY api.py /api.py
RUN chmod +x /start.sh

# Puertos:
# 5900 = VNC (acceso visual a MT5)
# 6080 = noVNC (navegador)
# 8080 = API Flask (para N8N)
EXPOSE 5900 6080 8080

ENV WINEPREFIX=/root/.wine
ENV WINEDEBUG=-all
ENV MT5_API_KEY=cambia-esta-clave-en-railway
ENV MT5_MAX_LOTE=0.01
ENV MT5_STOP_DIARIO_PCT=5
ENV API_PORT=8080

CMD ["/start.sh"]
