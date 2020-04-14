import pygame
from pygame.rect import Rect
import numpy as np

running = True

# set window size
width = 1920
height = 1080

head_center_x = 517
head_center_y = 539

last_mouse_pos = None
mouse_x, mouse_y = None, None

pygame.init()
screen = pygame.display.set_mode((width, height), 1, 16)

# title
pygame.display.set_caption("3DAB")

# Images
background_img = pygame.image.load('Images/bg.png')
record_img = pygame.image.load('Images/recordIcon.png')
x_img = pygame.image.load('Images/xicon.png')
play_img = pygame.image.load('Images/playIcon.png')
save_img = pygame.image.load('Images/saveIcon.png')
circle_img = pygame.image.load('Images/circle.png')
pb_img = pygame.image.load('Images/pb.png')
recordb_img = pygame.image.load('Images/recordb.png')


# starting position
# x = 100
# pygame.draw.rect(screen, (255,0,0), Rect(x, 5, 10, 90))
# pygame.display.update(pygame.Rect(0,0,width,height))

def get_img_width(img):
    return img.get_rect().width / 2


def get_img_height(img):
    return img.get_rect().height / 2


def ui_images():
    screen.blit(background_img, (0, 0))
    screen.blit(circle_img,
                (head_center_x - get_img_width(circle_img), head_center_y - get_img_height(circle_img)))
    screen.blit(recordb_img,
                (773 * 2 - get_img_width(recordb_img), 99 * 2 - get_img_height(recordb_img)))
    screen.blit(pb_img, (772 * 2 - get_img_width(pb_img), 283 * 2 - get_img_height(pb_img)))
    screen.blit(record_img, (773 * 2 - get_img_width(record_img), 99 * 2 - get_img_height(record_img)))
    screen.blit(x_img, (690 * 2 - get_img_width(x_img), 283 * 2 - get_img_height(x_img)))
    screen.blit(play_img, (772 * 2 - get_img_width(play_img), 283 * 2 - get_img_height(play_img)))
    screen.blit(save_img, (852 * 2 - get_img_width(save_img), 283 * 2 - get_img_height(save_img)))


# game loop
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # if event.type == pygame.MOUSEBUTTONDOWN:
            # mouse_x, mouse_y = pygame.mouse.get_pos()
            # if np.sqrt(
            #         np.square(head_center_x - mouse_x) + np.square(head_center_y - mouse_y)) < get_img_width(circle_img):
            #     last_mouse_pos = pygame.mouse.get_pos()

        elif event.type == pygame.KEYDOWN and event.unicode == 'c':
            # clear the circle when pressing the 'c' key
            last_mouse_pos = None

    ui_images()

    # mouse events, to draw the circle
    mouse_x, mouse_y = pygame.mouse.get_pos()
    if pygame.mouse.get_pressed()[0] and np.sqrt(
                    np.square(head_center_x - mouse_x) + np.square(head_center_y - mouse_y)) < get_img_width(circle_img):
        color = (255, 255, 255)
        last_mouse_pos = mouse_x, mouse_y

    if last_mouse_pos:
        color = (255, 255, 255)
        pos_x, pos_y = last_mouse_pos
        pygame.draw.circle(screen, color, (pos_x, pos_y), 30)
        # TODO make the circle give an angle according to the mouse position
        # if pos_x-head_center_x != 0:
        #     print(np.rad2deg(np.arctan((pos_y-head_center_y) / (pos_x-head_center_x))))


    # button = pygame.mouse.get_pressed()
    # if button[0] != 0:
    #     pos = pygame.mouse.get_pos()
    #     x = pos[0]
    #     y = pos[1]
    #     a = x - 5
    #     if a < 0:
    #         a = 0
    #     pygame.draw.rect(screen, (0,0,0), Rect(0, 0, width, height))
    #     # pygame.display.update(pygame.Rect(0,0,width,height))
    #     pygame.draw.rect(screen, (255,0,0), Rect(a, 5, 10, 90))
    #     pygame.display.update(pygame.Rect(0, 0, width, height))

    # makes the pygame update every frame
    pygame.display.update()
