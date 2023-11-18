import pygame
import time
pygame.init()
pygame.mixer.init()

sound = pygame.mixer.Sound("close.mp3")
sound.play()
time.sleep(1)