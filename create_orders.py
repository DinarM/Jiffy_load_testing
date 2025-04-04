import asyncio
import time

import aiohttp

from utils.endpoints import verify_customer, send_request

# async def main(token):
#     start_time = time.perf_counter()  # Засекаем время старта
#     tasks = []
#     async with aiohttp.ClientSession() as session:
#         for i in range(1, 2):  # Создаем 25 асинхронных задач
#             tasks.append(send_request(session, i, authorization_token=token))
#         await asyncio.gather(*tasks)
#         await asyncio.sleep(5)
#     end_time = time.perf_counter()  # Засекаем время завершения
#     print(f"Все заказы созданы за {end_time - start_time:.2f} секунд.")


async def main(token, n):
    start_time = time.perf_counter()  # Засекаем время старта
    order_count = 0
    async with aiohttp.ClientSession() as session:
        while order_count < n:
            tasks = []
            for i in range(1, 6):  # Создаем 25 асинхронных задач
                tasks.append(send_request(session, i, authorization_token=token))
            await asyncio.gather(*tasks)
            order_count += len(tasks)
            print(f"Создано {order_count} заказов")
            await asyncio.sleep(3)
        end_time = time.perf_counter()  # Засекаем время завершения
    print(f"Все заказы {order_count} созданы за {end_time - start_time:.2f} секунд.")

if __name__ == '__main__':
    # Сначала синхронно получаем токен через верификацию SMS
    token = verify_customer()
    if token:
        asyncio.run(main(token, 150))  # Замените 100 на нужное количество заказов
    else:
        print("Не удалось получить токен, заказы не отправляются.")