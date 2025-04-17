import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QTextEdit, QPushButton, QFileDialog, QVBoxLayout, QMessageBox
)
from embed import embed_data_into_image
from extract import extract_data_from_image

class StegoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BPCS Steganography")
        self.setGeometry(300, 300, 500, 400)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.label = QLabel("Secret Message:")
        self.layout.addWidget(self.label)

        self.text_edit = QTextEdit()
        self.layout.addWidget(self.text_edit)

        self.load_button = QPushButton("Select Cover Image")
        self.load_button.clicked.connect(self.select_image)
        self.layout.addWidget(self.load_button)

        self.embed_button = QPushButton("Embed Data")
        self.embed_button.clicked.connect(self.embed)
        self.layout.addWidget(self.embed_button)

        self.extract_button = QPushButton("Extract Data")
        self.extract_button.clicked.connect(self.extract)
        self.layout.addWidget(self.extract_button)

        self.cover_image_path = None

    def select_image(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Select Cover Image", "", "Images (*.png *.jpg)")
        if fname:
            self.cover_image_path = fname
            QMessageBox.information(self, "Image Selected", f"Selected image:\n{fname}")

    def embed(self):
        if not self.cover_image_path:
            QMessageBox.warning(self, "Error", "Please select a cover image first.")
            return

        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Error", "Please enter a message to embed.")
            return

        with open("input.txt", "w", encoding="utf-8") as f:
            f.write(text)

        try:
            embed_data_into_image(self.cover_image_path)
            QMessageBox.information(self, "Success", "Data embedded into stego_image.png")
        except Exception as e:
            QMessageBox.critical(self, "Embedding Failed", str(e))

    def extract(self):
        try:
            extract_data_from_image("stego_image.png")
            with open("output.txt", "r", encoding="utf-8") as f:
                extracted = f.read()

            # HTML formatting to change text size
            formatted_text = f"<p style='font-size: 18pt;'>{extracted}</p>"

            # Show the extracted message in a popup with customized text size
            QMessageBox.information(self, "Extracted Message", formatted_text, QMessageBox.Ok)
        except Exception as e:
            QMessageBox.critical(self, "Extraction Failed", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StegoApp()
    window.show()
    sys.exit(app.exec_())
