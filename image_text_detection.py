import cv2
import numpy as np
import pytesseract

import os

# os.system("adb -s 127.0.0.1:5555 exec-out screencap -p >  screen.png")

text_location = {
    "global-level-up": {"startX": 90, "startY": 450, "endX": 1000, "endY": 550},
    "level-up": {"startX": 150, "startY": 490, "endX": 925, "endY": 570},
    "check-energy": {"startX": 375, "startY": 40, "endX": 500, "endY": 80},
    "mysterious-vendor": {"startX": 305, "startY": 330, "endX": 780, "endY": 400},
    "endgame": {"startX": 320, "startY": 550, "endX": 750, "endY": 650},
}


def sum_white_pixels(image):
    in_game = {"startX": 40, "startY": 30, "endX": 90, "endY": 100}
    pause_button = image[in_game["startY"] : in_game["endY"], in_game["startX"] : in_game["endX"]]

    return np.sum(pause_button == 255)


def extract_text_from_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)[1]
    kernel = np.ones((3, 3), np.uint8)
    closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    inv = cv2.bitwise_not(closing)  # invert black/white
    img_rgb = cv2.cvtColor(inv, cv2.COLOR_BGR2RGB)

    # print(f"in_game white pixels: {sum_white_pixels(closing)}")
    if sum_white_pixels(closing) > 1700:
        return "in_game"

    for k, v in text_location.items():
        cropped = img_rgb[v["startY"] : v["endY"], v["startX"] : v["endX"]]
        text = pytesseract.image_to_string(cropped).lower().strip()

        if text != "":
            return text

    # cv2.imwrite("cropped.png", inv)

    return ""


# path = "screenshots"
# # path = "datas/1080x2220/screens"
# (_, _, filenames) = next(os.walk(path))

# for file in filenames:
#     image = cv2.imread(f"{path}/{file}")
#     text = extract_text_from_image(image)
#     print(f"\nImage: {file}, Text: {text}")
