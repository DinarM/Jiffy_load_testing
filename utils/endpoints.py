import uuid
import requests
from utils.urls import URL
from utils.data import DATA

import aiohttp
import os


def verify_customer(phone_number='09991579247', company_id='1eb53a13-5f9e-4deb-92d7-090a4b53fd21'):
    '''
    Синхронно отправляет запрос на верификацию SMS и извлекает access_token из ответа.
    '''
    url = f'{URL.CUSTOMER_AUTH}?phone_number={phone_number}&otp=0000&device_id=00000000-0000-0000-0000-000000000000'

    headers = {
        'accept': 'application/json, text/plain, */*',
        'x-company-id': company_id
    }

    response = requests.post(url, headers=headers, data='')

    if response.status_code == 200:
        data = response.json()
        token = f"Bearer {data.get('access_token')}"
        print('SMS verification succeeded, access_token получен.')
        return token
    else:
        print('SMS verification failed with status:', response.status_code)
        return None


async def access_token(session, phone_number):
    '''
    Асинхронно отправляет запрос на получение токена (аналог fetchAccessToken в JS)
    и извлекает access_token из ответа, оформлено аналогично verify_customer.
    '''
    url = URL.USER_AUTH
    headers = {
        'accept': 'application/json, text/plain, */*',
    }

    body_data = {
        'phone': phone_number,
        'code': '0000',
    }

    async with session.post(url, headers=headers, json=body_data) as response:
        if response.status == 200:
            data = await response.json()
            token = f'Bearer {data.get("data", {}).get("access_token")}'
            print('Access Token получен')
            return token
        else:
            print(f'Ошибка получения токена. HTTP статус: {response.status} {response.text}')
            return None


async def send_request(session, task_id, authorization_token):
    headers = {
    'accept': 'application/json, text/plain, */*',
    'authorization': authorization_token, 
    'idempotency-key': str(uuid.uuid4()),
}
    
    url = URL.CREATE_ORDER

    async with session.post(url, headers=headers, json=DATA.CREATE_ORDER_DATA) as response:
        text = await response.json()
        print(f'Task {task_id}: Status {response.status}, Response: {text}')


async def couriers_info(session, authorization_token):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'authorization': authorization_token,
    }

    url = URL.COURIERS_INFO

    async with session.get(url, headers=headers) as response:
        return await response.json()


async def mark_online(session, authorization_token):
    '''
    Асинхронно отправляет POST-запрос на endpoint для отметки курьера как онлайн.
    '''
    headers = {
        'accept': 'application/json, text/plain, */*',
        'authorization': authorization_token,
    }
    url = URL.MARK_ONLINE 
    
    async with session.post(url, headers=headers) as response:
        return await response.json()


async def mark_arrival(session, authorization_token, warehouse_id = 'ad253466-cfce-4036-8a0c-9fc98018e132'):
    '''
    Асинхронно отправляет POST-запрос на endpoint для отметки прибытия курьера.
    '''
    headers = {
        'accept': 'application/json, text/plain, */*',
        'authorization': authorization_token,
        'content-type': 'application/json'
    }
    url = URL.MARK_ARRIVAL  

    json_data = {'warehouseId': warehouse_id}
    
    async with session.post(url, headers=headers, json=json_data) as response:
        return await response.json()


async def get_assigned_jobs(session, authorization_token):
    '''
    Асинхронно отправляет GET-запрос на endpoint для получения назначенных заданий.
    '''
    headers = {
        'accept': 'application/json, text/plain, */*',
        'authorization': authorization_token,
    }
    url = URL.JOBS_GET_ASSIGNED

    async with session.get(url, headers=headers) as response:
        return await response.json()

async def on_point(session, authorization_token, task_id):
    '''
    Асинхронно отправляет POST-запрос на endpoint для отметки задачи как 'on point'.
    '''
    headers = {
        'accept': 'application/json, text/plain, */*',
        'authorization': authorization_token,
        'content-type': 'application/json'
    }
    url = URL.TASK_ON_POINT 

    json_data = {'taskId': task_id}
    
    async with session.post(url, headers=headers, json=json_data) as response:
        return await response.json()


async def start_task(session, authorization_token, task_id):
    '''
    Асинхронно отправляет POST-запрос на endpoint для старта задачи.
    '''
    headers = {
        'accept': 'application/json, text/plain, */*',
        'authorization': authorization_token,
        'content-type': 'application/json'
    }
    url = URL.TASK_START  
    json_data = {'taskId': task_id}
    
    async with session.post(url, headers=headers, json=json_data) as response:
        return await response.json()


async def complete_task(session, authorization_token, task_id, status, parcel_ids):
    '''
    Асинхронно отправляет POST-запрос на endpoint для завершения задачи.
    Ожидается, что URL для TASK_COMPLETE определён в utils/urls.py как URL.TASK_COMPLETE.
    '''
    headers = {
        'accept': 'application/json, text/plain, */*',
        'authorization': authorization_token,
        'content-type': 'application/json'
    }
    url = URL.TASK_COMPLETE 

    parcels_list = []
    for parcel_id in parcel_ids:
        parcels_list.append({
            'id': parcel_id,
            'ageConfirmed': True,
            'status': status
        })

    json_data = {
        'taskId': task_id,
        'taskState': 'COMPLETED',
        'parcels': parcels_list,
        'commentary': ''
    }
    
    async with session.post(url, headers=headers, json=json_data) as response:
        return await response.json()


async def upload_photo(session, authorization_token, photo_path, task_id):
    '''
    Асинхронно отправляет POST-запрос на endpoint для загрузки фотографии.
    Отправляет multipart/form-data с полем 'photo' (файл) и 'meta' (JSON-строка с taskId).
    '''
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'App-Version': '1.5.3',
        'Authorization': authorization_token,
    }
    url = URL.UPLOAD_PHOTO

    with open(photo_path, 'rb') as f:
        photo_data = f.read()

    form = aiohttp.FormData()
    form.add_field('photo',
                   photo_data,
                   filename=os.path.basename(photo_path),
                   content_type='image/jpeg')
    form.add_field('meta', '{"taskId":"' + task_id + '"}')

    async with session.post(url, headers=headers, data=form) as response:
        return await response.json()
    
async def accept_job(session, authorization_token, job_id):
    '''
    Асинхронно отправляет POST-запрос на endpoint для принятия задания.
    '''
    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'authorization': authorization_token,
    }
    url = URL.JOB_ACCEPT 
    json_data = {'jobId': job_id}
    
    async with session.post(url, headers=headers, json=json_data) as response:
        return await response.json()


async def mark_returning(session, authorization_token, warehouse_id='ad253466-cfce-4036-8a0c-9fc98018e132'):
    '''
    Асинхронно отправляет POST-запрос на endpoint для отметки курьера как возвращающегося.
    '''
    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'authorization': authorization_token,
    }
    url = URL.COURIER_MARK_RETURNING
    json_data = {'warehouseId': warehouse_id}
    
    async with session.post(url, headers=headers, json=json_data) as response:
        return await response.json()