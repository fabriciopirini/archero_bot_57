import os
import cv2
import numpy as np
import pytesseract

# os.system("adb -s 127.0.0.1:5555 exec-out screencap -p >  screen.png")


def extract_text_from_image(image):
    cropped = image[300:430, 40:1000]

    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)[1]
    kernel = np.ones((3, 3), np.uint8)
    closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    inv = cv2.bitwise_not(closing)  # invert black/white

    cv2.imwrite("cropped.png", inv)

    img_rgb = cv2.cvtColor(inv, cv2.COLOR_BGR2RGB)

    return pytesseract.image_to_string(img_rgb)


# (_, _, filenames) = next(os.walk("datas/1080x2220/screens"))

# for file in filenames:
#     image = cv2.imread(f"datas/1080x2220/screens/{file}")
#     text = extract_text_from_image(image)
#     print(text)
