import pygame
import os
import sys
import inspect
import time
from copy import deepcopy
from source_py import main
from source_py import player as pl

pygame.init()
WIDTH, HEIGHT = 550, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
all_sprites = pygame.sprite.Group()
tiles_group = pygame.sprite.Group()
player_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
FPS = 100
STEP = 50


def load_image(name, colorkey=None):
    # jpg, png, gif без анимации, bmp, pcx, tga, tif, lbm, pbm, xpm
    fullname = os.path.join("..\\", "data", "images", name)  # получение полного пути к файлу
    if not os.path.isfile(fullname):  # если файл не найден
        print(f"Файл с изображением {fullname} не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:  # пусть colorkey будет (0, 0) пикселем
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


# Shooting
EAST = 0
SE = 1
SOUTH = 2
SW = 3
WEST = 4
NW = 5
NORTH = 6
NE = 7
SHOOTING_SIDES = [[1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0], [-1, -1], [0, -1], [1, -1]]
SHOOT_AROUND = [i for i in range(8)]
SHOOT_FOUR_SIDES = [0, 2, 4, 6]
SHOOT_FOUR_SIDES_45 = [1, 3, 5, 7]
FRENDLY = True
#


class SpriteStates:
    IDLE = "1idle"
    FALLING = "2falling"
    JUMPING = "3jumping"
    MOVING = "4moving right"
    SLIDING = "5sliding left"
    DEAD = "8dead"

    @staticmethod
    def get_states():
        attributes = inspect.getmembers(SpriteStates, lambda a: not (inspect.isroutine(a)))
        attributes = sorted([a[1] for a in attributes if (not (a[0].startswith('__') and
                                                               a[0].endswith('__')))])
        return attributes


tile_images = {"wall": load_image("box.png"),
               "empty": load_image("grass.png")}
player_image = load_image('player.png', -1)
rat_image = load_image("mouse.png", -1)
rat_image = pygame.transform.scale(rat_image, (50, 50))
plant_image = load_image("plant.png", -1)
plant_image = pygame.transform.scale(plant_image, (50, 50))
tile_width = tile_height = 50


def real_coords(coord, x=False, y=False):
    if x and y:
        return coord * tile_width, coord * tile_height
    else:
        if x:
            return coord * tile_width
        if y:
            return coord * tile_height


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(tiles_group, all_sprites)
        self.type = tile_type
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(pos_x * tile_width, pos_y * tile_height)


pl.hp = 3


class MovingEnemy(main.AnimatedSprite):
    def __init__(self, x, y, damage, speed, points, spritesheet):
        super().__init__(spritesheet, x * tile_width, y * tile_height, enemy_group)
        self.damage = damage
        self.points = points
        self.next_point = points[0]
        self.speed = speed
        self.all_states = [[]]
        self.generate_states()
        self.state = deepcopy(self.all_states[0])
        self.state_number = 0
        self.point_number = 0
        self.last_time = time.time()
        self.side_point = 1
        self.side_state = 1

    def generate_states(self):
        for i in range(1, len(self.points)):
            if self.points[i][0] != self.points[i - 1][0]:
                difference = self.points[i][0] - self.points[i - 1][0]
                self.all_states.append([SpriteStates.MOVING, [difference // abs(difference), 0]])
            else:
                difference = self.points[i][1] - self.points[i - 1][1]
                self.all_states.append([SpriteStates.JUMPING, [0, difference // abs(difference)]])
        self.all_states[0] = self.all_states[1]

    def change_state(self, direction=False):
        self.state_number += self.side_state
        if self.state_number == len(self.all_states) or self.state_number <= 0:
            self.side_state *= -1
            self.state_number += self.side_state
        self.state = deepcopy(self.all_states[self.state_number])
        if self.side_state < 0 and self.state_number:
            self.state[1][0] *= -1
            self.state[1][1] *= -1
        if self.state[0] == SpriteStates.MOVING:
            if self.state[1] == [1, 0]:
                direction = True
            elif self.state[1] == [-1, 0]:
                direction = False
        else:
            direction = True
        self.set_status(self.state[0], direction)

    def change_point(self):
        self.point_number += self.side_point
        if self.point_number == len(self.points) or self.point_number < 0:
            self.side_point *= -1
            self.point_number += 2 * self.side_point
        self.next_point = self.points[self.point_number]

    def check_state(self):
        if self.state[0] == SpriteStates.MOVING:
            if self.state[1][0] > 0:
                if self.rect.x >= real_coords(self.next_point[0], x=True):
                    self.change_point()
                    self.change_state()
            elif self.state[1][0] < 0:
                if self.rect.x <= real_coords(self.next_point[0], x=True):
                    self.change_point()
                    self.change_state()
        elif self.state[0] == SpriteStates.JUMPING:
            if self.state[1][1] < 0:
                if self.rect.y <= real_coords(self.next_point[1], y=True):
                    self.change_point()
                    self.change_state()
            elif self.state[1][1] > 0:
                if self.rect.y >= real_coords(self.next_point[1], y=True):
                    self.change_point()
                    self.change_state()

    def update(self):
        self.rect.x += int(self.state[1][0] * self.speed)
        self.rect.y += int(self.state[1][1] * self.speed)
        self.image.get_rect().move(self.rect.x, self.rect.y)
        collisions = pygame.sprite.spritecollideany(self, player_group)
        if collisions:
            if time.time() - self.last_time > 1.5:
                self.last_time = time.time()
                collisions.hp -= 1
        self.check_state()
        super().update()


class StaticEnemies(main.AnimatedSprite):
    def __init__(self, x, y, damage, spritesheet):
        super().__init__(spritesheet, x * tile_width, y * tile_height, enemy_group)
        self.damage = damage


class ShootingEnemy(StaticEnemies):
    def __init__(self, x, y, damage, spritesheet, bullet_image, all_sides=None):
        super().__init__(x, y, damage, spritesheet)
        if all_sides is None:
            all_sides = [EAST, SE, SOUTH, SW, WEST, NW, NORTH, NE]
        self.bullet_image = bullet_image
        self.all_sides = all_sides
        self.last_time = 0
        self.last_hit_time = 0
        self.last_shoot_time = 0

    def update(self):
        if time.time() - self.last_shoot_time > 1.5:
            self.last_shoot_time = time.time()
            for i in self.all_sides:
                Bullet(self.rect.x, self.rect.y, self.bullet_image,
                       2, 1, SHOOTING_SIDES[i])
        collisions = pygame.sprite.spritecollideany(self, player_group)
        if collisions:
            if time.time() - self.last_hit_time > 1.5:
                self.last_hit_time = time.time()
                collisions.hp -= 1
        super().update()


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, image, speed, damage, sides, is_friendly=False):
        super().__init__(all_sprites, bullet_group)
        self.damage = damage
        self.image = image
        self.rect = self.image.get_rect().move(x, y)
        self.side_x = sides[0]
        self.side_y = sides[1]
        self.speed = speed
        self.last_time = 0
        self.is_friendly = is_friendly

    def update(self):
        self.rect.x += int(self.side_x * self.speed)
        self.rect.y += int(self.side_y * self.speed)
        self.image.get_rect().move(self.rect.x, self.rect.y)
        if not self.is_friendly:
            collides = pygame.sprite.spritecollideany(self, player_group)
            if collides:
                # Анимация взрыва
                # Анимация неуязвимости
                collides.hp -= self.damage
                self.kill()
        else:
            collides = pygame.sprite.spritecollide(self, enemy_group, False)
            for collide in collides:
                # Анимация взрыва
                collide.hp -= self.damage
                self.kill()
        collides = pygame.sprite.spritecollide(self, tiles_group, False)
        for collide in collides:
            if collide.type == "wall":
                # Анимация взрыва
                self.kill()


def move_player(player_moved, move_type, last_x, last_y):
    if move_type == 1:
        player_moved.rect.x -= STEP
    elif move_type == 2:
        player_moved.rect.x += STEP
    elif move_type == 3:
        player_moved.rect.y -= STEP
    elif move_type == 4:
        player_moved.rect.y += STEP
    if pygame.sprite.spritecollide(player_moved, tiles_group, False)[0].type == "wall":
        player_moved.rect = player_moved.image.get_rect().move(last_x, last_y)


def terminate():
    pygame.quit()
    sys.exit()


def start_screen():
    text = ["Приветствую", "", "Правила игры",
            "Если в правилах несколько строк,", "приходится выводить их построчно"]
    bg = pygame.transform.scale(load_image("fon.jpg"), (WIDTH, HEIGHT))
    screen.blit(bg, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 100
    for line in text:
        string_render = font.render(line, True, pygame.Color("black"))
        string_rect = string_render.get_rect()
        text_coord += 10
        string_rect.top = text_coord
        string_rect.x = 10
        text_coord += string_rect.height
        screen.blit(string_render, string_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                return
        pygame.display.flip()
        clock.tick(FPS)


def load_level(filename):
    filename = '../data/levels/' + filename
    with open(filename, "r") as map_file:
        level_map = [line.strip() for line in map_file]
        max_width = max(map(len, level_map))
    return list(map(lambda line: line.ljust(max_width, "."), level_map))


def generate_level(level):
    new_player, x, y = None, None, None
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == ".":
                Tile("empty", x, y)
            elif level[y][x] == "#":
                Tile("wall", x, y)
            if level[y][x] == "@":
                Tile("empty", x, y)
                new_player = pl.Player(x, y)
            if level[y][x] == "R":
                Tile("empty", x, y)
                MovingEnemy(x, y, 1, 1, [[x, y], [6, 10], [6, 9], [7, 9], [7, 8], [8, 8],
                                         [8, 3], [2, 3], [2, 4], [3, 4], [3, 9]],
                            "spritesheet1.png")
            if level[y][x] == "T":
                Tile("empty", x, y)
                ShootingEnemy(x, y, 1, "spritesheet1.png", plant_image, SHOOT_AROUND)
    return new_player, x, y


player, level_x, level_y = generate_level(load_level("level1.txt"))


start_screen()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                move_player(player, 1, player.rect.x, player.rect.y)
            elif event.key == pygame.K_RIGHT:
                move_player(player, 2, player.rect.x, player.rect.y)
            elif event.key == pygame.K_UP:
                move_player(player, 3, player.rect.x, player.rect.y)
            elif event.key == pygame.K_DOWN:
                move_player(player, 4, player.rect.x, player.rect.y)
    screen.fill(pygame.Color('black'))
    player_group.update()
    enemy_group.update()
    bullet_group.update()
    tiles_group.draw(screen)
    player_group.draw(screen)
    bullet_group.draw(screen)
    enemy_group.draw(screen)
    pygame.display.flip()
    clock.tick(FPS)
terminate()
