import pygame
import sys
import random

# Initialize Pygame
pygame.init()

# Set up the display
width, height = 1280, 720
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Morp(1)")

# Define colors
white = (255, 255, 255)
black = (0, 0, 0)
green = (0, 255, 0)
red = (255, 0, 0)
blue = (0, 0, 255)
gray = (128, 128, 128)

# Define the Player class
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, image_path):
        super().__init__()
        # Use the parameters passed to the constructor for position and image path
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
        self.direction = 'right'

        # XP and Leveling attributes
        self.level = 1
        self.xp = 0
        self.xp_needed = 100  # Initial XP required to level up

    def update(self, keys, obstacles, candies, screen_width, screen_height):
        # Movement logic with WASD keys
        if keys[pygame.K_w]:
            self.rect.y -= self.speed
        if keys[pygame.K_s]:
            self.rect.y += self.speed
        if keys[pygame.K_a]:
            self.rect.x -= self.speed
            # Flip image when moving left
            if self.direction != 'left':
                self.image = pygame.transform.flip(self.original_image, True, False)
                self.direction = 'left'
        if keys[pygame.K_d]:
            self.rect.x += self.speed
            # Reset image when moving right
            if self.direction != 'right':
                self.image = self.original_image
                self.direction = 'right'

        # Collision detection with window boundaries
        self.check_window_collision(screen_width, screen_height)

        # Check for candy collision and collect XP
        candy_collisions = pygame.sprite.spritecollide(self, candies, True)  # Remove candy on collision
        for candy in candy_collisions:
            self.gain_xp(10)  # Gain 10 XP for each candy collected

        # Check if the player can level up
        self.check_level_up()

        # Check for collisions with obstacles
        if pygame.sprite.spritecollide(self, obstacles, False):
            self.hp -= 1  # Reduce HP on collision
            print(f"Player HP: {self.hp}")

    def gain_xp(self, amount):
        self.xp += amount
        print(f"Player gained {amount} XP. Current XP: {self.xp}/{self.xp_needed}")

    def get_xp_progress(self):
        """Returns the percentage of XP filled for the current level."""
        return self.xp / self.xp_needed

    def check_level_up(self):
        if self.xp >= self.xp_needed:
            self.level += 1
            self.xp -= self.xp_needed  # Carry over remaining XP
            self.xp_needed = int(self.xp_needed * 1.2)  # Increase XP needed for next level
            print(f"Level Up! Player is now level {self.level}.")

    def check_window_collision(self, screen_width, screen_height):
        # Check for collision with the left side of the screen
        if self.rect.left < 0:
            self.rect.left = 0
        # Check for collision with the right side of the screen
        if self.rect.right > screen_width:
            self.rect.right = screen_width
        # Check for collision with the top of the screen
        if self.rect.top < 0:
            self.rect.top = 0
        # Check for collision with the bottom of the screen
        if self.rect.bottom > screen_height:
            self.rect.bottom = screen_height

    def get_hp(self):
        return self.hp


# Define the Candy class
class Candy(pygame.sprite.Sprite):
    def __init__(self, image_path):
        super().__init__()
        self.image = pygame.image.load(image_path).convert_alpha()
        self.rect = self.image.get_rect()
        self.spawn_random()

    def spawn_random(self):
        # Spawn candy at a random location on the screen
        self.rect.x = random.randint(0, width - self.rect.width)
        self.rect.y = random.randint(0, height - self.rect.height)

# Define the Slime Enemy class
class Slime(pygame.sprite.Sprite):
    print("WIP")#WIP

# Function to draw the XP bar and level text
def draw_xp_bar(screen, player):
    """Draws the XP bar on the screen."""
    # Define the XP bar's size and position
    bar_width = 150
    bar_height = 15
    bar_x = 15
    bar_y = 15

    # Calculate the filled width of the XP bar based on the player's XP progress
    fill_width = int(bar_width * player.get_xp_progress())

    # Draw the background of the XP bar (empty part)
    pygame.draw.rect(screen, gray, (bar_x, bar_y, bar_width, bar_height))

    # Draw the filled part of the XP bar (progress)
    pygame.draw.rect(screen, blue, (bar_x, bar_y, fill_width, bar_height))

    # Optional: You can add text to display XP amount
    font = pygame.font.Font(None, 25)
    text = font.render(f'XP: {player.xp}/{player.xp_needed}', True, black)
    screen.blit(text, (bar_x, bar_y + bar_height + 5))

    #Text for level
    font = pygame.font.Font(None, 25)
    text = font.render(f'Level: {player.level}', True, black)
    screen.blit(text, (bar_x, bar_y + bar_height + 20))

def draw_HP_bar(screen, player):
    """Draws the HP bar on the screen."""
    # Define the HP bar's size and position
    bar_width = 1.5
    bar_height = 15
    bar_x = 15
    bar_y = 70

    # Calculate the filled width of the HP bar based on the player's HP progress
    fill_width = int(bar_width * player.get_hp())

    # Draw the background of the HP bar (empty part)
    pygame.draw.rect(screen, gray, (bar_x, bar_y, bar_width, bar_height))

    # Draw the filled part of the HP bar (progress)
    pygame.draw.rect(screen, red, (bar_x, bar_y, fill_width, bar_height))

    # Optional: You can add text to display HP amount
    font = pygame.font.Font(None, 25)
    text = font.render(f'HP: {player.hp}', True, black)
    screen.blit(text, (bar_x, bar_y + bar_height + 5))



# Create the player instance
player = Player(640, 360, 'Pictures/Morp.png')

# Create sprite groups
all_sprites = pygame.sprite.Group()
all_sprites.add(player)

candies = pygame.sprite.Group()  # Group to hold candy sprites

# Timer to spawn candy every 15 seconds
candy_spawn_event = pygame.USEREVENT + 1
pygame.time.set_timer(candy_spawn_event, 5000)  # 15000 milliseconds = 15 seconds

# Create a group for obstacles (currently empty, but you can add obstacles here)
obstacles = pygame.sprite.Group()

#-----------------------------------------------------------

# Main game loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Spawn a new candy every # seconds
        if event.type == candy_spawn_event:
            candy = Candy('Pictures/Candy.png')  # Use your candy image path
            candies.add(candy)
            all_sprites.add(candy)  # Add the candy to all_sprites for drawing

    # Get the pressed keys
    keys = pygame.key.get_pressed()

    # Update the player (pass in the keys, obstacles, and candies for collision detection)
    player.update(keys, obstacles, candies, width, height)

    # Fill the screen with a background color (white in this case)
    screen.fill(white)

    # Draw the XP bar in the top-left corner of the screen
    draw_xp_bar(screen, player)

    # Draw the HP bar in the top-left corner of the screen
    draw_HP_bar(screen, player)

    # Draw all sprites (this includes the player and candies)
    all_sprites.draw(screen)

    # Update the display
    pygame.display.flip()

    # Cap the frame rate to 60 FPS
    pygame.time.Clock().tick(60)

# Quit the game when the loop ends
pygame.quit()
sys.exit()
