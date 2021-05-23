""" Shadofer#7312 """
import asyncio
from websockets import serve, WebSocketClientProtocol
from os import environ
from uuid import uuid4
from json import dumps

PING_INTERVAL = 5
PING_TIMEOUT = 5
RECOGNIZED_PATHS = ['/genuid']

class Server:
    """ The base Server class. Starts/Closes the server. """

    def __init__(self) -> None:

        # The main asyncio loop, for synchronous events. May use when performance is an issue.
        self.__loop = asyncio.get_event_loop()

    def __path_switcher(self, path: str) -> dict:
        """Loops over the paths and sends data accordingly.

        Args:
            path (str): The path which the client has requested.
        """
        if path in RECOGNIZED_PATHS:
            if path == '/genuid':
                return {'event': 'get_uid_reply', 'uid': str(uuid4())}
        else:
            return None

    async def serve(self, wss: WebSocketClientProtocol, path: str) -> None:
        """Called only by websockets.serve, provides start_server with info.

        Args:
            wss (WebSocketClientProtocol): The websocket client.
            path (str): The path which the client wants to access.
        """

        print(f'client accessing "{path}"')

        result = self.__path_switcher(path)

        if result:
            await wss.send(dumps(result))
        else:
            await wss.send(dumps({'event': 'error', 'message': 'Path not found.'}))

        wss.ping_interval = PING_INTERVAL
        wss.ping_timeout = PING_TIMEOUT
        await wss.keepalive_ping()

# for heroku
port = environ.get('PORT', 5000)

# Steps before serving.
server = Server()

start_server = serve(server.serve, '0.0.0.0', port)

print(f'Server running at: 0.0.0.0:{port}')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server)
    loop.run_forever()
