import customtkinter
from tkinter import StringVar, filedialog
from PIL import Image, ImageDraw
import os
import uuid
import styles

MAX_FIELD = 128


def _placeholder_image(size=60):
    # Grey rounded square with a simple camera glyph, used when no image is set.
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    dc = ImageDraw.Draw(img)
    dc.rounded_rectangle((0, 0, size - 1, size - 1), radius=8, fill="#1e1f22")
    body_top = size * 0.38
    dc.rounded_rectangle((size * 0.18, body_top, size * 0.82, size * 0.78), radius=4, fill="#4e5058")
    dc.rectangle((size * 0.40, body_top - size * 0.08, size * 0.60, body_top), fill="#4e5058")
    dc.ellipse((size * 0.40, size * 0.46, size * 0.60, size * 0.66), fill="#1e1f22")
    return img


class ProfileEditor(customtkinter.CTkToplevel):
    def __init__(self, master, profile, on_save):
        super().__init__(master)
        self.on_save = on_save
        self.is_new = profile is None
        self.profile = {} if profile is None else profile

        self.title("New Profile" if self.is_new else "Edit Profile")
        self.geometry("880x640")
        self.configure(fg_color=styles.BG_PRIMARY)
        self.attributes("-topmost", True)

        self._font_header = customtkinter.CTkFont(family=styles.FONT_FAMILY, size=styles.SIZE_HEADER, weight="bold")
        self._font_body = customtkinter.CTkFont(family=styles.FONT_FAMILY, size=styles.SIZE_BODY)
        self._font_bold = customtkinter.CTkFont(family=styles.FONT_FAMILY, size=styles.SIZE_BODY, weight="bold")
        self._font_small = customtkinter.CTkFont(family=styles.FONT_FAMILY, size=styles.SIZE_SMALL)
        self._font_tiny = customtkinter.CTkFont(family=styles.FONT_FAMILY, size=11)
        self._font_card_name = customtkinter.CTkFont(family=styles.FONT_FAMILY, size=16, weight="bold")

        self._elapsed_seconds = 0
        self._timer_id = None
        self._placeholder = customtkinter.CTkImage(_placeholder_image(60), size=(60, 60))

        self._build_vars()
        self._build_layout()
        self._render_preview()
        self._tick()

        self.protocol("WM_DELETE_WINDOW", self._close)

    # --- state ---------------------------------------------------------------
    def _build_vars(self):
        p = self.profile
        self.var_title = StringVar(value=p.get("profileTitle", ""))
        self.var_exe = StringVar(value=p.get("targetExe", ""))
        self.var_exe_path = StringVar(value=p.get("exe_path", ""))
        self.var_app_id = StringVar(value=p.get("discord_app_id", ""))
        self.var_name = StringVar(value=p.get("statusName", ""))
        self.var_details = StringVar(value=p.get("details", ""))
        self.var_state = StringVar(value=p.get("state", ""))
        self.var_large_text = StringVar(value=p.get("large_image_text", ""))
        self.var_small_text = StringVar(value=p.get("small_image_text", ""))

        for var in (self.var_name, self.var_details, self.var_state):
            var.trace_add("write", lambda *_: self._render_preview())

    # --- layout --------------------------------------------------------------
    def _build_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        left = customtkinter.CTkScrollableFrame(self, fg_color=styles.BG_PRIMARY, corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
        self._build_form(left)

        right = customtkinter.CTkFrame(self, fg_color=styles.BG_PRIMARY, width=380)
        right.grid(row=0, column=1, sticky="nsew", padx=(4, 12), pady=8)
        right.grid_propagate(False)
        self._build_preview(right)

    def _label(self, parent, text):
        customtkinter.CTkLabel(
            parent, text=text, font=self._font_bold, text_color=styles.TEXT_PRIMARY, anchor="w"
        ).pack(fill="x", padx=4, pady=(14, 2))

    def _entry(self, parent, var, placeholder):
        entry = customtkinter.CTkEntry(
            parent,
            textvariable=var,
            placeholder_text=placeholder,
            font=self._font_body,
            height=36,
            corner_radius=styles.RADIUS_INPUT,
            fg_color=styles.BG_TERTIARY,
            border_color=styles.BORDER,
            border_width=1,
            text_color=styles.TEXT_PRIMARY,
        )
        entry.pack(fill="x", padx=4)
        return entry

    def _hint(self, parent, text):
        customtkinter.CTkLabel(
            parent, text=text, font=self._font_tiny, text_color=styles.TEXT_MUTED, anchor="w", justify="left"
        ).pack(fill="x", padx=4, pady=(2, 0))

    def _build_form(self, parent):
        customtkinter.CTkLabel(
            parent,
            text="New Profile" if self.is_new else "Edit Profile",
            font=self._font_header,
            text_color=styles.TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", padx=4, pady=(4, 8))

        self._label(parent, "Profile title")
        self._entry(parent, self.var_title, "e.g. SolidWorks 2024")

        self._label(parent, "Executable")
        exe_row = customtkinter.CTkFrame(parent, fg_color="transparent")
        exe_row.pack(fill="x", padx=4)
        exe_entry = customtkinter.CTkEntry(
            exe_row,
            textvariable=self.var_exe,
            placeholder_text="SLDWORKS.exe",
            font=self._font_body,
            height=36,
            corner_radius=styles.RADIUS_INPUT,
            fg_color=styles.BG_TERTIARY,
            border_color=styles.BORDER,
            border_width=1,
            text_color=styles.TEXT_PRIMARY,
        )
        exe_entry.pack(side="left", fill="x", expand=True)
        customtkinter.CTkButton(
            exe_row,
            text="Browse",
            width=80,
            height=36,
            font=self._font_small,
            corner_radius=styles.RADIUS_BUTTON,
            fg_color=styles.BG_TERTIARY,
            hover_color=styles.BORDER,
            text_color=styles.TEXT_PRIMARY,
            command=self._pick_exe,
        ).pack(side="left", padx=(8, 0))
        self._hint(parent, "Pick the .exe or type its name — the profile activates while it runs.")

        self._label(parent, "Discord App ID")
        self._entry(parent, self.var_app_id, "123456789012345678")
        self._hint(parent, "Create an app at discord.com/developers → copy its Application ID.")

        self._label(parent, "Application name")
        self._entry(parent, self.var_name, "Shown bold in Discord")

        self._label(parent, "Details")
        self._entry(parent, self.var_details, "Top line, max 128 chars")

        self._label(parent, "State")
        self._entry(parent, self.var_state, "Bottom line, max 128 chars")

        self._label(parent, "Large image tooltip")
        self._entry(parent, self.var_large_text, "Hover text for the large image")

        self._label(parent, "Small image tooltip")
        self._entry(parent, self.var_small_text, "Hover text for the small image")

        toggles = customtkinter.CTkFrame(parent, fg_color="transparent")
        toggles.pack(fill="x", padx=4, pady=(16, 4))

        self.switch_elapsed = customtkinter.CTkSwitch(
            toggles,
            text="Show elapsed time",
            font=self._font_body,
            text_color=styles.TEXT_PRIMARY,
            progress_color=styles.ACCENT,
            command=self._render_preview,
        )
        self.switch_elapsed.pack(anchor="w", pady=4)
        if self.profile.get("show_elapsed", True):
            self.switch_elapsed.select()

        self.switch_enabled = customtkinter.CTkSwitch(
            toggles,
            text="Enable profile",
            font=self._font_body,
            text_color=styles.TEXT_PRIMARY,
            progress_color=styles.SUCCESS,
        )
        self.switch_enabled.pack(anchor="w", pady=4)
        if self.profile.get("enabled", True):
            self.switch_enabled.select()

        actions = customtkinter.CTkFrame(parent, fg_color="transparent")
        actions.pack(fill="x", padx=4, pady=(20, 8))
        customtkinter.CTkButton(
            actions,
            text="Cancel",
            font=self._font_bold,
            height=40,
            corner_radius=styles.RADIUS_BUTTON,
            fg_color=styles.BG_TERTIARY,
            hover_color=styles.BORDER,
            text_color=styles.TEXT_PRIMARY,
            command=self._close,
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))
        customtkinter.CTkButton(
            actions,
            text="Save Profile",
            font=self._font_bold,
            height=40,
            corner_radius=styles.RADIUS_BUTTON,
            fg_color=styles.ACCENT,
            hover_color=styles.ACCENT_HOVER,
            text_color=styles.TEXT_PRIMARY,
            command=self._save,
        ).pack(side="left", expand=True, fill="x", padx=(5, 0))

    def _build_preview(self, parent):
        customtkinter.CTkLabel(
            parent, text="Live preview", font=self._font_bold, text_color=styles.TEXT_MUTED, anchor="w"
        ).pack(fill="x", padx=4, pady=(4, 8))

        card = customtkinter.CTkFrame(parent, fg_color=styles.CARD_BG, corner_radius=styles.RADIUS_CARD)
        card.pack(fill="x", padx=4)

        # "PLAYING A GAME" header
        customtkinter.CTkLabel(
            card,
            text="PLAYING A GAME",
            font=customtkinter.CTkFont(family=styles.FONT_FAMILY, size=11, weight="bold"),
            text_color=styles.TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(16, 8))

        body = customtkinter.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=16, pady=(0, 16))

        self._img_label = customtkinter.CTkLabel(body, text="", image=self._placeholder, width=60, height=60)
        self._img_label.pack(side="left", anchor="n")

        text_col = customtkinter.CTkFrame(body, fg_color="transparent")
        text_col.pack(side="left", fill="x", expand=True, padx=(14, 0))

        self._lbl_name = customtkinter.CTkLabel(
            text_col, text="", font=self._font_card_name, text_color=styles.TEXT_PRIMARY, anchor="w", justify="left"
        )
        self._lbl_name.pack(fill="x")
        self._lbl_details = customtkinter.CTkLabel(
            text_col, text="", font=self._font_small, text_color=styles.TEXT_PRIMARY, anchor="w", justify="left"
        )
        self._lbl_details.pack(fill="x")
        self._lbl_state = customtkinter.CTkLabel(
            text_col, text="", font=self._font_small, text_color=styles.TEXT_PRIMARY, anchor="w", justify="left"
        )
        self._lbl_state.pack(fill="x")
        self._lbl_elapsed = customtkinter.CTkLabel(
            text_col, text="", font=self._font_small, text_color=styles.TEXT_MUTED, anchor="w", justify="left"
        )
        self._lbl_elapsed.pack(fill="x", pady=(2, 0))

        # Online status row
        status = customtkinter.CTkFrame(parent, fg_color="transparent")
        status.pack(fill="x", padx=4, pady=(12, 0))
        customtkinter.CTkLabel(status, text="●", font=self._font_small, text_color=styles.SUCCESS).pack(side="left")
        customtkinter.CTkLabel(
            status, text="Online", font=self._font_small, text_color=styles.TEXT_MUTED
        ).pack(side="left", padx=(6, 0))

    # --- behaviour -----------------------------------------------------------
    def _pick_exe(self):
        path = filedialog.askopenfilename(
            title="Select executable", filetypes=[("Executables", "*.exe"), ("All files", "*.*")]
        )
        if not path:
            return
        self.var_exe_path.set(path)
        self.var_exe.set(os.path.basename(path))
        self.lift()
        self.attributes("-topmost", True)

    def _render_preview(self):
        self._lbl_name.configure(text=self.var_name.get() or "Application name")
        self._lbl_details.configure(text=self.var_details.get())
        self._lbl_state.configure(text=self.var_state.get())
        if self.switch_elapsed.get():
            self._lbl_elapsed.pack(fill="x", pady=(2, 0))
        else:
            self._lbl_elapsed.pack_forget()

    def _tick(self):
        if not self.winfo_exists():
            return
        mins, secs = divmod(self._elapsed_seconds, 60)
        self._lbl_elapsed.configure(text=f"{mins:02d}:{secs:02d} elapsed")
        self._elapsed_seconds += 1
        self._timer_id = self.after(1000, self._tick)

    def _normalize_exe(self, value):
        value = value.strip()
        if value and not value.lower().endswith(".exe"):
            value = value + ".exe"
        return value

    def _save(self):
        p = self.profile
        if "id" not in p:
            p["id"] = str(uuid.uuid4())
        p["profileTitle"] = self.var_title.get().strip() or "Untitled"
        p["targetExe"] = self._normalize_exe(self.var_exe.get())
        p["exe_path"] = self.var_exe_path.get().strip()
        p["discord_app_id"] = self.var_app_id.get().strip()
        p["statusName"] = self.var_name.get().strip()[:MAX_FIELD]
        p["details"] = self.var_details.get().strip()[:MAX_FIELD]
        p["state"] = self.var_state.get().strip()[:MAX_FIELD]
        p["large_image_text"] = self.var_large_text.get().strip()
        p["small_image_text"] = self.var_small_text.get().strip()
        p["show_elapsed"] = bool(self.switch_elapsed.get())
        p["enabled"] = bool(self.switch_enabled.get())

        self.on_save(p, self.is_new)
        self._close()

    def _close(self):
        if self._timer_id is not None:
            self.after_cancel(self._timer_id)
            self._timer_id = None
        self.destroy()
