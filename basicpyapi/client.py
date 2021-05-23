import asyncio, websockets

async def func():
    async with websockets.connect('ws://localhost:5000/genuid') as ws:
        while True:
            res = await ws.recv()

            print(res)

loop = asyncio.get_event_loop()

loop.run_until_complete(func())
loop.run_forever()