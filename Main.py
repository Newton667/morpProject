from cgitb import reset

import pygame
import sys
import random
import math

# Initialize Pygame
pygame.init()

# Set up the display
width, height = 1280, 720
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Morp(1)")

# Load the Morp.png image and set it as the window icon
icon = pygame.image.load('Pictures/Morp.png')
pygame.display.set_icon(icon)

# Load the pause button image
pause_button = pygame.image.load('Pictures/Pause.png').convert_alpha()
pause_button_rect = pause_button.get_rect(topright=(width - 10, 10))  # Top right corner

# Define colors
white = (255, 255, 255)
black = (0, 0, 0)
green = (0, 255, 0)
red = (255, 0, 0)
blue = (0, 0, 255)
gray = (128, 128, 128)
sky_blue = (135, 206, 235)

# Define the Gun class to support multiple types of guns
class Gun:
    def __init__(self, name, image_path, bullet_image, damage, fire_rate, bullet_speed, spread_angle=0, projectile_count=1):
        self.name = name
        self.image = pygame.image.load(image_path).convert_alpha()
        self.bullet_image = bullet_image
        self.damage = damage
        self.fire_rate = fire_rate  # Cooldown between shots in milliseconds
        self.bullet_speed = bullet_speed
        self.spread_angle = spread_angle  # Spread angle in degrees
        self.projectile_count = projectile_count  # Number of bullets to fire


# Define the Player class
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, image_path, gun):
        super().__init__()
        self.x = x
        self.y = y
        self.image_path = image_path

        # Load the character image
        self.original_image = pygame.image.load(self.image_path).convert_alpha()
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.x, self.y)

        # Player attributes
        self.speed = 3
        self.hp = 100
        self.max_hp = 100
        self.direction = 'right'

        # XP and Leveling attributes
        self.level = 1
        self.xp = 0
        self.xp_needed = 50  # Initial XP required to level up

        # Cooldown for taking damage (in milliseconds)
        self.damage_cooldown = 500  # 0.5 second cooldown
        self.last_damage_time = 0  # Tracks the last time the player took damage

        # Blinking effect when taking damage
        self.is_blinking = False
        self.blink_duration = 300  # Blink duration in milliseconds
        self.blink_start_time = 0

        # Gun
        self.gun = gun
        self.gun_image = self.gun.image
        self.gun_rect = self.gun_image.get_rect()

        # Shooting cooldown
        self.last_shot_time = 0

        # Gun rotation variables
        self.gun_distance_from_player = 40  # Distance of the gun from the player's center
        self.gun_angle = 0  # Current angle of the gun

        # Initialize rotated gun and its rect (to avoid AttributeError)
        self.rotated_gun = self.gun_image  # Start with the gun's default image
        self.gun_rect = self.rotated_gun.get_rect(center=self.rect.center)  # Position gun initially

        # Initialize an inventory to track upgrades
        self.inventory = {}

    def update(self, keys, obstacles, Pickup, Bunger, slimes, screen_width, screen_height, mouse_pos):
        # Movement logic with WASD keys
        if keys[pygame.K_w]:
            self.rect.y -= self.speed
        if keys[pygame.K_s]:
            self.rect.y += self.speed
        if keys[pygame.K_a]:
            self.rect.x -= self.speed
            if self.direction != 'left':
                self.image = pygame.transform.flip(self.original_image, True, False)
                self.direction = 'left'
        if keys[pygame.K_d]:
            self.rect.x += self.speed
            if self.direction != 'right':
                self.image = self.original_image
                self.direction = 'right'

        # Handle blinking when taking damage
        if self.is_blinking:
            current_time = pygame.time.get_ticks()
            if current_time - self.blink_start_time > self.blink_duration:
                self.is_blinking = False
                self.image = self.original_image  # Revert to normal image

        # Collision detection with window boundaries
        self.check_window_collision(screen_width, screen_height)

        # Check for pickup collisions and collect XP or HP
        pickup_collisions = pygame.sprite.spritecollide(self, Pickup, True)
        for pickup in pickup_collisions:
            if isinstance(pickup, Candy):
                self.gain_xp(10)
                # Check if the player can level up
                self.check_level_up()
            elif isinstance(pickup, Bunger):
                self.gain_HP(100)  # Gain 100 HP on Bunger collection

        # Rotate the gun to face the mouse cursor and position it around the player
        self.rotate_gun(mouse_pos)

        """
        # Check for collisions with slimes and take damage (with cooldown)
        slime_collisions = pygame.sprite.spritecollide(self, slimes, False)
        for slime in slime_collisions:
            self.take_damage(10)  # Try to take 10 damage on slime collision
        """
        # Check for collisions with obstacles (if any)
        if pygame.sprite.spritecollide(self, obstacles, False):
            self.hp -= 1  # Reduce HP on collision

    def take_damage(self, amount):
        # Get the current time
        current_time = pygame.time.get_ticks()

        # Check if enough time has passed since the last damage
        if current_time - self.last_damage_time > self.damage_cooldown:
            self.hp -= amount
            self.last_damage_time = current_time  # Update the last damage time
            print(f"Player took {amount} damage. Current HP: {self.hp}")

            # Trigger blinking effect
            self.is_blinking = True
            self.blink_start_time = current_time
            self.image = self.original_image.copy()  # Copy the original image
            self.image.fill((255, 0, 0), special_flags=pygame.BLEND_RGBA_MULT)  # Tint red

        if self.hp <= 0:
            print("Game Over!")

    # Function to heal the player
    def gain_HP(self, amount):
        self.hp = min(self.hp + amount, self.max_hp)  # Increase HP but do not exceed max HP
        print(f"Player gained {amount} HP. Current HP: {self.hp}/{self.max_hp}")

    # Function to draw the XP bar and level text
    def get_hp(self):
        return self.hp

    # Function to draw the XP bar and level text
    def gain_xp(self, amount):
        self.xp += amount
        print(f"Player gained {amount} XP. Current XP: {self.xp}/{self.xp_needed}")

    def get_xp_progress(self):
        return self.xp / self.xp_needed

    def check_level_up(self):
        if self.xp >= self.xp_needed:
            self.level += 1
            self.xp -= self.xp_needed  # Carry over remaining XP
            self.xp_needed = int(self.xp_needed * 1.5)
            print(f"Level Up! Player is now level {self.level}.")
            Upgrade_Page(self)  # Call the upgrade page

            # Spawn new enemies based on the player's level
            self.spawn_enemies_based_on_level()

    def spawn_enemies_based_on_level(self):
        global enemies, all_sprites
        # Go through the enemy pool and add the appropriate enemies for the current level
        for pool in (enemy_pool, enemyBoss_pool):  # Iterate over both enemy pools
            for level, EnemyClass in pool:
                if level <= self.level:
                    # Create a new enemy of the specified class and add it to the groups
                    new_enemy = EnemyClass()
                    enemies.add(new_enemy)
                    all_sprites.add(new_enemy)

    def check_window_collision(self, screen_width, screen_height):
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > screen_width:
            self.rect.right = screen_width
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > screen_height:
            self.rect.bottom = screen_height

    def rotate_gun(self, mouse_pos):
        """Rotate the gun around the player based on the mouse cursor position."""
        # Get the player's center position
        player_center = self.rect.center

        # Calculate the angle between the player and the mouse cursor
        rel_x, rel_y = mouse_pos[0] - player_center[0], mouse_pos[1] - player_center[1]
        angle = math.degrees(math.atan2(-rel_y, rel_x))  # Negative for counterclockwise rotation

        # Convert angle to radians for trigonometry calculations
        rad_angle = math.radians(angle)

        # Calculate the new position for the gun around the player
        gun_x = player_center[0] + self.gun_distance_from_player * math.cos(rad_angle) - self.gun_rect.width // 100
        gun_y = player_center[1] - self.gun_distance_from_player * math.sin(rad_angle) - self.gun_rect.height // 100

        # Rotate the gun based on the angle
        rotated_gun_image = pygame.transform.rotate(self.gun.image, angle)

        # Check if the gun should be flipped horizontally based on the angle
        if 90 < angle < 270:
            # Flip the gun horizontally if it's on the left side of the player
            rotated_gun_image = pygame.transform.flip(rotated_gun_image, True, True)
            rotated_gun_image = pygame.transform.rotate(rotated_gun_image, 180)  # Rotate 180 degrees for flip

        # Update the gun's rect to its new position
        self.rotated_gun = rotated_gun_image
        self.gun_rect = self.rotated_gun.get_rect(center=(gun_x, gun_y))

    # Draw the player and gun on the screen
    def draw(self, surface):
        """Draw the player and the rotating gun on the screen."""
        # First, draw the player
        surface.blit(self.image, self.rect)

        # Then, draw the gun, ensuring it's drawn after the player
        surface.blit(self.rotated_gun, self.gun_rect)

    # Shooting function
    def shoot(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time >= self.gun.fire_rate:
            self.last_shot_time = current_time
            bullets = []

            # Calculate the base angle between the player and the mouse position
            mouse_x, mouse_y = pygame.mouse.get_pos()
            rel_x, rel_y = mouse_x - self.gun_rect.centerx, mouse_y - self.gun_rect.centery
            base_angle = math.atan2(-rel_y, rel_x)  # Negative for counterclockwise rotation

            # Spread adjustment
            spread_radians = math.radians(self.gun.spread_angle)
            start_angle = base_angle - spread_radians * (self.gun.projectile_count - 1) / 2

            # Create the projectiles
            for i in range(self.gun.projectile_count):
                angle = start_angle + i * spread_radians
                # Calculate direction vector from the angle
                direction = (math.cos(angle), -math.sin(angle))

                # Create a new projectile with direction
                bullet = Projectile(self.gun_rect.center, direction, self.gun.bullet_image, self.gun.bullet_speed,
                                    self.gun.damage)
                bullets.append(bullet)

            return bullets
        return None

    # Inventory function
    def add_upgrade_to_inventory(self, upgrade_name, upgrade_logo):
        """Add an upgrade to the player's inventory."""
        if upgrade_name in self.inventory:
            self.inventory[upgrade_name]['count'] += 1
        else:
            self.inventory[upgrade_name] = {'count': 1, 'logo': upgrade_logo}

    # Function to draw the XP bar and level text
    def get_level(self):
        return self.level

# Define the Projectile class (moved outside of the Player class)
class Projectile(pygame.sprite.Sprite):
    def __init__(self, pos, direction, image_path, speed, damage):
        super().__init__()
        self.image = pygame.image.load(image_path).convert_alpha()
        self.rect = self.image.get_rect(center=pos)
        self.damage = damage
        self.velocity = (direction[0] * speed, direction[1] * speed)

    def update(self):
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]

        # Remove bullet if it's off screen
        if self.rect.right < 0 or self.rect.left > width or self.rect.bottom < 0 or self.rect.top > height:
            self.kill()




# Define the Candy class
class Candy(pygame.sprite.Sprite):
    def __init__(self, image_path):
        super().__init__()
        self.image = pygame.image.load(image_path).convert_alpha()
        self.rect = self.image.get_rect()
        self.spawn_random()

    def spawn_random(self):
        self.rect.x = random.randint(0, width - self.rect.width)
        self.rect.y = random.randint(0, height - self.rect.height)

# Define the Bunger class
class Bunger(pygame.sprite.Sprite):
    def __init__(self, image_path):
        super().__init__()
        self.image = pygame.image.load(image_path).convert_alpha()
        self.rect = self.image.get_rect()
        self.spawn_random()

    def spawn_random(self):
        self.rect.x = random.randint(0, width - self.rect.width)
        self.rect.y = random.randint(0, height - self.rect.height)

#Enemy Class
# Define the Enemy base class
class Enemy(pygame.sprite.Sprite):
    def __init__(self, image_path, speed, hp, damage):
        super().__init__()
        self.image = pygame.image.load(image_path).convert_alpha()
        self.original_image = self.image.copy()  # Store the original image for resetting after blinking
        self.rect = self.image.get_rect()

        # Enemy attributes
        self.hp = hp
        self.speed = speed
        self.damage = damage  # New damage attribute
        self.direction = 'right'  # Initialize enemy facing right

        # Damage blinking attributes
        self.is_blinking = False
        self.blink_duration = 300  # Blink duration in milliseconds
        self.blink_start_time = 0

    def spawn_within_screen(self):
        """Spawn enemy at a random position within the screen."""
        self.rect.x = random.randint(0, width - self.rect.width)
        self.rect.y = random.randint(0, height - self.rect.height)

    def move_towards_player(self, player):
        """Moves the enemy towards the player."""
        direction_x = player.rect.x - self.rect.x
        direction_y = player.rect.y - self.rect.y
        distance = math.hypot(direction_x, direction_y)

        # Flip the enemy based on its direction relative to the player
        if direction_x < 0 and self.direction != 'left':  # Moving left
            self.image = pygame.transform.flip(self.original_image, True, False)
            self.direction = 'left'
        elif direction_x > 0 and self.direction != 'right':  # Moving right
            self.image = self.original_image  # Restore original image
            self.direction = 'right'

        if distance > 0:  # Normalize direction
            direction_x /= distance
            direction_y /= distance

        # Move the enemy towards the player
        self.rect.x += int(direction_x * self.speed)
        self.rect.y += int(direction_y * self.speed)

    def enemy_take_damage(self, damage):
        """Handles damage and triggers blinking effect."""
        self.hp -= damage
        print(f"{self.__class__.__name__} took {damage} damage. Current HP: {self.hp}")

        # Trigger the blinking effect
        self.is_blinking = True
        self.blink_start_time = pygame.time.get_ticks()

        # Tint red manually by setting a solid color
        red_tinted_image = self.original_image.copy()
        red_tinted_image.fill((255, 0, 0), special_flags=pygame.BLEND_ADD)  # Tint red with BLEND_ADD
        self.image = red_tinted_image

        if self.hp <= 0:
            self.kill()  # Remove the enemy when HP reaches 0

    def update(self):
        """Update the enemy, handle blinking state."""
        # Handle blinking effect
        if self.is_blinking:
            current_time = pygame.time.get_ticks()
            if current_time - self.blink_start_time > self.blink_duration:
                self.is_blinking = False
                # Restore the original image and reapply the correct flip (direction)
                if self.direction == 'left':
                    self.image = pygame.transform.flip(self.original_image, True, False)  # Face left again
                else:
                    self.image = self.original_image  # Face right



# Define the Slime class (inherits from Enemy) ----------------------------
class Slime(Enemy):
    def __init__(self):
        super().__init__('Pictures/Slime.png', speed=2, hp=10, damage=10)  # Set slime's damage to 10
        self.spawn_within_screen()

class BlueSlime(Enemy):
    def __init__(self):
        super().__init__('Pictures/BlueSlime.png', speed=3, hp=15, damage=15)  # Set blue slime's damage to 15
        self.spawn_within_screen()

class Golem(Enemy):
    def __init__(self):
        super().__init__('Pictures/Golem.png', speed=2, hp=30, damage=25)  # Set golem's damage to 20
        self.spawn_within_screen()

class FastFish(Enemy):
    def __init__(self):
        super().__init__('Pictures/FastFish.png', speed=5, hp=5, damage=5)  # Set fast fish's damage to 5
        self.spawn_within_screen()

# Enemy pool where each entry is a tuple of (level, EnemyClass)
enemy_pool = [
    (1, Slime),  # Slime starts appearing at level 1
    (2, Slime),  # Add more enemy types for higher levels
    (4, BlueSlime),
    (5, Slime),
    (10, FastFish),
    # Add more enemy types for higher levels
]

enemyBoss_pool = [
    (6, Golem),
]

def get_available_enemies(level):
    """Return a list of enemy classes available for the given level."""
    return [EnemyClass for lvl, EnemyClass in enemy_pool if lvl <= level]

def get_available_enemiesBoss(level):
    """Return a list of enemy classes available for the given level."""
    return [EnemyClass for lvl, EnemyClass in enemyBoss_pool if lvl <= level]

def spawn_random_enemies(player):
    """Spawn enemies based on the player's level and the enemy pool."""
    global enemies, all_sprites
    # Dictionary to keep track of how many of each enemy type to spawn
    enemies_to_spawn = {}

    # Determine which enemies to spawn based on the player's current level
    for level, EnemyClass in enemy_pool:
        if player.level >= level:
            # Count how many times an enemy class appears
            if EnemyClass in enemies_to_spawn:
                enemies_to_spawn[EnemyClass] += 1
            else:
                enemies_to_spawn[EnemyClass] = 1

    # Spawn the enemies according to the count in enemies_to_spawn
    for EnemyClass, count in enemies_to_spawn.items():
        for _ in range(count):
            # Create a new enemy instance and add it to the groups
            new_enemy = EnemyClass()
            enemies.add(new_enemy)
            all_sprites.add(new_enemy)

def spawn_random_enemies_Slow(player):
    """Spawn enemies based on the player's level and the enemy pool."""
    global enemies, all_sprites
    # Dictionary to keep track of how many of each enemy type to spawn
    enemies_to_spawn = {}

    # Determine which enemies to spawn based on the player's current level
    for level, EnemyClass in enemyBoss_pool:
        if player.level >= level:
            # Count how many times an enemy class appears
            if EnemyClass in enemies_to_spawn:
                enemies_to_spawn[EnemyClass] += 1
            else:
                enemies_to_spawn[EnemyClass] = 1

    # Spawn the enemies according to the count in enemies_to_spawn
    for EnemyClass, count in enemies_to_spawn.items():
        for _ in range(count):
            # Create a new enemy instance and add it to the groups
            new_enemy = EnemyClass()
            enemies.add(new_enemy)
            all_sprites.add(new_enemy)


# Replace slimes group with a generic enemies group
enemies = pygame.sprite.Group()

# In the game loop, spawn slimes and other enemies:
# Example for slime:
"""
slime = Slime()
enemies.add(slime)
all_sprites.add(slime)
"""

# Now update all enemies in the main game loop
for enemy in enemies:
    enemy.move_towards_player(player)  # Move each enemy toward the player
    enemy.update()  # Handle blinking and other updates


# Function to draw the XP bar and level text
def draw_xp_bar(screen, player):
    bar_width = 150
    bar_height = 15
    bar_x = 15
    bar_y = 15
    fill_width = int(bar_width * player.get_xp_progress())
    pygame.draw.rect(screen, gray, (bar_x, bar_y, bar_width, bar_height))
    pygame.draw.rect(screen, blue, (bar_x, bar_y, fill_width, bar_height))
    font = pygame.font.Font(None, 25)
    text = font.render(f'XP: {player.xp}/{player.xp_needed}', True, black)
    screen.blit(text, (bar_x, bar_y + bar_height + 5))
    text = font.render(f'Level: {player.level}', True, black)
    screen.blit(text, (bar_x, bar_y + bar_height + 20))


# Function to draw the HP bar and HP text
def draw_HP_bar(screen, player):
    bar_width = 12.3
    bar_height = 15
    bar_x = 15
    bar_y = 70
    fill_width = int(bar_width * (player.get_hp() / player.max_hp * bar_width))  # Adjust fill width based on max_hp
    pygame.draw.rect(screen, gray, (bar_x, bar_y, bar_width, bar_height))
    pygame.draw.rect(screen, red, (bar_x, bar_y, fill_width, bar_height))
    font = pygame.font.Font(None, 25)
    text = font.render(f'HP: {player.hp}/{player.max_hp}', True, black)
    screen.blit(text, (bar_x, bar_y + bar_height + 5))

# Draw timer
def draw_timer(screen, time):
    font = pygame.font.Font(None, 25)
    hours = time // 3600
    minutes = (time % 3600) // 60
    seconds = time % 60
    text = font.render(f'Time: {hours:02}:{minutes:02}:{seconds:02}', True, black)
    text_rect = text.get_rect(center=(width // 2, 15))  # Center the text at the top middle
    screen.blit(text, text_rect)


# Create guns/weapons
pistol = Gun("Pistol", 'Pictures/Pistol.png', 'Pictures/Bullet1.png', damage=5, fire_rate=500, bullet_speed=10, spread_angle=1, projectile_count=1)
katana = Gun("Katana", 'Pictures/Katana.png', 'Pictures/Slash.png', damage=5, fire_rate=250, bullet_speed=10, spread_angle=0, projectile_count=1)

# Create the player instance with the pistol gun
player = Player(640, 360, 'Pictures/Morp.png', pistol)

# Create sprite groups
all_sprites = pygame.sprite.Group()
all_sprites.add(player)

bullets = pygame.sprite.Group()
Pickup = pygame.sprite.Group()
slimes = pygame.sprite.Group()

# Timer to spawn candy every 15 seconds
candy_spawn_event = pygame.USEREVENT + 1
pygame.time.set_timer(candy_spawn_event, 5000)

# Timer to spawn slimes/enemies every # seconds
Enemy_Spawn_Timer = pygame.USEREVENT + 2
pygame.time.set_timer(Enemy_Spawn_Timer, 5000)

# Slower enemy spawn timer
Enemy_Spawn_Timer_Slow = pygame.USEREVENT + 3
pygame.time.set_timer(Enemy_Spawn_Timer_Slow, 10000)

# Timer to spawn Bunger every 15 seconds
bunger_spawn_event = pygame.USEREVENT + 4
pygame.time.set_timer(bunger_spawn_event, 15000)


# Create a group for obstacles (currently empty, but you can add obstacles here)
obstacles = pygame.sprite.Group()

#Title screen function ------------------------------------------------
def title_screen():
    """Title screen with a transparent background, title, and start button."""
    button_width = 150
    button_height = 40
    start_button = pygame.Rect(width // 2 - button_width // 2, height // 2 - 50, button_width, button_height)

    # Load the title image
    title_image = pygame.image.load('Pictures/title.png').convert_alpha()
    title_image_rect = title_image.get_rect(center=(width // 2, height // 2 - 200))

    # Create a semi-transparent surface for the frosted effect
    transparent_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    transparent_surface.fill((0, 0, 0, 128))  # Black with 50% transparency

    # Title screen loop
    while True:
        # Fill the screen with white color
        screen.fill(white)

        # Draw the transparent overlay and title screen on top of the current game state
        screen.blit(transparent_surface, (0, 0))  # Draw the transparent overlay

        # Blit the title image
        screen.blit(title_image, title_image_rect)

        font = pygame.font.Font(None, 48)
        title_text = font.render('Morp(1)', True, black)
        title_rect = title_text.get_rect(center=(width // 2, height // 2 - 100))
        screen.blit(title_text, title_rect)

        # Draw the start button
        pygame.draw.rect(screen, green, start_button)
        start_text = font.render('Start', True, black)
        start_text_rect = start_text.get_rect(center=start_button.center)
        screen.blit(start_text, start_text_rect)

        # Only one call to update the display
        pygame.display.flip()

        # Handle title screen events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.collidepoint(event.pos):
                    reset_game()  # Reset the game state and timer when the player starts
                    return  # Exit the title screen loop and start the game
    # Start the title screen loop

#Pause menu function ------------------------------------------------

# Initialize paused flag
paused = False  # Game starts in running state

# Define the pause menu function
def pause_menu():
    """Pause menu with a transparent background, title, resume, and quit buttons."""
    button_width = 150
    button_height = 40
    resume_button = pygame.Rect(width // 2 - button_width // 2, height // 2 - 70, button_width, button_height)
    titlescreen_button = pygame.Rect(width // 2 - button_width // 2, height // 2 - 10, button_width, button_height)
    quit_button = pygame.Rect(width // 2 - button_width // 2, height // 2 + 50, button_width, button_height)

    # Create a semi-transparent surface for the frosted effect
    transparent_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    transparent_surface.fill((0, 0, 0, 128))  # Black with 50% transparency

    # Pause menu loop
    while True:
        # First, draw the game state underneath
        draw_GameUI()

        # Draw the transparent overlay and pause menu on top of the current game state
        screen.blit(transparent_surface, (0, 0))  # Draw the transparent overlay

        font = pygame.font.Font(None, 36)
        title_font = pygame.font.Font(None, 48)  # Larger font for the title

        # Draw the title "Morp(1)"
        title_text = title_font.render('Morp(1)', True, black)
        title_rect = title_text.get_rect(center=(width // 2, height // 2 - 250))
        screen.blit(title_text, title_rect)

        # Draw the player's inventory
        inventory_y_start = height // 2 - 200
        inventory_x_start = width // 2 - 300
        for i, (upgrade_name, upgrade_info) in enumerate(player.inventory.items()):
            # Draw the upgrade logo
            logo_pos = (inventory_x_start, inventory_y_start + i * 70)
            screen.blit(upgrade_info['logo'], logo_pos)

            # Draw the count of upgrades
            count_text = font.render(f'x{upgrade_info["count"]}', True, black)
            screen.blit(count_text, (inventory_x_start + 80, logo_pos[1] + 20))

        # Draw the buttons (Resume, Title Screen, and Quit)
        pygame.draw.rect(screen, green, resume_button)
        pygame.draw.rect(screen, sky_blue, titlescreen_button)
        pygame.draw.rect(screen, red, quit_button)

        resume_text = font.render('Resume', True, black)
        titlescreen_text = font.render('Title Screen', True, black)
        quit_text = font.render('Quit', True, black)

        # Center the text within the buttons
        resume_text_rect = resume_text.get_rect(center=resume_button.center)
        titlescreen_text_rect = titlescreen_text.get_rect(center=titlescreen_button.center)
        quit_text_rect = quit_text.get_rect(center=quit_button.center)

        # Blit the text on the buttons
        screen.blit(resume_text, resume_text_rect)
        screen.blit(titlescreen_text, titlescreen_text_rect)
        screen.blit(quit_text, quit_text_rect)

        # Only one call to update the display
        pygame.display.flip()

        # Handle pause menu events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if resume_button.collidepoint(event.pos):
                    return False  # Resume the game
                if titlescreen_button.collidepoint(event.pos):
                    reset_game()  # Reset the game state
                    return 'title_screen'  # Indicate to show the title screen
                if quit_button.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False  # Resume the game if ESC is pressed


# Upgrade Page function ------------------------------------------------

# Define the Upgrade class
class Upgrade:
    def __init__(self, name, description, effect, logo_image_path):
        self.name = name
        self.description = description
        self.effect = effect  # A function to apply the upgrade
        self.logo_image = pygame.image.load(logo_image_path).convert_alpha()  # Load the logo image

    def apply(self, player):
        if self.name == "Bunger Rain":
            enable_bunger_spawn(player)
        else:
            self.effect(player)

        # Add upgrade to the player's inventory
        player.add_upgrade_to_inventory(self.name, self.logo_image)


# Upgrade effects
def increase_speed(player):
    player.speed += 1

def increase_damage(player):
    player.gun.damage += 5

def increase_health(player):
    player.max_hp += 20  # Increase max HP
    player.hp = min(player.hp + 20, player.max_hp)  # Heal the player, but do not exceed max HP

bunger_spawn_count = 0  # Initialize the counter for Bunger Rain upgrade


def enable_bunger_spawn(player):
    global bungerSpawn, bunger_spawn_count
    bungerSpawn = True
    bunger_spawn_count += 1  # Increase the count each time the upgrade is selected
    print(f"Bunger Rain upgrade activated! Bungers will spawn at level {bunger_spawn_count}.")



# Add the Bunger upgrade to the upgrades pool
upgrades_pool = [
    Upgrade("Speed Boost", "Increases player's speed by 1.", increase_speed, 'Pictures/Boot.png'),
    Upgrade("Damage Boost", "Increases gun damage by 5.", increase_damage, 'Pictures/DamagePlus.png'),
    Upgrade("Health Boost", "Increases max health by 20 and heals 20 HP.", increase_health, 'Pictures/HealCross.png'),
    Upgrade("Bunger Rain", "Bungers will start raining down!", enable_bunger_spawn, 'Pictures/Bunger.png'),
]


# Function to select random upgrades from the pool
import random
def select_random_upgrades(upgrades_pool, count=3):
    return random.sample(upgrades_pool, min(count, len(upgrades_pool)))


def Upgrade_Page(player):
    """Upgrade page that appears on leveling up."""
    button_width = 200
    button_height = 40
    selected_upgrades = select_random_upgrades(upgrades_pool, 3)
    logo_size = (64, 64)  # Size of the logos

    # Create a semi-transparent surface for the frosted effect
    transparent_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    transparent_surface.fill((0, 0, 0, 128))  # Black with 50% transparency

    # Create buttons for each upgrade
    upgrade_buttons = []
    for i, upgrade in enumerate(selected_upgrades):
        button_rect = pygame.Rect(
            width // 2 - button_width // 2,
            height // 2 - 100 + i * (logo_size[1] + button_height + 30),
            button_width,
            button_height
        )
        upgrade_buttons.append((button_rect, upgrade))

    while True:
        # First, draw the game state underneath
        draw_GameUI()

        # Draw the transparent overlay and upgrade menu on top of the current game state
        screen.blit(transparent_surface, (0, 0))  # Draw the transparent overlay

        font = pygame.font.Font(None, 36)
        title_font = pygame.font.Font(None, 48)  # Larger font for the title

        # Draw the title "Choose Your Upgrade"
        title_text = title_font.render('Choose Your Upgrade', True, white)
        title_rect = title_text.get_rect(center=(width // 2, height // 2 - 220))
        screen.blit(title_text, title_rect)

        # Draw the logos, descriptions, and buttons for each upgrade
        for button_rect, upgrade in upgrade_buttons:
            # Draw the logo
            logo_pos = (button_rect.x, button_rect.y - logo_size[1] - 10)  # Position logo above the button
            logo = pygame.transform.scale(upgrade.logo_image, logo_size)  # Resize the logo if needed
            screen.blit(logo, logo_pos)

            # Draw the description text
            desc_text = font.render(upgrade.description, True, black)
            desc_text_rect = desc_text.get_rect(center=(button_rect.centerx, button_rect.centery - 30))
            screen.blit(desc_text, desc_text_rect)

            # Draw the button
            pygame.draw.rect(screen, green, button_rect)
            button_text = font.render(upgrade.name, True, black)
            screen.blit(button_text, (button_rect.x + 10, button_rect.y + 5))

        # Only one call to update the display
        pygame.display.flip()

        # Handle upgrade selection events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for button_rect, upgrade in upgrade_buttons:
                    if button_rect.collidepoint(event.pos):
                        upgrade.apply(player)
                        return  # Exit the upgrade page after selecting an upgrade



# Reset the game state ------------------------------------------------
def reset_game():
    """Reset the game state to its initial configuration."""
    global player, all_sprites, bullets, Pickup, enemies, obstacles, start_time, total_paused_time, pause_start_time, paused, player_dead
    global bungerSpawn, bunger_spawn_count  # Include global variables related to upgrades

    # Clear all sprite groups to ensure no lingering objects
    all_sprites.empty()
    bullets.empty()
    Pickup.empty()
    enemies.empty()
    obstacles.empty()

    # Reset global variables related to upgrades
    bungerSpawn = False
    bunger_spawn_count = 0

    # Recreate the player instance with the pistol gun and reset HP and inventory
    player = Player(640, 360, 'Pictures/Morp.png', pistol)
    player.inventory = {}  # Reset the inventory
    player.speed = 3       # Reset player speed
    player.max_hp = 100    # Reset player max HP
    player.hp = 100        # Reset player HP to max HP
    player.gun.damage = 5  # Reset player gun damage to its initial value

    all_sprites.add(player)  # Add player to the all_sprites group

    # Reset the sprite groups
    bullets = pygame.sprite.Group()
    Pickup = pygame.sprite.Group()
    enemies = pygame.sprite.Group()  # Use a general enemies group instead of slimes
    obstacles = pygame.sprite.Group()  # Recreate the group for obstacles (currently empty)

    # Reset the game timer
    start_time = pygame.time.get_ticks()
    total_paused_time = 0
    pause_start_time = None

    # Reset paused and player dead states
    paused = False  # Reset paused state when the game is restarted
    player_dead = False  # Reset player dead status


#Death Game Over function ------------------------------------------------

# Define the Game Over screen function
def Game_Jover(death_time):
    """Death menu with a transparent background, title and quit buttons."""
    button_width = 150
    button_height = 40
    titlescreen_button = pygame.Rect(width // 2 - button_width // 2, height // 2 - 10, button_width, button_height)
    quit_button = pygame.Rect(width // 2 - button_width // 2, height // 2 + 50, button_width, button_height)

    # Create a semi-transparent surface for the frosted effect
    transparent_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    transparent_surface.fill((0, 0, 0, 128))  # Black with 50% transparency

    # Game over loop
    while True:
        # First, draw the game state underneath
        draw_GameUI()

        # Draw the transparent overlay and death menu on top of the current game state
        screen.blit(transparent_surface, (0, 0))  # Draw the transparent overlay

        font = pygame.font.Font(None, 36)
        title_font = pygame.font.Font(None, 48)  # Larger font for the title

        # Draw the title "Game Over"
        title_text = title_font.render('Game Over', True, black)
        title_rect = title_text.get_rect(center=(width // 2, height // 2 - 150))
        screen.blit(title_text, title_rect)

        # Display the time survived (using the death_time argument)
        minutes = death_time // 60
        seconds = death_time % 60
        time_survived_text = font.render(f'Time Survived: {minutes:02}:{seconds:02}', True, black)
        time_survived_rect = time_survived_text.get_rect(center=(width // 2, height // 2 - 100))
        screen.blit(time_survived_text, time_survived_rect)

        # Draw the buttons (Title Screen, and Quit)
        pygame.draw.rect(screen, sky_blue, titlescreen_button)
        pygame.draw.rect(screen, red, quit_button)

        titlescreen_text = font.render('Title Screen', True, black)
        quit_text = font.render('Quit', True, black)

        # Center the text within the buttons
        titlescreen_text_rect = titlescreen_text.get_rect(center=titlescreen_button.center)
        quit_text_rect = quit_text.get_rect(center=quit_button.center)

        # Blit the text on the buttons
        screen.blit(titlescreen_text, titlescreen_text_rect)
        screen.blit(quit_text, quit_text_rect)

        # Only one call to update the display
        pygame.display.flip()

        # Handle pause menu events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if titlescreen_button.collidepoint(event.pos):
                    reset_game()  # Reset the game state
                    return 'title_screen'  # Indicate to show the title screen
                if quit_button.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    reset_game()  # Reset the game state
                    return 'title_screen'  # Indicate to show the title screen


# Draw the game state ------------------------------------------------
def draw_GameUI():
    # Fill the screen with a background color (white in this case)
    screen.fill(white)

    # Draw the XP bar in the top-left corner of the screen
    draw_xp_bar(screen, player)

    # Draw the HP bar in the top-left corner of the screen
    draw_HP_bar(screen, player)

    # Draw the pause button
    screen.blit(pause_button, pause_button_rect)

    # Draw all other sprites (this includes the player)
    all_sprites.draw(screen)

    # Draw the player and the gun
    player.draw(screen)

    # Draw the bullets
    bullets.draw(screen)


# ---------------------------------------------------------------
# Main game loop

# Show the title screen before starting the main game loop
title_screen()

# Initialize the bungerSpawn flag
bungerSpawn = False

# Initialize the start time and total paused time
start_time = pygame.time.get_ticks()
total_paused_time = 0
pause_start_time = None

# Main game loop
running = True
player_dead = False  # Track if the player is dead
paused = False  # Ensure paused starts as False
death_time = 0  # Track the time of death

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Check for pause menu
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if not paused and not player_dead:
                paused = True
                pause_start_time = pygame.time.get_ticks()

        # Handle pause button click
        if event.type == pygame.MOUSEBUTTONDOWN:
            if pause_button_rect.collidepoint(event.pos) and not player_dead:
                paused = True
                pause_start_time = pygame.time.get_ticks()

        # Shooting (left mouse click)
        if not player_dead and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            bullets_fired = player.shoot()
            if bullets_fired:
                for bullet in bullets_fired:
                    bullets.add(bullet)
                    all_sprites.add(bullet)

        # Spawn a new candy every 5 seconds
        if event.type == candy_spawn_event and not player_dead:
            candy = Candy('Pictures/Candy.png')
            Pickup.add(candy)
            all_sprites.add(candy)

        if event.type == bunger_spawn_event and bungerSpawn and not player_dead:
            print(f"Spawning {bunger_spawn_count} bungers.")  # Debugging statement
            for _ in range(bunger_spawn_count):  # Spawn multiple bungers based on the count
                bunger = Bunger('Pictures/BUNGER.png')
                Pickup.add(bunger)  # Add the Bunger to the Pickup group for collision detection
                all_sprites.add(bunger)  # Add the Bunger to the all_sprites group

        # Spawn a new slime every # seconds
        #if event.type == slime_spawn_event and not player_dead:
        #    slime = Slime()
        #    enemies.add(slime)
        #    all_sprites.add(slime)  # Add slime to both enemies and all_sprites

        # Spawn enemies according to the pool every # seconds
        if event.type == Enemy_Spawn_Timer and not player_dead:
            spawn_random_enemies(player)

        if event.type == Enemy_Spawn_Timer_Slow and not player_dead:
            spawn_random_enemies_Slow(player)

    # Pause menu logic
    if paused:
        result = pause_menu()
        if result == 'title_screen':
            reset_game()
            title_screen()
        paused = False

        if pause_start_time is not None:
            total_paused_time += pygame.time.get_ticks() - pause_start_time
            pause_start_time = None
    else:
        # Calculate the elapsed time
        if not player_dead:
            elapsed_time = (pygame.time.get_ticks() - start_time - total_paused_time) // 1000

        # Regular game update logic
        if not player_dead:
            keys = pygame.key.get_pressed()
            mouse_pos = pygame.mouse.get_pos()
            player.update(keys, obstacles, Pickup, Bunger, enemies, width, height, mouse_pos)

            if player.get_hp() <= 0 and not player_dead:
                player_dead = True
                death_time = elapsed_time
                result = Game_Jover(death_time)
                if result == 'title_screen':
                    reset_game()
                    title_screen()
                    paused = False
                player_dead = False

            # Update and move all enemies
            for enemy in enemies:
                enemy.move_towards_player(player)
                enemy.update()

            # Check for collisions between player and enemies
            enemy_collisions = pygame.sprite.spritecollide(player, enemies, False)
            for enemy in enemy_collisions:
                player.take_damage(enemy.damage)  # Apply enemy's damage to the player

            # Update bullets
            bullets.update()

            # Check for bullet collisions with enemies
            for bullet in bullets:
                enemy_hit_list = pygame.sprite.spritecollide(bullet, enemies, False)
                for enemy in enemy_hit_list:
                    enemy.enemy_take_damage(bullet.damage)
                    bullet.kill()

        # Draw the game state
        draw_GameUI()

        # Draw timer
        if player_dead:
            draw_timer(screen, death_time)
        else:
            draw_timer(screen, elapsed_time)

        # Update display
        pygame.display.flip()

        # Cap frame rate
        pygame.time.Clock().tick(60)

# Quit the game when the loop ends
pygame.quit()
sys.exit()










