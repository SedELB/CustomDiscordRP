import customtkinter
from tkinter import filedialog
from PIL import Image
import os
import styles

# NOTE: Online search is intentionally disabled for now (DuckDuckGo/Bing scraping
# is being bot-blocked). The backend lives in image_search.py and can be re-enabled
# later by wiring a grid into the "Search online" tab. Upload is the active path.

THUMB = 84
IMAGES_DIR = os.path.join("assets", "profile_images")


def _checkerboard(size, square=8):
    # Light/dark checker so PNG transparency is visible behind a thumbnail.
    img = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    dark = (200, 200, 200, 255)
    for y in range(0, size, square):
        for x in range(0, size, square):
            if (x // square + y // square) % 2 == 0:
                for yy in range(y, min(y + square, size)):
                    for xx in range(x, min(x + square, size)):
                        img.putpixel((xx, yy), dark)
    return img


def square_crop(img, size=512):
    img = img.convert("RGBA")
    w, h = img.size
    m = min(w, h)
    left = (w - m) // 2
    top = (h - m) // 2
    return img.crop((left, top, left + m, top + m)).resize((size, size), Image.LANCZOS)


def _thumb_image(img, box=THUMB):
    base = _checkerboard(box).copy()
    fitted = img.convert("RGBA").copy()
    fitted.thumbnail((box, box), Image.LANCZOS)
    ox = (box - fitted.width) // 2
    oy = (box - fitted.height) // 2
    base.alpha_composite(fitted, (ox, oy))
    return base


class ImagePicker(customtkinter.CTkToplevel):
    def __init__(self, master, profile_id, default_query, on_pick):
        super().__init__(master)
        self.profile_id = profile_id
        self.on_pick = on_pick
        self.selected_image = None  # PIL.Image
        self._image_refs = []  # keep CTkImage references alive

        self.title("Choose Image")
        self.geometry("460x480")
        self.configure(fg_color=styles.BG_PRIMARY)
        self.attributes("-topmost", True)

        self._font_body = customtkinter.CTkFont(family=styles.FONT_FAMILY, size=styles.SIZE_BODY)
        self._font_bold = customtkinter.CTkFont(family=styles.FONT_FAMILY, size=styles.SIZE_BODY, weight="bold")
        self._font_small = customtkinter.CTkFont(family=styles.FONT_FAMILY, size=styles.SIZE_SMALL)

        tabs = customtkinter.CTkTabview(
            self,
            fg_color=styles.BG_SECONDARY,
            segmented_button_fg_color=styles.BG_TERTIARY,
            segmented_button_selected_color=styles.ACCENT,
            segmented_button_selected_hover_color=styles.ACCENT_HOVER,
            text_color=styles.TEXT_PRIMARY,
        )
        tabs.pack(fill="both", expand=True, padx=12, pady=12)
        # Upload first so it is the default/active tab.
        self._upload_tab = tabs.add("Upload")
        self._search_tab = tabs.add("Search online")

        self._build_upload_tab()
        self._build_search_stub()

        self._use_btn = customtkinter.CTkButton(
            self,
            text="Use this image",
            font=self._font_bold,
            height=40,
            corner_radius=styles.RADIUS_BUTTON,
            fg_color=styles.ACCENT,
            hover_color=styles.ACCENT_HOVER,
            text_color=styles.TEXT_PRIMARY,
            state="disabled",
            command=self._confirm,
        )
        self._use_btn.pack(fill="x", padx=12, pady=(0, 12))

    # --- upload tab ----------------------------------------------------------
    def _build_upload_tab(self):
        customtkinter.CTkLabel(
            self._upload_tab,
            text="Pick a local image (PNG, JPG, ICO, WEBP).\nIt will be cropped to a square.",
            font=self._font_small,
            text_color=styles.TEXT_MUTED,
            justify="center",
        ).pack(pady=(16, 12))

        customtkinter.CTkButton(
            self._upload_tab,
            text="Choose file…",
            font=self._font_bold,
            height=40,
            corner_radius=styles.RADIUS_BUTTON,
            fg_color=styles.ACCENT,
            hover_color=styles.ACCENT_HOVER,
            text_color=styles.TEXT_PRIMARY,
            command=self._choose_file,
        ).pack()

        self._upload_preview = customtkinter.CTkLabel(self._upload_tab, text="", width=160, height=160)
        self._upload_preview.pack(pady=20)

    def _choose_file(self):
        path = filedialog.askopenfilename(
            title="Select image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.ico *.webp"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            img = Image.open(path)
            img.load()
        except Exception as exc:
            self._upload_preview.configure(image=None, text=f"Could not open image:\n{exc}", text_color=styles.DANGER)
            return

        self.selected_image = img.convert("RGBA")
        preview = customtkinter.CTkImage(_thumb_image(self.selected_image, 160), size=(160, 160))
        self._image_refs.append(preview)
        self._upload_preview.configure(image=preview, text="")
        self._use_btn.configure(state="normal")
        self.lift()
        self.attributes("-topmost", True)

    # --- search tab (disabled stub) -----------------------------------------
    def _build_search_stub(self):
        customtkinter.CTkLabel(
            self._search_tab,
            text="Online search is unavailable right now.",
            font=self._font_bold,
            text_color=styles.TEXT_PRIMARY,
        ).pack(pady=(40, 8))
        customtkinter.CTkLabel(
            self._search_tab,
            text="Free image search providers are currently blocking\n"
            "automated requests. For now, use the Upload tab to\n"
            "add an image from your computer.",
            font=self._font_small,
            text_color=styles.TEXT_MUTED,
            justify="center",
        ).pack(pady=(0, 8))

    # --- confirm -------------------------------------------------------------
    def _confirm(self):
        if self.selected_image is None:
            return
        os.makedirs(IMAGES_DIR, exist_ok=True)
        path = os.path.join(IMAGES_DIR, f"{self.profile_id}.png")
        square_crop(self.selected_image).save(path, "PNG")
        self.on_pick(path)
        self.destroy()
