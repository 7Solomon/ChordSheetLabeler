from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QLabel, QLineEdit, QListWidget, QDialog, QDialogButtonBox
from PyQt5.QtGui import QPixmap, QPainter, QPen, QImage, QPalette, QColor
from PyQt5.QtCore import Qt, QRect, QThread, pyqtSignal, QThreadPool
import cv2
import numpy as np
from pdf2image import convert_from_path

from analyze_process import process_ocr_result

class OCRWorker(QThread):
    finished = pyqtSignal(str, tuple)

    def __init__(self, image, region, reader, key, name_of_part):
        super().__init__()
        self.image = image
        self.region = region
        
        self.reader = reader
        self.key = key
        self.name_of_part = name_of_part

    def run(self):
        x, y, w, h = self.region
        roi = self.image[y:y+h, x:x+w]
        
        result = self.reader.readtext(roi)
        final_json = process_ocr_result(result, self.key, self.name_of_part)
        
        self.finished.emit(str(self.region), tuple(final_json))

class SectionNameDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter Section Name")
        self.layout = QVBoxLayout(self)
        self.name_input = QLineEdit(self)
        self.layout.addWidget(self.name_input)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_name(self):
        return self.name_input.text()


class SelectImagePage(QWidget):
    image_selected = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()

        # Set the layout
        layout = QVBoxLayout(self)

        # Create a button
        self.upload_button = QPushButton("Upload Image/PDF")
        self.upload_button.setFixedSize(600, 400)
        self.upload_button.setStyleSheet("""
            QPushButton {
                font-size: 24px;          /* Larger font size */
                background-color: #bebebe; /* grey background */
                color: white;              /* White text color */
                border: none;              /* No border */
                border-radius: 10px;      /* Rounded corners */
                padding: 20px;            /* Padding for larger click area */
            }
            QPushButton:hover {
                background-color: #45a049; /* Darker green on hover */
            }
        """)
        
        # Connect the button click event
        self.upload_button.clicked.connect(self.upload_file)

        # Add the button to the layout and set it to fill the window
        layout.addWidget(self.upload_button, alignment=Qt.AlignCenter)  # Center the button
        layout.setStretch(0, 1)  # Allow the button to stretch and fill the window

        # Set the layout for the widget
        self.setLayout(layout)

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Open Image/PDF", 
            "", 
            "PDF Files (*.pdf);;Image Files (*.png *.jpg *.bmp)"
        )
        if file_path:
            if file_path.lower().endswith('.pdf'):
                pages = convert_from_path(file_path)
                image = np.array(pages[0])
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            else:
                image = cv2.imread(file_path)
            self.image_selected.emit(image)


class KeyOfSongWidget(QLineEdit):
    # Define a custom signal to send the key of the song
    keyEntered = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.default_text = "Tonart des Songs"
        self.set_background_text(self.default_text)
        
        # Connect the returnPressed signal to emit our custom signal
        self.returnPressed.connect(self.on_enter_pressed)

    def set_background_text(self, text):
        """Set the background text with a gray color."""
        self.setText(text)
        palette = self.palette()
        palette.setColor(QPalette.Text, QColor('gray'))
        self.setPalette(palette)

    def on_enter_pressed(self):
        """Emit the key of the song when the Enter key is pressed."""
        current_text = self.text().strip()
        if current_text != self.default_text:
            self.keyEntered.emit(current_text)  # Emit the signal
            self.clear()  # Optionally clear the field after pressing Enter


class ImageLabel(QLabel):
    section_selected = pyqtSignal(QRect)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.begin = None
        self.end = None
        self.selected_rect = None
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = event.pos()
        self.selected_rect = None
        self.update()

    def mouseMoveEvent(self, event):
        if self.begin:
            self.end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        self.end = event.pos()
        self.selected_rect = QRect(self.begin, self.end).normalized()
        self.section_selected.emit(self.selected_rect)
        self.begin = None
        self.end = None
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
        
        if self.begin and self.end:
            painter.drawRect(QRect(self.begin, self.end).normalized())
        
        if self.selected_rect:
            painter.drawRect(self.selected_rect)
