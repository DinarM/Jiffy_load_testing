import asyncio
import time
import aiohttp
from utils.endpoints import accept_job, access_token, complete_task, couriers_info, mark_online, mark_arrival, get_assigned_jobs, on_point, start_task


async def start_process(session, phone_number):
    token = await access_token(session, phone_number)
    if token is None:
        print('Не удалось получить токен, дальнейшие запросы не выполняются.')
        return
    response = await couriers_info(session, authorization_token=token)

    couriers_status = response.get('data', {}).get('courier', {}).get('courier', {}).get('status')
    activeJobs = response.get('data', {}).get('activeJob', {})
    # print(f'Active jobs: {activeJobs}')
    print(f'Courier status: {couriers_status}')

    if couriers_status == 'OFFLINE':
        print('Курьер оффлайн, переводим его в онлайн.')
        await mark_online(session, token)
    elif couriers_status == 'HEADING_TO_BASE':
        print('Курьер в пути к базе, ждем его прибытия.')
        await mark_arrival(session, token)
    elif couriers_status == 'ASSIGNED_TO_JOB' or couriers_status == 'ACCEPTED_JOB':
        print('Курьер назначен на работу, ждем выполнения задачи.')
        if activeJobs:
            print('activeJobs is not None')
            job_state = activeJobs.get('job', {}).get('state')
            if job_state == 'IN_PROGRESS':
                pickup_tasks = response.get('data', {}).get('activeJob', {}).get('pickupTasks', [])
                # print(f'Pickup tasks: {pickup_tasks}')
                for task_item in pickup_tasks:
                    task = task_item.get('task', {})
                    state = task.get('state')
                    if state == 'ASSIGNED_TO_JOB':
                        print('Вызываем метод on_point для выполнения задачи.')
                        await on_point(session, token, task.get('id'))
                    elif state == 'ON_POINT':
                        print('Вызываем метод start_task для начала выполнения задачи.')
                        await start_task(session, token, task.get('id'))
            
        else:
            print('Вызываем метод get_assigned_jobs для получения активной задачи.')
            response = await get_assigned_jobs(session, token)
            job = response.get('data', {}).get('activeJob', {}).get('job')
            job_status = job.get('state')
            job_id = job.get('id')
            print(f'Job status  {job_status}')
            if job_status == 'ASSIGNED':
                print('Курьер назначен на работу, берем инфу с джобы')
                await accept_job(session, token, job_id)
    elif couriers_status == 'PICKING_UP':
        print('Курьер забирает заказ, ждем завершения задачи.')
        pickup_tasks = response.get('data', {}).get('activeJob', {}).get('pickupTasks', [])
        # print(f'Pickup tasks: {pickup_tasks}')
        for task_item in pickup_tasks:
            pickup_state = task_item.get('task', {}).get('state')
            print(f'Pickup state: {pickup_state}')
            parcels = task_item.get('parcels', [])
            parcel_ids = [parcel.get('id') for parcel in parcels if parcel.get('id')]
            if pickup_state == 'ON_THE_WAY' or pickup_state == 'ON_POINT':
                print('Вызываем метод complete_task для выполнения задачи.')
                await complete_task(session, token, task_item.get('task', {}).get('id'), 'PICKED', parcel_ids)
            elif pickup_state == 'COMPLETED':
                print('Переходим к дропофф таске')
                dropoff_tasks = response.get('data', {}).get('activeJob', {}).get('dropOffTasks', [])
                # print(f'Dropoff tasks: {dropoff_tasks}')
                for dropoff_task in dropoff_tasks:
                    dropoff_state = dropoff_task.get('task', {}).get('state')
                    print(f'Dropoff state: {dropoff_state}')
                    dropoff_task_id = dropoff_task.get('task', {}).get('id')
                    print(f'Dropoff task ID: {dropoff_task_id}')
                    if dropoff_state == 'ASSIGNED_TO_JOB':
                        print('Вызываем метод start_task для выполнения задачи.')
                        await start_task(session, token, dropoff_task_id)
                        break
    elif couriers_status == 'DELIVERING':
        print('Статус курьера DELIVERING')
        dropoff_tasks = response.get('data', {}).get('activeJob', {}).get('dropOffTasks', [])
        # print(f'Dropoff tasks: {dropoff_tasks}')
        for dropoff_task in dropoff_tasks:
            dropoff_state = dropoff_task.get('task', {}).get('state')
            print(f'Dropoff state: {dropoff_state}')
            parcels = dropoff_task.get('parcels', [])
            parcel_ids = [parcel.get('id') for parcel in parcels if parcel.get('id')]
            dropoff_task_id = dropoff_task.get('task', {}).get('id')
            print(f'Dropoff task ID: {dropoff_task_id}')
            if dropoff_state == 'ON_POINT':
                print('Вызываем метод complete_task для выполнения задачи.')
                await complete_task(session, token, dropoff_task.get('task', {}).get('id'), 'DELIVERED', parcel_ids)
                break
            elif dropoff_state == 'ON_THE_WAY':
                print('Вызываем метод on_point для выполнения задачи.')
                await on_point(session, token, dropoff_task_id)
                break
            elif dropoff_state == 'ASSIGNED_TO_JOB':
                print('Вызываем метод start_task для выполнения задачи.')
                await start_task(session, token, dropoff_task_id)
                break
    
    else:
        print('продолжаем выполнение скрипта.')



async def main():
    phone_numbers = ['0591707617', '06731579222', '07112233122', '07112233124', '07112233123', '07112233121', '09233333333']
    duration = 360 
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        while time.time() - start_time < duration:
            tasks = []
            for phone in phone_numbers:
                tasks.append(start_process(session, phone))
            await asyncio.gather(*tasks)
            # await asyncio.sleep(1)

# для дебага
# async def main():
#     phone_number = '0591707617'
#     async with aiohttp.ClientSession() as session:
#         await start_process(session, phone_number)

if __name__ == '__main__':
    asyncio.run(main())
