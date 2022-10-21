from PySide2 import QtCore, QtWidgets, QtGui
import sys, os

class Example(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        if '__file__' in globals():
            self.Path = os.path.dirname(os.path.realpath(__file__))
        else:
            self.Path = os.getcwd()
        self.ImagePath = os.path.join(self.Path, "images")


        hbox = QtWidgets.QHBoxLayout(self)
        pixmap = QtGui.QPixmap(os.path.join(self.ImagePath, "Valve_green_V.png"))

        lbl = QtWidgets.QLabel(self)
        lbl.setPixmap(pixmap)

        hbox.addWidget(lbl)
        self.setLayout(hbox)

        self.move(300, 200)
        self.setWindowTitle('Image with PyQt')
        self.setStyleSheet("QWidget { background: red; }")
        self.show()

if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())