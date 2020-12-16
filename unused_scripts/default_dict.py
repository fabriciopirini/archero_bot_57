import json


def getButtons():
    calculus_width = 1080
    calculus_heigth = 2220
    buttons = {
        "pause": [20 / calculus_width, 20 / calculus_heigth],
        "start": [540 / calculus_width, 1700 / calculus_heigth],
        "collect_time_prize": [330 / calculus_width, 1490 / calculus_heigth],
        "ability_left": [210 / calculus_width, 1500 / calculus_heigth],
        "ability_center": [540 / calculus_width, 1500 / calculus_heigth],
        "ability_right": [870 / calculus_width, 1500 / calculus_heigth],
        "heal_right": [800 / calculus_width, 1590 / calculus_heigth],
        "heal_left": [290 / calculus_width, 1590 / calculus_heigth],
        "spin_wheel_back": [85 / calculus_width, 2140 / calculus_heigth],
        "lucky_wheel_start": [540 / calculus_width, 1675 / calculus_heigth],
        "ability_daemon_reject": [175 / calculus_width, 1790 / calculus_heigth],
        "close_end": [540 / calculus_width, 1993 / calculus_heigth],
        "menu_world": [540 / calculus_width, 2131 / calculus_heigth],
        "menu_equipment": [273 / calculus_width, 2131 / calculus_heigth],
        "menu_avatar_weapon": [166 / calculus_width, 226 / calculus_heigth],
        "menu_equip_weapon": [535 / calculus_width, 1780 / calculus_heigth],
        "resume": [540 / calculus_width, 1576 / calculus_heigth],
    }
    return buttons
