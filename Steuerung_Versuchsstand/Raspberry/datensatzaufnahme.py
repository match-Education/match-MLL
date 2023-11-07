#!/usr/bin/env python3
import tkinter
import tkinter.messagebox
from tkinter import *
from datetime import datetime
import os
from tkinter import filedialog, StringVar
import time
import cv2
import RPi.GPIO as GPIO
import os
import serial
from picamera2 import Picamera2
from picamera2.controls import Controls
import libcamera
import numpy as np
from PIL import Image, ImageTk
from os.path import exists
import customtkinter

import functions


customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme(
    "blue"
)  # Themes: "blue" (standard), "green", "dark-blue"


class App(customtkinter.CTk):
    # WIDTH = 1280 # 920
    # HEIGHT = 820 # 520

    camera = Picamera2()

    # resolution = (2048, 1536)  # 4:3
    resolution = camera.sensor_resolution
    aspect_ratio = resolution[0] / resolution[1]
    # camera.resolution = resolution
    # camera.shutter_speed = 3000
    # camera.iso = 150
    # camera.brightness = 60
    # camera.sharpness = 25
    # camera.exposure_mode = 'sports'  # off, sports, night
    controls = {"ExposureTime": 3500, "AnalogueGain": 2.5, "ColourGains": (2.2, 1.9)}
    capture_config = camera.create_still_configuration(controls=controls)
    camera.configure(capture_config)
    camera.start()

    arduino = serial.Serial("/dev/ttyACM0", baudrate=115200, timeout=10000)

    def __init__(self):
        super().__init__()

        self.Class_Choice = StringVar()
        self.counters = {}
        self.counter = StringVar()
        self.labels = []

        self.crop_start_x = 870
        self.crop_start_y = 110
        self.crop_groesse = 2450

        self.info_text = StringVar()

        home = os.path.expanduser(f"~{os.getlogin()}/")
        self.Datensatzaufnahme = os.path.join(home, "MLL/Datensatzaufnahme")

        self._save = False
        self._ready = False

        # ============ main window ============

        self.dpi = self.winfo_fpixels("1i")
        self.widget_scaling = 1.2 * self.dpi / 96
        # self.window_scaling = 1.1

        customtkinter.set_widget_scaling(
            self.widget_scaling
        )  # widget dimensions and text size
        customtkinter.set_spacing_scaling(
            self.widget_scaling
        )  # padding and place positions
        # customtkinter.set_window_scaling(self.window_scaling)  # window geometry dimensions

        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()

        # x_cordinate = int((screen_width/2) - (App.WIDTH*window_scaling/2))
        # y_cordinate = int((screen_height/2) - (App.HEIGHT*window_scaling/2))

        self.title("MLL-Datensatzaufnahme")
        self.attributes("-fullscreen", True)
        # self.geometry(f"{App.WIDTH}x{App.HEIGHT}+{x_cordinate}+{y_cordinate}")
        icon = tkinter.PhotoImage(file="Icon.png")
        self.iconphoto(True, icon)
        # self.resizable(False, False)
        self.protocol(
            "WM_DELETE_WINDOW", self.on_closing
        )  # call .on_closing() when app gets closed

        # ============ create three frames ============

        # configure grid layout (2x1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.frame_left_width = self.screen_width * 1.25 // 10
        self.frame_left = customtkinter.CTkFrame(
            master=self,
            # width=180,
            width=self.frame_left_width,
            corner_radius=0,
        )
        self.frame_left.grid_propagate(False)
        self.frame_left.grid(row=0, column=0, rowspan=3, sticky="nswe")

        self.frame_right_width = self.screen_width * 8 // 10
        self.frame_right_height = self.screen_height * 7 // 10
        self.frame_right = customtkinter.CTkFrame(
            master=self, width=self.frame_right_width, height=self.frame_right_height
        )
        self.frame_right.grid_propagate(False)
        self.frame_right.grid(row=1, column=1, sticky="nswe", padx=20, pady=10)

        self.label_smallprint = customtkinter.CTkLabel(
            master=self,
            text="\u00A9 Institut für Montagetechnik - 2022 - Masterlabor Maschinelles Lernen in der Produktionstechnik",  # - Made with \u2764\ufe0f by Yassine Neifer",
            text_font=("Roboto Medium", -10),
            justify=LEFT,
        )  # font name and size in px
        self.label_smallprint.grid(row=2, column=1, pady=5, padx=20, sticky="sw")

        self.frame_title = customtkinter.CTkFrame(
            master=self,
            width=self.frame_right_width,
            height=self.screen_height * 1 // 10,
        )
        self.frame_title.grid_propagate(False)
        self.frame_title.grid(row=0, column=1, padx=20, pady=10, sticky="ew")

        # ============ frame_title ============
        self.frame_title.grid_columnconfigure(0, weight=0)
        self.frame_title.grid_columnconfigure(1, weight=1)
        self.frame_title.grid_rowconfigure(0, weight=1)

        img = Image.open("match3W.png")
        scale = img.height / (self.screen_height * 0.8 // 10 * self.widget_scaling)
        img = img.resize((int(img.width / scale), int(img.height / scale)))
        self.match_logo_white = ImageTk.PhotoImage(img)

        img = Image.open("match3B.png")
        scale = img.height / (self.screen_height * 0.8 // 10 * self.widget_scaling)
        img = img.resize((int(img.width / scale), int(img.height / scale)))
        self.match_logo_black = ImageTk.PhotoImage(img)

        img = Image.open("match_Strukturleiste.png")
        scale = img.height / (self.screen_height * 0.8 // 10 * self.widget_scaling)
        img = img.resize((int(self.frame_right_width), int(img.height / scale)))
        self.match_bg = ImageTk.PhotoImage(img)

        self.label_title_bg = customtkinter.CTkLabel(
            master=self.frame_title,
            # bg_color=("gray75", "gray30"),
            image=self.match_bg,
            corner_radius=10,
        )  # font name and size in px
        self.label_title_bg.grid(
            row=0, column=0, columnspan=2, pady=0, padx=0, sticky=""
        )

        self.label_title_logo = customtkinter.CTkLabel(
            master=self.frame_title,
            # bg_color=("gray75", "gray30"),
            image=self.match_logo_white,
        )  # font name and size in px
        self.label_title_logo.grid(
            row=0, column=0, pady=5, padx=(100, 10), ipadx=10, sticky=""
        )

        self.label_title_text = customtkinter.CTkLabel(
            master=self.frame_title,
            text="Masterlabor: Maschinelles Lernen in der Produktionstechnik",
            text_font=("Roboto Medium", -24),
            # bg_color=("gray75", "gray30"),
            height=self.screen_height * 0.3 // 10,
            # image=self.match_logo,
            # compound='left'
        )  # font name and size in px
        self.label_title_text.grid(
            row=0, column=1, pady=5, padx=150, ipadx=10, sticky=""
        )

        # ============ frame_left ============

        # configure grid layout (1x11)
        self.frame_left.grid_columnconfigure(0, weight=1)
        self.frame_left.grid_rowconfigure(
            0, minsize=10
        )  # empty row with minsize as spacing
        self.frame_left.grid_rowconfigure(4, weight=1)  # empty row as spacing
        self.frame_left.grid_rowconfigure(
            8, weight=2
        )  # empty row with minsize as spacing
        self.frame_left.grid_rowconfigure(
            12, minsize=10
        )  # empty row with minsize as spacing

        self.label_2 = customtkinter.CTkLabel(
            master=self.frame_left,
            text="Visualisation Tools",
            text_font=("Roboto Medium", -18),
        )  # font name and size in px
        self.label_2.grid(row=1, column=0, pady=10)

        self.button_preview = customtkinter.CTkButton(
            master=self.frame_left,
            text="Preview",
            fg_color="#b3cb23",
            hover_color="#d4dc54",
            text_color="#000000",
            width=self.frame_left_width // 2,
            # bg_color=,
            command=self.Preview_clicked,
        )
        self.button_preview.grid(row=2, column=0, pady=10, padx=20)

        self.button_crop = customtkinter.CTkButton(
            master=self.frame_left,
            text="Crop Parameters",
            fg_color="#b3cb23",
            hover_color="#d4dc54",
            text_color="#000000",
            width=self.frame_left_width // 2,
            command=self.Crop_clicked,
        )
        self.button_crop.grid(row=3, column=0, pady=10, padx=20)

        self.label_1 = customtkinter.CTkLabel(
            master=self.frame_left, text="Dataset:", text_font=("Roboto Medium", -18)
        )  # font name and size in px
        self.label_1.grid(row=5, column=0, pady=10, padx=10)

        self.button_new = customtkinter.CTkButton(
            master=self.frame_left,
            text="New",
            fg_color="#b3cb23",
            hover_color="#d4dc54",
            text_color="#000000",
            width=self.frame_left_width // 2,
            command=self.New_clicked,
        )
        self.button_new.grid(row=6, column=0, pady=10, padx=20)

        self.button_browse = customtkinter.CTkButton(
            master=self.frame_left,
            text="Browse",
            fg_color="#b3cb23",
            hover_color="#d4dc54",
            text_color="#000000",
            width=self.frame_left_width // 2,
            command=self.Browse_clicked,
        )
        self.button_browse.grid(row=7, column=0, pady=10, padx=20)

        self.button_quit = customtkinter.CTkButton(
            master=self.frame_left,
            text="Quit",
            fg_color="#b3cb23",
            hover_color="#d4dc54",
            text_color="#000000",
            width=self.frame_left_width // 2,
            command=self.quit_clicked,
        )
        self.button_quit.grid(row=9, column=0, pady=10, padx=20)

        self.switch_save = customtkinter.CTkSwitch(
            master=self.frame_left,
            text="Save Mode",
            progress_color="#b3cb23",
            command=self.save_mode,
        )
        self.switch_save.grid(row=10, column=0, pady=10, padx=20, sticky="w")

        self.switch_mode = customtkinter.CTkSwitch(
            master=self.frame_left,
            text="Dark Mode",
            progress_color="#b3cb23",
            command=self.dark_mode,
        )
        self.switch_mode.grid(row=11, column=0, pady=10, padx=20, sticky="w")

        self.x_entry = customtkinter.CTkEntry(
            master=self.frame_left,
            placeholder_text="x-offset:",
            width=self.frame_left_width // 2,
        )
        self.y_entry = customtkinter.CTkEntry(
            master=self.frame_left,
            placeholder_text="y-offset:",
            width=self.frame_left_width // 2,
        )
        self.size_entry = customtkinter.CTkEntry(
            master=self.frame_left,
            placeholder_text="size:",
            width=self.frame_left_width // 2,
        )
        self.button_crop_confirm = customtkinter.CTkButton(
            master=self.frame_left,
            text="Ok",
            fg_color="#b3cb23",
            hover_color="#d4dc54",
            text_color="#000000",
            width=self.frame_left_width // 2,
            command=self.crop_confirm_clicked,
        )

        # ============ frame_right ============

        # configure grid layout (3x7)
        self.frame_right.rowconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=1)
        self.frame_right.columnconfigure((0, 1), weight=3)
        self.frame_right.columnconfigure(2, weight=1)

        # ============ canvas ============

        self.img_height = self.frame_right_height * 7 // 8
        self.img_width = self.img_height * self.aspect_ratio

        self.frame_img = customtkinter.CTkFrame(
            master=self.frame_right,
            width=self.img_width,
            height=self.img_height,
            fg_color=("gray75", "gray30"),
        )
        self.frame_img.grid(row=0, column=0, rowspan=7, pady=20, padx=20)

        self.img_icon = PhotoImage(file="Deckel_icon.png")
        self.image_preview_canvas = tkinter.Canvas(
            self.frame_img,
            height=self.img_height * self.widget_scaling,
            width=self.img_width * self.widget_scaling,  # 4:3
            # bd=2,
            # relief=RAISED
            # bg="gray70",
        )
        self.image_preview_canvas.create_image(
            self.img_width / 2 * self.widget_scaling,
            self.img_height / 2 * self.widget_scaling,
            image=self.img_icon,
            anchor=tkinter.CENTER,
        )
        self.image_preview_canvas.pack()

        self.info_text.set(
            "Resolution: Width x Height - Crop-Parameters: (x-offset, y-offset); size"
        )
        self.label_info = customtkinter.CTkLabel(
            master=self.frame_right,
            textvariable=self.info_text,
            width=self.img_width,
            fg_color=("gray75", "gray30"),  # <- custom tuple-color
            justify=tkinter.LEFT,
            corner_radius=8,
        )
        self.label_info.grid(row=8, column=0, pady=10, padx=20, sticky="")

        # ============ frame_right_column_2 ============

        self.radio_var = tkinter.IntVar(value=0)

        self.label_radio_group = customtkinter.CTkLabel(
            master=self.frame_right, text="Classes:", text_font=("Roboto Medium", -18)
        )
        self.label_radio_group.grid(row=0, column=1, pady=20, padx=10, sticky="")

        self.radio_buttons_list = []
        for i in range(4):
            self.radio_button = customtkinter.CTkRadioButton(
                master=self.frame_right,
                variable=self.radio_var,
                value=i,
                text=f"Class_{i+1}",
                fg_color="#b3cb23",
                hover_color="#d4dc54",
            )
            self.radio_button.configure(state=tkinter.DISABLED)
            self.radio_buttons_list.append(self.radio_button)
            self.radio_button.grid(row=i + 1, column=1, pady=10, padx=5)

        self.counter.set("Counter: -")
        self.label_radio_group = customtkinter.CTkLabel(
            master=self.frame_right,
            textvariable=self.counter,
            text_font=("Roboto Medium", -18),
        )
        self.label_radio_group.grid(row=8, column=1, pady=20, padx=10, sticky="")

        # set default values
        self.radio_buttons_list[0].select()
        self.switch_mode.select()

        main(self)

    # =========== Functions =============
    def get_save(self):
        return self._save

    def get_ready(self):
        return self._ready

    def quit_clicked(self):
        self.quit()
        self.destroy()

    def Preview_clicked(self):
        """
        This function executes by clicking on the 'Preview' button.
        It takes a photo and display it without saving it.

        :return: None
        """
        # self.capture = self.capture_np.reshape((App.resolution[1], App.resolution[0], 3))
        # App.camera.capture(self.capture, 'bgr')
        self.capture = App.camera.capture_array()
        # self.capture = self.capture_np.reshape((App.resolution[1], App.resolution[0], 3))
        self.capture = cv2.rectangle(
            self.capture,
            (self.crop_start_x, self.crop_start_y),
            (
                self.crop_start_x + self.crop_groesse,
                self.crop_start_y + self.crop_groesse,
            ),
            (211, 0, 0),
            3,
        )
        self.capture = cv2.resize(
            self.capture,  # cv2.cvtColor(self.capture, cv2.COLOR_BGR2RGB),
            (
                int(self.img_width * self.widget_scaling),
                int(self.img_height * self.widget_scaling),
            ),
            interpolation=cv2.INTER_AREA,
        )
        self.preview_image = ImageTk.PhotoImage(image=Image.fromarray(self.capture))
        self.image_preview_canvas.create_image(
            self.img_width / 2 * self.widget_scaling,
            self.img_height / 2 * self.widget_scaling,
            image=self.preview_image,
            anchor=tkinter.CENTER,
        )

        self.info_text.set(
            f"Resolution: {self.resolution[0]} x {self.resolution[1]} - Crop-Parameters: ({self.crop_start_x}, {self.crop_start_y}); {self.crop_groesse}"
        )

    def Crop_clicked(self):
        """
        This function executes by clicking on the 'Crop' button.
        The user can input the desired crop parameters.

        :return: None
        """
        self.label_1.grid_forget()
        self.button_new.grid_forget()
        self.button_browse.grid_forget()

        self.x_entry.grid(row=5, column=0, pady=10, padx=10)
        self.y_entry.grid(row=6, column=0, pady=10, padx=10)
        self.size_entry.grid(row=7, column=0, pady=10, padx=10)

        def entry_enter_clicked(event):
            self.crop_confirm_clicked()

        self.size_entry.bind("<Return>", entry_enter_clicked)
        self.size_entry.bind("<KP_Enter>", entry_enter_clicked)
        self.x_entry.bind("<Return>", entry_enter_clicked)
        self.x_entry.bind("<KP_Enter>", entry_enter_clicked)
        self.y_entry.bind("<Return>", entry_enter_clicked)
        self.y_entry.bind("<KP_Enter>", entry_enter_clicked)

        self.button_crop_confirm.grid(row=8, column=0, pady=10, padx=20)

    def crop_confirm_clicked(self):
        """
        Update the values of crop parameters

        :return: None
        """
        if self.x_entry.get().isdigit():
            self.crop_start_x = int(self.x_entry.get())

        if self.y_entry.get().isdigit():
            self.crop_start_y = int(self.y_entry.get())

        if self.size_entry.get().isdigit():
            self.crop_groesse = int(self.size_entry.get())

        self.Preview_clicked()
        self.x_entry.grid_forget()
        self.y_entry.grid_forget()
        self.size_entry.grid_forget()
        self.label_1.grid(row=5, column=0, pady=10, padx=10)
        self.button_new.grid(row=6, column=0, pady=10, padx=20)
        self.button_browse.grid(row=7, column=0, pady=10, padx=20)
        self.button_crop_confirm.grid_forget()

    def Browse_clicked(self):
        """
        This function executes by clicking on the 'Browse' button.
        1. The user select the folder where the dataset already exists
        2. The function loads the labels from 'Labels.txt'
        3. The function changes the classes Labels

        :return: None
        """
        # 1.

        self.Datensatz_dir = filedialog.askdirectory(
            initialdir=self.Datensatzaufnahme, title="Path to the Dataset folder:"
        )
        path_to_file = os.path.join(self.Datensatz_dir, "Labels.txt")

        # 2.
        if (
            isinstance(self.Datensatz_dir, str)
            and self.Datensatz_dir != ""
            and exists(path_to_file)
        ):
            with open(path_to_file) as Labels_txt:
                self.labels = [line.strip() for line in Labels_txt]

        self.old_radio_buttons_list = self.radio_buttons_list[:]

        # 3.
        for i in range(4):
            self.old_radio_buttons_list[i].destroy()
            try:
                self.radio_button = customtkinter.CTkRadioButton(
                    master=self.frame_right,
                    variable=self.Class_Choice,
                    value=self.labels[i],
                    text=self.labels[i],
                    fg_color="#b3cb23",
                    hover_color="#d4dc54",
                    command=self.radio_button_clicked,
                )
                self.radio_button.grid(
                    row=i + 1, column=1, pady=10, padx=(100, 5), sticky="w"
                )
                self.radio_buttons_list[i] = self.radio_button
                self.counters[self.labels[i]] = 0
            except IndexError:
                continue
        # self.radio_buttons_list[0].select()
        self.radio_buttons_list[0].invoke()

        self._ready = True

    def New_clicked(self):
        """
        This function executes by clicking on the 'New' button.
        1. The user select the folder where to save the dataset
        2. The user inputs the labels of the classes
        3. The function saves the labels under 'Labels.txt' and changes the main window

        :return: None
        """
        # 1.

        self.Datensatz_dir = filedialog.askdirectory(
            initialdir=self.Datensatzaufnahme, title="Save under:"
        )

        # 2.

        if isinstance(self.Datensatz_dir, str) and self.Datensatz_dir != "":
            self.button_browse.grid_forget()
            self.button_new.grid_forget()

            self.label_entry = customtkinter.CTkEntry(
                master=self.frame_left, placeholder_text="Class label:"
            )
            self.label_entry.grid(row=6, column=0, pady=10, padx=10)

            self.button_add = customtkinter.CTkButton(
                master=self.frame_left,
                text="Add",
                fg_color="#b3cb23",
                hover_color="#d4dc54",
                text_color="#000000",
                command=self.Add_clicked,
            )
            self.button_add.grid(row=7, column=0, pady=10, padx=20)

            self.button_Ok2 = customtkinter.CTkButton(
                master=self.frame_left,
                text="Ok",
                fg_color="#b3cb23",
                hover_color="#d4dc54",
                text_color="#000000",
                command=self.OK2_clicked,
            )
            self.button_Ok2.grid(row=8, column=0, pady=10, padx=20)

            def Add_Enter_clicked(event):
                self.Add_clicked()

            self.label_entry.bind("<Return>", Add_Enter_clicked)

            self.number_add_clicked = 0  # number of clicks on add
            self.old_radio_buttons_list = self.radio_buttons_list[:]
            self.labels.clear()

    def Add_clicked(self):
        """
        Append the non-empty user input to the Labels list
        Update the radio buttons
        :return: None
        """
        if self.label_entry.get() != "":
            self.labels.append(self.label_entry.get())
            Class_dir = os.path.join(self.Datensatz_dir, self.label_entry.get())
            if not os.path.exists(Class_dir):
                os.makedirs(Class_dir)
            self.label_entry.delete(0, END)
            self.label_entry.focus_set()

            self.old_radio_buttons_list[self.number_add_clicked].destroy()
            self.radio_button = customtkinter.CTkRadioButton(
                master=self.frame_right,
                variable=self.Class_Choice,
                value=self.labels[self.number_add_clicked],
                text=self.labels[self.number_add_clicked],
                fg_color="#b3cb23",
                hover_color="#d4dc54",
                command=self.radio_button_clicked,
            )
            self.radio_button.grid(
                row=self.number_add_clicked + 1, column=1, pady=10, padx=5, sticky="w"
            )
            self.radio_buttons_list[self.number_add_clicked] = self.radio_button
            self.counters[self.labels[self.number_add_clicked]] = 0
            self.number_add_clicked += 1
            if self.number_add_clicked == 4:
                self.OK2_clicked()

    def OK2_clicked(self):
        """
        This function is executed by clicking on ok in case of giving the labels.
        It saves Labels.txt and changes the main window

        :return: None
        """
        self.labels.sort()
        with open(
            os.path.join(self.Datensatz_dir, "Labels.txt"), "w"
        ) as labels_txt_file:
            for label in self.labels:
                labels_txt_file.write(str(label) + "\n")

        # self.radio_buttons_list[0].select()
        self.radio_buttons_list[0].invoke()

        self.label_entry.destroy()
        self.button_add.destroy()
        self.button_Ok2.destroy()

        self.button_new.grid(row=6, column=0, pady=10, padx=20)
        self.button_browse.grid(row=7, column=0, pady=10, padx=20)

        self._ready = True

    def radio_button_clicked(self):
        self.counter.set(f"Counter: {self.counters[self.Class_Choice.get()]}")

    def dark_mode(self):
        if self.switch_mode.get() == 1:
            customtkinter.set_appearance_mode("dark")
            self.label_title_logo.configure(image=self.match_logo_white)
        else:
            customtkinter.set_appearance_mode("light")
            self.label_title_logo.configure(image=self.match_logo_black)

    def save_mode(self):
        if self.switch_save.get() == 1:
            self._save = True
        else:
            self._save = False

    def on_closing(self, event=0):
        self.destroy()


def main(app):
    """
    The main function.

    :return: None
    """

    def take_photo(self):
        """
        Callback function for the event of Arduino sending back the signal, that the object reached the position.

        :param self:
        :return: None
        """
        # app.camera.capture(app.capture_np, 'bgr')
        app.capture = App.camera.capture_array()
        # app.capture = app.capture_np.reshape((app.resolution[1], app.resolution[0], 3))

        if app.get_save() and app.get_ready():
            Image_path = os.path.join(app.Datensatz_dir, app.Class_Choice.get())

            if not os.path.exists(Image_path):
                os.makedirs(Image_path)

            img_name = os.path.join(
                Image_path,
                app.Class_Choice.get()
                + "_"
                + "{}.jpg".format(datetime.now().strftime("%Y%m%d-%H%M%S")),
            )

            cv2.imwrite(img_name, cv2.cvtColor(app.capture, cv2.COLOR_BGR2RGB))

            app.counters[app.Class_Choice.get()] += 1
            app.counter.set(f"Counter: {app.counters[app.Class_Choice.get()]}")

        app.capture = cv2.rectangle(
            app.capture,
            (app.crop_start_x, app.crop_start_y),
            (app.crop_start_x + app.crop_groesse, app.crop_start_y + app.crop_groesse),
            (211, 0, 0),
            3,
        )
        app.capture = cv2.resize(
            app.capture,  # cv2.cvtColor(app.capture, cv2.COLOR_BGR2RGB),
            (
                int(app.img_width * app.widget_scaling),
                int(app.img_height * app.widget_scaling),
            ),
            interpolation=cv2.INTER_AREA,
        )
        app.preview_image = ImageTk.PhotoImage(image=Image.fromarray(app.capture))
        app.image_preview_canvas.create_image(
            app.img_width / 2 * app.widget_scaling,
            app.img_height / 2 * app.widget_scaling,
            image=app.preview_image,
            anchor=tkinter.CENTER,
        )

        app.info_text.set(
            f"Resolution: {app.resolution[0]} x {app.resolution[1]} - Crop-Parameters: ({app.crop_start_x}, {app.crop_start_y}); {app.crop_groesse}"
        )

    def send_value_to_arduino_callback(self):
        """
        Callback function for the event of detecting and object by the light barrier.
        Calls the function  functio.send_value_to_arduino(take-photo flag, take-photo flag position)

        :param self:
        :return: None
        """
        take_photo_position = 50
        functions.send_value_to_arduino(777, take_photo_position, 1)

    GPIO.setmode(GPIO.BCM)  # Pin-Belegung nach GPIO-Nummern

    PIN_Light_Barrier = 21
    PIN_Ardiuno = 22

    GPIO.setup(PIN_Light_Barrier, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(PIN_Ardiuno, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    time.sleep(2)

    GPIO.add_event_detect(
        PIN_Light_Barrier,
        GPIO.RISING,
        callback=send_value_to_arduino_callback,
        bouncetime=2000,
    )

    GPIO.add_event_detect(PIN_Ardiuno, GPIO.BOTH, callback=take_photo, bouncetime=2000)


def app_launch():
    """
    showing a splash screen then the main window

    :return: None
    """

    splash_win.destroy()
    app = App()
    app.mainloop()


if __name__ == "__main__":
    # ============ create splash screen ============

    SPLASH_WIN_HEIGHT = 100
    SPLASH_WIN_WIDTH = 800

    # Create an instance of tkinter frame
    splash_win = tkinter.Tk()

    screen_width = splash_win.winfo_screenwidth()
    screen_height = splash_win.winfo_screenheight()

    x_cordinate = int((screen_width / 2) - (SPLASH_WIN_WIDTH / 2))
    y_cordinate = int((screen_height / 2) - (SPLASH_WIN_HEIGHT / 2))

    # Set the title of the window
    splash_win.title("Splash Screen")

    # Define the size of the window or frame
    splash_win.geometry(
        "{}x{}+{}+{}".format(
            SPLASH_WIN_WIDTH, SPLASH_WIN_HEIGHT, x_cordinate, y_cordinate
        )
    )

    # Remove border of the splash Window
    splash_win.overrideredirect(True)

    # Define the label of the window
    match_logo = PhotoImage(file="match.png")
    splash_label = tkinter.Label(
        splash_win,
        text="Masterlabor\nMaschinelles Lernen in der Produktionstechnik",
        font=("Arial", 20, "bold"),
        bg="white",
        # bd=3,
        # relief=tkinter.RAISED,
        padx=25,
        image=match_logo,
        compound="left",
    )
    splash_label.pack()

    # Set Interval
    splash_win.after(2000, app_launch)

    # Execute tkinter
    tkinter.mainloop()
