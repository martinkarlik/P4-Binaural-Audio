import pygame
from pygame.rect import Rect
import numpy as np

running = True

# set window size
width = 1920
height = 1080

head_center_x = 517
head_center_y = 539
record_pos = (1546, 198)
x_pos = (1380, 566)
play_pos = (1544, 566)
save_pos = (1704, 566)

last_mouse_pos = None
mouse_x, mouse_y = None, None

pygame.init()
screen = pygame.display.set_mode((width, height), 1, 16)

# title
pygame.display.set_caption("3DAB")

# images
background_img = pygame.image.load('../dependencies/images/bg.png')
record_img = pygame.image.load('../dependencies/images/recordIcon.png')
x_img = pygame.image.load('../dependencies/images/xicon.png')
play_img = pygame.image.load('../dependencies/images/playIcon.png')
save_img = pygame.image.load('../dependencies/images/saveIcon.png')
circle_img = pygame.image.load('../dependencies/images/circle.png')
pb_img = pygame.image.load('../dependencies/images/pb.png')
recordb_img = pygame.image.load('../dependencies/images/recordb.png')


# starting position
# x = 100
# pygame.draw.rect(screen, (255,0,0), Rect(x, 5, 10, 90))
# pygame.display.update(pygame.Rect(0,0,width,height))

def get_img_width(img):
    return img.get_rect().width / 2


def get_img_height(img):
    return img.get_rect().height / 2


def get_img_center(image, pos):
    center_x = pos[0] - get_img_width(image)
    center_y = pos[1] - get_img_height(image)
    return center_x, center_y


def ui_images():
    screen.blit(background_img, (0, 0))
    # screen.blit(circle_img,
    #             (head_center_x - get_img_width(circle_img), head_center_y - get_img_height(circle_img)))
    screen.blit(recordb_img, (get_img_center(recordb_img, record_pos)))
    screen.blit(pb_img, (play_pos[0] - get_img_width(pb_img), play_pos[1] - get_img_height(pb_img)))
    screen.blit(record_img, (record_btn[0], record_btn[1]))
    screen.blit(x_img, (x_btn[0], x_btn[1]))
    screen.blit(play_img, (play_btn[0], play_btn[1]))
    screen.blit(save_img, (save_btn[0], save_btn[1]))


def is_mouse_over_btn(image, image_center, mouse_position):
    return np.sqrt(np.square(image_center[0] - mouse_position[0]) + np.square(image_center[1] - mouse_position[1])) \
           < get_img_width(image)


if __name__ == '__main__':

    # get btn positions
    record_btn = get_img_center(record_img, record_pos)
    x_btn = get_img_center(x_img, x_pos)
    play_btn = get_img_center(play_img, play_pos)
    save_btn = get_img_center(save_img, save_pos)

    # game loop
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                print("Recording: ", is_mouse_over_btn(recordb_img, record_pos, mouse_pos))
                print("Play: ", is_mouse_over_btn(play_img, play_pos, mouse_pos))
                print("Exit: ", is_mouse_over_btn(x_img, x_pos, mouse_pos))
                print("Save: ", is_mouse_over_btn(save_img, save_pos, mouse_pos))

            # if np.sqrt(
            #         np.square(head_center_x - mouse_x) + np.square(head_center_y - mouse_y)) \
            #         < get_img_width(circle_img):
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
