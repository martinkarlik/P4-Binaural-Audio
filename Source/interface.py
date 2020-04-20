import pygame
import numpy as np


class Interface:

    running = True
    DEFAULT_DIMS = (1920, 1080)

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 720), 1, 16)
        self.screen_ratio_to_default = self.screen.get_width() / self.DEFAULT_DIMS[0]

        self.Widget.surface = self.screen
        self.Widget.initial_scale_value = self.screen_ratio_to_default

    class Widget:

        surface = None
        initial_scale_value = 1

        def __init__(self, image, pos, shown=True):
            self.image = image
            self.pos = pos
            self.rect = image.get_rect()
            self.radius = self.rect.width / 2 * self.initial_scale_value
            self.shown = shown

        def get_distance(self, target):
            abs_pos = self.get_abs_pos()
            return np.sqrt(np.square(abs_pos[0] - target[0]) + np.square(abs_pos[1] - target[1]))

        def get_angle(self, target):
            abs_pos = self.get_abs_pos()

            if (abs_pos[0] - target[0]) == 0:
                return 0 if (abs_pos[1] > target[1]) else 180

            quarter = \
                int(abs_pos[0] <= target[0]) * (1 * int(abs_pos[1] >= target[1]) + 2 * int(abs_pos[1] < target[1])) + \
                int(abs_pos[0] > target[0]) * (4 * int(abs_pos[1] >= target[1]) + 3 * int(abs_pos[1] < target[1]))
            angle = np.rad2deg(np.arctan(abs((abs_pos[1] - target[1])) / abs((abs_pos[0] - target[0]))))

            return (quarter - 1) * 90 + int(quarter == 2 or quarter == 4) * angle + int(quarter == 1 or quarter == 3) * (90 - angle)

        def get_abs_pos(self):
            return np.multiply(self.pos, self.surface.get_size()).astype(int)

        def display(self, rotate_value=0, scale_value=1):  # not sure if I can say that
            image = pygame.transform.rotozoom(self.image, rotate_value, self.initial_scale_value * scale_value)
            image_rect = image.get_rect(center=self.get_abs_pos())
            self.surface.blit(image, image_rect)

        def replace(self, other):
            self.shown, other.shown = False, True

    class Button(Widget):
        def __init__(self, image, pos, shown=True):
            super().__init__(image, pos, shown)
            self.hovered = False
            self.pressed = False
            self.clicked = False

        def replace(self, other):
            super().replace(other)
            self.hovered, self.clicked = False, False

    class TextField(Widget):
        def __init__(self, image, pos, show=True):
            super().__init__(image, pos, show)
            self.content = ""


class CreatorInterface(Interface):

    new_angle_threshold = 10

    def __init__(self):
        super().__init__()
        pygame.display.set_caption("3DAB CREATOR")

        self.audio_manager = self.AudioManager(dict(
                play_button=self.Button(pygame.image.load('../Dependencies/Images/play_button.png'), [0.804, 0.524]),
                pause_button=self.Button(pygame.image.load('../Dependencies/Images/pause_button.png'), [0.804, 0.524], False),
                save_button=self.Button(pygame.image.load('../Dependencies/Images/save_button.png'), [0.903, 0.524]),
                discard_button=self.Button(pygame.image.load('../Dependencies/Images/discard_button.png'), [0.703, 0.524]),
                rec_start_button=self.Button(pygame.image.load('../Dependencies/Images/record_start_button.png'), [0.804, 0.183]),
                rec_stop_button=self.Button(pygame.image.load('../Dependencies/Images/record_stop_button.png'), [0.804, 0.183], False)
            )
        )

        self.audio_controller = self.AudioController(
            self.Button(pygame.image.load('../Dependencies/Images/head.png'), [0.269, 0.4]),
            self.Button(pygame.image.load('../Dependencies/Images/circle.png'), [0.269, 0.4]),
            dict(
                anechoic=self.Button(pygame.image.load('../Dependencies/Images/head.png'), [0.269, 0.499]),
                forest=self.Button(pygame.image.load('../Dependencies/Images/head.png'), [0.499, 0.499]),
                church=self.Button(pygame.image.load('../Dependencies/Images/head.png'), [0.499, 0.499]),
                cave=self.Button(pygame.image.load('../Dependencies/Images/head.png'), [0.499, 0.499])
            )
        )

    class AudioController:

        def __init__(self, head, circle, reverb_buttons):
            self.head = head
            self.circle = circle
            self.reverb_buttons = reverb_buttons
            self.distances = [0.2, 0.4, 0.8, 1.2]
            self.selection_shown = False
            self.selection = [0, 0]
            self.time = 0

        def polar_to_cartesian(self, polar_coord):
            x = int(np.cos(np.deg2rad(polar_coord[0])) * polar_coord[1])
            y = int(np.sin(np.deg2rad(polar_coord[0])) * polar_coord[1])
            return x, y

        def display(self, surface):
            self.head.display()

            for distance in self.distances:
                self.circle.display(0, distance)

            if self.selection_shown:
                cartesian_pos = self.polar_to_cartesian(self.selection)
                abs_pos = self.circle.get_abs_pos()
                pygame.draw.circle(surface, (255, 255, 255), (abs_pos[0] + cartesian_pos[0], abs_pos[1] + cartesian_pos[1]), 20)
                print("drawing! ")

            # surface!!

        def check_events(self, mouse_pos, mouse_pressed, mouse_clicked):
            for reverb_button in self.reverb_buttons.values():
                mouse_inside = reverb_button.get_distance(mouse_pos) < reverb_button.radius
                reverb_button.hovered, reverb_button.pressed = mouse_inside, mouse_inside and mouse_pressed

            # what happens if some button is pressed

            for distance in self.distances:

                mouse_inside = abs(self.circle.get_distance(mouse_pos) - self.circle.radius * distance) < 10
                self.selection_shown = mouse_inside and mouse_pressed
                if self.selection_shown:
                    self.selection = [self.circle.radius * distance, self.circle.get_angle(mouse_pos)]
                    print("Selection: ", self.selection)
                    return

    class AudioManager:

        def __init__(self, buttons):
            self.buttons = buttons
            self.recording_started = False
            self.recording_in_process = False
            self.recording_stopped = False

            self.playback_started = False
            self.playback_paused = False

        def display(self, surface):

            for button in self.buttons.values():
                if button.shown:
                    button.display(0, 1 if not button.hovered else 1.1)

        def check_events(self, mouse_pos, mouse_pressed, mouse_clicked):
            for button in self.buttons.values():
                if button.shown:
                    mouse_inside = button.get_distance(mouse_pos) < button.radius
                    button.hovered, button.clicked = mouse_inside, mouse_inside and mouse_clicked

            self.playback_started = self.buttons["play_button"].clicked
            self.playback_paused = self.buttons["pause_button"].clicked

            if self.buttons["play_button"].clicked:
                self.buttons["play_button"].replace(self.buttons["pause_button"])
            elif self.buttons["pause_button"].clicked:
                self.buttons["pause_button"].replace(self.buttons["play_button"])

            self.recording_started = self.buttons["rec_start_button"].clicked
            self.recording_stopped = self.buttons["rec_stop_button"].clicked
            if self.recording_started:
                self.recording_in_process = True
            if self.recording_stopped:
                self.recording_in_process = False

            if self.buttons["rec_start_button"].clicked:
                self.buttons["rec_start_button"].replace(self.buttons["rec_stop_button"])
            elif self.buttons["rec_stop_button"].clicked:
                self.buttons["rec_stop_button"].replace(self.buttons["rec_start_button"])

    def update(self):
        # get all the events, let buttons know they're clicked, etc.

        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        mouse_clicked = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.unicode == 'c':
                self.audio_controller.head = None
            elif event.type == pygame.MOUSEBUTTONUP and mouse_pressed:
                mouse_clicked = True

        self.audio_manager.check_events(mouse_pos, mouse_pressed, mouse_clicked)
        self.audio_controller.check_events(mouse_pos, mouse_pressed, mouse_clicked)

        self.audio_controller.time += 1

        # display all the visuals
        self.screen.fill((20, 40, 80))

        self.audio_manager.display(self.screen)
        self.audio_controller.display(self.screen)

        pygame.display.update()


class ListenerInterface(Interface):

    def __init__(self):
        super().__init__()

    def update(self):
        return

