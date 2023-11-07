#!/usr/bin/env python3
import glob
import os
import shutil
import sys
import time
import tkinter as tk
import tkinter.messagebox
from multiprocessing import Event, Process
from threading import Thread
from tkinter import IntVar, PhotoImage, StringVar, filedialog

import customtkinter

# import cv2
import numpy as np
import RPi.GPIO as GPIO
from picamera2 import Picamera2
from PIL import Image, ImageTk
from tflite_runtime.interpreter import Interpreter

from ejector import Ejector
import functions

customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("blue")


class App(customtkinter.CTk):
    """
    This class is the main application.
    It inherits from the customtkinter.CTk class.
    """

    camera = Picamera2()

    resolution = camera.sensor_resolution
    aspect_ratio = resolution[0] / resolution[1]
    controls = {"ExposureTime": 3500, "AnalogueGain": 2.5, "ColourGains": (2.2, 1.9)}
    capture_config = camera.create_still_configuration(controls=controls)
    camera.configure(capture_config)
    camera.start()

    def __init__(self) -> None:
        """
        This function initializes the main application.
        It configures the main window and creates the four frames.
        It also sets the default values for the crop parameters and the threshold.
        """

        super().__init__()  # initialize the customtkinter.CTk class

        self.labels = []
        # Create empty numpy array for the preview image
        self.capture = np.empty(
            (App.resolution[1] * App.resolution[0] * 3,), dtype=np.uint8
        )
        # Create a Tkinter PhotoImage from the preview image
        self.preview_image = ImageTk.PhotoImage(image=Image.fromarray(self.capture))

        # Default crop parameters
        self.x_offset = 870
        self.y_offset = 110
        self.crop_size = 2450

        self.info_text = StringVar()

        home = os.path.expanduser(f"~{os.getlogin()}/")

        self.dataset_folder = os.path.join(home, "MLL/Datensatzaufnahme")
        self.labels = []

        self.netze_folder = os.path.join(home, "MLL/Netze")
        self.netze_desktop = os.path.join(home, "Desktop/Netze")
        self.netze_paths = []
        self.netze_names = []
        self.netze_dict = {}
        self.netz_choice = StringVar()
        self.change_netz = False

        self.threshold = IntVar(value=30)
        self.pos_offset = IntVar(value=50)

        self.obj_num = 0
        self.prediction = " - "

        self.counters = {}

        # Fix: customtkinter variables not working when declared in widget
        self.labels_ready = False
        self.netze_ready = False
        self.grayscale_variable = False
        self.remote_serving_variable = False

        # Default classes to show in GUI
        self.classes = [
            StringVar(value="Class_1:\n\n-"),
            StringVar(value="Class_2:\n\n-"),
            StringVar(value="Class_3:\n\n-"),
            StringVar(value="Class_4:\n\n-"),
        ]

        self.state = "idle"  # 'idle' or 'busy'

        self.progress_bar_value = 0.1

        # ============ main window ============

        self.dpi = self.winfo_fpixels("1i")
        self.widget_scaling = 1.2 * self.dpi / 96

        customtkinter.set_widget_scaling(
            self.widget_scaling
        )  # widget dimensions and text size
        customtkinter.set_spacing_scaling(
            self.widget_scaling
        )  # padding and place positions

        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()

        self.title("MLL-Sortierung")
        self.attributes("-fullscreen", True)
        icon = tkinter.PhotoImage(file="Deckel_icon.png")
        self.iconphoto(True, icon)
        self.protocol(
            "WM_DELETE_WINDOW", self.on_closing
        )  # call .on_closing() when app gets closed

        # ============ create four frames ============

        # configure grid layout (3x1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=7)
        self.grid_columnconfigure(2, weight=2)
        self.grid_rowconfigure(0, weight=1)

        self.frame_left_width = self.screen_width * 1.5 // 10
        self.frame_left = customtkinter.CTkFrame(
            master=self, width=self.frame_left_width, corner_radius=0
        )
        self.frame_left.grid_propagate(False)
        self.frame_left.grid(row=0, column=0, rowspan=3, sticky="nswe")
        self.frame_middle_width = self.screen_width * 6.5 // 10
        self.frame_middle_height = self.screen_height * 6.5 // 10
        self.frame_middle = customtkinter.CTkFrame(
            master=self,
            width=self.frame_middle_width,
            height=self.frame_middle_height,
        )
        self.frame_middle.grid_propagate(False)
        self.frame_middle.grid(row=1, column=1, sticky="nswe", padx=20, pady=5)

        self.frame_right_width = self.screen_width * 2 // 10
        self.frame_right = customtkinter.CTkFrame(
            master=self, width=self.frame_right_width, corner_radius=0
        )
        self.frame_right.grid_propagate(False)
        self.frame_right.grid(row=0, column=2, rowspan=3, sticky="nswe")

        self.label_smallprint = customtkinter.CTkLabel(
            master=self,
            text=(
                "\u00A9 Institut für Montagetechnik - "
                "Masterlabor Maschinelles Lernen in der Produktionstechnik"
            ),
            justify=tk.LEFT,
        )
        self.label_smallprint.grid(row=2, column=1, pady=5, padx=20, sticky="sew")

        self.frame_title = customtkinter.CTkFrame(
            master=self,
            width=self.frame_middle_width,
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
        img = img.resize((int(self.frame_middle_width), int(img.height / scale)))
        self.match_bg = ImageTk.PhotoImage(img)

        self.label_title_bg = customtkinter.CTkLabel(
            master=self.frame_title,
            image=self.match_bg,
            corner_radius=10,
        )
        self.label_title_bg.grid(
            row=0, column=0, columnspan=2, pady=0, padx=0, sticky=""
        )

        self.label_title_logo = customtkinter.CTkLabel(
            master=self.frame_title,
            image=self.match_logo_white,
        )
        self.label_title_logo.grid(
            row=0, column=0, pady=5, padx=(75, 10), ipadx=10, sticky=""
        )

        self.label_title_text = customtkinter.CTkLabel(
            master=self.frame_title,
            text="Masterlabor: Maschinelles Lernen in der Produktionstechnik",
            text_font=("Roboto Medium", -22),
            height=self.screen_height * 0.3 // 10,
        )
        self.label_title_text.grid(
            row=0, column=1, pady=5, padx=40, ipadx=10, sticky=""
        )

        # ============ frame_left ============

        # configure grid layout (1x11)
        self.frame_left.grid_columnconfigure(0, weight=1)
        # empty rows with minsize as spacing between sections
        self.frame_left.grid_rowconfigure(0, minsize=10)
        self.frame_left.grid_rowconfigure(7, minsize=30)
        self.frame_left.grid_rowconfigure(11, minsize=30)
        self.frame_left.grid_rowconfigure(16, weight=1)
        self.frame_left.grid_rowconfigure(19, minsize=10)

        self.label_interpreters = customtkinter.CTkLabel(
            master=self.frame_left,
            text="Inference:",
            text_font=("Roboto Medium", -18),  # font name and size in px
        )
        self.label_interpreters.grid(row=1, column=0, pady=10, padx=10)

        # self.grayscale_variable = customtkinter.BooleanVar(value=False)
        self.switch_grayscale = customtkinter.CTkSwitch(
            master=self.frame_left,
            text="Grayscale",
            progress_color="#b3cb23",
            # variable=self.grayscale_variable,
            command=self.grayscale_command,
        )
        self.switch_grayscale.grid(row=2, column=0, pady=10, padx=50, sticky="w")

        # self.remote_serving_variable = customtkinter.BooleanVar(value=True)
        self.switch_remote = customtkinter.CTkSwitch(
            master=self.frame_left,
            text="Remote Serving",
            progress_color="#b3cb23",
            # variable=self.remote_serving_variable,
            command=self.switch_remote_command,
        )
        self.switch_remote.grid(row=3, column=0, pady=10, padx=50, sticky="w")

        self.hostname_var = customtkinter.CTkEntry(
            master=self.frame_left,
            placeholder_text="hostname/IP:",
            width=self.frame_left_width // 2,
        )
        self.hostname_var.grid(row=4, column=0, pady=10, padx=10)

        self.button_load_netze = customtkinter.CTkButton(
            master=self.frame_left,
            text="Load",
            fg_color="#b3cb23",
            hover_color="#d4dc54",
            text_color="#000000",
            width=self.frame_left_width // 2,
            command=self.load_netze_clicked,
        )
        self.button_load_netze.grid(row=5, column=0, pady=10, padx=10)

        self.option_menu_netze = customtkinter.CTkOptionMenu(
            master=self.frame_left,
            values=self.netze_names,
            variable=self.netz_choice,
            fg_color="#b3cb23",
            button_color="#b3cb23",
            button_hover_color="#d4dc54",
            dropdown_hover_color="#b3cb23",
            text_color="#000000",
            width=self.frame_left_width // 2,
            command=self.option_menu_callback,
            state="disabled",
        )
        self.option_menu_netze.grid(row=6, column=0, pady=10, padx=40)
        # TODO: This should only be shown once the models are loaded?

        self.progress_bar = customtkinter.CTkProgressBar(
            master=self.frame_left,
            width=self.frame_left_width // 2,
            progress_color="#b3cb23",
        )

        self.label_classes = customtkinter.CTkLabel(
            master=self.frame_left,
            text="Class Labels:",
            text_font=("Roboto Medium", -18),
        )
        self.label_classes.grid(row=8, column=0, pady=10)

        self.button_load_labels = customtkinter.CTkButton(
            master=self.frame_left,
            text="Load",
            fg_color="#b3cb23",
            hover_color="#d4dc54",
            text_color="#000000",
            width=self.frame_left_width // 2,
            command=self.load_labels_clicked,
        )
        self.button_load_labels.grid(row=9, column=0, pady=10, padx=20)

        self.label_crop = customtkinter.CTkLabel(
            master=self.frame_left,
            text="Crop Parameters:",
            text_font=("Roboto Medium", -18),
        )
        self.label_crop.grid(row=11, column=0, pady=10)

        self.button_set = customtkinter.CTkButton(
            master=self.frame_left,
            text="Set",
            fg_color="#b3cb23",
            hover_color="#d4dc54",
            text_color="#000000",
            width=self.frame_left_width // 2,
            command=self.set_clicked,
        )
        self.button_set.grid(row=12, column=0, pady=10, padx=20)

        self.button_quit = customtkinter.CTkButton(
            master=self.frame_left,
            text="Quit",
            width=self.frame_left_width // 2,
            fg_color="#b3cb23",
            hover_color="#d4dc54",
            text_color="#000000",
            command=self.quit_clicked,
        )
        self.button_quit.grid(row=17, column=0, pady=10, padx=20)

        self.switch_mode = customtkinter.CTkSwitch(
            master=self.frame_left,
            text="Dark Mode",
            progress_color="#b3cb23",
            command=self.dark_mode,
        )
        self.switch_mode.grid(row=18, column=0, pady=10, padx=50, sticky="w")

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

        # ============ frame_middle ============

        # configure grid layout (3x7)
        self.frame_middle.grid_rowconfigure((1, 2, 3, 4, 5, 6, 7, 8), weight=5)
        self.frame_middle.grid_rowconfigure(8, weight=1)
        self.frame_middle.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.img_height = self.frame_middle_height * 3 // 4
        self.img_width = self.img_height * self.aspect_ratio
        self.frame_img = customtkinter.CTkFrame(
            master=self.frame_middle, width=self.img_width, height=self.img_height
        )
        self.frame_img.grid(row=1, column=0, columnspan=4, rowspan=7, pady=5, padx=10)

        self.img_icon = PhotoImage(file="Deckel_icon.png")
        self.image_preview_canvas = tkinter.Canvas(
            self.frame_img,
            height=self.img_height * self.widget_scaling,
            width=self.img_width * self.widget_scaling,  # 4:3
        )
        self.image_preview_canvas.create_image(
            self.img_width / 2 * self.widget_scaling,
            self.img_height / 2 * self.widget_scaling,
            image=self.img_icon,
            anchor=tkinter.CENTER,
        )
        self.image_preview_canvas.pack()

        self.info_text.set(
            (
                f"Object N°: {self.obj_num} Prediction: {self.prediction}"
                f"\tCrop-Parameters: ({self.x_offset}, {self.y_offset}); {self.crop_size}"
            )
        )
        self.label_info = customtkinter.CTkLabel(
            master=self.frame_middle,
            textvariable=self.info_text,
            width=self.img_width,
            fg_color=("gray75", "gray30"),
            justify=tkinter.LEFT,
            corner_radius=8,
        )
        self.label_info.grid(row=0, column=0, columnspan=4, pady=10, padx=10, sticky="")

        frame_l_width = self.frame_middle_width * 1.5 / 10
        frame_l_height = self.frame_middle_height * 1 / 4 * 1 / 2
        self.frame_l1 = customtkinter.CTkFrame(
            master=self.frame_middle,
            width=frame_l_width,
            height=frame_l_height,
        )
        self.frame_l1.grid(row=8, column=0, pady=10, padx=10)

        self.frame_l1.rowconfigure(0, weight=1)
        self.frame_l1.columnconfigure(0, weight=1)
        self.frame_l1.grid_propagate(False)

        self.label_l1 = customtkinter.CTkLabel(
            master=self.frame_l1,
            textvariable=self.classes[0],
            text_font=("Roboto Medium", -18),
            wraplength=180,
        )
        self.label_l1.grid(row=0, column=0, padx=5, pady=5, sticky="nswe")

        self.frame_l2 = customtkinter.CTkFrame(
            master=self.frame_middle,
            width=frame_l_width,
            height=frame_l_height,
        )
        self.frame_l2.grid(row=8, column=1, pady=10, padx=10)

        self.frame_l2.rowconfigure(0, weight=1)
        self.frame_l2.columnconfigure(0, weight=1)
        self.frame_l2.grid_propagate(False)

        self.label_l2 = customtkinter.CTkLabel(
            master=self.frame_l2,
            textvariable=self.classes[1],
            text_font=("Roboto Medium", -18),
            wraplength=180,
        )
        self.label_l2.grid(row=0, column=0, padx=5, pady=5, sticky="nswe")

        self.frame_l3 = customtkinter.CTkFrame(
            master=self.frame_middle,
            width=frame_l_width,
            height=frame_l_height,
        )
        self.frame_l3.grid(row=8, column=2, pady=10, padx=10)

        self.frame_l3.rowconfigure(0, weight=1)
        self.frame_l3.columnconfigure(0, weight=1)
        self.frame_l3.grid_propagate(False)

        self.label_l3 = customtkinter.CTkLabel(
            master=self.frame_l3,
            textvariable=self.classes[2],
            text_font=("Roboto Medium", -18),
            wraplength=180,
        )
        self.label_l3.grid(row=0, column=0, padx=5, pady=5, sticky="nswe")

        self.frame_l4 = customtkinter.CTkFrame(
            master=self.frame_middle,
            width=frame_l_width,
            height=frame_l_height,
        )
        self.frame_l4.grid(row=8, column=3, pady=10, padx=10)

        self.frame_l4.rowconfigure(0, weight=1)
        self.frame_l4.columnconfigure(0, weight=1)
        self.frame_l4.grid_propagate(False)

        self.label_l4 = customtkinter.CTkLabel(
            master=self.frame_l4,
            textvariable=self.classes[3],
            text_font=("Roboto Medium", -18),
            wraplength=180,
        )
        self.label_l4.grid(row=0, column=0, padx=5, pady=5, sticky="nswe")

        # ============ frame_right ============

        # configure grid layout (1x11)
        self.frame_right.grid_columnconfigure(0, weight=4)
        self.frame_right.grid_columnconfigure(1, weight=1)
        self.frame_right.grid_rowconfigure(0, minsize=10)
        self.frame_right.grid_rowconfigure(3, minsize=30)
        self.frame_right.grid_rowconfigure(7, weight=1)
        self.frame_right.grid_rowconfigure(11, minsize=60)

        self.label_threshold = customtkinter.CTkLabel(
            master=self.frame_right, text="Threshold:", text_font=("Roboto Medium", -18)
        )
        self.label_threshold.grid(row=1, column=0, columnspan=2, pady=10, padx=10)

        self.entry_threshold = customtkinter.CTkEntry(
            master=self.frame_right,
            width=self.frame_right_width * 1.25 // 10,
            textvariable=self.threshold,
        )
        self.entry_threshold.grid(row=2, column=1, pady=10, padx=10, sticky="w")

        def entry_threshold_refocus(event):
            self.entry_threshold.focus_set()

        self.entry_threshold.bind("<Return>", entry_threshold_refocus)
        self.entry_threshold.bind("<KP_Enter>", entry_threshold_refocus)

        self.slider_threshold = customtkinter.CTkSlider(
            master=self.frame_right,
            from_=0,
            to=100,
            variable=self.threshold,
            width=self.frame_right_width * 6 // 10,
            progress_color="#b3cb23",
            button_color=("gray40", "gray90"),
            button_hover_color="white",
            command=self.entry_threshold.focus_set(),
        )
        self.slider_threshold.grid(row=2, column=0, pady=10, padx=10)

        self.label_pos = customtkinter.CTkLabel(
            master=self.frame_right,
            text="Position Offset:",
            text_font=("Roboto Medium", -18),
        )
        self.label_pos.grid(row=4, column=0, columnspan=2, pady=10, padx=10)

        self.entry_pos = customtkinter.CTkEntry(
            master=self.frame_right,
            placeholder_text="50",
            width=self.frame_right_width * 1.25 // 10,
            textvariable=self.pos_offset,
        )
        self.entry_pos.grid(row=5, column=1, pady=10, padx=10, sticky="w")

        def entry_pos_refocus(event):
            self.entry_pos.focus_set()

        self.entry_pos.bind("<Return>", entry_pos_refocus)
        self.entry_pos.bind("<KP_Enter>", entry_pos_refocus)

        self.slider_pos = customtkinter.CTkSlider(
            master=self.frame_right,
            from_=0,
            to=150,
            variable=self.pos_offset,
            width=self.frame_right_width * 6 // 10,
            progress_color="#b3cb23",
            button_color=("gray40", "gray90"),
            button_hover_color="white",
            command=self.entry_pos.focus_set(),
        )
        self.slider_pos.grid(row=5, column=0, pady=10, padx=10)

        self.label_counters = customtkinter.CTkLabel(
            master=self.frame_right, text="Counter:", text_font=("Roboto Medium", -18)
        )

        self.label_counters.grid(row=8, column=0, columnspan=2, pady=10, padx=10)

        self.button_reset = customtkinter.CTkButton(
            master=self.frame_right,
            text="Reset",
            fg_color="#b3cb23",
            hover_color="#d4dc54",
            text_color="#000000",
            width=self.frame_left_width // 2,
            command=self.counters_reset,
        )
        self.button_reset.grid(row=10, column=0, columnspan=2, pady=10, padx=10)

        # set default values, toggle switches to default state
        self.switch_mode.select()
        self.switch_remote.select()
        self.option_menu_netze.set("Netz_1")

    def getlabels_ready(self) -> bool:
        """
        This function returns the value of the labels_ready variable.
        """
        return self.labels_ready

    def getnetze_ready(self) -> bool:
        """
        This function returns the value of the netze_ready variable.
        """
        return self.netze_ready

    def counters_reset(self) -> None:
        """
        This function resets the counters and the object number.
        """
        self.obj_num = 0
        self.info_text.set(
            f"Object N°: {self.obj_num} Prediction: {self.prediction}"
            f"\tCrop-Parameters: ({self.x_offset}, {self.y_offset}); {self.crop_size}"
        )
        for label, i in zip(self.labels, range(4)):
            try:
                self.counters[label] = 0
                self.classes[i].set(f"{label}:\n\n{self.counters[label]}")
            except IndexError:
                pass

    def quit_clicked(self) -> None:
        """
        This function executes by clicking on the 'Quit' button.
        It closes the application.
        """
        self.quit()
        self.destroy()

    def load_netze_clicked(self) -> None:
        """
        This function executes by clicking on the 'Load' button.
        It allows the user to choose wisch CNN model/intrepeter to use.
        """
        if self.remote_serving_variable:
            # Remote serving, get list of available models
            self.netze_names = functions.get_remote_models(self.hostname_var.get())
            self.option_menu_netze.configure(values=self.netze_names)
            self.option_menu_netze.set(self.netze_names[0])
            self.option_menu_netze.configure(state=tkinter.NORMAL)
            self.netze_ready = True

        else:
            # local interpreter, load from server to local machine etc
            self.netze_folder = filedialog.askdirectory(
                initialdir=self.netze_folder, title="Intrepeter:"
            )
            self.button_load_netze.configure(state=tkinter.DISABLED)
            self.progress_bar.set(0.1)
            self.progress_bar.grid(row=7, column=0, pady=10, padx=40)

            load_netze_thread = Thread(target=self.copy_and_load_netze)
            load_netze_thread.start()

            update_progress_bar_thread = Thread(target=self.update_progress_bar)
            update_progress_bar_thread.start()

    def update_progress_bar(self) -> None:
        """
        This function updates the progress bar.
        """
        while self.progress_bar_value < 1:
            self.progress_bar.set(self.progress_bar_value)

    def copy_and_load_netze(self) -> None:
        """
        This function copies the intrepeters from the server to the local machine.
        It also loads the intrepeters and creates the option menu.
        """
        if isinstance(self.netze_folder, str) and self.netze_folder != "":
            self.netze_paths = glob.glob(os.path.join(self.netze_folder, "*.tflite"))

            if len(self.netze_paths) != 0:
                # copy files to Desktop/Netze
                shutil.rmtree(self.netze_desktop, ignore_errors=True)
                os.makedirs(self.netze_desktop)
                for file, i in zip(self.netze_paths, range(len(self.netze_paths))):
                    shutil.copy(file, self.netze_desktop)
                    self.progress_bar_value = 0.1 + 0.7 * i / len(self.netze_paths)

                self.netze_paths = glob.glob(
                    os.path.join(self.netze_desktop, "*.tflite")
                )

                for intrepeter in self.netze_paths:
                    name = intrepeter[
                        intrepeter.rfind("MLL-Netz_") + 9 : intrepeter.rfind(".")
                    ]
                    self.netze_names.append(name)
                    self.netze_dict[name] = intrepeter

                self.progress_bar_value = 0.8

                self.option_menu_netze.configure(values=self.netze_names)
                self.option_menu_netze.set(self.netze_names[0])
                self.netze_ready = True

                self.progress_bar_value = 1
                time.sleep(0.5)

            self.counters_reset()
            self.progress_bar.grid_forget()
            self.option_menu_netze.grid(row=6, column=0, pady=10, padx=40)
            self.button_load_netze.configure(state=tkinter.NORMAL)
            self.option_menu_netze.configure(state=tkinter.NORMAL)

    def load_labels_clicked(self) -> None:
        """
        This function executes by clicking on the 'Load' button.
        1. The user select the folder where the dataset already exists
        2. The function loads the labels from 'Labels.txt'
        3. The function changes the classes Labels
        """
        # If remote serving is true, use default labels, as there is no proper way to retrieve classes from model
        if self.remote_serving_variable:
            self.labels = ["Korken", "Kronkorken", "Metalldeckel", "Plastikdeckel"]
            self.labels_ready = True

        else:
            # 1.
            Labels_txt = filedialog.askopenfilename(
                initialdir=self.dataset_folder, title="Labels.txt:"
            )

            # 2.
            if isinstance(Labels_txt, str) and Labels_txt != "":
                with open(Labels_txt, encoding="utf-8") as f:
                    self.labels = [line.strip() for line in f]

                self.labels_ready = True

        # 3.
        for label, i in zip(self.labels, range(4)):
            try:
                self.counters[label] = 0
                self.classes[i].set(f"{label}:\n\n{self.counters[label]}")
            except IndexError:
                pass

    def set_clicked(self) -> None:
        """
        This function executes by clicking on the 'Crop' button.
        The user can input the desired crop parameters.
        """
        self.button_set.grid_forget()  # remove set button once it is clicked

        # populate the entry fields with the current values
        self.x_entry.grid(row=12, column=0, pady=10, padx=10)
        self.y_entry.grid(row=13, column=0, pady=10, padx=10)
        self.size_entry.grid(row=14, column=0, pady=10, padx=10)

        def entry_enter_clicked(event) -> None:
            # unclear what this does
            self.crop_confirm_clicked()

        self.size_entry.bind(
            "<Return>", entry_enter_clicked
        )  # bind the enter key to the entry field
        self.size_entry.bind(
            "<KP_Enter>", entry_enter_clicked
        )  # bind the numeric enter key to the entry field
        self.x_entry.bind("<Return>", entry_enter_clicked)
        self.x_entry.bind("<KP_Enter>", entry_enter_clicked)
        self.y_entry.bind("<Return>", entry_enter_clicked)
        self.y_entry.bind("<KP_Enter>", entry_enter_clicked)

        # populate row 12 with the OK button
        self.button_crop_confirm.grid(row=15, column=0, pady=10, padx=20)

    def crop_confirm_clicked(self) -> None:
        """
        Update the values of crop parameters
        """

        # Test if the input is a number and update the values
        if self.x_entry.get().isdigit():
            self.x_offset = int(self.x_entry.get())

        if self.y_entry.get().isdigit():
            self.y_offset = int(self.y_entry.get())

        if self.size_entry.get().isdigit():
            self.crop_size = int(self.size_entry.get())

        self.info_text.set(
            f"Object N°: {self.obj_num} Prediction: {self.prediction} \t"
            f"Crop-Parameters: ({self.x_offset}, {self.y_offset}); {self.crop_size}"
        )

        # remove the entry fields and the OK button but show the set button again
        self.x_entry.grid_forget()
        self.y_entry.grid_forget()
        self.size_entry.grid_forget()
        self.button_set.grid(row=12, column=0, pady=10, padx=20)
        self.button_crop_confirm.grid_forget()

    def option_menu_callback(self) -> None:
        """
        This function executes by clicking on the 'OptionMenu'.
        It loads the selected intrepeter.
        """
        if not self.remote_serving_variable and self.netze_ready:
            # if self.netze_ready:
            # TODO: Edgecases exist where there is no interpreter initiated
            # but predict(app) is called
            self.interpreter = Interpreter(self.netze_dict[self.netz_choice.get()])
            self.interpreter.allocate_tensors()

    def dark_mode(self) -> None:
        """
        This function executes by clicking on the 'Dark Mode' button.
        It changes the appearance of the GUI.
        """
        if self.switch_mode.get() == 1:
            customtkinter.set_appearance_mode("dark")
            self.label_title_logo.configure(image=self.match_logo_white)
        else:
            customtkinter.set_appearance_mode("light")
            self.label_title_logo.configure(image=self.match_logo_black)

    def grayscale_command(self) -> None:
        """
        This function executes by clicking on the 'Grayscale' button.
        It changes the appearance of the GUI.
        """
        # DONE: grayscale_variable is set directly from toggle so below is redundant
        # This is still required, as variables are set manually, because customtkinter seems to be broken
        if self.switch_grayscale.get() == 1:
            self.grayscale_variable = True
        else:
            self.grayscale_variable = False

    def switch_remote_command(self) -> None:
        """
        This function executes by clicking on the 'Remote Serving' button.
        It changes the appearance of the GUI.
        """
        if self.switch_remote.get() == 1:
            self.remote_serving_variable = True
            self.hostname_var.configure(state="normal")
            self.load_labels_clicked()
            self.button_load_labels.configure(state="disabled")
            self.hostname_var.configure(placeholder_text="hostname/IP:")
        else:
            self.remote_serving_variable = False
            self.hostname_var.configure(state="disabled")
            self.classes = [
                StringVar(value="Class_1:\n\n-"),
                StringVar(value="Class_2:\n\n-"),
                StringVar(value="Class_3:\n\n-"),
                StringVar(value="Class_4:\n\n-"),
            ]
            self.label_l1.configure(textvariable=self.classes[0])
            self.label_l2.configure(textvariable=self.classes[1])
            self.label_l3.configure(textvariable=self.classes[2])
            self.label_l4.configure(textvariable=self.classes[3])
            self.button_load_labels.configure(state="normal")

    def on_closing(self, event=0):
        """
        This function executes by closing the application.
        It closes the application.
        """
        self.destroy()


def app_launch() -> None:
    """
    This function launches the main application.
    """
    predict_signal = Event()  # multiprocessing event object

    GPIO.setmode(GPIO.BCM)  # Pin-Belegung nach GPIO-Nummern

    PIN_Light_Barrier = 21

    PIN_Ejector_1 = 23
    PIN_Ejector_2 = 24
    PIN_Ejector_3 = 25
    PIN_Ejector_4 = 12
    PIN_Arduino = 22

    GPIO.setup(PIN_Light_Barrier, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(PIN_Arduino, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(PIN_Ejector_1, GPIO.OUT)
    GPIO.setup(PIN_Ejector_2, GPIO.OUT)
    GPIO.setup(PIN_Ejector_3, GPIO.OUT)
    GPIO.setup(PIN_Ejector_4, GPIO.OUT)

    splash_win.destroy()
    app = App()

    wait_to_predict_thread = Thread(
        target=functions.wait_to_predict, args=(app, predict_signal)
    )
    wait_to_predict_thread.daemon = True
    light_barrier_thread = Thread(
        target=functions.light_barrier, args=(app, PIN_Light_Barrier)
    )
    light_barrier_thread.daemon = True

    eject_or_photo_process = Process(
        target=functions.eject_or_photo,
        args=(
            predict_signal,
            PIN_Arduino,
            PIN_Ejector_1,
            PIN_Ejector_2,
            PIN_Ejector_3,
            PIN_Ejector_4,
        ),
    )
    eject_or_photo_process.start()

    app.after(0, wait_to_predict_thread.start)
    app.after(0, light_barrier_thread.start)
    app.mainloop()

    # Closing Main Window
    try:
        eject_or_photo_process.terminate()
    except:
        pass

    GPIO.cleanup()
    sys.exit()


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
