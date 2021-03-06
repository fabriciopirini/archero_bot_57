from PyQt5 import QtWidgets

from TouchManager.TouchManagerController import TouchManagerController
from TouchManager.TouchManagerModel import TouchManagerModel
from TouchManager.TouchManagerView import TouchManagerWindow

if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    MainWindow.setWindowTitle("Touch Manager")
    model = TouchManagerModel()
    controller = TouchManagerController(model)
    ui = TouchManagerWindow(controller, model)
    ui.setupUi(MainWindow)
    model.load_data()
    MainWindow.show()
    sys.exit(app.exec_())
