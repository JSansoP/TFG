from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QDialog, QPushButton, QFileDialog, QMenu
#import flags
from PyQt5 import QtCore
import gui_utils.gutils as gutils
from gui_utils.project import Project
from gui_utils.gui_elements import MessagePopup, InputPopup
import transcribe_cut_long_audio
import os

SART_SCREEN = 0
RECORDING_SCREEN = 1


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('gui_utils/mainwindow.ui', self)
        self.setFixedSize(1000, 600)
        self.start_frame = Start(self)
        #set start frame centered on parent
        self.stackedWidget.addWidget(self.start_frame)
        self.start_frame.new_project.clicked.connect(self.create_new_project)
        self.start_frame.open_project.clicked.connect(self.open_project)
        self.start_frame.project_from_audio.clicked.connect(self.create_project_from_audio_folder)
        self.recording_frame = Recording(self)
        self.stackedWidget.addWidget(self.recording_frame)
        self.bar_open_project.triggered.connect(self.open_project)
        self.bar_new_project.triggered.connect(self.create_new_project)
        self.bar_exit.triggered.connect(lambda: self.close())
        self.bar_project_from_audio.triggered.connect(self.create_project_from_audio_folder)

    def show_start(self):
        self.stackedWidget.setCurrentIndex(SART_SCREEN)
    
    def show_recording(self):
        self.stackedWidget.setCurrentIndex(RECORDING_SCREEN)
        self.recording_frame.project_name.setText(f'Project: {self.current_project.project_name}')


    def open_project(self):
        #Open file dialog, file extension must be .json
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        project_file = QFileDialog.getOpenFileName(self, "Open Project", "projects", "Project Files (*.json)", options=options)[0]
        if project_file:
            print("Opening project: " + project_file)
            self.current_project = gutils.load_project(project_file)
            self.show_recording()

    def create_new_project(self):
        self.w = InputPopup(self)
        self.w.showPopup()
        if not self.w.cancelled:
            if not gutils.check_project_name(self.w.text):
                MessagePopup(self).showPopup("Project name cannot be empty, or contain spaces or special characters")
            elif gutils.project_exists(self.w.text):
                MessagePopup(self).showPopup("Project already exists")
            else:
                print("Created project: " + self.w.text)
                self.current_project = gutils.create_project(self.w.text)
                self.show_recording()
    
    def create_project_from_audio_folder(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        options |= QFileDialog.ShowDirsOnly
        audio_folder = QFileDialog.getExistingDirectory(self, "Select folder containing audios", options=options)
        if audio_folder:
            transcribe_cut_long_audio.main(audio_folder, "run", "es")



class Start(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi('gui_utils/start.ui', self)


class Recording(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi('gui_utils/recording.ui', self)

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()