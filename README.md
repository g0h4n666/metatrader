MetaTrader 5 + API Flask en Railway
Servicios que corre este contenedor
Puerto	Servicio	Acceso
5900	VNC	Solo interno
6080	noVNC (navegador)	Público opcional
8080	API Flask para N8N	Solo interno Railway
Variables de entorno requeridas en Railway
Configúralas en Railway → tu servicio metatrader → Variables:
```
VNC_PASSWORD=tu-password-vnc
MT5_API_KEY=tu-clave-secreta-para-n8n
MT5_MAX_LOTE=0.01
MT5_STOP_DIARIO_PCT=5
API_PORT=8080
```
URL interna para N8N
Desde N8N usa siempre la URL interna (nunca la pública):
```
http://metatrader.railway.internal:8080
```
Endpoints disponibles
GET /health
Sin autenticación. Verifica que la API está viva.
```bash
curl http://metatrader.railway.internal:8080/health
```
GET /estado
Requiere X-API-Key. Verifica si MT5 está corriendo.
```bash
curl -H "X-API-Key: tu-clave" \
     http://metatrader.railway.internal:8080/estado
```
POST /orden
Requiere X-API-Key. Ejecuta una orden en MT5.
```bash
curl -X POST \
     -H "X-API-Key: tu-clave" \
     -H "Content-Type: application/json" \
     -d '{
       "accion": "COMPRAR",
       "simbolo": "BTCUSD",
       "lote": 0.01,
       "sl_pips": 50,
       "tp_pips": 100,
       "confianza": 8
     }' \
     http://metatrader.railway.internal:8080/orden
```
Reglas de seguridad automáticas:
Confianza mínima: 7/10 (configurable)
Lote máximo: MT5_MAX_LOTE (default 0.01)
Rate limit: 5 órdenes por minuto
API key obligatoria en header X-API-Key
Pasos para activar
Sube estos archivos a tu repositorio GitHub
Railway redesplegará automáticamente
En Railway → Variables agrega las variables de entorno
En Railway → Networking NO generes dominio público para el puerto 8080
En N8N usa `http://metatrader.railway.internal:8080`
