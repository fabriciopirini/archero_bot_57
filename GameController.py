from PyQt5 import QtWidgets

from GameController.GameControllerController import GameControllerController
from GameController.GameControllerModel import GameControllerModel
from GameController.GameControllerView import GameControllerWindow

if __name__ == "__main__":
    import sys
    from loguru import logger

    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> [<level>{level}</level>] <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
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
