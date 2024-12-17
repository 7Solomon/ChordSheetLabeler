import sys
from PyQt5.QtWidgets import QApplication
from pdf2image import convert_from_path

from src.analyze_process import process_ocr_result
from src.GUIs.mainWindow import MainWindow


import easyocr

from paddleocr import PaddleOCR


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

def easy_ocr_test():
    reader = easyocr.Reader(['de', 'en'])
    result = reader.readtext('examples/1.png')
    final_json = process_ocr_result(result, 'G', 'test')



def paddle_ocr_test():
    # Initialize PaddleOCR
    ocr = PaddleOCR(use_angle_cls=True, lang='en')  # Set 'lang' to the desired language
    results = ocr.ocr('examples/1.png')
    
    final_json = process_ocr_result(results, 'G', 'test')
        

if __name__ == '__main__':
    paddle_ocr_test()