""" Shadofer#6681 """
import asyncio
from json import dumps, loads
from json.decoder import JSONDecodeError
from logging import DEBUG, NOTSET, StreamHandler, getLogger
from os import environ
from socket import gethostbyname, gethostname
from typing import Callable, Dict
from uuid import uuid4

from dotenv import load_dotenv
from websockets import WebSocketClientProtocol
from websockets import serve as ws_serve
from websockets.exceptions import ConnectionClosed

# Used by path_switcher and request_switchers.
current_error: str = None

# Telemetry
total_requests: int = 0

registered_responses: Dict[str, Callable] = {}

load_dotenv()

# Setup logging.
log = getLogger('basicpyapi')

if environ.get('BASICPYAPI_LOGGING') == 'True':
    log.setLevel(DEBUG)
    log.addHandler(StreamHandler())

else:
    log.setLevel(NOTSET)
    
def main():
    # Handles server startup.
    port = environ.get('PORT', 5000)

    start_server = ws_serve(serve, '0.0.0.0', port)

    log.info(f'Server running at: {gethostbyname(gethostname())}:{port}')

    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server)
    
    try:
        loop.run_forever()
        
    except KeyboardInterrupt:
        log.info('Server stopped manually.')
        pass

def format_res(event_name: str, is_no_event_response: bool = False, **kwargs) -> dict:
    """Constructs a basic formatted response with an event and extra arguments.

    Args:
        event_name (str): The name of the called event.

    Returns:
        dict: The formatted response.
    """
    final_dict = {'event': f'{event_name}Reply'}
    
    final_dict['data'] = {**kwargs}
    
    if not is_no_event_response:
        final_dict['originalEvent'] = event_name
    
    return dumps(final_dict)

def format_res_err(event_name: str, error_message: str, is_no_event_response: bool = False) -> dict:
    """Same as format_res but it also takes a custom error message to display.

    Args:
        event_name (str): The name of the called event.
        error_message (str): The error message to display.

    Returns:
        dict: The formatted error response.
    """
    final_dict = {'event': f'{event_name}Error'}
    
    final_dict['data'] = {'message': error_message}
    
    if not is_no_event_response:
        final_dict['originalEvent'] = event_name
    
    return dumps(final_dict)
    
def request_switcher(data: dict) -> dict:
    """Switches response according to the data provided.

    Args:
        data (dict): The data provided by serve.

    Returns:
        dict: The response according to the request. May be None, which means the request is invalid.
    """
    try:
        global current_error
        
        event = data['event']

        # check if the event is a registered response, unpack function's returned dict values
        if event in registered_responses:
            return format_res(event, **registered_responses[event]())

        else:
            current_error = format_res_err('rootEvent', f'The requested event doesn\'t exist: {event}', True)

    except KeyError:
        current_error = format_res_err('root', 'An event argument must be provided.', True)

async def serve(wss: WebSocketClientProtocol, *args, **kwargs) -> None:
        """Called only by websockets.serve.

        Args:
            wss (WebSocketClientProtocol): The websocket client.
        """
        log.info('A client has connected.')
        
        try:
            while True:
                try:
                    global current_error, total_requests
                    
                    data = loads(await wss.recv())

                    result = request_switcher(data)

                    if result and not current_error:
                        await wss.send(result)
                        
                        log.info(f'Reply sent for \'{data["event"]}\'.')
                        
                        total_requests += 1
                        log.info(f'Requests: {total_requests}')
                        
                    else:
                        await wss.send(current_error)

                except JSONDecodeError:
                    if not current_error:
                        await wss.send(format_res_err('global', 'Invalid data format.', True))

                finally:
                    current_error = None
                    
        except ConnectionClosed:
            log.info('A client has disconnected.')

# Decorators
def response(func: Callable = None, name: str = '') -> Callable:
    """Marks a response as callable with an event.

    Args:
        func (Callable, optional): The function to mark. Defaults to None.
        name (str, optional): The required name of the event with which this is called. Defaults to ''.
    """
    def wrapper(func: Callable) -> Callable:
        func_name = func.__name__ if not name else name
    
        if func_name in registered_responses:
            log.info(f'Aborting response addition, duplicate response found: {func_name}')
            return
    
        registered_responses[func_name] = func
    
        log.info(f'Registered response: {func_name}')

        return func
    return wrapper(func) if func else wrapper

# Registered runtime responses
@response(name='authenticate')
def auth():
    return dict(uid=str(uuid4()))

if __name__ == '__main__':
    main()
