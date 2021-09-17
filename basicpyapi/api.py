""" Shadofer#6681 """
import asyncio

from websockets import serve as ws_serve, WebSocketClientProtocol
from websockets.exceptions import ConnectionClosed

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

# Used by path_switcher and request_switchers.
current_error: str = None

# Telemetry
total_requests: int = 0

def main():
    # Starts the infinite asyncio loop and handles keyboard exits.
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server)
    
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

def format_res(event_name: str, **kwargs) -> dict:
    """Constructs a basic formatted response with an event and extra arguments.

    Args:
        event_name (str): The name of the called event.

    Returns:
        dict: The formatted response.
    """
    return dumps({'event': f'{event_name}Reply', **kwargs})

def format_res_err(event_name: str, error_message: str) -> dict:
    """Same as format_res but it also takes a custom error message to display.

    Args:
        event_name (str): The name of the called event.
        error_message (str): The error message to display.

    Returns:
        dict: The formatted error response.
    """
    return dumps({'event': f'{event_name}Error', 'message': error_message})

def request_switcher_root(data: dict) -> dict:
    """Switches response according to the data provided. Only for '/', root.

    Args:
        data (dict): The data provided by __path_switcher.

    Returns:
        dict: The response according to the request. May be None, which means the request is invalid.
    """
    try:
        global current_error
        
        event = data['event']

        if event in SUPPORTED_REQUESTS_ROOT:
            if event == 'authenticate':
                return format_res(event, uid=str(uuid4()))

        else:
            current_error = format_res_err('invalidRootEvent', 'The requested event doesn\'t exist.')

    except KeyError:
        current_error = format_res_err('root', 'An event argument must be provided.')

def path_switcher(path: str, data: dict) -> dict:
    """Loops over the paths and sends data accordingly.

    Args:
        path (str): The path which the client has requested.
        data (dict): The data, which will be used if the path is supported.

    Returns:
        dict: The output result either from this function or from a __request_switcher.
    """
    if path in SUPPORTED_PATHS:
        if path == '/':
            return request_switcher_root(data)
    else:
        global current_error
        current_error = format_res_err('global', f'The path {path} couldn\'t be found.')

async def serve(wss: WebSocketClientProtocol, path: str) -> None:
        """Called only by websockets.serve.

        Args:
            wss (WebSocketClientProtocol): The websocket client.
            path (str): The path which the client wants to access.
        """
        print('A client has connected.')
        
        try:
            while True:
                try:
                    global current_error, total_requests
                    
                    data = loads(await wss.recv())

                    result = path_switcher(path, data)

                    if result and not current_error:
                        await wss.send(result)
                        
                        print(f'Reply sent for \'{data["event"]}\'.')
                        
                        total_requests += 1
                        print(f'Requests: {total_requests}')
                        
                    else:
                        await wss.send(current_error)

                except JSONDecodeError:
                    if not current_error:
                        await wss.send(format_res_err('global', 'Invalid data format.'))

                finally:
                    current_error = None
                    
        except ConnectionClosed:
            print('A client has disconnected.')

# for heroku
port = environ.get('PORT', 5000)

start_server = ws_serve(serve, '0.0.0.0', port)

print(f'Server running at: {gethostbyname(gethostname())}:{port}')

if __name__ == '__main__':
    main()
