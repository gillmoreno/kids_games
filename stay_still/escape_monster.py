import pygame
import cv2
import mediapipe as mp
import numpy as np
import os
from pygame import mixer
import math
import urllib.request
import random

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Initialize Pygame
pygame.init()
mixer.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
MONSTER_SIZE = 100
MOVEMENT_THRESHOLD = 0.015  # Lowered base threshold
MOVEMENT_MAX = 0.03  # Maximum expected movement
DIFFICULTY_LEVELS = {
    "easy": 0.02,
    "medium": 0.015,
    "hard": 0.01,
    "insane": 0.005,
}

# Add these constants after other constants
MUSIC_NORMAL_TEMPO = 1.0
MUSIC_MAX_TEMPO = 2.0  # Maximum speed-up for music
PROXIMITY_THRESHOLD = WINDOW_WIDTH // 2  # When to start speeding up music

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PURPLE = (147, 0, 211)
DARK_PURPLE = (73, 0, 105)
ORANGE = (255, 165, 0)

# Set up the display
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Escape the Monster!")

# Monster setup
MONSTER_IMAGE_PATH = "assets/monster.png"  # Fix typo in filename

# Load monster image
try:
    monster_img = pygame.image.load(MONSTER_IMAGE_PATH)
    # Scale the image to our desired size while maintaining aspect ratio
    img_rect = monster_img.get_rect()
    scale_factor = MONSTER_SIZE / max(img_rect.width, img_rect.height)
    new_width = int(img_rect.width * scale_factor)
    new_height = int(img_rect.height * scale_factor)
    monster_img = pygame.transform.scale(monster_img, (new_width, new_height))
    # Convert the image for faster blitting
    monster_img = monster_img.convert_alpha()
except Exception as e:
    print(f"Error loading monster image: {e}")
    # Fallback to simple monster if loading fails
    monster_img = pygame.Surface((MONSTER_SIZE, MONSTER_SIZE))
    monster_img.fill(RED)

monster_pos = [WINDOW_WIDTH - 150, WINDOW_HEIGHT // 2]  # Monster starts on the right
monster_animation_counter = 0
ANIMATION_SPEED = 0.1

# Initialize camera
cap = cv2.VideoCapture(0)


# Add after pygame initialization
def load_and_play_music():
    try:
        pygame.mixer.music.load("assets/psycho.mp3")  # Add your music file here
        pygame.mixer.music.play(-1)  # -1 means loop indefinitely
        pygame.mixer.music.set_volume(0.5)  # Set initial volume
    except Exception as e:
        print(f"Error loading music: {e}")


def calculate_movement(previous_landmarks, current_landmarks):
    if not previous_landmarks or not current_landmarks:
        return 0

    # Calculate movement based on key points (shoulders, hips)
    movement = 0
    key_points = [11, 12, 23, 24]  # Shoulder and hip landmarks

    for point in key_points:
        if previous_landmarks.landmark[point] and current_landmarks.landmark[point]:
            prev = previous_landmarks.landmark[point]
            curr = current_landmarks.landmark[point]
            movement += math.sqrt((prev.x - curr.x) ** 2 + (prev.y - curr.y) ** 2)

    return movement / len(key_points)


def draw_movement_indicator(screen, movement, threshold):
    # Draw movement bar at the top of the screen
    bar_width = 200
    bar_height = 20
    x = WINDOW_WIDTH - bar_width - 10
    y = 10

    # Draw background
    pygame.draw.rect(screen, WHITE, (x, y, bar_width, bar_height), 1)

    # Calculate fill width based on movement
    fill_width = min((movement / MOVEMENT_MAX) * bar_width, bar_width)

    # Choose color based on movement level
    if movement < threshold:
        color = GREEN
    elif movement < threshold * 1.5:
        color = YELLOW
    else:
        color = RED

    # Draw fill
    pygame.draw.rect(screen, color, (x, y, fill_width, bar_height))

    # Draw threshold line
    threshold_x = x + (threshold / MOVEMENT_MAX) * bar_width
    pygame.draw.line(screen, WHITE, (threshold_x, y), (threshold_x, y + bar_height), 2)


def animate_monster(monster_surface, counter, distance_to_player):
    """Animate the monster with multiple effects"""
    # Base scaling animation (breathing effect)
    scale = 1.0 + 0.05 * math.sin(counter)  # Reduced scale effect for the PNG

    # Add wobble effect when moving
    wobble = math.sin(counter * 2) * (distance_to_player / WINDOW_WIDTH) * 5  # Reduced wobble

    # Create the scaled surface
    orig_size = monster_surface.get_rect()
    size_x = int(orig_size.width * scale)
    size_y = int(orig_size.height * scale)
    scaled = pygame.transform.scale(monster_surface, (size_x, size_y))

    # Color shift based on distance (gets redder as it gets closer)
    color_shift = int(200 * (1 - distance_to_player / WINDOW_WIDTH))  # Reduced color shift
    if color_shift > 0:
        color_surface = pygame.Surface(scaled.get_rect().size, pygame.SRCALPHA)
        color_surface.fill((color_shift, 0, 0, 50))  # More subtle red tint
        scaled.blit(color_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    # Apply wobble by rotating slightly
    return pygame.transform.rotate(scaled, wobble)


# Add this function after other function definitions
# def update_music_tempo(distance_to_player):
#     """Adjust music tempo based on monster proximity"""
#     if distance_to_player <= PROXIMITY_THRESHOLD:
#         # Calculate tempo multiplier (increases as monster gets closer)
#         proximity_factor = 1 - (distance_to_player / PROXIMITY_THRESHOLD)
#         new_tempo = MUSIC_NORMAL_TEMPO + (MUSIC_MAX_TEMPO - MUSIC_NORMAL_TEMPO) * proximity_factor
#         pygame.mixer.music.set_pos(pygame.mixer.music.get_pos() * new_tempo)


def main():
    clock = pygame.time.Clock()
    running = True
    game_over = False
    previous_landmarks = None
    monster_speed = 5
    score = 0
    font = pygame.font.Font(None, 36)
    difficulty = "medium"  # Default difficulty
    movement_threshold = DIFFICULTY_LEVELS[difficulty]
    monster_animation_counter = 0

    # Add this line after clock initialization
    load_and_play_music()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game_over:
                    # Reset game
                    game_over = False
                    monster_pos[0] = WINDOW_WIDTH - 150
                    score = 0
                # Difficulty adjustment keys
                elif event.key == pygame.K_1:
                    difficulty = "easy"
                    movement_threshold = DIFFICULTY_LEVELS[difficulty]
                elif event.key == pygame.K_2:
                    difficulty = "medium"
                    movement_threshold = DIFFICULTY_LEVELS[difficulty]
                elif event.key == pygame.K_3:
                    difficulty = "hard"
                    movement_threshold = DIFFICULTY_LEVELS[difficulty]
                elif event.key == pygame.K_4:
                    difficulty = "insane"
                    movement_threshold = DIFFICULTY_LEVELS[difficulty]

        # Read camera
        success, image = cap.read()
        if not success:
            continue

        # Flip the image horizontally for a later selfie-view display
        image = cv2.flip(image, 1)

        # Convert the BGR image to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Process the image and detect poses
        results = pose.process(image_rgb)

        # Calculate movement
        movement = 0
        if results.pose_landmarks:
            movement = calculate_movement(previous_landmarks, results.pose_landmarks)
            previous_landmarks = results.pose_landmarks

        # Update game state
        if not game_over:
            if movement > movement_threshold:
                # Player moved - monster approaches
                approach_speed = min(monster_speed * (movement / movement_threshold), monster_speed * 2)
                monster_pos[0] -= approach_speed
            else:
                # Player is still - monster retreats slightly
                monster_pos[0] = min(monster_pos[0] + 1, WINDOW_WIDTH - 150)

            # Update score
            score += 1

            # Check if monster caught player
            if monster_pos[0] <= 150:  # Player position
                game_over = True

            # Add this before drawing the screen
            distance_to_player = monster_pos[0] - 150
            # update_music_tempo(distance_to_player)

        # Update monster animation
        monster_animation_counter += ANIMATION_SPEED
        distance_to_player = monster_pos[0] - 150  # Distance to player position
        current_monster = animate_monster(monster_img, monster_animation_counter, distance_to_player)
        monster_rect = current_monster.get_rect()
        monster_rect.centerx = monster_pos[0]
        monster_rect.centery = monster_pos[1]

        # Draw game
        screen.fill(BLACK)

        # Add glow effect around monster
        glow_radius = int(MONSTER_SIZE * (1.2 + 0.2 * math.sin(monster_animation_counter)))
        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        for i in range(10):
            alpha = 100 - i * 10
            size = glow_radius - i * 2
            if size > 0:
                pygame.draw.circle(glow_surface, (*PURPLE[:3], alpha), (glow_radius, glow_radius), size)

        screen.blit(glow_surface, (monster_rect.centerx - glow_radius, monster_rect.centery - glow_radius))

        # Draw monster with animation
        screen.blit(current_monster, monster_rect)

        # Draw movement indicator
        draw_movement_indicator(screen, movement, movement_threshold)

        # Draw score
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        # Draw difficulty
        diff_text = font.render(f"Difficulty: {difficulty.title()} (1-4)", True, WHITE)
        screen.blit(diff_text, (10, 40))

        # Draw game over message
        if game_over:
            game_over_text = font.render("GAME OVER! Press R to restart", True, RED)
            text_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            screen.blit(game_over_text, text_rect)

        pygame.display.flip()
        clock.tick(30)

    # Modify cleanup section
    pygame.mixer.music.stop()
    cap.release()
    pygame.quit()


if __name__ == "__main__":
    main()
