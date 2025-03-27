import uuid
from locust import HttpUser, constant, task, between, events
from locust.clients import HttpSession

from utils.endpoints import verify_customer

# Список курьеров можно ебануть больше
# phone_numbers = [
#     '0591707617', '06731579222', '07112233122', '07112233124', '07112233123',
#     '09233333333', '02494270000', '02494270001', '02494270002',
#     '02494270003', '02494270004', '02494270005', '02494270006', '02494270008', '02494270012', '02494270013', '02494270014', '02494270015', '02494270016', '02494270017'
# ]
phone_numbers = [
    '0591707617', '06731579222', '07112233122', '07112233124', '07112233123',
    '09233333333', '02494270000', '02494270001', '02494270002',
    '02494270003', '02494270004', '02494270005', '02494270006', '02494270008', '02494270012', '02494270013', '02494270014', '02494270015', '02494270016', '02494270017'
]

COURIERS = [{"phone": phone} for phone in phone_numbers]

# URL-адреса (взято из urls.py - не выносил в параметры запуска)
STAGE = "stage"
URL = {
    "USER_AUTH": f"https://api2-{STAGE}.jiffy-team.com/auth/v1/auth/otp/confirm",
    "CUSTOMER_AUTH": f"https://api2-{STAGE}.jiffy-team.com/customer/sms/verify",
    "COURIERS_INFO": f"https://api2-{STAGE}.jiffy-team.com/dispatcher/v1/mobile/couriers/info",
    "MARK_ONLINE": f"https://api2-{STAGE}.jiffy-team.com/dispatcher/v1/mobile/couriers/mark-online",
    "MARK_ARRIVAL": f"https://api2-{STAGE}.jiffy-team.com/dispatcher/v1/mobile/couriers/mark-arrival",
    "JOBS_GET_ASSIGNED": f"https://api2-{STAGE}.jiffy-team.com/dispatcher/v1/mobile/jobs/get-assigned",
    "JOB_ACCEPT": f"https://api2-{STAGE}.jiffy-team.com/dispatcher/v1/mobile/jobs/accept",
    "TASK_ON_POINT": f"https://api2-{STAGE}.jiffy-team.com/dispatcher/v1/mobile/tasks/on-point",
    "TASK_START": f"https://api2-{STAGE}.jiffy-team.com/dispatcher/v1/mobile/tasks/start",
    "TASK_COMPLETE": f"https://api2-{STAGE}.jiffy-team.com/dispatcher/v1/mobile/tasks/complete",
    "CREATE_ORDER": f"https://api2-{STAGE}.jiffy-team.com/orders/v2/orders/new",
}


class DeliveryUser(HttpUser):
    wait_time = constant(1)  # Интервал между задачами - то есть 1 секунда между запросом для каждого пользователя нагрузочного теста - НЕ курьеры
    host = f"https://api2-{STAGE}.jiffy-team.com"  # Базовый URL

    def on_start(self):
        # Подымаем курьеров
        if not COURIERS:
            raise Exception("Нет доступных курьеров")
        self.courier = COURIERS.pop(0)  # Берем первого курьера - остальные по циклу будут подтягиваться
        self.token = None

        # Авторизация - вроде ничего не напутал.
        headers = {"accept": "application/json, text/plain, */*"}
        payload = {"phone": self.courier["phone"], "code": "0000"}
        with self.client.post(URL["USER_AUTH"], json=payload, headers=headers, catch_response=True) as resp:
            if resp.status_code == 200:
                self.token = f"Bearer {resp.json()['data']['access_token']}"
            else:
                resp.failure(f"Auth failed for {self.courier['phone']}: {resp.text}")
                raise Exception("Не удалось авторизоваться")

    def get_headers(self):
        # Апдейт заголовков
        return {
            "accept": "application/json, text/plain, */*",
            "authorization": self.token,
            "content-type": "application/json"
        }

    @task(10)  # Основная задача курьеров (вес 10) - т.е. она выполняется чаще чем задача с весом 1. Теоретически будет баланс создания заказов и их движения
    def process_courier(self):
        # Логика обработки статусов курьера
        # Запрос информации о курьере
        with self.client.get(URL["COURIERS_INFO"], headers=self.get_headers(), name="couriers_info", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Couriers info failed: {resp.text}")
                return
            data = resp.json()
            courier_status = data.get("data", {}).get("courier", {}).get("courier", {}).get("status")
            active_jobs = data.get("data", {}).get("activeJob", {})

        # Обработка статусов
        if courier_status == "OFFLINE":
            self.mark_online()
        elif courier_status == "HEADING_TO_BASE":
            self.mark_arrival()
        elif courier_status in ["ASSIGNED_TO_JOB", "ACCEPTED_JOB"]:
            self.handle_assigned_job(active_jobs)
        elif courier_status == "PICKING_UP":
            self.handle_picking_up(active_jobs)
        elif courier_status == "DELIVERING":
            self.handle_delivering(active_jobs)

    # Методы для обработки статусов
    def mark_online(self):
        with self.client.post(URL["MARK_ONLINE"], headers=self.get_headers(), name="mark_online", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Mark online failed: {resp.text}")

    def mark_arrival(self):
        payload = {"warehouseId": "ad253466-cfce-4036-8a0c-9fc98018e132"}
        with self.client.post(URL["MARK_ARRIVAL"], json=payload, headers=self.get_headers(), name="mark_arrival", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Mark arrival failed: {resp.text}")

    def handle_assigned_job(self, active_jobs):
        if active_jobs:
            job_state = active_jobs.get("job", {}).get("state")
            if job_state == "IN_PROGRESS":
                pickup_tasks = active_jobs.get("pickupTasks", [])
                for task_item in pickup_tasks:
                    task = task_item.get("task", {})
                    if task.get("state") == "ASSIGNED_TO_JOB":
                        self.on_point(task.get("id"))
                    elif task.get("state") == "ON_POINT":
                        self.start_task(task.get("id"))
        else:
            with self.client.get(URL["JOBS_GET_ASSIGNED"], headers=self.get_headers(), name="get_assigned_jobs", catch_response=True) as resp:
                if resp.status_code == 200:
                    job = resp.json().get("data", {}).get("activeJob", {}).get("job", {})
                    if job.get("state") == "ASSIGNED":
                        self.accept_job(job.get("id"))

    def handle_picking_up(self, active_jobs):
        pickup_tasks = active_jobs.get("pickupTasks", [])
        for task_item in pickup_tasks:
            task = task_item.get("task", {})
            state = task.get("state")
            parcel_ids = [p.get("id") for p in task_item.get("parcels", []) if p.get("id")]
            if state in ["ON_THE_WAY", "ON_POINT"]:
                self.complete_task(task.get("id"), "PICKED", parcel_ids)
            elif state == "COMPLETED":
                dropoff_tasks = active_jobs.get("dropOffTasks", [])
                for dropoff_task in dropoff_tasks:
                    if dropoff_task.get("task", {}).get("state") == "ASSIGNED_TO_JOB":
                        self.start_task(dropoff_task.get("task", {}).get("id"))
                        break

    def handle_delivering(self, active_jobs):
        dropoff_tasks = active_jobs.get("dropOffTasks", [])
        for dropoff_task in dropoff_tasks:
            task = dropoff_task.get("task", {})
            state = task.get("state")
            parcel_ids = [p.get("id") for p in dropoff_task.get("parcels", []) if p.get("id")]
            task_id = task.get("id")
            if state == "ON_POINT":
                self.complete_task(task_id, "DELIVERED", parcel_ids)
            elif state == "ON_THE_WAY":
                self.on_point(task_id)
            elif state == "ASSIGNED_TO_JOB":
                self.start_task(task_id)

    def on_point(self, task_id):
        payload = {"taskId": task_id}
        with self.client.post(URL["TASK_ON_POINT"], json=payload, headers=self.get_headers(), name="on_point", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"On point failed: {resp.text}")

    def start_task(self, task_id):
        payload = {"taskId": task_id}
        with self.client.post(URL["TASK_START"], json=payload, headers=self.get_headers(), name="start_task", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Start task failed: {resp.text}")

    def complete_task(self, task_id, status, parcel_ids):
        parcels = [{"id": pid, "ageConfirmed": True, "status": status} for pid in parcel_ids]
        payload = {"taskId": task_id, "taskState": "COMPLETED", "parcels": parcels, "commentary": ""}
        with self.client.post(URL["TASK_COMPLETE"], json=payload, headers=self.get_headers(), name="complete_task", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Complete task failed: {resp.text}")

    def accept_job(self, job_id):
        payload = {"jobId": job_id}
        with self.client.post(URL["JOB_ACCEPT"], json=payload, headers=self.get_headers(), name="accept_job", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Accept job failed: {resp.text}")

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