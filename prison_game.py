import cv2
import pygame
import time
import threading

# from datetime import datetime

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
upper_body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_upperbody.xml")
full_body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_fullbody.xml")

# Initialize video capture
# cap = cv2.VideoCapture(0)  # 0 for default camera
CAMERA_INDICES = [0, 1]  # List of camera indices to use

# Game settings
GAME_DURATION = 200  # seconds
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
FONT_SIZE = 36


class FaceDetectionGame:
    def __init__(self):
        self.game_active = False
        self.start_time = 0
        self.face_detected = False
        self.face_detected_frames = 0
        self.game_over = False
        self.font = cv2.FONT_HERSHEY_SIMPLEX

    def play_alarm(self):
        """Play alarm sound in a separate thread"""
        alarm_sound.play()

    def play_start_sound(self):
        """Play start sound"""
        start_sound.play()

    def stop_alarm(self):
        """Stop the alarm sound if it's playing."""
        alarm_sound.stop()  # Stop playing the alarm sound
        pygame.mixer.stop()  # Ensure mixer channels are stopped

    def reset_game(self):
        """Reset game state"""
        self.stop_alarm()  # Stop any playing alarm immediately
        self.game_active = True
        self.face_detected = False
        self.game_over = False
        self.start_time = time.time()
        self.start_detect_time = time.time()
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

        available_cameras = []
        for i in CAMERA_INDICES:
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append(cap)
            else:
                print(f"Warning: Could not open camera at index {i}.")

        if not available_cameras:
            print("Error: Could not open any cameras.")
            return

        caps = available_cameras

        while True:
            frames = []
            for cap in caps:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Could not read frame from camera.")
                    break
                frames.append(frame)
            if len(frames) != len(caps):
                break

            gray_frames = [cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) for frame in frames]

            # Facial, upper body, and full body detection and game logic for each camera
            face_detected_this_frame = False  # Flag to track if any body detection was successful in this frame
            for i, gray in enumerate(gray_frames):
                if self.game_active and time.time() >= self.start_detect_time:
                    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=6, minSize=(80, 80))
                    upper_bodies = upper_body_cascade.detectMultiScale(
                        gray, scaleFactor=1.2, minNeighbors=6, minSize=(80, 80)
                    )
                    full_bodies = full_body_cascade.detectMultiScale(
                        gray, scaleFactor=1.2, minNeighbors=3, minSize=(80, 80)
                    )

                    detections = list(faces) + list(upper_bodies) + list(full_bodies)
                    if len(detections) > 0:
                        face_detected_this_frame = True
                        for x, y, w, h in faces:
                            cv2.rectangle(frames[i], (x, y), (x + w, y + h), (0, 255, 0), 2)
                        for x, y, w, h in upper_bodies:
                            cv2.rectangle(frames[i], (x, y), (x + w, y + h), (255, 0, 0), 2)
                        for x, y, w, h in full_bodies:
                            cv2.rectangle(frames[i], (x, y), (x + w, y + h), (0, 0, 255), 2)

                # Display game information on each frame
                if self.game_active:
                    elapsed_time = time.time() - self.start_time
                    time_left = max(0, GAME_DURATION - elapsed_time)
                    cv2.putText(frames[i], f"Time Left: {time_left:.1f}", (10, 30), self.font, 1, (255, 255, 255), 2)
                    cv2.putText(
                        frames[i], f"Elapsed Time: {elapsed_time:.1f}", (10, 110), self.font, 1, (255, 255, 255), 2
                    )
                    cv2.putText(frames[i], "Hide your face!", (10, 70), self.font, 1, (0, 255, 0), 2)
                elif self.game_over:
                    cv2.putText(
                        frames[i], "GAME OVER!", (WINDOW_WIDTH // 4, WINDOW_HEIGHT // 2), self.font, 2, (0, 0, 255), 3
                    )
                    cv2.putText(
                        frames[i],
                        "Press SPACE to restart",
                        (WINDOW_WIDTH // 4, WINDOW_HEIGHT // 2 + 50),
                        self.font,
                        1,
                        (255, 255, 255),
                        2,
                    )
                else:
                    cv2.putText(
                        frames[i],
                        "Press SPACE to start",
                        (WINDOW_WIDTH // 4, WINDOW_HEIGHT // 2),
                        self.font,
                        1,
                        (255, 255, 255),
                        2,
                    )

                # Display the frame for each camera
                cv2.imshow(f"Camera {CAMERA_INDICES[i]}", frames[i])

            self.face_detected = face_detected_this_frame

            # Check game state
            self.check_game_over()

            # Handle key presses (only need one, as it applies to all cameras)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord(" ") and not self.game_active:
                self.reset_game()

        # Cleanup
        for cap in caps:
            cap.release()
            cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    game = FaceDetectionGame()
    game.run()

    cv2.destroyAllWindows()
