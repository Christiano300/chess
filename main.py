if __name__ != '__main__':
    print("someone got here")
from multiprocessing.connection import Connection
from multiprocessing import Process
from random import randint
from engine import Move, get_engine_process, get_engine_thread, move_to_uci
import pygame as pg
from functools import lru_cache


def load_from_fen(fen: str, pieces_group, board, images):
    fenBoard = fen.split()[0]
    file, rank = 0, 7
    for symbol in fenBoard:
        if symbol == "/":
            file = 0
            rank -= 1
        else:
            if symbol.isdigit():
                file += int(symbol)
            else:
                piece_color = "b" if symbol.islower() else "w"
                piece_type = symbol.lower()
                piece = Piece(piece_color + piece_type, rank, file, images)
                pieces_group.add(piece)
                board[file][rank] = piece
                file += 1


def draw_background(screen, img_settings):
    screen.fill((95, 216, 127))
    for i in range(8):
        for j in range(8):
            if (i + j) % 2 == 0:
                pg.draw.rect(screen,
                             (234, 198, 164),
                             (i * 75 + 50, j * 75 + 50, 75, 75))
            else:
                pg.draw.rect(screen,
                             (168, 94, 62),
                             (i * 75 + 50, j * 75 + 50, 75, 75))
    pg.draw.rect(screen, (0, 0, 0), (45, 45, 610, 610), 5, 4)
    screen.blit(img_settings, (630, 10))


class Piece(pg.sprite.Sprite):
    def __init__(self, piece, rank, file, images):
        pg.sprite.Sprite.__init__(self)
        self.color = piece[0]
        self.type = piece[1]
        self.rank = rank
        self.file = file
        self.image: pg.surface.Surface = images[piece]
        self.rect: pg.rect.Rect = self.image.get_rect()
        self.rect.left = self.file * 75 + 50
        self.rect.top = (-self.rank + 7) * 75 + 50
        if self.type == "e":
            self.rect = pg.Rect(0, 0, 0, 0)
            self.image = pg.Surface((0, 0))

    def move(self, file, rank, board, move_history, ui_conn):
        move_history.append(((self.file, self.rank), (file, rank)))
        board[self.file][self.rank] = None
        self.file = file
        self.rank = rank
        board[self.file][self.rank] = self
        self.rect.left = self.file * 75 + 50
        self.rect.top = (-self.rank + 7) * 75 + 50
        update_move(ui_conn, move_history)


def toggle_screensize(settings_open, screen, groesse, groesse_open):
    if settings_open:
        settings_open = False
        screen = pg.display.set_mode(groesse, pg.RESIZABLE)
    else:
        settings_open = True
        screen = pg.display.set_mode(groesse_open, pg.RESIZABLE)

    return settings_open, screen


def get_engine_updates(ui_conn, moves: list):
    if not ui_conn.poll():
        return
    update = ui_conn.recv()

    print(f"GUI received update: {update}")
    if update[0] == "moves":
        moves.clear()
        for i in update[1]:
            moves.append(i)
        print(len(moves))


def update_move(ui_conn, move_history):
    ui_conn.send("position startpos moves " +
                 " ".join([move_to_uci(i) for i in move_history]))
    ui_conn.send("go perft 1")


def setup(pieces_group, board, move_history, images):
    ui_conn, engine = get_engine_thread()
    setup_game(pieces_group, board, move_history, images, ui_conn)
    return ui_conn, engine


def setup_game(pieces_group, board, move_history, images, ui_conn):
    load_from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                  pieces_group, board, images)
    # load_from_fen("7k/3N2qp/b5r1/2p1Q1N1/Pp4PK/7P/1P3p2/6r1")
    # load_from_fen("pppppppp/pppppppp/pppppppp/pppppppp/pppppppp/pppppppp/pppppppp/pppppppp")
    update_move(ui_conn, move_history)


@lru_cache
def get_move_color(move):
    return randint(0, 0xffffff)


def main():
    pg.init()
    groesse = breite, hoehe = 700, 700
    groesse_open = breite_open, hoehe_open = 1000, 700
    screen = pg.display.set_mode(groesse, pg.RESIZABLE)

    current_player = "w"
    players_turn = True

    engine = None  # type: ignore
    ui_conn: Connection = None  # type: ignore

    pieces_group = pg.sprite.Group()
    clock = pg.time.Clock()

    images = {c + p: pg.image.load(f'files/{p}_{c}.png').convert_alpha()
              for p in "kqbnrp" for c in "wb"}

    img_over_normal = pg.image.load("files/overlay_normal.png").convert_alpha()
    img_over_capture = pg.image.load(
        "files/overlay_capture.png").convert_alpha()
    img_settings = pg.image.load("files/settings.png").convert_alpha()

    settings_rect = pg.Rect(630, 10, 26, 26)
    board_rect = pg.Rect(50, 50, 600, 600)

    select_overlay = pg.Surface((75, 75), pg.SRCALPHA)
    select_overlay.fill("0xffff007f")

    pg.display.set_icon(images["bn"])
    pg.display.set_caption("Chess")

    settings_open = False

    moves: list[Move] = []          # list of moves for current board
    current_moves: list[Move] = []  # list of moves for current piece
    move_history: list[Move] = []

    selected_piece = None

    board: list[list[Piece | None]] = [
        [None for _ in range(8)] for _ in range(8)]

    ui_conn, engine = setup(
        pieces_group, board, move_history, images)  # type: ignore
    engine.start()

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                print(clock.get_fps())
                ui_conn.close()
                return
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if pg.Rect.collidepoint(settings_rect, event.pos):  # type: ignore
                        settings_open, screen = toggle_screensize(
                            settings_open, screen, groesse, groesse_open)

                    elif pg.Rect.collidepoint(board_rect, event.pos) and players_turn:
                        file = (event.pos[0] - 50) // 75
                        rank = -(event.pos[1] - 50) // 75 + 8
                        if not selected_piece:  # no piece selected, try to select piece # type:ignore
                            if board[file][rank] is not None:
                                selected_piece = board[file][rank]
                                current_moves = list(
                                    filter(lambda x: x[0] == (file, rank), moves))
                                print(f"{file=}, {rank=}")

                        else:  # piece selected, try to move piece, if not valid deselect
                            if (file, rank) in (i[1] for i in current_moves):  # type: ignore
                                if board[file][rank] is not None:
                                    board[file][rank].kill()
                                selected_piece.move(
                                    file, rank, board, move_history, ui_conn)
                                selected_piece = None
                                current_moves = []
                            elif board[file][rank] is not None and board[file][rank] != selected_piece:
                                selected_piece = board[file][rank]
                                current_moves = list(
                                    filter(lambda x: x[0] == (file, rank), moves))
                                print(f"{file=}, {rank=}")
                            else:
                                selected_piece = None
                                current_moves = []

        get_engine_updates(ui_conn, moves)

        draw_background(screen, img_settings)
        if selected_piece:  # type: ignore
            screen.blit(select_overlay, selected_piece.rect)


        # Code for displaying overlay
        for move in current_moves:
            dest = move[1]
            if board[dest[0]][dest[1]] is not None:
                screen.blit(img_over_capture,
                            (dest[0] * 75 + 50, (-dest[1] + 7) * 75 + 50))
            else:
                screen.blit(img_over_normal,
                            (dest[0] * 75 + 50, (-dest[1] + 7) * 75 + 50))

        for move in moves:
            pg.draw.line(screen, get_move_color(move),
                         (move[0][0] * 75 + 87,
                          (-move[0][1] + 7) * 75 + 87),
                         (move[1][0] * 75 + 87,
                          (-move[1][1] + 7) * 75 + 87), 5)
        
        pieces_group.draw(screen)
        
        pg.display.update()
        clock.tick(30)


if __name__ == "__main__":
    main()
