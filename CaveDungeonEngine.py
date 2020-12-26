import enum
import os
import time
from datetime import datetime

import cv2
from loguru import logger
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QObject

from GameScreenConnector import GameScreenConnector
from image_text_detection import extract_energy
from StatisticsManager import StatisticsManager
from UsbConnector import UsbConnector
from Utils import buildDataFolder
from Utils import getCoordFilePath
from Utils import loadJsonData
from Utils import readAllSizesFolders


class HealingStrategy(enum.Enum):
    AlwaysHeal = 0
    AlwaysPowerUp = 1


class CaveEngine(QObject):
    levelChanged = pyqtSignal(int)
    addLog = pyqtSignal(str)
    resolutionChanged = pyqtSignal(int, int)
    dataFolderChanged = pyqtSignal(str)
    noEnergyLeft = pyqtSignal()
    gameWon = pyqtSignal()
    healingStrategyChanged = pyqtSignal(bool)

    # onDictionaryTapsChanged = pyqtSignal(dict)
    # onButtonLocationChanged = pyqtSignal(str)
    # onImageSelected = pyqtSignal()
    MAX_LEVEL = 20

    playtime = 70
    # Set this to true if you want to use generated data with TouchManager. Uses below coordinates path
    UseGeneratedData = False
    # Set this to true if keep receiving "No energy, waiting for one minute"
    UseManualStart = False
    # Set this to true if want to automatically check for energy
    SkipEnergyCheck = False
    data_pack = "datas"
    coords_path = "coords"
    buttons_filename = "buttons.json"
    movements_filename = "movements.json"
    print_names_movements = {
        "n": "up",
        "s": "down",
        "e": "right",
        "w": "left",
        "ne": "up-right",
        "nw": "up-left",
        "se": "down-right",
        "sw": "down-left",
    }

    t_intro = "intro"
    t_normal = "normal"
    t_heal = "heal"
    t_boss = "boss"
    t_final_boss = "final_boss"

    levels_type = {
        0: t_intro,
        1: t_normal,
        2: t_heal,
        3: t_normal,
        4: t_heal,
        5: t_boss,
        6: t_normal,
        7: t_heal,
        8: t_normal,
        9: t_heal,
        10: t_boss,
        11: t_normal,
        12: t_heal,
        13: t_normal,
        14: t_heal,
        15: t_boss,
        16: t_normal,
        17: t_heal,
        18: t_normal,
        19: t_heal,
        20: t_final_boss,
    }
    max_loops_game = 20

    def __init__(self, connectImmediately: bool = False):
        super(QObject, self).__init__()
        self.currentLevel = 0
        self.currentDungeon = 6
        self.statisctics_manager = StatisticsManager()
        self.start_date = datetime.now()
        self.stat_lvl_start = 0
        self.screen_connector = GameScreenConnector()
        self.screen_connector.debug = False
        self.width, self.heigth = 1080, 2220
        self.device_connector = UsbConnector()
        self.device_connector.setFunctionToCallOnConnectionStateChanged(self.onConnectionStateChanged)
        self.buttons = {}
        self.movements = {}
        self.stopRequested = False
        self.currentDataFolder = ""
        self.dataFolders = {}
        self.healingStrategy = HealingStrategy.AlwaysPowerUp
        self.centerAfterCrossingDungeon = False
        if connectImmediately:
            self.initDeviceConnector()
        self.check_seconds = 4

    def initDataFolders(self):
        self.dataFolders = readAllSizesFolders()
        deviceFolder = buildDataFolder(self.width, self.heigth)
        first_folder = list(self.dataFolders.keys())[0]
        if deviceFolder not in self.dataFolders:
            logger.info("Error: not having %s coordinates. Trying with %s" % (deviceFolder, first_folder))
            deviceFolder = first_folder
        self.changeCurrentDataFolder(deviceFolder)

    def initdeviceconnector(self):
        self.device_connector.connect()

    def changeHealStrategy(self, always_heal: bool):
        self.healingStrategy = HealingStrategy.AlwaysHeal if always_heal else HealingStrategy.AlwaysPowerUp
        self.healingStrategyChanged.emit(always_heal)

    def changeChapter(self, new_chapter):
        self.currentDungeon = new_chapter

    def onConnectionStateChanged(self):
        if self.device_connector.connected:
            self.initDataFolders()
            self.screen_connector.change_device_connector(self.device_connector)
            self.updateScreenSizeByPhone()

    def updateScreenSizeByPhone(self):
        if self.device_connector is not None:
            w, h = self.device_connector.adb_get_size()
            self.change_screen_size(w, h)
            self.screen_connector.change_screen_size(w, h)
        else:
            logger.info("Device connector is none. initialize it before calling this method!")

    def changeCurrentDataFolder(self, new_folder):
        self.currentDataFolder = new_folder
        self.loadCoords()
        self.dataFolderChanged.emit(new_folder)

    def loadCoords(self):
        self.buttons = loadJsonData(getCoordFilePath(self.buttons_filename, sizePath=self.currentDataFolder))
        self.movements = loadJsonData(getCoordFilePath(self.movements_filename, sizePath=self.currentDataFolder))

    def setStopRequested(self):
        self.stopRequested = True
        self.screen_connector.stopRequested = True
        self.statisctics_manager.saveOneGame(self.start_date, self.stat_lvl_start, self.currentLevel)

    def change_screen_size(self, w, h):
        self.width, self.heigth = w, h
        logger.info("New resolution set: %dx%d" % (self.width, self.heigth))
        self.resolutionChanged.emit(w, h)

    def swipe_points(self, start, stop, s):
        start = self.buttons[start]
        stop = self.buttons[stop]
        logger.info("Swiping between %s and %s in %f" % (start, stop, s))
        self.device_connector.adb_swipe(
            [
                start[0] * self.width,
                start[1] * self.heigth,
                stop[2] * self.width,
                stop[3] * self.heigth,
            ],
            s,
        )

    def swipe(self, name, s):
        if self.stopRequested:
            exit()
        coord = self.movements[name]
        logger.debug("Swiping %s in %.2f" % (self.print_names_movements[name], s))
        # convert back from normalized values
        self.device_connector.adb_swipe(
            [
                coord[0][0] * self.width,
                coord[0][1] * self.heigth,
                coord[1][0] * self.width,
                coord[1][1] * self.heigth,
            ],
            s,
        )

    def tap(self, name):
        if self.stopRequested:
            exit()
        # convert back from normalized values
        x, y = int(self.buttons[name][0] * self.width), int(self.buttons[name][1] * self.heigth)
        logger.debug("Tapping on %s at [%d, %d]" % (name, x, y))
        self.device_connector.adb_tap((x, y))

    def wait(self, s):
        decimal = s
        if int(s) > 0:
            decimal = s - int(s)
            for _ in range(int(s)):
                if self.stopRequested:
                    exit()
                time.sleep(1)
        if self.stopRequested:
            exit()
        time.sleep(decimal)

    def exit_dungeon_uncentered(self, second_check=True):
        # Center
        _, direction = self.screen_connector.get_player_decentering()
        self.wait(0.5)
        if direction == "left":
            self.swipe("w", 0.7)
            self.swipe("ne", 4)
        elif direction == "right":
            self.swipe("e", 0.7)
            self.swipe("nw", 4)
        elif direction == "center":
            self.swipe("n", 2)
        else:
            self.swipe("n", 2)
        if second_check and self.screen_connector.get_frame_state() != "in_game":
            self.reactGamePopups()
            self.exit_dungeon_uncentered(False)
        self.wait(1)  # Safety wait for extra check

    def goTroughDungeon10(self):
        logger.info("Going through dungeon (designed for #10)")
        self.swipe("n", 0.5)
        self.swipe("nw", 4)
        self.swipe("ne", 4)
        self.swipe("nw", 2)
        self.swipe("e", 0.20)

    def goTroughDungeon_old(self):
        logger.info("Going through dungeon old design 'S')")
        self.swipe("n", 1.5)
        self.swipe("w", 0.32)
        self.swipe("n", 0.5)
        self.swipe("e", 0.32)
        self.swipe("e", 0.32)
        self.swipe("n", 0.5)
        self.swipe("w", 0.325)
        self.swipe("n", 1.5)

    def goTroughDungeon6(self):
        logger.debug("Going through dungeon (designed for #6)")
        self.swipe("n", 1.5)
        self.swipe("w", 0.32)
        self.swipe("n", 0.5)
        self.swipe("e", 0.32)
        self.swipe("e", 0.32)
        self.swipe("n", 0.7)
        self.swipe("w", 0.325)
        self.swipe("w", 0.3)
        self.swipe("n", 1.6)
        self.swipe("e", 0.28)
        self.swipe("n", 2.5)

    def goTroughDungeon3(self):
        logger.info("Going through dungeon (designed for #3)")
        self.swipe("n", 1.5)
        self.swipe("w", 0.25)
        self.swipe("n", 0.5)
        self.swipe("e", 0.25)
        self.swipe("n", 2)
        # And now we need to go around possible obstacle
        self.swipe("w", 1)
        self.swipe("n", 0.5)
        self.swipe("e", 1)
        self.swipe("n", 0.3)

    def goTroughDungeon(self):
        if self.currentDungeon == 3:
            self.goTroughDungeon3()
        elif self.currentDungeon == 6:
            self.goTroughDungeon6()
        elif self.currentDungeon == 10:
            self.goTroughDungeon10()
        else:
            self.goTroughDungeon_old()
        # Add movement if decentering is detected
        if self.centerAfterCrossingDungeon:
            self.centerPlayer()

    def centerPlayer(self):
        px, dir = self.screen_connector.get_player_decentering()
        # Move in oppositye direction. Speed is made by y = mx + q
        duration = 0.019 * abs(px) - 4.8
        if px < self.screen_connector.door_width / 2.0:
            pass
        if dir == "left":
            logger.info("Centering player <--")
            self.swipe("e", duration)
        elif dir == "right":
            logger.info("Centering player -->")
            self.swipe("w", duration)
        elif dir == "center":
            pass

    def letPlay(self, _time: int, is_boss=False):
        check_exp_bar = not is_boss
        # self.wait(2)
        logger.debug("Auto attacking")
        experience_bar_line = self.screen_connector.get_line_exp_bar()
        recheck = False
        for i in range(_time, 0, -1):
            if i % self.check_seconds == 0 or recheck:
                recheck = False
                logger.debug("Checking screen...")
                frame = self.screen_connector.get_frame()
                state = self.screen_connector.get_frame_state(frame)
                if state == "unknown":
                    logger.info("Unknown screen situation detected. Checking again...")
                    self.wait(2)
                    if self.screen_connector.get_frame_state() == "unknown":
                        raise Exception("unknown_screen_state")
                    else:
                        recheck = True
                        continue
                elif state == "endgame" or state == "repeat_endgame_question":
                    if state == "repeat_endgame_question":
                        self.wait(5)
                    logger.info("Game ended")
                    self.wait(1)
                    logger.info("Going back to menu...")
                    self.tap("close_end")
                    self.wait(8)  # Wait to go to the menu
                    raise Exception("ended")
                elif state in [
                    "select_ability",
                    "fortune_wheel",
                    "devil_question",
                    "mistery_vendor",
                    "ad_ask",
                ]:
                    logger.info("Level ended. Collecting results for leveling up.")
                    self.wait(1)
                    return
                elif check_exp_bar and self.screen_connector.check_exp_bar_has_changed(experience_bar_line, frame):
                    logger.info("Experience gained!")
                    self.wait(3)
                    return
                elif state == "in_game":
                    if self.screen_connector.check_doors_open(frame):
                        logger.info("In game, door opened")
                        self.wait(1)
                        return
                    else:
                        logger.debug("In game. Playing but level not ended")
            self.wait(1)

    def _exitEngine(self):
        self.statisctics_manager.saveOneGame(self.start_date, self.stat_lvl_start, self.currentLevel)
        exit(1)

    def reactGamePopups(self) -> None:
        state = ""
        i = 0
        wait_time = 1
        wait_time_wheel = 5
        have_battle_pass = True

        while state != "in_game":
            if self.stopRequested:
                exit()
            if i > self.max_loops_game:
                logger.info("Max loops reached")
                self._exitEngine()
            logger.debug("Checking screen...")
            state = self.screen_connector.get_frame_state()
            logger.info("state: %s" % state)
            if state == "select_ability":
                self.tap("ability_left")
            elif state == "fortune_wheel":
                self.tap("lucky_wheel_start")
                self.wait(wait_time_wheel)
                continue
            elif state == "ad_ask":
                if have_battle_pass:
                    self.tap("lucky_wheel_start")
                else:
                    self.tap("spin_wheel_back")
            elif state in [
                "repeat_endgame_question",
                "mistery_vendor",
                "special_gift_respin",
            ]:
                self.tap("spin_wheel_back")
            elif state == "devil_question":
                self.tap("ability_daemon_reject")
            elif state == "angel_heal":
                self.tap("heal_right" if self.healingStrategy == HealingStrategy.AlwaysHeal else "heal_left")
            elif state == "on_pause":
                self.tap("resume")
            elif state == "time_prize":
                logger.info("Collecting time prize and ending game. Unexpected behaviour but managed")
                self.tap("collect_time_prize")
                self.wait(wait_time)
                raise Exception("ended")
            elif state == "endgame":
                raise Exception("ended")
            i += 1
            self.wait(wait_time)

    def normal_lvl(self):
        self.goTroughDungeon()
        self.letPlay(self.playtime)
        self.reactGamePopups()
        self.exit_dungeon_uncentered()

    def normal_lvl_manual(self):
        self.goTroughDungeon()
        self.letPlay(self.playtime)
        self.tap("spin_wheel_back")  # guard not to click on mistery vendor
        self.wait(1)
        self.tap("ability_left")
        self.wait(1)
        self.tap("spin_wheel_back")  # guard not to click on watch
        self.wait(3)
        self.tap("ability_left")
        self.wait(2)
        self.tap("spin_wheel_back")  # guard not to click on watch or buy stuff (armor or others)
        self.wait(1)
        self.exit_dungeon_uncentered()

    def heal_lvl(self):
        self.swipe("n", 1.7)
        self.reactGamePopups()
        self.swipe("n", 0.8)
        self.reactGamePopups()
        self.swipe("n", 1)
        # self.exit_dungeon_uncentered()

    def heal_lvl_manual(self):
        self.swipe("n", 1.7)
        self.wait(1)
        self.tap("ability_daemon_reject")
        self.tap("ability_right")
        self.wait(1.5)
        self.tap("spin_wheel_back")
        self.wait(1)
        self.swipe("n", 0.8)
        self.wait(1.5)
        self.tap("spin_wheel_back")
        self.wait(1.5)
        self.exit_dungeon_uncentered()

    def boss_lvl(self):
        self.swipe("n", 2)
        self.swipe("w", 0.25)
        self.swipe("n", 2)
        self.letPlay(self.playtime, is_boss=True)
        self.reactGamePopups()
        self.exit_dungeon_uncentered()

    def boss_lvl_manual(self):
        self.swipe("n", 2)
        self.swipe("n", 1.2)
        if self.currentLevel != 15:
            self.swipe("n", 1)
        self.letPlay(self.playtime, is_boss=True)
        self.tap("lucky_wheel_start")
        self.wait(6)
        self.tap("spin_wheel_back")
        self.wait(1.5)
        self.tap("ability_daemon_reject")
        self.tap("ability_left")
        self.wait(1.5)
        self.tap("spin_wheel_back")  # guard not to click on watch
        self.wait(1.5)
        self.tap("ability_left")  # Extra guard for level up
        self.wait(1.5)
        self.exit_dungeon_uncentered()

    def intro_lvl(self):
        self.wait(3)
        self.tap("ability_daemon_reject")
        self.tap("ability_left")
        self.swipe("n", 3)
        self.wait(5)
        self.tap("lucky_wheel_start")
        self.wait(5)
        self.swipe("n", 2)

    def play_cave(self):
        self.levelChanged.emit(self.currentLevel)
        if self.currentLevel < 0 or self.currentLevel > 20:
            logger.info("level out of range: %d" % self.currentLevel)
            self._exitEngine()
        while self.currentLevel <= self.MAX_LEVEL:
            logger.info("Level %d: %s" % (self.currentLevel, str(self.levels_type[self.currentLevel])))
            if self.levels_type[self.currentLevel] == self.t_intro:
                self.intro_lvl()
            elif self.levels_type[self.currentLevel] == self.t_normal:
                self.normal_lvl()
            elif self.levels_type[self.currentLevel] == self.t_heal:
                self.heal_lvl()
            elif self.levels_type[self.currentLevel] == self.t_final_boss:
                self.boss_final()
            elif self.levels_type[self.currentLevel] == self.t_boss:
                self.boss_lvl()
            self.changeCurrentLevel(self.currentLevel + 1)
        self.wait(5)
        if self.screen_connector.check_frame("endgame"):
            self.tap("close_end")
            self.gameWon.emit()

    def changeCurrentLevel(self, new_lvl):
        self.currentLevel = new_lvl
        self.levelChanged.emit(self.currentLevel)

    def boss_final(self):
        self.wait(2)
        self.swipe("w", 3)
        self.wait(50)
        self.reactGamePopups()
        self.tap("start")
        self.wait(2)
        self.swipe("n", 5)
        self.wait(0.5)
        self.swipe("ne", 3)
        self.wait(5)
        self.tap("close_end")  # this is to wxit

    def chooseCave(self):
        logger.info("Main menu")
        self.tap("start")
        self.wait(3)

    def start_infinite_play(self):
        while True:
            self.start_one_game()
            self.currentLevel = 0

    def enough_energy(self, min_energy=5):
        result = self.device_connector.my_device.screencap()
        with open("screen.png", "wb") as fp:
            fp.write(result)

        image = cv2.imread("screen.png")

        energy = extract_energy(image)

        return True if energy >= min_energy else False

    def start_one_game(self):
        delay_energy_check = 30

        self.start_date = datetime.now()
        self.stat_lvl_start = self.currentLevel
        self.stopRequested = False
        self.screen_connector.stopRequested = False

        logger.info("New game. Starting from level %d" % self.currentLevel)
        self.wait(5)
        if self.currentLevel == 0:
            if self.UseManualStart:
                input("Press any key to start a game (your energy bar must be at least 5)")
            else:
                logged_first = False
                while not self.SkipEnergyCheck and not self.screen_connector.check_frame("least_5_energy"):
                    if not logged_first:
                        logger.info(f"Waiting for enough energy...")
                        logged_first = True

                    self.noEnergyLeft.emit()
                    self.wait(delay_energy_check)
            self.chooseCave()

        start_time = time.perf_counter()
        try:
            self.play_cave()
        except Exception as exc:
            self.pressCloseEndIfEndedFrame()
            if exc.args[0] == "ended":
                logger.info("Game ended. Farmed a little bit...")
            elif exc.args[0] == "unable_exit_dungeon":
                logger.info("Unable to exit a room in a dungeon. Waiting instead of causing troubles")
                self._exitEngine()
            elif exc.args[0] == "unknown_screen_state":
                logger.info("Unknows screen state. Exiting instead of doing trouble")
                self._exitEngine()
            else:
                logger.exception("Got an unknown exception: %s" % exc)
                self._exitEngine()

        end_time = time.perf_counter()
        logger.info(f"This play took {(end_time-start_time)/60:0.1f} minutes")

        self.pressCloseEndIfEndedFrame()
        self.statisctics_manager.saveOneGame(self.start_date, self.stat_lvl_start, self.currentLevel)

    def pressCloseEndIfEndedFrame(self):
        if self.screen_connector.check_frame("endgame"):
            self.tap("close_end")
