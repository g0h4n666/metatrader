from flask import Flask, request, jsonify
from functools import wraps
import subprocess, os, time, logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

API_KEY    = os.getenv("MT5_API_KEY", "cambia-esta-clave")
MAX_LOTE   = float(os.getenv("MT5_MAX_LOTE", "0.01"))
STOP_PCT   = float(os.getenv("MT5_STOP_DIARIO_PCT", "5"))

# --- Rate limiting simple ---
_llamadas = []
MAX_POR_MINUTO = 5

def rate_limit():
    ahora = time.time()
    recientes = [t for t in _llamadas if ahora - t < 60]
    _llamadas.clear()
    _llamadas.extend(recientes)
    if len(recientes) >= MAX_POR_MINUTO:
        return False
    _llamadas.append(ahora)
    return True

# --- Decorador autenticación ---
def requiere_api_key(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "")
        if key != API_KEY:
            logging.warning(f"Acceso no autorizado desde {request.remote_addr}")
            return jsonify({"error": "No autorizado"}), 401
        if not rate_limit():
            logging.warning("Rate limit alcanzado")
            return jsonify({"error": "Demasiadas solicitudes, espera 1 minuto"}), 429
        return f(*args, **kwargs)
    return wrapper

# --- Script MQL5 para ejecutar orden via Wine ---
def ejecutar_script_mt5(accion, simbolo, lote, sl_pips, tp_pips):
    """
    Crea un archivo .mq5 temporal y lo ejecuta via Wine.
    MT5 debe estar corriendo para que funcione.
    """
    script = f"""
import MetaTrader5 as mt5

mt5.initialize()
symbol = "{simbolo}"
lote   = {lote}
sl     = {sl_pips}
tp     = {tp_pips}

info = mt5.symbol_info_tick(symbol)
if not info:
    print("ERROR: no se obtuvo precio")
    mt5.shutdown()
    exit(1)

if "{accion}" == "COMPRAR":
    order_type = mt5.ORDER_TYPE_BUY
    price = info.ask
    sl_price = price - sl * mt5.symbol_info(symbol).point * 10
    tp_price = price + tp * mt5.symbol_info(symbol).point * 10
elif "{accion}" == "VENDER":
    order_type = mt5.ORDER_TYPE_SELL
    price = info.bid
    sl_price = price + sl * mt5.symbol_info(symbol).point * 10
    tp_price = price - tp * mt5.symbol_info(symbol).point * 10
else:
    print("ESPERAR: sin orden")
    mt5.shutdown()
    exit(0)

request_data = {{
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": lote,
    "type": order_type,
    "price": price,
    "sl": sl_price,
    "tp": tp_price,
    "deviation": 20,
    "magic": 123456,
    "comment": "n8n-bot",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_IOC,
}}

result = mt5.order_send(request_data)
print(f"RESULTADO: {{result.retcode}} - {{result.comment}}")
mt5.shutdown()
"""
    # Guardar script Python temporal
    script_path = "/tmp/mt5_orden.py"
    with open(script_path, "w") as f:
        f.write(script)

    # Ejecutar con Python dentro de Wine (MT5 Python API)
    resultado = subprocess.run(
        ["wine", "python.exe", script_path],
        capture_output=True, text=True, timeout=30,
        env={**os.environ, "DISPLAY": ":99", "WINEPREFIX": "/root/.wine"}
    )
    return resultado.stdout, resultado.stderr, resultado.returncode

# --- Endpoints ---

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "servicio": "MT5 API", "version": "1.0"})

@app.route("/precio", methods=["GET"])
@requiere_api_key
def precio():
    simbolo = request.args.get("simbolo", "BTCUSD")
    logging.info(f"Consulta de precio: {simbolo}")
    return jsonify({
        "simbolo": simbolo,
        "mensaje": "Conecta MT5 Python API para precio en vivo",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    })

@app.route("/orden", methods=["POST"])
@requiere_api_key
def orden():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Body JSON requerido"}), 400

    accion  = data.get("accion", "ESPERAR").upper()
    simbolo = data.get("simbolo", "BTCUSD")
    lote    = float(data.get("lote", 0.01))
    sl_pips = int(data.get("sl_pips", 50))
    tp_pips = int(data.get("tp_pips", 100))
    confianza = int(data.get("confianza", 5))

    logging.info(f"Orden recibida: {accion} {simbolo} lote={lote} confianza={confianza}")

    # Validaciones
    if accion not in ["COMPRAR", "VENDER", "ESPERAR"]:
        return jsonify({"error": f"Acción inválida: {accion}"}), 400

    if lote > MAX_LOTE:
        return jsonify({"error": f"Lote {lote} supera el máximo permitido {MAX_LOTE}"}), 400

    if confianza < 7:
        logging.info(f"Orden rechazada por baja confianza: {confianza}/10")
        return jsonify({
            "status": "ignorada",
            "motivo": f"Confianza {confianza}/10 es menor al mínimo requerido (7)",
            "accion": accion
        })

    if accion == "ESPERAR":
        return jsonify({"status": "ok", "accion": "ESPERAR", "mensaje": "Sin orden ejecutada"})

    # Ejecutar en MT5
    stdout, stderr, code = ejecutar_script_mt5(accion, simbolo, lote, sl_pips, tp_pips)
    logging.info(f"MT5 stdout: {stdout}")
    if stderr:
        logging.error(f"MT5 stderr: {stderr}")

    return jsonify({
        "status": "ejecutada" if code == 0 else "error",
        "accion": accion,
        "simbolo": simbolo,
        "lote": lote,
        "confianza": confianza,
        "mt5_respuesta": stdout.strip(),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    })

@app.route("/estado", methods=["GET"])
@requiere_api_key
def estado():
    # Verificar si MT5 está corriendo
    resultado = subprocess.run(
        ["pgrep", "-f", "terminal64.exe"],
        capture_output=True, text=True
    )
    mt5_activo = resultado.returncode == 0
    return jsonify({
        "mt5_activo": mt5_activo,
        "display": os.getenv("DISPLAY", ":99"),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    })

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 8080))
    logging.info(f"API MT5 iniciando en puerto {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
