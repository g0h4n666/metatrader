# 🤖 Agente de Trading BTC · Railway
> Última actualización: 2026-05-19

---

## Stack tecnológico

| Componente | Tecnología | Estado |
|---|---|---|
| Terminal de trading | MetaTrader 5 (Wine + Docker) | ✅ Desplegado en Railway |
| Orquestador | N8N | ✅ Desplegado en Railway |
| LLM / Agente | OpenClaw | ✅ Desplegado en Railway |
| API bridge | Flask (Python) · puerto 8080 | ⚠️ Parcial — necesita corrección |
| Conexión interna | `metatrader.railway.internal:8080` | ✅ Configurado |
| Broker | Pepperstone · cuenta demo | 🔄 En proceso |
| Símbolo | BTCUSD | ✅ Definido |
| Alertas | Telegram | ✅ En workflow N8N |

---

## Decisiones de arquitectura tomadas

- **Bridge MT5 ↔ Python**: EA MQL5 (`BridgeEA.mq5`) corriendo dentro del terminal MT5, escuchando en `127.0.0.1:9090`. Flask reenvía comandos al EA via socket TCP. **No usar** `wine python.exe + MetaTrader5` (no funciona bajo Wine/Linux).
- **Conexión N8N ↔ MT5**: Red interna de Railway — `metatrader.railway.internal:8080`. Sin exposición pública.
- **Estrategias de trading (BTC)**:
  - Estrategia 1: EMA Crossover + RSI (seguimiento de tendencia)
  - Estrategia 2: Bollinger Bands + Volume (volatilidad)
  - Estrategia 3: MACD + Ichimoku Cloud (señales mediano plazo)
- **Confianza mínima para ejecutar**: 7/10
- **Lote máximo**: 0.01 (configurable via `MT5_MAX_LOTE`)
- **Rate limit API**: 5 órdenes por minuto

---

## Variables de entorno en Railway (pendiente configurar)

```env
MT5_LOGIN=<numero_cuenta_pepperstone>
MT5_PASSWORD=<clave_trading>
MT5_SERVER=Pepperstone-Demo
MT5_API_KEY=<clave_para_flask>
MT5_MAX_LOTE=0.01
```

---

## Problemas identificados en el código actual

### `api.py` — CRÍTICO
- `ejecutar_script_mt5()` usa `wine python.exe` con `import MetaTrader5` → **no funciona** (lib solo existe en Windows nativo)
- Endpoint `/precio` devuelve mensaje fijo, no precio real
- No hay endpoints `/posiciones` ni `/cerrar` → riesgo de órdenes duplicadas

### Workflow N8N — IMPORTANTE
- Nodo `Code — Indicadores`: RSI calculado con tabla estática basada en cambio 24h de CoinGecko → **no es RSI real**
- Se necesitan velas OHLCV reales (Binance API o similar) para calcular EMA, RSI, Bollinger, MACD, Ichimoku

---

## Tareas del proyecto

### ✅ Completadas
- [x] Análisis completo del repositorio (Dockerfile, api.py, start.sh, railway.toml, workflow N8N)
- [x] Diagnóstico del problema de conexión MT5 ↔ Python bajo Wine
- [x] Definición de arquitectura: EA MQL5 como bridge via socket
- [x] Selección de estrategias de trading para BTC
- [x] Confirmación de broker: Pepperstone demo

### 🔄 En curso
- [ ] Obtener credenciales demo Pepperstone (login + password + servidor exacto)

### 📋 Pendientes
- [ ] **T4** — Escribir `BridgeEA.mq5`: EA MQL5 que hace login a Pepperstone y escucha comandos JSON en `127.0.0.1:9090`
- [ ] **T5** — Corregir `api.py`: Flask se comunica con EA via socket TCP (reemplazar wine python.exe)
- [ ] **T6** — Actualizar `start.sh`: copiar `BridgeEA.ex5` al directorio Experts de Wine y activarlo en BTCUSD al arrancar
- [ ] **T7** — Implementar indicadores reales en N8N: velas OHLCV de Binance API → EMA, RSI, Bollinger, MACD, Ichimoku
- [ ] **T8** — Agregar endpoints `/posiciones` y `/cerrar` a `api.py`
- [ ] **T9** — Actualizar prompt del agente LLM (OpenClaw) para analizar las 3 estrategias y decidir acción
- [ ] **T10** — Pruebas end-to-end: N8N → Flask → EA → Pepperstone demo → respuesta

---

## Preguntas pendientes de confirmar

1. ¿Número de cuenta demo Pepperstone y servidor exacto? (`Pepperstone-Demo` o `Pepperstone-Demo01`)
2. ¿Timeframe de análisis? (opciones: 1m / 5m / 1h / 4h)
3. ¿El bot de Telegram ya está configurado en N8N?
4. ¿Los hosts internos de Railway están abriendo bien? (reportado como problema)

---

## Archivos del repositorio (metatrader-main)

| Archivo | Estado | Notas |
|---|---|---|
| `Dockerfile` | ✅ OK | Ubuntu 22.04 + Wine + Xvfb + Flask |
| `start.sh` | ⚠️ Actualizar | Agregar copia y activación del EA |
| `api.py` | ❌ Corregir | Bridge roto, endpoints faltantes |
| `railway.toml` | ✅ OK | Puerto 8080, hostname interno correcto |
| `workflow_n8n.json` | ⚠️ Actualizar | Indicadores reales, prompt LLM mejorado |
| `BridgeEA.mq5` | ❌ Crear | EA MQL5 — aún no existe |

---

## Cómo usar este archivo

Al inicio de cada sesión con Claude, sube este archivo o pega su contenido y di:
> "Continuemos el proyecto de trading, aquí está el PROJECT.md actualizado"

Claude retomará exactamente desde donde lo dejamos.
