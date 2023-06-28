import os
import wave
from threading import Thread

import pyaudio
# import flags
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QFileDialog, QLabel

import gui_utils.gutils as gutils
import transcribe_cut_long_audio
from gui_utils.gui_elements import MessagePopup, InputPopup, ExitPopup

START_SCREEN = 0
RECORDING_SCREEN = 1

RECORD_CHUNK = 1024
SAMPLE_FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 22050

record_thread = None
recording = False
playing = False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('gui_utils/mainwindow.ui', self)
        self.setFixedSize(1000, 600)
        self.start_frame = Start(self)
        # set start frame centered on parent
        self.stackedWidget.addWidget(self.start_frame)

        self.recording_frame = Recording(self)
        self.stackedWidget.addWidget(self.recording_frame)
        self.add_triggers()
        self.recording_frame.play_recording.setEnabled(False)
        self.recording_frame.delete_recording.setEnabled(False)
        self.recording_frame.new_sentence.setEnabled(False)
        self.show_start()
        self.current_sentence = ""
        self.current_project = None
        self.recording_frame.text_area.setFont(QFont("Tahoma", 28))
        self.recording_frame.text_area.setReadOnly(True)
        self.current_sentence_saved = False

    def closeEvent(self, event):
        if self.current_project:
            popup = ExitPopup(self)
            popup.show_popup()
            if popup.cancelled:
                event.ignore()
                return
        gutils.remove_temp_folder()
        super(MainWindow, self).closeEvent(event)

    def add_triggers(self):
        self.bar_open_project.triggered.connect(self.open_project)
        self.bar_new_project.triggered.connect(self.create_new_project)
        self.bar_exit.triggered.connect(lambda: self.close())
        self.bar_project_from_audio.triggered.connect(self.create_project_from_audio_folder)
        self.bar_save_project.triggered.connect(self.save_project)
        self.bar_save_project.setEnabled(False)

        self.start_frame.new_project.clicked.connect(self.create_new_project)
        self.start_frame.open_project.clicked.connect(self.open_project)
        self.start_frame.project_from_audio.clicked.connect(self.create_project_from_audio_folder)

        self.recording_frame.record_stop.clicked.connect(self.start_stop_recording)
        self.recording_frame.play_recording.clicked.connect(self.play_recording)
        self.recording_frame.delete_recording.clicked.connect(self.delete_recording)
        self.recording_frame.new_sentence.clicked.connect(self.new_sentence)

    def show_start(self):
        self.stackedWidget.setCurrentIndex(START_SCREEN)

    def show_recording(self):
        self.stackedWidget.setCurrentIndex(RECORDING_SCREEN)
        self.recording_frame.project_name.setText(f'Project: {self.current_project.project_name}')
        layout = self.recording_frame.scrollContents.layout()
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)
        for audio in self.current_project.audios:
            lab = QLabelClickable()
            number = os.path.basename(audio.path).split('.')[0]
            lab.clicked.connect(self.label_clicked)
            lab.setText(f"{number}.wav")
            lab.setVisible(True)
            layout.insertWidget(layout.count() - 1, lab)
            layout.addStretch()
        self.current_sentence = gutils.get_first_sentence()
        self.recording_frame.text_area.setText(self.current_sentence)

    def save_project(self):
        if gutils.tempfile_exists():
            self.new_sentence()
        gutils.save_project(self.current_project)

    def open_project(self):
        # Open file dialog, file extension must be .json
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        project_file = \
            QFileDialog.getOpenFileName(self, "Open Project", "projects", "Project Files (*.json)", options=options)[0]
        if project_file:
            print("Opening project: " + project_file)
            self.current_project = gutils.open_project(project_file)
            print(self.current_project.audios)
            self.show_recording()
            gutils.create_temp_folder()

    def create_new_project(self):
        self.w = InputPopup(self)
        self.w.show_popup()
        if not self.w.cancelled:
            if not gutils.check_project_name(self.w.text):
                MessagePopup(self).showPopup("Project name cannot be empty, or contain spaces or special characters")
            elif gutils.project_exists(self.w.text):
                MessagePopup(self).showPopup("Project already exists")
            else:
                print("Created project: " + self.w.text)
                self.current_project = gutils.create_project(self.w.text)
                print(self.current_project.to_json())
                self.current_sentence = gutils.get_first_sentence()
                self.recording_frame.text_area.setText(self.current_sentence)
                self.show_recording()

    def create_project_from_audio_folder(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        options |= QFileDialog.ShowDirsOnly
        audio_folder = QFileDialog.getExistingDirectory(self, "Select folder containing audios", options=options)
        if audio_folder:
            transcribe_cut_long_audio.main(audio_folder, "run", "es")

    def start_stop_recording(self):
        global recording, record_thread
        if not recording:
            recording = True
            tempfile = os.path.join("projects", "TEMP", "tempfile.wav")
            record_thread = Thread(target=record_audio, args=(tempfile,))
            record_thread.start()
            self.recording_frame.record_stop.setText("Stop")
        else:
            recording = False
            record_thread.join()
            record_thread = None
            self.recording_frame.record_stop.setText("Record")
            self.recording_frame.play_recording.setEnabled(True)
            self.recording_frame.delete_recording.setEnabled(True)
            self.recording_frame.new_sentence.setEnabled(True)
            self.recording_frame.record_stop.setEnabled(False)

    def play_recording(self):
        if not playing:
            play_thread = Thread(target=play_audio, args=(os.path.join("projects", "TEMP", "tempfile.wav"),))
            play_thread.start()

    def delete_recording(self):
        os.remove(os.path.join("projects", "TEMP", "tempfile.wav"))
        self.recording_frame.play_recording.setEnabled(False)
        self.recording_frame.delete_recording.setEnabled(False)
        self.recording_frame.new_sentence.setEnabled(False)
        self.recording_frame.record_stop.setEnabled(True)

    def label_clicked(self):
        filename = self.sender().text()
        # We gotta set the current sentence to the one that was clicked, and also
        # set the audio to the one that was clicked
        self.current_sentence = gutils.get_sentence_from_audio(self.current_project, filename)
        print(self.current_sentence)
        self.recording_frame.text_area.setText(self.current_sentence)
        self.recording_frame.play_recording.setEnabled(True)
        self.recording_frame.delete_recording.setEnabled(True)
        self.recording_frame.new_sentence.setEnabled(True)
        self.recording_frame.record_stop.setEnabled(False)
        gutils.copy_audio_to_TEMP(self.current_project, filename)
        self.current_sentence_saved = True

    def new_sentence(self):
        if not self.current_sentence_saved:
            gutils.save_current_audio(self.current_project, self.current_sentence)
        layout = self.recording_frame.scrollContents.layout()
        lab = QLabelClickable()
        lab.clicked.connect(self.label_clicked)
        lab.setText(f"{self.current_project.index - 1}.wav")
        lab.setVisible(True)
        layout.insertWidget(layout.count() - 1, lab)
        layout.addStretch()
        self.current_sentence = gutils.get_new_sentence()
        self.recording_frame.text_area.setText(self.current_sentence)
        self.recording_frame.play_recording.setEnabled(False)
        self.recording_frame.delete_recording.setEnabled(False)
        self.recording_frame.new_sentence.setEnabled(False)
        self.recording_frame.record_stop.setEnabled(True)
        self.recording_frame.record_stop.setText("Record")
        print(self.current_project.to_json())
        self.bar_save_project.setEnabled(True)


class Start(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi('gui_utils/start.ui', self)


class Recording(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi('gui_utils/recording.ui', self)


class QLabelClickable(QLabel):
    clicked: pyqtSignal = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


def play_audio(filename):
    global playing
    playing = True
    wf = wave.open(filename, 'rb')
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()), channels=wf.getnchannels(),
                    rate=wf.getframerate(), output=True)
    data = wf.readframes(RECORD_CHUNK)
    while data:
        stream.write(data)
        data = wf.readframes(RECORD_CHUNK)
    stream.stop_stream()
    stream.close()
    p.terminate()
    playing = False


def record_audio(filename):
    p = pyaudio.PyAudio()
    stream = p.open(format=SAMPLE_FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=RECORD_CHUNK)
    frames = []
    while recording:
        data = stream.read(RECORD_CHUNK)
        frames.append(data)
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(SAMPLE_FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()


if __name__ == '__main__':
    gutils.remove_temp_folder()
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
