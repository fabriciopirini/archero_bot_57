import math

from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget

from GameController.GameControllerController import GameControllerController
from GameController.GameControllerModel import GameControllerModel
from QMyWidgets.QLevelState import PlayState
from QMyWidgets.QLevelState import QLevelState


class QDeskArea(QWidget):
    def __init__(
        self,
        controller: GameControllerController,
        model: GameControllerModel,
    ):
        super(QWidget, self).__init__()
        self.model = model
        self.controller = controller
        self.scroll = QScrollArea()  # Scroll Area which contains the widgets, set as the centralWidget
        self.widget = QWidget()  # Widget that contains the collection of Vertical Box
        self.box = QHBoxLayout()  # The H Box that contains the V Boxes of  labels and buttons
        self.main_layout = QHBoxLayout()
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: rgb(43, 43, 43)")
        self.chapersState = []
        self.rows = 3
        self.initUI()
        self.initconnectors()

    def initconnectors(self):
        self.model.engine.levelChanged.connect(self.levelChanged)
        self.model.engine.addLog.connect(self.logArrived)

    def levelChanged(self, new_level):
        for i, levelState in enumerate(self.chapersState):
            if i < new_level:
                levelState.SetState(PlayState.Played)
            elif i == new_level:
                levelState.SetState(PlayState.Playing)
            else:
                levelState.SetState(PlayState.ToBePlayed)

    def logArrived(self, log: str):
        self.chapersState[self.model.engine.currentLevel].addLog(log)

    def build_add_btn(self):
        button = QPushButton(self)
        button.setFixedSize(26, 26)
        button.setText("+")
        button.setStyleSheet("background-color: (225,225,225); border-radius: 13px;text-align: center")
        return button

    def resetCurrentDungeon(self):
        for levelState in self.chapersState:
            levelState.reset()

    def initUI(self):
        self.setLayout(self.main_layout)
        self.chapersState = []
        level_names = self.model.getLevelsNames()
        v_layouts = []
        line_elements = math.ceil(len(level_names) / self.rows)
        for i in range(line_elements):
            lay = QVBoxLayout()
            lay.setAlignment(Qt.AlignTop)
            v_layouts.append(lay)
            self.box.addLayout(lay)
        for i, v in level_names.items():
            level_obj = QLevelState(self.model, self.controller, i, v)
            level_obj.setFixedSize(100, 180)
            if i == self.model.engine.currentLevel:
                level_obj.SetState(PlayState.Playing)
            self.chapersState.append(level_obj)
            v_layouts[i % line_elements].addWidget(level_obj)
            # self.box.addWidget(level_obj)
        # self.insertMockupData()
        self.widget.setLayout(self.box)

        # Scroll Area Properties
        # self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.widget)
        self.scroll.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.scroll)
