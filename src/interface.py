import pygame
import numpy as np
import threading
import time
from scipy.interpolate import interp1d
from tkinter import messagebox
import tkinter as t


text_blue = (62, 132, 240)


class Interface:
    running = True

    def __init__(self):
        pygame.init()
        self.root = t.Tk()

    # This is a static method. You can tell, because if you look carefully, it has a decorated "@staticmethod" above it.
    # The reason it is static is because back in the day when it wasn't static, pycharm would be like:
    # "Yo make this static!" It does some stuff like if user is stupid it tells them that it's not their fault etc.

    @staticmethod
    def show_error_message(message):
        messagebox.showinfo("Error", message)

    # This is a Widget class. Originally it was called UI_Element but then I was like Nah let's call it Widget.
    # It represents any UI_Element, such as buttons, text fields, ... I could go on
    # but I can't cause we don't have nothing else than buttons and text fields. They inherit from Widget.

    class Widget:

        initial_scale_value = 1  # Ratio between current screen dims and default dims.

        def __init__(self, pos, shown=True):
            self.pos = pos
            self.shown = shown

        def get_angle(self, surface, target):  # Gets azimuth angle in degrees to a different Widget / mouse.
            abs_pos = self.get_abs_pos(surface)

            # You'd think that to calculate angle from 2 positions would be easy, huh? Yeah so did I.
            # Some trigonometry...

            int(x < 0) * (360 + x) + int(x >= 0) * x

            if (abs_pos[0] - target[0]) == 0:  # The case when arctan cannot be calculated (when x diff is 0)
                return 0 if (abs_pos[1] > target[1]) else 180

            # Arctan doesn't really like negative numbers (negative distances), so we'll have to find which
            # quarter we are in and only then we can get the azimuth angle.
            quarter = \
                int(abs_pos[0] <= target[0]) * (1 * int(abs_pos[1] >= target[1]) + 2 * int(abs_pos[1] < target[1])) + \
                int(abs_pos[0] > target[0]) * (4 * int(abs_pos[1] >= target[1]) + 3 * int(abs_pos[1] < target[1]))

            angle = np.rad2deg(np.arctan(abs((abs_pos[1] - target[1])) / abs((abs_pos[0] - target[0]))))

            return int((quarter - 1) * 90 + int(quarter == 2 or quarter == 4) * angle + int(quarter == 1 or quarter == 3) * (
                        90 - angle))
            # Just trust that it gets the angle.

        def get_euclidean_distance(self, surface, target):
            abs_pos = self.get_abs_pos(surface)
            return np.sqrt(np.square(abs_pos[0] - target[0]) + np.square(abs_pos[1] - target[1]))

        def get_manhattan_distance(self, surface, target):
            abs_pos = self.get_abs_pos(surface)
            distance_x = abs(abs_pos[0] - target[0])
            distance_y = abs(abs_pos[1] - target[1])
            return distance_x, distance_y

        def get_moved_by_polar(self, surface, polar):  # Gets absolute position of an object moved by a vector in polar form (angle, distance).
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

        def replace(self, other):  # Replaces widget with another, e.g. when play / pause button is clicked.
            self.shown, other.shown = False, True

    class Button(Widget):  # Widget with clicking functionality, should be self-explanatory.
        def __init__(self, image, pos, shown=True):
            super().__init__(pos, shown)
            self.image = image
            self.size = (
                image.get_rect().width * self.initial_scale_value, image.get_rect().height * self.initial_scale_value)
            self.radius = self.size[0] / 2
            self.hovered = False
            self.pressed = False
            self.clicked = False

        def display(self, surface, rotate_value=0, scale_value=1):
            image = pygame.transform.rotozoom(self.image, rotate_value, self.initial_scale_value * scale_value)
            image_rect = image.get_rect(center=self.get_abs_pos(surface))
            surface.blit(image, image_rect)

        def replace(self, other):
            super().replace(other)
            self.hovered, self.clicked = False, False

    class TextField(Widget):  # Widget with text-fieldy functionality.

        def __init__(self, pos, text, size, shown=True):
            super().__init__(pos, shown)
            self.font = pygame.font.Font('C:/Windows/Fonts/segoeuil.ttf', int(size * self.initial_scale_value))
            self.text = text

        def display(self, surface, rotate_value=0, scale_value=1):
            text = self.font.render(self.text, True, text_blue)
            text_rect = text.get_rect(center=self.get_abs_pos(surface))
            surface.blit(text, text_rect)


class CreatorInterface(Interface):
    DEFAULT_DIMS = (1920, 1080)

    def __init__(self):
        super().__init__()
        pygame.display.set_caption("3DAB CREATOR")

        self.screen = pygame.display.set_mode((1280, 720), 1, 16)
        self.screen_ratio_to_default = self.screen.get_width() / self.DEFAULT_DIMS[0]

        self.Widget.initial_scale_value = self.screen_ratio_to_default

        self.audio_manager = self.AudioManager(
            dict(
                play_button=self.Button(pygame.image.load('../dependencies/images/play_button.png'), [0.872, 0.300]),
                pause_button=self.Button(pygame.image.load('../dependencies/images/pause_button.png'), [0.872, 0.300],
                                         False),
                save_button=self.Button(pygame.image.load('../dependencies/images/save_button.png'), [0.872, 0.565]),
                open_button=self.Button(pygame.image.load('../dependencies/images/1open_file.png'), [0.766, 0.6]),
                edit_button=self.Button(pygame.image.load('../dependencies/images/edit_button.png'),
                                        [0.660, 0.565]),
                editing_button=self.Button(pygame.image.load('../dependencies/images/editing_button.png'),
                                           [0.660, 0.565], False),
                rec_start_button=self.Button(pygame.image.load('../dependencies/images/record_start_button.png'),
                                             [0.660, 0.300]),
                rec_stop_button=self.Button(pygame.image.load('../dependencies/images/record_stop_button.png'),
                                            [0.660, 0.300], False)
            ),
            dict(
                rec_text=self.TextField([0.658, 0.115], "Record", 60, True),
                play_text=self.TextField([0.870, 0.115], "Play", 60, True),
                edit_text=self.TextField([0.658, 0.652], "Edit audio", 30, True),
                save_text=self.TextField([0.870, 0.652], "Save", 30, True),
                record_time_text=self.TextField([0.759, 0.780], "Recorded time", 35, True),
                playback_timer=self.TextField([0.7, 0.880], "00:00", 75, True),  # Martin Use this
                recording_timer=self.TextField([0.82, 0.880], "00:00", 75, True),  # and this
                slash_symbol=self.TextField([0.76, 0.880], "/", 75, True),

                n_is_for_narrator=self.TextField([0.269, 0.53], "Press 'N' for Narrator", 25, True),
                anechoic_text=self.TextField([0.114, 0.974], "Anechoic", 30, True),
                forest_text=self.TextField([0.217, 0.974], "Forest", 30, True),
                church_text=self.TextField([0.321, 0.974], "Church", 30, True),
                cave_text=self.TextField([0.424, 0.974], "Cave", 30, True)
            )
        )

        self.audio_controller = self.AudioController(
            self.Button(pygame.image.load('../dependencies/images/audio_controller.png'), [0.269, 0.4]),
            self.Button(pygame.image.load('../dependencies/images/marker.png'), [0.269, 0.4]),
            dict(
                anechoic=self.Button(pygame.image.load('../dependencies/images/anechoic.png'), [0.114, 0.890]),
                forest=self.Button(pygame.image.load('../dependencies/images/forest.png'), [0.217, 0.890]),
                church=self.Button(pygame.image.load('../dependencies/images/church.png'), [0.321, 0.890]),
                cave=self.Button(pygame.image.load('../dependencies/images/cave.png'), [0.424, 0.890])
            )
        )

    class AudioController:

        def __init__(self, head, selection, reverb_buttons):
            self.head = head
            self.selection = selection
            self.reverb_buttons = reverb_buttons

            self.radii = [0.225, 0.55, 0.775, 1]

            self.current_filter_data = dict(angle=127, radius=1, reverb="anechoic")
            self.previous_filter_data = self.current_filter_data.copy()
            self.full_filter_data = []

        def display(self, surface):
            self.head.display(surface, 0, 1)


            if self.current_filter_data["radius"] > 0:
                selection_pos = self.head.get_moved_by_polar(surface, (
                    self.current_filter_data["radius"] * self.head.radius, self.current_filter_data["angle"]))

                pygame.draw.circle(surface, (253, 92, 92), selection_pos, 20)
                self.selection.display(surface, 0, 0)

            self.reverb_buttons[self.current_filter_data["reverb"]].display(surface, 0, 1.2)
            for button in self.reverb_buttons.values():
                if button.shown:
                    if button != self.reverb_buttons[self.current_filter_data["reverb"]]:
                        button.display(surface, 0, 1 if not button.hovered else 1.1)

        def check_events(self, surface, mouse_data, edit_state, playback_state):

            for reverb_button in self.reverb_buttons.values():
                mouse_inside = reverb_button.get_euclidean_distance(surface, mouse_data["pos"]) < reverb_button.radius
                reverb_button.hovered, reverb_button.pressed = mouse_inside, mouse_inside and mouse_data["clicked"]
                # find which reverb button, if any, is active now

            if self.reverb_buttons["anechoic"].pressed:
                self.current_filter_data["reverb"] = "anechoic"
            if self.reverb_buttons["forest"].pressed:
                self.current_filter_data["reverb"] = "forest"
            if self.reverb_buttons["church"].pressed:
                self.current_filter_data["reverb"] = "church"
            if self.reverb_buttons["cave"].pressed:
                self.current_filter_data["reverb"] = "cave"

            distance_to_mouse = self.head.get_euclidean_distance(surface, mouse_data["pos"])
            mouse_inside = distance_to_mouse < self.head.radius * 1.4 and mouse_data["pressed"]

            if mouse_inside:
                self.current_filter_data["angle"] = self.head.get_angle(surface, mouse_data["pos"])
                shortest_distance = self.head.radius * 1.4
                self.current_filter_data["radius"] = 0
                for r in self.radii:
                    distance = np.abs(distance_to_mouse - self.head.radius * r)
                    if distance < shortest_distance:
                        shortest_distance = distance
                        self.current_filter_data["radius"] = r

            if edit_state["started"]:
                edit_state["stopped"] = False
                self.previous_filter_data = self.current_filter_data.copy()

            if edit_state["in_process"]:

                if self.current_filter_data["angle"] != self.previous_filter_data["angle"] or \
                        self.current_filter_data["radius"] != self.previous_filter_data["radius"] or \
                        self.current_filter_data["reverb"] != self.previous_filter_data["reverb"]:

                    if len(self.full_filter_data) > 0:
                        position_time = edit_state["timer"].get_time() - np.sum(
                            np.array(self.full_filter_data)[:, 1])
                        self.full_filter_data.append((self.previous_filter_data, position_time))
                    else:
                        position_time = edit_state["timer"].get_time()
                        self.full_filter_data.append((self.previous_filter_data, position_time))

                    self.previous_filter_data = self.current_filter_data.copy()

            if edit_state["stopped"]:
                if len(self.full_filter_data) > 0:
                    position_time = edit_state["timer"].get_time() - np.sum(np.array(self.full_filter_data)[:, 1])
                    self.full_filter_data.append((self.previous_filter_data, position_time))
                else:
                    position_time = edit_state["timer"].get_time()
                    self.full_filter_data.append((self.previous_filter_data, position_time))

        def get_filter_data(self):
            return np.array(self.full_filter_data)

        def clear_filter_data(self):
            self.current_filter_data = dict(angle=-1, radius=0, reverb="anechoic")
            self.previous_filter_data = self.current_filter_data.copy()
            self.full_filter_data = []

    class AudioManager:

        class Timer(threading.Thread):
            def __init__(self):
                super().__init__()
                self.active = False
                self.initial_time = 0

            def run(self):
                self.initial_time = time.time()
                self.active = True

            def get_time(self):
                return time.time() - self.initial_time if self.active else 0.0

                # return self.current_time

        def __init__(self, buttons, text_fields):
            self.buttons = buttons
            self.text_fields = text_fields

            self.recording_state = dict(started=False, stopped=False, in_process=False, timer=self.Timer())
            self.playback_state = dict(started=False, stopped=False, in_process=False, paused=False, terminated=False,
                                       timer=self.Timer())
            self.edit_state = dict(started=False, stopped=False, in_process=False, paused=False, terminated=False,
                                   timer=self.Timer())

        def display(self, surface):

            for button in self.buttons.values():
                if button.shown:
                    button.display(surface, 0, 1 if not button.hovered else 1.1)

            for text_field in self.text_fields.values():
                if text_field.shown:
                    text_field.display(surface, 0, 1)

        def check_events(self, surface, mouse_data):

            for button in self.buttons.values():
                if button.shown:
                    mouse_inside = button.get_euclidean_distance(surface, mouse_data["pos"]) < button.radius
                    button.hovered, button.clicked = mouse_inside, mouse_inside and mouse_data["clicked"]

            self.recording_state["started"] = self.buttons["rec_start_button"].clicked
            self.recording_state["stopped"] = self.buttons["rec_stop_button"].clicked

            if self.recording_state["started"]:
                self.recording_state["timer"] = self.Timer()
                self.recording_state["timer"].start()
                self.recording_state["in_process"] = True
                self.buttons["rec_start_button"].replace(self.buttons["rec_stop_button"])
                self.text_fields["playback_timer"].text = "00:00"

            elif self.recording_state["stopped"]:

                self.recording_state["timer"].active = False
                self.recording_state["timer"].join()
                self.recording_state["in_process"] = False
                self.buttons["rec_stop_button"].replace(self.buttons["rec_start_button"])

            elif self.recording_state["in_process"]:
                rec_time = int(self.recording_state["timer"].get_time())

                minutes = f"0{rec_time // 60}" if rec_time // 60 < 10 else f"{rec_time // 60}"
                seconds = f"0{rec_time % 60}" if rec_time % 60 < 10 else f"{rec_time % 60}"
                self.text_fields["recording_timer"].text = minutes + ":" + seconds

            self.playback_state["started"] = self.buttons["play_button"].clicked
            self.playback_state["paused"] = self.buttons["pause_button"].clicked and False  # problem? fucking sue me

            if self.playback_state["started"]:
                self.playback_state["timer"] = self.Timer()
                self.playback_state["timer"].start()
                self.playback_state["in_process"] = True
                self.buttons["play_button"].replace(self.buttons["pause_button"])

            elif self.playback_state["terminated"]:
                self.playback_state["stopped"] = True
                self.playback_state["terminated"] = False

            elif self.playback_state["stopped"]:
                self.playback_state["timer"].active = False
                self.playback_state["timer"].join()
                self.playback_state["stopped"] = False
                self.playback_state["in_process"] = False
                self.buttons["pause_button"].replace(self.buttons["play_button"])

            if self.playback_state["in_process"]:
                play_time = int(self.playback_state["timer"].get_time())

                minutes = f"0{play_time // 60}" if play_time // 60 < 10 else f"{play_time // 60}"
                seconds = f"0{play_time % 60}" if play_time % 60 < 10 else f"{play_time % 60}"
                self.text_fields["playback_timer"].text = minutes + ":" + seconds

            elif self.playback_state["paused"]:
                self.playback_state["in_process"] = False
                self.buttons["pause_button"].replace(self.buttons["play_button"])

            self.edit_state["started"] = self.buttons["edit_button"].clicked
            self.edit_state["paused"] = self.buttons["editing_button"].clicked

            if self.edit_state["started"]:
                self.edit_state["timer"] = self.Timer()
                self.edit_state["timer"].start()
                self.edit_state["in_process"] = True
                self.buttons["edit_button"].replace(self.buttons["editing_button"])

            elif self.edit_state["terminated"]:
                self.edit_state["stopped"] = True
                self.edit_state["terminated"] = False

            elif self.edit_state["stopped"]:
                self.edit_state["timer"].active = False
                self.edit_state["timer"].join()
                self.edit_state["stopped"] = False
                self.edit_state["in_process"] = False
                self.buttons["editing_button"].replace(self.buttons["edit_button"])

            if self.edit_state["in_process"]:
                edit_time = int(self.edit_state["timer"].get_time())

                minutes = f"0{edit_time // 60}" if edit_time // 60 < 10 else f"{edit_time // 60}"
                seconds = f"0{edit_time % 60}" if edit_time % 60 < 10 else f"{edit_time % 60}"
                self.text_fields["playback_timer"].text = minutes + ":" + seconds

            elif self.edit_state["paused"]:
                self.edit_state["in_process"] = False
                self.edit_state["paused"] = True
                self.buttons["editing_button"].replace(self.buttons["edit_button"])

    def update(self):
        mouse_data = dict(pos=pygame.mouse.get_pos(), pressed=pygame.mouse.get_pressed()[0], clicked=False)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.unicode == 'n':
                self.audio_controller.current_filter_data["angle"] = -1
                self.audio_controller.current_filter_data["radius"] = 0
                self.audio_controller.current_filter_data["reverb"] = "anechoic"

            elif mouse_data["pressed"] and event.type == pygame.MOUSEBUTTONUP:
                mouse_data["clicked"] = True

        self.audio_manager.check_events(self.screen, mouse_data)
        self.audio_controller.check_events(self.screen, mouse_data, self.audio_manager.edit_state, self.audio_manager.playback_state)

        # display all the visuals
        self.screen.fill((40, 45, 46))

        self.audio_manager.display(self.screen)
        self.audio_controller.display(self.screen)

        self.root.withdraw()
        pygame.display.update()


class ListenerInterface(Interface):
    DEFAULT_DIMS = (1080, 1920)

    def __init__(self):
        super().__init__()
        pygame.display.set_caption("3DAB LISTENER")
        self.screen = pygame.display.set_mode((480, 852), 1, 16)
        self.screen_ratio_to_default = self.screen.get_width() / self.DEFAULT_DIMS[0]

        self.Widget.initial_scale_value = self.screen_ratio_to_default

        self.pulse_sound_location = (0.7, 0.4)

        self.player_controller = self.PlayerController(dict(
            jump_forward=self.Button(pygame.image.load('../dependencies/images/1jump_forward.png'), [0.8, 0.67]),
            jump_backwards=self.Button(pygame.image.load('../dependencies/images/1jump_backwards.png'), [0.2, 0.67]),
            play_button=self.Button(pygame.image.load('../dependencies/images/1play_button.png'), [0.5, 0.67]),
            pause_button=self.Button(pygame.image.load('../dependencies/images/1pause_button.png'), [0.5, 0.67],
                                     False),
            open_file_button=self.Button(pygame.image.load('../dependencies/images/1open_file.png'),
                                         [0.18, 0.93]),
            reset_headtracking_button=self.Button(pygame.image.load('../dependencies/images/1reset_headtracking.png'),
                                                  [0.45, 0.93]),

        ),

            self.Button(pygame.image.load('../dependencies/images/1pulse.png'), self.pulse_sound_location),
            self.Button(pygame.image.load('../dependencies/images/1slider.png'), [0.5, 0.8]),
            self.Button(pygame.image.load('../dependencies/images/1background.png'), [0.5, 0.5]),
            self.Button(pygame.image.load('../dependencies/images/1head.png'), [0.5, 0.25])
        )

    class PlayerController:

        def __init__(self, buttons, pulse, slider, background, head):

            self.pulse = pulse
            self.buttons = buttons
            self.head = head
            self.slider = slider
            self.background = background
            self.slider_position = 25
            self.playing_progress = 1

            # self.paused_state = dict(started=False)
            self.playback_state = dict(started=False, stopped=False, in_process=False, paused=False)

        def display(self, surface):

            self.background.display(surface)
            self.head.display(surface)
            self.slider.display(surface)
            self.pulse.display(surface)

            selection_pos = (self.slider_position, self.slider.get_abs_pos(surface)[1])
            pygame.draw.circle(surface, (112, 199, 172), selection_pos, 20)

            for button in self.buttons.values():
                if button.shown:
                    button.display(surface, 0, 1 if not button.hovered else 1.1)

        def check_events(self, surface, mouse_data):

            distance_to_mouse = self.slider.get_manhattan_distance(surface, mouse_data["pos"])

            mouse_inside = distance_to_mouse[0] < self.slider.size[0] / 2 and distance_to_mouse[1] < self.slider.size[
                1] / 2 and mouse_data["pressed"]

            self.playing_progress = interp1d([25, 455], [0, 100])

            if mouse_inside:
                self.slider_position = mouse_data["pos"][0]

            for button in self.buttons.values():
                if button.shown:
                    mouse_inside = button.get_euclidean_distance(surface, mouse_data["pos"]) < button.radius
                    button.hovered, button.clicked = mouse_inside, mouse_inside and mouse_data["clicked"]

            self.playback_state["started"] = self.buttons["play_button"].clicked
            self.playback_state["paused"] = self.buttons["pause_button"].clicked

            if self.playback_state["started"]:
                self.playback_state["in_process"] = True
                self.playback_state["stopped"] = False
                self.buttons["play_button"].replace(self.buttons["pause_button"])

            elif self.playback_state["paused"]:
                self.playback_state["in_process"] = False
                self.playback_state["paused"] = True
                self.buttons["pause_button"].replace(self.buttons["play_button"])

            elif self.playback_state["stopped"]:
                self.playback_state["in_process"] = False
                self.buttons["pause_button"].replace(self.buttons["play_button"])

    def update(self):
        mouse_data = dict(pos=pygame.mouse.get_pos(), pressed=pygame.mouse.get_pressed()[0], clicked=False)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif mouse_data["pressed"] and event.type == pygame.MOUSEBUTTONUP:
                mouse_data["clicked"] = True

        self.player_controller.check_events(self.screen, mouse_data)
        self.player_controller.display(self.screen)

        self.root.withdraw()
        pygame.display.update()
