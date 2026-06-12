import io
import os
from PIL import Image
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog, QFrame, QLabel, QPushButton, QLineEdit, QFileDialog, QTabWidget,
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QMessageBox,
)
import styles
import qt_utils
import qt_net
import image_search

IMAGES_DIR = os.path.join("assets", "profile_images")
GRID_COLS = 4
THUMB = 88


def square_crop(img, size=512):
    img = img.convert("RGBA")
    w, h = img.size
    m = min(w, h)
    left = (w - m) // 2
    top = (h - m) // 2
    return img.crop((left, top, left + m, top + m)).resize((size, size), Image.LANCZOS)


class ImagePicker(QDialog):
    # on_pick(local_path_or_None, hosted_url_or_None)
    def __init__(self, parent, profile_id, default_query, on_pick):
        super().__init__(parent)
        self.profile_id = profile_id
        self.on_pick = on_pick
        self.selected_image = None
        self._net = qt_net.Net(self)
        self._thumb_buttons = []
        self._pending = 0
        self._opened = False

        self.setWindowTitle("Choose Image")
        self.setWindowIcon(qt_utils.app_icon())
        self.setFixedSize(520, 560)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 16)
        lay.setSpacing(12)

        title = QLabel("Choose an image")
        f = title.font(); f.setPointSize(13); f.setBold(True); title.setFont(f)
        lay.addWidget(title)

        tabs = QTabWidget()
        tabs.addTab(self._build_search_tab(default_query), "Search logos")
        tabs.addTab(self._build_upload_tab(), "Upload")
        lay.addWidget(tabs, stretch=1)

        self.status = QLabel("")
        self.status.setProperty("muted", True)
        sf = self.status.font(); sf.setPointSize(8); self.status.setFont(sf)
        lay.addWidget(self.status)

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

    # --- search tab ----------------------------------------------------------
    def _build_search_tab(self, default_query):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(0, 12, 0, 0)
        lay.setSpacing(10)

        bar = QHBoxLayout()
        self.query = QLineEdit()
        self.query.setPlaceholderText("Search for a brand or app logo…")
        self.query.setText(default_query)
        self.query.returnPressed.connect(self._do_search)
        bar.addWidget(self.query, stretch=1)
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._do_search)
        bar.addWidget(search_btn)
        lay.addLayout(bar)

        self.search_status = QLabel("Type a query and press Search.")
        self.search_status.setProperty("muted", True)
        ssf = self.search_status.font(); ssf.setPointSize(8); self.search_status.setFont(ssf)
        lay.addWidget(self.search_status)

        scroll = qt_utils.SmoothScrollArea()
        scroll.setWidgetResizable(True)
        host = QWidget()
        self.grid = QGridLayout(host)
        self.grid.setContentsMargins(0, 0, 6, 0)
        self.grid.setSpacing(8)
        scroll.setWidget(host)
        lay.addWidget(scroll, stretch=1)
        return tab

    def _do_search(self):
        query = self.query.text().strip()
        if not query:
            return
        self.search_status.setText("Searching…")
        self._clear_grid()
        self._net.search_brandfetch(query, lambda data: self._on_search(query, data))

    def _on_search(self, query, data):
        results = image_search.parse_logo_results(data, query, n=8)
        if not results:
            self.search_status.setText("No logos found. Try another name or use the Upload tab.")
            return
        self.search_status.setText(f"Loading {len(results)} logos…")
        self._pending = len(results)
        for r in results:
            self._net.get(r["url"], lambda d, name=r["name"]: self._on_thumb(name, d))

    def _on_thumb(self, name, data):
        self._pending -= 1
        if data is not None:
            try:
                img = Image.open(io.BytesIO(data)).convert("RGBA")
                self._add_thumb(name, img)
            except Exception:
                pass
        if self._pending <= 0:
            count = len(self._thumb_buttons)
            self.search_status.setText(
                f"{count} logo{'s' if count != 1 else ''} found. Click one to select." if count
                else "No logos loaded. Try the Upload tab."
            )

    def _add_thumb(self, name, img):
        idx = len(self._thumb_buttons)
        btn = QPushButton()
        btn.setProperty("kind", "thumb")
        btn.setCheckable(True)
        btn.setFixedSize(THUMB, THUMB)
        btn.setIconSize(QSize(THUMB - 16, THUMB - 16))
        btn.setIcon(QIcon(qt_utils.crisp_from_pil(img, THUMB - 16, radius=8)))
        btn.setToolTip(name)
        btn.clicked.connect(lambda _c, i=img, b=btn: self._select_thumb(i, b))
        self.grid.addWidget(btn, idx // GRID_COLS, idx % GRID_COLS)
        self._thumb_buttons.append(btn)

    def _clear_grid(self):
        self._thumb_buttons = []
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _select_thumb(self, img, button):
        self.selected_image = img
        for b in self._thumb_buttons:
            b.setChecked(b is button)
        self.use_btn.setEnabled(True)

    # --- upload tab ----------------------------------------------------------
    def _build_upload_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(0, 16, 0, 0)
        lay.setSpacing(12)

        info = QLabel("Pick a local image (PNG, JPG, ICO, WEBP).\nIt will be cropped to a square.")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setProperty("muted", True)
        lay.addWidget(info)

        choose = QPushButton("Choose file…")
        choose.setFixedHeight(40)
        choose.clicked.connect(self._choose_file)
        row = QHBoxLayout(); row.addStretch(); row.addWidget(choose); row.addStretch()
        lay.addLayout(row)

        wrap = QFrame()
        wrap.setObjectName("darkPanel")
        wl = QVBoxLayout(wrap)
        self.upload_preview = QLabel("No image selected")
        self.upload_preview.setProperty("muted", True)
        self.upload_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.upload_preview.setFixedHeight(190)
        wl.addWidget(self.upload_preview)
        lay.addWidget(wrap)
        lay.addStretch()
        return tab

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
            self.upload_preview.setText(f"Could not open image:\n{exc}")
            self.upload_preview.setStyleSheet(f"color: {styles.DANGER};")
            return
        self.selected_image = img.convert("RGBA")
        self.upload_preview.setPixmap(qt_utils.crisp_from_pil(square_crop(self.selected_image, 512), 170, radius=16))
        self.use_btn.setEnabled(True)

    # --- hosting + confirm ---------------------------------------------------
    def _confirm(self):
        if self.selected_image is None:
            return
        self.use_btn.setEnabled(False)
        self.status.setText("Uploading image to host…")

        # All PIL work on the main thread; only the upload goes async via Qt.
        square = square_crop(self.selected_image)
        os.makedirs(IMAGES_DIR, exist_ok=True)
        self._save_path = os.path.join(IMAGES_DIR, f"{self.profile_id}.png")
        try:
            square.save(self._save_path, "PNG")
        except Exception as exc:
            print(f"local save failed: {exc}")
            self._save_path = ""
        buf = io.BytesIO()
        square.save(buf, "PNG")
        self._net.upload_catbox(buf.getvalue(), self._on_hosted)

    def _on_hosted(self, url):
        if not url:
            QMessageBox.warning(
                self, "Upload failed",
                "Couldn't upload the image to a host, so it will preview locally but "
                "may not appear in Discord. You can try again or paste an image URL manually.",
            )
        self.on_pick(self._save_path or None, url or None)
        self.close()

    def showEvent(self, event):
        super().showEvent(event)
        if not self._opened:
            self._opened = True
            qt_utils.animate_open(self)
