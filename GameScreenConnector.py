import logging
import os
import time
from typing import Tuple

import cv2
import numpy as np

from custom_types import Frame
from image_text_detection import extract_text_from_image
from UsbConnector import UsbConnector
from Utils import buildDataFolder
from Utils import loadJsonData

logger = logging.getLogger(__name__)


class GameScreenConnector:
    def __init__(self, device_connector=None):
        self.debug = True
        self.device_connector = device_connector
        self.width = 0
        self.height = 0
        # This should be in format rgba
        self.coords_path = ""
        self.specific_checks_path = ""
        self.hor_lines_path = ""
        self.specific_checks_coords = {}
        self.static_coords = {}
        self.door_width = 180.0 / 1080.0
        self.yellow_experience = [255, 170, 16, 255]
        self.green_hp = [70, 158, 47, 255]
        self.green_hp_high = [84, 180, 58, 255]
        # Line coordinates: x1,y1,x2,y2
        self.hor_lines = {}
        self.stop_requested = False

    def change_device_connector(self, new_dev: UsbConnector):
        self.device_connector = new_dev

    def change_screen_size(self, w, h):
        self.width, self.height = w, h
        self.coords_path = os.path.join(
            "datas",
            buildDataFolder(self.width, self.height),
            "coords",
            "static_coords.json",
        )
        self.specific_checks_path = os.path.join(
            "datas",
            buildDataFolder(self.width, self.height),
            "coords",
            "static_specific_coords.json",
        )
        self.hor_lines_path = os.path.join(
            "datas",
            buildDataFolder(self.width, self.height),
            "coords",
            "hor_lines.json",
        )

        self.specific_checks_coords = loadJsonData(self.specific_checks_path)
        self.static_coords = loadJsonData(self.coords_path)
        self.hor_lines = loadJsonData(self.hor_lines_path)

    def pixel_equals(self, px_readed, px_expected, around=5):
        arr = [5, 5, 5]
        if isinstance(around, int):
            arr = [around, around, around]
        elif isinstance(around, list):
            arr = [around[0], around[1], around[2]]
        # checking only RGB from RGBA
        return (
            px_expected[0] - arr[0] <= px_readed[0] <= px_expected[0] + arr[0]
            and px_expected[1] - arr[1] <= px_readed[1] <= px_expected[1] + arr[1]
            and px_expected[2] - arr[2] <= px_readed[2] <= px_expected[2] + arr[2]
        )

    def get_frame_attr(self, frame, attributes):
        attr_data = []
        for attr in attributes:
            x = int(attr[0] * self.width)
            y = int(attr[1] * self.height)
            attr_data.append(frame[int(y * self.width + x)])
        return attr_data

    def _check_screen_points_equal(self, frame: Frame, points_list, points_value, around=2):
        """
        Gets 2 lists of x,y coordinates where to get values and list of values to comapre.
        Returns true if current frame have those values
        :param points_list: a list of x,y coordinates (absolute, not normalized)
        :param points_value: a list (same size of points_list) with values for equals check (values are 4d)
        :param around: an integer for interval of search: +around and -around.
        :return:
        """
        if len(points_list) != len(points_value):
            print("Wrong size between points and values!")
            return False
        if self.debug:
            print("-----------------------------------")
        if self.debug:
            print("|   Smartphone   |     Values     |")
        attr_data = self.get_frame_attr(frame, points_list)
        equal = True
        for i in range(len(attr_data)):
            if self.debug:
                print(
                    "| %4d %4d %4d | %4d %4d %4d |"
                    % (
                        attr_data[i][0],
                        attr_data[i][1],
                        attr_data[i][2],
                        points_value[i][0],
                        points_value[i][1],
                        points_value[i][2],
                    )
                )
            if not self.pixel_equals(attr_data[i], points_value[i], around=around):
                equal = False
        if self.debug:
            print("|-->         %s" % ("  equal           <--|" if equal else "not equal         <--|"))
        if self.debug:
            print("-----------------------------------")
        return equal

    def check_doors_open(self, frame: Frame = None):
        if frame is None:
            frame = self.get_frame()
        # Add opened doors check
        px_up = 50
        h_bar = self.hor_lines["hor_hp_bar"][1]  # HP bar height
        for i in range(1, 4, 1):
            line = self._get_horizontal_line(
                [
                    480 / 1080.0,
                    h_bar - ((px_up * i) / self.height),
                    600 / 1080.0,
                    h_bar - ((px_up * i) / self.height),
                ],
                frame,
            )
            white = True
            for px in line:
                if px[0] != 255 or px[1] != 255 or px[2] != 255:
                    white = False
                    break
            if white:
                return True
        return False

    def check_frame(self, coords_name: str, frame: Frame = None):
        """
        Given a coordinates name it checkes if the Frame has those pixels.
        If no Frame given , it will take a screenshot.
        :return:
        """
        dict_to_take = []
        if coords_name in self.static_coords.keys():
            dict_to_take = self.static_coords
        elif coords_name in self.specific_checks_coords.keys():
            dict_to_take = self.specific_checks_coords
        else:
            print("No coordinates called %s is saved in memory! Returning false." % coords_name)
            return False
        if self.debug:
            print("Checking %s" % (coords_name))
        if frame is None:
            frame = self.get_frame()
        around = dict_to_take[coords_name].get("around", 2)
        is_equal = self._check_screen_points_equal(
            frame,
            dict_to_take[coords_name]["coordinates"],
            dict_to_take[coords_name]["values"],
            around=around,
        )
        return is_equal

    def get_frame(self) -> np.ndarray:
        if self.stop_requested:
            exit()
        return self.device_connector.adb_screen_getpixels()

    def get_frame_state_complete(self, frame: Frame = None) -> dict:
        """
        Computes a complete check on given frame (takes a screen if none passed.
        Returns a dictionary with all known states with boolean value assigned.
        :return:
        """
        result = {}
        if frame is None:
            frame = self.get_frame()
        for k, v in self.static_coords.items():
            around = self.static_coords[k].get("around", 2)
            if self.debug:
                print("Checking %s, around = %d" % (k, around))
            result[k] = self._check_screen_points_equal(frame, v["coordinates"], v["values"], around=around)
        return result

    def define_state_by_pixel_matching(self, frame: Frame) -> str:
        if frame is None:
            frame = self.get_frame()
        for k, v in self.static_coords.items():
            around = self.static_coords[k].get("around", 2)
            if self.debug:
                print("Checking %s, around = %d" % (k, around))
            if self._check_screen_points_equal(frame, v["coordinates"], v["values"], around=around):
                return k
        return "unknown"

    def define_state_by_ocr(self) -> str:
        min_energy = 5

        os.system("adb exec-out screencap -p >  screen.png")
        image = cv2.imread("screen.png")
        extracted_from_image = extract_text_from_image(image)

        extracted_text = extracted_from_image.get("text", "")
        params = extracted_from_image.get("params", {})
        energy_text = params.get("energy", "")
        energy = energy_text.split("/")[0] if energy_text else None

        logger.debug(f"Text extracted: {extracted_text}, Energy: {energy}")

        if "in_game" in extracted_text:
            return "in_game"
        elif "mysterious" in extracted_text and "vendor" in extracted_text:
            return "mistery_vendor"
        elif "angel" in extracted_text:
            return "angel_heal"
        elif "lucky" in extracted_text or "wheel" in extracted_text:
            return "fortune_wheel"
        elif "level" in extracted_text or "adventure" in extracted_text:
            return "select_ability"
        elif "special" in extracted_text or "reward" in extracted_text:
            return "special_gift_respin"
        elif "devil" in extracted_text:
            return "devil_question"
        elif "game over" in extracted_text:
            return "endgame"
        # elif "bones" in extracted_text and energy >= min_energy:
        #     return ""

        return "unknown"

    def get_frame_state(self, frame: Frame = None) -> str:
        """
        Computes a complete check on given frame (takes a screen if none passed.
        Returns a string with the name of current state, or unknown if no state found.
        :return:
        """
        start_time = time.perf_counter()

        state = self.define_state_by_ocr()

        end_time = time.perf_counter()
        logger.debug(f"OCR detection took {end_time-start_time:0.4f} seconds")

        if state == "unknown":
            start_time = time.perf_counter()
            logger.debug("Couldn't detect state. Falling back for Pixel matching...")

            state = self.define_state_by_pixel_matching(frame)

            end_time = time.perf_counter()

            logger.debug(f"Pixel detection failed in {end_time-start_time:0.4f} seconds")

        return state

    def _get_horizontal_line(self, hor_line, frame: Frame):
        """
        Returns a horizontal line (list of colors) given hor_line [x1, y1, x2, y2] coordinates. If no frame given, it takes a screen.
        :param hor_line:
        :param frame:
        :return:
        """
        x1, y1, x2, y2 = (
            hor_line[0] * self.width,
            hor_line[1] * self.height,
            hor_line[2] * self.width,
            hor_line[3] * self.height,
        )
        if frame is None:
            frame = self.get_frame()
        start = int(y1 * self.width + x1)
        size = int(x2 - x1)
        line = frame[start : start + size]
        return line

    def get_line_exp_bar(self, frame: Frame = None):
        """
        Returns the colors of Experience bar as a line. If no frame given, it takes a screen.
        :param frame:
        :return:
        """
        line = self._get_horizontal_line(self.hor_lines["hor_exp_bar"], frame)
        masked_yellow = []
        for px in line:
            if self.pixel_equals(px, self.yellow_experience, 3):
                masked_yellow.append(px)
            else:
                masked_yellow.append([0, 0, 0, 0])
        return masked_yellow

    def filter_raw_hp_line_window(self, line):
        """
        Given a horizontal array of pixels RGBA, filter data in order to obtain position of character based on his HP.
        """
        # Filter outlayers:
        first_filter = self.remove_outlayers_in_line(line, self.green_hp)
        return first_filter

    def filter_line_by_color(self, line):
        masked_green = []
        for px in line:
            if self.pixel_equals(px, self.green_hp, [8, 12, 8]) or self.pixel_equals(
                px, self.green_hp_high, [8, 12, 8]
            ):
                masked_green.append(self.green_hp)
            else:
                masked_green.append([0, 0, 0, 0])
        return masked_green

    def get_player_decentering_by__start_stop(self, line):
        first = 0
        last = 0
        for i, el in enumerate(line):
            if self.pixel_equals(self.green_hp, el, 2):
                if first == 0:
                    first = i
                last = i
        center_px = (last + first) / 2
        center_diff = int((self.width / 2) - center_px)
        return center_diff

    def get_player_decentering_by_max_green_group(self, line):
        groups = []
        high_val = self.green_hp[1]
        start = 0
        in_block = False
        biggest_width = [0, 0, 0]
        for i, el in enumerate(line):
            if el[1] == high_val:
                if in_block:
                    groups.append([start, i, i - start])
                    if groups[-1][-1] > biggest_width[-1]:
                        biggest_width = groups[-1]
                else:
                    in_block = True
                    start = i
        center_px = (biggest_width[0] + biggest_width[1]) / 2
        center_diff = int((self.width / 2) - center_px)
        return center_diff

    def get_player_decentering(self) -> Tuple[int, str]:
        line = self.get_line_hp_bar()
        line = self.filter_line_by_color(line)
        line_filtered = self.filter_raw_hp_line_window(line)

        center_diff = self.get_player_decentering_by_max_green_group(line_filtered)
        if abs(center_diff) < (self.door_width * self.width) / 4.0:
            direction = "center"
        else:
            direction = "right" if center_diff < 0 else "left"
        logger.debug("Character on the %s side by %dpx" % (direction, abs(center_diff)))
        return center_diff, direction

    def remove_outlayers_in_line(self, masked_green, high_pixel_color):
        line = masked_green.copy()
        n = len(line)
        i = 0
        window_width = 15
        min_greens_pixels = 9
        while i < n:
            if i in range(window_width):  # First 4 take black. no problem losing them
                line[i] = [0, 0, 0, 0]
            else:
                counter = 0
                for j in range(window_width):
                    counter += 1 if masked_green[i - j][0] == high_pixel_color[0] else 0
                for j in range(window_width):
                    line[i - j] = [0, 0, 0, 0] if counter < min_greens_pixels else high_pixel_color
                i += window_width - 1  # Skip() and go to next window
            i += 1
        for i in range(window_width):  # Last 4 take black. no problem losing them
            line[n - i - 1] = [0, 0, 0, 0]
        return line

    def get_line_hp_bar(self, frame: Frame = None):
        """
        Returns the colors of Experience bar as a line. If no frame given, it takes a screen.
        :param frame:
        :return:
        """
        line = self._get_horizontal_line(self.hor_lines["hor_hp_bar"], frame)
        return line

    def get_horizontal_line(self, line_name: str, frame: Frame = None):
        """
        Returns the colors of Experience bar as a line. If no frame given, it takes a screen.
        :param line_name: line x,y coordinates
        :param frame:
        :return:
        """
        if line_name not in self.hor_lines:
            print("Given line name '%s' is not a known horizontal line name." % line_name)
            return []
        return self._get_horizontal_line(self.hor_lines[line_name], frame)

    def _check_bar_has_changed(self, old_line_hor_bar, current_exp_bar, around=0):
        if len(old_line_hor_bar) != len(current_exp_bar):
            min_len = min(len(old_line_hor_bar), len(current_exp_bar))
            old_line_hor_bar = old_line_hor_bar[:min_len]
            current_exp_bar = current_exp_bar[:min_len]
        changed = False
        for i in range(len(old_line_hor_bar)):
            if not self.pixel_equals(old_line_hor_bar[i], current_exp_bar[i], around=around):
                changed = True
                break
        return changed

    def check_exp_bar_has_changed(self, old_line_hor_bar, frame: Frame = None):
        """
        Checks if old experience bar line is different that this one. If no frame given, it takes a screen.
        :param old_line_hor_bar:
        :param frame:
        :return:
        """
        if self.debug:
            print("Checking LineExpBar has changed")
        new_line = self.get_line_exp_bar(frame)
        return self._check_bar_has_changed(old_line_hor_bar, new_line, around=2)

    def check_upper_line_has_changed(self, old_line, frame: Frame = None):
        """
        Checks if old upper line is different that this one. If no frame given, it takes a screen.
        :param old_line:
        :param frame:
        :return:
        """
        if self.debug:
            print("Checking LineUpper has changed")
        new_line = self.get_horizontal_line("hor_up_line", frame)
        return self._check_bar_has_changed(old_line, new_line, around=10)
