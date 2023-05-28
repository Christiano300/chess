import pygame as pg
from subprocess import Popen, PIPE
stockfish = Popen(r"C:\Users\Christian\Desktop\stockfish.exe", stdin=PIPE, stdout=PIPE)

while True:
    print(repr(stockfish.stdout.readline()))
    
    if 7 == 0:
        break


pg.init()
groesse = breite, hoehe = 700, 700
groesse_open = breite_open, hoehe_open = 1000, 700
screen = pg.display.set_mode(groesse, pg.RESIZABLE)

DIRECTION_OFFSETS = [8, -8, -1, 1, 7, -7, 9, -9]
player_turn = "w"

pieces_group = pg.sprite.Group()
clock = pg.time.Clock()

img_nb = None
for i in "kqbnrp":
    for j in "wb":
        exec(f"img_{i}{j} = pg.image.load('files/{i}_{j}.png').convert_alpha()")

img_over_normal = pg.image.load("files/overlay_normal.png").convert_alpha()
img_over_capture = pg.image.load(
    "files/overlay_capture.png").convert_alpha()
img_settings = pg.image.load("files/settings.png").convert_alpha()

pg.display.set_icon(img_nb)
pg.display.set_caption("Chess")

settings_open = False

board = [[None for _ in range(8)] for _ in range(8)]
moves = []
selected_piece = None


def draw_background():
    screen.fill((95, 216, 127))
    for i in range(8):
        for j in range(8):
            if not (i + j) % 2:
                pg.draw.rect(screen, (234, 198, 164),
                                 (i * 75 + 50, j * 75 + 50, 75, 75))
            else:
                pg.draw.rect(screen, (168, 94, 62),
                                 (i * 75 + 50, j * 75 + 50, 75, 75))
    pg.draw.rect(screen, (0, 0, 0), (45, 45, 610, 610), 5, 4)
    screen.blit(img_settings, (630, 10))


class Piece(pg.sprite.Sprite):
    def __init__(self, piece, row, column):
        pg.sprite.Sprite.__init__(self)
        self.type = piece[0]
        self.color = piece[1]
        self.row = row
        self.column = column
        if piece != "ew":
            exec(f"self.image = img_{piece}")
            self.rect = self.image.get_rect()
            self.rect.left = self.column * 75 + 50
            self.rect.top = self.row * 75 + 50
        if self.type == "p":
            self.en_passant = False
        elif self.type in ("k", "r"):
            self.castle = True

    def draw(self):
        screen.blit(self.image, self.rect)
    
    def move(self, x, y):
        board[self.row][self.column] = None
        self.row = y
        self.column = x
        board[self.row][self.column] = self
        self.rect.left = self.column * 75 + 50
        self.rect.top = self.row * 75 + 50


def load_from_fen(fen: str):
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
                piece = Piece(piece_type + piece_color, rank, file)
                pieces_group.add(piece)
                board[rank][file] = piece
                file += 1


def straight_line(board: list, piece: Piece, offsets: int) -> list:
    moves = []
    x, y = piece.row, piece.column
    while True:
        x += offsets[0]
        y += offsets[1]
        if not (x in range(8) and y in range(8)):
            return moves
        moves.append([x, y])
        if board[x][y] != None:
            return moves


def generate_moves(board: list, piece: Piece) -> list:
    moves = []
    if piece.type == "q":
        for i in range(-1, 2):
            for j in range(-1, 2):
                if i or j:
                    moves.extend(straight_line(board, piece, (i, j)))
        print(moves)
        return moves
    if piece.type == "r":
        for i in range(-1, 2):
            for j in range(-1, 2):
                if not (i and j) and (i or j):
                    moves.extend(straight_line(board, piece, (i, j)))
        print(moves)
        return moves
    if piece.type == "b":
        for i in (-1, 1):
            for j in (-1, 1):
                moves.extend(straight_line(board, piece, (i, j)))

        print(moves)
        return moves
    return moves


def toggle_screensize():
    global settings_open, screen
    if settings_open:
        settings_open = False
        screen = pg.display.set_mode(groesse)
    else:
        settings_open = True
        screen = pg.display.set_mode(groesse_open)

# load_from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")
load_from_fen("7k/3N2qp/b5r1/2p1Q1N1/Pp4PK/7P/1P3p2/6r1")

while True:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            quit()
        elif event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                # print(event.pos)
                if event.pos[0] in range(630, 656) and event.pos[1] in range(10, 36):
                    toggle_screensize()
                if event.pos[0] in range(50, 650) and event.pos[1] in range(50, 650):
                    row = (event.pos[1] - 50) // 75
                    column = (event.pos[0] - 50) // 75
                    if board[row][column] and board[row][column].type != "e" and not selected_piece:
                        selected_piece = board[row][column]
                        moves = generate_moves(board, selected_piece)
                    elif selected_piece and [row, column] in [i[1] for i in moves]:
                        # move piece to position
                        board[row][column].move(row, column)
                    else:
                        selected_piece = None
                        moves = []

                else:
                    selected_piece = None
                    moves = []

            elif event.button == 4:
                pass

            elif event.button == 5:
                pass

    draw_background()
    if selected_piece:
        pg.draw.rect(
            screen, (255, 255, 0), selected_piece.rect)

    for i in pieces_group:
        i.draw()

    # Code for displaying overlay
    for i in moves:
        if board[i[0]][i[1]]:
            screen.blit(img_over_capture, (i[1] * 75 + 50, i[0] * 75 + 50))
        else:
            screen.blit(img_over_normal, (i[1] * 75 + 50, i[0] * 75 + 50))

    pg.display.update()
    clock.tick(45)
