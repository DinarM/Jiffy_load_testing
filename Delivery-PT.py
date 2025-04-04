import uuid
from locust import HttpUser, constant, task, between, events
from locust.clients import HttpSession

# Список курьеров можно ебануть больше
# phone_numbers = [
#     '02494270000', '02494270001', '02494270002', '02494270003', '02494270004',
#     '02494270005', '02494270006', '02494270008', '02494270009', '02494270010',
#     '02494270011', '02494270012', '02494270013', '02494270014', '02494270015',
#     '02494270016', '02494270017', '02494270018', '02494270019', '02494270020',
#     '02494270021', '02494270022', '02494270023', '02494270024', '02494270025',
#     '02494270026', '02494270027', '02494270028', '02494270029', '02494270030',
#     '02494270031', '02494270032', '02494270033', '02494270034', '02494270035',
#     '02494270036', '02494270037', '02494270038', '02494270039', '02494270040',
#     '02494270041', '02494270042', '02494270043', '02494270044', '02494270045',
#     '02494270046', '02494270047', '02494270048', '02494270049', '0591707617',
# ]
phone_numbers = [
    '02494270000', '02494270001', '02494270002', '02494270003', '02494270004', 
    '02494270005', '02494270006', '02494270008', '02494270009', '02494270010',

    '02494270011', '02494270012', '02494270013', '02494270014', '02494270015', 
    '02494270016', '02494270017', '02494270018', '02494270019', '02494270020',

    '02494270021', '02494270022', '02494270023', '02494270024', '02494270025', 
    '02494270026', '02494270027', '02494270028', '02494270030', '02494270031',

    '02494270032', '02494270033', '02494270034', '02494270037', '02494270038', 
    '02494270040', '02494270029', '02494270035', '02494270036', '02494270039',

    '02494270041', '02494270042', '02494270043', '02494270044', '02494270045', 
    '02494270046', '02494270047', '02494270048', '02494270049', '02494270007',

    '02494270050', '02494270051', '02494270052', '02494270053', '02494270054', 
    '02494270055', '02494270056', '02494270057', '02494270058', '02494270059',

    '02494270060', '02494270061', '02494270062', '02494270063', '02494270064', 
    '02494270065', '02494270066', '02494270067', '02494270068', '02494270077',

    '02494270078', '02494270079', '02494270080', '02494270069', '02494270070', 
    '02494270071', '02494270072', '02494270073', '02494270074', '02494270075',

    '02494270076', '02494270081', '02494270082', '02494270083', '02494270084', 
    '02494270085', '02494270086', '02494270087', '02494270088', '02494270089',

    '02494270090', '02494270091', '02494270093', '02494270094', '02494270095', 
    '02494270096', '02494270097', '02494270098', '02494270099', '02494270092',
]

COURIERS = [{"phone": phone} for phone in phone_numbers]
GLOBAL_TOKEN = None
DISPATCHER_PHONE = '09991579247'
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
    "GET_LIST": f"https://api2-{STAGE}.jiffy-team.com/dispatcher/v1/admin/jobs/get-list",
    "ASSIGN_COURIER": f"https://api2-{STAGE}.jiffy-team.com/dispatcher/v1/admin/jobs/assign-courier",
    "GET_INFO": f"https://api2-{STAGE}.jiffy-team.com/dispatcher/v1/admin/dashboard/get-info",
    "FORCE_OFFLINE": f"https://api2-{STAGE}.jiffy-team.com/dispatcher/v1/admin/couriers/force-offline",
}


class DeliveryUser(HttpUser):
    wait_time = constant(3)  # Интервал между задачами - то есть 1 секунда между запросом для каждого пользователя нагрузочного теста - НЕ курьеры
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
            
        global GLOBAL_TOKEN
        if GLOBAL_TOKEN is None:
            headers = {"accept": "application/json, text/plain, */*"}
            payload = {"phone": DISPATCHER_PHONE, "code": "0000"}
            with self.client.post(URL["USER_AUTH"], json=payload, headers=headers, name="DISP_AUTH", catch_response=True) as resp:
                if resp.status_code == 200:
                    GLOBAL_TOKEN = f"Bearer {resp.json()['data']['access_token']}"
                else:
                    resp.failure(f"Auth failed for dispatcher {DISPATCHER_PHONE}: {resp.text}")
                    raise Exception("Не удалось авторизоваться диспетчеру")

    def get_headers(self):
        # Апдейт заголовков
        return {
            "accept": "application/json, text/plain, */*",
            "authorization": self.token,
            "content-type": "application/json"
        }

    def get_dispatcher_headers(self):
        # Апдейт заголовков
        return {
            "accept": "application/json, text/plain, */*",
            "authorization": GLOBAL_TOKEN,
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

    # @task(2)
    def manual_assign(self):
        job_ids = []
        courier_ids = []

        self.get_info()
        self.get_list()

        jobs = self.list_response.json().get("data")
        teams = self.info_response.json().get("data").get("teams")

        for job in jobs:
            job_state = job["job"]["state"]
            if job_state == "UNASSIGNED":
                job_ids.append(job["job"]["id"])
        
        for team in teams:
            if team["team"]["externalId"] == "van1":
                for courier in team["couriers"]:
                    if courier["courier"]["status"] == "IDLE":
                        courier_ids.append(courier["courier"]["id"])

        for i in range(min(len(job_ids), len(courier_ids))):
            self.assign_couirier(jobId=job_ids[i], courierId=courier_ids[i])

    # @task(10) 
    def courier_offline(self):
        courier_ids = []

        self.get_info()

        teams = self.info_response.json().get("data").get("teams")

        for team in teams:
            if team["team"]["externalId"] == "van1":
                for courier in team["couriers"]:
                    if courier["courier"]["status"] in ["IDLE", "HEADING_TO_BASE", "ASSIGNED_TO_JOB",]:
                        courier_ids.append(courier["courier"]["id"])

        for courier_id in courier_ids:
            self.force_offline(courier_id=courier_id)


    def force_offline(self, courier_id):
        payload = {"id":courier_id}
        with self.client.post(URL["FORCE_OFFLINE"], json=payload, headers=self.get_dispatcher_headers(), name="FORCE_OFFLINE", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"FORCE_OFFLINE info failed: {resp.text}")

    def assign_couirier(self, jobId, courierId):
        payload = {"jobId":jobId,"courierId":courierId}
        with self.client.post(URL["ASSIGN_COURIER"], json=payload, headers=self.get_dispatcher_headers(), name="ASSIGN_COURIER", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"ASSIGN_COURIER info failed: {resp.text}")
    @task(2)
    def get_info(self):
        with self.client.get(URL["GET_INFO"], headers=self.get_dispatcher_headers(), name="GET_INFO", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"GET_INFO info failed: {resp.text}")
        self.info_response = resp  # Сохраняем результат

    @task(2)
    def get_list(self):
        payload = {"allowedStates":["UNASSIGNED","ASSIGNED","IN_PROGRESS"],"page":{"size":10000,"current":1},"warehouses":["VAN1"]}
        with self.client.post(URL["GET_LIST"], json=payload, headers=self.get_dispatcher_headers(), name="GET_LIST", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"GET_LIST info failed: {resp.status_code} {resp.text}")
        self.list_response = resp


    def mark_online(self):
        with self.client.post(URL["MARK_ONLINE"], headers=self.get_headers(), name="mark_online", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Mark online failed:{resp.status_code} {resp.text}")


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
                resp.failure(f"Start task failed: status code: {resp.status_code} body: {resp.text}")

    def complete_task(self, task_id, status, parcel_ids):
        parcels = [{"id": pid, "ageConfirmed": True, "status": status} for pid in parcel_ids]
        payload = {"taskId": task_id, "taskState": "COMPLETED", "parcels": parcels, "commentary": ""}
        with self.client.post(URL["TASK_COMPLETE"], json=payload, headers=self.get_headers(), name="complete_task", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Complete task failed: status code: {resp.status_code} body: {resp.text}")

    def accept_job(self, job_id):
        payload = {"jobId": job_id}
        with self.client.post(URL["JOB_ACCEPT"], json=payload, headers=self.get_headers(), name="accept_job", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Accept job failed: status code: {resp.status_code} body: {resp.text}")

# Здесь пуллинг для отчета
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    if exception:
        print(f"Запрос {name} завершился с ошибкой: {exception}")
    else:
        print(f"Запрос {name} выполнен за {response_time} мс")

if __name__ == "__main__":
    import os
    os.system(f"locust -f {__file__} --users 50 --spawn-rate 20")