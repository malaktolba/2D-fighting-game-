import pygame
import sys
import random
import math

# Initialize Pygame
pygame.init()

# Initialize Pygame mixer for sound
pygame.mixer.init()

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 35
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BUTTON_COLOR = (0, 255, 0)
HOVER_COLOR = (0, 200, 0)
BACKGROUND_COLOR = (40, 40, 40)
TEXT_COLOR = (255, 255, 255)
HEALTH_BAR_WIDTH = 200
HEALTH_BAR_HEIGHT = 20

# Fonts
TITLE_FONT = pygame.font.SysFont("Arial", 48)
BUTTON_FONT = pygame.font.SysFont("Arial", 24)
INSTRUCTION_FONT = pygame.font.SysFont("Arial", 28)

# Screen and Clock
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Shooter Game")
clock = pygame.time.Clock()

# Background Music Path
background_music_path = "C:/Users/Lenovo/Downloads/battle-fight-music-dynamic-warrior-background-intro-theme-272176.wav"

# Global variable to store player name and mute state
player_name = ""
is_muted = False

# Button Class
class Button:
    def __init__(self, x, y, width, height, text, action):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.font = BUTTON_FONT
        self.color = BUTTON_COLOR
        self.hover_color = HOVER_COLOR

    def draw(self):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, self.hover_color, self.rect)
        else:
            pygame.draw.rect(screen, self.color, self.rect)

        text_surface = self.font.render(self.text, True, BLACK)
        screen.blit(
            text_surface,
            (
                self.rect.centerx - text_surface.get_width() // 2,
                self.rect.centery - text_surface.get_height() // 2,
            ),
        )

    def click(self, pos):
        if self.rect.collidepoint(pos):
            self.action()

# Bullet Class
class Bullet:
    def __init__(self, x, y, radius, color, angle, speed=10):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.angle = angle
        self.speed = speed

    def move(self):
        self.x += self.speed * math.cos(self.angle)
        self.y += self.speed * math.sin(self.angle)

    def draw(self):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)

    def off_screen(self):
        return self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT

    def collides_with(self, fighter):
        return pygame.Rect(fighter.x, fighter.y, fighter.width, fighter.height).collidepoint(self.x, self.y)

# Fighter Class (for both player and AI)
class Fighter:
    def __init__(self, x, y, width, height, image_path=None, speed=5, health=100, style="player"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = speed
        self.health = health
        self.style = style
        
        # Load player image if path is provided
        if image_path:
            self.image = pygame.image.load(image_path).convert_alpha()  # Load with transparency support
            self.image = pygame.transform.scale(self.image, (self.width, self.height))  # Scale image to fit fighter size
        else:
            self.image = None

    def move(self, keys=None, target=None, min_distance=20):
        # Player movement - Confined to left side
        if self.style == "player" and keys:
            if keys[pygame.K_UP] and self.y > 50:  # Move up (inside frame)
                self.y -= self.speed
            if keys[pygame.K_DOWN] and self.y + self.height < HEIGHT - 50:  # Move down (inside frame)
                self.y += self.speed
            if keys[pygame.K_LEFT] and self.x > 50:  # Move left (inside frame, confined to left side)
                self.x -= self.speed
            if keys[pygame.K_RIGHT] and self.x + self.width < WIDTH // 2 - 50:  # Move right (inside left half)
                self.x += self.speed

        # AI movement - Confined to right side
        elif self.style == "ai" and target:
            if target:
                dx = target.x - self.x
                dy = target.y - self.y
                distance = math.sqrt(dx**2 + dy**2)

                # If AI is too close to the player, it moves away
                if distance < min_distance:
                    # Move in the opposite direction from the player
                    angle = math.atan2(dy, dx) + math.pi  # Move opposite to the player
                    self.x += self.speed * math.cos(angle)
                    self.y += self.speed * math.sin(angle)
                else:
                    # Move towards the player normally
                    angle = math.atan2(dy, dx)
                    self.x += self.speed * math.cos(angle)
                    self.y += self.speed * math.sin(angle)

            # Confine AI to the right half of the screen
            self.x = max(WIDTH // 2 + 50, min(self.x, WIDTH - self.width - 50))

    def shoot(self, target=None):
        if target:  # AI shooting towards the player
            # Calculate the angle to shoot towards the player
            angle = math.atan2(target.y - self.y, target.x - self.x)
            return Bullet(self.x + self.width // 2, self.y + self.height // 2, 10, WHITE, angle)
        else:
            # Player shooting (direction not dependent on target)
            return Bullet(self.x + self.width // 2, self.y + self.height // 2, 10, WHITE, 0)

    def draw(self):
        if self.image:
            screen.blit(self.image, (self.x, self.y))  # Draw the image of the player
        else:
            pygame.draw.rect(screen, WHITE, (self.x, self.y, self.width, self.height))

# Health bar display function with player name and percentage
def draw_health_bar(fighter, x, y, label):
    pygame.draw.rect(screen, WHITE, (x, y, HEALTH_BAR_WIDTH, HEALTH_BAR_HEIGHT))
    pygame.draw.rect(
        screen,
        (0, 255, 0),  # Green color for health
        (x, y, HEALTH_BAR_WIDTH * (fighter.health / 100), HEALTH_BAR_HEIGHT),
    )

    font = pygame.font.SysFont("Arial", 24)
    label_text = font.render(label, True, WHITE)
    screen.blit(label_text, (x, y - 30))

    health_text = font.render(f"{fighter.health}%", True, WHITE)
    screen.blit(
        health_text,
        (x + (HEALTH_BAR_WIDTH - health_text.get_width()) // 2, y + HEALTH_BAR_HEIGHT + 5),
    )

# Game Over Screen with Play Again and Main Menu buttons
def game_over(winner):
    def play_again():
        choose_difficulty()

    def go_to_main_menu():
        main_menu()

    font = pygame.font.SysFont("arial", 48)
    text = font.render(f"{winner} Wins!", True, WHITE)
    screen.fill(BACKGROUND_COLOR)
    screen.blit(
        text,
        (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2),
    )

    play_again_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 50, "Play Again", play_again)
    main_menu_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 200, 200, 50, "Main Menu", go_to_main_menu)

    play_again_button.draw()
    main_menu_button.draw()

    pygame.display.flip()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                play_again_button.click(event.pos)
                main_menu_button.click(event.pos)

# Choose Difficulty Screen
def choose_difficulty():
    def set_difficulty(difficulty):
        if difficulty == "easy":
            main_game(ai_speed=2, ai_health=100)
        elif difficulty == "medium":
            main_game(ai_speed=4, ai_health=125)
        elif difficulty == "hard":
            main_game(ai_speed=6, ai_health=150)

    screen.fill(BACKGROUND_COLOR)

    # Display the title
    title_text = TITLE_FONT.render("Choose Difficulty", True, TEXT_COLOR)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 4))

    # Create buttons for different difficulty levels
    easy_button = Button(WIDTH // 2 - 100, HEIGHT // 2 - 100, 200, 50, "Easy", lambda: set_difficulty("easy"))
    medium_button = Button(WIDTH // 2 - 100, HEIGHT // 2, 200, 50, "Medium", lambda: set_difficulty("medium"))
    hard_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 50, "Hard", lambda: set_difficulty("hard"))

    easy_button.draw()
    medium_button.draw()
    hard_button.draw()

    pygame.display.flip()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                easy_button.click(event.pos)
                medium_button.click(event.pos)
                hard_button.click(event.pos)

# Main Menu Function
def main_menu():
    def start_game():
        choose_difficulty()  # Navigate to the difficulty selection screen

    def quit_game():
        pygame.quit()
        sys.exit()

    # Play background music as soon as the game starts
    pygame.mixer.music.load(background_music_path)
    pygame.mixer.music.play(-1, 0.0)  # Loop indefinitely

    screen.fill(BACKGROUND_COLOR)
    title_text = TITLE_FONT.render("Shooter Game", True, TEXT_COLOR)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 4))

    start_button = Button(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 50, "Start Game", start_game)
    quit_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 50, "Quit Game", quit_game)

    start_button.draw()
    quit_button.draw()

    pygame.display.flip()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                start_button.click(event.pos)
                quit_button.click(event.pos)

# Main Game loop (pass ai_speed and ai_health for difficulty)
def main_game(ai_speed=3, ai_health=100):
    player_image_path = "C:/Users/Lenovo/Downloads/download__3_-removebg-preview.png"
    player_width = 200
    player_height = 200
    player = Fighter(WIDTH // 4, HEIGHT // 2, player_width, player_height, image_path=player_image_path)
    ai = Fighter(WIDTH * 3 // 4, HEIGHT // 2, 200, 200, image_path="C:/Users/Lenovo/Downloads/download__7_-removebg-preview.png", speed=ai_speed, health=ai_health, style="ai")

    player_bullets = []
    ai_bullets = []

    # Shooting cooldowns (in milliseconds)
    player_last_shot = 0
    ai_last_shot = 0
    shoot_cooldown = 500

    try:
        background_image = pygame.image.load("C:/Users/Lenovo/OneDrive/Pictures/download.jpeg")
        background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))
    except pygame.error:
        print("Error: Background image not found or invalid format.")
        pygame.quit()
        sys.exit()

    running = True
    while running:
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()
        player.move(keys)

        if keys[pygame.K_SPACE] and current_time - player_last_shot >= shoot_cooldown:
            player_bullets.append(player.shoot())  # Player shoots
            player_last_shot = current_time

        if random.random() < 0.02 and current_time - ai_last_shot >= shoot_cooldown:
            ai_bullets.append(ai.shoot(player))  # AI shoots
            ai_last_shot = current_time

        ai.move(target=player)

        for bullet in player_bullets:
            bullet.move()
            if bullet.off_screen():
                player_bullets.remove(bullet)

        for bullet in ai_bullets:
            bullet.move()
            if bullet.off_screen():
                ai_bullets.remove(bullet)

        # Collision detection
        for bullet in player_bullets:
            if bullet.collides_with(ai):
                ai.health -= 10
                player_bullets.remove(bullet)
                if ai.health <= 0:
                    game_over("Player")

        for bullet in ai_bullets:
            if bullet.collides_with(player):
                player.health -= 10
                ai_bullets.remove(bullet)
                if player.health <= 0:
                    game_over("AI")

        # Draw everything
        screen.blit(background_image, (0, 0))  # Draw background
        player.draw()
        ai.draw()

        for bullet in player_bullets:
            bullet.draw()

        for bullet in ai_bullets:
            bullet.draw()

        draw_health_bar(player, 50, 50, "Player")
        draw_health_bar(ai, WIDTH - 250, 50, "AI")

        pygame.display.flip()

        clock.tick(FPS)

# Run the game
main_menu()
