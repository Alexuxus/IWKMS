import pygame
import os

pygame.init()
pygame.display.init()

# Screen settings
WIDTH, HEIGHT = 1024, 512
TILE_SIZE = 8
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("I WANNA BE A PVL")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


# Load game progression
def load_game_progress():
    if not os.path.exists("game_progression.txt"):
        with open("game_progression.txt", "w") as file:
            file.write("0")
    with open("game_progression.txt", "r") as file:
        return int(file.read().strip())


def save_game_progress(level_index):
    with open("game_progression.txt", "w") as file:
        file.write(str(level_index))


level_index = str(load_game_progress())


class SpriteSheet:
    def __init__(self, filename):
        try:
            self.sheet = pygame.image.load(filename).convert_alpha()
        except pygame.error as message:
            print('Unable to load spritesheet image:', filename)
            raise SystemExit(message)

    def image_at(self, rectangle, colorkey=None):
        rect = pygame.Rect(rectangle)
        image = pygame.Surface(rect.size, pygame.SRCALPHA).convert_alpha()
        image.blit(self.sheet, (0, 0), rect)
        if colorkey is not None:
            if colorkey == -1:
                colorkey = image.get_at((0, 0))
            image.set_colorkey(colorkey, pygame.RLEACCEL)
        return image

    def images_at(self, rects, colorkey=None):
        return [self.image_at(rect, colorkey) for rect in rects]


# Load spritesheet
spritesheet = SpriteSheet("qubic.png")

# Player Sprite Rects
sprite_rects = [
    (4, 3, 14, 17),  # 0 - standing
    (18, 3, 14, 17),  # 1 - walk 1
    (32, 3, 14, 17),  # 2 - walk 2
    (46, 3, 14, 17),  # 3 - walk 3
    (16, 22, 17, 13)  # 4 - death
]
sprites = spritesheet.images_at(sprite_rects, colorkey=(255, 255, 255))

# Tile images
tile_images = {
    't': pygame.transform.scale(pygame.image.load("grass-top.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    'g': pygame.transform.scale(pygame.image.load("grass-under.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    's': pygame.transform.scale(pygame.image.load("spike1.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    'd': pygame.transform.scale(pygame.image.load("spike2.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    'f': pygame.transform.scale(pygame.image.load("spike3.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    'e': pygame.transform.scale(pygame.image.load("spike4.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    'w': pygame.transform.scale(pygame.image.load("cuboc.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    '.': None
}


def load_level(filename):
    try:
        with open(filename, 'r') as file:
            return [row.strip() for row in file]
    except FileNotFoundError:
        print(f"Error: Level file '{filename}' not found.")
        pygame.quit()
        exit()


level_data = load_level("level" + level_index + ".txt")
LEVEL_WIDTH, LEVEL_HEIGHT = len(level_data[0]), len(level_data)

# Player settings
player_x, player_y = 50, 200
player_speed = 5
player_frame = 0
movement_direction = None
is_jumping = True
y_velocity = 0
gravity = 1
facing_right = True
is_dead = False
is_on_ground = False
death_animation_delay = 0
right_frames = [0, 1, 2, 3]
tprev = 1000000
# Find starting position
for row_index, row in enumerate(level_data):
    if 't' in row and tprev > row_index * TILE_SIZE:
        player_start_y = row_index * TILE_SIZE
        tprev = player_start_y

else:
    player_start_y = 500
player_x = 0
player_y = player_start_y - sprites[0].get_height()


class GameObject(pygame.sprite.Sprite):
    def __init__(self, x, y, image=None, tile_type=None):
        super().__init__()
        self.image = image if image else pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.tile_type = tile_type

    def move(self, dx, dy, everything):
        global is_on_ground, y_velocity, is_dead
        # X-axis movement
        self.rect.x += dx
        for other in pygame.sprite.spritecollide(self, everything, False):
            if other.tile_type in ['t', 'g']:
                if dx > 0:
                    self.rect.right = other.rect.left
                elif dx < 0:
                    self.rect.left = other.rect.right
                dx = 0

        # Y-axis movement
        self.rect.y += dy
        for other in pygame.sprite.spritecollide(self, everything, False):
            if other.tile_type in ['t', 'g']:
                if dy > 0:
                    self.rect.bottom = other.rect.top
                    is_on_ground = True
                    is_jumping = False
                    y_velocity = 0
                elif dy < 0:
                    self.rect.top = other.rect.bottom
                    y_velocity = 0
                dy = 0


# Create objects
everything = pygame.sprite.Group()
spikes = pygame.sprite.Group()
cup = pygame.sprite.Group()
tiles = []
for row_index, row in enumerate(level_data):
    for col_index, tile in enumerate(row):
        tile_image = tile_images.get(tile)
        if tile_image:
            tile_obj = GameObject(col_index * TILE_SIZE, row_index * TILE_SIZE, tile_image, tile)
            everything.add(tile_obj)
            tiles.append(tile_obj)
            if tile in ['s', 'd', 'f', 'e']:
                spikes.add(tile_obj)
            if tile == 'w':
                cup.add(tile_obj)

player = GameObject(player_x, player_y, sprites[0])
everything.add(player)


# Function to respawn the player
def respawn_player():
    global player_x, player_y, y_velocity, is_jumping, is_on_ground, player_frame, movement_direction, death_animation_delay
    # Reset player position
    for row_index, row in enumerate(level_data):
        if 't' in row:
            player_start_y = row_index * TILE_SIZE
            break
    else:
        player_start_y = 500
    new_y = player_start_y - sprites[0].get_height()
    player.rect.topleft = (0, new_y)
    # Reset physics and state
    y_velocity = 0
    is_jumping = False
    is_on_ground = False
    player_frame = 0
    movement_direction = None
    death_animation_delay = 0
    # Ensure player lands on ground after respawn
    player.move(0, 1, everything)


# Main loop
running = True
clock = pygame.time.Clock()
current_sprite_index = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if not is_dead:
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_d, pygame.K_RIGHT]:
                    movement_direction = "right"
                if event.key in [pygame.K_a, pygame.K_LEFT]:
                    movement_direction = "left"
                if event.key in [pygame.K_w, pygame.K_UP] and is_on_ground:
                    is_jumping = True
                    y_velocity = -15
                    is_on_ground = False
            if event.type == pygame.KEYUP:
                if event.key in [pygame.K_d, pygame.K_RIGHT] and movement_direction == "right":
                    movement_direction = None
                if event.key in [pygame.K_a, pygame.K_LEFT] and movement_direction == "left":
                    movement_direction = None

    # Player movement
    dx, dy = 0, 0
    if not is_dead:
        if movement_direction == "right":
            dx += player_speed
            player_frame = (player_frame + 1) % (len(right_frames) * 2)
            current_sprite_index = right_frames[player_frame // 2]
            facing_right = True
        elif movement_direction == "left":
            dx -= player_speed
            player_frame = (player_frame + 1) % (len(right_frames) * 2)
            current_sprite_index = right_frames[player_frame // 2]
            facing_right = False
        else:
            current_sprite_index = 0

        # Jump and gravity
        if is_jumping:
            dy += y_velocity
            y_velocity += gravity
        elif not is_on_ground:
            dy += gravity

    # Limit player movement within screen bounds
    if player.rect.right + dx > WIDTH:
        dx = WIDTH - player.rect.right
    if player.rect.left + dx < 0:
        dx = -player.rect.left

    player.move(dx, dy, everything)

    # Spike collision check
    if not is_dead and pygame.sprite.spritecollideany(player, spikes):
        is_dead = True
        current_sprite_index = 4
        movement_direction = None
        y_velocity = 0
        is_jumping = False

    # Win condition (cup collision)
    if not is_dead and pygame.sprite.spritecollideany(player, cup):
        current_level = int(level_index)
        save_game_progress(current_level + 1)
        running = False
        pygame.quit()
        exit()

    # Death animation
    if is_dead:
        death_animation_delay += 1
        if death_animation_delay > 30:  # Wait for 30 frames before respawning
            respawn_player()
            is_dead = False
            is_jumping = True
            is_on_ground = False

    # Rendering
    screen.fill(WHITE)
    for tile in tiles:
        screen.blit(tile.image, tile.rect)

    current_sprite = sprites[current_sprite_index]
    if facing_right or is_dead:
        screen.blit(current_sprite, player.rect)
    else:
        flipped = pygame.transform.flip(current_sprite, True, False)
        screen.blit(flipped, player.rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
