import os
from typing import Dict
from typing import Optional

import cv2
import numpy as np
import pytesseract
from loguru import logger

text_location = {
    "global-level-up": {"startX": 90, "startY": 450, "endX": 1000, "endY": 550},
    "level-up": {"startX": 150, "startY": 490, "endX": 925, "endY": 570},
    "mysterious-vendor": {"startX": 305, "startY": 330, "endX": 780, "endY": 400},
    "endgame": {"startX": 320, "startY": 550, "endX": 750, "endY": 650},
}


def sum_white_pixels(image) -> int:
    in_game = {"startX": 40, "startY": 30, "endX": 90, "endY": 100}
    pause_button = image[in_game["startY"] : in_game["endY"], in_game["startX"] : in_game["endX"]]

    return np.sum(pause_button == 255)


def extract_energy(image=None) -> int:
    if image is None:
        _, image = process_image(image)

    energy = {"startX": 375, "startY": 35, "endX": 500, "endY": 85}
    cropped = image[energy["startY"] : energy["endY"], energy["startX"] : energy["endX"]]
    text = pytesseract.image_to_string(cropped).lower().strip()

    try:
        return int(text.split("/")[0]) if text else 0
    except Exception:
        logger.exception("Exception while extracting energy from image")
        return 0


def extract_text(image, context: str) -> str:
    cropped = image[
        text_location[context]["startY"] : text_location[context]["endY"],
        text_location[context]["startX"] : text_location[context]["endX"],
    ]
    if context == "check-energy":
        cv2.imshow("cropped", cropped)
        cv2.waitKey()
    return pytesseract.image_to_string(cropped).lower().strip()


def process_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)[1]
    kernel = np.ones((3, 3), np.uint8)
    white_text_img = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    black_text_img = cv2.bitwise_not(white_text_img)

    return white_text_img, black_text_img


def extract_text_from_image(image) -> Dict[str, Optional[str]]:
    white_text_img, black_text_img = process_image(image)

    # print(f"in_game white pixels: {sum_white_pixels(closing)}")
    if sum_white_pixels(white_text_img) > 1700:
        return {"text": "in_game", "params": {}}

    for key in text_location.keys():
        text = extract_text(black_text_img, key)

        if text != "":
            return {"text": text, "params": {}}

    # cv2.imwrite("cropped.png", inv)

    return {"text": "", "params": {}}


if __name__ == "__main__":
    path = "screenshots"
    # path = "datas/1080x2220/screens"
    (_, _, filenames) = next(os.walk(path))

    for file in filenames:
        image = cv2.imread(f"{path}/{file}")
        text = extract_text_from_image(image)
        print(f"Image: {file}, Text: {text}")
