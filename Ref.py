from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QPushButton, QLineEdit, QWidget, QSizePolicy, QSlider
from PyQt5.QtGui import QPixmap, QGuiApplication
from PyQt5.QtCore import Qt, QSize
import sys
import requests
from io import BytesIO

class ImageLabel(QLabel):
    def sizeHint(self):
        return QSize(0, 0)

    def minimumSizeHint(self):
        return QSize(0, 0)

class TextBasedImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Viewer")
        self.setGeometry(100, 100, 400, 300)
        self.setAcceptDrops(True)  # Enable drag-and-drop for the main window

        # Always-on-top state
        self.is_on_top = False

        # Store the original and scaled pixmaps
        self.original_pixmap = None
        self.scaled_pixmap = None

        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

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
        self.image_label.setStyleSheet("border: 1px solid black; padding: 10px;")
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

        # Auto-fetch URL from clipboard
        self.auto_fetch_url_from_clipboard()

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
        self.resize(400, 300)  # Reset to default size
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
