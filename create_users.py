import requests
import time
import json

def create_users(num_requests):
    # URL и заголовки запроса
    url = "https://api2-stage.jiffy-team.com/auth/v1/users"
    headers = {
        "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI3OTU0NjhmMi05NzViLTRkNGItYjViMy1kYjc3NWExY2I3MzMiLCJjb21wYW55SWQiOiIxZWI1M2ExMy01ZjllLTRkZWItOTJkNy0wOTBhNGI1M2ZkMjEiLCJyb2xlcyI6WyJhZG1pbiJdLCJpYXQiOjE3NDI4MjM2NDQsImV4cCI6MTc0MjgyNDU0NH0.tuJWEkybY06SZ1xBo-GDI6Y0ti0DHcDl5u49R_PVyhw",
        "Content-Type": "application/json"
    }

    for i in range(num_requests):
        # Формируем уникальные данные для каждого запроса
        payload = {
            "email": f"AQA_courier_{i}@mailto.plus",
            "password": "q1w2e3r4T%",
            "phone": f"0249427{str(i).zfill(4)}", # Добавляем номер итерации в телефон
            "firstName": f"AQA_COURIER_LOAD_TESTING_{i}",
            "lastName": "DINAR",
            "roles": {"ids": [10]},
            "permissions": {"ids": []}
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            print(f"Запрос {i+1}: Статус {response.status_code}")
            print(f"Ответ: {response.text}")
            
            # Добавляем небольшую задержку между запросами
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Ошибка при выполнении запроса {i+1}: {str(e)}")

if __name__ == "__main__":
    # Запрашиваем количество запросов у пользователя
    try:
        num_requests = int(input("Введите количество запросов для выполнения: "))
        create_users(num_requests)
    except ValueError:
        print("Пожалуйста, введите корректное число.")
