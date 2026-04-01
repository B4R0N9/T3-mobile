# ============================================================
# Nama  : M.Danuarta Wiraguna
# NIM   : F1D02310124
# Kelas : C
# Tugas : T2-Week4 — Form Multi-Step dengan Event & Signal Handling
# ============================================================

import sys
import re
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout,
    QRadioButton, QButtonGroup, QDateEdit, QFrame,
    QScrollArea, QSizePolicy, QStackedWidget, QTextEdit
)
from PySide6.QtCore import (
    Qt, Signal, QObject, QDate, QPropertyAnimation,
    QEasingCurve, QSize
)
from PySide6.QtGui import (
    QFont, QColor, QPainter, QPen, QBrush, QPalette,
    QLinearGradient, QIcon
)


class StepSignals(QObject):
    """Custom signals untuk notifikasi perpindahan antar step."""
    step_changed   = Signal(int, int)   
    step_completed = Signal(int)        
    form_submitted = Signal(dict)      


class ProgressIndicator(QWidget):
    """Widget progress indicator bergaya step-circle seperti contoh."""

    STEPS = ["Data Pribadi", "Kontak", "Akun"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_step = 0          
        self.completed_steps: set = set()
        self.setMinimumHeight(80)
        self.setMinimumWidth(400)

    def set_step(self, step: int):
        self.current_step = step
        self.update()

    def mark_completed(self, step: int):
        self.completed_steps.add(step)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        n = len(self.STEPS)

        circle_r   = 22
        top_y      = h // 2 - 10
        label_y    = top_y + circle_r + 14

        margin = 60
        step_w = (w - 2 * margin) / (n - 1)
        cx = [int(margin + i * step_w) for i in range(n)]

        for i in range(n - 1):
            x1 = cx[i] + circle_r
            x2 = cx[i + 1] - circle_r
            y  = top_y

          
            if i in self.completed_steps or i < self.current_step:
                pen = QPen(QColor("#4CAF50"), 3)
            else:
                pen = QPen(QColor("#C0C0C0"), 3)
            painter.setPen(pen)
            painter.drawLine(x1, y, x2, y)

        for i, label in enumerate(self.STEPS):
            x = cx[i]
            y = top_y

            if i in self.completed_steps or i < self.current_step:
                # Selesai → hijau + centang
                painter.setBrush(QBrush(QColor("#4CAF50")))
                painter.setPen(QPen(QColor("#4CAF50")))
                painter.drawEllipse(x - circle_r, y - circle_r,
                                    circle_r * 2, circle_r * 2)
                painter.setPen(QPen(QColor("white"), 2))
                painter.setFont(QFont("Arial", 13, QFont.Weight.Bold))
                painter.drawText(x - circle_r, y - circle_r,
                                 circle_r * 2, circle_r * 2,
                                 Qt.AlignmentFlag.AlignCenter, "✓")
                label_color = QColor("#4CAF50")

            elif i == self.current_step:
                # Aktif → biru
                painter.setBrush(QBrush(QColor("#2196F3")))
                painter.setPen(QPen(QColor("#2196F3")))
                painter.drawEllipse(x - circle_r, y - circle_r,
                                    circle_r * 2, circle_r * 2)
                painter.setPen(QPen(QColor("white"), 2))
                painter.setFont(QFont("Arial", 13, QFont.Weight.Bold))
                painter.drawText(x - circle_r, y - circle_r,
                                 circle_r * 2, circle_r * 2,
                                 Qt.AlignmentFlag.AlignCenter, str(i + 1))
                label_color = QColor("#2196F3")

            else:
                # Belum aktif → abu-abu
                painter.setBrush(QBrush(QColor("#C0C0C0")))
                painter.setPen(QPen(QColor("#C0C0C0")))
                painter.drawEllipse(x - circle_r, y - circle_r,
                                    circle_r * 2, circle_r * 2)
                painter.setPen(QPen(QColor("white"), 2))
                painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
                painter.drawText(x - circle_r, y - circle_r,
                                 circle_r * 2, circle_r * 2,
                                 Qt.AlignmentFlag.AlignCenter, str(i + 1))
                label_color = QColor("#888888")

            # Label teks bawah circle
            painter.setPen(QPen(label_color))
            painter.setFont(QFont("Arial", 9,
                                  QFont.Weight.Bold if i == self.current_step
                                  else QFont.Weight.Normal))
            painter.drawText(x - 50, label_y, 100, 20,
                             Qt.AlignmentFlag.AlignCenter, label)

        painter.end()

class ValidatedLineEdit(QLineEdit):
    """QLineEdit dengan border berwarna sesuai status validasi."""

    validity_changed = Signal(bool)

    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self._validator_fn = None
        self._is_valid = False
        self._error_msg = ""
        self._apply_style(None)   # awal: netral
        self.textChanged.connect(self._on_text_changed)

    def set_validator(self, fn):
        """fn(text) -> (bool, str_error)"""
        self._validator_fn = fn

    def _on_text_changed(self, text):
        if not self._validator_fn:
            return
        if not text:
            self._apply_style(None)
            was = self._is_valid
            self._is_valid = False
            if was:
                self.validity_changed.emit(False)
            return
        valid, msg = self._validator_fn(text)
        self._error_msg = msg
        self._apply_style(valid)
        if valid != self._is_valid:
            self._is_valid = valid
            self.validity_changed.emit(valid)

    def _apply_style(self, valid):
        base = (
            "QLineEdit {"
            "  padding: 8px 12px;"
            "  border-radius: 6px;"
            "  font-size: 14px;"
            "  color: #111111;"
            "  background: #FFFFFF;"
            "  selection-background-color: #2196F3;"
            "  selection-color: #FFFFFF;"
        )
        if valid is None:
            style = base + "  border: 2px solid #CCCCCC;}"
        elif valid:
            style = base + "  border: 2px solid #4CAF50;}"
        else:
            style = base + "  border: 2px solid #FF9800;}"
        self.setStyleSheet(style)

    @property
    def is_valid(self):
        return self._is_valid

    @property
    def error_message(self):
        return self._error_msg


# ─────────────────────────────────────────────
#  STEP 1 — Data Pribadi
# ─────────────────────────────────────────────
class Step1Widget(QWidget):
    validity_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._check_validity()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Step 1: Data Pribadi")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #1A1A1A;")
        layout.addWidget(title)

        # Nama
        layout.addWidget(self._label("Nama Lengkap"))
        self.nama = ValidatedLineEdit("Masukkan nama lengkap")
        self.nama.set_validator(lambda t: (len(t.strip()) >= 3,
                                           "Nama minimal 3 karakter"))
        self.nama.validity_changed.connect(self._check_validity)
        layout.addWidget(self.nama)
        self.err_nama = self._error_label()
        layout.addWidget(self.err_nama)

        # Tanggal Lahir
        layout.addWidget(self._label("Tanggal Lahir"))
        self.tgl_lahir = QDateEdit()
        self.tgl_lahir.setCalendarPopup(True)
        self.tgl_lahir.setDate(QDate(2000, 1, 1))
        self.tgl_lahir.setMaximumDate(QDate.currentDate())
        self.tgl_lahir.setStyleSheet(
            "QDateEdit { padding: 8px 12px; border: 2px solid #4CAF50;"
            " border-radius: 6px; font-size: 14px; color: #111111; background: #FFFFFF;}"
            "QDateEdit::drop-down { border: none; width: 20px; }"
        )
        self.tgl_lahir.dateChanged.connect(self._check_validity)
        layout.addWidget(self.tgl_lahir)

        # Jenis Kelamin
        layout.addWidget(self._label("Jenis Kelamin"))
        jk_frame = QFrame()
        jk_layout = QHBoxLayout(jk_frame)
        jk_layout.setContentsMargins(0, 0, 0, 0)
        self.rb_laki   = QRadioButton("Laki-laki")
        self.rb_perempuan = QRadioButton("Perempuan")
        self.rb_laki.setStyleSheet("color: #1A1A1A; font-size: 13px;")
        self.rb_perempuan.setStyleSheet("color: #1A1A1A; font-size: 13px;")
        self.jk_group  = QButtonGroup(self)
        self.jk_group.addButton(self.rb_laki, 1)
        self.jk_group.addButton(self.rb_perempuan, 2)
        self.rb_laki.toggled.connect(self._check_validity)
        self.rb_perempuan.toggled.connect(self._check_validity)
        jk_layout.addWidget(self.rb_laki)
        jk_layout.addWidget(self.rb_perempuan)
        jk_layout.addStretch()
        layout.addWidget(jk_frame)
        self.err_jk = self._error_label()
        layout.addWidget(self.err_jk)

        layout.addStretch()

    def _label(self, text):
        lbl = QLabel(text)
        lbl.setFont(QFont("Arial", 10))
        lbl.setStyleSheet("color: #333333; font-weight: bold;")
        return lbl

    def _error_label(self):
        lbl = QLabel("")
        lbl.setStyleSheet("color: #FF9800; font-size: 11px;")
        lbl.setVisible(False)
        return lbl

    def _check_validity(self):
        # Nama
        nama_ok = self.nama.is_valid
        if self.nama.text() and not nama_ok:
            self.err_nama.setText(f"⚠ {self.nama.error_message}")
            self.err_nama.setVisible(True)
        else:
            self.err_nama.setVisible(False)

        # Jenis kelamin
        jk_ok = self.jk_group.checkedId() != -1
        if not jk_ok and (self.rb_laki.isChecked() or self.rb_perempuan.isChecked()):
            self.err_jk.setText("⚠ Pilih jenis kelamin")
            self.err_jk.setVisible(True)
        else:
            self.err_jk.setVisible(False)

        # Tanggal lahir selalu valid (QDateEdit)
        all_valid = nama_ok and jk_ok
        self.validity_changed.emit(all_valid)

    def get_data(self) -> dict:
        jk = "Laki-laki" if self.rb_laki.isChecked() else "Perempuan"
        return {
            "nama": self.nama.text(),
            "tanggal_lahir": self.tgl_lahir.date().toString("dd-MM-yyyy"),
            "jenis_kelamin": jk,
        }


# ─────────────────────────────────────────────
#  STEP 2 — Kontak
# ─────────────────────────────────────────────
class Step2Widget(QWidget):
    validity_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._check_validity()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Step 2: Informasi Kontak")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #1A1A1A;")
        layout.addWidget(title)

        # Email
        layout.addWidget(self._label("Email"))
        self.email = ValidatedLineEdit("contoh@email.com")
        self.email.set_validator(self._validate_email)
        self.email.validity_changed.connect(self._check_validity)
        layout.addWidget(self.email)
        self.err_email = self._error_label()
        layout.addWidget(self.err_email)

        # Telepon
        layout.addWidget(self._label("Telepon"))
        self.telepon = ValidatedLineEdit("08xxxxxxxxxx")
        self.telepon.set_validator(lambda t: (
            t.isdigit() and len(t) >= 10,
            "Nomor minimal 10 digit"
        ))
        self.telepon.validity_changed.connect(self._check_validity)
        layout.addWidget(self.telepon)
        self.err_telepon = self._error_label()
        layout.addWidget(self.err_telepon)

        # Alamat
        layout.addWidget(self._label("Alamat"))
        self.alamat = ValidatedLineEdit("Jalan / Kota / Provinsi")
        self.alamat.set_validator(lambda t: (len(t.strip()) >= 10,
                                              "Alamat minimal 10 karakter"))
        self.alamat.validity_changed.connect(self._check_validity)
        layout.addWidget(self.alamat)
        self.err_alamat = self._error_label()
        layout.addWidget(self.err_alamat)

        layout.addStretch()

    def _label(self, text):
        lbl = QLabel(text)
        lbl.setFont(QFont("Arial", 10))
        lbl.setStyleSheet("color: #333333; font-weight: bold;")
        return lbl

    def _error_label(self):
        lbl = QLabel("")
        lbl.setStyleSheet("color: #FF9800; font-size: 11px;")
        lbl.setVisible(False)
        return lbl

    @staticmethod
    def _validate_email(text):
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
        ok = bool(re.match(pattern, text))
        return ok, "Format email tidak valid"

    def _check_validity(self):
        for field, err_lbl in [
            (self.email,   self.err_email),
            (self.telepon, self.err_telepon),
            (self.alamat,  self.err_alamat),
        ]:
            if field.text() and not field.is_valid:
                err_lbl.setText(f"⚠ {field.error_message}")
                err_lbl.setVisible(True)
            else:
                err_lbl.setVisible(False)

        all_valid = (self.email.is_valid and
                     self.telepon.is_valid and
                     self.alamat.is_valid)
        self.validity_changed.emit(all_valid)

    def get_data(self) -> dict:
        return {
            "email":   self.email.text(),
            "telepon": self.telepon.text(),
            "alamat":  self.alamat.text(),
        }


# ─────────────────────────────────────────────
#  STEP 3 — Akun
# ─────────────────────────────────────────────
class Step3Widget(QWidget):
    validity_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._check_validity()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Step 3: Informasi Akun")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #1A1A1A;")
        layout.addWidget(title)

        # Username
        layout.addWidget(self._label("Username"))
        self.username = ValidatedLineEdit("Minimal 4 karakter")
        self.username.set_validator(lambda t: (
            len(t.strip()) >= 4 and t.replace("_", "").isalnum(),
            "Username minimal 4 karakter, hanya huruf/angka/_"
        ))
        self.username.validity_changed.connect(self._check_validity)
        layout.addWidget(self.username)
        self.err_username = self._error_label()
        layout.addWidget(self.err_username)

        # Password
        layout.addWidget(self._label("Password"))
        self.password = ValidatedLineEdit("Minimal 8 karakter")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.set_validator(lambda t: (
            len(t) >= 8,
            "Password minimal 8 karakter"
        ))
        self.password.validity_changed.connect(self._check_validity)
        self.password.textChanged.connect(self._recheck_confirm)
        layout.addWidget(self.password)
        self.err_password = self._error_label()
        layout.addWidget(self.err_password)

        # Confirm Password
        layout.addWidget(self._label("Konfirmasi Password"))
        self.confirm = ValidatedLineEdit("Ulangi password")
        self.confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm.set_validator(lambda t: (
            t == self.password.text(),
            "Password tidak cocok"
        ))
        self.confirm.validity_changed.connect(self._check_validity)
        layout.addWidget(self.confirm)
        self.err_confirm = self._error_label()
        layout.addWidget(self.err_confirm)

        layout.addStretch()

    def _label(self, text):
        lbl = QLabel(text)
        lbl.setFont(QFont("Arial", 10))
        lbl.setStyleSheet("color: #333333; font-weight: bold;")
        return lbl

    def _error_label(self):
        lbl = QLabel("")
        lbl.setStyleSheet("color: #FF9800; font-size: 11px;")
        lbl.setVisible(False)
        return lbl

    def _recheck_confirm(self):
        """Trigger revalidasi confirm saat password berubah."""
        if self.confirm.text():
            self.confirm._on_text_changed(self.confirm.text())

    def _check_validity(self):
        for field, err_lbl in [
            (self.username, self.err_username),
            (self.password, self.err_password),
            (self.confirm,  self.err_confirm),
        ]:
            if field.text() and not field.is_valid:
                err_lbl.setText(f"⚠ {field.error_message}")
                err_lbl.setVisible(True)
            else:
                err_lbl.setVisible(False)

        all_valid = (self.username.is_valid and
                     self.password.is_valid and
                     self.confirm.is_valid)
        self.validity_changed.emit(all_valid)

    def get_data(self) -> dict:
        return {
            "username": self.username.text(),
            "password": self.password.text(),
        }


# ─────────────────────────────────────────────
#  STEP 4 — Review & Submit
# ─────────────────────────────────────────────
class ReviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Review Data")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #1A1A1A;")
        layout.addWidget(title)

        subtitle = QLabel("Periksa kembali data Anda sebelum submit:")
        subtitle.setStyleSheet("color: #444444; font-size: 12px;")
        layout.addWidget(subtitle)

        # Frame untuk tabel review
        self.review_frame = QFrame()
        self.review_frame.setStyleSheet(
            "QFrame { background: #F8F9FA; border: 1px solid #E0E0E0;"
            " border-radius: 8px; padding: 8px; }"
        )
        self.review_layout = QGridLayout(self.review_frame)
        self.review_layout.setSpacing(8)
        layout.addWidget(self.review_frame)
        layout.addStretch()

    def populate(self, data: dict):
        """Isi tabel review dengan data dari semua step."""
        # Hapus widget lama
        while self.review_layout.count():
            item = self.review_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        labels = {
            "nama":           "Nama Lengkap",
            "tanggal_lahir":  "Tanggal Lahir",
            "jenis_kelamin":  "Jenis Kelamin",
            "email":          "Email",
            "telepon":        "Telepon",
            "alamat":         "Alamat",
            "username":       "Username",
            "password":       "Password",
        }
        row = 0
        for key, display in labels.items():
            val = data.get(key, "-")
            if key == "password":
                val = "●" * len(val)

            key_lbl = QLabel(display + ":")
            key_lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            key_lbl.setStyleSheet("color: #1A1A1A;")

            val_lbl = QLabel(val)
            val_lbl.setFont(QFont("Arial", 10))
            val_lbl.setStyleSheet("color: #111111;")
            val_lbl.setWordWrap(True)

            self.review_layout.addWidget(key_lbl, row, 0)
            self.review_layout.addWidget(val_lbl, row, 1)
            row += 1
# ─────────────────────────────────────────────
#  Main Window
# ─────────────────────────────────────────────
class FormRegistrasi(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Form Registrasi")
        self.setFixedSize(660, 560)

        # Signals
        self.signals = StepSignals()
        self.signals.step_changed.connect(self._on_step_changed)
        self.signals.step_completed.connect(self._on_step_completed)
        self.signals.form_submitted.connect(self._on_form_submitted)

        self.current_step = 0
        self.form_data: dict = {}

        self._build_ui()
        self._update_nav_buttons()

    # ── UI Builder ──────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header bar (mirip title bar kustom)
        header = QFrame()
        header.setFixedHeight(44)
        header.setStyleSheet(
            "QFrame { background: #2D3748; border-radius: 0px; }"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 0, 14, 0)
        icon_lbl = QLabel("📋")
        icon_lbl.setFont(QFont("Arial", 14))
        title_lbl = QLabel("Form Registrasi")
        title_lbl.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: white;")
        header_layout.addWidget(icon_lbl)
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        # Tombol window palsu
        for sym in ["─", "□", "✕"]:
            btn = QLabel(sym)
            btn.setFont(QFont("Arial", 11))
            btn.setStyleSheet("color: #AAAAAA; margin-left: 8px;")
            header_layout.addWidget(btn)
        root.addWidget(header)

        # Progress area
        prog_frame = QFrame()
        prog_frame.setStyleSheet(
            "QFrame { background: #EEEEEE; border-bottom: 1px solid #DDDDDD; }"
        )
        prog_layout = QHBoxLayout(prog_frame)
        prog_layout.setContentsMargins(20, 8, 20, 8)
        self.progress = ProgressIndicator()
        prog_layout.addWidget(self.progress)
        root.addWidget(prog_frame)

        # Stacked content
        content = QFrame()
        content.setStyleSheet("QFrame { background: white; }")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 20, 30, 10)

        self.stack = QStackedWidget()
        self.step1 = Step1Widget()
        self.step2 = Step2Widget()
        self.step3 = Step3Widget()
        self.review = ReviewWidget()

        self.step1.validity_changed.connect(self._on_validity_changed)
        self.step2.validity_changed.connect(self._on_validity_changed)
        self.step3.validity_changed.connect(self._on_validity_changed)

        self.stack.addWidget(self.step1)
        self.stack.addWidget(self.step2)
        self.stack.addWidget(self.step3)
        self.stack.addWidget(self.review)

        content_layout.addWidget(self.stack)
        root.addWidget(content, 1)

        # Nav buttons
        nav_frame = QFrame()
        nav_frame.setStyleSheet(
            "QFrame { background: white; border-top: 1px solid #EEEEEE; }"
        )
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(30, 10, 30, 10)

        self.btn_back = QPushButton("← Kembali")
        self.btn_back.setFixedHeight(40)
        self.btn_back.setMinimumWidth(120)
        self.btn_back.setStyleSheet(
            "QPushButton { background: #E0E0E0; color: #333; border-radius: 6px;"
            " font-size: 13px; font-weight: bold; }"
            "QPushButton:hover { background: #BDBDBD; }"
        )
        self.btn_back.clicked.connect(self._go_back)

        self.btn_next = QPushButton("Lanjut →")
        self.btn_next.setFixedHeight(40)
        self.btn_next.setMinimumWidth(120)
        self.btn_next.setStyleSheet(
            "QPushButton { background: #2196F3; color: white; border-radius: 6px;"
            " font-size: 13px; font-weight: bold; }"
            "QPushButton:hover { background: #1976D2; }"
            "QPushButton:disabled { background: #B0BEC5; color: #ECEFF1; }"
        )
        self.btn_next.clicked.connect(self._go_next)

        nav_layout.addWidget(self.btn_back)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_next)
        root.addWidget(nav_frame)

        # Status bar
        self.status_bar = QLabel("Step 1 dari 3 — Lengkapi semua field untuk melanjutkan")
        self.status_bar.setStyleSheet(
            "color: #333333; font-size: 11px; padding: 4px 16px 6px 16px;"
            " background: #FAFAFA; border-top: 1px solid #EEEEEE;"
        )
        root.addWidget(self.status_bar)

    # ── Navigation ──────────────────────────────
    def _go_next(self):
        if self.current_step < 3:
            prev = self.current_step
            self.current_step += 1
            self.signals.step_completed.emit(prev)
            self.signals.step_changed.emit(prev, self.current_step)
        elif self.current_step == 3:
            # Submit
            self._collect_all_data()
            self.signals.form_submitted.emit(self.form_data)

    def _go_back(self):
        if self.current_step > 0:
            prev = self.current_step
            self.current_step -= 1
            self.signals.step_changed.emit(prev, self.current_step)

    # ── Signal Handlers ─────────────────────────
    def _on_step_changed(self, from_step: int, to_step: int):
        print(f"[Signal] Pindah dari step {from_step + 1} ke step {to_step + 1}")

        if to_step == 3:
            # Halaman review
            self._collect_all_data()
            self.review.populate(self.form_data)
            self.stack.setCurrentIndex(3)
        else:
            self.stack.setCurrentIndex(to_step)

        self.progress.set_step(to_step if to_step < 3 else 2)
        self._update_nav_buttons()

    def _on_step_completed(self, step: int):
        print(f"[Signal] Step {step + 1} selesai!")
        self.progress.mark_completed(step)

    def _on_form_submitted(self, data: dict):
        print("[Signal] Form berhasil di-submit!")
        print("Data:", data)
        # Tampilkan dialog sukses sederhana
        self._show_success()

    def _on_validity_changed(self, valid: bool):
        self._update_nav_buttons()

    # ── Helpers ─────────────────────────────────
    def _update_nav_buttons(self):
        step = self.current_step

        # Tombol back
        self.btn_back.setVisible(step > 0)

        if step == 0:
            valid = self.step1.nama.is_valid and (
                self.step1.jk_group.checkedId() != -1)
        elif step == 1:
            valid = (self.step2.email.is_valid and
                     self.step2.telepon.is_valid and
                     self.step2.alamat.is_valid)
        elif step == 2:
            valid = (self.step3.username.is_valid and
                     self.step3.password.is_valid and
                     self.step3.confirm.is_valid)
        else:
            valid = True   # Review page — selalu bisa submit

        self.btn_next.setEnabled(valid)

        if step < 3:
            self.btn_next.setText("Lanjut →")
            self.status_bar.setText(
                f"Step {step + 1} dari 3 — "
                f"{'Lengkapi semua field untuk melanjutkan' if not valid else 'Klik Lanjut untuk melanjutkan'}"
            )
        else:
            self.btn_next.setText("Submit ✓")
            self.status_bar.setText("Review data Anda lalu klik Submit")

    def _collect_all_data(self):
        self.form_data = {}
        self.form_data.update(self.step1.get_data())
        self.form_data.update(self.step2.get_data())
        self.form_data.update(self.step3.get_data())

    def _show_success(self):
        """Tampilkan halaman sukses sederhana."""
        win = QWidget(self)
        win.setGeometry(0, 0, self.width(), self.height())
        win.setStyleSheet("background: rgba(255,255,255,0.97);")
        lyt = QVBoxLayout(win)
        lyt.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel("✅")
        icon.setFont(QFont("Arial", 48))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        msg = QLabel("Registrasi Berhasil!")
        msg.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setStyleSheet("color: #4CAF50;")

        sub = QLabel(f"Selamat datang, {self.form_data.get('nama', '')}!")
        sub.setFont(QFont("Arial", 12))
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: #222222;")

        btn_close = QPushButton("Tutup")
        btn_close.setFixedWidth(160)
        btn_close.setFixedHeight(40)
        btn_close.setStyleSheet(
            "QPushButton { background: #2196F3; color: white; border-radius: 8px;"
            " font-size: 13px; font-weight: bold; }"
            "QPushButton:hover { background: #1976D2; }"
        )
        btn_close.clicked.connect(win.close)

        lyt.addWidget(icon)
        lyt.addWidget(msg)
        lyt.addWidget(sub)
        lyt.addSpacing(20)
        lyt.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)

        win.show()
        win.raise_()


# ─────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    palette = app.palette()
    palette.setColor(QPalette.ColorRole.WindowText,      QColor("#111111"))
    palette.setColor(QPalette.ColorRole.Text,            QColor("#111111"))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor("#111111"))
    palette.setColor(QPalette.ColorRole.ToolTipText,     QColor("#111111"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#AAAAAA"))
    palette.setColor(QPalette.ColorRole.Window,          QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.Base,            QColor("#FFFFFF"))
    app.setPalette(palette)

    window = FormRegistrasi()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
