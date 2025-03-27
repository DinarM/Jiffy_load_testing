import uuid
from locust import HttpUser, constant, task, between, events
from locust.clients import HttpSession

from utils.endpoints import verify_customer

# picker_codes = ['JIFFN4GA7G', 'JIFFN4GA85']
# picker_codes = ['JIFFN4GA7G', 'JIFFN4GA85', 'JIFFN4GA8W', 'JIFFN4GA9K', 'JIFFN4GAAM', 'JIFFN4GAB9', 'JIFFN4GACF']
picker_codes = ['JIFFN4GA7G', 'JIFFN4GA85', 'JIFFN4GA8W', 'JIFFN4GA9K', 'JIFFN4GAAM', 'JIFFN4GAB9', 'JIFFN4GACF', 'JIFFN4GADD', 'JIFFN4GAEE', 'JIFFN4GAFV', 'JIFFN4GAGH', 'JIFFN4GAH9', 'JIFFN4GAHT', 'JIFFN4GAIQ', 'JIFFN4GAJD', 'JIFFN4GAZZ', 'JIFFN4GB0P', 'JIFFN4GB1O', 'JIFFN4DR3L', 'JIFFN4DR4W', 'JIFFN4DR5Y', 'JIFFN4DR6W', 'JIFFN4DR7T', 'JIFFN4DR97', 'JIFFN4DRAH', 'JIFFN4DRBN', 'JIFFN4DRCO', 'JIFFN4G9Y1', 'JIFFN4G9ZI', 'JIFFN4GA1R', 'JIFFN4GA2V', 'JIFFN4GA3K', 'JIFFN4GA4M', 'JIFFN4GA5T', 'JIFFN4GAO3', 'JIFFN4GAQJ', 'JIFFN4GARC', 'JIFFN4GAS7', 'JIFFN4GATD', 'JIFFN4GAUI', 'JIFFN4GAVG', 'JIFFN4GAW9', 'JIFFN4GAX4', 'JIFFN4GAYN', 'JIFFN4DR25', 'JIFFN4G9XA', 'JIFFN4GAK0', 'JIFFN4GAKS', 'JIFFN4GALR', 'JIFFN4GAMH', 'JIFFN4GANB', 'JIFFN4GAOP', 'JIFFN4GAPJ']


PICKERS = [{"token": token} for token in picker_codes]

# URL-адреса (взято из urls.py - не выносил в параметры запуска)
STAGE = "stage"
URL = {
    'AUTH_TOKEN': f'https://api2-{STAGE}.jiffy-team.com/auth/v1/auth/sign-in/token',
    'WAREHOUSE_AUTH': f'https://api2-{STAGE}.jiffy-team.com/picking/v2/auth/warehouse',
    'UNFINISHED_ORDERS': f'https://api2-{STAGE}.jiffy-team.com/picking/v2/picking-orders/unfinished',
    'NEXT_ITEM': f'https://api2-{STAGE}.jiffy-team.com/picking/v2/picking-orders/{{}}/items/next',
    'SCAN_ITEM': f'https://api2-{STAGE}.jiffy-team.com/picking/v2/picking-items/{{}}/scan',
    'PACK_ORDER': f'https://api2-{STAGE}.jiffy-team.com/picking/v2/picking-orders/{{}}/pack',
    'FINISH_ORDER': f'https://api2-{STAGE}.jiffy-team.com/picking/v2/picking-orders/{{}}/finish',
    'ASSIGN_ORDERS': f'https://api2-{STAGE}.jiffy-team.com/picking/v2/picking-orders/assign',
}


class DeliveryUser(HttpUser):
    wait_time = constant(0)  # Интервал между задачами - то есть 1 секунда между запросом для каждого пользователя нагрузочного теста - НЕ курьеры
    host = f"https://api2-{STAGE}.jiffy-team.com"  # Базовый URL

    def on_start(self):
        # Подымаем курьеров
        if not PICKERS:
            raise Exception("Нет доступных пикеров")
        self.picker = PICKERS.pop(0)  # Берем первого курьера - остальные по циклу будут подтягиваться
        self.token = None

        # Авторизация - вроде ничего не напутал.
        headers = {"accept": "application/json, text/plain, */*"}
        payload = {"token": self.picker["token"]}
        with self.client.post(URL["AUTH_TOKEN"], json=payload, headers=headers, catch_response=True) as resp:
            if resp.status_code == 200:
                self.token = f"Bearer {resp.json()['data']['access_token']}"
            else:
                resp.failure(f"Auth failed for {self.picker['token']}: {resp.text}")
                raise Exception("Не удалось авторизоваться")
        
        self.warehouse_auth()
  
    def get_headers(self):
        # Апдейт заголовков
        return {
            "accept": "application/json, text/plain, */*",
            "authorization": self.token,
            "content-type": "application/json"
        }

    @task(10)  # Основная задача курьеров (вес 10) - т.е. она выполняется чаще чем задача с весом 1. Теоретически будет баланс создания заказов и их движения
    def process_picker(self):
        # Логика обработки статусов курьера
        # Запрос информации о курьере
        with self.client.get(URL["UNFINISHED_ORDERS"], headers=self.get_headers(), name="UNFINISHED_ORDERS", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"UNFINISHED_ORDERS failed: {resp.text}")
                return
            data = resp.json()

        if data['data'] is not None:
            self.scan_items(order_id=data['data']['id'])
        else:
            with self.client.put(URL["ASSIGN_ORDERS"], headers=self.get_headers(), name="ASSIGN_ORDERS", catch_response=True) as resp:
                if resp.status_code != 200:
                    resp.failure(f"ASSIGN_ORDERS failed: {resp.text}")
            data = resp.json()
            if data.get('data') is not None:
                self.scan_items(order_id=data['data']['id'])


    def warehouse_auth(self, warehouse_code='VAN1'):
        payload = {'warehouseCode': warehouse_code,  'currentTerminalId': str(uuid.uuid4())}
        with self.client.post(URL["WAREHOUSE_AUTH"], json=payload, headers=self.get_headers(), catch_response=True) as resp:
            data = resp.json()
            if resp.status_code != 200 or data.get('code') == 'USER_ALREADY_LOGGED':
                resp.failure(f"Warehouse_auth failed: {resp.text}")


    def scan_items(self, order_id):
        while True:
            with self.client.get(URL["NEXT_ITEM"].format(order_id), headers=self.get_headers(), name="NEXT_ITEM", catch_response=True) as resp:
                if resp.status_code != 200:
                    resp.failure(f"NEXT_ITEM failed: {resp.text}")

            data = resp.json()
            
            if data['data']['item'] is None:
                break
            else:
                productBarcodes = data['data']['item']['productBarcodes']
                item_id = data['data']['item']['id']
                self.scan_item(item_id=item_id, barcode=productBarcodes[0])

        self.pack_order(order_id=order_id)
        self.finish_order(order_id=order_id)


    def scan_item(self, item_id, barcode, quantity=1):
        payload = {'barcode': barcode, 'quantity': quantity}
        with self.client.post(URL["SCAN_ITEM"].format(item_id), json=payload, headers=self.get_headers(), name="SCAN_ITEM", catch_response=True) as resp:
            if resp.status_code != 204:
                resp.failure(f"SCAN_ITEM failed: {resp.text}")


    def pack_order(self, order_id, package_count=2):
        payload = {'count': package_count}
        with self.client.put(URL["PACK_ORDER"].format(order_id), json=payload, headers=self.get_headers(), name="PACK_ORDER", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"PACK_ORDER failed: {resp.text}")


    def finish_order(self, order_id, package_count=2):
        payload = {'count': package_count}
        with self.client.put(URL["FINISH_ORDER"].format(order_id), json=payload, headers=self.get_headers(), name="FINISH_ORDER", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"FINISH_ORDER failed: {resp.text}")



# Здесь пуллинг для отчета
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    if exception:
        print(f"Запрос {name} завершился с ошибкой: {exception}")
    else:
        print(f"Запрос {name} выполнен за {response_time} мс")

if __name__ == "__main__":
    import os
    os.system(f"locust -f {__file__} --users 5 --spawn-rate 1")