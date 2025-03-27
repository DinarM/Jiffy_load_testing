import asyncio
import time
import aiohttp
from utils.endpoints import assign_orders, finish_order, get_unfinished_orders, pack_order, picking_auth, scan_item, warehouse_auth, get_next_item


async def scan_items(session, token, order_id):
    while True:
        response = await get_next_item(session, authorization_token=token, order_id=order_id)
        
        if response['data']['item'] is None:
            break
        else:
            productBarcodes = response['data']['item']['productBarcodes']
            item_id = response['data']['item']['id']
            await scan_item(session, authorization_token=token, item_id=item_id, barcode=productBarcodes[0])

    await pack_order(session, authorization_token=token, order_id=order_id)
    await finish_order(session, authorization_token=token, order_id=order_id)


async def start_process(session, picker_code):
    token = await picking_auth(session, picker_code)
    if token is None:
        print('Не удалось получить токен, дальнейшие запросы не выполняются.')
        return
    await warehouse_auth(session, authorization_token=token)

    unfinished_orders = await get_unfinished_orders(session, authorization_token=token)
    # print(f'unfinished_orders: {unfinished_orders['data']}')

    if unfinished_orders['data'] is not None:
        await scan_items(session, token=token, order_id=unfinished_orders['data']['id'])
    else:
        response = await assign_orders(session, authorization_token=token)
        # print(f'assign_orders: {response}')
        if response.get('data') is not None:
            await scan_items(session, token=token, order_id=response['data']['id'])
        else:
            print('Заказы отсутствуют')



# async def main():
#     picker_code = 'JIFF6LYSAS'
#     async with aiohttp.ClientSession() as session:
#         await start_process(session, picker_code)

async def main():
    picker_codes = ['JIFFN4GA7G', 'JIFFN4GA85']
    # picker_codes = ['JIFFN4GA7G', 'JIFFN4GA85', 'JIFFN4GA8W', 'JIFFN4GA9K', 'JIFFN4GAAM', 'JIFFN4GAB9', 'JIFFN4GACF']
    # picker_codes = ['JIFFN4GA7G', 'JIFFN4GA85', 'JIFFN4GA8W', 'JIFFN4GA9K', 'JIFFN4GAAM', 'JIFFN4GAB9', 'JIFFN4GACF', 'JIFFN4GADD', 'JIFFN4GAEE', 'JIFFN4GAFV', 'JIFFN4GAGH', 'JIFFN4GAH9', 'JIFFN4GAHT', 'JIFFN4GAIQ', 'JIFFN4GAJD', 'JIFFN4GAZZ', 'JIFFN4GB0P', 'JIFFN4GB1O', 'JIFFN4DR3L', 'JIFFN4DR4W', 'JIFFN4DR5Y', 'JIFFN4DR6W', 'JIFFN4DR7T', 'JIFFN4DR97', 'JIFFN4DRAH', 'JIFFN4DRBN', 'JIFFN4DRCO', 'JIFFN4G9Y1', 'JIFFN4G9ZI', 'JIFFN4GA1R', 'JIFFN4GA2V', 'JIFFN4GA3K', 'JIFFN4GA4M', 'JIFFN4GA5T', 'JIFFN4GAO3', 'JIFFN4GAQJ', 'JIFFN4GARC', 'JIFFN4GAS7', 'JIFFN4GATD', 'JIFFN4GAUI', 'JIFFN4GAVG', 'JIFFN4GAW9', 'JIFFN4GAX4', 'JIFFN4GAYN', 'JIFFN4DR25', 'JIFFN4G9XA', 'JIFFN4GAK0', 'JIFFN4GAKS', 'JIFFN4GALR', 'JIFFN4GAMH', 'JIFFN4GANB', 'JIFFN4GAOP', 'JIFFN4GAPJ']
    duration = 36000
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        while time.time() - start_time < duration:
            tasks = []
            for picker_code in picker_codes:
                tasks.append(start_process(session, picker_code))
            await asyncio.gather(*tasks)
            await asyncio.sleep(2)

if __name__ == '__main__':
    asyncio.run(main())
