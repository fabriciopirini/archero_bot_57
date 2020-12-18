from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtCore import Qt
from TouchManager.TouchManagerController import TouchManagerController
from TouchManager.TouchManagerModel import TouchManagerModel
from TouchManager.TouchManagerController import ShowAreaState
from TouchManager.ButtonOption import ButtonOption
from TouchManager.MovementOption import MovementOption
from TouchManager.FrameCheckOption import FrameCheckOption


class ElementOption(QWidget):
    def __init__(
        self,
        controller: TouchManagerController,
        model: TouchManagerModel,
    ):
        super(QWidget, self).__init__()
        self.model = model
        self.controller = controller
        self.main_lay = QVBoxLayout()
        self.wid: QWidget = ButtonOption(self, controller, model)
        self.currentType: ShowAreaState = ShowAreaState.Buttons
        self.setupUI()
        self.initControllers()
        self.areatypeChanged(self.controller.currentAreaType)

    def reset(self):
        self.lblInfoDesc.clear()

    def setupUI(self):
        self.main_lay.setAlignment(Qt.AlignTop)
        self.main_lay.setContentsMargins(0, 0, 0, 0)
        # self.setFixedHeight(150)
        self.main_lay.addWidget(self.wid)
        self.setLayout(self.main_lay)

    def initControllers(self):
        self.controller.onCurrentShowAreaChanged.connect(self.areatypeChanged)
        self.controller.onElementSelectionChanged.connect(self.onElementChanged)

    def onElementChanged(self):
        self.wid.changeData(self.controller.currentCoordinates)

    def areatypeChanged(self, new_type: ShowAreaState):
        self.clearLayout()
        if new_type == ShowAreaState.Buttons:
            self.wid.deleteLater()
            self.wid.setParent(None)
            self.wid = ButtonOption(self.main_lay, self.controller, self.model)
            self.main_lay.insertWidget(0, self.wid)
        elif new_type == ShowAreaState.Movements:
            self.wid.deleteLater()
            self.wid.setParent(None)
            self.wid = MovementOption(self.main_lay, self.controller, self.model)
            self.main_lay.insertWidget(0, self.wid)
        elif new_type == ShowAreaState.FrameCheck:
            self.wid.deleteLater()
            self.wid.setParent(None)
            self.wid = FrameCheckOption(self.main_lay, self.controller, self.model)
            self.main_lay.insertWidget(0, self.wid)

    def clearLayout(self):
        self.wid.setParent(None)
