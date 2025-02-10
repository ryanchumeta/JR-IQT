from PyQt5 import QtCore, QtGui, QtWidgets
import sys
from CallStageUI import CallStageUI



if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = CallStageUI()
    ui.setupUi(MainWindow)
    ui.setUpBtnconnect()
    MainWindow.show()
    sys.exit(app.exec_())
