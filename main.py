
import pygame
import os
import time

pygame.init()
pygame.mixer.init()

# Get display information
info = pygame.display.Info()
DISPLAY_WIDTH = info.current_w
# Screen settings
WIDTH = DISPLAY_WIDTH
HEIGHT = DISPLAY_WIDTH / 2  # Fixed Height
TILE_SIZE = WIDTH / 128  # Dynamic Tile Size, adjust 128 to change base resolution
SCALE_FACTOR = WIDTH / 1024  # Scale relative to a base resolution of 1024 width
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("I WANNA BE A PVL")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)

# Music files
BACKGROUND_MUSIC_LEVEL0 = "background-song.mp3"
BACKGROUND_MUSIC_OTHER = "back-background-song.mp3"
DEATH_MUSIC = "death_mus.mp3"
FAKE_ERROR_MUSIC = "Fake Error.mp3"  # Add the fake error sound

# Load the background music
try:
    pygame.mixer.music.load(BACKGROUND_MUSIC_LEVEL0)
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)
except pygame.error as e:
    print(f"Error loading music: {e}")
    raise SystemExit()

# Function to play music
def play_music(music_file, loop=-1):
    try:
        pygame.mixer.music.load(music_file)
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(loop)
    except pygame.error as e:
        print(f"Error loading music: {e}")

# Function to play a sound effect
def play_sound(sound_file):
    try:
        sound = pygame.mixer.Sound(sound_file)
        sound.set_volume(0.5)  # Adjust volume if needed
        sound.play()
    except pygame.error as e:
        print(f"Error loading sound effect: {e}")

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
            print("Unable to load spritesheet image:", filename)
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
        return [self.image_at(rects, colorkey) for rects in rects]

# Load spritesheet
spritesheet = SpriteSheet("qubic.png")

# Player Sprite Rects, scale the default sprite size
sprite_width, sprite_height = int(14 * SCALE_FACTOR), int(17 * SCALE_FACTOR)
sprite_rects = [
    (4, 3, 14, 17),  # 0 - standing
    (18, 3, 14, 17),  # 1 - walk 1
    (32, 3, 14, 17),  # 2 - walk 2
    (46, 3, 14, 17),  # 3 - walk 3
    (16, 22, 16, 13),  # 4 - death
]
sprites = [pygame.transform.scale(
    spritesheet.image_at(rect, colorkey=(255, 255, 255)), (sprite_width, sprite_height)) for rect in sprite_rects]

# Tile images
tile_images = {
    "t": pygame.transform.scale(pygame.image.load("grass-top.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    "g": pygame.transform.scale(pygame.image.load("grass-under.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    "s": pygame.transform.scale(pygame.image.load("spike1.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    "d": pygame.transform.scale(pygame.image.load("spike2.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    "f": pygame.transform.scale(pygame.image.load("spike3.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    "e": pygame.transform.scale(pygame.image.load("spike4.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    "w": pygame.transform.scale(pygame.image.load("cuboc.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    "p": pygame.transform.scale(pygame.image.load("grass-top.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    ".": None,
}

# Load cursor image
try:
    cursor_image = pygame.image.load("cursor.png").convert_alpha()
    # Optionally scale the cursor image if it's too big or small
    cursor_size = int(20 * SCALE_FACTOR)  # Scale cursor size
    cursor_image = pygame.transform.scale(cursor_image, (12, 19))  # Keep aspect ratio
    cursor_rect = cursor_image.get_rect()
except pygame.error as e:
    print(f"Error loading cursor image: {e}")
    cursor_image = pygame.Surface((10, 10))  # Default black square
    cursor_image.fill(BLACK)
    cursor_rect = cursor_image.get_rect()

def load_level(filename):
    try:
        with open(filename, "r") as file:
            return [row.strip() for row in file]
    except FileNotFoundError:
        print(f"Error: Level file '{filename}' not found.")
        pygame.quit()
        exit()

def parse_platform_data(line):
    parts = line.split(":")
    if len(parts) != 8:
        print("Invalid platform data format.")
        return None
    try:
        x_start, y_start = int(parts[0]), int(parts[1])
        width = int(parts[2])
        x_end, y_end = int(parts[3]), int(parts[4])
        time_to_target, wait_time, time_to_start = float(parts[5]), float(parts[6]), float(parts[7])
        return {
            "x_start": x_start,
            "y_start": y_start,
            "width": width,
            "x_end": x_end,
            "y_end": y_end,
            "time_to_target": time_to_target,
            "wait_time": wait_time,
            "time_to_start": time_to_start,
        }
    except ValueError:
        print("Error converting platform data to numbers.")
        return None

level_data = load_level("level" + level_index + ".txt")
LEVEL_WIDTH, LEVEL_HEIGHT = len(level_data[0]), len(level_data)

# Player settings, dynamic starting pos to scale
player_x, player_y = 50 * SCALE_FACTOR, 200 * SCALE_FACTOR
player_speed = 5 * SCALE_FACTOR
player_frame = 0
movement_direction = None
is_jumping = True
y_velocity = 0
gravity = 1 * SCALE_FACTOR
facing_right = True
is_dead = False
is_on_ground = False
death_animation_delay = 0
right_frames = [0, 1, 2, 3]

# Mouse inactivity variables
mouse_inactivity_timer = 0
MOUSE_INACTIVITY_THRESHOLD = 3  # seconds
cursor_speed = 2 * SCALE_FACTOR
angry_cursor_x, angry_cursor_y = pygame.mouse.get_pos()  # Starting position for the cursor
cursor_attached = True  # Initially, the cursor is attached
last_mouse_pos = pygame.mouse.get_pos()

tprev = 0  # Initialize tprev here

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
        collisions = pygame.sprite.spritecollide(self, everything, False)
        for other in collisions:
            if other.tile_type in ["t", "g", "p"]:
                if dx > 0:
                    self.rect.right = other.rect.left
                    dx = 0
                elif dx < 0:
                    self.rect.left = other.rect.right
                    dx = 0

        # Y-axis movement
        self.rect.y += dy
        collisions = pygame.sprite.spritecollide(self, everything, False)
        for other in collisions:
            if other.tile_type in ["t", "g", "p"]:
                if dy > 0:
                    self.rect.bottom = other.rect.top
                    is_on_ground = True
                    is_jumping = False
                    y_velocity = 0
                    # Attach to platform
                    if isinstance(other, MovingPlatform):
                        self.platform = other
                elif dy < 0:
                    self.rect.top = other.rect.bottom
                    y_velocity = 0
                dy = 0
        return dx, dy

# Moving Platform Class
class MovingPlatform(GameObject):
    def __init__(self, platform_data):
        # Конвертируем координаты из тайлов в пиксели
        self.x_start = platform_data["x_start"] * TILE_SIZE
        self.y_start = platform_data["y_start"] * TILE_SIZE
        self.width_tiles = platform_data["width"]
        self.x_end = platform_data["x_end"] * TILE_SIZE
        self.y_end = platform_data["y_end"] * TILE_SIZE
        self.time_to_target = platform_data["time_to_target"]
        self.wait_time = platform_data["wait_time"]
        self.time_to_start = platform_data["time_to_start"]

        # Рассчитываем ширину платформы в пикселях
        platform_width = self.width_tiles * TILE_SIZE

        # Инициализируем платформу с изображением "t" (верхняя часть травы)
        super().__init__(self.x_start, self.y_start, tile_images["t"], "p")
        self.image = pygame.transform.scale(self.image, (platform_width, TILE_SIZE))
        self.rect = self.image.get_rect(topleft=(self.x_start, self.y_start))

        # Начальные параметры движения
        self.current_x = self.x_start
        self.current_y = self.y_start - TILE_SIZE
        self.target_x = self.x_end
        self.target_y = self.y_end
        self.speed_x = (self.target_x - self.x_start) / self.time_to_target if self.time_to_target else 0
        self.speed_y = (self.target_y - self.y_start) / self.time_to_target if self.time_to_start else 0
        self.state = "waiting at start"
        self.timer = 0
        self.is_reset = True
        self.dx = 0  # Смещение по X
        self.dy = 0  # Смещение по Y

    def update(self, dt, everything, player):
        self.dx, self.dy = 0, 0
        if self.is_reset:
            self.current_x = self.x_start
            self.current_y = self.y_start - 10
            self.timer = 0
            self.state = "waiting_at_start"
            self.is_reset = False

        if self.state == "moving_to_target":
            prev_x = self.current_x
            prev_y = self.current_y

            self.current_x += self.speed_x * dt
            self.current_y += self.speed_y * dt

            # Проверяем, достигли ли мы целевой точки
            if (self.speed_x > 0 and self.current_x >= self.target_x) or (
                    self.speed_x < 0 and self.current_x <= self.target_x):
                self.current_x = self.target_x
                self.state = "waiting_at_target"
                self.timer = 0

            if (self.speed_y > 0 and self.current_y >= self.target_y) or (
                    self.speed_y < 0 and self.current_y <= self.target_y):
                self.current_y = self.target_y
                self.state = "waiting_at_target"
                self.timer = 0

            # Обновляем положение платформы
            self.dx = self.current_x - prev_x
            self.dy = self.current_y - prev_y
            self.rect.x = self.current_x
            self.rect.y = self.current_y

        elif self.state == "waiting_at_target":
            self.timer += dt
            if self.timer >= self.wait_time:
                self.state = "moving_to_start"
                self.speed_x = (self.x_start - self.target_x) / self.time_to_start if self.time_to_start else 0
                self.speed_y = (self.y_start - self.target_y) / self.time_to_start if self.time_to_start else 0
                self.timer = 0

        elif self.state == "moving_to_start":
            prev_x = self.current_x
            prev_y = self.current_y

            self.current_x += self.speed_x * dt
            self.current_y += self.speed_y * dt

            # Проверяем, достигли ли мы начальной точки
            if (self.speed_x > 0 and self.current_x >= self.x_start) or (
                    self.speed_x < 0 and self.current_x <= self.x_start):
                self.current_x = self.x_start
                self.state = "waiting_at_start"
                self.timer = 0

            if (self.speed_y > 0 and self.current_y >= self.y_start) or (
                    self.speed_y < 0 and self.current_y <= self.y_start):
                self.current_y = self.y_start
                self.state = "waiting_at_start"
                self.timer = 0

            # Обновляем положение платформы
            self.dx = self.current_x - prev_x
            self.dy = self.current_y - prev_y
            self.rect.x = self.current_x
            self.rect.y = self.current_y

        elif self.state == "waiting_at_start":
            self.timer += dt
            if self.timer >= self.wait_time:
                self.state = "moving_to_target"
                self.speed_x = (self.target_x - self.x_start) / self.time_to_target if self.time_to_target else 0
                self.speed_y = (self.target_y - self.y_start) / self.time_to_target if self.time_to_start else 0
                self.timer = 0

        # Обновляем положение платформы
        self.rect.x = self.current_x
        self.rect.y = self.current_y

# Create objects
everything = pygame.sprite.Group()
spikes = pygame.sprite.Group()
cup = pygame.sprite.Group()
platforms = pygame.sprite.Group()
tiles = []

moving_platform_data = []  # Данные платформ хранятся здесь
for row_index, row in enumerate(level_data):
    if row.startswith("//"):
        platform_data = parse_platform_data(row[2:])
        if platform_data:
            moving_platform_data.append(platform_data)

# Создаем платформы
moving_platforms = []
for platform_data in moving_platform_data:
    platform = MovingPlatform(platform_data)
    moving_platforms.append(platform)
    everything.add(platform)
    platforms.add(platform)

player_start_x, player_start_y = None, None
for row_index, row in enumerate(level_data):
    for col_index, tile in enumerate(row):
        if tile == "t":
            if col_index == 0:  # Lower row takes precedence
                player_start_y = row_index
                player_start_x = 0

if player_start_x is None or player_start_y is None:
    print("Error: No 't' tile found in the level data.  Spawning at 0,0")
    player_start_x = 0
    player_start_y = 0

player_x = player_start_x * TILE_SIZE
player_y = player_start_y * TILE_SIZE - sprites[0].get_height()

for row_index, row in enumerate(level_data):
    for col_index, tile in enumerate(row):
        tile_image = tile_images.get(tile)
        if tile_image:
            tile_obj = GameObject(col_index * TILE_SIZE, row_index * TILE_SIZE, tile_image, tile)
            everything.add(tile_obj)
            tiles.append(tile_obj)
            if tile in ["s", "d", "f", "e"]:
                spikes.add(tile_obj)
            if tile == "w":
                cup.add(tile_obj)

player = GameObject(player_x, player_y, sprites[0])
player.platform = None  # Initially not on a platform
everything.add(player)

# Function to respawn the player
def respawn_player():
    global player_x, player_y, y_velocity, is_jumping, is_on_ground, player_frame, movement_direction, death_animation_delay, is_dead, cursor_attached

    # Останавливаем музыку и играем музыку смерти
    play_music(DEATH_MUSIC, 0)

    # Сбрасываем позицию игрока
    global player_start_x, player_start_y
    player_start_x, player_start_y = None, None
    for row_index, row in enumerate(level_data):
        for col_index, tile in enumerate(row):
            if tile == "t":
                if col_index == 0:  # Lower row takes precedence
                    player_start_y = row_index
                    player_start_x = 0
    if player_start_x is None or player_start_y is None:
        print("Error: No 't' tile found in the level data.  Spawning at 0,0")
        player_start_x = 0
        player_start_y = 0

    new_x = player_start_x * TILE_SIZE
    new_y = player_start_y * TILE_SIZE - sprites[0].get_height()
    player.rect.topleft = (new_x, new_y)

    # Сбрасываем физику и состояние игрока
    y_velocity = 0
    is_jumping = False
    is_on_ground = False
    player_frame = 0
    movement_direction = None
    death_animation_delay = 0
    cursor_attached = True
    player.platform = None

    # Убеждаемся, что игрок приземлился на землю после возрождения
    player.move(0, 1, everything)
    pygame.time.delay(2000)

    is_dead = False
    if level_index == "0":
        play_music(BACKGROUND_MUSIC_LEVEL0)
    else:
        play_music(BACKGROUND_MUSIC_OTHER)

    # Сбрасываем позицию курсора
    global angry_cursor_x, angry_cursor_y
    angry_cursor_x, angry_cursor_y = pygame.mouse.get_pos()

    # Сбрасываем позиции платформ
    for platform in moving_platforms:
        platform.is_reset = True

def show_level_complete_screen(time_taken):
    font = pygame.font.Font(None, 50)  # Выберите подходящий шрифт и размер
    text = font.render(f"Time: {time_taken:.2f} seconds", True, BLACK)
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, text_rect)

    pygame.display.flip()
    pygame.time.delay(4000)

# Function to load the next level
def load_next_level():
    global level_index, level_data, current_level, everything, spikes, cup, tiles, moving_platforms, platforms, player_start_x, player_start_y

    # Increment level index
    level_index = str(int(level_index) + 1)

    # Save progress
    save_game_progress(level_index)

    # Stop music and play next level's music
    pygame.mixer.music.stop()
    play_music(BACKGROUND_MUSIC_OTHER)

    # Load next level data
    current_level = "level" + level_index + ".txt"
    level_data = load_level(current_level)

    # Clear existing game objects
    everything.empty()
    spikes.empty()
    cup.empty()
    tiles.clear()
    platforms.empty()
    moving_platforms = []  # Clear old platforms

    # Load Platform Data
    moving_platform_data = []  # Moving Platforms stored here
    for row_index, row in enumerate(level_data):
        if row.startswith("//"):
            platform_data = parse_platform_data(row[2:])
            if platform_data:
                moving_platform_data.append(platform_data)

    # Create game objects for the new level
    for row_index, row in enumerate(level_data):
        for col_index, tile in enumerate(row):
            tile_image = tile_images.get(tile)
            if tile_image:
                tile_obj = GameObject(col_index * TILE_SIZE, row_index * TILE_SIZE, tile_image, tile)
                everything.add(tile_obj)
                tiles.append(tile_obj)
                if tile in ["s", "d", "f", "e"]:
                    spikes.add(tile_obj)
                if tile == "w":
                    cup.add(tile_obj)

    # Create moving platforms
    for platform_data in moving_platform_data:
        platform = MovingPlatform(platform_data)
        moving_platforms.append(platform)
        everything.add(platform)
        platforms.add(platform)

    # Find starting position
    player_start_x, player_start_y = None, None
    for row_index, row in enumerate(level_data):
        for col_index, tile in enumerate(row):
            if tile == "t":
                if player_start_y is None or row_index > player_start_y:  # Lower row takes precedence
                    player_start_y = row_index
                    player_start_x = col_index
                elif row_index == player_start_y and col_index < player_start_x:  # If on same row, leftmost takes precedence
                    player_start_x = col_index

    if player_start_x is None or player_start_y is None:
        print("Error: No 't' tile found in the level data. Spawning at 0,0")
        player_start_x = 0
        player_start_y = 0

    player_x = player_start_x * TILE_SIZE
    player_y = player_start_y * TILE_SIZE - sprites[0].get_height()

    # Reset player
    player.rect.x = player_x
    player.rect.y = player_y
    player.platform = None
    everything.add(player)

    return True

# Initialize music based on the current level
if level_index == "0":
    play_music(BACKGROUND_MUSIC_LEVEL0)
else:
    play_music(BACKGROUND_MUSIC_OTHER)

# Main loop
running = True
clock = pygame.time.Clock()
current_sprite_index = 0
dt = 0


typed_code = []

# Disable system cursor
pygame.mouse.set_visible(False)

# Обновляем движущиеся платформы
for platform in moving_platforms:
    platform.update(dt, everything, player)
start_time = time.time()

while running:
    dt = clock.tick(60) / 1000  # Get the time delta in seconds
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            play_sound(FAKE_ERROR_MUSIC)  # Play the fake error sound
            pygame.time.delay(2000)  # Let the sound play for a bit
            running = False

        # Update the mouse timer
        if event.type == pygame.MOUSEMOTION:
            mouse_inactivity_timer = 0
            angry_cursor_x, angry_cursor_y = event.pos  # Follow mouse movement
            cursor_attached = True  # Re-attach when moving

        if not is_dead:
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_d, pygame.K_RIGHT] and level_index != "0":
                    movement_direction = "right"
                if event.key in [pygame.K_a, pygame.K_LEFT] and level_index != "0":
                    movement_direction = "left"
                if event.key in [pygame.K_SPACE] and is_on_ground and level_index == "0":
                    pygame.mixer.music.stop()
                    load_next_level()
                    if not level_data:
                        play_sound(FAKE_ERROR_MUSIC)  # Play the fake error sound
                        pygame.time.delay(2000)  # Let the sound play for a bit
                        running = False  # No more levels, quit the game
                    level_index = str(load_game_progress())
                    if level_index == "0":
                        play_music(BACKGROUND_MUSIC_LEVEL0)
                    else:
                        play_music(BACKGROUND_MUSIC_OTHER)
                elif event.key in [pygame.K_UP, pygame.K_w] and is_on_ground:
                    is_jumping = True
                    y_velocity = -15 * SCALE_FACTOR
                    is_on_ground = False
                    if player.platform:  # Detach from platform on jump
                        player.platform = None

            if event.type == pygame.KEYUP:
                if event.key in [pygame.K_d, pygame.K_RIGHT] and movement_direction == "right" and level_index != "0":
                    movement_direction = None
                if event.key in [pygame.K_a, pygame.K_LEFT] and movement_direction == "left" and level_index != "0":
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

        # Move the player
        original_dx = dx  # Store original dx
        dx, dy = player.move(dx, dy, everything)

        # Check if the player is on the platform and adjust horizontal movement
        if player.platform:
            player.rect.x += player.platform.dx
            player.rect.y += player.platform.dy
            is_on_ground = True

            # If trying to move against the platform, reset the movement
            if (original_dx > 0 and player.platform.dx < 0) or (original_dx < 0 and player.platform.dx > 0):
                dx = 0  # Reset horizontal movement

    # Limit player movement within screen bounds
    if player.rect.right > WIDTH:
        player.rect.right = WIDTH
    if player.rect.left < 0:
        player.rect.left = 0

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
        end_time = time.time()  # Записываем время завершения уровня
        time_taken = end_time - start_time  # Вычисляем время прохождения
        show_level_complete_screen(time_taken)
        load_next_level()
        start_time = time.time()
        if not level_data:
            play_sound(FAKE_ERROR_MUSIC)  # Play the fake error sound
            pygame.time.delay(2000)  # Let the sound play for a bit
            running = False  # No more levels, quit the game
        level_index = str(load_game_progress())
        if level_index == "0":
            play_music(BACKGROUND_MUSIC_LEVEL0)
        else:
            play_music(BACKGROUND_MUSIC_OTHER)
        play_sound(FAKE_ERROR_MUSIC)  # Play the fake error sound
        pygame.time.delay(2000)  # Let the sound play for a bit

        running = False

    # Death animation
    if is_dead:
        death_animation_delay += 1
        if death_animation_delay > 30:  # Wait for 30 frames before respawning
            respawn_player()
            start_time = time.time()
            is_dead = False
            is_jumping = True
            is_on_ground = False

    # Angry Cursor Logic
    mouse_inactivity_timer += clock.get_time() / 1000  # Accumulate seconds

    if mouse_inactivity_timer >= MOUSE_INACTIVITY_THRESHOLD:
        cursor_attached = False  # Detach after inactivity
        player_center_x = player.rect.centerx
        player_center_y = player.rect.centery

        # Calculate direction towards the player
        dir_x = player_center_x - angry_cursor_x
        dir_y = player_center_y - angry_cursor_y
        distance = (dir_x**2 + dir_y**2) ** 0.5

        # Normalize direction
        if distance > 0:
            dir_x /= distance
            dir_y /= distance

            # Move the cursor towards the player
            angry_cursor_x += dir_x * cursor_speed
            angry_cursor_y += dir_y * cursor_speed

        # Check for cursor-player collision using rectangles
        cursor_rect.center = (int(angry_cursor_x), int(angry_cursor_y))  # Update cursor rect position
        if player.rect.colliderect(cursor_rect):  # Use default sprite rectangle
            is_dead = True
            current_sprite_index = 4
            movement_direction = None
            y_velocity = 0
            is_jumping = False
    else:
        if cursor_attached:
            angry_cursor_x, angry_cursor_y = pygame.mouse.get_pos()  # Update cursor position

    # Update moving platforms
    for platform in moving_platforms:
        platform.update(dt, everything, player)
    for platform in moving_platforms:
        screen.blit(platform.image, platform.rect)
    # Rendering
    screen.fill(WHITE)
    for tile in tiles:
        screen.blit(tile.image, (tile.rect.x, tile.rect.y))
    for platform in moving_platforms:
        screen.blit(platform.image, platform.rect)
    current_sprite = sprites[current_sprite_index]
    if facing_right or is_dead:
        if level_index == "12":
            image = pygame.transform.scale(pygame.image.load("END_SCREEN.png").convert(), (WIDTH, HEIGHT))
            screen.blit(image, (0, 0))
        else:
            screen.blit(current_sprite, (player.rect.x, player.rect.y))
    else:
        flipped = pygame.transform.flip(current_sprite, True, False)
        screen.blit(flipped, (player.rect.x, player.rect.y))
    if level_index == "0":
        image = pygame.transform.scale(pygame.image.load("TITLE SCREEN.png").convert(), (WIDTH, HEIGHT))
        screen.blit(image, (0, 0))
        MOUSE_INACTIVITY_THRESHOLD = 3.1556926 * (10**113)
    if level_index == "12":
        image = pygame.transform.scale(pygame.image.load("END_SCREEN.png").convert(), (WIDTH, HEIGHT))
        screen.blit(image, (0, 0))
        MOUSE_INACTIVITY_THRESHOLD = 3.1556926 * (10 ** 113)
    # Draw the angry cursor
    cursor_rect.center = (int(angry_cursor_x), int(angry_cursor_y))  # Update center for drawing
    screen.blit(cursor_image, cursor_rect)

    pygame.display.flip()

pygame.quit()

