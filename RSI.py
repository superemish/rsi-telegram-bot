"""
Bot de trading RSI con datos cada 1 minuto (Binance API)
Envía alertas por Telegram cuando RSI cruza zonas clave.
"""

import time
import pandas as pd
import requests
import ta
from datetime import datetime

# -------- CONFIGURACIÓN GENERAL --------
SYMBOL = "BTCUSDT"
INTERVAL = "1m"       # Temporalidad de 1 minuto
LIMIT = 200           # Se necesitan al menos 200 velas para RSI

RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

TELEGRAM_TOKEN = "8058989918:AAE_xgTnAFJNHnyu20NdkNJYXuj6HUiDKmc"
TELEGRAM_CHAT_IDS = ["1570066712"]

# -------- FUNCIONES --------

def enviar_telegram(mensaje: str) -> None:
    """Envía mensaje a los chats autorizados por Telegram"""
    for chat_id in TELEGRAM_CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": mensaje}
        try:
            r = requests.post(url, data=payload)
            if r.status_code == 200:
                print(f"✅ Mensaje enviado a {chat_id}")
            else:
                print(f"❌ Error al enviar a {chat_id}: {r.text}")
        except Exception as e:
            print(f"❌ Excepción al enviar a {chat_id}: {e}")

def obtener_datos_binance(symbol: str, interval: str, limit: int) -> pd.DataFrame:
    """Obtiene datos OHLC de Binance en tiempo real"""
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    data = requests.get(url, timeout=10).json()
    df = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df["close"] = pd.to_numeric(df["close"])
    return df

def detectar_senial_rsi(df: pd.DataFrame) -> str | None:
    """Analiza RSI y genera alertas según cruces"""
    rsi_indicator = ta.momentum.RSIIndicator(close=df["close"], window=RSI_PERIOD)
    df["rsi"] = rsi_indicator.rsi()

    prev_rsi = df["rsi"].iloc[-2]
    curr_rsi = df["rsi"].iloc[-1]

    if prev_rsi < RSI_OVERSOLD and curr_rsi >= RSI_OVERSOLD:
        return "🟢 RSI cruzó 30 ↑ desde sobreventa. Posible entrada LONG."
    if prev_rsi > RSI_OVERBOUGHT and curr_rsi <= RSI_OVERBOUGHT:
        return "🔴 RSI cruzó 70 ↓ desde sobrecompra. Posible entrada SHORT."
    if curr_rsi < RSI_OVERSOLD:
        return "⚠️ RSI sigue en zona de sobreventa (<30). Sin confirmación aún."
    if curr_rsi > RSI_OVERBOUGHT:
        return "⚠️ RSI sigue en zona de sobrecompra (>70). Sin confirmación aún."

    return None

# -------- MAIN LOOP --------

def main():
    print("📡 Bot RSI activo (1m)...")
    enviar_telegram("✅ Bot RSI con intervalo 1m iniciado.")

    ultimo_mensaje = None

    while True:
        try:
            df = obtener_datos_binance(SYMBOL, INTERVAL, LIMIT)
            mensaje = detectar_senial_rsi(df)
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if mensaje and mensaje != ultimo_mensaje:
                print(f"[{ahora}] Alerta: {mensaje}")
                enviar_telegram(f"📢 ALERTA RSI 1m {SYMBOL} ({ahora}):\n{mensaje}")
                ultimo_mensaje = mensaje
            elif mensaje == ultimo_mensaje:
                print(f"[{ahora}] Mismo estado. No se envía alerta.")
            else:
                print(f"[{ahora}] Sin señales RSI.")

        except Exception as e:
            print(f"❌ Error en ejecución: {e}")

        time.sleep(60)

if __name__ == "__main__":
    main()
