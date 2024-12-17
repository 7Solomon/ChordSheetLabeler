import random
import sys
import cv2
import numpy as np
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QFileDialog, QLabel, QListWidget, QFrame, QSplitter, QStackedWidget,
                             QTextEdit, QLineEdit, QMessageBox, QScrollArea)
from PyQt5.QtGui import QPixmap, QImage, QColor, QPainter, QBrush, QPen
from PyQt5.QtCore import Qt, QThreadPool
import easyocr
from paddleocr import PaddleOCR
from pdf2image import convert_from_path

# Import your custom widget classes
from src.widgets import OCRWorker, SectionNameDialog, KeyOfSongWidget, ImageLabel, SelectImagePage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OCR Music Sheet Reader")
        self.setGeometry(100, 100, 1200, 800)
        #self.reader = easyocr.Reader(['de', 'en'])
        self.reader =  PaddleOCR(use_angle_cls=True, lang='en')
        
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        # Page 1: Select Image
        self.select_image_page = SelectImagePage()
        self.select_image_page.image_selected.connect(self.on_image_selected)
        self.central_widget.addWidget(self.select_image_page)

        # Page 2: Main Interface
        self.main_page = QWidget()
        self.main_layout = QHBoxLayout(self.main_page)
        self.central_widget.addWidget(self.main_page)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.image_label = ImageLabel(self)
        self.image_label.section_selected.connect(self.on_section_selected)
        self.scroll_area.setWidget(self.image_label)
        self.main_layout.addWidget(self.scroll_area)

        self.key_of_song = None
        self.song_name = None

        # Right panel
        self.right_panel = QWidget()
        self.right_panel.setMinimumWidth(400)
        self.right_panel_layout = QVBoxLayout(self.right_panel)
        self.main_layout.addWidget(self.right_panel)

        # Song Name Widget
        self.song_name_widget = QWidget()
        self.song_name_layout = QHBoxLayout(self.song_name_widget)
        self.song_name_input = QLineEdit()
        self.song_name_input.installEventFilter(self)

        self.song_name_layout.addWidget(QLabel("Song Name:"))
        self.song_name_layout.addWidget(self.song_name_input)

        self.right_panel_layout.addWidget(self.song_name_widget)

        # Key of Song Widget
        self.key_of_song_widget = KeyOfSongWidget(self)
        self.key_of_song_widget.keyEntered.connect(self.key_of_song_entered)
        self.right_panel_layout.addWidget(self.key_of_song_widget)

        # Key display
        self.current_key_label = QLabel("Current Key: None")
        self.right_panel_layout.addWidget(self.current_key_label)

        # Sections List
        self.sections_list = QListWidget()
        self.right_panel_layout.addWidget(self.sections_list)
        self.sections_list.itemClicked.connect(self.on_item_clicked)

        # Export Button
        self.export_button = QPushButton("Export to JSON")
        self.export_button.clicked.connect(self.export_to_json)
        self.right_panel_layout.addWidget(self.export_button)

        # Section Data Overview
        self.section_data_overview = QTextEdit()
        self.section_data_overview.setReadOnly(False)
        self.right_panel_layout.addWidget(self.section_data_overview)

        self.image = None
        self.sections = []
        self.section_colors = {}
        self.thread_pool = QThreadPool()
        self.ocr_threads = []

    def set_song_name(self):
        self.song_name = self.song_name_input.text()

    def on_image_selected(self, image):
        self.image = image
        height, width, channel = self.image.shape
        bytes_per_line = 3 * width
        q_image = QImage(self.image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        self.image_label.setPixmap(pixmap)
        self.image_label.setFixedSize(width, height)
        self.central_widget.setCurrentWidget(self.main_page)

    def key_of_song_entered(self, key_of_song):
        self.key_of_song = key_of_song
        self.current_key_label.setText(f"Current Key: {self.key_of_song}")

    def on_section_selected(self, rect):
        if self.key_of_song:
            dialog = SectionNameDialog(self)
            if dialog.exec_():
                section_name = dialog.get_name()
                if section_name:
                    self.save_section(section_name, rect)
        else:
            QMessageBox.warning(self, "Warning", "Du hast noch keine Tonart festgelegt. Bitte wähle eine Tonart aus du kek.")
                
    def save_section(self, name, rect):
        x, y, w, h = rect.getRect()
        self.sections.append({"name": name, "rect": (x, y, w, h), "ocr_data": None})

        color = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 100)
        self.section_colors[name] = color

        self.repaint_image_with_sections()

        self.sections_list.addItem(name)

        worker = OCRWorker(self.image, (x, y, w, h), self.reader, self.key_of_song, name)
        worker.finished.connect(self.update_ocr_result)
        self.ocr_threads.append(worker)
        worker.start()

    def repaint_image_with_sections(self):
        height, width, channel = self.image.shape
        img_copy = self.image.copy()

        bytes_per_line = 3 * width
        q_image = QImage(img_copy.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)

        painter = QPainter(pixmap)

        for section in self.sections:
            name = section["name"]
            x, y, w, h = section["rect"]
            color = self.section_colors[name]
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.NoPen))
            painter.drawRect(x, y, w, h)

        painter.end()
        self.image_label.setPixmap(pixmap)

    def update_ocr_result(self, region, data):
        name_of_part, ocr_data = data
        for section in self.sections:
            if str(section["rect"]) == region:
                section["ocr_data"] = ocr_data
                break
        self.update_section_data_overview()

    def on_item_clicked(self, item):
        item_text = item.text()
        section_data = next((section for section in self.sections if section["name"] == item_text), None)
        if section_data and section_data["ocr_data"]:
            self.section_data_overview.setText(f"Details for {item_text}:\n{json.dumps(section_data['ocr_data'], indent=2)}")
        else:
            self.section_data_overview.setText(f"Details for {item_text}: No OCR data available.")

    def update_section_data_overview(self):
        overview = ""
        for section in self.sections:
            overview += f"Section: {section['name']}\n"
            if section['ocr_data']:
                overview += json.dumps(section['ocr_data'], indent=2) + "\n"
            else:
                overview += "  No OCR data available\n"
            overview += "\n"
        self.section_data_overview.setText(overview)

    def export_to_json(self):
        data = {
            "header": {
                "name": self.song_name or "Untitled",
                "key": self.key_of_song or "Unknown",
                "authors": []
            },
            "data": {}
        }
        for section in self.sections:
            data["data"][section["name"]] = section["ocr_data"]

        file_path, _ = QFileDialog.getSaveFileName(self, "Save JSON", "", "JSON Files (*.json)")
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)

    def eventFilter(self, source, event):
        if (event.type() == event.KeyPress and 
            source is self.song_name_input and 
            event.key() == Qt.Key_Return):
            self.set_song_name()
            return True  # Indicate that the event has been handled
        return super().eventFilter(source, event)
    def closeEvent(self, event):
        for thread in self.ocr_threads:
            thread.wait()
        super().closeEvent(event)