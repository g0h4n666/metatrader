FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99

# Instalar dependencias
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
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Instalar winetricks y dependencias de MT5
RUN wget -q https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks \
    -O /usr/local/bin/winetricks && \
    chmod +x /usr/local/bin/winetricks

# Descargar instalador MT5
RUN wget -q https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe \
    -O /tmp/mt5setup.exe

# Copiar scripts
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 5900 6080
ENV WINEPREFIX=/root/.wine
ENV WINEDEBUG=-all
CMD ["/start.sh"]
