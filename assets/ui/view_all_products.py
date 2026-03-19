"""
Products tab — inventory table layout.
Each row: thumbnail | id | name | category | price | stock progress bar | qty | status | actions.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QSizePolicy, QScrollArea,
    QComboBox, QSpinBox, QDialog, QFileDialog, QDoubleSpinBox,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath, QColor

import styles
from styles import AMBER, ORANGE, CAT_ICONS, combo_style, input_style
from database.database import get_connection, image_path_to_blob, blob_to_pixmap

CATEGORIES = [
    "Electronics", "Clothing", "Food & Beverage", "Office Supplies",
    "Sports & Fitness", "Home & Garden", "Beauty & Personal Care",
    "Toys & Games", "Health & Wellness", "Tools & Hardware", "Other",
]


# ═══════════════════════════════════════════════════════════════
#  SHARED DIALOG BASE
# ═══════════════════════════════════════════════════════════════
class _BaseDialog(QDialog):
    def __init__(self, parent=None, width=400):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)
        self.setFixedWidth(width)
        self._apply_card_style()
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(28, 24, 28, 24)
        self._root.setSpacing(0)

    def _apply_card_style(self):
        bg  = styles.c("CARD_BG"); bd = styles.c("BORDER"); txt = styles.c("TEXT_PRIMARY")
        self.setStyleSheet(
            f"QDialog{{background:{bg};border:2px solid {bd};border-radius:18px;}}"
            f"QLabel{{background:transparent;border:none;color:{txt};}}"
            f"QLineEdit{{background:{styles.c('INPUT_BG')};border:1.5px solid {bd};"
            f"border-radius:10px;padding:0 14px;color:{txt};font-size:13px;min-height:40px;}}"
            f"QLineEdit:focus{{border:1.5px solid {AMBER};}}"
            f"QSpinBox,QDoubleSpinBox{{background:{styles.c('INPUT_BG')};border:1.5px solid {bd};"
            f"border-radius:10px;padding:0 12px;color:{txt};font-size:14px;font-weight:700;min-height:40px;}}"
            f"QSpinBox:focus,QDoubleSpinBox:focus{{border:1.5px solid {AMBER};}}"
            f"QSpinBox::up-button,QSpinBox::down-button,QDoubleSpinBox::up-button,QDoubleSpinBox::down-button"
            f"{{border:none;background:transparent;width:20px;}}"
            f"QComboBox{{background:{styles.c('INPUT_BG')};border:1.5px solid {bd};"
            f"border-radius:10px;padding:0 14px;color:{txt};font-size:13px;min-height:42px;}}"
            f"QComboBox:focus,QComboBox:on{{border:1.5px solid {AMBER};}}"
            f"QComboBox::drop-down{{border:none;background:rgba(245,158,11,0.12);"
            f"border-top-right-radius:9px;border-bottom-right-radius:9px;width:32px;}}"
            f"QComboBox::down-arrow{{image:none;width:0;height:0;"
            f"border-left:5px solid transparent;border-right:5px solid transparent;"
            f"border-top:6px solid {AMBER};}}"
            f"QComboBox QAbstractItemView{{background:{bg};border:1.5px solid {bd};"
            f"border-radius:10px;outline:none;color:{txt};font-size:13px;"
            f"selection-background-color:rgba(245,158,11,0.18);}}"
            f"QComboBox QAbstractItemView::item{{padding:10px 14px;min-height:34px;}}"
            f"QComboBox QAbstractItemView::item:hover{{background:rgba(245,158,11,0.12);color:{AMBER};}}")

    def _title(self, text):
        l = QLabel(text)
        l.setStyleSheet(f"font-size:17px;font-weight:800;color:{styles.c('TEXT_PRIMARY')};background:transparent;border:none;")
        return l

    def _subtitle(self, text):
        l = QLabel(text); l.setWordWrap(True)
        l.setStyleSheet(f"font-size:12px;color:{styles.c('TEXT_MUTED')};background:transparent;border:none;")
        return l

    def _sep(self):
        f = QFrame(); f.setFixedHeight(1)
        f.setStyleSheet("background:rgba(245,158,11,0.20);border:none;")
        return f

    def _cap(self, text):
        l = QLabel(text)
        l.setStyleSheet(f"font-size:10px;font-weight:700;letter-spacing:0.8px;color:{styles.c('TEXT_MUTED')};background:transparent;border:none;")
        return l

    def _btn_primary(self, text):
        b = QPushButton(text); b.setFixedHeight(44); b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {AMBER},stop:1 {ORANGE});"
            f"color:#111;border:none;border-radius:10px;font-size:14px;font-weight:800;}}"
            f"QPushButton:hover{{background:{AMBER};}}"
            f"QPushButton:pressed{{background:{ORANGE};color:white;}}")
        return b

    def _btn_secondary(self, text):
        b = QPushButton(text); b.setFixedHeight(44); b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet(
            f"QPushButton{{background:transparent;color:{styles.c('TEXT_MUTED')};"
            f"border:1.5px solid {styles.c('BORDER')};border-radius:10px;font-size:13px;font-weight:600;}}"
            f"QPushButton:hover{{border-color:{AMBER};color:{AMBER};}}")
        return b

    def _btn_danger(self, text):
        b = QPushButton(text); b.setFixedHeight(44); b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet(
            f"QPushButton{{background:transparent;color:{styles.c('DANGER')};"
            f"border:1.5px solid {styles.c('DANGER')};border-radius:10px;font-size:13px;font-weight:700;}}"
            f"QPushButton:hover{{background:{styles.c('DANGER')};color:white;}}")
        return b

    def sp(self, px):
        s = QWidget(); s.setFixedHeight(px); s.setStyleSheet("background:transparent;border:none;")
        self._root.addWidget(s)


class ConfirmDialog(_BaseDialog):
    def __init__(self, title, message, confirm_text="Confirm", danger=False, parent=None):
        super().__init__(parent, width=420)
        r = self._root
        icon = QLabel("⚠" if danger else "ℹ")
        icon.setFixedSize(52, 52); icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(f"font-size:28px;background:rgba(245,158,11,0.10);border-radius:24px;padding:10px;border:none;color:{'#EF4444' if danger else AMBER};")
        hdr = QHBoxLayout(); hdr.setSpacing(14); hdr.addWidget(icon, 0, Qt.AlignVCenter)
        r.addLayout(hdr); self.sp(6); r.addWidget(self._title(title)); self.sp(16)
        msg = QLabel(message); msg.setWordWrap(True)
        msg.setStyleSheet(f"font-size:13px;color:{styles.c('TEXT_PRIMARY')};background:transparent;border:none;line-height:1.5;")
        r.addWidget(msg); self.sp(20); r.addWidget(self._sep()); self.sp(16)
        btns = QHBoxLayout(); btns.setSpacing(10)
        cancel = self._btn_secondary("Cancel"); cancel.clicked.connect(self.reject)
        ok = self._btn_danger(confirm_text) if danger else self._btn_primary(confirm_text)
        ok.clicked.connect(self.accept)
        btns.addWidget(cancel, 1); btns.addWidget(ok, 2); r.addLayout(btns)


class InfoDialog(_BaseDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(parent, width=380)
        r = self._root; r.addWidget(self._title(title)); self.sp(10); r.addWidget(self._sep()); self.sp(14)
        msg = QLabel(message); msg.setWordWrap(True)
        msg.setStyleSheet(f"font-size:13px;color:{styles.c('TEXT_PRIMARY')};background:transparent;border:none;")
        r.addWidget(msg); self.sp(20)
        ok = self._btn_primary("OK"); ok.clicked.connect(self.accept); r.addWidget(ok)


# ═══════════════════════════════════════════════════════════════
#  EDIT PRODUCT DIALOG
# ═══════════════════════════════════════════════════════════════
class EditProductDialog(_BaseDialog):
    def __init__(self, row: list, parent=None):
        super().__init__(parent, width=480)
        self._pid = row[0]; self._img_blob = row[6] if len(row) > 6 else None; self._new_img = ""
        r = self._root
        hdr_row = QHBoxLayout(); hdr_row.setSpacing(12)
        badge = QLabel("✎"); badge.setFixedSize(40, 40); badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(f"background:rgba(245,158,11,0.14);color:{AMBER};font-size:18px;border-radius:12px;border:none;")
        hdr_row.addWidget(badge); hdr_row.addWidget(self._title("Edit Product"), 1)
        r.addLayout(hdr_row); self.sp(6)
        r.addWidget(self._subtitle(f"ID #{row[0]}  ·  added {row[5][:10] if row[5] else ''}"))
        self.sp(14); r.addWidget(self._sep()); self.sp(16)
        r.addWidget(self._cap("PRODUCT IMAGE")); self.sp(6)
        img_row = QHBoxLayout(); img_row.setSpacing(12)
        self._img_thumb = QLabel(); self._img_thumb.setFixedSize(80, 80); self._img_thumb.setAlignment(Qt.AlignCenter)
        self._refresh_thumb(); img_row.addWidget(self._img_thumb)
        img_btns = QVBoxLayout(); img_btns.setSpacing(8)
        btn_pick = QPushButton("Change Image…"); btn_pick.setFixedHeight(36); btn_pick.setCursor(Qt.PointingHandCursor)
        btn_pick.setStyleSheet(f"QPushButton{{background:rgba(245,158,11,0.12);color:{AMBER};border:none;border-radius:8px;font-size:12px;font-weight:700;}}QPushButton:hover{{background:rgba(245,158,11,0.28);}}")
        btn_pick.clicked.connect(self._pick_image)
        btn_clear = QPushButton("Remove Image"); btn_clear.setFixedHeight(36); btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.setStyleSheet(f"QPushButton{{background:transparent;color:{styles.c('TEXT_MUTED')};border:1px solid {styles.c('BORDER')};border-radius:8px;font-size:12px;font-weight:600;}}QPushButton:hover{{border-color:{styles.c('DANGER')};color:{styles.c('DANGER')};}}")
        btn_clear.clicked.connect(self._clear_image)
        img_btns.addWidget(btn_pick); img_btns.addWidget(btn_clear); img_btns.addStretch()
        img_row.addLayout(img_btns, 1); r.addLayout(img_row); self.sp(16); r.addWidget(self._sep()); self.sp(16)
        r.addWidget(self._cap("PRODUCT NAME")); self.sp(6)
        self.inp_name = QLineEdit(row[1]); r.addWidget(self.inp_name); self.sp(12)
        r.addWidget(self._cap("CATEGORY")); self.sp(6)
        self.cmb_cat = QComboBox(); self.cmb_cat.addItems(CATEGORIES)
        idx = self.cmb_cat.findText(row[2])
        if idx >= 0: self.cmb_cat.setCurrentIndex(idx)
        r.addWidget(self.cmb_cat); self.sp(12)
        ps_row = QHBoxLayout(); ps_row.setSpacing(12)
        pc = QVBoxLayout(); pc.setSpacing(6); pc.addWidget(self._cap("PRICE (PHP)"))
        self.inp_price = QDoubleSpinBox(); self.inp_price.setPrefix("PHP "); self.inp_price.setMaximum(999_999.99)
        self.inp_price.setDecimals(2); self.inp_price.setSingleStep(10); self.inp_price.setValue(float(row[3])); self.inp_price.setFixedHeight(44)
        pc.addWidget(self.inp_price)
        sc = QVBoxLayout(); sc.setSpacing(6); sc.addWidget(self._cap("STOCK"))
        self.inp_stock = QSpinBox(); self.inp_stock.setMinimum(0); self.inp_stock.setMaximum(999_999)
        self.inp_stock.setValue(int(row[4])); self.inp_stock.setFixedHeight(44)
        qa = QHBoxLayout(); qa.setSpacing(6)
        for d in [1, 5, 10, 50]:
            b = QPushButton(f"+{d}"); b.setFixedHeight(28); b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(f"QPushButton{{background:rgba(245,158,11,0.10);color:{AMBER};border:none;border-radius:7px;font-size:11px;font-weight:700;}}QPushButton:hover{{background:rgba(245,158,11,0.26);}}")
            b.clicked.connect(lambda _, v=d: self.inp_stock.setValue(self.inp_stock.value()+v)); qa.addWidget(b)
        sc.addWidget(self.inp_stock); sc.addLayout(qa)
        ps_row.addLayout(pc, 1); ps_row.addLayout(sc, 1); r.addLayout(ps_row)
        self.sp(20); r.addWidget(self._sep()); self.sp(16)
        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        cancel = self._btn_secondary("Cancel"); cancel.clicked.connect(self.reject)
        save = self._btn_primary("Save Changes"); save.clicked.connect(self._save)
        btn_row.addWidget(cancel, 1); btn_row.addWidget(save, 2); r.addLayout(btn_row)

    def _refresh_thumb(self):
        self._img_thumb.setStyleSheet(f"background:{styles.c('INPUT_BG')};border-radius:10px;border:1.5px solid {styles.c('BORDER')};color:{AMBER};font-size:28px;")
        px = None
        if self._new_img and os.path.exists(self._new_img): px = QPixmap(self._new_img)
        elif self._img_blob: px = blob_to_pixmap(self._img_blob)
        if px and not px.isNull():
            self._img_thumb.setPixmap(px.scaled(76, 76, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self._img_thumb.setStyleSheet("background:#141414;border-radius:10px;border:none;"); return
        self._img_thumb.setPixmap(QPixmap()); self._img_thumb.setText("📦")

    def _pick_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if path: self._new_img = path; self._refresh_thumb()

    def _clear_image(self):
        self._new_img = "__CLEAR__"; self._img_blob = None; self._img_thumb.setPixmap(QPixmap()); self._img_thumb.setText("📦")
        self._img_thumb.setStyleSheet(f"background:{styles.c('INPUT_BG')};border-radius:10px;border:1.5px solid {styles.c('BORDER')};color:{AMBER};font-size:28px;")

    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            self.inp_name.setFocus()
            self.inp_name.setStyleSheet(f"QLineEdit{{background:{styles.c('INPUT_BG')};border:1.5px solid #EF4444;border-radius:10px;padding:0 14px;color:{styles.c('TEXT_PRIMARY')};font-size:13px;min-height:40px;}}"); return
        self.accept()

    def get_values(self) -> dict:
        if self._new_img == "__CLEAR__": final_blob = None
        elif self._new_img and os.path.exists(self._new_img): final_blob = image_path_to_blob(self._new_img)
        else: final_blob = self._img_blob
        return {"name": self.inp_name.text().strip(), "category": self.cmb_cat.currentText(),
                "price": self.inp_price.value(), "stock": self.inp_stock.value(), "image_data": final_blob}



# ═══════════════════════════════════════════════════════════════
#  STOCK PROGRESS BAR  — tall version to match ROW_H 220
# ═══════════════════════════════════════════════════════════════
class StockProgressBar(QWidget):
    def __init__(self, stock, max_stock=100, parent=None):
        super().__init__(parent)
        self.stock = stock; self.max_stock = max(max_stock, 1)
        self.setFixedHeight(16)
        self.setMinimumWidth(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet("background:transparent;border:none;")

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        bar_h = 14; bar_y = (h - bar_h) // 2
        track = QPainterPath()
        track.addRoundedRect(0, bar_y, w, bar_h, bar_h//2, bar_h//2)
        p.setPen(Qt.NoPen); p.setBrush(QColor(styles.c("BORDER"))); p.drawPath(track)
        ratio = min(1.0, self.stock / self.max_stock)
        if ratio > 0:
            fill_w = max(bar_h, int(w * ratio))
            fill = QPainterPath()
            fill.addRoundedRect(0, bar_y, fill_w, bar_h, bar_h//2, bar_h//2)
            if self.stock == 0: color = QColor("#EF4444")
            elif self.stock <= 5: color = QColor("#F97316")
            elif ratio < 0.25: color = QColor("#FBBF24")
            else: color = QColor("#10B981")
            p.setBrush(color); p.drawPath(fill)
        p.end()


# ═══════════════════════════════════════════════════════════════
#  INVENTORY ROW  — ROW_H = 220, all elements scaled up
# ═══════════════════════════════════════════════════════════════
class InventoryRow(QFrame):
    ROW_H = 220

    def __init__(self, pid, name, category, price, stock, image_blob,
                 created_at="", max_stock=100, parent=None):
        super().__init__(parent)
        self._pid = pid; self._selected = False
        self.setFixedHeight(self.ROW_H)
        self.setCursor(Qt.PointingHandCursor)
        self._apply_style(False)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(22, 0, 22, 0)
        layout.setSpacing(0)

        # Thumbnail — fixed square, does not need to stretch
        thumb = QLabel(); thumb.setFixedSize(170, 170); thumb.setAlignment(Qt.AlignCenter)
        px = blob_to_pixmap(image_blob) if image_blob else None
        if px and not px.isNull():
            thumb.setPixmap(px.scaled(164, 164, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            thumb.setStyleSheet("background:#141414;border-radius:14px;border:none;")
        else:
            thumb.setText(CAT_ICONS.get(category, "📦"))
            thumb.setStyleSheet(f"background:{styles.c('INPUT_BG')};border-radius:14px;border:none;color:{AMBER};font-size:54px;")
        layout.addWidget(thumb, 0)
        layout.addSpacing(22)

        # ID — fixed narrow column
        id_lbl = QLabel(f"#{pid}")
        id_lbl.setFixedWidth(58)
        id_lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        id_lbl.setStyleSheet(f"color:{styles.c('TEXT_MUTED')};font-size:16px;font-weight:600;background:transparent;border:none;")
        layout.addWidget(id_lbl, 0)
        layout.addSpacing(16)

        # Name + category — STRETCHY (stretch=3)
        info_w = QWidget(); info_w.setStyleSheet("background:transparent;border:none;")
        info_w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        info = QVBoxLayout(info_w); info.setSpacing(8); info.setContentsMargins(0,0,0,0)
        nm = QLabel(name); nm.setWordWrap(True)
        nm.setStyleSheet(f"color:{styles.c('TEXT_PRIMARY')};font-size:18px;font-weight:700;background:transparent;border:none;")
        cat_lbl = QLabel(category)
        cat_lbl.setStyleSheet(f"color:{styles.c('TEXT_MUTED')};font-size:14px;font-weight:500;background:transparent;border:none;")
        info.addStretch(); info.addWidget(nm); info.addWidget(cat_lbl); info.addStretch()
        layout.addWidget(info_w, 3)
        layout.addSpacing(20)

        # Price — STRETCHY (stretch=2)
        price_lbl = QLabel(f"PHP {price:,.2f}")
        price_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        price_lbl.setStyleSheet(f"color:{AMBER};font-size:20px;font-weight:800;background:transparent;border:none;")
        layout.addWidget(price_lbl, 2)
        layout.addSpacing(18)

        # Progress bar + labels — STRETCHY (stretch=3)
        prog_w = QWidget(); prog_w.setStyleSheet("background:transparent;border:none;")
        prog_w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        prog_col = QVBoxLayout(prog_w); prog_col.setSpacing(8); prog_col.setContentsMargins(0,0,0,0)
        bar = StockProgressBar(stock, max_stock)
        pct = min(100, int(stock / max(max_stock, 1) * 100))
        pct_lbl = QLabel(f"{pct}% of capacity")
        pct_lbl.setStyleSheet(f"color:{styles.c('TEXT_MUTED')};font-size:13px;font-weight:500;background:transparent;border:none;")
        units_lbl = QLabel(f"{stock} units remaining")
        units_lbl.setStyleSheet(f"color:{styles.c('TEXT_MUTED')};font-size:12px;font-weight:400;background:transparent;border:none;")
        prog_col.addStretch()
        prog_col.addWidget(bar)
        prog_col.addWidget(pct_lbl)
        prog_col.addWidget(units_lbl)
        prog_col.addStretch()
        layout.addWidget(prog_w, 3)
        layout.addSpacing(16)

        # Stock count — fixed width number
        if stock == 0: sc = "#EF4444"
        elif stock <= 5: sc = "#F97316"
        else: sc = "#10B981"
        stock_lbl = QLabel(str(stock))
        stock_lbl.setFixedWidth(72)
        stock_lbl.setAlignment(Qt.AlignCenter)
        stock_lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        stock_lbl.setStyleSheet(f"color:{sc};font-size:38px;font-weight:800;background:transparent;border:none;")
        layout.addWidget(stock_lbl, 0)
        layout.addSpacing(16)

        # Status badge — fixed width pill
        if stock == 0: bg_c, txt_c, badge_text = "rgba(239,68,68,0.14)", "#EF4444", "Out of Stock"
        elif stock <= 5: bg_c, txt_c, badge_text = "rgba(249,115,22,0.14)", "#F97316", "Low Stock"
        else: bg_c, txt_c, badge_text = "rgba(16,185,129,0.14)", "#10B981", "In Stock"
        badge = QLabel(badge_text)
        badge.setFixedWidth(120); badge.setFixedHeight(42)
        badge.setAlignment(Qt.AlignCenter)
        badge.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        badge.setStyleSheet(f"background:{bg_c};color:{txt_c};font-size:14px;font-weight:700;border-radius:14px;padding:0 10px;border:none;")
        layout.addWidget(badge, 0)
        layout.addSpacing(16)

        # Action buttons — stacked vertically, fixed width
        self._edit_cb = None; self._delete_cb = None
        btn_edit = QPushButton("✎  Edit"); btn_edit.setFixedSize(110, 60); btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.setStyleSheet(f"QPushButton{{background:rgba(16,185,129,0.12);color:#10B981;border:1.5px solid rgba(16,185,129,0.35);border-radius:12px;font-size:14px;font-weight:700;}}QPushButton:hover{{background:#10B981;color:white;border-color:#10B981;}}")
        btn_edit.clicked.connect(lambda: self._edit_cb and self._edit_cb(self._pid))
        btn_del = QPushButton("🗑  Delete"); btn_del.setFixedSize(110, 60); btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setStyleSheet(f"QPushButton{{background:rgba(239,68,68,0.12);color:#EF4444;padding:5px;border:1.5px solid rgba(239,68,68,0.35);border-radius:12px;font-size:14px;font-weight:700;}}QPushButton:hover{{background:#EF4444;color:white;border-color:#EF4444;}}")
        btn_del.clicked.connect(lambda: self._delete_cb and self._delete_cb(self._pid))
        btn_col = QVBoxLayout(); btn_col.setSpacing(10); btn_col.setContentsMargins(0,0,0,0)
        btn_col.addStretch(); btn_col.addWidget(btn_edit); btn_col.addWidget(btn_del); btn_col.addStretch()
        btn_wrap = QWidget(); btn_wrap.setFixedWidth(110); btn_wrap.setStyleSheet("background:transparent;border:none;")
        btn_wrap.setLayout(btn_col)
        layout.addWidget(btn_wrap, 0)

    def set_edit_callback(self, cb): self._edit_cb = cb
    def set_delete_callback(self, cb): self._delete_cb = cb

    def _apply_style(self, sel):
        self._selected = sel
        if sel:
            self.setStyleSheet(f"QFrame{{background:rgba(245,158,11,0.08);border:2px solid {AMBER};border-radius:16px;}}")
        else:
            self.setStyleSheet(
                f"QFrame{{background:{styles.c('CARD_BG')};border:1px solid {styles.c('BORDER')};border-radius:16px;}}"
                f"QFrame:hover{{border:1.5px solid rgba(245,158,11,0.40);background:rgba(245,158,11,0.03);}}")

    def set_selected(self, s): self._apply_style(s)
    def is_selected(self): return self._selected
    def pid(self): return self._pid



# ═══════════════════════════════════════════════════════════════
#  TABLE HEADER  — widths matched to ROW_H 220 columns
# ═══════════════════════════════════════════════════════════════
class _TableHeader(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(46)
        self.setStyleSheet(f"QFrame{{background:{styles.c('INPUT_BG')};border:1px solid {styles.c('BORDER')};border-radius:12px;}}")
        layout = QHBoxLayout(self); layout.setContentsMargins(22, 0, 22, 0); layout.setSpacing(0)

        def h(text, w=None, align=Qt.AlignLeft):
            l = QLabel(text); l.setAlignment(align | Qt.AlignVCenter)
            l.setStyleSheet(f"color:{styles.c('TEXT_MUTED')};font-size:12px;font-weight:700;letter-spacing:0.8px;background:transparent;border:none;")
            if w: l.setFixedWidth(w)
            return l

        # Mirror the exact stretch factors used in InventoryRow
        layout.addWidget(h("", 170), 0); layout.addSpacing(22)
        layout.addWidget(h("ID", 58), 0); layout.addSpacing(16)
        layout.addWidget(h("PRODUCT / CATEGORY"), 3); layout.addSpacing(20)
        layout.addWidget(h("UNIT PRICE"), 2); layout.addSpacing(18)
        layout.addWidget(h("STOCK LEVEL"), 3); layout.addSpacing(16)
        layout.addWidget(h("QTY", 72, Qt.AlignCenter), 0); layout.addSpacing(16)
        layout.addWidget(h("STATUS", 120, Qt.AlignCenter), 0); layout.addSpacing(16)
        layout.addWidget(h("ACTIONS", 110, Qt.AlignCenter), 0)


# ═══════════════════════════════════════════════════════════════
#  VIEW ALL PRODUCTS TAB
# ═══════════════════════════════════════════════════════════════
class ViewAllProductsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._all_rows = []; self._row_widgets = []; self._selected_pid = None

        root = QVBoxLayout(self); root.setContentsMargins(28, 22, 28, 16); root.setSpacing(14)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("Products"); title.setProperty("title", True)
        sub = QLabel("Browse and manage your inventory catalog"); sub.setProperty("subtitle", True)
        hv = QVBoxLayout(); hv.setSpacing(2); hv.addWidget(title); hv.addWidget(sub)
        hdr.addLayout(hv, 1)
        self._count_lbl = QLabel("0 items")
        self._count_lbl.setStyleSheet(f"background:rgba(245,158,11,0.13);color:{AMBER};font-size:12px;font-weight:700;border-radius:12px;padding:4px 12px;border:none;")
        hdr.addWidget(self._count_lbl, 0, Qt.AlignVCenter)
        root.addLayout(hdr)

        # Toolbar
        tb = QHBoxLayout(); tb.setSpacing(10)
        self.search = QLineEdit(); self.search.setPlaceholderText("Search products…")
        self.search.setFixedHeight(40); self.search.setCursor(Qt.IBeamCursor); self.search.setStyleSheet(input_style())
        self.search.textChanged.connect(self._apply_filter)
        self.cmb_cat = QComboBox(); self.cmb_cat.setFixedHeight(40); self.cmb_cat.setFixedWidth(170)
        self.cmb_cat.setCursor(Qt.PointingHandCursor); self.cmb_cat.addItem("All Categories")
        self.cmb_cat.setStyleSheet(combo_style()); self.cmb_cat.currentIndexChanged.connect(self._apply_filter)
        self.cmb_sort = QComboBox(); self.cmb_sort.setFixedHeight(40); self.cmb_sort.setFixedWidth(170)
        self.cmb_sort.setCursor(Qt.PointingHandCursor)
        for s in ["Newest First","Oldest First","Price: Low→High","Price: High→Low","Name A→Z","Stock: Low→High","Stock: High→Low"]:
            self.cmb_sort.addItem(s)
        self.cmb_sort.setStyleSheet(combo_style()); self.cmb_sort.currentIndexChanged.connect(self._apply_filter)
        btn_refresh = QPushButton("↻  Refresh"); btn_refresh.setFixedHeight(40); btn_refresh.setFixedWidth(100)
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(f"QPushButton{{background:rgba(245,158,11,0.12);color:{AMBER};border:none;border-radius:10px;padding:10px;font-size:12px;font-weight:700;}}QPushButton:hover{{background:rgba(245,158,11,0.24);}}")
        btn_refresh.clicked.connect(self.refresh)
        self.btn_edit = QPushButton("✎  Edit Product"); self.btn_edit.setFixedHeight(40); self.btn_edit.setCursor(Qt.PointingHandCursor)
        self.btn_edit.setStyleSheet(f"QPushButton{{background:transparent;color:{styles.c('SUCCESS')};border:1.5px solid {styles.c('SUCCESS')};border-radius:10px;font-size:12px;font-weight:700;padding:0 14px;}}QPushButton:hover{{background:{styles.c('SUCCESS')};color:white;}}")
        self.btn_edit.clicked.connect(self._edit_selected)
        self.btn_del = QPushButton("🗑  Delete"); self.btn_del.setFixedHeight(40); self.btn_del.setCursor(Qt.PointingHandCursor)
        self.btn_del.setStyleSheet(f"QPushButton{{background:transparent;color:{styles.c('DANGER')};border:1.5px solid {styles.c('DANGER')};border-radius:10px;font-size:12px;font-weight:700;padding:0 14px;}}QPushButton:hover{{background:{styles.c('DANGER')};color:white;}}")
        self.btn_del.clicked.connect(self._delete_selected)
        tb.addWidget(self.search, 1); tb.addWidget(self.cmb_cat); tb.addWidget(self.cmb_sort)
        tb.addWidget(btn_refresh); tb.addWidget(self.btn_edit); tb.addWidget(self.btn_del)
        root.addLayout(tb)

        # Legend
        leg = QHBoxLayout(); leg.setSpacing(16)
        for color, text in [("#10B981","● In Stock (6+)"),("#F97316","● Low Stock (1–5)"),("#EF4444","● Out of Stock (0)")]:
            l = QLabel(text); l.setStyleSheet(f"color:{color};font-size:11px;font-weight:600;background:transparent;border:none;")
            leg.addWidget(l)
        leg.addStretch()
        self._total_lbl = QLabel("")
        self._total_lbl.setStyleSheet(f"font-size:11px;color:{styles.c('TEXT_MUTED')};background:transparent;border:none;")
        leg.addWidget(self._total_lbl)
        root.addLayout(leg)

        # Table header
        root.addWidget(_TableHeader())

        # Scroll area
        self._scroll = QScrollArea(); self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame); self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(
            f"QScrollArea{{background:transparent;border:none;}}"
            f"QScrollBar:vertical{{width:6px;background:transparent;}}"
            f"QScrollBar::handle:vertical{{background:rgba(245,158,11,0.35);border-radius:3px;min-height:20px;}}"
            f"QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}")
        self._list_widget = QWidget(); self._list_widget.setStyleSheet("background:transparent;")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setSpacing(6); self._list_layout.setAlignment(Qt.AlignTop); self._list_layout.setContentsMargins(0, 4, 0, 4)
        self._scroll.setWidget(self._list_widget)
        root.addWidget(self._scroll, 1)

        self._empty_lbl = QLabel("No products found"); self._empty_lbl.setAlignment(Qt.AlignCenter)
        self._empty_lbl.setStyleSheet(f"font-size:16px;color:{styles.c('TEXT_MUTED')};background:transparent;border:none;")
        self._empty_lbl.hide(); root.addWidget(self._empty_lbl)

    def _clear_list(self):
        while self._list_layout.count():
            it = self._list_layout.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        self._row_widgets.clear(); self._selected_pid = None

    def _populate_list(self, rows):
        self._clear_list()
        if not rows: self._empty_lbl.show(); return
        self._empty_lbl.hide()
        stocks = [r[4] for r in rows if r[4] > 0]
        max_stock = max(50, min(500, max(stocks))) if stocks else 100
        for row in rows:
            pid, name, cat, price, stock = row[0], row[1], row[2], row[3], row[4]
            created_at = row[5] if len(row) > 5 else ""
            img_blob   = row[6] if len(row) > 6 else None
            w = InventoryRow(pid, name, cat, price, stock, img_blob, created_at=created_at, max_stock=max_stock)
            w.mousePressEvent = lambda e, ww=w: self._row_clicked(e, ww)
            w.set_edit_callback(self._edit_pid)
            w.set_delete_callback(self._delete_pid)
            self._list_layout.addWidget(w); self._row_widgets.append(w)
        self._count_lbl.setText(f"{len(rows)} items")
        self._total_lbl.setText(f"Showing {len(rows)} product{'s' if len(rows)!=1 else ''}")

    def _row_clicked(self, event, row):
        for r in self._row_widgets:
            if r is not row and r.is_selected(): r.set_selected(False)
        new_sel = not row.is_selected()
        row.set_selected(new_sel)
        self._selected_pid = row.pid() if new_sel else None

    def _no_selection_dialog(self):
        InfoDialog("Nothing Selected", "Click a product row first to select it.", parent=self).exec_()

    def _edit_selected(self):
        if self._selected_pid is None: self._no_selection_dialog(); return
        self._edit_pid(self._selected_pid)

    def _edit_pid(self, pid):
        row = next((r for r in self._all_rows if r[0] == pid), None)
        if row is None: return
        dlg = EditProductDialog(row, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            v = dlg.get_values()
            with get_connection() as conn:
                conn.execute("UPDATE products SET name=?,category=?,price=?,stock=?,image_data=? WHERE id=?",
                             (v["name"], v["category"], v["price"], v["stock"], v["image_data"], pid))
            self.refresh()

    def _delete_selected(self):
        if self._selected_pid is None: self._no_selection_dialog(); return
        self._delete_pid(self._selected_pid)

    def _delete_pid(self, pid):
        name = next((r[1] for r in self._all_rows if r[0] == pid), "this product")
        dlg = ConfirmDialog("Delete Product",
                            f"Delete  '{name}'?\n\nAll related sales records will also be permanently removed.",
                            confirm_text="Delete", danger=True, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            with get_connection() as conn:
                conn.execute("DELETE FROM sales WHERE product_id=?", (pid,))
                conn.execute("DELETE FROM products WHERE id=?", (pid,))
            self._selected_pid = None; self.refresh()

    def _apply_filter(self):
        query = self.search.text().lower(); cat_sel = self.cmb_cat.currentText(); sort_sel = self.cmb_sort.currentText()
        rows = list(self._all_rows)
        if cat_sel != "All Categories": rows = [r for r in rows if r[2] == cat_sel]
        if query: rows = [r for r in rows if query in r[1].lower() or query in r[2].lower()]
        if   sort_sel == "Newest First":      rows.sort(key=lambda r: r[5], reverse=True)
        elif sort_sel == "Oldest First":      rows.sort(key=lambda r: r[5])
        elif sort_sel == "Price: Low→High":   rows.sort(key=lambda r: r[3])
        elif sort_sel == "Price: High→Low":   rows.sort(key=lambda r: r[3], reverse=True)
        elif sort_sel == "Name A→Z":          rows.sort(key=lambda r: r[1].lower())
        elif sort_sel == "Stock: Low→High":   rows.sort(key=lambda r: r[4])
        elif sort_sel == "Stock: High→Low":   rows.sort(key=lambda r: r[4], reverse=True)
        self._populate_list(rows)

    def refresh(self):
        with get_connection() as conn:
            try:
                rows = conn.execute("SELECT id,name,category,price,stock,created_at,image_data FROM products ORDER BY id DESC").fetchall()
            except Exception:
                rows = conn.execute("SELECT id,name,category,price,stock,created_at,NULL AS image_data FROM products ORDER BY id DESC").fetchall()
        self._all_rows = [list(r) for r in rows]
        cats = sorted(set(r[2] for r in self._all_rows))
        self.cmb_cat.blockSignals(True)
        cur = self.cmb_cat.currentText(); self.cmb_cat.clear(); self.cmb_cat.addItem("All Categories")
        for cat in cats: self.cmb_cat.addItem(cat)
        idx = self.cmb_cat.findText(cur); self.cmb_cat.setCurrentIndex(max(0, idx))
        self.cmb_cat.blockSignals(False); self._apply_filter()