import math
import random
import sys
from dataclasses import dataclass

import pygame


WIDTH, HEIGHT = 900, 700
GRID_SIZE = 3
BOARD_PIXELS = 540
CELL_SIZE = BOARD_PIXELS // GRID_SIZE
BOARD_LEFT = (WIDTH - BOARD_PIXELS) // 2
BOARD_TOP = 100
BOARD_RECT = pygame.Rect(BOARD_LEFT, BOARD_TOP, BOARD_PIXELS, BOARD_PIXELS)
FPS = 60

EMPTY = 0
HUMAN = 1
AI = 2

MENU = "menu"
PLAYING = "playing"
GAME_OVER = "game_over"

EASY = "Easy"
MEDIUM = "Medium"
HARD = "Hard"
DIFFICULTIES = [EASY, MEDIUM, HARD]


@dataclass
class MoveResult:
    row: int
    col: int


class ChalkTicTacToe:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Naughts and Crosses - Chalkboard")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.font_large = pygame.font.SysFont("georgia", 54, bold=True)
        self.font_medium = pygame.font.SysFont("georgia", 34, bold=True)
        self.font_small = pygame.font.SysFont("georgia", 24)

        self.chalk_color = (225, 240, 220)
        self.board_color = (20, 72, 38)

        self.background = self._create_chalkboard_background()
        self.grid_surface = self._create_grid_surface()

        self.state = MENU
        self.difficulty = MEDIUM
        self.reset_game()

    def _start_game(self, difficulty: str) -> None:
        self.difficulty = difficulty
        self.state = PLAYING
        self.reset_game()

    def _return_to_menu(self) -> None:
        self.state = MENU
        self.reset_game()

    def _start_rematch(self) -> None:
        self.state = PLAYING
        self.reset_game()

    def _menu_option_rect(self, idx: int, label: str) -> pygame.Rect:
        y = 265 + idx * 56
        text_rect = self.font_medium.render(label, True, self.chalk_color).get_rect(center=(WIDTH // 2, y))
        return text_rect.inflate(72, 20)

    def _playing_menu_rect(self) -> pygame.Rect:
        text_rect = self.font_small.render("M: menu", True, self.chalk_color).get_rect(center=(WIDTH - 110, 24))
        return text_rect.inflate(24, 14)

    def _game_over_rematch_rect(self) -> pygame.Rect:
        text_rect = self.font_small.render("R: Rematch", True, self.chalk_color).get_rect(center=(WIDTH // 2 - 92, 82))
        return text_rect.inflate(24, 14)

    def _game_over_menu_rect(self) -> pygame.Rect:
        text_rect = self.font_small.render("M: menu", True, self.chalk_color).get_rect(center=(WIDTH // 2 + 110, 82))
        return text_rect.inflate(24, 14)

    def reset_game(self) -> None:
        self.board = [[EMPTY for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.current_player = HUMAN
        self.winner = EMPTY
        self.winning_combo = None
        self.game_over_reason = ""
        self.pending_ai_move_ms = 0
        self.mark_layers = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    def _create_chalkboard_background(self) -> pygame.Surface:
        surface = pygame.Surface((WIDTH, HEIGHT))
        surface.fill(self.board_color)
        rng = random.Random(6)

        # Layer subtle grain to mimic chalkboard texture.
        for _ in range(18000):
            x = rng.randrange(WIDTH)
            y = rng.randrange(HEIGHT)
            shade = rng.randint(-12, 14)
            base = 60 + shade
            color = (max(0, base // 3), max(0, base), max(0, base // 2))
            surface.set_at((x, y), color)

        vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        cx, cy = WIDTH // 2, HEIGHT // 2
        max_dist = math.hypot(cx, cy)
        for y in range(HEIGHT):
            for x in range(WIDTH):
                dist = math.hypot(x - cx, y - cy)
                alpha = int((dist / max_dist) * 58)
                vignette.set_at((x, y), (0, 0, 0, alpha))
        surface.blit(vignette, (0, 0))

        return surface.convert()

    def _create_grid_surface(self) -> pygame.Surface:
        surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        rng = random.Random(22)

        for i in range(1, GRID_SIZE):
            x = BOARD_LEFT + i * CELL_SIZE
            y = BOARD_TOP + i * CELL_SIZE

            self._draw_scribble_line(
                surface,
                (x, BOARD_TOP + 12),
                (x, BOARD_TOP + BOARD_PIXELS - 12),
                self.chalk_color,
                width=8,
                wiggle=4,
                passes=3,
                rng=rng,
            )
            self._draw_scribble_line(
                surface,
                (BOARD_LEFT + 12, y),
                (BOARD_LEFT + BOARD_PIXELS - 12, y),
                self.chalk_color,
                width=8,
                wiggle=4,
                passes=3,
                rng=rng,
            )

        return surface

    def _draw_scribble_line(
        self,
        surface: pygame.Surface,
        start: tuple[int, int],
        end: tuple[int, int],
        color: tuple[int, int, int],
        width: int,
        wiggle: float,
        passes: int,
        rng: random.Random,
    ) -> None:
        sx, sy = start
        ex, ey = end
        for _ in range(passes):
            points = []
            steps = 22
            for i in range(steps + 1):
                t = i / steps
                x = sx + (ex - sx) * t + rng.uniform(-wiggle, wiggle)
                y = sy + (ey - sy) * t + rng.uniform(-wiggle, wiggle)
                points.append((x, y))
            w = max(1, width + rng.randint(-2, 2))
            pygame.draw.lines(surface, color, False, points, w)

            # Chalk dust around each pass.
            for _ in range(40):
                t = rng.random()
                x = sx + (ex - sx) * t + rng.uniform(-10, 10)
                y = sy + (ey - sy) * t + rng.uniform(-10, 10)
                pygame.draw.circle(surface, (*color, 65), (int(x), int(y)), rng.randint(1, 2))

    def _cell_rect(self, row: int, col: int) -> pygame.Rect:
        return pygame.Rect(
            BOARD_LEFT + col * CELL_SIZE,
            BOARD_TOP + row * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE,
        )

    def _draw_scribble_x(self, row: int, col: int) -> pygame.Surface:
        rect = self._cell_rect(row, col)
        layer = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        rng = random.Random(1000 + row * 31 + col * 17)
        margin = 34
        p1 = (margin, margin)
        p2 = (CELL_SIZE - margin, CELL_SIZE - margin)
        p3 = (CELL_SIZE - margin, margin)
        p4 = (margin, CELL_SIZE - margin)

        self._draw_scribble_line(layer, p1, p2, self.chalk_color, width=8, wiggle=5, passes=3, rng=rng)
        self._draw_scribble_line(layer, p3, p4, self.chalk_color, width=8, wiggle=5, passes=3, rng=rng)

        return layer

    def _draw_scribble_o(self, row: int, col: int) -> pygame.Surface:
        layer = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        rng = random.Random(2000 + row * 47 + col * 23)
        center = (CELL_SIZE // 2, CELL_SIZE // 2)
        radius = CELL_SIZE // 2 - 34

        for _ in range(3):
            points = []
            segments = 70
            wobble = rng.uniform(3, 7)
            for i in range(segments + 1):
                t = (i / segments) * math.tau
                r = radius + rng.uniform(-wobble, wobble)
                x = center[0] + math.cos(t) * r + rng.uniform(-1.5, 1.5)
                y = center[1] + math.sin(t) * r + rng.uniform(-1.5, 1.5)
                points.append((x, y))
            pygame.draw.lines(layer, self.chalk_color, True, points, rng.randint(5, 8))

        for _ in range(90):
            angle = rng.uniform(0, math.tau)
            r = radius + rng.uniform(-8, 8)
            x = center[0] + math.cos(angle) * r
            y = center[1] + math.sin(angle) * r
            pygame.draw.circle(layer, (*self.chalk_color, 70), (int(x), int(y)), rng.randint(1, 2))

        return layer

    def _available_moves(self, board: list[list[int]]) -> list[MoveResult]:
        moves = []
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if board[r][c] == EMPTY:
                    moves.append(MoveResult(r, c))
        return moves

    def _check_winner(self, board: list[list[int]]) -> tuple[int, tuple[tuple[int, int], ...] | None]:
        lines = []

        for r in range(GRID_SIZE):
            lines.append(((r, 0), (r, 1), (r, 2)))
        for c in range(GRID_SIZE):
            lines.append(((0, c), (1, c), (2, c)))
        lines.append(((0, 0), (1, 1), (2, 2)))
        lines.append(((0, 2), (1, 1), (2, 0)))

        for combo in lines:
            a, b, c = combo
            v1 = board[a[0]][a[1]]
            v2 = board[b[0]][b[1]]
            v3 = board[c[0]][c[1]]
            if v1 != EMPTY and v1 == v2 == v3:
                return v1, combo

        if all(board[r][c] != EMPTY for r in range(GRID_SIZE) for c in range(GRID_SIZE)):
            return -1, None  # Draw

        return EMPTY, None

    def _simulate_winning_move(self, player: int) -> MoveResult | None:
        for move in self._available_moves(self.board):
            self.board[move.row][move.col] = player
            winner, _ = self._check_winner(self.board)
            self.board[move.row][move.col] = EMPTY
            if winner == player:
                return move
        return None

    def _minimax(self, board: list[list[int]], maximizing: bool) -> tuple[int, MoveResult | None]:
        winner, _ = self._check_winner(board)
        if winner == AI:
            return 10, None
        if winner == HUMAN:
            return -10, None
        if winner == -1:
            return 0, None

        moves = self._available_moves(board)
        if maximizing:
            best_score = -999
            best_move = None
            for move in moves:
                board[move.row][move.col] = AI
                score, _ = self._minimax(board, False)
                board[move.row][move.col] = EMPTY
                score -= 1
                if score > best_score:
                    best_score = score
                    best_move = move
            return best_score, best_move

        best_score = 999
        best_move = None
        for move in moves:
            board[move.row][move.col] = HUMAN
            score, _ = self._minimax(board, True)
            board[move.row][move.col] = EMPTY
            score += 1
            if score < best_score:
                best_score = score
                best_move = move
        return best_score, best_move

    def _ai_move(self) -> None:
        if self.state != PLAYING:
            return

        move = None
        moves = self._available_moves(self.board)
        if not moves:
            return

        if self.difficulty == EASY:
            move = random.choice(moves)

        elif self.difficulty == MEDIUM:
            move = self._simulate_winning_move(AI)
            if move is None:
                move = self._simulate_winning_move(HUMAN)
            if move is None:
                # Mildly strategic randomness.
                center = next((m for m in moves if m.row == 1 and m.col == 1), None)
                if center and random.random() < 0.6:
                    move = center
                else:
                    corners = [m for m in moves if m.row in (0, 2) and m.col in (0, 2)]
                    move = random.choice(corners if corners else moves)

        else:  # HARD
            _, move = self._minimax(self.board, True)
            if move is None:
                move = random.choice(moves)

        self._place_mark(move.row, move.col, AI)

    def _place_mark(self, row: int, col: int, player: int) -> None:
        self.board[row][col] = player
        if player == HUMAN:
            self.mark_layers[row][col] = self._draw_scribble_x(row, col)
        else:
            self.mark_layers[row][col] = self._draw_scribble_o(row, col)

        winner, combo = self._check_winner(self.board)
        if winner == HUMAN:
            self.winner = HUMAN
            self.winning_combo = combo
            self.state = GAME_OVER
            self.game_over_reason = "You win!"
        elif winner == AI:
            self.winner = AI
            self.winning_combo = combo
            self.state = GAME_OVER
            self.game_over_reason = "Computer wins!"
        elif winner == -1:
            self.winner = -1
            self.winning_combo = None
            self.state = GAME_OVER
            self.game_over_reason = "Draw game"
        else:
            self.current_player = HUMAN if player == AI else AI
            if self.current_player == AI:
                self.pending_ai_move_ms = pygame.time.get_ticks() + 420

    def _handle_click(self, pos: tuple[int, int]) -> None:
        if self.state == MENU:
            for idx, level in enumerate(DIFFICULTIES, start=1):
                label = f"{idx}. {level}"
                if self._menu_option_rect(idx, label).collidepoint(pos):
                    self._start_game(level)
                    return
            return

        if self.state == GAME_OVER:
            if self._game_over_rematch_rect().collidepoint(pos):
                self._start_rematch()
                return
            if self._game_over_menu_rect().collidepoint(pos):
                self._return_to_menu()
                return
            return

        if self._playing_menu_rect().collidepoint(pos):
            self._return_to_menu()
            return

        if self.state != PLAYING or self.current_player != HUMAN:
            return
        if not BOARD_RECT.collidepoint(pos):
            return

        col = (pos[0] - BOARD_LEFT) // CELL_SIZE
        row = (pos[1] - BOARD_TOP) // CELL_SIZE

        if self.board[row][col] != EMPTY:
            return

        self._place_mark(row, col, HUMAN)

    def _draw_chalk_text(
        self,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        x: int,
        y: int,
        centered: bool = True,
    ) -> None:
        rng = random.Random(hash((text, x, y)) & 0xFFFFFFFF)
        for _ in range(3):
            jitter_x = x + rng.randint(-1, 1)
            jitter_y = y + rng.randint(-1, 1)
            render = font.render(text, True, color)
            rect = render.get_rect()
            if centered:
                rect.center = (jitter_x, jitter_y)
            else:
                rect.topleft = (jitter_x, jitter_y)
            self.screen.blit(render, rect)

    def _draw_menu(self) -> None:
        self._draw_chalk_text("Naughts and Crosses", self.font_large, self.chalk_color, WIDTH // 2, 140)
        self._draw_chalk_text("Choose computer difficulty", self.font_medium, self.chalk_color, WIDTH // 2, 235)

        for idx, level in enumerate(DIFFICULTIES, start=1):
            active = level == self.difficulty
            color = (248, 252, 242) if active else (198, 214, 192)
            label = f"{idx}. {level}"
            option_rect = self._menu_option_rect(idx, label)
            if active:
                pygame.draw.rect(self.screen, (170, 196, 160), option_rect, width=2, border_radius=8)
            self._draw_chalk_text(label, self.font_medium, color, WIDTH // 2, 265 + idx * 56)

        self._draw_chalk_text("Press 1, 2, 3, or click to start", self.font_small, self.chalk_color, WIDTH // 2, 500)

    def _draw_winning_scratch(self) -> None:
        if not self.winning_combo:
            return

        (r1, c1), _, (r3, c3) = self.winning_combo
        start = (
            BOARD_LEFT + c1 * CELL_SIZE + CELL_SIZE // 2,
            BOARD_TOP + r1 * CELL_SIZE + CELL_SIZE // 2,
        )
        end = (
            BOARD_LEFT + c3 * CELL_SIZE + CELL_SIZE // 2,
            BOARD_TOP + r3 * CELL_SIZE + CELL_SIZE // 2,
        )

        layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        rng = random.Random(509)
        self._draw_scribble_line(layer, start, end, (250, 245, 220), width=12, wiggle=9, passes=4, rng=rng)
        self.screen.blit(layer, (0, 0))

    def _draw_play(self) -> None:
        self.screen.blit(self.grid_surface, (0, 0))

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                layer = self.mark_layers[r][c]
                if layer is not None:
                    self.screen.blit(layer, (BOARD_LEFT + c * CELL_SIZE, BOARD_TOP + r * CELL_SIZE))

        self._draw_chalk_text(
            f"Difficulty: {self.difficulty}",
            self.font_small,
            self.chalk_color,
            24,
            24,
            centered=False,
        )

        if self.state == PLAYING:
            turn = "Your move" if self.current_player == HUMAN else "Computer thinking..."
            self._draw_chalk_text(turn, self.font_medium, self.chalk_color, WIDTH // 2, 42)
            self._draw_chalk_text("M: menu", self.font_small, self.chalk_color, WIDTH - 110, 24)
        else:
            self._draw_winning_scratch()
            self._draw_chalk_text(self.game_over_reason, self.font_medium, self.chalk_color, WIDTH // 2, 42)
            self._draw_chalk_text("R: Rematch", self.font_small, self.chalk_color, WIDTH // 2 - 92, 82)
            self._draw_chalk_text("M: menu", self.font_small, self.chalk_color, WIDTH // 2 + 110, 82)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            if self.state == MENU:
                if event.key in (pygame.K_1, pygame.K_KP1):
                    self._start_game(EASY)
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    self._start_game(MEDIUM)
                elif event.key in (pygame.K_3, pygame.K_KP3):
                    self._start_game(HARD)

            elif self.state in (PLAYING, GAME_OVER):
                if event.key == pygame.K_m:
                    self._return_to_menu()
                elif event.key == pygame.K_r and self.state == GAME_OVER:
                    self._start_rematch()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos)

    def update(self) -> None:
        if self.state == PLAYING and self.current_player == AI:
            now = pygame.time.get_ticks()
            if now >= self.pending_ai_move_ms:
                self.pending_ai_move_ms = 0
                self._ai_move()

    def draw(self) -> None:
        self.screen.blit(self.background, (0, 0))

        if self.state == MENU:
            self._draw_menu()
        else:
            self._draw_play()

        pygame.display.flip()

    def run(self) -> None:
        while True:
            for event in pygame.event.get():
                self.handle_event(event)

            self.update()
            self.draw()
            self.clock.tick(FPS)


def main() -> None:
    game = ChalkTicTacToe()
    game.run()


if __name__ == "__main__":
    main()
