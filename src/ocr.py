
from PyQt5.QtCore import QThread, pyqtSignal
import cv2
import numpy as np

from src.analyze_process import process_ocr_result


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

        result = self.readeer.ocr(roi)
        final_json = process_ocr_result(result, self.key, self.name_of_part)
        
        self.finished.emit(str(self.region), tuple(final_json))
