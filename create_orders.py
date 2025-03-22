import asyncio
import time

import aiohttp

from utils.endpoints import verify_customer, send_request


async def main(token):
    start_time = time.perf_counter()  # Засекаем время старта
    tasks = []
    async with aiohttp.ClientSession() as session:
        for i in range(1, 2):  # Создаем 25 асинхронных задач
            tasks.append(send_request(session, i, authorization_token=token))
        await asyncio.gather(*tasks)
    end_time = time.perf_counter()  # Засекаем время завершения
    print(f"Все заказы созданы за {end_time - start_time:.2f} секунд.")

if __name__ == '__main__':
    # Сначала синхронно получаем токен через верификацию SMS
    token = verify_customer()
    if token:
        asyncio.run(main(token))
    else:
        print("Не удалось получить токен, заказы не отправляются.")