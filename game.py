if __name__ == "__main__":
    import wss

import asyncio
from io import StringIO
import json
from random import choice, randint
import re
from typing import Callable
from engine import Move, get_engine_thread
from websockets.server import WebSocketServerProtocol


_simple_stockfish_modes: dict[str, str] = {
    "1": "movetime 1",
    "d": "depth 18",
    "D": "depth 25",
    "n": "nodes 50000",
    "N": "nodes 1000000",
    "t": "movetime 100",
    "T": "movetime 1500",
}

invert_color_map = {"w": "b", "b": "w", "r": "r"}

new_game_regex = re.compile(
    r"n([sp])([wW1edDnNtT]?)([wbr])((?:pub)|(?:prv))(.*)")

numerals = "0123456789abcdefghijklmnopqrstuvwxyz"


def numberToBase(n, b=len(numerals), pad=4):
    if n == 0:
        return "0"
    digits = []
    while n:
        digits.insert(0, int(n % b))
        n //= b
    return "".join(numerals[i] for i in digits).rjust(4, "0")


def str_to_pos(string) -> tuple[int, int]:
    return (ord(string[0]) - 97, int(string[1]) - 1)


def pos_to_str(pos):
    return chr(pos[0] + 97) + str(pos[1] + 1)


def game_to_json(game_id):
    game = running_games[game_id]
    return {"name": game.p1, "id": numberToBase(game.id), "color": invert_color_map[game.color]}


class Game:
    start_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    def __init__(self, fen=start_fen):
        self.board = []
        self.current_player = "w"
        self.castle = ["K", "Q", "k", "q"]
        self.ep_pos = (-1, -1)
        self.move = 1
        self.plies = 0
        self.valid_moves: list[Move] = []
        self.cache_valid_moves = False
        self.engine_conn, self.engine = get_engine_thread()
        self.engine.start()
        self.id = randint(0, int("zzzz", 36))
        self.singleplayer = False
        self.p1 = self.p2 = ""
        self.players_swapped = False
        self.color = "w"
        self.public = False
        self.stockfish_mode = ""
        self.stockfish_running = False
        self.load_from_fen(fen)
        running_games[self.id] = self

    def load_from_fen(self, fen):
        self.board = [["" for _ in range(8)] for _ in range(8)]
        parts = fen.split()
        fenBoard = parts[0]
        file, rank = 0, 7
        for symbol in fenBoard:
            if symbol == "/":
                file = 0
                rank -= 1
            else:
                if symbol.isdigit():
                    file += int(symbol)
                else:
                    self.board[file][rank] = symbol
                    file += 1

        self.current_player = parts[1]
        castle = parts[2]
        self.castle.clear()
        for i in castle:
            self.castle.append(i)

        if parts[3] != "-":
            self.ep_pos = str_to_pos(parts[3])
        self.plies = int(parts[4])
        self.move = int(parts[5])

    def to_fen(self) -> str:
        fen_io = StringIO()
        empty_count = 0
        for rank in range(7, -1, -1):
            for file in range(8):
                tile = self.board[file][rank]
                if tile == "":
                    empty_count += 1
                else:
                    if empty_count != 0:
                        fen_io.write(str(empty_count))
                        empty_count = 0
                    fen_io.write(tile)

            if empty_count != 0:
                fen_io.write(str(empty_count))
                empty_count = 0
            if rank != 0:
                fen_io.write("/")

        fen_io.write(f" {self.current_player} ")

        if any(self.castle):
            if self.castle[0]:
                fen_io.write("K")
            if self.castle[1]:
                fen_io.write("Q")
            if self.castle[2]:
                fen_io.write("k")
            if self.castle[3]:
                fen_io.write("q")
        else:
            fen_io.write("-")

        fen_io.write(" ")
        if self.ep_pos == (-1, -1):
            fen_io.write("-")
        else:
            fen_io.write(pos_to_str(self.ep_pos))

        fen_io.write(f" {self.plies} {self.move}")

        return fen_io.getvalue()

    def get_valid_moves(self):
        if self.cache_valid_moves:
            return self.valid_moves
        self.engine_conn.send(f"position fen {self.to_fen()}")
        self.engine_conn.send("go perft 1")
        while True:
            data = self.engine_conn.recv()
            if data[0] == "moves":
                self.valid_moves = data[1]
                self.cache_valid_moves = True
                return self.valid_moves
            else:  # TODO: do something else with the data
                pass

    def get_board_at(self, pos):
        return self.board[pos[0]][pos[1]]

    def set_board_at(self, pos, value: str):
        self.board[pos[0]][pos[1]] = value

    def make_castle_move(self, move: Move):
        rookFile = 0 if move.dest[1] == 2 else 7
        self.set_board_at([move.dest[0], 3 if move.dest[1] == 2 else 5],
                          self.get_board_at([move.dest[0], rookFile]))
        self.set_board_at([move.dest[0], rookFile], "")

    def make_move(self, move: Move, websocket: WebSocketServerProtocol):
        valid_moves = self.get_valid_moves()
        if not move in valid_moves:
            print(move)
            print(valid_moves)
            raise ValueError("invalid move")
        self.cache_valid_moves = False
        src = self.get_board_at(move.src)

        if move.dest == self.ep_pos:  # en passant capture
            self.set_board_at(
                (move.dest[0], move.dest[1] + (1 if src == "p" else -1)), "")
            self.ep_pos = (-1, -1)

        # en passant move
        elif src in "Pp" and abs(move.src[1] - move.dest[1]) == 2:
            self.ep_pos = (
                move.src[0], move.src[1] + (1 if src == "P" else -1))

        else:
            self.ep_pos = (-1, -1)

        # castle move
        castleOffset = move.dest[1] - move.src[1]
        if src.lower() == "k" and abs(castleOffset) == 2:
            if castleOffset == 2 and ("K" if self.current_player == "w" else "k") in self.castle:
                self.make_castle_move(move)

            elif castleOffset == -2 and ("Q" if self.current_player == "w" else "q") in self.castle:
                self.make_castle_move(move)
        
        if src.lower() == "k":
            self.castle[0 if self.current_player == "w" else 2] = ""
            self.castle[1 if self.current_player == "w" else 3] = ""

        elif src.lower() == "r":
            if move.src[0] == 0:
                self.castle[1 if self.current_player == "w" else 3] = ""
            elif move.src[0] == 7:
                self.castle[0 if self.current_player == "w" else 2] = ""

        self.set_board_at(move.dest, self.get_board_at(move.src))
        self.set_board_at(move.src, "")

        if move.promote:
            self.set_board_at(move.dest, move.promote.upper()
                              if src.upper() else move.promote.lower())

        self.current_player = "w" if self.current_player == "b" else "b"

        self.get_valid_moves()

    async def make_stockfish_move(self, websocket: WebSocketServerProtocol):
        self.engine_conn.send(_simple_stockfish_modes[self.stockfish_mode])
        while True:
            res = self.engine_conn.recv()
            if res[0] == "bestmove":
                await websocket.send(res[1]["move"])
                break



running_games: dict[int, Game] = {}


def create_game(params) -> Game:  # type: ignore
    match = new_game_regex.match(params)
    if not match:
        raise ValueError()
    game = Game()
    game.singleplayer = match.group(1) == "s"
    game.stockfish_mode = match.group(2)
    game.color = color = match.group(3)
    if color == "r":
        color = choice("wb")
    game.players_swapped = color == "b"
    game.public = match.group(4) == "pub"
    game.p1 = match.group(5)
    return game
