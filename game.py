from io import StringIO
from random import choice, randint
import re
from engine import get_engine_thread

running_games = {}

_stockfish_modes = {
    "w": lambda self: self.worstfish(False),
    "W": lambda self: self.worstfish(True),
    "1": lambda self: "movetime 1",
    "e": lambda self: "",
    "d": lambda self: "depth 18",
    "D": lambda self: "depth 25",
    "n": lambda self: "nodes 50000",
    "N": lambda self: "nodes 1000000",
    "t": lambda self: "movetime 100",
    "T": lambda self: "movetime 1500"
}

new_game_regex = re.compile(r"n([sp])([wW1edDnNtT]?)([wbr])((?:pub)|(?:prv))(.*)")


def str_to_pos(string) -> tuple[int, int]:
    return (ord(string[0]) - 97, int(string[1]) - 1)

def pos_to_str(pos):
    return chr(pos[0] + 97) + str(pos[1] + 1)

def public_games():
    return [{"name": game.p1, "id": game.id, "color": game.color} for game in filter(lambda x: x.public, running_games.values())]

def create_game(params):
    # ofs = 0
    # if params[1] == "s":
    #     game.stockfish_mode = params[2]
    #     ofs = 1
    # color = params[2 + ofs]
    # if color == "r":
    #     color = choice("wb")
    # game.players_swapped = color == "b"

    # game.public = params[3 + ofs:6 + ofs] == "pub"
    # game.p1 = params[6 + ofs:]
    # return game
    match = new_game_regex.match(params)
    if match:
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

    else:
        pass # error handling

class Game:
    start_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    def __init__(self, fen=start_fen):
        self.board = []
        self.current_player = "w"
        self.castle = [False, False, False, False]
        self.ep_pos = (-1, -1)
        self.move = 1
        self.plies = 0
        self.engine_conn, self.engine = get_engine_thread()
        self.engine.start()
        self.id = randint(0, 0xffff)
        self.singleplayer = False
        self.p1 = self.p2 = ""
        self.players_swapped = False
        self.color = "w"
        self.public = False
        self.stockfish_mode = ""
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
        self.castle.append("K" in castle)
        self.castle.append("Q" in castle)
        self.castle.append("k" in castle)
        self.castle.append("q" in castle)
        
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