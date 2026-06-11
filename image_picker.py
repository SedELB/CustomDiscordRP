import os
from PIL import Image
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QFrame, QLabel, QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout,
)
import styles
import qt_utils

# NOTE: Online search is intentionally disabled for now (free providers are
# bot-blocking scrapers). The backend lives in image_search.py for later.

IMAGES_DIR = os.path.join("assets", "profile_images")


def square_crop(img, size=512):
    img = img.convert("RGBA")
    w, h = img.size
    m = min(w, h)
    left = (w - m) // 2
    top = (h - m) // 2
    return img.crop((left, top, left + m, top + m)).resize((size, size), Image.LANCZOS)


class ImagePicker(QDialog):
    def __init__(self, parent, profile_id, default_query, on_pick):
        super().__init__(parent)
        self.profile_id = profile_id
        self.on_pick = on_pick
        self.selected_image = None

        self.setWindowTitle("Choose Image")
        self.setWindowIcon(qt_utils.app_icon())
        self.setFixedSize(420, 470)
        self._opened = False

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 16)
        lay.setSpacing(12)

        title = QLabel("Choose an image")
        font = title.font()
        font.setPointSize(13)
        font.setBold(True)
        title.setFont(font)
        lay.addWidget(title)

        sub = QLabel("PNG, JPG, ICO or WEBP — it will be cropped to a square.")
        sub.setProperty("muted", True)
        sfont = sub.font()
        sfont.setPointSize(9)
        sub.setFont(sfont)
        lay.addWidget(sub)

        choose = QPushButton("Choose file…")
        choose.setFixedHeight(40)
        choose.clicked.connect(self._choose_file)
        lay.addWidget(choose)

        preview_wrap = QFrame()
        preview_wrap.setObjectName("darkPanel")
        pv_lay = QVBoxLayout(preview_wrap)
        pv_lay.setContentsMargins(12, 12, 12, 12)
        self.preview = QLabel("No image selected")
        self.preview.setProperty("muted", True)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setFixedHeight(200)
        pv_lay.addWidget(self.preview)
        lay.addWidget(preview_wrap)

        note = QLabel("Online image search is unavailable right now — free providers block automated requests.")
        note.setProperty("muted", True)
        nfont = note.font()
        nfont.setPointSize(8)
        note.setFont(nfont)
        note.setWordWrap(True)
        lay.addWidget(note)

        lay.addStretch()

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setProperty("kind", "ghost")
        cancel.clicked.connect(self.close)
        buttons.addWidget(cancel)
        self.use_btn = QPushButton("Use this image")
        self.use_btn.setEnabled(False)
        self.use_btn.clicked.connect(self._confirm)
        buttons.addWidget(self.use_btn)
        lay.addLayout(buttons)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._opened:
            self._opened = True
            qt_utils.animate_open(self)

    def _choose_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select image", "", "Images (*.png *.jpg *.jpeg *.ico *.webp);;All files (*.*)"
        )
        if not path:
            return
        try:
            img = Image.open(path)
            img.load()
        except Exception as exc:
            self.preview.setText(f"Could not open image:\n{exc}")
            self.preview.setStyleSheet(f"color: {styles.DANGER};")
            return

        self.selected_image = img.convert("RGBA")
        pm = qt_utils.crisp_from_pil(square_crop(self.selected_image, 512), 180, radius=16)
        self.preview.setPixmap(pm)
        self.use_btn.setEnabled(True)

    def _confirm(self):
        if self.selected_image is None:
            return
        os.makedirs(IMAGES_DIR, exist_ok=True)
        path = os.path.join(IMAGES_DIR, f"{self.profile_id}.png")
        square_crop(self.selected_image).save(path, "PNG")
        self.on_pick(path)
        self.close()
