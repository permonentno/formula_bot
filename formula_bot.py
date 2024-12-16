import requests
from time import sleep

# Настройки
TELEGRAM_TOKEN = '7423664576:AAEp4qRlj-47puKPLAg1tLYptLkED6yH2HM'  # Токен для работы с Telegram API
CHAT_ID = '-1002379376855'  # Идентификатор чата Telegram, куда будут отправляться сообщения
CHECK_INTERVAL = 120  # Интервал проверки стакана в секундах
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"  # URL для отправки сообщений в Telegram
HEADERS = {'User-Agent': 'Mozilla/5.0'}  # Заголовок для запросов к API Binance

# Функция для отправки сообщений в Telegram
def send_telegram_message(message):
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}  # Данные для отправки сообщения
    try:
        response = requests.post(TELEGRAM_URL, data=data, timeout=10)  # Отправка POST-запроса в Telegram API
        response.raise_for_status()  # Проверка на успешность выполнения запроса
        print(f"Message sent successfully: {response.json()}")  # Лог успешной отправки
    except requests.exceptions.RequestException as e:
        print(f"Ошибка отправки сообщения в Telegram: {e}")  # Лог ошибки при отправке

# Функция для получения данных стакана
def fetch_order_book(symbol, limit=100):
    url = f'https://api.binance.com/api/v3/depth?symbol={symbol}&limit={limit}'  # URL для запроса данных стакана
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)  # Отправка GET-запроса в API Binance
        response.raise_for_status()  # Проверка на успешность выполнения запроса
        order_book = response.json()  # Обработка JSON-ответа
        return order_book['bids'], order_book['asks']  # Возврат списков заявок на покупку и продажу
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса стакана Binance: {e}")  # Лог ошибки при запросе стакана
        return [], []

# Функция для расчета глубины рынка
def calculate_market_depth(order_book):
    total_usdt = 0  # Общая сумма заявок в USDT
    total_amount = 0  # Общий объем заявок
    for i, (price, amount) in enumerate(order_book):  # Итерация по заявкам в стакане
        price = float(price)  # Преобразование цены в число с плавающей точкой
        amount = float(amount)  # Преобразование объема в число с плавающей точкой
        total_usdt += price * amount  # Увеличение суммы заявок
        total_amount += amount  # Увеличение объема заявок
    return total_usdt, total_amount  # Возврат общей суммы и объема заявок

# Функция для проверки крупных ордеров
def check_large_orders(order_book, threshold=100000):
    large_orders = []  # Список крупных ордеров
    for price, amount in order_book:  # Итерация по заявкам в стакане
        price = float(price)  # Преобразование цены в число с плавающей точкой
        amount = float(amount)  # Преобразование объема в число с плавающей точкой
        order_value = price * amount  # Расчет общей стоимости ордера
        if order_value >= threshold:  # Проверка, превышает ли ордер заданный порог
            large_orders.append((price, amount, order_value))  # Добавление ордера в список крупных
    return large_orders  # Возврат списка крупных ордеров

# Основная функция отслеживания стакана
def track_order_book():
    print("Начало отслеживания стакана...")  # Сообщение в консоли о запуске отслеживания
    pair = 'ETHUSDT'  # Торговая пара для анализа

    while True:
        try:
            bids, asks = fetch_order_book(pair)  # Получение данных стакана

            # Рассчитать глубину покупок и продаж
            total_bids_usdt, total_bids_amount = calculate_market_depth(bids)  # Глубина покупок
            total_asks_usdt, total_asks_amount = calculate_market_depth(asks)  # Глубина продаж

            # Найти крупные ордера
            large_bid_orders = check_large_orders(bids)  # Крупные заявки на покупку
            large_ask_orders = check_large_orders(asks)  # Крупные заявки на продажу

            # Отправить сообщение о крупных ордерах
            for price, amount, value in large_bid_orders:  # Итерация по крупным заявкам на покупку
                send_telegram_message(
                    f"<b>Крупный ордер на покупку:</b>\n"
                    f"Цена: {price:.2f} USDT, Количество: {amount:.4f} ETH, Сумма: {value:.2f} USDT"
                )

            for price, amount, value in large_ask_orders:  # Итерация по крупным заявкам на продажу
                send_telegram_message(
                    f"<b>Крупный ордер на продажу:</b>\n"
                    f"Цена: {price:.2f} USDT, Количество: {amount:.4f} ETH, Сумма: {value:.2f} USDT"
                )

            # Определить доминирование в процентах
            total_volume = total_bids_usdt + total_asks_usdt  # Общий объем покупок и продаж
            if total_volume > 0:
                bids_percentage = (total_bids_usdt / total_volume) * 100  # Доля покупок в процентах
                asks_percentage = (total_asks_usdt / total_volume) * 100  # Доля продаж в процентах

                if bids_percentage > asks_percentage:  # Сравнение долей покупок и продаж
                    dominance_message = f"Больше покупок на {bids_percentage - asks_percentage:.2f}%"
                elif asks_percentage > bids_percentage:
                    dominance_message = f"Больше продаж на {asks_percentage - bids_percentage:.2f}%"
                else:
                    dominance_message = "Покупки и продажи равны"
            else:
                dominance_message = "Нет данных для расчета доминирования"  # Сообщение, если данных недостаточно

            # Отправить сообщение о доминировании
            send_telegram_message(f"<b>Доминирование:</b> {dominance_message}")  # Уведомление о доминировании

        except Exception as e:
            print(f"Общая ошибка: {e}")  # Лог ошибки в основной функции
        sleep(CHECK_INTERVAL)  # Задержка перед следующим запросом

if __name__ == "__main__":
    track_order_book()  # Запуск основной функции

