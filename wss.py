import asyncio
import json
from time import perf_counter
import time
from websockets.server import serve, WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed
from engine import Move

from game import create_game, game_to_json, numberToBase, running_games

lock = asyncio.Lock()

num_connections = 0
MAX_CONNECTIONS = 5

# sessionID: (gameID, websocket, is_p1)
player_games: dict[int, tuple[int, WebSocketServerProtocol, bool]] = {}

game_opponents: dict[int, int] = {}  # sessionID: sessionID
open_games: dict[int, int] = {}  # gameID: sessionID


async def server(websocket: WebSocketServerProtocol):
    print("client connected")
    session_id = hash(perf_counter().as_integer_ratio()) % int("1_000_000", 36)
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
        print(num_connections)

    try:
        async for message in websocket:
            if isinstance(message, bytes):
                await websocket.send("EF")
                continue
            if message == "rs":
                await websocket.send("s" + numberToBase(session_id, 36, pad=6))
            
            elif message == "s":
                session_id = int(message[1:], 36)

            elif message == "rg":
                async with lock:
                    await websocket.send("o" + json.dumps([game_to_json(game_id) for game_id in open_games]))
            
            elif message == "rb":
                async with lock:
                    if not session_id in player_games:
                        await websocket.send("Ee")
                        continue
                    game_id = player_games[session_id]
                    game = running_games[game_id[0]]
                    await websocket.send(f"b{'w' if game.players_swapped ^ game_id[2] else 'b'}{game.to_fen()}")
            
            elif message == "rm":
                async with lock:
                    if not session_id in player_games:
                        await websocket.send("Ee")
                        continue
                    game = running_games[player_games[session_id][0]]
                    await websocket.send(f"M{''.join(str(move) for move in game.get_valid_moves())}")

            elif message.startswith("n"):
                async with lock:
                    try:
                        new_game = create_game(message)
                    except ValueError:
                        await websocket.send("Ei")
                        continue
                    player_games[session_id] = (new_game.id, websocket, True)
                await websocket.send("i" + numberToBase(new_game.id))

                if new_game.singleplayer:
                    await websocket.send(f"b{'b' if new_game.players_swapped else 'w'}{new_game.to_fen()}")
                else:
                    async with lock:
                        open_games[new_game.id] = session_id

            elif message.startswith("j"):
                print("recieved join command")
                game_id = int(message[1:5], 36)
                async with lock:
                    game_full = game_id not in open_games
                    if not game_full:
                        starter_id = open_games[game_id]
                        open_games.pop(game_id)

                if game_full:
                    await websocket.send("Ee")
                    continue
                else:
                    async with lock:
                        player_games[session_id] = (game_id, websocket, False)
                        game = running_games[game_id]
                        starter_socket = player_games[starter_id][1] # type: ignore
                        game_opponents[session_id] = starter_id # type: ignore
                        game_opponents[starter_id] = session_id # type: ignore
                    game.p2 = message[5:]
                    await starter_socket.send(f"b{'b' if game.players_swapped else 'w'}{game.to_fen()}")
                    await starter_socket.send(f"O{game.p2}")
                    
                    await websocket.send(f"b{'w' if game.players_swapped else 'b'}{game.to_fen()}")
                    await websocket.send(f"O{game.p1}")
                    
                    if game.players_swapped:
                        await websocket.send(f"M{''.join(str(move) for move in game.get_valid_moves())}")
                    else:
                        await starter_socket.send(f"M{''.join(str(move) for move in game.get_valid_moves())}")
                    
                    print("sent board")
                    
            elif message.startswith("m"):
                print(f"recieved move: {message[1:]}")
                # make the move in the current game, and send the move to the other player
                async with lock:
                    if not session_id in player_games:
                        await websocket.send("Ee")
                        continue
                    game_id = player_games[session_id][0]
                    game = running_games[game_id]
                
                try:
                    game.make_move(Move.from_str(message[1:]), websocket)
                except ValueError:
                    await websocket.send("Ei")
                    print("apparently invalid move")
                    continue
                    
                if game.singleplayer:
                    # make stockfish take a move on the board
                    asyncio.run(game.make_stockfish_move(websocket)) # makes a stockfish move, sends it and sends the next available moves to the websocket
                else:
                    other_socket = player_games[game_opponents[session_id]][1]
                    await other_socket.send(message) # send move to other player
                    print("answer sent")
                    # send the next available moves to other player
                    await other_socket.send(f"M{''.join(str(move) for move in game.get_valid_moves())}")
                
            else:
                print(f"recieved unknown message: {message}")

    except ConnectionClosed:
        print("client closed")
        async with lock:
            num_connections -= 1
            print(num_connections)

    except Exception as e:
        print("thread crashed, client closed")
        async with lock:
            num_connections -= 1
            print(num_connections)
        raise e


async def main():
    async with serve(server, "localhost", 8080):
        await asyncio.Future()

asyncio.run(main())
