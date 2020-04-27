import pygame
import numpy as np
import threading
import time


class Interface:
    running = True
    DEFAULT_DIMS = (1920, 1080)

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 720), 1, 16)
        self.screen_ratio_to_default = self.screen.get_width() / self.DEFAULT_DIMS[0]

        self.Widget.initial_scale_value = self.screen_ratio_to_default

    class Widget:

        initial_scale_value = 1

        def __init__(self, image, pos, shown=True):
            self.image = image
            self.pos = pos
            self.rect = image.get_rect()
            self.radius = self.rect.width / 2 * self.initial_scale_value
            self.shown = shown

        def get_angle(self, surface, target):
            abs_pos = self.get_abs_pos(surface)

            if (abs_pos[0] - target[0]) == 0:
                return 0 if (abs_pos[1] > target[1]) else 180

            quarter = \
                int(abs_pos[0] <= target[0]) * (1 * int(abs_pos[1] >= target[1]) + 2 * int(abs_pos[1] < target[1])) + \
                int(abs_pos[0] > target[0]) * (4 * int(abs_pos[1] >= target[1]) + 3 * int(abs_pos[1] < target[1]))
            angle = np.rad2deg(np.arctan(abs((abs_pos[1] - target[1])) / abs((abs_pos[0] - target[0]))))

            return int(
                (quarter - 1) * 90 + int(quarter == 2 or quarter == 4) * angle + int(quarter == 1 or quarter == 3) * (
                        90 - angle))

        def get_distance(self, surface, target):
            abs_pos = self.get_abs_pos(surface)
            return np.sqrt(np.square(abs_pos[0] - target[0]) + np.square(abs_pos[1] - target[1]))

        def get_moved_by_polar(self, surface, polar):
            abs_pos = self.get_abs_pos(surface)

            distance = polar[0]
            angle = polar[1]

            if angle <= 180:
                return int(abs_pos[0] + np.sin(np.deg2rad(180 - angle)) * distance), int(
                    abs_pos[1] + np.cos(np.deg2rad(180 - angle)) * distance)
            else:
                return int(abs_pos[0] - np.sin(np.deg2rad(360 - angle)) * distance), int(
                    abs_pos[1] - np.cos(np.deg2rad(360 - angle)) * distance)

        def get_abs_pos(self, surface):
            return np.multiply(self.pos, surface.get_size()).astype(int)

        def display(self, surface, rotate_value=0, scale_value=1):  # not sure if I can say that
            image = pygame.transform.rotozoom(self.image, rotate_value, self.initial_scale_value * scale_value)
            image_rect = image.get_rect(center=self.get_abs_pos(surface))
            surface.blit(image, image_rect)

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
            pause_button=self.Button(pygame.image.load('../Dependencies/Images/pause_button.png'), [0.804, 0.524],
                                     False),
            save_button=self.Button(pygame.image.load('../Dependencies/Images/save_button.png'), [0.903, 0.524]),
            discard_button=self.Button(pygame.image.load('../Dependencies/Images/discard_button.png'), [0.703, 0.524]),
            rec_start_button=self.Button(pygame.image.load('../Dependencies/Images/record_start_button.png'),
                                         [0.804, 0.183]),
            rec_stop_button=self.Button(pygame.image.load('../Dependencies/Images/record_stop_button.png'),
                                        [0.804, 0.183], False)
            )
        )

        self.audio_controller = self.AudioController(
            self.Button(pygame.image.load('../Dependencies/Images/head.png'), [0.269, 0.4]),
            self.Button(pygame.image.load('../Dependencies/Images/circle.png'), [0.269, 0.4]),
            self.Button(pygame.image.load('../Dependencies/Images/jakub.png'), [0.269, 0.4]),
            dict(
                anechoic=self.Button(pygame.image.load('../Dependencies/Images/anechoic.png'), [0.146, 0.911]),
                forest=self.Button(pygame.image.load('../Dependencies/Images/forest.png'), [0.229, 0.911]),
                church=self.Button(pygame.image.load('../Dependencies/Images/church.png'), [0.312, 0.911]),
                cave=self.Button(pygame.image.load('../Dependencies/Images/cave.png'), [0.397, 0.911])
            )
        )

    class AudioController:

        NEW_ANGLE_THRESHOLD = 5

        def __init__(self, head, circle, selection, reverb_buttons):
            self.head = head
            self.circle = circle
            self.selection = selection
            self.reverb_buttons = reverb_buttons
            self.radii = [0.2, 0.4, 0.8, 1.2]
            # self.radii = [0.5, 1, 2, 3]

            self.current_audio_data = dict(angle=-1, radius=0, reverb="anechoic")
            self.previous_audio_data = self.current_audio_data.copy()
            self.full_audio_data = []

        def display(self, surface):
            self.head.display(surface)

            for r in self.radii:
                self.circle.display(surface, 0, r)

            if self.current_audio_data["radius"] > 0:
                selection_pos = self.head.get_moved_by_polar(surface, (
                    self.current_audio_data["radius"] * self.circle.radius, self.current_audio_data["angle"]))

                pygame.draw.circle(surface, (255, 255, 255), selection_pos, 20)
                # self.selection.display(surface, 0, 0.3)

            for button in self.reverb_buttons.values():
                if button.shown:
                    button.display(surface, 0, 1 if not button.hovered else 1.1)

        def check_events(self, surface, mouse_data, playback_state):

            for reverb_button in self.reverb_buttons.values():
                mouse_inside = reverb_button.get_distance(surface, mouse_data["pos"]) < reverb_button.radius
                reverb_button.hovered, reverb_button.pressed = mouse_inside, mouse_inside and mouse_data["clicked"]
                # find which reverb button, if any, is active now

            # This is very inelegant and also stupid but i guess it shows how dumb i am
            if self.reverb_buttons["anechoic"].pressed:
                self.current_audio_data["reverb"] = "anechoic"
            if self.reverb_buttons["forest"].pressed:
                self.current_audio_data["reverb"] = "forest"
            if self.reverb_buttons["church"].pressed:
                self.current_audio_data["reverb"] = "church"
            if self.reverb_buttons["cave"].pressed:
                self.current_audio_data["reverb"] = "cave"

            distance_to_mouse = self.circle.get_distance(surface, mouse_data["pos"])
            mouse_inside = distance_to_mouse < self.circle.radius * 1.4 and mouse_data["pressed"]
            if mouse_inside:
                shortest_distance = self.circle.radius * 1.4
                self.current_audio_data["angle"] = self.head.get_angle(surface, mouse_data["pos"])
                self.current_audio_data["radius"] = 0
                for r in self.radii:
                    distance = np.abs(distance_to_mouse - self.circle.radius * r)
                    if distance < shortest_distance:
                        shortest_distance = distance
                        self.current_audio_data["radius"] = r

            if playback_state["started"]:
                self.previous_audio_data = self.current_audio_data.copy()

            if playback_state["in_process"]:

                if abs(self.current_audio_data["angle"] - self.previous_audio_data["angle"]) > self.NEW_ANGLE_THRESHOLD or \
                        self.current_audio_data["radius"] != self.previous_audio_data["radius"] or \
                        self.current_audio_data["reverb"] != self.previous_audio_data["reverb"]:
                    self.full_audio_data.append((self.previous_audio_data, playback_state["timer"].get_time()))

                    self.previous_audio_data = self.current_audio_data.copy()

            elif playback_state["stopped"]:
                self.full_audio_data.append([self.current_audio_data, playback_state["timer"].get_time()])

    class AudioManager:

        class Timer(threading.Thread):
            def __init__(self):
                super().__init__()
                self.active = True
                self.initial_time = 0

            def run(self):
                self.initial_time = time.time()

                # while self.active:
                #     t0 = time.time()
                #     t1 = t0
                #     while t0 == t1:
                #         t1 = time.time()
                #     self.current_time += t1 - t0

            def get_time(self):
                return time.time() - self.initial_time

                # return self.current_time

        def __init__(self, buttons):
            self.buttons = buttons

            self.recording_state = dict(started=False, stopped=False, in_process=False, timer=self.Timer())
            self.playback_state = dict(started=False, stopped=False, in_process=False, paused=False, timer=self.Timer())

        def display(self, surface):

            for button in self.buttons.values():
                if button.shown:
                    button.display(surface, 0, 1 if not button.hovered else 1.1)

        def check_events(self, surface, mouse_data):
            for button in self.buttons.values():
                if button.shown:
                    mouse_inside = button.get_distance(surface, mouse_data["pos"]) < button.radius
                    button.hovered, button.clicked = mouse_inside, mouse_inside and mouse_data["clicked"]

            self.playback_state["started"] = self.buttons["play_button"].clicked
            self.playback_state["paused"] = self.buttons["pause_button"].clicked

            if self.playback_state["started"]:
                self.playback_state["timer"] = self.Timer()
                self.playback_state["timer"].start()
                self.playback_state["in_process"] = True
                self.buttons["play_button"].replace(self.buttons["pause_button"])

            elif self.playback_state["paused"]:
                self.playback_state["in_process"] = False
                self.playback_state["paused"] = True
                self.buttons["pause_button"].replace(self.buttons["play_button"])

            elif self.playback_state["stopped"]:
                self.playback_state["timer"].active = False
                self.playback_state["timer"].join()
                self.playback_state["in_process"] = False
                self.buttons["pause_button"].replace(self.buttons["play_button"])

            self.recording_state["started"] = self.buttons["rec_start_button"].clicked
            self.recording_state["stopped"] = self.buttons["rec_stop_button"].clicked

            if self.recording_state["started"]:
                self.recording_state["timer"] = self.Timer()
                self.recording_state["timer"].start()
                self.recording_state["in_process"] = True

            elif self.recording_state["stopped"]:
                self.recording_state["timer"].active = False
                self.recording_state["timer"].join()
                self.recording_state["in_process"] = False

            if self.buttons["rec_start_button"].clicked:
                self.buttons["rec_start_button"].replace(self.buttons["rec_stop_button"])
            elif self.buttons["rec_stop_button"].clicked:
                self.buttons["rec_stop_button"].replace(self.buttons["rec_start_button"])

    def update(self):
        # get all the events, let buttons know they're clicked, etc.

        mouse_data = dict(pos=pygame.mouse.get_pos(), pressed=pygame.mouse.get_pressed()[0], clicked=False)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.unicode == 'c':
                self.audio_controller.current_audio_data["angle"] = -1
                self.audio_controller.current_audio_data["radius"] = 0

            elif mouse_data["pressed"] and event.type == pygame.MOUSEBUTTONUP:
                mouse_data["clicked"] = True

        self.audio_manager.check_events(self.screen, mouse_data)

        self.audio_controller.check_events(self.screen, mouse_data, self.audio_manager.playback_state)

        if self.audio_manager.playback_state["in_process"]:
            print(self.audio_manager.playback_state["timer"].get_time())

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

# make buttons pressed infos (recording, playback) dictionaries
