try:
    print(client.futures_account())
except Exception as e:
    print(f"خطأ الاتصال: {e}")
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
        tp_price = round(price * (1 + TAKE_PROFIT) if signal == "LONG" else price * (1 - TAKE_PROFIT), 4)
        sl_price = round(price * (1 - STOP_LOSS) if signal == "LONG" else price * (1 + STOP_LOSS), 4)
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
