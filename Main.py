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
    def __init__(self, name, image_path, bullet_image, damage, fire_rate, bullet_speed, spread_angle=0, projectile_count=1, automatic_fire=False, bullet_duration=2000, piercing=False):
        self.name = name
        self.gun_image_path = image_path  # Store image path for creating new instances
        self.original_image = pygame.image.load(image_path).convert_alpha()
        self.image = self.original_image.copy()
        self.bullet_image = bullet_image
        self.damage = damage
        self.fire_rate = fire_rate  # Cooldown between shots in milliseconds
        self.bullet_speed = bullet_speed
        self.spread_angle = spread_angle  # Spread angle for the bullets
        self.projectile_count = projectile_count  # Number of projectiles fired at once
        self.automatic_fire = automatic_fire  # Whether the gun can fire automatically
        self.bullet_duration = bullet_duration  # Duration of each projectile in milliseconds
        self.piercing = piercing  # Whether projectiles can pierce through enemies

# Define the Player Class
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

        # Base stats that upgrades will modify
        self.base_damage = 0  # Additional damage from upgrades
        self.base_fire_rate = 0  # Reduction in fire rate from upgrades

        # Store the original base values of gun attributes for cumulative upgrades
        self.gun_base_damage = gun.damage  # Base gun damage
        self.gun_base_fire_rate = gun.fire_rate  # Base gun fire rate

        # Apply upgrades initially
        self.apply_upgrades_to_gun()

        # Miniaturization attributes
        self.is_miniaturized = False  # Flag to track miniaturization
        self.cumulative_scale = 1.0  # Start with normal scale

    def equip_gun(self, gun):
        """Equip a new gun and apply player upgrades to it."""
        # Create a new gun instance to avoid modifying the global gun
        self.gun = Gun(
            gun.name, gun.gun_image_path, gun.bullet_image, gun.damage, gun.fire_rate,
            gun.bullet_speed, gun.spread_angle, gun.projectile_count, gun.automatic_fire,
            gun.bullet_duration, gun.piercing
        )
        self.gun_image = self.gun.image.copy()
        self.gun_rect = self.gun_image.get_rect()

        # Reset base attributes when equipping a new gun
        self.gun_base_damage = self.gun.damage
        self.gun_base_fire_rate = self.gun.fire_rate
        self.apply_upgrades_to_gun()  # Apply any base upgrades to the new gun

        # Apply miniaturization to the new gun if the player is miniaturized
        if self.is_miniaturized:
            # Scale the gun image
            new_width = int(self.gun.original_image.get_width() * self.cumulative_scale)
            new_height = int(self.gun.original_image.get_height() * self.cumulative_scale)
            self.gun_image = pygame.transform.scale(self.gun.original_image, (new_width, new_height))
            self.gun_rect = self.gun_image.get_rect(center=self.gun_rect.center)

    def apply_upgrades_to_gun(self):
        """Apply player upgrades to the equipped gun based on stored base values."""
        # Calculate final damage and fire rate using base values with upgrades
        self.gun.damage = self.gun_base_damage + self.base_damage
        self.gun.fire_rate = max(100, self.gun_base_fire_rate - self.base_fire_rate)  # Ensures minimum fire rate

        # Update turrets
        for turret in turrets:
            turret.apply_upgrades()

    def update(self, keys, obstacles, Pickup, Bunger, slimes, screen_width, screen_height, mouse_pos, mouse_held, Lollipop):
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
            elif isinstance(pickup, Lollipop):
                self.gain_xp(10)

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

        # Handle automatic firing
        if mouse_held and self.gun.automatic_fire:
            bullets = self.shoot()
            if bullets:
                return bullets

        return None

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
        self.check_level_up()

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

            # Spawn new bosses based on the player's level
            self.spawn_boss_based_on_level()

    def spawn_enemies_based_on_level(self):
        global enemies, all_sprites
        for level, EnemyClass in enemy_pool:
            if level <= self.level:
                new_enemy = EnemyClass()  # Don't pass player's cumulative_scale
                if self.is_miniaturized:
                    # Apply enemy cumulative scale to new enemies
                    new_enemy.apply_miniaturization(self.enemy_cumulative_scale)
                enemies.add(new_enemy)
                all_sprites.add(new_enemy)

    def spawn_boss_based_on_level(self):
        global enemies, all_sprites
        for level, BossClass in enemyBoss_pool:
            if level <= self.level:
                new_boss = BossClass()
                if self.is_miniaturized:
                    new_boss.apply_miniaturization(self.enemy_cumulative_scale)
                enemies.add(new_boss)
                all_sprites.add(new_boss)
                print(f"Boss {new_boss.__class__.__name__} spawned!")

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
        rotated_gun_image = pygame.transform.rotate(self.gun_image, angle)  # Use self.gun_image

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

            # Apply spread even for a single projectile by adding a random offset to the base angle
            if self.gun.projectile_count == 1:
                # Random spread offset within the range [-spread_angle, +spread_angle]
                spread_offset = math.radians(random.uniform(-self.gun.spread_angle, self.gun.spread_angle))
                angle = base_angle + spread_offset
                direction = (math.cos(angle), -math.sin(angle))

                # Create a single projectile with random spread
                bullet = Projectile(
                    self.gun_rect.center, direction,
                    self.gun.bullet_image, self.gun.bullet_speed,
                    self.gun.damage, self.gun.bullet_duration,
                    piercing=self.gun.piercing,
                    cumulative_scale=self.cumulative_scale
                )
                bullets.append(bullet)
            else:
                # Calculate spread for multi-projectile weapons as usual
                spread_radians = math.radians(self.gun.spread_angle)
                start_angle = base_angle - spread_radians * (self.gun.projectile_count - 1) / 2

                for i in range(self.gun.projectile_count):
                    angle = start_angle + i * spread_radians
                    direction = (math.cos(angle), -math.sin(angle))

                    bullet = Projectile(
                        self.gun_rect.center, direction,
                        self.gun.bullet_image, self.gun.bullet_speed,
                        self.gun.damage, self.gun.bullet_duration,
                        piercing=self.gun.piercing
                    )
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


class Projectile(pygame.sprite.Sprite):
    def __init__(self, pos, direction, image_path, speed, damage, duration=2000, piercing=False, cumulative_scale=1.0):
        super().__init__()
        self.original_image = pygame.image.load(image_path).convert_alpha()

        # Calculate the angle in degrees based on direction vector
        angle = math.degrees(math.atan2(-direction[1], direction[0]))

        # Rotate the image to face the direction
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=pos)

        self.damage = damage
        self.velocity = (direction[0] * speed, direction[1] * speed)
        self.piercing = piercing  # Set whether this projectile is piercing

        # Duration handling
        self.duration = duration  # Duration of projectile in milliseconds
        self.spawn_time = pygame.time.get_ticks()  # Record the time the projectile was created

        # Initialize cumulative scaling
        self.cumulative_scale = 1.0  # Start with no scaling

        # Rotate the original image based on direction
        angle = math.degrees(math.atan2(-direction[1], direction[0]))
        self.image = pygame.transform.rotate(self.original_image, angle)

        # Apply cumulative scaling if necessary
        if cumulative_scale != 1.0:
            self.apply_miniaturization(cumulative_scale)

        self.rect = self.image.get_rect(center=pos)

    def apply_miniaturization(self, scale_factor):
        """Shrink the projectile's image and rect by a cumulative scale factor."""
        self.cumulative_scale *= scale_factor
        # Scale the original image
        new_width = int(self.original_image.get_width() * self.cumulative_scale)
        new_height = int(self.original_image.get_height() * self.cumulative_scale)
        scaled_image = pygame.transform.scale(self.original_image, (new_width, new_height))
        # Rotate the scaled image
        angle = math.degrees(math.atan2(-self.velocity[1], self.velocity[0]))
        self.image = pygame.transform.rotate(scaled_image, angle)
        # Update the rect
        self.rect = self.image.get_rect(center=self.rect.center)

    def update(self):
        # Move the projectile
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]

        # Check if the projectile is out of screen bounds
        if self.rect.right < 0 or self.rect.left > width or self.rect.bottom < 0 or self.rect.top > height:
            self.kill()

        # Check if the duration has expired
        if pygame.time.get_ticks() - self.spawn_time > self.duration:
            self.kill()  # Remove projectile if duration has passed



#Pickup Classes ------------------------------------------------

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

# Define the Lolipop class
class Lollipop(pygame.sprite.Sprite):
    def __init__(self, image_path):
        super().__init__()
        self.image = pygame.image.load(image_path).convert_alpha()
        self.rect = self.image.get_rect()
        self.spawn_random()

    def spawn_random(self):
        self.rect.x = random.randint(0, width - self.rect.width)
        self.rect.y = random.randint(0, height - self.rect.height)

#------------------------------------------------

#Enemy Class
# Define the Enemy base class
class Enemy(pygame.sprite.Sprite):
    def __init__(self, image_path, speed, hp, damage, xp_reward, cumulative_scale=1.0):
        super().__init__()
        self.original_image = pygame.image.load(image_path).convert_alpha()
        self.cumulative_scale = cumulative_scale
        self.direction = 'right'  # Initialize enemy facing right

        # Enemy attributes
        self.hp = hp
        self.speed = speed
        self.damage = damage
        self.xp_reward = xp_reward

        # Damage blinking attributes
        self.is_blinking = False
        self.blink_duration = 500  # Increase to 500 milliseconds
        self.blink_start_time = 0

        # Initialize image and rect
        self.image = self.original_image
        self.rect = self.image.get_rect()  # Define self.rect here
        self.update_scaled_image()

        # Set initial position (e.g., spawn within the screen)
        self.spawn_within_screen()


    def spawn_within_screen(self):
        """Spawn enemy at a random position within the screen."""
        self.rect.x = random.randint(0, width - self.rect.width)
        self.rect.y = random.randint(0, height - self.rect.height)

    def move_towards_player(self, player):
        """Moves the enemy towards the player while preserving scale and flipping based on direction."""
        direction_x = player.rect.x - self.rect.x
        direction_y = player.rect.y - self.rect.y
        distance = math.hypot(direction_x, direction_y)

        # Flip based on movement direction and update the image accordingly
        if direction_x < 0 and self.direction != 'left':
            self.direction = 'left'
            self.update_scaled_image()  # Update the image to reflect the direction change
        elif direction_x > 0 and self.direction != 'right':
            self.direction = 'right'
            self.update_scaled_image()

        if distance > 0:
            direction_x /= distance
            direction_y /= distance

        # Move the enemy towards the player
        self.rect.x += int(direction_x * self.speed)
        self.rect.y += int(direction_y * self.speed)

    def enemy_take_damage(self, damage, player):
        """Handles damage and triggers blinking effect without resetting size."""
        self.hp -= damage
        print(f"{self.__class__.__name__} took {damage} damage. Current HP: {self.hp}")

        # Trigger the blinking effect without altering the size
        self.is_blinking = True
        self.blink_start_time = pygame.time.get_ticks()

        # Reapply the image with the current cumulative scale
        self.update_scaled_image()
        tinted_image = self.image.copy()
        tinted_image.fill((255, 0, 0), special_flags=pygame.BLEND_ADD)  # Apply red tint
        self.image = tinted_image  # Assign the tinted image as current

        if self.hp <= 0:
            player.gain_xp(self.xp_reward)
            print(f"Player gained {self.xp_reward} XP for killing {self.__class__.__name__}")
            self.kill()  # Remove the enemy when HP reaches 0

    def update(self):
        # Handle blinking effect
        if self.is_blinking:
            current_time = pygame.time.get_ticks()
            if current_time - self.blink_start_time > self.blink_duration:
                self.is_blinking = False
                # Restore the original image while keeping the miniaturization scale
                self.update_scaled_image()

    def apply_miniaturization(self, scale_factor):
        """Shrink an enemy's image and rect by a new scale factor."""
        self.cumulative_scale *= scale_factor  # Accumulate the scaling
        print(f"Applying miniaturization to {self.__class__.__name__} with scale factor {scale_factor}")
        self.update_scaled_image()  # Update the image based on the new scale

    def update_scaled_image(self):
        """Update the enemy's image and rect based on the current cumulative scale and direction."""
        new_width = int(self.original_image.get_width() * self.cumulative_scale)
        new_height = int(self.original_image.get_height() * self.cumulative_scale)
        self.miniaturized_image = pygame.transform.scale(self.original_image, (new_width, new_height))

        # Adjust the image based on the enemy's current direction
        if self.direction == 'left':
            self.image = pygame.transform.flip(self.miniaturized_image, True, False)
        else:
            self.image = self.miniaturized_image

        # Adjust rect to match new image size, keeping the center consistent
        if hasattr(self, 'rect'):
            center = self.rect.center
        else:
            center = None
        self.rect = self.image.get_rect()
        if center is not None:
            self.rect.center = center


# Define the Slime class (inherits from Enemy) ----------------------------
class Slime(Enemy):
    def __init__(self, cumulative_scale=1.0):
        super().__init__('Pictures/Slime.png', speed=2, hp=10, damage=10, xp_reward=10, cumulative_scale=cumulative_scale)  # Set slime's damage to 10
        self.spawn_within_screen()

class BlueSlime(Enemy):
    def __init__(self, cumulative_scale=1.0):
        super().__init__('Pictures/BlueSlime.png', speed=3, hp=15, damage=15, xp_reward=20, cumulative_scale=cumulative_scale)  # Set blue slime's damage to 15
        self.spawn_within_screen()

class Golem(Enemy):
    def __init__(self, cumulative_scale=1.0):
        super().__init__('Pictures/Golem.png', speed=2, hp=100, damage=50, xp_reward=50, cumulative_scale=cumulative_scale)  # Make sure to inherit properly
        self.spawn_within_screen()


class FastFish(Enemy):
    def __init__(self, cumulative_scale=1.0):
        super().__init__('Pictures/FastFish.png', speed=5, hp=5, damage=5, xp_reward=150, cumulative_scale=cumulative_scale)  # Set fast fish's damage to 5
        self.spawn_within_screen()

class OrangeSlime(Enemy):
    def __init__(self, cumulative_scale=1.0):
        super().__init__('Pictures/OrangeSlime.png', speed=3, hp=150, damage=25, xp_reward=100, cumulative_scale=cumulative_scale)
        self.spawn_within_screen()

class ZapOrb(Enemy):
    def __init__(self, cumulative_scale=1.0):
        super().__init__('Pictures/ZapOrb.png', speed=2, hp=300, damage=50, xp_reward=200, cumulative_scale=cumulative_scale)
        self.spawn_within_screen()

class RedSlime(Enemy):
    def __init__(self, cumulative_scale=1.0):
        super().__init__('Pictures/RedSlime.png', speed=2, hp=400, damage=30, xp_reward=300, cumulative_scale=cumulative_scale)
        self.spawn_within_screen()



# Enemy pool where each entry is a tuple of (level, EnemyClass)
enemy_pool = [
    (1, Slime),  # Slime starts appearing at level 1
    (2, Slime),  # Add more enemy types for higher levels
    (4, BlueSlime),
    (5, Slime),
    (7, OrangeSlime),
    (8, BlueSlime),
    (9, ZapOrb),
    (10, FastFish),
    (11, RedSlime),
    (12, RedSlime),
    (13, OrangeSlime),
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
    return [BossClass for lvl, BossClass in enemyBoss_pool if lvl <= level]

def spawn_random_enemies(player):
    """Spawn regular enemies based on the player's level and the enemy pool."""
    global enemies, all_sprites

    # Dictionary to keep track of how many of each enemy type to spawn
    enemies_to_spawn = {}

    # Determine which regular enemies to spawn based on the player's current level
    for level, EnemyClass in enemy_pool:
        if player.level >= level:
            if EnemyClass in enemies_to_spawn:
                enemies_to_spawn[EnemyClass] += 1
            else:
                enemies_to_spawn[EnemyClass] = 1

    # Spawn the regular enemies according to the count in enemies_to_spawn
    for EnemyClass, count in enemies_to_spawn.items():
        for _ in range(count):
            new_enemy = EnemyClass()
            if player.is_miniaturized:
                new_enemy.apply_miniaturization(player.enemy_cumulative_scale)
            enemies.add(new_enemy)
            all_sprites.add(new_enemy)


def spawn_boss_enemies(player):
    """Spawn boss enemies based on the player's level and the boss enemy pool."""
    global enemies, all_sprites

    # Dictionary to keep track of how many of each boss type to spawn
    bosses_to_spawn = {}

    # Determine which bosses to spawn based on the player's current level
    for level, BossClass in enemyBoss_pool:
        if player.level >= level:
            if BossClass in bosses_to_spawn:
                bosses_to_spawn[BossClass] += 1
            else:
                bosses_to_spawn[BossClass] = 1

    # Spawn the bosses according to the count in bosses_to_spawn
    for BossClass, count in bosses_to_spawn.items():
        for _ in range(count):
            new_boss = BossClass()
            if player.is_miniaturized:
                new_boss.apply_miniaturization(player.enemy_cumulative_scale)
            enemies.add(new_boss)
            all_sprites.add(new_boss)
            print(f"Boss {new_boss.__class__.__name__} spawned!")  # Debugging print



# Replace slimes group with a generic enemies group
enemies = pygame.sprite.Group()

# Initialize the turrets group
turrets = pygame.sprite.Group()


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
    # Set bar width as an integer to avoid mismatch
    bar_width = 150  # Adjust this to the desired length for the HP bar
    bar_height = 15
    bar_x = 15
    bar_y = 70

    # Calculate the fill width based on current HP
    fill_width = int(bar_width * (player.get_hp() / player.max_hp))

    # Draw the background (gray) and the filled (red) parts of the HP bar
    pygame.draw.rect(screen, gray, (bar_x, bar_y, bar_width, bar_height))  # Full gray background
    pygame.draw.rect(screen, red, (bar_x, bar_y, fill_width, bar_height))  # Filled red part based on HP

    # Draw HP text
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
pistol = Gun("Pistol", 'Pictures/Pistol.png', 'Pictures/Bullet1.png', damage=5, fire_rate=400, bullet_speed=10, spread_angle=1, projectile_count=1, automatic_fire=False, bullet_duration=2000, piercing=False)
katana = Gun("Katana", 'Pictures/Katana.png', 'Pictures/Slash.png', damage=2, fire_rate=250, bullet_speed=10, spread_angle=20, projectile_count=1, automatic_fire=True, bullet_duration=100, piercing=True)
shotgun = Gun("Shotgun", 'Pictures/Shotgun.png', 'Pictures/Bullet1.png', damage=4, fire_rate=1000, bullet_speed=10, spread_angle=10, projectile_count=5, automatic_fire=False, bullet_duration=2000, piercing=False)
peashooter = Gun("Peashooter", 'Pictures/Peashooter.png', 'Pictures/Bullet2.png', damage=1, fire_rate=50, bullet_speed=10, spread_angle=5, projectile_count=1, automatic_fire=True, bullet_duration=2000, piercing=False)
voidbook = Gun("Voidbook", 'Pictures/VoidBook.png', 'Pictures/VoidOrb.png', damage=1, fire_rate=2000,bullet_speed=1.5, spread_angle=1, projectile_count=1, automatic_fire=False, bullet_duration=4000, piercing=True)

#Turret class ------------------------------------------------

class TurretType:
    def __init__(self, name, image_path, bullet_image, damage, fire_rate, bullet_speed,
                 spread_angle=0, projectile_count=1, piercing=False, bullet_duration=2000):
        self.name = name
        self.image_path = image_path  # Path to the turret's image
        self.original_image = pygame.image.load(image_path).convert_alpha()
        self.bullet_image = bullet_image  # Path to the bullet image
        self.damage = damage
        self.fire_rate = fire_rate  # Cooldown between shots in milliseconds
        self.bullet_speed = bullet_speed
        self.spread_angle = spread_angle  # Spread angle for bullets
        self.projectile_count = projectile_count  # Number of projectiles fired at once
        self.piercing = piercing  # Whether projectiles can pierce through enemies
        self.bullet_duration = bullet_duration  # Duration of each projectile in milliseconds

class Turret(pygame.sprite.Sprite):
    def __init__(self, x, y, turret_type, player):
        super().__init__()
        self.player = player  # Reference to the player to access upgrades
        self.turret_type = turret_type  # The type of turret
        self.original_image = turret_type.original_image.copy()
        self.scaled_image = self.original_image.copy()  # Initialize scaled_image
        self.image = self.scaled_image.copy()
        self.rect = self.image.get_rect(center=(x, y))

        # Turret attributes
        self.base_damage = turret_type.damage  # Base damage
        self.base_fire_rate = turret_type.fire_rate  # Base fire rate in milliseconds
        self.bullet_speed = turret_type.bullet_speed  # Speed of the bullets
        self.last_shot_time = 0  # Last time the turret fired

        # Bullet properties
        self.bullet_image = turret_type.bullet_image
        self.spread_angle = turret_type.spread_angle
        self.projectile_count = turret_type.projectile_count
        self.piercing = turret_type.piercing
        self.bullet_duration = turret_type.bullet_duration

        # Rotation variables
        self.angle = 0  # Current rotation angle

        # Miniaturization attributes
        self.cumulative_scale = 1.0  # Start with normal scale
        self.is_miniaturized = False

        # Apply player upgrades initially
        self.apply_upgrades()

    def apply_upgrades(self):
        """Apply the player's damage and attack speed upgrades to the turret."""
        self.damage = self.base_damage + self.player.base_damage
        self.fire_rate = max(100, self.base_fire_rate - self.player.base_fire_rate)

    def apply_miniaturization(self, scale_factor):
        """Apply miniaturization effect to the turret."""
        self.cumulative_scale *= scale_factor
        new_width = int(self.original_image.get_width() * self.cumulative_scale)
        new_height = int(self.original_image.get_height() * self.cumulative_scale)
        self.scaled_image = pygame.transform.scale(self.original_image, (new_width, new_height))
        self.image = self.scaled_image
        self.rect = self.image.get_rect(center=self.rect.center)

    def update(self):
        """Update the turret's rotation and shooting."""
        # Apply upgrades
        self.apply_upgrades()

        # Find the nearest enemy
        if enemies:
            nearest_enemy = min(enemies, key=lambda enemy: self.get_distance(enemy))
            # Calculate the angle to the enemy
            rel_x, rel_y = nearest_enemy.rect.centerx - self.rect.centerx, nearest_enemy.rect.centery - self.rect.centery
            angle = math.degrees(math.atan2(-rel_y, rel_x))
            self.angle = angle
            # Rotate the turret image using the scaled image
            rotated_image = pygame.transform.rotate(self.scaled_image, angle)
            self.image = rotated_image
            self.rect = self.image.get_rect(center=self.rect.center)

            # Shooting
            current_time = pygame.time.get_ticks()
            if current_time - self.last_shot_time >= self.fire_rate:
                self.shoot(nearest_enemy)
                self.last_shot_time = current_time

    def get_distance(self, enemy):
        dx = enemy.rect.centerx - self.rect.centerx
        dy = enemy.rect.centery - self.rect.centery
        return math.hypot(dx, dy)

    def shoot(self, target):
        """Shoot bullet(s) at the target."""
        # Calculate base angle to target
        rel_x, rel_y = target.rect.centerx - self.rect.centerx, target.rect.centery - self.rect.centery
        base_angle = math.atan2(-rel_y, rel_x)

        bullets_fired = []
        spread_radians = math.radians(self.spread_angle)

        if self.projectile_count == 1:
            # Single projectile with possible random spread
            spread_offset = random.uniform(-spread_radians / 2, spread_radians / 2)
            angle = base_angle + spread_offset
            direction = (math.cos(angle), -math.sin(angle))
            bullet = Projectile(
                self.rect.center, direction,
                self.bullet_image, self.bullet_speed,
                self.damage, self.bullet_duration,
                piercing=self.piercing,
                cumulative_scale=self.cumulative_scale
            )
            bullets_fired.append(bullet)
        else:
            # Multiple projectiles with spread
            start_angle = base_angle - spread_radians * (self.projectile_count - 1) / 2
            for i in range(self.projectile_count):
                angle = start_angle + i * spread_radians
                direction = (math.cos(angle), -math.sin(angle))
                bullet = Projectile(
                    self.rect.center, direction,
                    self.bullet_image, self.bullet_speed,
                    self.damage, self.bullet_duration,
                    piercing=self.piercing,
                    cumulative_scale=self.cumulative_scale
                )
                bullets_fired.append(bullet)

        for bullet in bullets_fired:
            bullets.add(bullet)
            all_sprites.add(bullet)

# Create turret types ------------------------------------------------

# Create turret types
mg_turret_type = TurretType(
    "MG Turret",
    'Pictures/MGturret.png',
    'Pictures/Bullet1.png',
    damage=5,
    fire_rate=500,
    bullet_speed=10,
    spread_angle=0,
    projectile_count=1,
    piercing=False
)

sniper_turret_type = TurretType(
    "Sniper Turret",
    'Pictures/Sniperturret.png',
    'Pictures/Bullet3.png',
    damage=20,
    fire_rate=2000,
    bullet_speed=75,
    spread_angle=0,
    projectile_count=1,
    piercing=True
)


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

# Timer to spawn regular enemies every X seconds
Enemy_Spawn_Timer = pygame.USEREVENT + 2
pygame.time.set_timer(Enemy_Spawn_Timer, 5000)  # Regular enemies every 5 seconds

# Timer to spawn bosses every Y seconds (separate timer)
Boss_Spawn_Timer = pygame.USEREVENT + 3
pygame.time.set_timer(Boss_Spawn_Timer, 30000)  # Bosses every 30 seconds

# Timer to spawn Bunger every 15 seconds
bunger_spawn_event = pygame.USEREVENT + 4
pygame.time.set_timer(bunger_spawn_event, 15000)

# Timer to spawn Lollipop every 10 seconds
lollipop_spawn_event = pygame.USEREVENT + 5
pygame.time.set_timer(lollipop_spawn_event, 10000)

# Set up a timer for bandage healing every 10 seconds
bandage_heal_event = pygame.USEREVENT + 6  # Unique event ID for bandage healing
pygame.time.set_timer(bandage_heal_event, 10000)  # Trigger every 10 seconds

# Set up a timer for healing needle every 1 seconds
healing_needle_event = pygame.USEREVENT + 7  # Unique event ID for healing needle
pygame.time.set_timer(healing_needle_event, 1000)  # Trigger every 1 seconds

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


#Full screen checkbox funtion ------------------------------------------------

class Fullscreen_Checkbox:
    def __init__(self, x, y, size=20, checked=False):
        self.rect = pygame.Rect(x, y, size, size)
        self.checked = checked

    def draw(self, screen):
        # Draw the checkbox outline
        pygame.draw.rect(screen, black, self.rect, 2)
        # Fill the checkbox if it's checked
        if self.checked:
            pygame.draw.rect(screen, green, self.rect.inflate(-4, -4))

    def handle_event(self, event):
        # Toggle checked state on mouse click within checkbox area
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.checked = not self.checked
            return self.checked
        return None


#Pause menu function ------------------------------------------------

# Initialize paused flag
paused = False  # Game starts in running state

# Initialize the fullscreen_mode as a global variable
fullscreen_mode = False  # Track the fullscreen mode state globally

# Define the pause menu function
def pause_menu():
    """Pause menu with a transparent background, title, resume, and quit buttons, plus a fullscreen toggle checkbox."""
    global fullscreen_mode  # Use the global variable to persist the state
    button_width = 150
    button_height = 40
    resume_button = pygame.Rect(width // 2 - button_width // 2, height // 2 - 70, button_width, button_height)
    titlescreen_button = pygame.Rect(width // 2 - button_width // 2, height // 2 - 10, button_width, button_height)
    quit_button = pygame.Rect(width // 2 - button_width // 2, height // 2 + 50, button_width, button_height)

    # Initialize the checkbox with the current fullscreen state
    checkbox = Fullscreen_Checkbox(width // 2 - 100, height // 2 + 120, size=20, checked=fullscreen_mode)

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

        # Draw checkbox with fullscreen label
        checkbox.draw(screen)
        fullscreen_text = font.render("Fullscreen Mode", True, black)
        screen.blit(fullscreen_text, (checkbox.rect.right + 10, checkbox.rect.top))

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

            # Check for checkbox interaction and toggle fullscreen
            checkbox_state = checkbox.handle_event(event)
            if checkbox_state is not None:
                fullscreen_mode = checkbox_state  # Update the global state
                if fullscreen_mode:
                    pygame.display.set_mode((width, height), pygame.FULLSCREEN)
                else:
                    pygame.display.set_mode((width, height))

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
        if self.name == "Lollipop Rain":
            enable_lollipop_spawn(player)
        else:
            self.effect(player)

        # Add upgrade to the player's inventory
        player.add_upgrade_to_inventory(self.name, self.logo_image)


# Upgrade effects
def increase_damage(player):
    player.base_damage += 5
    player.apply_upgrades_to_gun()  # Update the equipped weapon

# This will increase the player's movement speed by 1
def increase_speed(player):
    player.speed += 1

# This will improve the fire rate of the gun (reduce time between shots)
def increase_attackSpeed(player):
    player.base_fire_rate += 50  # Modify base fire rate directly
    player.apply_upgrades_to_gun()  # Apply upgrade to the equipped gun's fire rate

# Increase health and max health
def increase_health(player):
    player.max_hp += 50
    player.hp = min(player.hp + 50, player.max_hp)  # Increase HP up to the new max

bunger_spawn_count = 0  # Initialize the counter for Bunger Rain upgrade

def enable_bunger_spawn(player):
    global bungerSpawn, bunger_spawn_count
    bungerSpawn = True
    bunger_spawn_count += 1  # Increase the count each time the upgrade is selected
    print(f"Bunger Rain upgrade activated! Bungers will spawn at level {bunger_spawn_count}.")

lollipop_spawn_count = 0  # Initialize the counter for Lollipop Rain upgrade

def enable_lollipop_spawn(player):
    global lollipopSpawn, lollipop_spawn_count
    lollipopSpawn = True
    lollipop_spawn_count += 1
    print(f"Lollipop Rain upgrade activated! Lollipops will spawn at level {lollipop_spawn_count}.")

# Add a global variable to track bandage upgrades
bandage_count = 0  # Initialize the count of Bandage upgrades

# Define the Bandage upgrade effect
def apply_bandage(player):
    global bandage_count
    bandage_count += 1  # Increment the count of Bandage upgrades
    print(f"Bandage upgrade applied! Healing 10 HP every 10 seconds. Current Bandages: {bandage_count}")

# Add a global variable to track healing needle upgrade
needle_count = 0

# Define the Healing Needle upgrade effect
def apply_healing_needle(player):
    global needle_count
    needle_count += 1
    print(f"Healing Needle upgrade applied! Healing 50 HP instantly. Current Needles: {needle_count}")


# Function to apply miniaturization effect to all entities
def miniaturize_entities(player):
    global enemies, bullets, turrets
    """Shrink player, enemies, turrets, and projectiles by consistent but adjustable scale factors."""
    player_scale_factor = 0.95  # Shrink player by 5%
    enemy_scale_factor = 0.9    # Shrink enemies by 10%
    bullet_scale_factor = player_scale_factor  # Bullets scale with player

    # Update cumulative scaling factor for player
    player.cumulative_scale *= player_scale_factor

    # Initialize enemy_cumulative_scale if not already
    if not hasattr(player, 'enemy_cumulative_scale'):
        player.enemy_cumulative_scale = 1.0
    player.enemy_cumulative_scale *= enemy_scale_factor

    # Miniaturize the player using cumulative scale
    new_width = int(player.original_image.get_width() * player.cumulative_scale)
    new_height = int(player.original_image.get_height() * player.cumulative_scale)
    player.image = pygame.transform.scale(player.original_image, (new_width, new_height))
    player.rect = player.image.get_rect(center=player.rect.center)
    player.original_image = player.image.copy()

    # Set flag to indicate that miniaturization is active
    player.is_miniaturized = True

    # Miniaturize all existing enemies
    for enemy in enemies:
        enemy.apply_miniaturization(enemy_scale_factor)

    # Miniaturize all current projectiles
    for bullet in bullets:
        bullet.apply_miniaturization(bullet_scale_factor)

    # Miniaturize all existing turrets
    for turret in turrets:
        turret.apply_miniaturization(player_scale_factor)

    # Miniaturize the gun
    apply_gun_miniaturization(player, player_scale_factor)



# def apply_miniaturization(self, scale_factor):
#     """Shrink an enemy's image and rect by a new scale factor."""
#     self.cumulative_scale *= scale_factor  # Accumulate the scaling
#     self.update_scaled_image()  # Update the image based on the new scale
#
#     # Adjust the image based on the enemy's current direction
#     if self.direction == 'left':
#         self.image = pygame.transform.flip(self.miniaturized_image, True, False)
#     else:
#         self.image = self.miniaturized_image
#     self.rect = self.image.get_rect(center=self.rect.center)


def apply_shrink_to_bullet(bullet, scale_factor):
    """Apply shrink effect to an individual bullet."""
    bullet.image = pygame.transform.scale(bullet.image, (int(bullet.rect.width * scale_factor), int(bullet.rect.height * scale_factor)))
    bullet.rect = bullet.image.get_rect(center=bullet.rect.center)

def apply_gun_miniaturization(player, scale_factor):
    """Shrink the player's gun image and adjust position."""
    player.gun_distance_from_player *= scale_factor  # Adjust the gun distance

    # Scale the gun image
    new_width = int(player.gun.original_image.get_width() * player.cumulative_scale)
    new_height = int(player.gun.original_image.get_height() * player.cumulative_scale)
    player.gun_image = pygame.transform.scale(player.gun.original_image, (new_width, new_height))
    player.gun_rect = player.gun_image.get_rect(center=player.gun_rect.center)

# Weapon Upgrades ------------------------------------------------

# Function to swap the player's weapon to Katana
def swap_to_katana(player):
    player.equip_gun(katana)
    print("Player swapped to Katana!")

def swap_to_pistol(player):
    player.equip_gun(pistol)
    print("Player swapped to Pistol!")

def swap_to_shotgun(player):
    player.equip_gun(shotgun)
    print("Player swapped to Shotgun!")

def swap_to_peashooter(player):
    player.equip_gun(peashooter)
    print("Player swapped to Peashooter!")

def swap_to_voidbook(player):
    player.equip_gun(voidbook)
    print("Player swapped to Voidbook!")

# turret upgrades ------------------------------------------------

def deploy_turret(player, turret_type):
    # Create a turret at the player's position
    turret = Turret(player.rect.centerx, player.rect.centery, turret_type, player)
    turrets.add(turret)
    all_sprites.add(turret)

    # Add the turret to the player's inventory
    player.add_upgrade_to_inventory(turret_type.name, turret_type.original_image)


# Upgrade Pool
upgrades_pool = [
    Upgrade("Speed Boost", "Increases player's speed by 1.", increase_speed, 'Pictures/Boot.png'),
    Upgrade("Damage Boost", "Increases gun damage by 5.", increase_damage, 'Pictures/DamagePlus.png'),
    Upgrade("Health Boost", "Increases max health by 50 and heals 50 HP.", increase_health, 'Pictures/HealCross.png'),
    Upgrade("Bunger Rain", "Bungers will start raining down!", enable_bunger_spawn, 'Pictures/Bunger.png'),
    Upgrade("Attack Speed", "Increases attack speed by 50.", increase_attackSpeed, 'Pictures/AttackSpeed.png'),
    Upgrade("Lollipop Rain", "Lollipops will start raining down!", enable_lollipop_spawn, 'Pictures/Lollipop.png'),
    Upgrade("Katana", "Swap to the Katana weapon!", swap_to_katana, 'Pictures/Katana.png'),
    Upgrade("Pistol", "WHY???", swap_to_pistol, 'Pictures/Pistol.png'),
    Upgrade("Shotgun", "Gun that goes Boom!", swap_to_shotgun, 'Pictures/Shotgun.png'),
    Upgrade("Peashooter", "Gun that goes Pew rapidly!", swap_to_peashooter, 'Pictures/Peashooter.png'),
    Upgrade("Miniaturization", "Shrink everything by 10%.", miniaturize_entities, 'Pictures/SizeShrink.png'),
    Upgrade("Bandage", "Heals 10 HP every 10 seconds. Stacks with each upgrade.", apply_bandage, 'Pictures/Bandage.png'),
    Upgrade("Healing Needle", "Heals 1 HP every 1 second. Stacks with each upgrade.", apply_healing_needle, 'Pictures/Needle.png'),
    Upgrade("Voidbook", "Swap to the Voidbook weapon!", swap_to_voidbook, 'Pictures/VoidBook.png'),
    Upgrade("Deploy MG Turret", "Deploys an MG Turret that shoots at enemies.", lambda player: deploy_turret(player, mg_turret_type), 'Pictures/MGturret.png'),
    Upgrade("Deploy Sniper Turret", "Deploys a Sniper Turret that deals high damage to enemies.", lambda player: deploy_turret(player, sniper_turret_type), 'Pictures/Sniperturret.png')
]


# Function to select random upgrades from the pool
import random
def select_random_upgrades(upgrades_pool, count=4):
    return random.sample(upgrades_pool, min(count, len(upgrades_pool)))


def Upgrade_Page(player):
    """Upgrade page that appears on leveling up."""
    button_width = 200
    button_height = 40
    selected_upgrades = select_random_upgrades(upgrades_pool, 4)  # Shows up to 4 upgrade options
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
                        upgrade.apply(player)  # Apply the selected upgrade
                        return  # Exit the upgrade page after selection



# Reset the game state ------------------------------------------------
def reset_game():
    """Reset the game state to its initial configuration."""
    global player, all_sprites, bullets, Pickup, enemies, obstacles, turrets
    global start_time, total_paused_time, pause_start_time, paused, player_dead
    global bungerSpawn, bunger_spawn_count, lollipopSpawn, lollipop_spawn_count, bandage_count, needle_count
    global pistol, katana, shotgun, peashooter, voidbook  # Include global gun instances

    # Clear all sprite groups to ensure no lingering objects
    all_sprites.empty()
    bullets.empty()
    Pickup.empty()
    enemies.empty()
    obstacles.empty()
    turrets.empty()  # Properly clear the turrets group

    # Reset global upgrade flags and counters
    bungerSpawn = False
    bunger_spawn_count = 0
    lollipopSpawn = False
    lollipop_spawn_count = 0
    bandage_count = 0
    needle_count = 0

    # Recreate the guns to reset their attributes
    pistol = Gun("Pistol", 'Pictures/Pistol.png', 'Pictures/Bullet1.png', damage=5, fire_rate=400,
                 bullet_speed=10, spread_angle=1, projectile_count=1, automatic_fire=False,
                 bullet_duration=2000, piercing=False)
    katana = Gun("Katana", 'Pictures/Katana.png', 'Pictures/Slash.png', damage=2, fire_rate=250,
                 bullet_speed=10, spread_angle=20, projectile_count=1, automatic_fire=True,
                 bullet_duration=100, piercing=True)
    shotgun = Gun("Shotgun", 'Pictures/Shotgun.png', 'Pictures/Bullet1.png', damage=4, fire_rate=1000,
                  bullet_speed=10, spread_angle=10, projectile_count=5, automatic_fire=False,
                  bullet_duration=2000, piercing=False)
    peashooter = Gun("Peashooter", 'Pictures/Peashooter.png', 'Pictures/Bullet2.png', damage=1, fire_rate=50,
                     bullet_speed=10, spread_angle=5, projectile_count=1, automatic_fire=True,
                     bullet_duration=2000, piercing=False)
    voidbook = Gun("Voidbook", 'Pictures/VoidBook.png', 'Pictures/VoidOrb.png', damage=1, fire_rate=2000,
                   bullet_speed=1.5, spread_angle=1, projectile_count=1, automatic_fire=False, bullet_duration=4000,
                   piercing=True)

    # Recreate the player instance with default attributes and upgrades reset
    player = Player(640, 360, 'Pictures/Morp.png', pistol)
    player.inventory = {}       # Reset the inventory
    player.speed = 3            # Reset player speed
    player.max_hp = 100         # Reset player max HP
    player.hp = 100             # Reset player HP to max HP
    player.base_damage = 0      # Reset base damage
    player.base_fire_rate = 0   # Reset base fire rate

    # Reset gun's base damage and fire rate to the default weapon values
    player.gun_base_damage = pistol.damage  # Use the initial gun's damage as the base value
    player.gun_base_fire_rate = pistol.fire_rate  # Reset base fire rate
    player.apply_upgrades_to_gun()  # Ensure gun is reset with no upgrades

    all_sprites.add(player)  # Add player to the all_sprites group

    # Reset the sprite groups
    bullets = pygame.sprite.Group()
    Pickup = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    obstacles = pygame.sprite.Group()
    turrets = pygame.sprite.Group()

    # Reset the game timer
    start_time = pygame.time.get_ticks()
    total_paused_time = 0
    pause_start_time = None

    # Reset paused and player dead states
    paused = False
    player_dead = False

    # Reset miniaturization attributes
    player.is_miniaturized = False
    player.cumulative_scale = 1.0
    if hasattr(player, 'enemy_cumulative_scale'):
        player.enemy_cumulative_scale = 1.0


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

# Initialize the lollipopSpawn flag
lollipopSpawn = False

# Initialize the start time and total paused time
start_time = pygame.time.get_ticks()
total_paused_time = 0
pause_start_time = None

# Main game loop
# Main game loop
running = True
player_dead = False  # Track if the player is dead
paused = False  # Ensure paused starts as False
death_time = 0  # Track the time of death

# Create a clock to manage frame rate
clock = pygame.time.Clock()

while running:

    mouse_held = pygame.mouse.get_pressed()[0]  # Check if the left mouse button is held

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

        # Manual shooting (left mouse click)
        if not player_dead and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Fire only on mouse click if automatic fire is off
            if not player.gun.automatic_fire:
                bullets_fired = player.shoot()  # This handles a single click shoot
                if bullets_fired:
                    for bullet in bullets_fired:
                        bullets.add(bullet)
                        all_sprites.add(bullet)

        # Spawn a new candy every 5 seconds
        if event.type == candy_spawn_event and not player_dead:
            candy = Candy('Pictures/Candy.png')
            Pickup.add(candy)
            all_sprites.add(candy)

        # Spawn Bungers if Bunger Rain upgrade is active
        if event.type == bunger_spawn_event and bungerSpawn and not player_dead:
            print(f"Spawning {bunger_spawn_count} bungers.")  # Debugging statement
            for _ in range(bunger_spawn_count):  # Spawn multiple bungers based on the count
                bunger = Bunger('Pictures/BUNGER.png')
                Pickup.add(bunger)  # Add the Bunger to the Pickup group for collision detection
                all_sprites.add(bunger)  # Add the Bunger to the all_sprites group

        # Spawn Lollipops if Lollipop Rain upgrade is active
        if event.type == lollipop_spawn_event and lollipopSpawn and not player_dead:
            print(f"Spawning {lollipop_spawn_count} lollipops.")
            for _ in range(lollipop_spawn_count):
                Lollipop = Candy('Pictures/Lollipop.png')
                Pickup.add(Lollipop)
                all_sprites.add(Lollipop)

        # Handle bandage healing event
        if event.type == bandage_heal_event and bandage_count > 0:
            heal_amount = 10 * bandage_count  # Heal amount scales with bandage count
            player.gain_HP(heal_amount)  # Heal the player
            print(f"Bandage healed {heal_amount} HP. Current HP: {player.hp}")

        # Handle healing needle event
        if event.type == healing_needle_event and needle_count > 0:
            heal_amount = 1 * needle_count
            player.gain_HP(heal_amount)
            print(f"Healing needle healed {heal_amount} HP. Current HP: {player.hp}")

        # Inside the main game loop:
        if event.type == Enemy_Spawn_Timer and not player_dead:
            player.spawn_enemies_based_on_level()

        # Spawn boss enemies every 30 seconds or based on level
        if event.type == Boss_Spawn_Timer and not player_dead:
            player.spawn_boss_based_on_level()

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

            # Player automatic shooting check
            if mouse_held and player.gun.automatic_fire:
                new_bullets = player.shoot()
                if new_bullets:
                    for bullet in new_bullets:
                        bullets.add(bullet)
                        all_sprites.add(bullet)

            # Update player and other elements
            player.update(keys, obstacles, Pickup, Bunger, enemies, width, height, mouse_pos, mouse_held, Lollipop)

            if player.get_hp() <= 0 and not player_dead:
                player_dead = True
                death_time = elapsed_time
                result = Game_Jover(death_time)
                if result == 'title_screen':
                    reset_game()
                    title_screen()
                    paused = False
                player_dead = False

            # Update and move all turrets
            turrets.update()

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
                    enemy.enemy_take_damage(bullet.damage, player)  # Pass the player to award XP on enemy death

                    # Only kill the bullet if it's not piercing
                    if not bullet.piercing:
                        bullet.kill()  # Remove the bullet once it hits an enemy if it's not piercing

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
        clock.tick(60)  # Ensure the game runs at 60 FPS

# Quit the game when the loop ends
pygame.quit()
sys.exit()










