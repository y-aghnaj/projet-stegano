import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QTextEdit, QPushButton, QFileDialog,
    QVBoxLayout, QMessageBox, QDialog, QScrollArea
)
from embed import embed_data_into_image, embed_data_into_video
from extract import extract_data_from_image, extract_data_from_video


class StegoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BPCS Steganography")
        self.setGeometry(300, 300, 500, 500)

        # Layout setup
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Label and text editor for secret message input
        self.label = QLabel("Secret Message:")
        self.layout.addWidget(self.label)

        self.text_edit = QTextEdit()
        self.layout.addWidget(self.text_edit)

        # File selection and operation buttons
        self.load_button = QPushButton("Select Cover File (Image/Video)")
        self.load_button.clicked.connect(self.select_file)
        self.layout.addWidget(self.load_button)

        self.embed_button = QPushButton("Embed Data")
        self.embed_button.clicked.connect(self.embed)
        self.layout.addWidget(self.embed_button)

        self.extract_button = QPushButton("Extract Data")
        self.extract_button.clicked.connect(self.extract)
        self.layout.addWidget(self.extract_button)

        # Track selected file path and type
        self.cover_file_path = None
        self.file_type = None  # 'image' or 'video'

    def select_file(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, "Select Cover File", "", "Images (*.png *.jpg *.jpeg);;Videos (*.mp4 *.avi)"
        )
        if fname:
            self.cover_file_path = fname
            if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                self.file_type = 'image'
            elif fname.lower().endswith(('.mp4', '.avi')):
                self.file_type = 'video'
            else:
                self.file_type = None

            QMessageBox.information(self, "File Selected", f"Selected file:\n{fname}")

    def embed(self):
        if not self.cover_file_path or not self.file_type:
            QMessageBox.warning(self, "Error", "Please select a valid cover image or video first.")
            return

        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Error", "Please enter a message to embed.")
            return

        with open("input.txt", "w", encoding="utf-8") as f:
            f.write(text)

        try:
            if self.file_type == 'image':
                embed_data_into_image(self.cover_file_path)
                QMessageBox.information(self, "Success", "Data embedded into stego_image.png")
            elif self.file_type == 'video':
                embed_data_into_video(self.cover_file_path)
                QMessageBox.information(self, "Success", "Data embedded into stego_video.mp4")
        except Exception as e:
            QMessageBox.critical(self, "Embedding Failed", str(e))

    def extract(self):
        try:
            if self.file_type == 'image':
                extract_data_from_image("stego_image.png")
            elif self.file_type == 'video':
                extract_data_from_video("stego_video.mp4")
            else:
                QMessageBox.warning(self, "Error", "Please select a cover image or video first.")
                return

            with open("output.txt", "r", encoding="utf-8") as f:
                extracted = f.read()

            # Show extracted message in a scrollable dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Extracted Message")
            dialog.resize(600, 400)

            layout = QVBoxLayout(dialog)

            scroll_area = QScrollArea()
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setText(extracted)
            scroll_area.setWidget(text_edit)
            scroll_area.setWidgetResizable(True)

            layout.addWidget(scroll_area)

            close_button = QPushButton("Close", dialog)
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)

            dialog.setLayout(layout)
            dialog.exec_()

        except FileNotFoundError:
            QMessageBox.critical(self, "Extraction Failed", "Stego file or output.txt not found.")
        except Exception as e:
            QMessageBox.critical(self, "Extraction Failed", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StegoApp()
    window.show()
    sys.exit(app.exec_())
