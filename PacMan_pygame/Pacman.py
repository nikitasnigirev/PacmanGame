import pygame
import numpy as np
import tcod
import random
from enum import Enum


class Score(Enum):
    COOKIE = 10
    POWERUP = 50
    GHOST = 400


class GhostMode(Enum):
    CHASE = 1
    SCATTER = 2

class Movement(Enum):
    DOWN = -90
    RIGHT = 0
    UP = 90
    LEFT = 180
    NONE = 360


class GameObj:
    def __init__(self, surface, x, y,
                 size: int, color=(255, 0, 0),
                 is_circle: bool = False):
        self._size = size
        self.renderer: Render = surface
        self.surface = surface.screen
        self.y = y
        self.x = x
        self._color = color
        self._circle = is_circle
        self._shape = pygame.Rect(self.x, self.y, size, size)

    def draw(self):
        if self._circle:
            pygame.draw.circle(self.surface,
                               self._color,
                               (self.x, self.y),
                               self._size)
        else:
            rect_object = pygame.Rect(self.x, self.y, self._size, self._size)
            pygame.draw.rect(self.surface,
                             self._color,
                             rect_object,
                             border_radius=1)

    def tick(self):
        pass

    def get_shape(self):
        return pygame.Rect(self.x, self.y, self._size, self._size)

    def set_position(self, x, y):
        self.x = x
        self.y = y

    def get_position(self):
        return (self.x, self.y)


class Wall(GameObj):
    def __init__(self, surface, x, y, size: int, color=(0, 0, 255)):
        super().__init__(surface, x * size, y * size, size, color)


class Render:
    def __init__(self, width: int, height: int):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption('Pacman')
        self.clock = pygame.time.Clock()
        self.done = False
        self.won = False
        self.game_objects = []
        self.walls = []
        self.cookies = []
        self.powerups = []
        self.ghosts = []
        self.pacman: Pacman = None
        self.lives = 3
        self.score = 0
        self.score_cookie_pickup = 10
        self.score_ghost_eaten = 400
        self.score_powerup_pickup = 50
        self.powerup_active = False  # powerup, special ability
        self.current_mode = GhostMode.SCATTER
        self.mode_switch_event = pygame.USEREVENT + 1
        self.powerup_end_event = pygame.USEREVENT + 2
        self.pakupaku_event = pygame.USEREVENT + 3
        self.modes = [
            (7, 99999),
            (7, 100),
            (5, 100),
            (5, 999999)
        ]
        self.current_phase = 0

    def tick(self, fps: int):
        black = (0, 0, 0)

        self.switch_mode()
        pygame.time.set_timer(self.pakupaku_event, 200)  # open close mouth
        while not self.done:
            for game_object in self.game_objects:
                game_object.tick()
                game_object.draw()

            self.display_text(f"[Score: {self.score}]  [Lives: {self.lives}]")

            if self.pacman is None: self.display_text("YOU DIED", (self.width / 2 - 256, self.height / 2 - 256), 100)
            if self.get_won(): self.display_text("YOU WON", (self.width / 2 - 256, self.height / 2 - 256), 100)
            pygame.display.flip()
            self.clock.tick(fps)
            self.screen.fill(black)
            self.handle_events()

    def switch_mode(self):
        phase_timing = self.modes[self.current_phase]
        scatter_time = phase_timing[0]
        chase_time = phase_timing[1]

        if self.current_mode == GhostMode.CHASE:
            self.current_phase += 1
            self.set_current_mode(GhostMode.SCATTER)
        else:
            self.set_current_mode(GhostMode.CHASE)

        used_timing = scatter_time if self.current_mode == GhostMode.SCATTER else chase_time
        pygame.time.set_timer(self.mode_switch_event, used_timing * 1000)

    def start_powerup_timeout(self):
        pygame.time.set_timer(self.powerup_end_event, 10000)  # 10s

    def add_game_obj(self, obj: GameObj):
        self.game_objects.append(obj)

    def add_cookie(self, obj: GameObj):
        self.game_objects.append(obj)
        self.cookies.append(obj)

    def add_ghost(self, obj: GameObj):
        self.game_objects.append(obj)
        self.ghosts.append(obj)

    def add_powerup(self, obj: GameObj):
        self.game_objects.append(obj)
        self.powerups.append(obj)

    def active_powerup(self):
        self.powerup_active = True
        self.set_current_mode(GhostMode.SCATTER)
        self.start_powerup_timeout()

    def set_won(self):
        self.won = True

    def get_won(self):
        return self.won

    def add_score(self, in_score: Score):
        self.score += in_score.value

    def get_hero_position(self):
        return self.pacman.get_position() if self.pacman != None else (0, 0)

    def set_current_mode(self, in_mode: GhostMode):
        self.current_mode = in_mode

    def get_current_mode(self):
        return self.current_mode

    def end_game(self):
        if self.pacman in self.game_objects:
            self.game_objects.remove(self.pacman)
        self.pacman = None

    def kill_pacman(self):
        self.lives -= 1
        self.pacman.set_position(32, 32)
        self.pacman.set_dir(Movement.NONE)
        if self.lives == 0: self.end_game()

    def display_text(self, text, in_position=(32, 0), in_size=30):
        font = pygame.font.SysFont('Arial', in_size)
        text_surface = font.render(text, False, (255, 255, 255))
        self.screen.blit(text_surface, in_position)

    def is_powerup_active(self):
        return self.powerup_active

    def add_wall(self, obj: Wall):
        self.add_game_obj(obj)
        self.walls.append(obj)

    def get_walls(self):
        return self.walls

    def get_cookies(self):
        return self.cookies

    def get_ghosts(self):
        return self.ghosts

    def get_powerups(self):
        return self.powerups

    def get_game_objects(self):
        return self.game_objects

    def add_hero(self, pacman):
        self.add_game_obj(pacman)
        self.pacman = pacman

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.done = True

            if event.type == self.mode_switch_event:
                self.switch_mode()

            if event.type == self.powerup_end_event:
                self.powerup_active = False

            if event.type == self.pakupaku_event:
                if self.pacman is None: break
                self.pacman.mouth_open = not self.pacman.mouth_open

        pressed = pygame.key.get_pressed()
        if self.pacman is None: return
        if pressed[pygame.K_UP]:
            self.pacman.set_dir(Movement.UP)
        elif pressed[pygame.K_LEFT]:
            self.pacman.set_dir(Movement.LEFT)
        elif pressed[pygame.K_DOWN]:
            self.pacman.set_dir(Movement.DOWN)
        elif pressed[pygame.K_RIGHT]:
            self.pacman.set_dir(Movement.RIGHT)



class MovableObj(GameObj):
    def __init__(self, surface, x, y, size: int, color=(255, 0, 0), is_circle: bool = False):
        super().__init__(surface, x, y, size, color, is_circle)
        self.current_direction = Movement.NONE
        self.direction_buff = Movement.NONE
        self.last_direction = Movement.NONE
        self.location_queue = []
        self.next_target = None
        self.image = pygame.image.load('images/ghost.png')

    def get_next_location(self):
        return None if len(self.location_queue) == 0 else self.location_queue.pop(0)

    def set_dir(self, direction):
        self.current_direction = direction
        self.direction_buff = direction

    def collides_with_wall(self, position):
        collision_rect = pygame.Rect(position[0], position[1], self._size, self._size)
        collides = False
        walls = self.renderer.get_walls()
        for wall in walls:
            collides = collision_rect.colliderect(wall.get_shape())
            if collides: break
        return collides

    def check_collision_in_direction(self, direction: Movement):
        desired_position = (0, 0)
        if direction == Movement.NONE: return False, desired_position
        if direction == Movement.UP:
            desired_position = (self.x, self.y - 1)
        elif direction == Movement.DOWN:
            desired_position = (self.x, self.y + 1)
        elif direction == Movement.LEFT:
            desired_position = (self.x - 1, self.y)
        elif direction == Movement.RIGHT:
            desired_position = (self.x + 1, self.y)

        return self.collides_with_wall(desired_position), desired_position

    def automatic_move(self, direction: Movement):
        pass

    def tick(self):
        self.reached_target()
        self.automatic_move(self.current_direction)

    def reached_target(self):
        pass

    def draw(self):
        self.image = pygame.transform.scale(self.image, (32, 32))
        self.surface.blit(self.image, self.get_shape())


class Pacman(MovableObj):
    def __init__(self, surface, x, y, size: int):
        super().__init__(surface, x, y, size, (255, 255, 0), False)
        self.last_notcolliding_position = (0, 0)
        self.open = pygame.image.load("images/paku.png")
        self.closed = pygame.image.load("images/man.png")
        self.image = self.open
        self.mouth_open = True

    def tick(self):
        # Телепорт
        if self.x < 0:
            self.x = self.renderer.width

        if self.x > self.renderer.width:
            self.x = 0

        self.last_notcolliding_position = self.get_position()

        if self.check_collision_in_direction(self.direction_buff)[0]:
            self.automatic_move(self.current_direction)
        else:
            self.automatic_move(self.direction_buff)
            self.current_direction = self.direction_buff

        if self.collides_with_wall((self.x, self.y)):
            self.set_position(self.last_notcolliding_position[0], self.last_notcolliding_position[1])

        self.handle_cookie_and_powerup_pickup()
        self.handle_ghosts()

    def automatic_move(self, direction: Movement):
        collision_result = self.check_collision_in_direction(direction)

        desired_position_collides = collision_result[0]
        if not desired_position_collides:
            self.last_direction = self.current_direction
            desired_position = collision_result[1]
            self.set_position(desired_position[0], desired_position[1])
        else:
            self.current_direction = self.last_direction

    def handle_cookie_and_powerup_pickup(self):
        collision_rect = pygame.Rect(self.x, self.y, self._size, self._size)
        cookies = self.renderer.get_cookies()
        powerups = self.renderer.get_powerups()
        game_objects = self.renderer.get_game_objects()
        cookie_to_remove = None
        for cookie in cookies:
            collides = collision_rect.colliderect(cookie.get_shape())
            if collides and cookie in game_objects:
                game_objects.remove(cookie)
                self.renderer.add_score(Score.COOKIE)
                cookie_to_remove = cookie

        if cookie_to_remove is not None:
            cookies.remove(cookie_to_remove)

        if len(self.renderer.get_cookies()) == 0:
            self.renderer.set_won()

        for powerup in powerups:
            collides = collision_rect.colliderect(powerup.get_shape())
            if collides and powerup in game_objects:
                if not self.renderer.is_powerup_active():
                    game_objects.remove(powerup)
                    self.renderer.add_score(Score.POWERUP)
                    self.renderer.active_powerup()

    def handle_ghosts(self):
        collision_rect = pygame.Rect(self.x, self.y, self._size, self._size)
        ghosts = self.renderer.get_ghosts()
        game_objects = self.renderer.get_game_objects()
        for ghost in ghosts:
            collides = collision_rect.colliderect(ghost.get_shape())
            if collides and ghost in game_objects:
                if self.renderer.is_powerup_active():
                    game_objects.remove(ghost)
                    self.renderer.add_score(Score.GHOST)
                else:
                    if not self.renderer.get_won():
                        self.renderer.kill_pacman()

    def draw(self):
        self.image = self.open if self.mouth_open else self.closed
        self.image = pygame.transform.rotate(self.image, self.current_direction.value)
        super(Pacman, self).draw()


class Ghost(MovableObj):
    def __init__(self, in_surface, x, y, size: int, game_controller, sprite_path="images/ghost_fright.png"):
        super().__init__(in_surface, x, y, size)
        self.game_controller = game_controller
        self.normal_sprite = pygame.image.load(sprite_path)
        self.fright_sprite = pygame.image.load("images/ghost_fright.png")

    def reached_target(self):
        if (self.x, self.y) == self.next_target:
            self.next_target = self.get_next_location()
        self.current_direction = self.calculate_direction_to_next_target()

    def set_new_path(self, path):
        for item in path:
            self.location_queue.append(item)
        self.next_target = self.get_next_location()

    def calculate_direction_to_next_target(self) -> Movement:
        if self.next_target is None:
            if self.renderer.get_current_mode() == GhostMode.CHASE and not self.renderer.is_powerup_active():
                self.path_to_player(self)
            else:
                self.game_controller.request_random_path(self)
            return Movement.NONE

        diff_x = self.next_target[0] - self.x
        diff_y = self.next_target[1] - self.y
        if diff_x == 0:
            return Movement.DOWN if diff_y > 0 else Movement.UP
        if diff_y == 0:
            return Movement.LEFT if diff_x < 0 else Movement.RIGHT

        if self.renderer.get_current_mode() == GhostMode.CHASE and not self.renderer.is_powerup_active():
            self.path_to_player(self)
        else:
            self.game_controller.request_random_path(self)
        return Movement.NONE

    def path_to_player(self, in_ghost):
        player_position = screen_to_maze(in_ghost.renderer.get_hero_position())
        maze_coord = screen_to_maze(in_ghost.get_position())
        path = self.game_controller.p.get_path(maze_coord[1], maze_coord[0], player_position[1],
                                               player_position[0])

        new_path = [maze_to_screen(item) for item in path]
        in_ghost.set_new_path(new_path)

    def automatic_move(self, direction: Movement):
        if direction == Movement.UP:
            self.set_position(self.x, self.y - 1)
        elif direction == Movement.DOWN:
            self.set_position(self.x, self.y + 1)
        elif direction == Movement.LEFT:
            self.set_position(self.x - 1, self.y)
        elif direction == Movement.RIGHT:
            self.set_position(self.x + 1, self.y)

    def draw(self):
        self.image = self.fright_sprite if self.renderer.is_powerup_active() else self.normal_sprite
        super(Ghost, self).draw()


class Point(GameObj):
    def __init__(self, surface, x, y):
        super().__init__(surface, x, y, 4, (255, 255, 0), True)


class Powerup(GameObj):
    def __init__(self, surface, x, y):
        super().__init__(surface, x, y, 8, (255, 255, 255), True)


class PathFinder:
    def __init__(self, arr):
        cost = np.array(arr, dtype=np.bool_).tolist()
        self.pf = tcod.path.AStar(cost=cost, diagonal=0)

    def get_path(self, from_x, from_y, to_x, to_y) -> object:
        res = self.pf.get_path(from_x, from_y, to_x, to_y)
        return [(sub[1], sub[0]) for sub in res]


class GameController:
    def __init__(self):
        self.maze = [
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            "XP           XX            X",
            "X XXXX XXXXX XX XXXXX XXXX X",
            "X XXXXOXXXXX XX XXXXXOXXXX X",
            "X XXXX XXXXX XX XXXXX XXXX X",
            "X                          X",
            "X XXXX XX XXXXXXXX XX XXXX X",
            "X XXXX XX XXXXXXXX XX XXXX X",
            "X      XX    XX    XX      X",
            "XXXXXX XXXXX XX XXXXX XXXXXX",
            "XXXXXX XXXXX XX XXXXX XXXXXX",
            "XXXXXX XX     G    XX XXXXXX",
            "XXXXXX XX XXX  XXX XX XXXXXX",
            "XXXXXX XX X      X XX XXXXXX",
            "   G      X      X          ",
            "XXX XX XX X      X XX XX XXX",
            "XXX XX XX XXXXXXXX XX XX XXX",
            "XXX    XX    G     XX    XXX",
            "XXX XX XX XXXXXXXX XX XX XXX",
            "XXX XXOXX XXXXXXXX XXOXX XXX",
            "XXX          G           XXX",
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        ]

        self.numpy_maze = []
        self.point_spaces = []
        self.powerup_spaces = []
        self.reachable_spaces = []
        self.ghost_spawns = []
        self.ghost_colors = [
            "images/ghost.png",
            "images/ghost_pink.png",
            "images/ghost_orange.png",
            "images/ghost_blue.png"
        ]
        self.size = (0, 0)
        self.convert_maze_to_numpy()
        self.p = PathFinder(self.numpy_maze)

    def request_random_path(self, ghost: Ghost):
        random_space = random.choice(self.reachable_spaces)
        maze_coord = screen_to_maze(ghost.get_position())

        path = self.p.get_path(maze_coord[1], maze_coord[0], random_space[1],
                               random_space[0])
        test_path = [maze_to_screen(item) for item in path]
        ghost.set_new_path(test_path)

    def convert_maze_to_numpy(self):
        for x, row in enumerate(self.maze):
            self.size = (len(row), x + 1)
            binary_row = []
            for y, column in enumerate(row):
                if column == "G":
                    self.ghost_spawns.append((y, x))

                if column == "X":
                    binary_row.append(0)
                else:
                    binary_row.append(1)
                    self.point_spaces.append((y, x))
                    self.reachable_spaces.append((y, x))
                    if column == "O":
                        self.powerup_spaces.append((y, x))

            self.numpy_maze.append(binary_row)

def screen_to_maze(coord, size=32):
    return int(coord[0] / size), int(coord[1] / size)


def maze_to_screen(coord, size=32):
    return coord[0] * size, coord[1] * size

if __name__ == "__main__":
    unified_size = 32
    pacman_game = GameController()
    size = pacman_game.size
    game_renderer = Render(size[0] * unified_size, size[1] * unified_size)

    for y, row in enumerate(pacman_game.numpy_maze):
        for x, column in enumerate(row):
            if column == 0:
                game_renderer.add_wall(Wall(game_renderer, x, y, unified_size))

    for cookie_space in pacman_game.point_spaces:
        translated = maze_to_screen(cookie_space)
        cookie = Point(game_renderer, translated[0] + unified_size / 2, translated[1] + unified_size / 2)
        game_renderer.add_cookie(cookie)

    for powerup_space in pacman_game.powerup_spaces:
        translated = maze_to_screen(powerup_space)
        powerup = Powerup(game_renderer, translated[0] + unified_size / 2, translated[1] + unified_size / 2)
        game_renderer.add_powerup(powerup)

    for i, ghost_spawn in enumerate(pacman_game.ghost_spawns):
        translated = maze_to_screen(ghost_spawn)
        ghost = Ghost(game_renderer, translated[0], translated[1], unified_size, pacman_game,
                      pacman_game.ghost_colors[i % 4])
        game_renderer.add_ghost(ghost)

    pacman = Pacman(game_renderer, unified_size, unified_size, unified_size)
    game_renderer.add_hero(pacman)
    game_renderer.set_current_mode(GhostMode.CHASE)
    game_renderer.tick(120)
