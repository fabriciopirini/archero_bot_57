import json
import os
import sys

import numpy as np
from PIL import Image

from GameScreenConnector import GameScreenConnector
from Utils import readAllSizesFolders

# from pure_adb_connector import *


def getImageFrame(path: str):
    with Image.open(path, "r") as im:
        pixval = np.array(im.getdata())
    return pixval


screens_data = readAllSizesFolders()
keys = [k for k in screens_data.keys()]

for i in range(len(keys)):
    print("%d: %s" % (i, keys[i]))
choosen = input("Select your number")
folder = keys[int(choosen)]
screens_path = os.path.join("datas", folder, "screens")
print("Using %s" % screens_path)

selected_debug = input(
    "Do you wish to debug? (set yes only if you did it already once and found some rows with NO_DETECTION): (y/n):"
)
debug = False
if selected_debug != None:
    if selected_debug == "y" or selected_debug == "yes":
        debug = True
width, heigth = screens_data[folder]
excluded = []

screen_conector = GameScreenConnector()
screen_conector.change_screen_size(width, heigth)
screen_conector.debug = debug
static_coords = screen_conector.static_coords

files = os.listdir(screens_path)
files.sort()
all_ok = True
for file in files:
    if file not in excluded:
        full_path = os.path.join(screens_path, file)
        frame = getImageFrame(full_path)
        complete_frame = screen_conector.get_frame_state_complete(frame)
        computed = [k for k, v in complete_frame.items() if v]
        sum = len(computed)
        ok = False
        exergy_print = "" if not screen_conector.check_frame("least_5_energy", frame) else " + least_5_energy"
        if sum == 0:
            print("NO_DETECTION - %s %s" % (file, exergy_print))
        elif sum == 1:
            print("OK - %s: %s %s" % (file, computed[0], exergy_print))
            ok = True
        else:
            ones_name_purged_singular = [
                k for k in computed if len(screen_conector.static_coords[k]["coordinates"]) > 1
            ]
            removed = [k for k in computed if k not in ones_name_purged_singular]
            if len(ones_name_purged_singular) == 0:
                print("MUL_DETECTIONS %s: %s %s" % (file, ", ".join(computed), exergy_print))
            elif len(ones_name_purged_singular) == 1:
                print(
                    "OK - %s: %s. Extra detected singulars: %s %s"
                    % (
                        file,
                        ones_name_purged_singular[0],
                        ", ".join(removed),
                        exergy_print,
                    )
                )
                ok = True
            else:
                print("MUL_DETECTIONS %s: %s %s" % (file, ", ".join(ones_name_purged_singular), exergy_print))
        all_ok = all_ok and ok

if all_ok:
    print("All tests passed!")
else:
    print(
        "Got some failed tests. It is advised not to use the bot. Infinite loops and damage can be done by randomply clicking without knowledge."
    )

# a = input("Press ENTER to exit")
