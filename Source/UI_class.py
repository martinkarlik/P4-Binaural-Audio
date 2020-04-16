import pygame
from pygame.rect import Rect
import numpy as np


class Interface:

    class Element:

        def __init__(self, name, image, pos):
            self.name = name
            self.image = image
            self.pos = pos
            self.rect = image.get_rect()
            # self.radius = np.sqrt(np.square(self.rect[0] - self.rect[2]) + np.square(self.rect[1] - self.rect[3]))
            self.radius = self.rect[0] / 2
            self.hovered = False
            self.clicked = False

        def get_distance(self, other):
            return np.sqrt(np.square(self.pos[0] - other[0]) + np.square(self.pos[1] - other[1]))

    running = True

    def __init__(self):
        pygame.init()
        self.width = 1920
        self.height = 1080
        self.screen = pygame.display.set_mode((self.width, self.height), 1, 16)


class CreationInterface(Interface):

    new_angle_threshold = 10

    def __init__(self):
        super().__init__()
        pygame.display.set_caption("3DAB")

        self.ui_elements = [
            self.Element("background", pygame.image.load('../Dependencies/Images/bg.png'), [self.width / 2, self.height / 2]),
            self.Element("circle", pygame.image.load('../Dependencies/Images/circle.png'), [517, 539]),
            # self.Element("head", pygame.image.load('../Dependencies/Images/head.png'), [517, 539]),
            self.Element("pb", pygame.image.load('../Dependencies/Images/pb.png'), [1544, 566]),
            self.Element("play", pygame.image.load('../Dependencies/Images/playIcon.png'), [1544, 566]),
            self.Element("save", pygame.image.load('../Dependencies/Images/saveIcon.png'), [1704, 566]),
            self.Element("x", pygame.image.load('../Dependencies/Images/xicon.png'), [1380, 566]),
            self.Element("record", pygame.image.load('../Dependencies/Images/recordb.png'), [1544, 198]),
            self.Element("record_icon", pygame.image.load('../Dependencies/Images/recordIcon.png'), [1546, 198])
        ]

        self.cross_last_pos = None


    def get_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN and event.unicode == 'c':
                # clear the circle when pressing the 'c' key
                last_mouse_pos = None

        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        for element in self.ui_elements:
            mouse_inside = element.get_distance(mouse_pos) < element.radius
            element.hovered, element.clicked = mouse_inside, mouse_inside and mouse_pressed



        distance_to_head = np.sqrt(np.square(self.head_center_x - mouse_x) + np.square(self.head_center_y - mouse_y))
        if pygame.mouse.get_pressed()[0] and distance_to_head < self.get_img_width(self.circle_img):
            color = (255, 255, 255)
            last_mouse_pos = mouse_x, mouse_y

        if last_mouse_pos:
            color = (255, 255, 255)
            pos_x, pos_y = last_mouse_pos
            pygame.draw.circle(self.screen, color, (pos_x, pos_y), 30)
            # TODO make the circle give an angle according to the mouse position
            # if pos_x-head_center_x != 0:
            #     print(np.rad2deg(np.arctan((pos_y-head_center_y) / (pos_x-head_center_x))))

    def update(self):
        # display all creation interface visuals
        for element in self.ui_elements:
            element_rect = element.image.get_rect(center=(element.pos[0], element.pos[1]))
            self.screen.blit(element.image, element_rect)

        pygame.display.update()


ui = CreationInterface()
while True:

    ui.get_events()



    ui.update()