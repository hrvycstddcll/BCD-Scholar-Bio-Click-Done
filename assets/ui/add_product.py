import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QDoubleSpinBox, QSpinBox, QTextEdit,
    QMessageBox, QFrame, QSizePolicy, QComboBox, QFileDialog,
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QPainter, QBrush, QLinearGradient, QPainterPath, QPixmap

import styles
from styles import AMBER, ORANGE, CAT_ICONS, combo_style, input_style, spinbox_style, msgbox_style
from database.database import get_connection, image_path_to_blob

def _c(k): return styles.c(k)

CATEGORIES = [
    "Electronics", "Clothing", "Food & Beverage", "Office Supplies",
    "Sports & Fitness", "Home & Garden", "Beauty & Personal Care",
    "Toys & Games", "Health & Wellness", "Tools & Hardware", "Other",
]
PRESET_TAGS = ["New Arrival", "Best Seller", "On Sale", "Featured", "Imported", "Local"]

# ── Glass card ────────────────────────────────────────────────
class _GCard(QWidget):
    def __init__(self, radius=14, parent=None):
        super().__init__(parent)
        self._r = radius
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h, r, pad = self.width(), self.height(), self._r, 7
        for i in range(5, 0, -1):
            sp = i * 2; a = max(0, 8 - i)
            sh = QColor(180, 130, 30, a) if not styles.is_dark() else QColor(0, 0, 0, a * 2)
            p.setBrush(QBrush(sh)); p.setPen(Qt.NoPen)
            sp_path = QPainterPath()
            sp_path.addRoundedRect(QRectF(pad-sp, pad+sp//2, w-pad*2+sp*2, h-pad*2+sp), r+sp//2, r+sp//2)
            p.drawPath(sp_path)
        grad = QLinearGradient(0, pad, 0, h - pad)
        if styles.is_dark():
            grad.setColorAt(0.0, QColor(32, 34, 46, 245))
            grad.setColorAt(1.0, QColor(24, 26, 36, 245))
        else:
            grad.setColorAt(0.0, QColor(255, 255, 255, 252))
            grad.setColorAt(0.6, QColor(255, 253, 244, 250))
            grad.setColorAt(1.0, QColor(255, 249, 230, 248))
        p.setBrush(QBrush(grad)); p.setPen(Qt.NoPen)
        card = QPainterPath()
        card.addRoundedRect(QRectF(pad, pad, w-pad*2, h-pad*2), r, r)
        p.drawPath(card)
        sheen = QLinearGradient(0, pad, 0, pad + 26)
        sheen.setColorAt(0.0, QColor(255, 255, 255, 75 if not styles.is_dark() else 18))
        sheen.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(sheen))
        sh2 = QPainterPath()
        sh2.addRoundedRect(QRectF(pad, pad, w-pad*2, 26), r, r)
        p.drawPath(sh2)
        p.end()


# ── Image preview ──────────────────────────────────────────────
class ImagePreview(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._img_path = ""
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCursor(Qt.PointingHandCursor)
        self.setAcceptDrops(True)
        self._set_empty()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._placeholder = QLabel("📷\nClick or drop image here")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setStyleSheet(
            f"color:{_c('TEXT_MUTED')};font-size:13px;font-weight:500;"
            f"background:transparent;border:none;")
        lay.addWidget(self._placeholder, 1)

        self._img_lbl = QLabel()
        self._img_lbl.setAlignment(Qt.AlignCenter)
        self._img_lbl.setStyleSheet("background:transparent;border:none;")
        self._img_lbl.hide()
        lay.addWidget(self._img_lbl, 1)

        rm_row = QHBoxLayout()
        rm_row.setContentsMargins(8, 4, 8, 8)
        self._rm_btn = QPushButton("✕  Remove")
        self._rm_btn.setFixedHeight(28)
        self._rm_btn.setCursor(Qt.PointingHandCursor)
        self._rm_btn.setStyleSheet(
            f"QPushButton{{background:rgba(0,0,0,0.50);color:white;border:none;"
            f"border-radius:8px;font-size:11px;font-weight:600;padding:0 12px;}}"
            f"QPushButton:hover{{background:{_c('DANGER')};color:white;}}")
        self._rm_btn.clicked.connect(self.clear_image)
        self._rm_btn.hide()
        rm_row.addStretch()
        rm_row.addWidget(self._rm_btn)
        rm_w = QWidget()
        rm_w.setStyleSheet("background:transparent;")
        rm_w.setLayout(rm_row)
        self._rm_w = rm_w
        self._rm_w.hide()
        lay.addWidget(self._rm_w)

    def _set_empty(self):
        self.setStyleSheet(
            "QFrame{background:rgba(245,158,11,0.05);"
            "border:2px dashed rgba(245,158,11,0.40);border-radius:12px;}")

    def _set_filled(self):
        self.setStyleSheet("QFrame{background:#141414;border:none;border-radius:12px;}")

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls(): e.acceptProposedAction()

    def dropEvent(self, e):
        for url in e.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')):
                self.load_image(path); break

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and not self._img_path:
            self._browse()

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if path: self.load_image(path)

    def load_image(self, path):
        px = QPixmap(path)
        if px.isNull(): return
        self._img_path = path
        self._refresh_pixmap()
        self._placeholder.hide()
        self._img_lbl.show()
        self._rm_w.show()
        self._rm_btn.show()
        self._set_filled()

    def _refresh_pixmap(self):
        if not self._img_path: return
        px = QPixmap(self._img_path)
        if px.isNull(): return
        scaled = px.scaled(
            max(40, self.width() - 8),
            max(40, self.height() - 44),
            Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._img_lbl.setPixmap(scaled)

    def clear_image(self):
        self._img_path = ""
        self._img_lbl.clear()
        self._img_lbl.hide()
        self._rm_w.hide()
        self._rm_btn.hide()
        self._placeholder.show()
        self._set_empty()

    def image_path(self): return self._img_path
    def resizeEvent(self, e): self._refresh_pixmap(); super().resizeEvent(e)


# ── Tag chip ──────────────────────────────────────────────────
class TagChip(QWidget):
    def __init__(self, text, on_remove, parent=None):
        super().__init__(parent)
        self._text = text
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 3, 6, 3)
        lay.setSpacing(4)
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color:{AMBER};font-size:11px;font-weight:600;"
            f"background:transparent;border:none;")
        btn = QPushButton("×")
        btn.setFixedSize(16, 16)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton{{background:transparent;color:{AMBER};border:none;"
            f"font-size:13px;font-weight:700;padding:0;}}"
            f"QPushButton:hover{{color:{ORANGE};}}")
        btn.clicked.connect(lambda: on_remove(text))
        lay.addWidget(lbl)
        lay.addWidget(btn)
        self.setStyleSheet(
            "QWidget{background:rgba(245,158,11,0.13);"
            "border:none;border-radius:10px;}")
        self.setFixedHeight(24)

    def tag_text(self): return self._text


class FlowWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._chips = []
        self._lay = QHBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(6)
        self._lay.addStretch()

    def add_tag(self, text, on_remove=None):
        text = text.strip()
        if not text: return
        if any(c.tag_text() == text for c in self._chips): return
        chip = TagChip(text, on_remove or self.remove_tag)
        self._lay.insertWidget(self._lay.count() - 1, chip)
        self._chips.append(chip)

    def remove_tag(self, text):
        for chip in self._chips[:]:
            if chip.tag_text() == text:
                self._lay.removeWidget(chip)
                chip.deleteLater()
                self._chips.remove(chip)

    def get_tags(self): return [c.tag_text() for c in self._chips]

    def clear_all(self):
        for chip in self._chips[:]: self.remove_tag(chip.tag_text())


# ── Small helpers ─────────────────────────────────────────────
def _lbl(text, required=False):
    l = QLabel(text + (" *" if required else ""))
    l.setStyleSheet(
        f"color:{_c('TEXT_MUTED')};font-size:11px;font-weight:700;"
        f"letter-spacing:0.5px;background:transparent;border:none;")
    return l


def _section(text):
    l = QLabel(text)
    l.setStyleSheet(
        f"font-size:14px;font-weight:800;color:{_c('TEXT_PRIMARY')};"
        f"background:transparent;border:none;")
    return l


def _sep():
    f = QFrame()
    f.setFixedHeight(1)
    f.setStyleSheet("background:rgba(245,158,11,0.14);border:none;")
    return f


def _field(placeholder="", height=42):
    w = QLineEdit()
    w.setPlaceholderText(placeholder)
    w.setFixedHeight(height)
    w.setCursor(Qt.IBeamCursor)
    w.setStyleSheet(input_style())
    return w


def _spin_style(widget):
    """Apply solid input style to QSpinBox / QDoubleSpinBox."""
    widget.setStyleSheet(spinbox_style())


# ══════════════════════════════════════════════════════════════
#  ADD PRODUCT TAB
# ══════════════════════════════════════════════════════════════
class AddProductTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 20, 28, 16)
        root.setSpacing(14)

        # ── Header ────────────────────────────────────────
        hdr = QHBoxLayout()
        title = QLabel("Add Product"); title.setProperty("title", True)
        sub   = QLabel("Fill in the details below to list a new product")
        sub.setProperty("subtitle", True)
        hv = QVBoxLayout(); hv.setSpacing(2)
        hv.addWidget(title); hv.addWidget(sub)
        hdr.addLayout(hv, 1)

        req = QLabel("* Required")
        req.setStyleSheet(
            f"font-size:11px;color:{_c('TEXT_MUTED')};"
            f"background:transparent;border:none;")
        hdr.addWidget(req, 0, Qt.AlignVCenter)
        root.addLayout(hdr)

        # ── Two equal columns ─────────────────────────────
        cols = QHBoxLayout()
        cols.setSpacing(16)

        # ═══════════ LEFT COLUMN ═════════════════════════
        left = QVBoxLayout(); left.setSpacing(12)

        # — Image card (takes ~40% of left height) —
        img_card = _GCard(radius=14)
        il = QVBoxLayout(img_card)
        il.setContentsMargins(16, 14, 16, 14); il.setSpacing(10)
        il.addWidget(_section("Product Image"))
        il.addWidget(_sep())

        self._img_preview = ImagePreview()
        self._img_preview.setMinimumHeight(160)
        il.addWidget(self._img_preview, 1)

        browse_row = QHBoxLayout(); browse_row.setSpacing(8)
        img_hint = QLabel("PNG  ·  JPG  ·  WEBP  ·  BMP")
        img_hint.setStyleSheet(
            f"font-size:10px;color:{_c('TEXT_MUTED')};"
            f"background:transparent;border:none;")
        btn_browse = QPushButton("BROWSE")
        btn_browse.setFixedHeight(32); btn_browse.setFixedWidth(90)
        btn_browse.setCursor(Qt.PointingHandCursor)
        btn_browse.setStyleSheet(
            f"QPushButton{{background:rgba(245,158,11,0.14);color:{AMBER};"
            f"border:none;border-radius:8px;padding:10px;font-size:12px;font-weight:700;}}"
            f"QPushButton:hover{{background:rgba(245,158,11,0.28);}}")
        btn_browse.clicked.connect(self._img_preview._browse)
        browse_row.addWidget(img_hint, 1)
        browse_row.addWidget(btn_browse)
        il.addLayout(browse_row)
        left.addWidget(img_card, 2)   # 2-parts height

        # — Info card (takes ~60% of left height) —
        info_card = _GCard(radius=14)
        info_lay = QVBoxLayout(info_card)
        info_lay.setContentsMargins(16, 14, 16, 16); info_lay.setSpacing(10)
        info_lay.addWidget(_section("Product Information"))
        info_lay.addWidget(_sep())

        info_lay.addWidget(_lbl("Product Name", required=True))
        self.inp_name = _field("e.g. Wireless Ergonomic Mouse")
        info_lay.addWidget(self.inp_name)

        # Category + Sub-category row
        cat_row = QHBoxLayout(); cat_row.setSpacing(12)

        cat_col = QVBoxLayout(); cat_col.setSpacing(6)
        cat_col.addWidget(_lbl("Category", required=True))
        self.cmb_category = QComboBox()
        self.cmb_category.addItems(["Select category…"] + CATEGORIES)
        self.cmb_category.setFixedHeight(42)
        self.cmb_category.setCursor(Qt.PointingHandCursor)
        self.cmb_category.setStyleSheet(combo_style())
        cat_col.addWidget(self.cmb_category)

        sub_col = QVBoxLayout(); sub_col.setSpacing(6)
        sub_col.addWidget(_lbl("Sub-category"))
        self.inp_sub = _field("e.g. Gaming")
        sub_col.addWidget(self.inp_sub)

        cat_row.addLayout(cat_col, 1)
        cat_row.addLayout(sub_col, 1)
        info_lay.addLayout(cat_row)

        info_lay.addWidget(_lbl("Description"))
        self.inp_desc = QTextEdit()
        self.inp_desc.setPlaceholderText("Features, dimensions, material…")
        self.inp_desc.setMinimumHeight(80)
        self.inp_desc.setCursor(Qt.IBeamCursor)
        self.inp_desc.setStyleSheet(
            f"QTextEdit{{background:{_c('INPUT_BG')};border:1.5px solid {_c('BORDER')};"
            f"border-radius:10px;padding:10px 14px;"
            f"color:{_c('TEXT_PRIMARY')};font-size:13px;}}"
            f"QTextEdit:focus{{border:1.5px solid {AMBER};}}")
        info_lay.addWidget(self.inp_desc, 1)
        left.addWidget(info_card, 3)   # 3-parts height

        # ═══════════ RIGHT COLUMN ════════════════════════
        right = QVBoxLayout(); right.setSpacing(12)

        # — Pricing & Stock card —
        price_card = _GCard(radius=14)
        pl = QVBoxLayout(price_card)
        pl.setContentsMargins(16, 14, 16, 16); pl.setSpacing(10)
        pl.addWidget(_section("Pricing & Stock"))
        pl.addWidget(_sep())

        pl.addWidget(_lbl("Unit Price (PHP)", required=True))
        self.inp_price = QDoubleSpinBox()
        self.inp_price.setPrefix("PHP ")
        self.inp_price.setMaximum(999_999.99)
        self.inp_price.setDecimals(2)
        self.inp_price.setSingleStep(10)
        self.inp_price.setFixedHeight(44)
        self.inp_price.setCursor(Qt.PointingHandCursor)
        _spin_style(self.inp_price)
        pl.addWidget(self.inp_price)

        pl.addWidget(_lbl("Initial Stock Quantity"))
        self.inp_stock = QSpinBox()
        self.inp_stock.setMinimum(0)
        self.inp_stock.setMaximum(999_999)
        self.inp_stock.setFixedHeight(44)
        self.inp_stock.setCursor(Qt.PointingHandCursor)
        _spin_style(self.inp_stock)
        pl.addWidget(self.inp_stock)

        # Stock quick-set buttons
        qrow = QHBoxLayout(); qrow.setSpacing(8)
        pl.addWidget(_lbl("Quick Set Stock"))
        for n in [0, 10, 50, 100]:
            b = QPushButton(str(n))
            b.setFixedHeight(34)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(
                f"QPushButton{{background:rgba(245,158,11,0.10);color:{AMBER};"
                f"border:none;border-radius:8px;font-size:12px;font-weight:700;}}"
                f"QPushButton:hover{{background:rgba(245,158,11,0.26);}}"
                f"QPushButton:pressed{{background:{AMBER};color:#111;}}")
            b.clicked.connect(lambda _, v=n: self.inp_stock.setValue(v))
            qrow.addWidget(b)
        pl.addLayout(qrow)

        stock_note = QLabel("Stock 0 = pre-listed, not yet in inventory.")
        stock_note.setStyleSheet(
            f"font-size:10px;color:{_c('TEXT_MUTED')};"
            f"background:transparent;border:none;")
        pl.addWidget(stock_note)
        pl.addStretch()
        right.addWidget(price_card, 2)

        # — Tags card —
        tags_card = _GCard(radius=14)
        tl = QVBoxLayout(tags_card)
        tl.setContentsMargins(16, 14, 16, 14); tl.setSpacing(10)
        tl.addWidget(_section("Tags"))
        tl.addWidget(_sep())

        tag_input_row = QHBoxLayout(); tag_input_row.setSpacing(8)
        self.inp_tag = QLineEdit()
        self.inp_tag.setPlaceholderText("Type a tag and press Enter…")
        self.inp_tag.setFixedHeight(38)
        self.inp_tag.setCursor(Qt.IBeamCursor)
        self.inp_tag.setStyleSheet(input_style())
        self.inp_tag.returnPressed.connect(self._add_tag)
        btn_at = QPushButton("ADD")
        btn_at.setFixedSize(60, 38)
        btn_at.setCursor(Qt.PointingHandCursor)
        btn_at.setStyleSheet(
            f"QPushButton{{background:{AMBER};color:#111;border:none;"
            f"border-radius:8px;padding:10px;font-size:12px;font-weight:700;}}"
            f"QPushButton:hover{{background:#FBBF24;}}")
        btn_at.clicked.connect(self._add_tag)
        tag_input_row.addWidget(self.inp_tag, 1)
        tag_input_row.addWidget(btn_at)
        tl.addLayout(tag_input_row)

        self._tag_flow = FlowWidget()
        self._tag_flow.setFixedHeight(28)
        self._tag_flow.setStyleSheet("background:transparent;border:none;")
        tl.addWidget(self._tag_flow)

        pre_row = QHBoxLayout(); pre_row.setSpacing(6)
        for tag in PRESET_TAGS:
            b = QPushButton(tag)
            b.setFixedHeight(24)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(
                f"QPushButton{{background:rgba(245,158,11,0.10);color:{AMBER};"
                f"border:none;border-radius:12px;font-size:10px;font-weight:600;"
                f"padding:0 10px;}}"
                f"QPushButton:hover{{background:rgba(245,158,11,0.26);}}")
            b.clicked.connect(lambda _, t=tag: self._tag_flow.add_tag(t))
            pre_row.addWidget(b)
        pre_row.addStretch()
        tl.addLayout(pre_row)
        right.addWidget(tags_card, 1)

        # — Actions card —
        act_card = _GCard(radius=14)
        al = QVBoxLayout(act_card)
        al.setContentsMargins(16, 16, 16, 16); al.setSpacing(12)

        self.btn_add = QPushButton("Publish Product")
        self.btn_add.setFixedHeight(52)
        self.btn_add.setCursor(Qt.PointingHandCursor)
        self.btn_add.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {AMBER},stop:1 {ORANGE});color:#111111;border:none;"
            f"border-radius:12px;font-size:15px;font-weight:800;"
            f"letter-spacing:0.3px;}}"
            f"QPushButton:hover{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 #FBBF24,stop:1 {AMBER});}}"
            f"QPushButton:pressed{{background:{ORANGE};color:white;}}")

        self.btn_clear = QPushButton("Clear Form")
        self.btn_clear.setFixedHeight(40)
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.setStyleSheet(
            f"QPushButton{{background:transparent;color:{_c('TEXT_MUTED')};"
            f"border:1.5px solid {_c('BORDER')};border-radius:10px;"
            f"font-size:13px;font-weight:600;}}"
            f"QPushButton:hover{{border-color:{AMBER};color:{AMBER};}}")

        self.btn_add.clicked.connect(self.add_product)
        self.btn_clear.clicked.connect(self.clear_form)
        al.addWidget(self.btn_add)
        al.addWidget(self.btn_clear)
        right.addWidget(act_card)

        cols.addLayout(left, 1)
        cols.addLayout(right, 1)
        root.addLayout(cols, 1)

    # ── Logic ─────────────────────────────────────────────
    def _add_tag(self):
        tag = self.inp_tag.text().strip()
        if tag:
            self._tag_flow.add_tag(tag)
            self.inp_tag.clear()

    def _get_image_blob(self, src):
        """Convert selected image file to PNG bytes for DB storage."""
        return image_path_to_blob(src)

    def add_product(self):
        name    = self.inp_name.text().strip()
        cat_idx = self.cmb_category.currentIndex()
        cat     = self.cmb_category.currentText() if cat_idx > 0 else ""
        price   = self.inp_price.value()
        stock   = self.inp_stock.value()

        if not name:
            mb = QMessageBox(self)
            mb.setWindowTitle("Required Field")
            mb.setText("Product Name is required.")
            mb.setStyleSheet(msgbox_style())
            mb.exec_()
            self.inp_name.setFocus()
            return
        if not cat:
            mb = QMessageBox(self)
            mb.setWindowTitle("Required Field")
            mb.setText("Please select a Category.")
            mb.setStyleSheet(msgbox_style())
            mb.exec_()
            self.cmb_category.setFocus()
            return

        img_blob = self._get_image_blob(self._img_preview.image_path())
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO products (name,category,price,stock,image_data) VALUES (?,?,?,?,?)",
                (name, cat, price, stock, img_blob))

        mb = QMessageBox(self)
        mb.setWindowTitle("Product Published")
        mb.setText(
            f"'{name}' has been added!\n\n"
            f"Category : {cat}\n"
            f"Price    : PHP {price:,.2f}\n"
            f"Stock    : {stock}")
        mb.setStyleSheet(msgbox_style())
        mb.exec_()
        self.clear_form()

    def clear_form(self):
        self.inp_name.clear()
        self.cmb_category.setCurrentIndex(0)
        self.inp_sub.clear()
        self.inp_desc.clear()
        self.inp_price.setValue(0)
        self.inp_stock.setValue(0)
        self.inp_tag.clear()
        self._tag_flow.clear_all()
        self._img_preview.clear_image()
        self.inp_name.setFocus()

    def refresh(self): pass
