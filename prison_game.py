import cv2
import pygame
import time
import threading
from datetime import datetime

# Initialize Pygame for sound
pygame.mixer.init()

# Load sounds
try:
    alarm_sound = pygame.mixer.Sound("prison_breakout.mp3")  # You'll need an alarm sound file
    start_sound = pygame.mixer.Sound("clashofclans.mp3")  # You'll need a start sound file
except:
    print("Error loading sound files. Make sure you have 'alarm.wav' and 'start.wav' in your directory")
    exit()

# Initialize face cascade classifier
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Initialize video capture
cap = cv2.VideoCapture(0)  # 0 for default camera

# Game settings
GAME_DURATION = 10  # seconds
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
FONT_SIZE = 36


class FaceDetectionGame:
    def __init__(self):
        self.game_active = False
        self.start_time = 0
        self.face_detected = False
        self.game_over = False
        self.font = cv2.FONT_HERSHEY_SIMPLEX

    def play_alarm(self):
        """Play alarm sound in a separate thread"""
        alarm_sound.play()

    def play_start_sound(self):
        """Play start sound"""
        start_sound.play()

    def reset_game(self):
        """Reset game state"""
        self.game_active = True
        self.face_detected = False
        self.game_over = False
        self.start_time = time.time()
        threading.Thread(target=self.play_start_sound).start()

    def check_game_over(self):
        """Check if game should end"""
        if not self.game_active:
            return False

        current_time = time.time()
        elapsed_time = current_time - self.start_time

        # Check if time is up
        if elapsed_time >= GAME_DURATION:
            self.game_over = True
            self.game_active = False
            threading.Thread(target=self.play_alarm).start()
            return True

        # Check if face is detected
        if self.face_detected:
            self.game_over = True
            self.game_active = False
            threading.Thread(target=self.play_alarm).start()
            return True

        return False

    def run(self):
        self.reset_game()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Detect faces
            if self.game_active:
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

                # Draw rectangles around detected faces
                for x, y, w, h in faces:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    self.face_detected = True

            # Check game state
            self.check_game_over()

            # Display game information
            if self.game_active:
                time_left = max(0, GAME_DURATION - (time.time() - self.start_time))
                cv2.putText(frame, f"Time Left: {time_left:.1f}", (10, 30), self.font, 1, (255, 255, 255), 2)
                cv2.putText(frame, "Hide your face!", (10, 70), self.font, 1, (0, 255, 0), 2)
            elif self.game_over:
                cv2.putText(frame, "GAME OVER!", (WINDOW_WIDTH // 4, WINDOW_HEIGHT // 2), self.font, 2, (0, 0, 255), 3)
                cv2.putText(
                    frame,
                    "Press SPACE to restart",
                    (WINDOW_WIDTH // 4, WINDOW_HEIGHT // 2 + 50),
                    self.font,
                    1,
                    (255, 255, 255),
                    2,
                )
            else:
                cv2.putText(
                    frame,
                    "Press SPACE to start",
                    (WINDOW_WIDTH // 4, WINDOW_HEIGHT // 2),
                    self.font,
                    1,
                    (255, 255, 255),
                    2,
                )

            # Display the frame
            cv2.imshow("Face Detection Game", frame)

            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord(" ") and not self.game_active:
                self.reset_game()

        # Cleanup
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    game = FaceDetectionGame()
    game.run()
