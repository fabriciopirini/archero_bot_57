from PyQt5 import QtWidgets
from GameController.GameControllerView import GameControllerWindow
from GameController.GameControllerModel import GameControllerModel
from GameController.GameControllerController import GameControllerController

if __name__ == "__main__":
    import sys
    import logging

    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=logging.INFO,
        datefmt="%H:%M:%S",
    )

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    MainWindow.setWindowTitle("Game Controller")
    model = GameControllerModel()
    controller = GameControllerController(model)
    ui = GameControllerWindow(model, controller)
    ui.setupUi(MainWindow)
    model.load_data()
    MainWindow.show()
    result = app.exec_()
    model.requestClose()
    sys.exit(result)
