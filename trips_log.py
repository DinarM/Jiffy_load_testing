import asyncio
import time
import aiohttp

from utils.endpoints import access_token

async def send_log_request(session, job_id, authorization_token):
    url = 'https://api2-stage.jiffy-team.com/dispatcher/v1/mobile/trips/log'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': authorization_token
    }
    payload = {
        "longitude": "53.12345",
        "latitude": "56.3234545",
        "jobId": job_id
    }
    
    try:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                print(f"Успешно отправлен лог для job_id: {job_id}")
            else:
                print(f"Ошибка при отправке лога для job_id: {job_id}. Статус: {response.status}")
    except Exception as e:
        print(f"Исключение при отправке лога для job_id: {job_id}. Ошибка: {str(e)}")

async def main(token, request_count=100):
    
    start_time = time.perf_counter()
    tasks = []
    
    # Базовый job_id (можно заменить на нужный)
    base_job_id = "d9815cea-015a-4620-a7e0-3e8e8e907126"
    
    async with aiohttp.ClientSession() as session:
        for i in range(request_count):
            token = await access_token(session, '06731579222')
            # Можно модифицировать job_id для каждого запроса если нужно
            tasks.append(send_log_request(session, base_job_id, token))
        await asyncio.gather(*tasks)
    
    end_time = time.perf_counter()
    print(f"Все логи отправлены за {end_time - start_time:.2f} секунд.")

if __name__ == '__main__':
    # Токен из примера (нужно заменить на актуальный)
    
    
    # Указываем количество запросов
    request_count = 100
    asyncio.run(main(request_count))
