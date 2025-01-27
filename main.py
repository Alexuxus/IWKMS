import pygame

pygame.init()
pygame.display.init()

# Screen settings
WIDTH, HEIGHT = 1024, 512
TILE_SIZE = 8  # Size of each tile in pixels
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("IWKMS")

# Colors
WHITE = (255, 255, 255)


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
    (4, 3, 14, 17),  # 0 - right stand
    (18, 3, 14, 17),  # 1 - right walk 1
    (32, 3, 14, 17),  # 2 - right walk 2
    (46, 3, 14, 17),  # 3 - right walk 3
    (16, 22, 17, 13)  # 4 - dead
]

# Extract Sprites
sprites = spritesheet.images_at(sprite_rects, colorkey=(255, 255, 255))

# Load Tile Images (Make sure these images are in the same directory)
tile_images = {
    't': pygame.transform.scale(pygame.image.load("grass-top.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    'g': pygame.transform.scale(pygame.image.load("grass-under.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    's': pygame.transform.scale(pygame.image.load("spike1.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    'd': pygame.transform.scale(pygame.image.load("spike2.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    'f': pygame.transform.scale(pygame.image.load("spike3.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    'e': pygame.transform.scale(pygame.image.load("spike4.png").convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    # Changed 'g' to 'e' to avoid conflict with grass
    '.': None  # empty tile
}


# Load Level
def load_level(filename):
    level_data = []
    with open(filename, 'r') as file:
        for row in file:
            level_data.append(row.strip())
    return level_data


level_data = load_level("level.txt")
LEVEL_WIDTH = len(level_data[0])
LEVEL_HEIGHT = len(level_data)

# Player settings
player_x = 50
player_y = 500
player_speed = 5
animation_speed = 1
player_frame = 0
movement_direction = None
is_jumping = False
y_velocity = 0
gravity = 1
facing_right = True
is_dead = False  # New death variable
dead_frame = 4  # New frame if player is dead
is_on_ground = False  # New variable

# Animation frames
right_frames = [0, 1, 2, 3]

# Find player starting position
for row_index, row in enumerate(level_data):
    if 't' in row:
        player_start_y = row_index * TILE_SIZE
        break
    else:
        player_start_y = 500

# Set player pos
player_x = 0
player_y = player_start_y - sprites[0].get_height()


# Collision Detection Function
def check_collision(player_rect, level_data):
    player_x, player_y = player_rect.x, player_rect.y
    player_width, player_height = player_rect.width, player_rect.height

    # Calculate the tiles the player is touching
    left_tile_x = int(player_x // TILE_SIZE)
    right_tile_x = int((player_x + player_width) // TILE_SIZE)
    top_tile_y = int(player_y // TILE_SIZE)
    bottom_tile_y = int((player_y + player_height) // TILE_SIZE)

    colliding = False
    is_dead = False
    collision_side = None  # New variable
    collided_tile = None  # New variable for tile type

    for y in range(top_tile_y, bottom_tile_y + 1):
        for x in range(left_tile_x, right_tile_x + 1):
            if 0 <= y < LEVEL_HEIGHT and 0 <= x < LEVEL_WIDTH:  # check if tiles are in range
                tile = level_data[y][x]
                if tile == 't' or tile == 'g':  # Check for collision with grass tiles
                    tile_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if player_rect.colliderect(tile_rect):
                        colliding = True

                        # check for collision direction
                        if player_rect.bottom > tile_rect.top and player_rect.centery < tile_rect.centery:  # top collision
                            player_rect.bottom = tile_rect.top + 1  # Move player 1 pixel above
                            collision_side = "top"
                            collided_tile = tile  # Store the tile
                            return True, False, collision_side, collided_tile, player_rect
                        if player_rect.top < tile_rect.bottom and player_rect.centery > tile_rect.centery:  # bottom collision
                            player_rect.top = tile_rect.bottom
                            collision_side = "bottom"
                            return True, False, collision_side, collided_tile, player_rect

                        if player_rect.right > tile_rect.left and player_rect.centerx < tile_rect.centerx:  # left collision
                            player_rect.right = tile_rect.left
                            collision_side = "left"
                            return True, False, collision_side, collided_tile, player_rect
                        if player_rect.left < tile_rect.right and player_rect.centerx > tile_rect.centerx:  # right collision
                            player_rect.left = tile_rect.right
                            collision_side = "right"
                            return True, False, collision_side, collided_tile, player_rect
                if tile == 's' or tile == 'd' or tile == 'f' or tile == 'e':
                    tile_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if player_rect.colliderect(tile_rect):
                        is_dead = True
    return colliding, is_dead, collision_side, collided_tile, player_rect


# Main loop
running = True
clock = pygame.time.Clock()

while running:

    side_collision = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and not is_dead:
            if event.key in [pygame.K_d, pygame.K_RIGHT]:
                movement_direction = "right"
            if event.key in [pygame.K_a, pygame.K_LEFT]:
                movement_direction = "left"
            if event.key in [pygame.K_w, pygame.K_UP] and not is_jumping and is_on_ground:
                is_jumping = True
                y_velocity = -15
                is_on_ground = False  # when we jump, is_on_ground = False
        if event.type == pygame.KEYUP and not is_dead:
            if (event.key in [pygame.K_d, pygame.K_RIGHT]) and movement_direction == "right":
                movement_direction = None
            if (event.key in [pygame.K_a, pygame.K_LEFT]) and movement_direction == "left":
                movement_direction = None
    if not is_dead:
        # Movement & Animation Logic
        if movement_direction == "right" and not side_collision:
            player_x += player_speed
            if not is_jumping:
                player_frame = (player_frame + 1) % (len(right_frames) * animation_speed)
                current_sprite_index = right_frames[player_frame // animation_speed]
            else:
                current_sprite_index = 0

        elif movement_direction == "left" and not side_collision:
            player_x -= player_speed
            if not is_jumping:
                player_frame = (player_frame + 1) % (len(right_frames) * animation_speed)
                current_sprite_index = right_frames[player_frame // animation_speed]
            else:
                current_sprite_index = 0
        else:
            current_sprite_index = 0
    else:
        current_sprite_index = dead_frame  # If dead use death sprite

    # Keep player within screen bounds
    player_x = max(0, player_x)
    player_x = min(WIDTH - sprites[0].get_width(), player_x)

    # Jumping Logic
    if is_jumping:
        player_y += y_velocity
        y_velocity += gravity

    # Create player rect
    player_rect = pygame.Rect(player_x, player_y, sprites[0].get_width(), sprites[0].get_height())

    # check for collisions
    colliding, is_dead_temp, collision_side, collided_tile, player_rect = check_collision(player_rect, level_data)

    if colliding and collision_side == "top" and (collided_tile == 't' or collided_tile == 'g'):
        is_jumping = False
        y_velocity = 0
        player_y = player_rect.y
        is_on_ground = True  # Set to True here only
    if colliding and collision_side in ["left", "right"]:
        side_collision = True
        player_x = player_rect.x
    if colliding and collision_side == "bottom":
        player_y = player_rect.y
    if not colliding:
        is_jumping = True

    if colliding and (collided_tile == "s" or collided_tile == "d" or collided_tile == "f" or collided_tile == "e"):
        is_dead = True

    if player_y >= 500 and not colliding:
        player_y = 500
        is_jumping = False
        y_velocity = 0
        is_on_ground = True  # Set to True here only

    if is_dead_temp:
        is_dead = True

    # Falling logic
    if not is_on_ground and not is_jumping and not is_dead:
        player_y += gravity * 2  # Add gravity

    # Clear the screen
    screen.fill(WHITE)

    # Draw Level
    for row_index, row in enumerate(level_data):
        for col_index, tile in enumerate(row):
            tile_image = tile_images.get(tile)
            if tile_image:
                screen.blit(tile_image, (col_index * TILE_SIZE, row_index * TILE_SIZE))

    # Blit the current sprite
    current_sprite = sprites[current_sprite_index]
    if movement_direction == 'left' and not is_dead:
        flipped_sprite = pygame.transform.flip(current_sprite, True, False)
        screen.blit(flipped_sprite, (player_x, player_y))
    else:
        screen.blit(current_sprite, (player_x, player_y))

    # Update the display
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
