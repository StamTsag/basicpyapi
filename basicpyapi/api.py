""" Shadofer#7312 """
import asyncio
from websockets import serve, WebSocketClientProtocol
from os import environ
from uuid import uuid4
from json import dumps, loads
from json.decoder import JSONDecodeError
from socket import gethostname, gethostbyname

PING_INTERVAL = 5
PING_TIMEOUT = 5

SUPPORTED_PATHS = ['/']

# ROOT /
SUPPORTED_REQUESTS_ROOT = ['authenticate']

class Server:
    """ The base Server class. Starts/Closes the server. """

    def __init__(self) -> None:

        # The main asyncio loop, for synchronous events. May use when performance is an issue.
        self.__loop = asyncio.get_event_loop()

        # Used by __path_switcher and __request_switchers.
        self.__current_error: str = None

        # telemetry
        self.__total_requests: int = 0

    def __format_res(self, event_name: str, **kwargs) -> dict:
        return dumps({'event': f'{event_name}_reply', **kwargs})

    def __format_res_err(self, event_name: str, error_message: str) -> dict:
        return dumps({'event': f'{event_name}_error', 'message': error_message})

    def __request_switcher_root(self, data: dict) -> dict:
        """Switches response according to the data provided. Only for '/', root.

        Args:
            data (dict): The data provided by __path_switcher.

        Returns:
            dict: The response according to the request. May be None, which means the request is invalid.
        """
        try:
            event = data['event']

            if event in SUPPORTED_REQUESTS_ROOT:
                if event == 'authenticate':
                    return self.__format_res(event, uid=str(uuid4()))

            else:
                self.__current_error = self.__format_res_err(event, 'This event doesn\'t exist.')
                return None

        except KeyError:
            self.__current_error = self.__format_res_err('root', 'An event argument must be provided.')
            return None

    def __path_switcher(self, path: str, data: dict) -> dict:
        """Loops over the paths and sends data accordingly.

        Args:
            path (str): The path which the client has requested.
            data (dict): The data, which will be used if the path is supported.

        Returns:
            dict: The output result either from this function or from a __request_switcher.
        """
        if path in SUPPORTED_PATHS:
            if path == '/':
                return self.__request_switcher_root(data)
        else:
            self.__current_error = self.__format_res_err('global', f'The path {path} couldn\'t be found.')
            return None

    async def serve(self, wss: WebSocketClientProtocol, path: str) -> None:
        """Called only by websockets.serve, provides start_server with info.

        Args:
            wss (WebSocketClientProtocol): The websocket client.
            path (str): The path which the client wants to access.
        """
        while True:
            try:
                data = loads(await wss.recv())

                result = self.__path_switcher(path, data)

                if result and not self.__current_error:
                    await wss.send(result)
                    print(f'Reply sent for \'{data["event"]}\'.')
                    self.__total_requests += 1
                    print(f'Requests: {self.__total_requests}')
                else:
                    await wss.send(self.__current_error)

            except JSONDecodeError as e:
                if not self.__current_error:
                    await wss.send(self.__format_res_err('global', 'Invalid data format.'))

            finally:
                self.__current_error = None

# for heroku
port = environ.get('PORT', 5000)

# Steps before serving.
server = Server()

start_server = serve(server.serve, '0.0.0.0', port)

print(f'Server running at: {gethostbyname(gethostname())}:{port}')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server)
    loop.run_forever()
