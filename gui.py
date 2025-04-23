import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QTextEdit, QPushButton, QFileDialog,
    QVBoxLayout, QMessageBox, QComboBox, QHBoxLayout, QLineEdit
)
from video_embed import embed_into_video
from video_extract import extract_from_video
from embed import embed_data_into_image
from extract import extract_data_from_image

class UnifiedStegoApp(QWidget):
    global key
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Unified BPCS Steganography")
        self.setGeometry(300, 300, 600, 500)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Image", "Video"])
        self.layout.addWidget(QLabel("Select Mode:"))
        self.layout.addWidget(self.mode_selector)

        self.label = QLabel("Secret Message:")
        self.layout.addWidget(self.label)

        self.text_edit = QTextEdit()
        self.layout.addWidget(self.text_edit)

        self.key_label = QLabel("Encryption Key:")
        self.layout.addWidget(self.key_label)

        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.Password)  # Hide the input for security
        self.layout.addWidget(self.key_input)

        self.file_button = QPushButton("Select File")
        self.file_button.clicked.connect(self.select_file)
        self.layout.addWidget(self.file_button)

        self.embed_button = QPushButton("Embed")
        self.embed_button.clicked.connect(self.embed)
        self.layout.addWidget(self.embed_button)

        self.extract_button = QPushButton("Extract")
        self.extract_button.clicked.connect(self.extract)
        self.layout.addWidget(self.extract_button)

        self.selected_path = None

    def select_file(self):
        if self.mode_selector.currentText() == "Image":
            fname, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg)")
        else:
            fname, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Videos (*.mp4 *.avi *.mov)")
        if fname:
            self.selected_path = fname
            QMessageBox.information(self, "File Selected", f"Selected file:\n{fname}")

    def embed(self):
        if not self.selected_path:
            QMessageBox.warning(self, "Error", "Please select a file first.")
            return

        message = self.text_edit.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "Error", "Please enter a message to embed.")
            return

        # Get the key from input field
        key = self.key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Error", "Please enter an encryption key.")
            return

        with open("input.txt", "w", encoding="utf-8") as f:
            f.write(message)

        try:
            if self.mode_selector.currentText() == "Image":
                embed_data_into_image(self.selected_path)  # Embed for image
                QMessageBox.information(self, "Success", "Data embedded into stego_image.png")
            else:
                embed_into_video(self.selected_path, "stego_video.avi", message, key)  # Pass key to video embed
                QMessageBox.information(self, "Success", "Data embedded into stego_video.avi")
        except Exception as e:
            QMessageBox.critical(self, "Embedding Failed", str(e))

    def extract(self):
        try:
            if self.mode_selector.currentText() == "Image":
                extract_data_from_image("stego_image.png")  # Extract from image
            else:
                extract_from_video("stego_video.avi", key)  # Extract from video

            with open("output.txt", "r", encoding="utf-8") as f:
                extracted = f.read()

            QMessageBox.information(self, "Extracted Message", extracted, QMessageBox.Ok)
        except Exception as e:
            QMessageBox.critical(self, "Extraction Failed", str(e))
    key = ""


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UnifiedStegoApp()
    window.show()
    sys.exit(app.exec_())
