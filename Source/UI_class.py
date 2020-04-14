import pygame
from pygame.rect import Rect


class Interface:

    running = True
    new_angle_threshold = 10

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("3DAB")
        self.running = True
        self.width = 360
        self.height = 100
        self.screen = pygame.display.set_mode((self.width, self.height), 1, 16)

        self.x = 100
        pygame.draw.rect(self.screen, (255, 0, 0), Rect(self.x, 5, 10, 90))

    def update(self):

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

        button = pygame.mouse.get_pressed()
        if button[0] != 0:
            pos = pygame.mouse.get_pos()
            self.x = pos[0]
            y = pos[1]
            a = self.x - 5
            if a < 0:
                a = 0
            pygame.draw.rect(self.screen, (0, 0, 0), Rect(0, 0, self.width, self.height))
            pygame.draw.rect(self.screen, (255, 0, 0), Rect(a, 5, 10, 90))

        pygame.display.update()

    def get_value(self):
        return self.x


