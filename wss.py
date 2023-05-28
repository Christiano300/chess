import asyncio
from time import perf_counter
from websockets.server import serve, WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed

from game import Game, create_game

lock = asyncio.Lock()

num_connections = 0
MAX_CONNECTIONS = 1

games = []

async def echo(websocket: WebSocketServerProtocol):
    print("client connected")
    session_id = hash(perf_counter().as_integer_ratio()) & 0xffffffff
    async with lock:
        global num_connections
        if num_connections >= MAX_CONNECTIONS:
            print("client rejected")
            await websocket.send("c")
            await websocket.close()
            return
        else:
            print("client accepted")
            num_connections += 1
    
    try:
        async for message in websocket:
            if message == "rs":
                await websocket.send("s" + str(session_id))
            
            elif message.startswith("n"): # type: ignore
                new_game = create_game(message)
                
    except ConnectionClosed:
        print("client closed")
        async with lock:
            num_connections -= 1
    
    except Exception:
        print("thread crashed, client closed")
        async with lock:
            num_connections -= 1

async def main():
    async with serve(echo, "localhost", 8080):
        await asyncio.Future()

asyncio.run(main())