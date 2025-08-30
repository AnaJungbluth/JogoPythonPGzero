import random
from pgzero.rect import Rect

# --- CONFIGURAÇÕES ---
WIDTH = 800
HEIGHT = 500
GRAVITY = 0.5
TILE_SIZE = 128

# --- GAME START ---
game_state = "menu"
level = 1
num_enemies = 2
music_on = True
music.play("background")
finished = False

# --- TILES ---
tile_images = {
    "GC": "terrain_grass_block_top",
    "C": "cactus",
    "SR": "sign_right",
    ".": None
}

# --- MAP ---
map = [
    ["."] * 30,
    ["."] * 30,
    [".", ".", "SR", ".", ".", ".", ".", "C", "C", ".", ".", ".", ".", ".", ".", "C", ".", ".", ".", "C", ".", ".", ".", ".", "C", ".", ".", ".", "."],
    ["GC", "GC", "GC", "GC", "GC", "GC", "GC", "GC", "GC", "GC", "GC", "GC", "GC", "GC", "GC", "GC", "GC", "GC", "GC", "GC", "GC", "GC", "GC", "GC", "GC", "GC", "GC", "GC", "GC", "GC"]
]
map_width = len(map[0]) * TILE_SIZE
map_height = len(map) * TILE_SIZE

# --- PLATAFORMAS DE COLISÃO ---
platforms = []
for row_index, row in enumerate(map):
    for col_index, tile in enumerate(row):
        if tile in ["GL","GC","GR"]:
            rect = Rect(col_index*TILE_SIZE, row_index*TILE_SIZE, TILE_SIZE, TILE_SIZE)
            platforms.append(rect)

# deslocamento para melhorar o collider do player
offset_x = 25 
offset_y = 20

# --- PLAYER ---
class Player:
    def __init__(self, actor, x, y):
        self.actor = actor
        self.actor.x = x
        self.actor.y = y
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.direction = "right" 

        # collider
        self.width = 75  
        self.height = 95 
        self.rect = Rect(self.actor.x + offset_x, self.actor.y - offset_y, self.width, self.height) 

        # animações  
        self.walk_right = ["character_pink_walk_a_right", "character_pink_walk_b_right"]
        self.walk_left  = ["character_pink_walk_a_left", "character_pink_walk_b_left"]  
        self.idle_images = ["character_pink_idle", "character_pink_front"]
        self.jump_right  = ["character_pink_jump_right"]
        self.jump_left   = ["character_pink_jump_left"]
        self.frame = 0
        self.animation_idle = 0.05
        self.animation_speed = 0.10
        self.moving = False

    def move_left(self):
        self.vx = -2
        self.moving = True
        self.direction = "left"

    def move_right(self):
        self.vx = 2
        self.moving = True
        self.direction = "right"

    def stop(self):
        self.vx = 0
        self.moving = False

    def jump(self):
        global music_on
        if self.on_ground:
            self.vy = -15
            if music_on:
                sounds.sfx_jump.play()
    
    def victory(self):
        global game_state, finished
        game_state = "victory"
        finished = True

    def death(self):
        global game_state, music_on, finished
        if music_on and finished == False:
            sounds.death.play()
            finished = True
        game_state = "game_over"

    def update_animation(self):
        if not self.on_ground:
            self.frame += self.animation_speed
            if self.direction == "right":
                images_list = self.jump_right
            else:
                images_list = self.jump_left
            if self.frame >= len(images_list):
                self.frame = 0
            self.actor.image = images_list[int(self.frame)]

        elif self.moving:
            self.frame += self.animation_speed
            if self.direction == "right":
                images_list = self.walk_right
            else:
                images_list = self.walk_left
            if self.frame >= len(images_list):
                self.frame = 0
            self.actor.image = images_list[int(self.frame)]

        else:
            self.frame += self.animation_idle
            if self.frame >= len(self.idle_images):
                self.frame = 0
            self.actor.image = self.idle_images[int(self.frame)]

    def update(self, platforms):
        global offset_x, offset_y
        self.actor.x += self.vx
        self.rect.topleft = (self.actor.x + offset_x, self.actor.y - offset_y)

        for plat in platforms:
            if self.actor.colliderect(plat):
                if self.vx > 0:
                    self.actor.right = plat.left
                elif self.vx < 0:
                    self.actor.left = plat.right
        
        # Checa limites do mapa
        if self.actor.left < 0:
            self.actor.left = 0
            self.vx = 0
        if self.actor.right > map_width:
            self.actor.right = map_width
            self.vx = 0

        # gravidade / movimento vertical
        self.vy += GRAVITY
        self.actor.y += self.vy
        self.on_ground = False
        for plat in platforms:
            if self.actor.colliderect(plat):
                if self.vy > 0:  
                    self.actor.bottom = plat.top 
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:  
                    self.actor.top = plat.bottom
                    self.vy = 0

        self.update_animation()

player = Player(Actor("character_pink_idle"), 70, 100)

# --- CAMERA ---
camera_x = 0
camera_y = 0
def update_camera(player):
    global camera_x
    target_x = player.actor.x - WIDTH // 2
    max_camera_x = map_width - WIDTH
    target_x = max(0, min(max_camera_x, target_x))
    camera_x = target_x

# --- BANDEIRA ---
flag = Actor(
    "flag_green_a",
    (map_width - (1.5 * TILE_SIZE), map_height - 2 * TILE_SIZE)
)
flag_frames = ["flag_green_a", "flag_green_b"]
flag_index = 0
flag_timer = 0

offset_y_rat = 15

# --- INIMIGO ---
class Enemy:
    def __init__(self, actor, enemy_type, walk_right_images, walk_left_images, y, speed):
        import random
        self.actor = actor
        self.enemy_type = enemy_type
        self.walk_right_images = walk_right_images
        self.walk_left_images = walk_left_images
        self.actor.y = y
        # Spawn aleatório no eixo X
        self.actor.x = random.randint(0, map_width - self.actor.width)
        self.vx = speed if random.choice([True, False]) else -speed
        self.left_limit = 200
        self.right_limit = map_width - self.actor.width
        self.direction = "right" if self.vx > 0 else "left"

        # collider
        if enemy_type == "bee":
            self.width = 64  
            self.height = 60 
        elif enemy_type == "rat":
            self.width = 60  
            self.height = 50 
        self.rect = Rect(self.actor.x, self.actor.y + offset_y_rat, self.width, self.height)

        # animações
        self.frame = 0
        self.animation_speed = 0.10

    def update(self):
        self.actor.x += self.vx
        if self.enemy_type == "rat":
            self.rect.topleft = (self.actor.x, self.actor.y + offset_y_rat)
        elif self.enemy_type == "bee":
            self.rect.topleft = (self.actor.x, self.actor.y)

        # Checa limites do mapa
        if self.actor.left <= self.left_limit:
            self.actor.left = self.left_limit
            self.vx *= -1
            self.direction = "right"
        elif self.actor.right >= self.right_limit:
            self.actor.right = self.right_limit
            self.vx *= -1
            self.direction = "left"

        self.frame += self.animation_speed
        if self.frame >= len(self.walk_right_images):
            self.frame = 0

        if self.direction == "right":
            self.actor.image = self.walk_right_images[int(self.frame)]
        else:
            self.actor.image = self.walk_left_images[int(self.frame)]

num_bees = 5   
num_rats = 3   
bees = []
rats = []

for _ in range(num_bees):
    bees.append(
        Enemy(
            Actor("bee_a_right"), 
            enemy_type="bee",
            walk_right_images=["bee_a_right", "bee_b_right"],
            walk_left_images=["bee_a_left", "bee_b_left"],
            y=210, 
            speed=2
        )
    )

for _ in range(num_rats):
    rats.append(
        Enemy(
            Actor("mouse_walk_a_right"), 
            enemy_type="rat",
            walk_right_images=["mouse_walk_a_right", "mouse_walk_b_right"],
            walk_left_images=["mouse_walk_a_left", "mouse_walk_b_left"],
            y=335, 
            speed=1.5
        )
    )

class Button:
    def __init__(self, text, x, y, width, height, action, color = (205, 133, 63)):
        self.text = text
        self.rect = Rect(x, y, width, height)
        self.action = action
        self.color = color

    def draw(self):
        screen.draw.filled_rect(self.rect, self.color)
        screen.draw.text(
            self.text,
            center=self.rect.center,
            color="white",
            fontsize=30
        )

    def click(self, pos):
        if self.rect.collidepoint(pos):
            self.action()

def start_game():
    global game_state
    game_state = "playing"

def toggle_sound():
    global music_on
    if music_on:
        music.stop()
        music_on = False
    else:
        music.play("background")
        music_on = True

def exit_game():
    quit()

def restart_game():
    global game_state, player, bee, rat, finished

    player.actor.x = 70
    player.actor.y = 0
    player.vx = 0
    player.vy = 0
    player.won = False
    player.on_ground = False

    for bee in bees:
        bee.actor.x = random.randint(0, map_width - bee.actor.width)
        bee.vx = 2 if random.choice([True, False]) else -2
        bee.direction = "right" if bee.vx > 0 else "left"

    for rat in rats:
        rat.actor.x = random.randint(0, map_width - rat.actor.width)
        rat.vx = 1.5 if random.choice([True, False]) else -1.5
        rat.direction = "right" if rat.vx > 0 else "left"

    game_state = "playing"
    finished = False
    if music_on:
        music.play("background")

menu_buttons = [
    Button("Start Game", WIDTH//2 - 100, HEIGHT//2 - 60, 200, 50, start_game),
    Button("Toggle Sound", WIDTH//2 - 100, HEIGHT//2, 200, 50, toggle_sound),
    Button("Exit", WIDTH//2 - 100, HEIGHT//2 + 60, 200, 50, exit_game),
]

game_over_buttons = [
    Button("Play Again", WIDTH//2 - 100, HEIGHT//2 - 60, 200, 50, restart_game),
    Button("Toggle Sound", WIDTH//2 - 100, HEIGHT//2, 200, 50, toggle_sound),
    Button("Exit", WIDTH//2 - 100, HEIGHT//2 + 60, 200, 50, exit_game),
]

def update():
    global flag_index, flag_timer, finished

    if finished == False:
        if keyboard.left:
            player.move_left()
        elif keyboard.right:
            player.move_right()
        else:
            player.stop()

        if keyboard.space:
            player.jump()

    flag_timer += 1
    if flag_timer % 10 == 0:  
        flag_index = (flag_index + 1) % len(flag_frames)
        flag.image = flag_frames[flag_index]

    if player.actor.colliderect(flag):  
        player.victory()
    
    player.update(platforms)
    update_camera(player)
    
    for bee in bees:
        bee.update()
        if player.rect.colliderect(bee.rect):
            player.death()
    for rat in rats:
        rat.update()
        if player.rect.colliderect(rat.rect):
            player.death()

def draw():
    screen.clear()
    if game_state == "menu":
        screen.fill("black")
        screen.draw.text("My Platformer Game", center=(WIDTH//2, HEIGHT//2 - 120), color="white", fontsize=50)
        for button in menu_buttons:
            button.draw()

    elif game_state == "game_over":
        screen.fill("darkred")
        screen.draw.text("Game Over", center=(WIDTH//2, HEIGHT//2 - 120), color="white", fontsize=60)
        for button in game_over_buttons:
            button.draw()
    
    elif game_state == "victory":
        screen.fill("darkgreen")
        screen.draw.text("You Won!", center=(WIDTH//2, HEIGHT//2 - 120), color="white", fontsize=60)
        for button in game_over_buttons:
            button.draw()

    elif game_state == "playing":
        screen.blit("back", (0, 0))  
        for y, linha in enumerate(map):
            for x, c in enumerate(linha):
                img = tile_images.get(c)
                if img:
                    screen.blit(img, (x * TILE_SIZE - camera_x, y * TILE_SIZE))

        screen.blit(flag.image, (flag.x - camera_x, flag.y - camera_y))
        screen.blit(player.actor.image, (player.actor.x - camera_x, player.actor.y - camera_y - 50))
        
        for bee in bees:
            screen.blit(bee.actor.image, (bee.actor.x - camera_x, bee.actor.y))
        for rat in rats:
            screen.blit(rat.actor.image, (rat.actor.x - camera_x, rat.actor.y))

def on_mouse_down(pos):
    if game_state == "menu":
        for button in menu_buttons:
            button.click(pos)
    elif game_state == "game_over" or game_state == "victory":
        for button in game_over_buttons:
            button.click(pos)
