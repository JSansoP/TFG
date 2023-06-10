
from PyQt5.QtWidgets import *


class Popup(QDialog):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setGeometry(50, 50, 400, 200)
        self.exit = QPushButton("Ok")
        self.setFixedSize(400, 200)
        # set position on screen centered on parent
        self.move(self.parent().property("pos").x() + self.parent().property("width") / 2 - self.property("width") / 2, self.parent().property("pos").y() + self.parent().property("height") / 2 - self.property("height") / 2)


class ExitPopup(Popup):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Close program?")
        self.setModal(True)
        self.label = QLabel("Are you sure you want to exit? All unsaved changes will be lost.", self)
        self.cancel = QPushButton("Cancel", self)
        self.exit = QPushButton("Exit", self)
        self._cancelled = True
        self.cancel.clicked.connect(self.cancel_pressed)
        self.cancel.setDefault(True)
        self.exit.setDefault(False)
        self.exit.clicked.connect(self.okay_pressed)
        # set position of label, textbox and buttons
        self.label.setGeometry(50, 20, 280, 40)
        self.cancel.setGeometry(50, 120, 80, 40)
        self.exit.setGeometry(250, 120, 80, 40)

    def cancel_pressed(self):
        self._cancelled = True
        self.close()

    def okay_pressed(self):
        self._cancelled = False
        self.close()

    @property
    def cancelled(self):
        return self._cancelled

    def show_popup(self):
        self.exec_()

class InputPopup(Popup):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Create new project")
        self.setModal(True)
        self.label = QLabel("Enter project name:", self)
        self.textbox = QLineEdit(self)
        self.cancel = QPushButton("Cancel", self)
        self.ok = QPushButton("Ok", self)
        self._cancelled = True
        self.cancel.clicked.connect(self.close)
        self.cancel.setDefault(False)
        self.ok.setDefault(True)
        self.ok.clicked.connect(self.okay_pressed)
        # set position of label, textbox and buttons
        self.label.setGeometry(50, 20, 280, 40)
        self.textbox.setGeometry(50, 60, 280, 40)
        self.cancel.setGeometry(50, 120, 80, 40)
        self.ok.setGeometry(250, 120, 80, 40)
        self.setWindowTitle("New project")
        self.textbox.returnPressed.connect(self.okay_pressed)

    @property
    def text(self):
        return self.textbox.text()

    @property
    def cancelled(self):
        return self._cancelled

    def okay_pressed(self):
        self._cancelled = False
        self.close()

    def show_popup(self):
        self.exec_()


class MessagePopup(Popup):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Info")
        self.setModal(True)
        self.setFixedSize(400, 150)
        self.label = QLabel("", self)
        self.ok = QPushButton("Ok", self)
        self.ok.clicked.connect(self.close)
        self.label.setGeometry(50, 20, 350, 40)
        self.label.show()
        # Window size is set to 400, 150, set the button centered
        self.ok.setGeometry(int(400/2) - int(80 / 2), 100, 80, 40)
        self.ok.show()

    def showPopup(self, text):
        self.label.setText(text)
        self.exec_()
