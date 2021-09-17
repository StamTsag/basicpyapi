import asyncio

import websockets

from json import dumps, loads

def main():
    loop = asyncio.get_event_loop()
    
    try:
        loop.run_until_complete(connection_stream())
        loop.run_forever()
        
    except KeyboardInterrupt:
        pass

async def connection_stream():
    async with websockets.connect('ws://localhost:5000') as wss:
        await wss.send(dumps({'event': 'authenticate'}))

        while True:
            auth_reply = loads(await wss.recv())
            
            print(f'Authentication UID: {auth_reply["uid"]}')

if __name__ == '__main__':
    main()
