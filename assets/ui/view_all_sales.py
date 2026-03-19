import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QSizePolicy, QComboBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

import styles
from styles import AMBER, ORANGE, combo_style, input_style
from database.database import get_connection

def _c(k): return styles.c(k)


# ── Glassmorphism stat chip ────────────────────────────────────
class _StatChip(QFrame):
    def __init__(self, label, value, color, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame{{background:{_c('CARD_BG')};border:1px solid {_c('BORDER')};"
            f"border-radius:14px;}}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 14, 20, 14); lay.setSpacing(4)
        lbl = QLabel(label.upper())
        lbl.setStyleSheet(
            f"color:{_c('TEXT_MUTED')};font-size:10px;font-weight:700;"
            f"letter-spacing:1px;background:transparent;border:none;")
        self._val = QLabel(value)
        self._val.setStyleSheet(
            f"font-size:20px;font-weight:800;color:{color};"
            f"background:transparent;border:none;")
        lay.addWidget(lbl); lay.addWidget(self._val)

    def set_value(self, v): self._val.setText(v)




class ViewAllSalesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 16); root.setSpacing(16)

        # ── Header ────────────────────────────────────────
        hdr = QHBoxLayout()
        hv = QVBoxLayout(); hv.setSpacing(3)
        title = QLabel("Sales History"); title.setProperty("title", True)
        sub   = QLabel("Complete record of all transactions")
        sub.setProperty("subtitle", True)
        hv.addWidget(title); hv.addWidget(sub)
        hdr.addLayout(hv, 1)
        root.addLayout(hdr)

        # ── KPI strip ─────────────────────────────────────
        kpi = QHBoxLayout(); kpi.setSpacing(12)
        self._chip_tx   = _StatChip("Transactions", "—", AMBER)
        self._chip_unit = _StatChip("Units Sold",   "—", "#10B981")
        self._chip_rev  = _StatChip("Total Revenue","—", "#A78BFA")
        self._chip_avg  = _StatChip("Avg. Sale",    "—", "#38BDF8")
        for chip in (self._chip_tx, self._chip_unit, self._chip_rev, self._chip_avg):
            chip.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            kpi.addWidget(chip)
        root.addLayout(kpi)

        # ── Toolbar ───────────────────────────────────────
        tb = QHBoxLayout(); tb.setSpacing(10)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search product, category, date...")
        self.search.setFixedHeight(40); self.search.setCursor(Qt.IBeamCursor)
        self.search.setStyleSheet(
            f"QLineEdit{{background:{_c('CARD_BG')};border:none;"
            f"border-bottom:2px solid {_c('BORDER')};"
            f"border-radius:10px;padding:0 14px;"
            f"color:{_c('TEXT_PRIMARY')};font-size:13px;}}"
            f"QLineEdit:focus{{border-bottom:2px solid {AMBER};}}")
        self.search.textChanged.connect(self.apply_filter)

        # Category filter
        self.cmb_cat = QComboBox()
        self.cmb_cat.setFixedHeight(40); self.cmb_cat.setFixedWidth(160)
        self.cmb_cat.setCursor(Qt.PointingHandCursor)
        self.cmb_cat.addItem("All Categories")
        self.cmb_cat.setStyleSheet(combo_style())
        self.cmb_cat.currentIndexChanged.connect(self._cat_filter)

        # Sort
        self.cmb_sort = QComboBox()
        self.cmb_sort.setFixedHeight(40); self.cmb_sort.setFixedWidth(150)
        self.cmb_sort.setCursor(Qt.PointingHandCursor)
        for s in ["Newest First", "Oldest First", "Highest Total", "Lowest Total"]:
            self.cmb_sort.addItem(s)
        self.cmb_sort.setStyleSheet(combo_style())

        btn_refresh = QPushButton("Refresh")
        btn_refresh.setFixedHeight(40); btn_refresh.setFixedWidth(90)
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(
            f"QPushButton{{background:rgba(245,158,11,0.12);color:{AMBER};"
            f"border:none;border-radius:10px;font-size:12px;font-weight:700;}}"
            f"QPushButton:hover{{background:rgba(245,158,11,0.26);}}")
        btn_refresh.clicked.connect(self.refresh)

        tb.addWidget(self.search, 1)
        tb.addWidget(self.cmb_cat)
        tb.addWidget(self.cmb_sort)
        tb.addWidget(btn_refresh)
        root.addLayout(tb)

        # ── Table — glassmorphism styled ──────────────────
        self.table = QTableWidget()
        self.table.setCursor(Qt.PointingHandCursor)
        cols = ["ID", "Product", "Category", "Qty", "Unit Price", "Total", "Date & Time"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Stretch)
        hh.setSectionResizeMode(0, QHeaderView.Fixed); self.table.setColumnWidth(0, 60)
        hh.setSectionResizeMode(3, QHeaderView.Fixed); self.table.setColumnWidth(3, 60)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setStyleSheet(f"""
            QTableWidget{{
                background:{_c('CARD_BG')};
                border:1px solid {_c('BORDER')};
                border-radius:16px;
                font-size:13px;
                outline:none;
            }}
            QTableWidget::item{{
                padding:11px 14px;
                border:none;
                border-bottom:1px solid rgba(245,158,11,0.08);
                color:{_c('TEXT_PRIMARY')};
            }}
            QTableWidget::item:selected{{
                background:rgba(245,158,11,0.14);
                color:{_c('TEXT_PRIMARY')};
            }}
            QTableWidget::item:hover{{
                background:rgba(245,158,11,0.07);
            }}
            QHeaderView::section{{
                background:rgba(245,158,11,0.08);
                color:{_c('TEXT_MUTED')};
                padding:10px 14px;
                font-size:10px;font-weight:800;
                letter-spacing:1.2px;
                border:none;
                border-bottom:2px solid rgba(245,158,11,0.20);
            }}
            QHeaderView::section:first{{
                border-top-left-radius:16px;
            }}
            QHeaderView::section:last{{
                border-top-right-radius:16px;
            }}
            QScrollBar:vertical{{
                width:6px;background:transparent;
            }}
            QScrollBar::handle:vertical{{
                background:rgba(245,158,11,0.35);
                border-radius:3px;min-height:20px;
            }}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}
        """)
        root.addWidget(self.table, 1)

        # Row count strip
        self._row_info = QLabel("")
        self._row_info.setStyleSheet(
            f"font-size:11px;color:{_c('TEXT_MUTED')};"
            f"background:transparent;border:none;")
        root.addWidget(self._row_info)

        self._all_rows = []

    def _cat_filter(self):
        self.apply_filter(self.search.text())

    def apply_filter(self, text=""):
        text    = text.lower()
        cat_sel = self.cmb_cat.currentText()
        sort_sel = self.cmb_sort.currentText()

        rows = list(self._all_rows)
        if cat_sel != "All Categories":
            rows = [r for r in rows if r[2] == cat_sel]
        if text:
            rows = [r for r in rows if
                    text in r[1].lower() or text in r[2].lower() or text in r[6].lower()]

        if sort_sel == "Newest First":
            rows = sorted(rows, key=lambda r: r[6], reverse=True)
        elif sort_sel == "Oldest First":
            rows = sorted(rows, key=lambda r: r[6])
        elif sort_sel == "Highest Total":
            rows = sorted(rows, key=lambda r: r[5], reverse=True)
        elif sort_sel == "Lowest Total":
            rows = sorted(rows, key=lambda r: r[5])

        self._render_rows(rows)

    def _render_rows(self, rows):
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            vals = [str(row[0]), row[1], row[2], str(row[3]),
                    f"PHP {row[4]:,.2f}", f"PHP {row[5]:,.2f}", row[6]]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                if col == 5:
                    item.setForeground(QColor(AMBER))
                    f = item.font(); f.setBold(True); item.setFont(f)
                elif col == 3:
                    item.setForeground(QColor(_c("TEXT_MUTED")))
                self.table.setItem(r, col, item)
            self.table.setRowHeight(r, 46)

        visible = sum(1 for r in range(self.table.rowCount()) if not self.table.isRowHidden(r))
        self._row_info.setText(f"Showing {len(rows)} of {len(self._all_rows)} transactions")

    def refresh(self):
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT s.id,p.name,p.category,s.quantity,s.unit_price,s.total,s.sold_at
                FROM sales s JOIN products p ON p.id=s.product_id
                ORDER BY s.id DESC""").fetchall()
            total_rev = conn.execute(
                "SELECT COALESCE(SUM(total),0) FROM sales").fetchone()[0]
            total_qty = conn.execute(
                "SELECT COALESCE(SUM(quantity),0) FROM sales").fetchone()[0]
            tx_count  = conn.execute(
                "SELECT COUNT(*) FROM sales").fetchone()[0]
            avg_sale  = (total_rev / tx_count) if tx_count else 0.0

        self._all_rows = [list(r) for r in rows]

        # Update KPI chips
        self._chip_tx.set_value(f"{tx_count:,}")
        self._chip_unit.set_value(f"{total_qty:,}")
        self._chip_rev.set_value(f"PHP {total_rev:,.0f}")
        self._chip_avg.set_value(f"PHP {avg_sale:,.0f}")

        # Rebuild category dropdown
        cats = sorted(set(r[2] for r in self._all_rows))
        self.cmb_cat.blockSignals(True)
        cur = self.cmb_cat.currentText()
        self.cmb_cat.clear()
        self.cmb_cat.addItem("All Categories")
        for c in cats: self.cmb_cat.addItem(c)
        idx = self.cmb_cat.findText(cur)
        self.cmb_cat.setCurrentIndex(max(0, idx))
        self.cmb_cat.blockSignals(False)

        self.apply_filter(self.search.text())