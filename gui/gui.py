from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QDialog, QPushButton
#import flags
from PyQt5 import QtCore
import utils
from gui_elements import MessagePopup, InputPopup

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('gui/mainwindow.ui', self)
        self.setFixedSize(1000, 600)
        self.start_frame = Start(self)
        #set start frame centered on parent
        self.stackedWidget.addWidget(self.start_frame)
        self.start_frame.new_project.clicked.connect(self.create_new_project)
        self.recording_frame = Recording(self)
        self.stackedWidget.addWidget(self.recording_frame)
        self.recording_frame.record_stop.clicked.connect(self.go_to_first)

    def go_to_first(self):
        self.stackedWidget.setCurrentIndex(0)

    def create_new_project(self):
        self.w = InputPopup(self)
        self.w.showPopup()
        if not self.w.cancelled:
            if self.w.text == "":
                MessagePopup(self).showPopup("Project name cannot be empty")
            elif utils.project_exists(self.w.text):
                MessagePopup(self).showPopup("Project already exists")
            else:
                utils.create_project(self.w.text)
                self.current_project = self.w.text
                self.stackedWidget.setCurrentIndex(1)



class Start(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi('gui/start.ui', self)


class Recording(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi('gui/recording.ui', self)

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()