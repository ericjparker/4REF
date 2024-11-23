from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QPushButton, QLineEdit, QWidget, QSizePolicy, QSlider
from PyQt5.QtGui import QPixmap, QGuiApplication, QIcon, QFont, QFontDatabase
from PyQt5.QtCore import Qt, QSize
import sys
import requests
from io import BytesIO
import os

class ImageLabel(QLabel):
    def sizeHint(self):
        return QSize(0, 0)

    def minimumSizeHint(self):
        return QSize(0, 0)

class TextBasedImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        # Determine the base path
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        # Load and set the embedded font
        font_path = os.path.join(base_path, "TMT-Paint-Regular.otf")
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id == -1:
                print(f"Failed to load the font from {font_path}.")
                # Try to use the system-installed font
                font = QFont("TMT Paint", 14)
                QApplication.setFont(font)
            else:
                font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
                font = QFont(font_family, 14)
                QApplication.setFont(font)
        else:
            print(f"Font file not found at {font_path}.")
            # Try to use the system-installed font
            font = QFont("TMT Paint", 14)
            QApplication.setFont(font)

        # Update paths for images
        icon_path = os.path.join(base_path, "images", "icon.png")
        logo_path = os.path.join(base_path, "images", "logo.png")

        self.setWindowTitle("4REF - Reference Image Viewer")
        self.setWindowIcon(QIcon(icon_path))
        self.setGeometry(100, 100, 480, 360)  # Increased window size by 20%
        self.setAcceptDrops(True)  # Enable drag-and-drop for the main window

        # Set the background color
        self.setStyleSheet("background-color: #253a5e;")

        # Always-on-top state
        self.is_on_top = False

        # Store the original and scaled pixmaps
        self.original_pixmap = None
        self.scaled_pixmap = None

        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Logo at the top
        self.logo_label = QLabel()
        self.logo_pixmap = QPixmap(logo_path)
        self.logo_label.setPixmap(self.logo_pixmap)
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.logo_label)

        # Paste URL Input
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste Image URL")
        self.layout.addWidget(self.url_input)

        # Load Image Button
        self.load_button = QPushButton("Load Image from URL")
        self.load_button.clicked.connect(self.load_image_from_url)
        self.layout.addWidget(self.load_button)

        # Drag-and-Drop Label
        self.image_label = ImageLabel("Drag and Drop an Image Here")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setAcceptDrops(True)  # Allow QLabel to accept drops
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.image_label)

        # Reset Button (moved to bottom)
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_app)
        self.layout.addWidget(self.reset_button)

        # Opacity Slider
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(10)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setTickInterval(10)
        self.opacity_slider.setTickPosition(QSlider.TicksBelow)
        self.opacity_slider.valueChanged.connect(self.change_opacity)
        self.layout.addWidget(self.opacity_slider)

        # Label for Opacity Slider
        self.opacity_label = QLabel("Window Opacity: 100%")
        self.opacity_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.opacity_label)

        # Toggle Always-on-Top Button
        self.toggle_top_button = QPushButton("Toggle Always-on-Top")
        self.toggle_top_button.clicked.connect(self.toggle_on_top)
        self.layout.addWidget(self.toggle_top_button)

        # Apply styles
        self.apply_styles()

        # Auto-fetch URL from clipboard
        self.auto_fetch_url_from_clipboard()

    def apply_styles(self):
        # Button Style with Material Design feel
        button_style = """
        QPushButton {
            background-color: #4f8fba;
            color: white;
            border-radius: 5px;
            padding: 8px 16px;
            font-size: 14pt;
        }
        QPushButton:hover {
            background-color: #5faad1;
        }
        """
        self.load_button.setStyleSheet(button_style)
        self.reset_button.setStyleSheet(button_style)
        self.toggle_top_button.setStyleSheet(button_style)

        # Line Edit Style
        line_edit_style = """
        QLineEdit {
            background-color: #3c5e8b;
            color: #172038;
            border: none;
            padding: 8px;
            border-radius: 5px;
            font-size: 14pt;
        }
        """
        self.url_input.setStyleSheet(line_edit_style)

        # Image Label Style
        image_label_style = """
        QLabel {
            background-color: #3c5e8b;
            color: #172038;
            border: 1px solid #172038;
            padding: 10px;
            font-size: 14pt;
        }
        """
        self.image_label.setStyleSheet(image_label_style)

        # Opacity Label Style
        self.opacity_label.setStyleSheet("color: #FFFFFF; font-size: 14pt;")

        # Slider Style
        slider_style = """
        QSlider::groove:horizontal {
            border: 1px solid #172038;
            height: 8px;
            background: #3c5e8b;
            margin: 2px 0;
        }

        QSlider::handle:horizontal {
            background: #172038;
            border: 1px solid #172038;
            width: 18px;
            margin: -2px 0;
            border-radius: 3px;
        }
        """
        self.opacity_slider.setStyleSheet(slider_style)

        # Logo Style (Optional, if you want to adjust it)
        self.logo_label.setStyleSheet("background-color: #253a5e;")

    def load_image_from_url(self):
        """Load an image from the URL entered in the text field."""
        url = self.url_input.text()
        try:
            response = requests.get(url)
            response.raise_for_status()
            img_data = BytesIO(response.content)
            pixmap = QPixmap()
            pixmap.loadFromData(img_data.read())

            # Store the original pixmap
            self.original_pixmap = pixmap

            # Update the image display
            self.update_image()
        except Exception as e:
            self.image_label.setText(f"Error loading image: {e}")

    def update_image(self):
        """Update the displayed image, scaling it to fit within maximum size and the label."""
        if self.original_pixmap is None:
            return

        # Maximum size for the image
        max_size = QSize(800, 800)

        # First, scale the original pixmap to fit within maximum size, maintaining aspect ratio
        if (self.original_pixmap.width() > max_size.width() or
                self.original_pixmap.height() > max_size.height()):
            self.scaled_pixmap = self.original_pixmap.scaled(
                max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            self.scaled_pixmap = self.original_pixmap

        # Now, scale the pixmap to fit within the label's size, maintaining aspect ratio
        label_size = self.image_label.size()
        if label_size.width() > 0 and label_size.height() > 0:
            pixmap = self.scaled_pixmap.scaled(
                label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setPixmap(self.scaled_pixmap)

    def resizeEvent(self, event):
        """Handle window resizing and dynamically scale the image."""
        self.update_image()
        super().resizeEvent(event)

    def change_opacity(self):
        """Change the window opacity based on the slider value."""
        value = self.opacity_slider.value()
        opacity = value / 100.0  # Convert to a float between 0.1 and 1.0
        self.setWindowOpacity(opacity)
        self.opacity_label.setText(f"Window Opacity: {value}%")

    def toggle_on_top(self):
        """Toggle the always-on-top state of the window."""
        if self.is_on_top:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            self.toggle_top_button.setText("Toggle Always-on-Top (OFF)")
        else:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.toggle_top_button.setText("Toggle Always-on-Top (ON)")
        self.is_on_top = not self.is_on_top
        self.show()  # Reapply window flags

    def auto_fetch_url_from_clipboard(self):
        """Automatically fetch and load an image URL from the clipboard."""
        clipboard = QGuiApplication.clipboard()
        url = clipboard.text()
        if any(url.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg']):
            self.url_input.setText(url)
            self.load_image_from_url()

    def reset_app(self):
        """Reset the application to its default state."""
        self.url_input.clear()
        self.image_label.clear()
        self.image_label.setText("Drag and Drop an Image Here")
        self.original_pixmap = None
        self.scaled_pixmap = None
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)  # Reset always-on-top
        self.resize(480, 360)  # Reset to default size
        self.is_on_top = False
        self.setWindowOpacity(1.0)  # Reset opacity to 100%
        self.opacity_slider.setValue(100)
        self.opacity_label.setText("Window Opacity: 100%")
        self.show()  # Reapply window flags

    def dragEnterEvent(self, event):
        """Allow drag events if they contain files."""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Handle file drops."""
        file_path = event.mimeData().urls()[0].toLocalFile()
        pixmap = QPixmap(file_path)

        # Store the original pixmap
        self.original_pixmap = pixmap

        # Update the image display
        self.update_image()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = TextBasedImageViewer()
    viewer.show()
    sys.exit(app.exec_())
