import asyncio, websockets
from json import dumps, loads

async def func():
    async with websockets.connect('ws://localhost:5000') as wss:
        await wss.send(dumps({'event': 'authenticate'}))


        while True:
            print(await wss.recv())

loop = asyncio.get_event_loop()

loop.run_until_complete(func())
loop.run_forever()