import requests
from time import sleep

# Настройки
TELEGRAM_TOKEN = '7423664576:AAEp4qRlj-47puKPLAg1tLYptLkED6yH2HM'
CHAT_ID = '-1002379376855'
CHECK_INTERVAL = 60
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

# Функция для отправки сообщений в Telegram
def send_telegram_message(message):
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(TELEGRAM_URL, data=data, timeout=10)
        response.raise_for_status()
        print(f"Message sent successfully: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка отправки сообщения в Telegram: {e}")

# Функция для получения данных стакана
def fetch_order_book(symbol, limit=100):
    url = f'https://api.binance.com/api/v3/depth?symbol={symbol}&limit={limit}'
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        order_book = response.json()
        return order_book['bids'], order_book['asks']
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса стакана Binance: {e}")
        return [], []

# Функция для расчета глубины рынка
def calculate_market_depth(order_book):
    total_usdt = 0
    total_amount = 0
    for i, (price, amount) in enumerate(order_book):
        price = float(price)
        amount = float(amount)
        total_usdt += price * amount
        total_amount += amount
    return total_usdt, total_amount

# Функция для проверки крупных ордеров
def check_large_orders(order_book, threshold=100000):
    large_orders = []
    for price, amount in order_book:
        price = float(price)
        amount = float(amount)
        order_value = price * amount
        if order_value >= threshold:
            large_orders.append((price, amount, order_value))
    return large_orders

# Основная функция отслеживания стакана
def track_order_book():
    print("Начало отслеживания стакана...")
    pair = 'ETHUSDT'

    while True:
        try:
            bids, asks = fetch_order_book(pair)

            # Рассчитать глубину покупок и продаж
            total_bids_usdt, total_bids_amount = calculate_market_depth(bids)
            total_asks_usdt, total_asks_amount = calculate_market_depth(asks)

            # Найти крупные ордера
            large_bid_orders = check_large_orders(bids)
            large_ask_orders = check_large_orders(asks)

            # Отправить сообщение о крупных ордерах
            for price, amount, value in large_bid_orders:
                send_telegram_message(
                    f"<b>Крупный ордер на покупку:</b>\n"
                    f"Цена: {price:.2f} USDT, Количество: {amount:.4f} ETH, Сумма: {value:.2f} USDT"
                )

            for price, amount, value in large_ask_orders:
                send_telegram_message(
                    f"<b>Крупный ордер на продажу:</b>\n"
                    f"Цена: {price:.2f} USDT, Количество: {amount:.4f} ETH, Сумма: {value:.2f} USDT"
                )

            # Определить доминирование в процентах
            total_volume = total_bids_usdt + total_asks_usdt
            if total_volume > 0:
                bids_percentage = (total_bids_usdt / total_volume) * 100
                asks_percentage = (total_asks_usdt / total_volume) * 100

                if bids_percentage > asks_percentage:
                    dominance_message = f"Больше покупок на {bids_percentage - asks_percentage:.2f}%"
                elif asks_percentage > bids_percentage:
                    dominance_message = f"Больше продаж на {asks_percentage - bids_percentage:.2f}%"
                else:
                    dominance_message = "Покупки и продажи равны"
            else:
                dominance_message = "Нет данных для расчета доминирования"

            # Отправить сообщение о доминировании
            send_telegram_message(f"<b>Доминирование:</b> {dominance_message}")

        except Exception as e:
            print(f"Общая ошибка: {e}")
        sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    track_order_book()
