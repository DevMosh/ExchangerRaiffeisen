import aiohttp
import asyncio

# служебные импорты
import time
import functools


# декоратор для измерения скорости выполнения функций
def timer_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Function {func.__name__} executed in {end_time - start_time} seconds")
        return result

    return wrapper


@timer_decorator
async def make_request():
    url = 'https://api2.bybit.com/fiat/otc/item/online'

    payload = {"userId": "",
               "tokenId": "USDT",
               "currencyId": "RUB",
               "payment": ["64"],  # 64 райфайзенбанк
               "side": "0",  # покупка 0, продажа 1
               "size": "1",
               "page": "1",
               "amount": "",
               "authMaker": False,
               "canTrade": False}

    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.post(url, json=payload) as response:
            data = await response.json()
            return data

loop = asyncio.get_event_loop()
result = loop.run_until_complete(make_request())
print(result)

