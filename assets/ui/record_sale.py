"""
Record Sale — product card-grid picker on the left, order summary on the right.
Left panel mirrors the Products page visual style (image cards with all details).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QComboBox, QPushButton, QFrame, QSizePolicy, QScrollArea,
    QLineEdit, QDialog, QGridLayout,
)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QPixmap, QColor, QPainter, QPainterPath, QFont, QPen, QFontMetrics

import styles
from styles import AMBER, ORANGE, CAT_ICONS, combo_style, input_style
from database.database import get_connection, blob_to_pixmap

CARD_W = 190
CARD_H = 270


def _c(k): return styles.c(k)


# ═══════════════════════════════════════════════════════════════
#  DIALOG BASE
# ═══════════════════════════════════════════════════════════════
class _BaseDialog(QDialog):
    def __init__(self, parent=None, width=400):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True); self.setFixedWidth(width)
        bg = _c("CARD_BG"); bd = _c("BORDER"); txt = _c("TEXT_PRIMARY")
        self.setStyleSheet(
            f"QDialog{{background:{bg};border:2px solid {bd};border-radius:18px;}}"
            f"QLabel{{background:transparent;border:none;color:{txt};}}")
        self._r = QVBoxLayout(self); self._r.setContentsMargins(28, 24, 28, 24); self._r.setSpacing(0)

    def _sep(self):
        f = QFrame(); f.setFixedHeight(1); f.setStyleSheet("background:rgba(245,158,11,0.20);border:none;"); return f

    def _sp(self, px):
        s = QWidget(); s.setFixedHeight(px); s.setStyleSheet("background:transparent;border:none;"); self._r.addWidget(s)

    def _btn(self, text, primary=True, danger=False):
        b = QPushButton(text); b.setFixedHeight(44); b.setCursor(Qt.PointingHandCursor)
        if primary and not danger:
            b.setStyleSheet(
                f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {AMBER},stop:1 {ORANGE});"
                f"color:#111;border:none;border-radius:10px;font-size:14px;font-weight:800;}}"
                f"QPushButton:hover{{background:{AMBER};}}"
                f"QPushButton:pressed{{background:{ORANGE};color:white;}}")
        elif danger:
            b.setStyleSheet(
                f"QPushButton{{background:transparent;color:{_c('DANGER')};border:1.5px solid {_c('DANGER')};"
                f"border-radius:10px;font-size:13px;font-weight:700;}}QPushButton:hover{{background:{_c('DANGER')};color:white;}}")
        else:
            b.setStyleSheet(
                f"QPushButton{{background:transparent;color:{_c('TEXT_MUTED')};border:1.5px solid {_c('BORDER')};"
                f"border-radius:10px;font-size:13px;font-weight:600;}}QPushButton:hover{{border-color:{AMBER};color:{AMBER};}}")
        return b


class InfoDialog(_BaseDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(parent, 380)
        tl = QLabel(title); tl.setStyleSheet(f"font-size:16px;font-weight:800;color:{_c('TEXT_PRIMARY')};background:transparent;border:none;")
        self._r.addWidget(tl); self._sp(10); self._r.addWidget(self._sep()); self._sp(14)
        ml = QLabel(message); ml.setWordWrap(True)
        ml.setStyleSheet(f"font-size:13px;color:{_c('TEXT_PRIMARY')};background:transparent;border:none;line-height:1.5;")
        self._r.addWidget(ml); self._sp(20)
        ok = self._btn("OK"); ok.clicked.connect(self.accept); self._r.addWidget(ok)


class WarnDialog(_BaseDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(parent, 400)
        icon = QLabel("⚠"); icon.setFixedSize(46, 46); icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(f"font-size:22px;background:rgba(239,68,68,0.12);border-radius:23px;color:#EF4444;border:none;")
        hr = QHBoxLayout(); hr.setSpacing(12); hr.addWidget(icon, 0, Qt.AlignVCenter)
        tl = QLabel(title); tl.setStyleSheet(f"font-size:16px;font-weight:800;color:{_c('TEXT_PRIMARY')};background:transparent;border:none;")
        hr.addWidget(tl, 1); self._r.addLayout(hr); self._sp(14); self._r.addWidget(self._sep()); self._sp(14)
        ml = QLabel(message); ml.setWordWrap(True)
        ml.setStyleSheet(f"font-size:13px;color:{_c('TEXT_PRIMARY')};background:transparent;border:none;line-height:1.5;")
        self._r.addWidget(ml); self._sp(20)
        ok = self._btn("OK"); ok.clicked.connect(self.accept); self._r.addWidget(ok)


class SuccessDialog(_BaseDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(parent, 400)
        icon = QLabel("✓"); icon.setFixedSize(46, 46); icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(f"font-size:22px;font-weight:800;background:rgba(16,185,129,0.14);border-radius:23px;color:#10B981;border:none;")
        hr = QHBoxLayout(); hr.setSpacing(12); hr.addWidget(icon, 0, Qt.AlignVCenter)
        tl = QLabel(title); tl.setStyleSheet(f"font-size:16px;font-weight:800;color:{_c('TEXT_PRIMARY')};background:transparent;border:none;")
        hr.addWidget(tl, 1); self._r.addLayout(hr); self._sp(14); self._r.addWidget(self._sep()); self._sp(14)
        ml = QLabel(message); ml.setWordWrap(True)
        ml.setStyleSheet(f"font-size:13px;color:{_c('TEXT_PRIMARY')};background:transparent;border:none;line-height:1.5;")
        self._r.addWidget(ml); self._sp(20)
        ok = self._btn("Done"); ok.clicked.connect(self.accept); self._r.addWidget(ok)


# ═══════════════════════════════════════════════════════════════
#  PRODUCT SALE CARD
# ═══════════════════════════════════════════════════════════════
class SaleProductCard(QFrame):
    """Card showing product image, name, category, price, stock — selectable."""

    def __init__(self, pid, name, category, price, stock, description, image_blob, parent=None):
        super().__init__(parent)
        self._pid = pid; self._selected = False
        self._stock = stock; self._price = price
        self.setFixedSize(CARD_W, CARD_H)
        self.setCursor(Qt.PointingHandCursor)
        self._apply_style(False)

        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        # Image area
        img_frame = QFrame(); img_frame.setFixedHeight(140)
        img_frame.setStyleSheet(
            f"QFrame{{background:{_c('INPUT_BG')};border:none;"
            f"border-top-left-radius:14px;border-top-right-radius:14px;}}")
        il = QVBoxLayout(img_frame); il.setContentsMargins(0, 0, 0, 0)
        img_lbl = QLabel(); img_lbl.setAlignment(Qt.AlignCenter); img_lbl.setStyleSheet("background:transparent;border:none;")
        px = blob_to_pixmap(image_blob) if image_blob else None
        if px and not px.isNull():
            img_lbl.setPixmap(px.scaled(CARD_W - 8, 132, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            img_lbl.setText(CAT_ICONS.get(category, "📦"))
            img_lbl.setStyleSheet(f"background:transparent;border:none;color:{AMBER};font-size:36px;")
        il.addWidget(img_lbl)
        root.addWidget(img_frame)

        # Stock badge overlay row
        bc, bt = self._stock_badge(stock)
        badge = QLabel(bt); badge.setFixedHeight(20)
        badge.setStyleSheet(f"QLabel{{background:{bc};color:white;font-size:10px;font-weight:700;border-radius:10px;padding:0 8px;border:none;}}")
        br = QHBoxLayout(); br.setContentsMargins(8, 0, 8, 0); br.addStretch(); br.addWidget(badge)
        root.addLayout(br)

        # Text area
        tf = QFrame(); tf.setStyleSheet("QFrame{background:transparent;border:none;}")
        tl = QVBoxLayout(tf); tl.setContentsMargins(12, 6, 12, 10); tl.setSpacing(2)

        cat_lbl = QLabel(category)
        cat_lbl.setStyleSheet(f"color:{_c('TEXT_MUTED')};font-size:10px;font-weight:600;background:transparent;border:none;letter-spacing:0.5px;")
        tl.addWidget(cat_lbl)

        nm = QLabel(name); nm.setWordWrap(True)
        nm.setStyleSheet(f"color:{_c('TEXT_PRIMARY')};font-size:12px;font-weight:700;background:transparent;border:none;")
        nm.setMaximumHeight(34)
        tl.addWidget(nm)

        if description:
            desc = QLabel(description[:60] + ("…" if len(description) > 60 else ""))
            desc.setWordWrap(True)
            desc.setStyleSheet(f"color:{_c('TEXT_MUTED')};font-size:10px;background:transparent;border:none;")
            desc.setMaximumHeight(26)
            tl.addWidget(desc)

        tl.addStretch()
        pr = QHBoxLayout(); pr.setSpacing(4)
        pl = QLabel(f"PHP {price:,.2f}")
        pl.setStyleSheet(f"color:{AMBER};font-size:13px;font-weight:800;background:transparent;border:none;")
        sl = QLabel(f"Stk: {stock}")
        if stock == 0: sc = "#EF4444"
        elif stock <= 5: sc = "#F97316"
        else: sc = "#10B981"
        sl.setStyleSheet(f"color:{sc};font-size:10px;font-weight:700;background:transparent;border:none;")
        pr.addWidget(pl); pr.addStretch(); pr.addWidget(sl)
        tl.addLayout(pr)
        root.addWidget(tf, 1)

    def _apply_style(self, sel):
        self._selected = sel
        if sel:
            self.setStyleSheet(f"QFrame{{background:{_c('CARD_BG')};border:2px solid {AMBER};border-radius:14px;}}")
        else:
            if self._stock == 0:
                self.setStyleSheet(f"QFrame{{background:{_c('CARD_BG')};border:1px solid {_c('BORDER')};border-radius:14px;opacity:0.6;}}")
            else:
                self.setStyleSheet(
                    f"QFrame{{background:{_c('CARD_BG')};border:1px solid {_c('BORDER')};border-radius:14px;}}"
                    f"QFrame:hover{{border:1.5px solid rgba(245,158,11,0.55);}}")

    def set_selected(self, s): self._apply_style(s)
    def is_selected(self): return self._selected
    def pid(self): return self._pid

    @staticmethod
    def _stock_badge(stock):
        if stock == 0: return "#EF4444", "Out of Stock"
        if stock <= 5: return "#F97316", f"Low: {stock}"
        return "#10B981", "In Stock"


# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════
def _sep():
    f = QFrame(); f.setFixedHeight(1); f.setStyleSheet("background:rgba(245,158,11,0.16);border:none;"); return f

def _section(text):
    l = QLabel(text)
    l.setStyleSheet(f"font-size:16px;font-weight:800;color:{_c('TEXT_PRIMARY')};background:transparent;border:none;")
    return l

def _cap(text):
    l = QLabel(text)
    l.setStyleSheet(f"font-size:10px;font-weight:700;color:{_c('TEXT_MUTED')};letter-spacing:1px;background:transparent;border:none;")
    return l


class _GCard(QFrame):
    def __init__(self, accent=False, parent=None):
        super().__init__(parent)
        if accent:
            self.setStyleSheet("QFrame{background:rgba(245,158,11,0.06);border:1.5px solid rgba(245,158,11,0.32);border-radius:16px;}")
        else:
            self.setStyleSheet(f"QFrame{{background:{_c('CARD_BG')};border:1px solid {_c('BORDER')};border-radius:16px;}}")


# ═══════════════════════════════════════════════════════════════
#  RECORD SALE TAB
# ═══════════════════════════════════════════════════════════════
class RecordSaleTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._all_rows    = []   # full DB rows
        self._cards       = []
        self._selected_pid = None

        root = QVBoxLayout(self); root.setContentsMargins(28, 24, 28, 24); root.setSpacing(16)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("Record Sale"); title.setProperty("title", True)
        sub = QLabel("Select a product from the catalog, set quantity, and confirm the transaction")
        sub.setProperty("subtitle", True)
        hv = QVBoxLayout(); hv.setSpacing(2); hv.addWidget(title); hv.addWidget(sub)
        hdr.addLayout(hv, 1)
        root.addLayout(hdr)

        body = QHBoxLayout(); body.setSpacing(20)

        # ═══ LEFT — product grid picker ══════════════════
        left_card = _GCard()
        ll = QVBoxLayout(left_card); ll.setContentsMargins(20, 18, 20, 18); ll.setSpacing(12)
        ll.addWidget(_section("Select Product"))
        ll.addWidget(_sep())

        # Search + category filter toolbar
        ftb = QHBoxLayout(); ftb.setSpacing(10)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Type name to filter…")
        self.search_box.setFixedHeight(40); self.search_box.setCursor(Qt.IBeamCursor)
        self.search_box.setStyleSheet(input_style())
        self.search_box.textChanged.connect(self._apply_filter)
        self.cmb_cat = QComboBox(); self.cmb_cat.setFixedHeight(40); self.cmb_cat.setFixedWidth(160)
        self.cmb_cat.setCursor(Qt.PointingHandCursor); self.cmb_cat.addItem("All Categories")
        self.cmb_cat.setStyleSheet(combo_style()); self.cmb_cat.currentIndexChanged.connect(self._apply_filter)
        ftb.addWidget(self.search_box, 1); ftb.addWidget(self.cmb_cat)
        ll.addLayout(ftb)

        # Legend
        leg = QHBoxLayout(); leg.setSpacing(12)
        for color, text in [("#10B981","● In Stock"),("#F97316","● Low Stock"),("#EF4444","● Out of Stock")]:
            l = QLabel(text); l.setStyleSheet(f"color:{color};font-size:10px;font-weight:600;background:transparent;border:none;")
            leg.addWidget(l)
        leg.addStretch()
        self._grid_count = QLabel("")
        self._grid_count.setStyleSheet(f"font-size:10px;color:{_c('TEXT_MUTED')};background:transparent;border:none;")
        leg.addWidget(self._grid_count)
        ll.addLayout(leg)

        # Grid scroll area
        self._scroll = QScrollArea(); self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame); self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(
            f"QScrollArea{{background:transparent;border:none;}}"
            f"QScrollBar:vertical{{width:6px;background:transparent;}}"
            f"QScrollBar::handle:vertical{{background:rgba(245,158,11,0.35);border-radius:3px;min-height:20px;}}"
            f"QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}")
        self._grid_widget = QWidget(); self._grid_widget.setStyleSheet("background:transparent;")
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setSpacing(14); self._grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._scroll.setWidget(self._grid_widget)
        ll.addWidget(self._scroll, 1)

        self._empty_lbl = QLabel("No products found"); self._empty_lbl.setAlignment(Qt.AlignCenter)
        self._empty_lbl.setStyleSheet(f"font-size:14px;color:{_c('TEXT_MUTED')};background:transparent;border:none;")
        self._empty_lbl.hide(); ll.addWidget(self._empty_lbl)
        body.addWidget(left_card, 6)

        # ═══ RIGHT — order summary ════════════════════════
        right = QVBoxLayout(); right.setSpacing(16)

        self._sum_card = _GCard(accent=True)
        sv = QVBoxLayout(self._sum_card); sv.setContentsMargins(22, 20, 22, 20); sv.setSpacing(12)
        sv.addWidget(_section("Order Summary"))
        sv.addWidget(_sep())

        # Product image preview (larger)
        self._prev_img = QLabel(); self._prev_img.setFixedHeight(150); self._prev_img.setAlignment(Qt.AlignCenter)
        self._prev_img.setText("📦")
        self._prev_img.setStyleSheet(f"background:{_c('INPUT_BG')};border-radius:12px;color:{AMBER};font-size:50px;border:none;")
        sv.addWidget(self._prev_img)

        self._prev_name = QLabel("Select a product to begin"); self._prev_name.setWordWrap(True)
        self._prev_name.setStyleSheet(f"font-size:16px;font-weight:800;color:{_c('TEXT_PRIMARY')};background:transparent;border:none;")
        sv.addWidget(self._prev_name)

        self._prev_cat = QLabel("")
        self._prev_cat.setStyleSheet(f"font-size:11px;font-weight:700;color:{_c('TEXT_MUTED')};letter-spacing:1px;background:transparent;border:none;")
        sv.addWidget(self._prev_cat)

        self._prev_desc = QLabel("")
        self._prev_desc.setWordWrap(True)
        self._prev_desc.setStyleSheet(f"font-size:11px;color:{_c('TEXT_MUTED')};background:transparent;border:none;line-height:1.4;")
        sv.addWidget(self._prev_desc)

        sv.addWidget(_sep())

        ps = QHBoxLayout(); ps.setSpacing(0)
        pc = QVBoxLayout(); pc.setSpacing(4); pc.addWidget(_cap("UNIT PRICE"))
        self._prev_price = QLabel("PHP 0.00")
        self._prev_price.setStyleSheet(f"font-size:20px;font-weight:800;color:{AMBER};background:transparent;border:none;")
        pc.addWidget(self._prev_price)
        sc_col = QVBoxLayout(); sc_col.setSpacing(4); sc_col.addWidget(_cap("IN STOCK"))
        self._prev_stock = QLabel("—")
        self._prev_stock.setStyleSheet(f"font-size:20px;font-weight:800;color:#10B981;background:transparent;border:none;")
        sc_col.addWidget(self._prev_stock)
        ps.addLayout(pc); ps.addStretch(); ps.addLayout(sc_col)
        sv.addLayout(ps)
        sv.addWidget(_sep())

        # Quantity row
        qty_row = QHBoxLayout(); qty_row.setSpacing(10)
        qty_left = QVBoxLayout(); qty_left.setSpacing(6); qty_left.addWidget(_cap("QUANTITY"))
        self.inp_qty = QSpinBox(); self.inp_qty.setMinimum(1); self.inp_qty.setMaximum(999_999)
        self.inp_qty.setFixedHeight(46); self.inp_qty.setCursor(Qt.PointingHandCursor)
        self.inp_qty.setStyleSheet(
            f"QSpinBox{{background:{_c('INPUT_BG')};border:1.5px solid {_c('BORDER')};border-radius:10px;"
            f"padding:0 14px;color:{_c('TEXT_PRIMARY')};font-size:20px;font-weight:800;}}"
            f"QSpinBox:focus{{border:1.5px solid {AMBER};}}"
            f"QSpinBox::up-button,QSpinBox::down-button{{border:none;background:transparent;width:20px;}}")
        self.inp_qty.valueChanged.connect(self._update_totals)
        qty_left.addWidget(self.inp_qty)
        qty_right = QVBoxLayout(); qty_right.setSpacing(6); qty_right.addWidget(_cap("QUICK SET"))
        qrow = QHBoxLayout(); qrow.setSpacing(6)
        for n in [1, 2, 5, 10, 20]:
            b = QPushButton(str(n)); b.setFixedHeight(46); b.setMinimumWidth(36); b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(
                f"QPushButton{{background:rgba(245,158,11,0.10);color:{AMBER};border:none;border-radius:10px;font-size:13px;font-weight:700;}}"
                f"QPushButton:hover{{background:rgba(245,158,11,0.26);}}"
                f"QPushButton:pressed{{background:{AMBER};color:#111;}}")
            b.clicked.connect(lambda _, v=n: self.inp_qty.setValue(v)); qrow.addWidget(b)
        qty_right.addLayout(qrow)
        qty_row.addLayout(qty_left, 1); qty_row.addLayout(qty_right, 2)
        sv.addLayout(qty_row)
        sv.addWidget(_sep())

        tot = QHBoxLayout()
        tot_l = QLabel("ORDER TOTAL")
        tot_l.setStyleSheet(f"font-size:11px;font-weight:700;color:{_c('TEXT_MUTED')};letter-spacing:1px;background:transparent;border:none;")
        self.lbl_subtotal = QLabel("PHP 0.00")
        self.lbl_subtotal.setStyleSheet(f"font-size:26px;font-weight:800;color:{AMBER};background:transparent;border:none;")
        tot.addWidget(tot_l, 1, Qt.AlignVCenter); tot.addWidget(self.lbl_subtotal, 0, Qt.AlignVCenter)
        sv.addLayout(tot)

        self.lbl_available = QLabel("")
        self.lbl_available.setStyleSheet(f"font-size:11px;font-weight:600;color:{_c('SUCCESS')};background:transparent;border:none;")
        sv.addWidget(self.lbl_available)
        right.addWidget(self._sum_card, 1)

        # Confirm card
        conf_card = _GCard()
        cl = QVBoxLayout(conf_card); cl.setContentsMargins(22, 16, 22, 16); cl.setSpacing(8)
        self.btn_sell = QPushButton("✓  Confirm Sale"); self.btn_sell.setFixedHeight(54); self.btn_sell.setCursor(Qt.PointingHandCursor)
        self.btn_sell.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {AMBER},stop:1 {ORANGE});"
            f"color:#111111;border:none;border-radius:12px;font-size:15px;font-weight:800;}}"
            f"QPushButton:hover{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #FBBF24,stop:1 {AMBER});}}"
            f"QPushButton:pressed{{background:{ORANGE};color:white;}}")
        self.btn_sell.clicked.connect(self.record_sale)
        cl.addWidget(self.btn_sell)
        btn_reset = QPushButton("Reset"); btn_reset.setFixedHeight(32); btn_reset.setCursor(Qt.PointingHandCursor)
        btn_reset.setStyleSheet(f"QPushButton{{background:transparent;color:{_c('TEXT_MUTED')};border:none;border-radius:8px;font-size:12px;font-weight:600;}}QPushButton:hover{{background:rgba(245,158,11,0.10);color:{AMBER};}}")
        btn_reset.clicked.connect(self._reset)
        cl.addWidget(btn_reset)
        right.addWidget(conf_card)
        body.addLayout(right, 4)
        root.addLayout(body, 1)

    # ── Grid helpers ──────────────────────────────────────
    def _clear_grid(self):
        while self._grid_layout.count():
            it = self._grid_layout.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        self._cards.clear()
        self._selected_pid = None
        self._reset_summary()

    def _populate_grid(self, rows):
        self._clear_grid()
        if not rows: self._empty_lbl.show(); return
        self._empty_lbl.hide()
        avail_w = max(400, self._scroll.viewport().width() - 20)
        cols = max(2, avail_w // (CARD_W + 14))
        for idx, row in enumerate(rows):
            pid, name, cat, price, stock = row[0], row[1], row[2], row[3], row[4]
            desc     = row[5] if len(row) > 5 else ""
            img_blob = row[6] if len(row) > 6 else None
            card = SaleProductCard(pid, name, cat, price, stock, desc, img_blob)
            card.mousePressEvent = lambda e, c=card: self._card_clicked(e, c)
            r, ci = divmod(idx, cols)
            self._grid_layout.addWidget(card, r, ci)
            self._cards.append(card)
        self._grid_count.setText(f"{len(rows)} products")

    def _card_clicked(self, event, card):
        if card._stock == 0: return   # can't select out-of-stock
        for c in self._cards:
            if c is not card and c.is_selected(): c.set_selected(False)
        new_sel = not card.is_selected()
        card.set_selected(new_sel)
        self._selected_pid = card.pid() if new_sel else None
        self._update_summary()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._all_rows: QTimer.singleShot(50, self._apply_filter)

    # ── Summary panel ─────────────────────────────────────
    def _reset_summary(self):
        self._prev_name.setText("Select a product to begin")
        self._prev_cat.setText("")
        self._prev_desc.setText("")
        self._prev_price.setText("PHP 0.00")
        self._prev_stock.setText("—")
        self._prev_stock.setStyleSheet(f"font-size:20px;font-weight:800;color:#10B981;background:transparent;border:none;")
        self.lbl_subtotal.setText("PHP 0.00")
        self.lbl_available.setText("")
        self._prev_img.setPixmap(QPixmap())
        self._prev_img.setText("📦")
        self._prev_img.setStyleSheet(f"background:{_c('INPUT_BG')};border-radius:12px;color:{AMBER};font-size:50px;border:none;")

    def _update_summary(self):
        if self._selected_pid is None:
            self._reset_summary(); return
        row = next((r for r in self._all_rows if r[0] == self._selected_pid), None)
        if row is None: self._reset_summary(); return
        pid, name, cat, price, stock = row[0], row[1], row[2], row[3], row[4]
        desc     = row[5] if len(row) > 5 else ""
        img_blob = row[6] if len(row) > 6 else None
        qty = self.inp_qty.value()
        self._prev_name.setText(name)
        self._prev_cat.setText(cat.upper())
        self._prev_desc.setText(desc if desc else "")
        self._prev_price.setText(f"PHP {price:,.2f}")
        self.lbl_subtotal.setText(f"PHP {price * qty:,.2f}")
        if img_blob:
            px = blob_to_pixmap(img_blob)
            if px and not px.isNull():
                self._prev_img.setPixmap(px.scaled(280, 146, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self._prev_img.setText("")
                self._prev_img.setStyleSheet("background:#141414;border-radius:12px;border:none;")
            else:
                self._prev_img.setPixmap(QPixmap())
                self._prev_img.setText(CAT_ICONS.get(cat, "📦"))
                self._prev_img.setStyleSheet(f"background:{_c('INPUT_BG')};border-radius:12px;color:{AMBER};font-size:50px;border:none;")
        else:
            self._prev_img.setPixmap(QPixmap())
            self._prev_img.setText(CAT_ICONS.get(cat, "📦"))
            self._prev_img.setStyleSheet(f"background:{_c('INPUT_BG')};border-radius:12px;color:{AMBER};font-size:50px;border:none;")
        if stock == 0:   color, msg = "#EF4444", "⚠  Out of stock"
        elif stock < qty: color, msg = ORANGE, f"⚠  Only {stock} available"
        else:             color, msg = "#10B981", f"✓  {stock - qty} units remaining after this sale"
        self._prev_stock.setText(str(stock))
        self._prev_stock.setStyleSheet(f"font-size:20px;font-weight:800;color:{color};background:transparent;border:none;")
        self.lbl_available.setText(msg)
        self.lbl_available.setStyleSheet(f"font-size:11px;font-weight:600;color:{color};background:transparent;border:none;")

    def _update_totals(self):
        self._update_summary()

    # ── Filter ─────────────────────────────────────────────
    def _apply_filter(self):
        query   = self.search_box.text().lower()
        cat_sel = self.cmb_cat.currentText()
        rows = list(self._all_rows)
        if cat_sel != "All Categories": rows = [r for r in rows if r[2] == cat_sel]
        if query: rows = [r for r in rows if query in r[1].lower() or query in r[2].lower()]
        self._populate_grid(rows)

    # ── Reset ──────────────────────────────────────────────
    def _reset(self):
        self.inp_qty.setValue(1)
        self.search_box.clear()
        self.cmb_cat.setCurrentIndex(0)

    # ── Record sale ────────────────────────────────────────
    def record_sale(self):
        if self._selected_pid is None:
            WarnDialog("No Product Selected", "Click a product card first to select it.", parent=self).exec_(); return
        row = next((r for r in self._all_rows if r[0] == self._selected_pid), None)
        if row is None: return
        pid, name, price, stock = row[0], row[1], row[3], row[4]
        qty = self.inp_qty.value()
        if stock == 0:
            WarnDialog("Out of Stock", f"'{name}' is currently out of stock.", parent=self).exec_(); return
        if qty > stock:
            WarnDialog("Insufficient Stock", f"Only {stock} unit(s) of '{name}' available.\nPlease reduce the quantity.", parent=self).exec_(); return
        total = price * qty
        with get_connection() as conn:
            conn.execute("INSERT INTO sales (product_id,quantity,unit_price,total) VALUES (?,?,?,?)", (pid, qty, price, total))
            conn.execute("UPDATE products SET stock=stock-? WHERE id=?", (qty, pid))
        SuccessDialog("Sale Recorded",
                      f"Product  :  {name}\nQty      :  {qty}\nTotal    :  PHP {total:,.2f}",
                      parent=self).exec_()
        self.inp_qty.setValue(1)
        self.search_box.clear()
        self.refresh()

    # ── Refresh ────────────────────────────────────────────
    def refresh(self):
        with get_connection() as conn:
            try:
                rows = conn.execute(
                    "SELECT id,name,category,price,stock,description,image_data FROM products ORDER BY name"
                ).fetchall()
            except Exception:
                try:
                    rows = conn.execute(
                        "SELECT id,name,category,price,stock,'' as description,image_data FROM products ORDER BY name"
                    ).fetchall()
                except Exception:
                    rows = conn.execute(
                        "SELECT id,name,category,price,stock,'' as description,NULL as image_data FROM products ORDER BY name"
                    ).fetchall()
        self._all_rows = [list(r) for r in rows]
        # Repopulate category combobox
        cats = sorted(set(r[2] for r in self._all_rows))
        self.cmb_cat.blockSignals(True)
        cur = self.cmb_cat.currentText(); self.cmb_cat.clear(); self.cmb_cat.addItem("All Categories")
        for cat in cats: self.cmb_cat.addItem(cat)
        idx = self.cmb_cat.findText(cur); self.cmb_cat.setCurrentIndex(max(0, idx))
        self.cmb_cat.blockSignals(False)
        self._apply_filter()
        # Re-select previously selected card if still present
        if self._selected_pid is not None:
            found = next((c for c in self._cards if c.pid() == self._selected_pid), None)
            if found: found.set_selected(True)
            else: self._selected_pid = None; self._reset_summary()
        self._update_summary()
