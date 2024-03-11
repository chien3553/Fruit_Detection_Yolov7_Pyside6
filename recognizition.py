import glob
import os
import shutil
import sys
import cv2
import numpy as np
import keyboard
from PySide6.QtGui import QPixmap, QImage, QMouseEvent, QGuiApplication
from PySide6.QtWidgets import QMessageBox, QFileDialog, QMainWindow, QWidget, QApplication
from PySide6.QtUiTools import QUiLoader, loadUiType
from PySide6.QtCore import QFile, QTimer, Qt, QEventLoop, QThread
from PySide6 import QtCore, QtGui

from PIL import Image
from lib import glo
from YoloClass import YoloThread

GLOBAL_STATE = True

formType, baseType = loadUiType("./ui/main.ui")


class YOLO(formType, baseType):
    def __init__(self):
        super().__init__()
        # Load UI
        self.setupUi(self)
        self.setWindowFlags(Qt.CustomizeWindowHint)

        self.inputPath = ""
        self.path_files = []
        self.i = 0
        keyboard.on_press(self.handle_key_press)

        # Slider
        self.con_slider.valueChanged.connect(self.ValueChangeSlider)
        self.con_num.valueChanged.connect(self.ValueChangeSpin)
        self.iou_slider.valueChanged.connect(self.ValueChangeSlider)
        self.iou_num.valueChanged.connect(self.ValueChangeSpin)

        # TOOLS
        self.file.clicked.connect(self.Selectfile)
        self.folder.clicked.connect(self.SelectFolder)
        self.importbtn.clicked.connect(self.Import)
        self.exporter.clicked.connect(self.Export)
        self.webcam.clicked.connect(self.Webcam)

        # Maximize, Minimize, Close button
        MaxIcon = QtGui.QIcon()
        MaxIcon.addPixmap(QtGui.QPixmap("./img/icons/square.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MaxIcon.addPixmap(QtGui.QPixmap("./img/icons/reduce.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        MaxIcon.addPixmap(QtGui.QPixmap("./img/icons/reduce.png"), QtGui.QIcon.Selected, QtGui.QIcon.On)
        self.MaxButton.setCheckable(True)
        self.MaxButton.setIcon(MaxIcon)
        self.MaxButton.clicked.connect(self.max_or_restore)
        self.MinButton.clicked.connect(self.showMinimized)
        self.CloseButton.clicked.connect(self.close)
        # Preview
        self.input.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.output.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)

        # Play/Pause button
        PlayIcon = QtGui.QIcon()
        PlayIcon.addPixmap(QtGui.QPixmap("./img/icons/play-button.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        PlayIcon.addPixmap(QtGui.QPixmap("./img/icons/pause.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        PlayIcon.addPixmap(QtGui.QPixmap("./img/icons/play-button.png"), QtGui.QIcon.Disabled, QtGui.QIcon.Off)
        PlayIcon.addPixmap(QtGui.QPixmap("./img/icons/pause.png"), QtGui.QIcon.Disabled, QtGui.QIcon.On)
        PlayIcon.addPixmap(QtGui.QPixmap("./img/icons/play-button.png"), QtGui.QIcon.Active, QtGui.QIcon.Off)
        PlayIcon.addPixmap(QtGui.QPixmap("./img/icons/pause.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        PlayIcon.addPixmap(QtGui.QPixmap("./img/icons/play-button.png"), QtGui.QIcon.Selected, QtGui.QIcon.Off)
        PlayIcon.addPixmap(QtGui.QPixmap("./img/icons/pause.png"), QtGui.QIcon.Selected, QtGui.QIcon.On)
        self.playbtn.setCheckable(True)
        self.playbtn.setIcon(PlayIcon)

        # Load .pt default
        self.comboBox.clear()
        self.pt_Path = "./ptmodel"
        self.pt_list = os.listdir('./ptmodel')
        self.pt_list = [file for file in self.pt_list if file.endswith('.pt')]
        self.pt_list.sort(key=lambda x: os.path.getsize('./ptmodel/' + x))
        self.comboBox.clear()
        self.comboBox.addItems(self.pt_list)
        self.qtimer_search = QTimer(self)
        self.qtimer_search.timeout.connect(lambda: self.search_pt())
        self.qtimer_search.start(2000)
        self.comboBox.currentTextChanged.connect(self.change_model)

        # yolov7 thread
        self.yolo_thread = YoloThread()
        # Load .pt
        self.model_type = self.comboBox.currentText()
        self.yolo_thread.weights = "./ptmodel/%s" % self.model_type

        self.yolo_thread.percent_length = self.progressBar.maximum()
        self.yolo_thread.send_input.connect(lambda x: self.showimg(x, self.input, 'img'))
        self.yolo_thread.send_output.connect(lambda x: self.showimg(x, self.output, 'img'))
        self.yolo_thread.send_result.connect(self.show_result)
        self.yolo_thread.send_msg.connect(lambda x: self.foot_print(x))
        self.yolo_thread.send_percent.connect(lambda x: self.progressBar.setValue(x))
        self.yolo_thread.send_fps.connect(lambda x: self.fps_label.setText(x))

        # Play/Stop
        self.playbtn.clicked.connect(self.run_or_continue)
        self.stopbtn.clicked.connect(self.stop)



    # Search .pt
    def search_pt(self):
        pt_list = os.listdir('./ptmodel')
        pt_list = [file for file in pt_list if file.endswith('.pt')]
        pt_list.sort(key=lambda x: os.path.getsize('./ptmodel/' + x))

        if pt_list != self.pt_list:
            self.pt_list = pt_list
            self.comboBox.clear()
            self.comboBox.addItems(self.pt_list)

    # Conf and IoU changes
    def ValueChangeSlider(self):
        self.numcon = self.con_slider.value() / 100.0
        self.numiou = self.iou_slider.value() / 100.0
        self.con_num.setValue(self.numcon)
        self.yolo_thread.conf = self.numcon
        self.iou_num.setValue(self.numiou)
        self.yolo_thread.iou = self.numiou

    def ValueChangeSpin(self):
        self.numcon = self.con_num.value()
        self.numiou = self.iou_num.value()
        self.con_slider.setValue(self.numcon * 100)
        self.yolo_thread.conf = self.numcon
        self.iou_slider.setValue(self.numiou * 100)
        self.yolo_thread.iou = self.numiou

    # Model changes
    def change_model(self, x):
        self.model_type = self.comboBox.currentText()
        self.yolo_thread.weights = "./ptmodel/%s" % self.model_type

    # Show
    @staticmethod
    def showimg(img, label, flag):
        try:
            if flag == "path":
                img_src = cv2.imdecode(np.fromfile(img, dtype=np.uint8), -1)
            else:
                img_src = img
            ih, iw, _ = img_src.shape
            w = label.geometry().width()
            h = label.geometry().height()
            # keep original aspect ratio
            if iw / w > ih / h:
                scal = w / iw
                nw = w
                nh = int(scal * ih)
                img_src_ = cv2.resize(img_src, (nw, nh))
            else:
                scal = h / ih
                nw = int(scal * iw)
                nh = h
                img_src_ = cv2.resize(img_src, (nw, nh))

            frame = cv2.cvtColor(img_src_, cv2.COLOR_BGR2RGB)
            img = QImage(frame.data, frame.shape[1], frame.shape[0], frame.shape[2] * frame.shape[1],
                         QImage.Format_RGB888)
            label.setPixmap(QPixmap.fromImage(img))

        except Exception as e:
            print(repr(e))

    # Select image/video
    def Selectfile(self):
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "./",
            "(*.jpg *.jpeg *.png *.bmp *.dib  *.jpe  *.jp2 *.mp4)"
        )
        if file == "":
            pass
        else:
            self.inputPath = file
            print(self.inputPath)
            glo.set_value('inputPath', self.inputPath)
            if ".avi" in self.inputPath or ".mp4" in self.inputPath:
                # Show first frame
                self.cap = cv2.VideoCapture(self.inputPath)
                ret, frame = self.cap.read()
                if ret:
                    rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    self.showimg(rgbImage, self.input, 'img')
            else:
                self.showimg(self.inputPath, self.input, 'path')
            self.foot_print("Ready")

    def SelectFolder(self):
        options = QFileDialog.Options()
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder", options=options)
        if folder_path == '':
            pass
        else:
            self.i = 0
            self.path_files = glob.glob(folder_path + '\\*')
            self.inputPath = self.path_files[self.i].replace('\\', '/')
            glo.set_value('inputPath', self.inputPath)
            # print(self.inputPath)
            self.showimg(self.inputPath, self.input, 'path')
        self.foot_print("Ready")

    def handle_key_press(self, event):
        if self.i < len(self.path_files) - 1:  # Đảm bảo không vượt quá chỉ số cuối cùng của mảng
            if event.name == 'd':  # Kiểm tra xem phím được nhấn có phải là phím D hay không
                self.i += 1
            elif event.name == 'a':
                self.i -= 1
            self.inputPath = self.path_files[self.i]
            glo.set_value('inputPath', self.inputPath)
            # print(self.i)
            self.showimg(self.inputPath, self.input, 'path')
        self.foot_print("Ready")


    # Import model
    def Import(self):
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Select Model",
            "./",
            "(*.pt)"
        )
        if file == "":
            pass
        else:
            shutil.copy(file, self.pt_Path)
            QMessageBox.information(self, 'Tips', 'Import model succeeded!')

    # Export image/video(webcam)
    def Export(self):
        self.OutputDir, _ = QFileDialog.getSaveFileName(
            self,
            "Export",
            r".",
            "(*.jpg *.jpeg *.png *.bmp *.dib  *.jpe  *.jp2 *.mp4)"
        )
        if self.output == "":
            QMessageBox.warning(self, 'Tips', 'Please select the location to save the image/video first')
        else:
            try:
                shutil.copy(self.yolo_thread.save_path, self.OutputDir)
                QMessageBox.warning(self, 'Tips', 'Export succeeded!')
            except Exception as e:
                QMessageBox.warning(self, 'Tips', 'Please detect first')
                print(e)

    # maximize minimize window
    def max_or_restore(self):
        global GLOBAL_STATE
        status = GLOBAL_STATE
        if status:
            self.showMaximized()
            GLOBAL_STATE = False
        else:
            self.showNormal()
            GLOBAL_STATE = True

    # Play/Pause
    def run_or_continue(self):
        if self.inputPath == "":
            QMessageBox.warning(self, "Tips", "No image or video")
            self.playbtn.setChecked(False)
        else:
            self.yolo_thread.jump_out = False
            if self.playbtn.isChecked():
                self.yolo_thread.is_continue = True
                # print(self.yolo_thread.isRunning())
                if not self.yolo_thread.isRunning():
                    self.yolo_thread.start()
                    self.foot_print("Detecting>>>>>" + self.inputPath)
            else:
                self.yolo_thread.is_continue = False
                self.foot_print('Pause')

    # Webcam
    def Webcam(self):
        self.inputPath = '0'
        glo.set_value('inputPath', self.inputPath)
        self.yolo_thread.jump_out = False
        self.yolo_thread.is_continue = True
        if not self.yolo_thread.isRunning():
            self.yolo_thread.start()
            self.foot_print("Detecting")
            self.playbtn.setChecked(True)

    # Stop
    def stop(self):
        self.yolo_thread.jump_out = True
        self.foot_print('Stop')
        # print(self.yolo_thread.isRunning())

    # Show statistics
    def show_result(self, statistic_dic):
        try:
            self.resultlist.clear()
            statistic_dic = sorted(statistic_dic.items(), key=lambda x: x[1], reverse=True)
            statistic_dic = [i for i in statistic_dic if i[1] > 0]
            results = [' ' + str(i[0]) + '：' + str(i[1]) for i in statistic_dic]
            self.resultlist.addItems(results)

        except Exception as e:
            print(repr(e))

    # foot print
    def foot_print(self, msg):
        if msg in ['Stop', 'Finished'] or msg.startswith("Error!"):
            self.playbtn.setChecked(False)
        self.outputbox.setText(msg)


class MyWindow(YOLO):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.center()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.mouse_start_pt = event.globalPosition().toPoint()
            self.window_pos = self.frameGeometry().topLeft()
            self.drag = True

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.drag:
            distance = event.globalPosition().toPoint() - self.mouse_start_pt
            self.move(self.window_pos + distance)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.drag = False

    def center(self):
        screen = QGuiApplication.primaryScreen().size()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2 - 10)
