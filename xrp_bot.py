import time
import logging
from binance.client import Client
from binance.enums import *
import pandas as pd
import numpy as np

API_KEY = "ضع_API_KEY_هنا"
API_SECRET = "ضع_API_SECRET_هنا"

SYMBOL = "XRPUSDT"
LEVERAGE = 10
TRADE_USDT = 9
TAKE_PROFIT = 0.02
STOP_LOSS = 0.01
TIMEFRAMES = ["15m", "1h", "4h"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s", handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()])
log = logging.getLogger()

client = Client(API_KEY, API_SECRET)

def set_leverage():
    try:
        client.futures_change_leverage(symbol=SYMBOL, leverage=LEVERAGE)
        log.info(f"تم تعيين الرافعة: {LEVERAGE}x")
    except Exception as e:
        log.error(f"خطأ في الرافعة: {e}")

def get_klines(timeframe, limit=200):
    klines = client.futures_klines(symbol=SYMBOL, interval=timeframe, limit=limit)
    df = pd.DataFrame(klines, columns=["time","open","high","low","close","volume","close_time","quote_vol","trades","taker_base","taker_quote","ignore"])
    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)
    return df

def calc_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def calc_rsi(series, period=6):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calc_macd(series):
    ema12 = calc_ema(series, 12)
    ema26 = calc_ema(series, 26)
    dif = ema12 - ema26
    dea = calc_ema(dif, 9)
    return dif, dea

def analyze(timeframe):
    df = get_klines(timeframe)
    close = df["close"]
    volume = df["volume"]
    ema20 = calc_ema(close, 20)
    ema55 = calc_ema(close, 55)
    rsi = calc_rsi(close, 6)
    dif, dea = calc_macd(close)
    vol_ma10 = volume.rolling(10).mean()
    last = -1
    vol_ok = volume.iloc[last] > vol_ma10.iloc[last]
    if ema20.iloc[last] > ema55.iloc[last] and rsi.iloc[last] > 50 and vol_ok and dif.iloc[last] > dea.iloc[last]:
        return "LONG"
    elif ema20.iloc[last] < ema55.iloc[last] and rsi.iloc[last] < 50 and vol_ok and dif.iloc[last] < dea.iloc[last]:
        return "SHORT"
    return None

def get_confirmed_signal():
    signals = [analyze(tf) for tf in TIMEFRAMES]
    log.info(f"الإشارات: {signals}")
    if all(s == "LONG" for s in signals):
        return "LONG"
    elif all(s == "SHORT" for s in signals):
        return "SHORT"
    return None

def get_quantity(price):
    return round((TRADE_USDT * LEVERAGE) / price, 1)

def open_trade(signal, price):
    qty = get_quantity(price)
    side = SIDE_BUY if signal == "LONG" else SIDE_SELL
    try:
        client.futures_create_order(symbol=SYMBOL, side=side, type=ORDER_TYPE_MARKET, quantity=qty)
        tp_price = round(price * (1 + TAKE_PROFIT if signal == "LONG" else 1 - TAKE_PROFIT), 4)
        sl_price = round(price * (1 - STOP_LOSS if signal == "LONG" else 1 + STOP_LOSS), 4)
        close_side = SIDE_SELL if signal == "LONG" else SIDE_BUY
        client.futures_create_order(symbol=SYMBOL, side=close_side, type=FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET, stopPrice=tp_price, closePosition=True, timeInForce=TIME_IN_FORCE_GTC)
        client.futures_create_order(symbol=SYMBOL, side=close_side, type=FUTURE_ORDER_TYPE_STOP_MARKET, stopPrice=sl_price, closePosition=True, timeInForce=TIME_IN_FORCE_GTC)
        log.info(f"صفقة {signal} | TP: {tp_price} | SL: {sl_price}")
    except Exception as e:
        log.error(f"خطأ: {e}")

def has_open_position():
    positions = client.futures_position_information(symbol=SYMBOL)
    return any(float(p["positionAmt"]) != 0 for p in positions)

def run():
    log.info("البوت يعمل الآن")
    set_leverage()
    while True:
        try:
            if has_open_position():
                log.info("يوجد صفقة مفتوحة")
            else:
                price = float(client.futures_symbol_ticker(symbol=SYMBOL)["price"])
                signal = get_confirmed_signal()
                if signal:
                    open_trade(signal, price)
                else:
                    log.info("لا توجد إشارة")
            time.sleep(900)
        except Exception as e:
            log.error(f"خطأ: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run()
