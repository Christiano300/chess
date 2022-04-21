import pygame
pygame.init()
groesse = breite, hoehe = 700, 700
groesse_open = breite_open, hoehe_open = 1000, 700
screen = pygame.display.set_mode(groesse, pygame.RESIZABLE)

DIRECTION_OFFSETS = [8, -8, -1, 1, 7, -7, 9, -9]
player_turn = "w"

pieces_group = pygame.sprite.Group()
clock = pygame.time.Clock()

img_nb = None
for i in "kqbnrp":
    for j in "wb":
        exec(f"img_{i}{j} = pygame.image.load('files/{i}_{j}.png').convert_alpha()")

img_over_normal = pygame.image.load("files/overlay_normal.png").convert_alpha()
img_over_capture = pygame.image.load(
    "files/overlay_capture.png").convert_alpha()
img_settings = pygame.image.load("files/settings.png").convert_alpha()

pygame.display.set_icon(img_nb)
pygame.display.set_caption("Chess")

settings_open = False

board = [None for _ in range(64)]
moves = []
selected_piece = None


def draw_background():
    screen.fill((95, 216, 127))
    for i in range(8):
        for j in range(8):
            if not (i + j) % 2:
                pygame.draw.rect(screen, (234, 198, 164),
                                 (i * 75 + 50, j * 75 + 50, 75, 75))
            else:
                pygame.draw.rect(screen, (168, 94, 62),
                                 (i * 75 + 50, j * 75 + 50, 75, 75))
    pygame.draw.rect(screen, (0, 0, 0), (45, 45, 610, 610), 5, 4)
    screen.blit(img_settings, (630, 10))


class Piece(pygame.sprite.Sprite):
    def __init__(self, piece, index):
        pygame.sprite.Sprite.__init__(self)
        self.type = piece[0]
        self.color = piece[1]
        self.index = index
        if piece != "ew":
            exec(f"self.image = img_{piece}")
            self.rect = self.image.get_rect()
            self.rect.left = self.index % 8 * 75 + 50
            self.rect.top = (7 - self.index // 8) * 75 + 50
        if self.type == "p":
            self.en_passant = False
        elif self.type in ("k", "r"):
            self.castle = True

    def draw(self):

        screen.blit(self.image, self.rect)


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
                piece = Piece(piece_type + piece_color, rank * 8 + file)
                pieces_group.add(piece)
                board[rank * 8 + file] = piece
                file += 1


def spaces_to_edge(index: int, dir: int) -> int:
    if dir == 0:  # north
        return 7 - index // 8
    elif dir == 1:  # south
        return index // 8
    elif dir == 2:  # west
        return index % 8
    elif dir == 3:  # east
        return 7 - index % 8
    elif dir == 4:
        return min(7 - index // 8, index % 8)
    elif dir == 5:
        return min(index // 8, 7 - index % 8)
    elif dir == 6:
        return min(7 - index // 8, 7 - index % 8)
    else:
        return min(index // 8, index % 8)


def generate_moves(board: list, piece: Piece) -> list:
    moves = []
    if piece.type in ("q", "r", "b"):
        if piece.type == "q":
            diroffsets = DIRECTION_OFFSETS
        elif piece.type == "r":
            diroffsets = DIRECTION_OFFSETS[:4]
        else:
            diroffsets = DIRECTION_OFFSETS[4:]
        for dirindex, diroffset in enumerate(diroffsets):
            for i in range(spaces_to_edge(piece.index, dirindex)):
                space = board[i * diroffset]
                ispiece = isinstance(space, Piece)
                if ispiece and space.color == piece.color:
                    break
                elif ispiece:
                    moves.append([piece.index, space.index])
                    break
                moves.append([piece.index, i * diroffset])

    elif piece.type == "k":
        for dirindex, diroffset in enumerate(DIRECTION_OFFSETS):
            if spaces_to_edge(piece.index, dirindex):
                moves.append([piece.index, piece.index + diroffset])

    elif piece.type == "n":
        for dirindex, diroffset in enumerate(DIRECTION_OFFSETS[:4]):
            if spaces_to_edge(piece.index, dirindex) and spaces_to_edge(piece.index, dirindex - 4):
                moves.append([piece.index, piece.index + diroffset *
                             2 + DIRECTION_OFFSETS[diroffset - 4]])

    elif piece.type == "p":
        if piece.color == "w":
            if spaces_to_edge(piece.index, 0) and board[piece.index + 8]:
                moves.append([piece.index, piece.index + 8])
            if piece.index // 8 == 1 and board[piece.index + 16]:
                moves.append([piece.index, piece.index + 16])
                piece = Piece("e" + piece.color, ())

            if spaces_to_edge(piece.index, 0) and board[piece.index + 9] and board[piece.index + 9].color == "b":
                moves.append([piece.index, piece.index + 9])
            if spaces_to_edge(piece.index, 0) and board[piece.index + 7] and board[piece.index + 7].color == "b":
                moves.append([piece.index, piece.index + 7])

        if piece.color == "b":
            if spaces_to_edge(piece.index, 1) and board[piece.index + 1]:
                moves.append([piece.index, piece.index + 8])
            if piece.index // 8 == 1 and board[piece.index + 16]:
                moves.append([piece.index, piece.index + 16])
            if spaces_to_edge(piece.index, 1) and board[piece.index + -9] and board[piece.index + -9].color == "w":
                moves.append([piece.index, piece.index + 9])
            if spaces_to_edge(piece.index, 1) and board[piece.index + -7] and board[piece.index + -7].color == "w":
                moves.append([piece.index, piece.index + -7])

    return moves


def toggle_screensize():
    global settings_open
    global screen
    if settings_open:
        settings_open = False
        screen = pygame.display.set_mode(groesse)
    else:
        settings_open = True
        screen = pygame.display.set_mode(groesse_open)


# load_from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")
load_from_fen("7k/3N2qp/b5r1/2p1Q1N1/Pp4PK/7P/1P3p2/6r1")

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # print(event.pos)
                if event.pos[0] in range(630, 656) and event.pos[1] in range(10, 36):
                    toggle_screensize()
                if event.pos[0] in range(50, 650) and event.pos[1] in range(50, 650):
                    index = (event.pos[0] - 50) // 75 + \
                        (7 - (event.pos[1] - 50) // 75) * 8
                    if board[index] and board[index].type != "e" and not selected_piece:
                        selected_piece = board[index]
                        moves = generate_moves(board, selected_piece)
                    elif selected_piece and index in [i[1] for i in moves]:
                        # move piece to position
                        pass
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
        pygame.draw.rect(
            screen, (255, 255, 0), selected_piece.rect)

    for i in pieces_group:
        i.draw()

    # Code for displaying overlay
    for i in moves:
        if board[i[1]]:
            screen.blit(img_over_capture,
                        (i[1] % 8 * 75 + 50, (7 - i[1]) // 8 * 75 + 50))
        else:
            screen.blit(img_over_normal,
                        (i[1] % 8 * 75 + 50, (7 - i[1]) // 8 * 75 + 50))

    pygame.display.update()
    clock.tick(45)
