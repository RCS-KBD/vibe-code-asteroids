import pygame
import sys
import random
import math
from pygame import Vector2

# Initialize Pygame
pygame.init()

# Constants
WIDTH = 800
HEIGHT = 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SHIP_SIZE = 20
BULLET_SIZE = 3
BULLET_SPEED = 10
ASTEROID_SIZES = [50, 30, 20]

class Player:
    def __init__(self):
        self.position = Vector2(WIDTH // 2, HEIGHT // 2)
        self.velocity = Vector2(0, 0)
        self.acceleration = 0.5
        self.friction = 0.98
        self.rotation = 0
        self.size = 20

    def get_nose_position(self):
        # Calculate the position of the ship's nose using Vector2
        nose_offset = Vector2(0, -self.size).rotate(self.rotation)
        return self.position + nose_offset

    def draw(self, screen):
        # Draw triangular ship
        points = [
            self.position + Vector2(0, -self.size).rotate(self.rotation),
            self.position + Vector2(-self.size/2, self.size/2).rotate(self.rotation),
            self.position + Vector2(self.size/2, self.size/2).rotate(self.rotation)
        ]
        pygame.draw.polygon(screen, WHITE, points, 2)

    def update(self):
        keys = pygame.key.get_pressed()
        
        # Rotation
        if keys[pygame.K_LEFT]:
            self.rotation -= 5
        if keys[pygame.K_RIGHT]:
            self.rotation += 5

        # Thrust
        if keys[pygame.K_UP]:
            thrust = Vector2(0, -self.acceleration).rotate(self.rotation)
            self.velocity += thrust

        # Update position with velocity
        self.velocity *= self.friction
        self.position += self.velocity

        # Screen wrapping
        self.position.x %= WIDTH
        self.position.y %= HEIGHT

class Bullet:
    def __init__(self, x, y, angle):
        self.position = Vector2(x, y)
        # Use the same Vector2 direction calculation as the ship's nose
        self.velocity = Vector2(0, -BULLET_SPEED).rotate(angle)
        self.lifetime = 60  # frames

    def update(self):
        self.position += self.velocity
        self.position.x %= WIDTH
        self.position.y %= HEIGHT
        self.lifetime -= 1

    def draw(self, surface):
        pygame.draw.circle(surface, WHITE, (int(self.position.x), int(self.position.y)), BULLET_SIZE)

class Asteroid:
    def __init__(self, x=None, y=None, size_index=0):
        self.size_index = size_index
        self.size = ASTEROID_SIZES[size_index]
        if x is None:
            self.x = random.randint(0, WIDTH)
        else:
            self.x = x
        if y is None:
            self.y = random.randint(0, HEIGHT)
        else:
            self.y = y
        
        angle = random.random() * 2 * math.pi
        speed = random.random() * 2 + 1
        self.velocity_x = math.cos(angle) * speed
        self.velocity_y = math.sin(angle) * speed

    def draw(self, screen):
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.size, 2)

    def update(self):
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.x %= WIDTH
        self.y %= HEIGHT

class ExplosionLine:
    def __init__(self, x, y, angle):
        self.position = Vector2(x, y)
        self.velocity = Vector2(0, -5).rotate(angle)  # Lines shoot out at different angles
        self.lifetime = 30  # frames
        self.length = 20  # pixels

    def update(self):
        self.position += self.velocity
        self.lifetime -= 1

    def draw(self, surface):
        if self.lifetime > 0:
            # Calculate end point of the line
            end_pos = self.position + self.velocity.normalize() * self.length
            # Fade out the line as lifetime decreases
            alpha = int((self.lifetime / 30) * 255)
            color = (255, 255, 255, alpha)
            pygame.draw.line(surface, color, 
                           (int(self.position.x), int(self.position.y)),
                           (int(end_pos.x), int(end_pos.y)), 2)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Vibe Code Asteroids")
        self.clock = pygame.time.Clock()
        self.reset_game()

    def reset_game(self):
        self.player = Player()
        self.level = 1
        self.start_new_level()
        self.running = True
        self.game_over = False
        self.level_complete = False
        self.level_transition_timer = 0
        self.bullets = []
        self.score = 0
        self.explosion_lines = []

    def start_new_level(self):
        # Clear any remaining objects
        self.asteroids = []
        self.bullets = []
        
        # Number of asteroids increases with each level
        num_asteroids = 3 + self.level
        
        # Create new asteroids with increasing speed based on level
        for _ in range(num_asteroids):
            asteroid = Asteroid()
            # Increase asteroid speed by 10% each level
            speed_multiplier = 1 + (self.level - 1) * 0.1
            asteroid.velocity_x *= speed_multiplier
            asteroid.velocity_y *= speed_multiplier
            self.asteroids.append(asteroid)
        
        self.level_complete = False
        self.level_transition_timer = 0

    def check_level_complete(self):
        if len(self.asteroids) == 0 and not self.level_complete:
            self.level_complete = True
            self.level_transition_timer = 180  # 3 seconds at 60 FPS

    def create_explosion(self, x, y):
        # Create 12 lines shooting out in different directions
        for i in range(12):
            angle = i * 30  # 360 degrees / 12 = 30 degrees between each line
            self.explosion_lines.append(ExplosionLine(x, y, angle))

    def check_player_asteroid_collision(self):
        # Check collision between player and asteroids
        for asteroid in self.asteroids:
            # Calculate distance between player center and asteroid center
            dx = self.player.position.x - asteroid.x
            dy = self.player.position.y - asteroid.y
            distance = math.sqrt(dx**2 + dy**2)
            
            # If distance is less than combined radii (player size/2 + asteroid size)
            if distance < (self.player.size/2 + asteroid.size):
                self.game_over = True
                # Create explosion at player's position
                self.create_explosion(self.player.position.x, self.player.position.y)
                break

    def update(self):
        if self.game_over:
            # Update explosion lines even in game over state
            self.explosion_lines = [line for line in self.explosion_lines if line.lifetime > 0]
            for line in self.explosion_lines:
                line.update()
            return

        if self.level_complete:
            self.level_transition_timer -= 1
            if self.level_transition_timer <= 0:
                self.level += 1
                self.start_new_level()
            return

        self.player.update()
        for asteroid in self.asteroids:
            asteroid.update()
        
        # Update bullets and remove dead ones
        self.bullets = [bullet for bullet in self.bullets if bullet.lifetime > 0]
        for bullet in self.bullets:
            bullet.update()

        # Check for player collision with asteroids
        self.check_player_asteroid_collision()

        # Bullet-asteroid collision detection
        for bullet in self.bullets[:]:
            for asteroid in self.asteroids[:]:
                dx = bullet.position.x - asteroid.x
                dy = bullet.position.y - asteroid.y
                distance = math.sqrt(dx**2 + dy**2)
                
                if distance < asteroid.size:
                    self.bullets.remove(bullet)
                    self.asteroids.remove(asteroid)
                    self.score += (3 - asteroid.size_index) * 100
                    
                    # Split asteroid if it's not the smallest size
                    if asteroid.size_index < len(ASTEROID_SIZES) - 1:
                        for _ in range(2):
                            new_asteroid = Asteroid(
                                asteroid.x, asteroid.y, 
                                asteroid.size_index + 1
                            )
                            # Apply same level speed multiplier
                            speed_multiplier = 1 + (self.level - 1) * 0.1
                            new_asteroid.velocity_x *= speed_multiplier
                            new_asteroid.velocity_y *= speed_multiplier
                            self.asteroids.append(new_asteroid)
                    break

        # Check if level is complete
        self.check_level_complete()

        # Update explosion lines
        self.explosion_lines = [line for line in self.explosion_lines if line.lifetime > 0]
        for line in self.explosion_lines:
            line.update()

    def draw(self):
        self.screen.fill(BLACK)
        
        # Draw game objects
        if not self.game_over:
            self.player.draw(self.screen)
        for bullet in self.bullets:
            bullet.draw(self.screen)
        for asteroid in self.asteroids:
            asteroid.draw(self.screen)
        
        # Draw explosion lines
        for line in self.explosion_lines:
            line.draw(self.screen)

        # Draw HUD
        font = pygame.font.Font(None, 36)
        # Draw score in top left
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        # Draw level in top right
        level_text = font.render(f"Level: {self.level}", True, WHITE)
        level_rect = level_text.get_rect()
        level_rect.topright = (WIDTH - 10, 10)
        self.screen.blit(level_text, level_rect)

        # Draw level complete message
        if self.level_complete and not self.game_over:
            font_large = pygame.font.Font(None, 74)
            level_complete_text = font_large.render(f"Level {self.level} Complete!", True, WHITE)
            text_rect = level_complete_text.get_rect(center=(WIDTH/2, HEIGHT/2 - 50))
            self.screen.blit(level_complete_text, text_rect)
            
            font = pygame.font.Font(None, 48)
            next_level_text = font.render(f"Get Ready for Level {self.level + 1}", True, WHITE)
            next_rect = next_level_text.get_rect(center=(WIDTH/2, HEIGHT/2 + 50))
            self.screen.blit(next_level_text, next_rect)

        # Draw game over message
        if self.game_over:
            font = pygame.font.Font(None, 74)
            game_over_text = font.render("GAME OVER", True, WHITE)
            text_rect = game_over_text.get_rect(center=(WIDTH/2, HEIGHT/2))
            self.screen.blit(game_over_text, text_rect)
            
            font = pygame.font.Font(None, 36)
            final_score_text = font.render(f"Final Score: {self.score}", True, WHITE)
            score_rect = final_score_text.get_rect(center=(WIDTH/2, HEIGHT/2 + 50))
            self.screen.blit(final_score_text, score_rect)
            
            restart_text = font.render("Press R to Restart or ESC to Quit", True, WHITE)
            restart_rect = restart_text.get_rect(center=(WIDTH/2, HEIGHT/2 + 100))
            self.screen.blit(restart_text, restart_rect)

        pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE and not self.game_over and not self.level_complete:
                    # Create new bullet at ship's nose position with ship's angle
                    nose_pos = self.player.get_nose_position()
                    self.bullets.append(Bullet(nose_pos.x, nose_pos.y, self.player.rotation))
                elif event.key == pygame.K_r and self.game_over:
                    # Reset game
                    self.reset_game()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()