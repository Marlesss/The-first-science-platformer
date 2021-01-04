import pygame, os, sys, time
from source_py.main import SpriteStates, AnimatedSprite

# Добавить константы стандартного ускорения, скорости, гравитации персонажа
# Протестировать и посмотреть, чтобы динамика игры соответствовала этим скоростям
# Добавить прыжки, отскоки от стен, подогнать их под (пока не существующую) систему анимаций

# На удаление
# {
pygame.init()
SIZE = WIDTH, HEIGHT = 800, 600
FPS = 60

screen = pygame.display.set_mode(SIZE)
clock = pygame.time.Clock()
# На удаление
# }


# На удаление
# {
level_map = ['............................',
             '............................',
             '#....#................#....#',
             '#....#................#....#',
             '#....#................#....#',
             '#....#................#....#',
             '#....#................#....#',
             '#....#................#....#',
             '#..........................#',
             '#..........................#',
             '.###...................###.',
             '........##........##........',
             '#..........................#',
             '#.............@............#',
             '############################']


# На удаление
# }

# На удаление
# {
def load_image(name, colorkey=None):
    # jpg, png, gif без анимации, bmp, pcx, tga, tif, lbm, pbm, xpm
    fullname = os.path.join("..\data", "images", name)  # получение полного пути к файлу
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


# На удаление
# }

# На удаление
# {
tiles = {'wall': load_image("box.png"), 'empty': load_image("grass.png")}
player_spritesheet = "spritesheet1.png"
tile_width, tile_height = 25, 40

all_sprites = pygame.sprite.Group()
tile_sprites = pygame.sprite.Group()
player_sprites = pygame.sprite.Group()


# На удаление
# }


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, x, y):
        super().__init__(tile_sprites, all_sprites)
        self.type = tile_type
        self.image = pygame.transform.scale(tiles[tile_type], (tile_width, tile_height))
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x * tile_width, y * tile_height


# Класс-синглтон для проверки наличия столкновения объекта (rect) с группой спрайтов
class Collision:
    @staticmethod
    def get_collision(rect, obj_list):
        collision_detected = list()
        for obj in obj_list:
            if rect.colliderect(obj.rect):
                collision_detected.append(obj)
        return collision_detected


class Unit(AnimatedSprite):
    LEFT = -1
    RIGHT = 1

    def __init__(self, spritesheet, x, y, *groups):
        super().__init__(spritesheet, x, y, *groups)

    def setup_movemet(self):
        pass

    def update_movement(self):
        pass

    def move(self):
        pass

    def update_status(self, is_sliding, in_air, cur_rotation, falling, moving):
        if is_sliding and in_air:
            super().set_status(SpriteStates.SLIDING, not cur_rotation == Unit.RIGHT)
        elif in_air:
            if falling:
                super().set_status(SpriteStates.FALLING, cur_rotation == Unit.RIGHT)
            else:
                super().set_status(SpriteStates.JUMPING, cur_rotation == Unit.RIGHT)
        elif moving:
            super().set_status(SpriteStates.MOVING, cur_rotation == Unit.RIGHT)
        else:
            super().set_status(SpriteStates.IDLE, cur_rotation == Unit.RIGHT)


class Player(Unit):
    def __init__(self, x, y):
        super().__init__(player_spritesheet, x * tile_width, y * tile_height, (player_sprites,))
        self.setup_movement()

    # Базовые параметры физики персонажа
    def setup_movement(self):
        self.speed = [0, 0]
        self.velocity = [3, 3]
        self.gravity = 0.3
        self.max_speed = [4, 16]
        self.max_speed_sliding = [4, 4]

        self.moving_left, self.moving_right = False, False
        self.sliding_left, self.sliding_right = False, False

        self.jump_count = 2
        self.cur_rotation = Unit.RIGHT

        self.is_sliding = False
        self.in_air = False
        self.has_extra_jump = False

        # Применение параметров ускорения для персонажа

    def update_movement(self):
        self.speed = [0, 0]
        # Применение горизонтального ускорения
        if self.moving_right:
            self.speed[0] += self.velocity[0]
        if self.moving_left:
            self.speed[0] -= self.velocity[0]

        # Применение вертикального ускорения, учет гравитации и нормализация вертикального ускорения
        self.speed[1] += self.velocity[1]
        self.velocity[1] += self.gravity
        self.velocity[1] = min(self.velocity[1], self.max_speed[1])

        # Дополнительная нормализация вертикальной скорости и ускорения в зависимости от того
        # Находится ли в данный момент персонаж в состоянии скольжения
        if self.is_sliding:
            self.speed[1] = min(self.speed[1], self.max_speed_sliding[1])
            self.velocity[1] = min(self.velocity[1], self.max_speed_sliding[1])
        else:
            self.speed[1] = min(self.speed[1], self.max_speed[1])

    # Функция перемещения персонажа - с учётом и компенсацией возможных столкновений по всем осям
    def move(self):
        collision = {"top": False, "right": False, "left": False, "bottom": False}

        # Перемещаем персонажа и проверяем столкновения по горизонтальной оси
        self.rect.x += int(self.speed[0])
        collided = Collision.get_collision(self.rect, tile_sprites)
        for obj in collided:
            if self.speed[0] > 0:
                self.rect.right = obj.rect.left
                collision["right"] = True
            else:
                self.rect.left = obj.rect.right
                collision["left"] = True

        # Перемещаем персонажа и проверяем столкновения по вертикальной оси
        self.rect.y += int(self.speed[1])
        collided = Collision.get_collision(self.rect, tile_sprites)
        for obj in collided:
            if self.speed[1] > 0:
                self.rect.bottom = obj.rect.top
                collision["bottom"] = True
            else:
                self.rect.top = obj.rect.bottom
                collision["top"] = True

        # При отстутствии столкновения по вертикальной оси и наличием минимального вертикального
        # Ускорения - считаем, что игрок находится в воздухе
        if not collision["bottom"] and self.velocity[1] > 1.75:
            self.in_air = True

        # При столкновении по вертикальной оси с полом
        # Обнуляем характеристики sliding
        # Обнуляем количество возможных прыжков
        # Обнуляем вертикальное ускорение
        if collision["bottom"]:
            self.in_air = False
            self.jump_count = 2
            self.velocity[1] = 0
            self.sliding_right = False
            self.sliding_left = False
            self.is_sliding = False

        # При столкновении со стеной слева и при отсутствии предшедствующего скольжения слева
        # Обнуляем количество допустимых прыжков, разрешаем дополнительный прыжок от стены
        # Устанавливаем параметры sliding
        elif collision["left"] and not self.sliding_left:
            self.jump_count = 0
            self.has_extra_jump = True
            self.sliding_left = True
            self.sliding_right = False
            self.is_sliding = True

        # При столкновении со стеной справа и при отсутствии предшедствующего скольжения справа
        # Обнуляем количество допустимых прыжков, разрешаем дополнительный прыжок от стены
        # Устанавливаем параметры sliding
        elif collision["right"] and not self.sliding_right:
            self.jump_count = 0
            self.has_extra_jump = True
            self.sliding_right = True
            self.sliding_left = False
            self.is_sliding = True

        # При отсутствии столкновений по горизонтальной оси, но предшедствующем скольжении
        # Отключаем возможность дополнительного прыжка от стены
        # Нормализируем вертикальное ускорение
        elif not collision["right"] and not collision["left"]:
            if self.is_sliding:
                self.is_sliding = False
                self.has_extra_jump = False
                self.velocity[1] = min(self.velocity[1], self.max_speed_sliding[1])

        # При столкновении с потолком - обнуляем вертикальное ускорение
        if collision["top"]:
            self.velocity[1] = 0

        self.update_status(self.is_sliding, self.in_air, self.cur_rotation,
                           self.velocity[1] > 0, self.moving_right ^ self.moving_left)

    # Обновление положения, статуса (в воздухе, процессе скольжения), персонажа
    # С учётом клавиатурного ввода
    def update(self, *args):
        if len(args) > 0:
            event = args[0]
            if event.type == pygame.KEYDOWN:
                # При перемещении влево или вправо - меняем текущее направление персонажа
                # Также начианем движение персонажа в соответствующую сторону
                if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    self.moving_right = True
                    self.cur_rotation = Unit.RIGHT
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    self.moving_left = True
                    self.cur_rotation = Unit.LEFT
                # При попытке прыжка - проверяем на наличие дополнительного прыжка (при скольжении)
                # Или при наличии второго прыжка (self.jump_count)
                elif event.key == pygame.K_UP or pygame.key == pygame.K_w:
                    if self.jump_count > 0 or self.has_extra_jump:
                        self.in_air = True
                        self.has_extra_jump = False
                        self.velocity[1] = -7.5
                        self.jump_count = max(self.jump_count - 1, 0)
            # При отпускании клавиши - останавливаем движение персонажа
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    self.moving_right = False
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    self.moving_left = False

    # Анимирование персонажа - ответственность базового
    # Класса - AnimatedSprite
    def animate(self):
        AnimatedSprite.update(self)


# На удаление
# {
def generate_level():
    new_player, x, y = None, None, None
    for y in range(len(level_map)):
        for x in range(len(level_map[y])):
            if level_map[y][x] == '#':
                Tile("wall", x, y)
            else:
                if level_map[y][x] == '@':
                    new_player = Player(x, y)

    return new_player, x, y


# На удаление
# }

# На удаление
# {
background = pygame.transform.scale(load_image("fon.jpg"), SIZE)
screen.blit(background, (0, 0))
p = generate_level()[0]

running = True
while running:
    p.update_movement()
    p.move()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
            p.update(event)

    p.animate()

    screen.fill(pygame.Color("black"))
    delay = clock.tick(FPS)
    screen.blit(background, (0, 0))
    tile_sprites.draw(screen)
    player_sprites.draw(screen)
    pygame.display.flip()

pygame.quit()
# На удаление
# }
