""" Shadofer#6681 """
import asyncio
from json import dumps, loads
from os import environ

import websockets
from dotenv import load_dotenv

server_port = None

def main():
    # Handles client startup.
    load_dotenv()
    
    global server_port
    server_port = environ.get('PORT', 5000)
    
    print(f'Establishing connection to localhost server at port {server_port}...')
    
    loop = asyncio.get_event_loop()
    
    try:
        loop.run_until_complete(connection_stream())
        loop.run_forever()
        
    except KeyboardInterrupt:
        pass
    
    except ConnectionRefusedError:
        print('Failed to connect to server, did you start it first?')

async def connection_stream():
    global server_port
    
    async with websockets.connect(f'ws://localhost:{server_port}') as wss:
        print('Connection to server established, sending auth request...')
        
        await wss.send(dumps({'event': 'authenticate'}))

        while True:
            auth_reply = loads(await wss.recv())
            
            print(f'Authentication UID: {auth_reply["data"]["uid"]}')

if __name__ == '__main__':
    main()
