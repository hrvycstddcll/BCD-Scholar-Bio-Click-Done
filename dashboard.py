import os
import math
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QStackedWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QSizePolicy, QPushButton, QMessageBox,
    QApplication, QGridLayout, QScrollArea,
)
from PyQt5.QtCore import Qt, QTimer, QRectF, pyqtSignal
from PyQt5.QtGui import (
    QColor, QPainter, QBrush, QPen, QLinearGradient, QRadialGradient,
    QFont, QPainterPath, QCursor, QPixmap,
)

from database.database import get_connection
import styles
from assets.ui.add_product       import AddProductTab
from assets.ui.view_all_products import ViewAllProductsTab
from assets.ui.record_sale       import RecordSaleTab
from assets.ui.view_all_sales    import ViewAllSalesTab

AMBER  = "#F59E0B"
ORANGE = "#F97316"
def _c(k): return styles.c(k)


# ── Custom amber cursor ───────────────────────────────────────
def _make_cursor():
    sz = 26
    px = QPixmap(sz, sz)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor(AMBER), 2.0))
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(2, 2, sz - 4, sz - 4)
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(QColor(AMBER)))
    p.drawEllipse(sz // 2 - 3, sz // 2 - 3, 6, 6)
    p.end()
    return QCursor(px, sz // 2, sz // 2)


# ── GlassCard ─────────────────────────────────────────────────
# Lightweight painted card — no child _body widget.
# Children are added directly via body_layout (a QVBoxLayout on self).
class GlassCard(QFrame):
    def __init__(self, radius=16, parent=None):
        super().__init__(parent)
        self._r = radius
        self._body_lay = QVBoxLayout(self)
        self._body_lay.setContentsMargins(0, 0, 0, 0)
        self._body_lay.setSpacing(0)

    @property
    def body_layout(self): return self._body_lay

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h, r, pad = self.width(), self.height(), self._r, 8

        # Shadow layers
        for i in range(5, 0, -1):
            sp = i * 3
            a  = max(0, 9 - i)
            sh = QColor(180, 130, 30, a) if not styles.is_dark() else QColor(0, 0, 0, a * 2)
            p.setBrush(QBrush(sh)); p.setPen(Qt.NoPen)
            sp_path = QPainterPath()
            sp_path.addRoundedRect(
                QRectF(pad - sp, pad + sp // 2, w - pad*2 + sp*2, h - pad*2 + sp),
                r + sp // 2, r + sp // 2)
            p.drawPath(sp_path)

        # Card body
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
        card.addRoundedRect(QRectF(pad, pad, w - pad*2, h - pad*2), r, r)
        p.drawPath(card)

        # Top sheen
        sheen = QLinearGradient(0, pad, 0, pad + 30)
        sheen.setColorAt(0.0, QColor(255, 255, 255, 80 if not styles.is_dark() else 22))
        sheen.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(sheen))
        sh2 = QPainterPath()
        sh2.addRoundedRect(QRectF(pad, pad, w - pad*2, 30), r, r)
        p.drawPath(sh2)

        # Border
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(245, 200, 100, 50 if not styles.is_dark() else 30), 1.0))
        p.drawPath(card)
        p.end()
        # FIX: do NOT call super().paintEvent — QFrame default would repaint children twice


# ── SparkLine ─────────────────────────────────────────────────
class SparkLine(QWidget):
    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(72)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._color = color
        self._data  = [0.0, 0.0]
        t = QTimer(self)
        t.timeout.connect(self.update)
        t.start(200)

    def push(self, v: float):
        self._data.append(float(v))
        self._data = self._data[-30:]

    def push_history(self, values: list):
        if not values:
            return
        self._data = [float(x) for x in values]
        if len(self._data) < 2:
            self._data = [self._data[0], self._data[0]]
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        pts = self._data
        if len(pts) < 2:
            p.end()
            return

        mn, mx = min(pts), max(pts)
        span = mx - mn if mx != mn else 1.0

        def pt(i, v):
            return int(i * w / (len(pts) - 1)), int(h - 4 - ((v - mn) / span) * (h - 8))

        color = QColor(self._color)
        fill = QLinearGradient(0, 0, 0, h)
        fc = QColor(color); fc.setAlpha(80)
        fc2 = QColor(color); fc2.setAlpha(0)
        fill.setColorAt(0.0, fc)
        fill.setColorAt(1.0, fc2)

        area = QPainterPath()
        x0, y0 = pt(0, pts[0])
        area.moveTo(x0, h)
        area.lineTo(x0, y0)
        for i in range(1, len(pts)):
            xi, yi = pt(i, pts[i])
            xp, yp = pt(i - 1, pts[i - 1])
            area.cubicTo((xp + xi) // 2, yp, (xp + xi) // 2, yi, xi, yi)
        area.lineTo(w, h)
        area.closeSubpath()
        p.setBrush(QBrush(fill)); p.setPen(Qt.NoPen)
        p.drawPath(area)

        line = QPainterPath()
        line.moveTo(*pt(0, pts[0]))
        for i in range(1, len(pts)):
            xi, yi = pt(i, pts[i])
            xp, yp = pt(i - 1, pts[i - 1])
            line.cubicTo((xp + xi) // 2, yp, (xp + xi) // 2, yi, xi, yi)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(color, 2.5))
        p.drawPath(line)
        p.end()


# ── DonutChart ────────────────────────────────────────────────
class DonutChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._vals        = [30.0, 25.0, 25.0, 20.0]
        self._colors      = [AMBER, "#10B981", "#A78BFA", "#38BDF8"]
        self._labels_txt  = ["Products", "Stock", "Sales", "Revenue"]
        self._t           = 0.0
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(48)

    def set_values(self, cat_revenues: list):
        if not cat_revenues:
            return
        total = max(1.0, sum(float(v) for _, v in cat_revenues))
        self._vals = [float(v) / total * 100 for _, v in cat_revenues]
        self._labels_txt = [str(lbl) for lbl, _ in cat_revenues]
        while len(self._vals) < 4:
            self._vals.append(0.0)
            self._labels_txt.append("")
        self._vals       = self._vals[:4]
        self._labels_txt = self._labels_txt[:4]
        self.update()

    def _tick(self):
        self._t += 0.025
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        R     = int(min(w, h) * 0.36)
        thick = int(R * 0.42)
        total = sum(self._vals) or 1.0
        angle = 90.0

        for i, (v, color) in enumerate(zip(self._vals, self._colors)):
            if v <= 0:
                continue
            span  = (v / total) * 360.0
            pulse = 1.0 + 0.02 * math.sin(self._t + i * 1.3)
            pr    = int(R * pulse)
            inner = max(1, pr - thick // 2)
            pen = QPen(QColor(color), thick)
            pen.setCapStyle(Qt.RoundCap)
            p.setPen(pen)
            p.drawArc(
                QRectF(cx - inner, cy - inner, inner * 2, inner * 2),
                int(angle * 16), int(-span * 16))
            if span > 25:
                mid = math.radians(angle - span / 2)
                lx = cx + int(math.cos(mid) * (inner + thick // 2 + 16))
                ly = cy - int(math.sin(mid) * (inner + thick // 2 + 16))
                p.setFont(QFont("Segoe UI", 8, QFont.Bold))
                p.setPen(QColor(color))
                p.drawText(lx - 14, ly - 7, 28, 14, Qt.AlignCenter, f"{int(v)}%")
            angle -= span

        p.setFont(QFont("Segoe UI", 10, QFont.Bold))
        p.setPen(QColor(_c("TEXT_PRIMARY")))
        p.drawText(QRectF(cx - 40, cy - 11, 80, 22), Qt.AlignCenter, "Revenue")
        p.end()


# ── StatCard ──────────────────────────────────────────────────
# FIX: plain QFrame — does NOT inherit GlassCard.
# Uses setStyleSheet for card appearance (crash-safe on Windows).
# Icon: 150×150 PNG with transparent background, displayed at top of card.
_ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icons")

class StatCard(QFrame):
    def __init__(self, label, icon_file, color, parent=None):
        super().__init__(parent)
        self._color = color
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(220)
        self._apply_style()

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 14)
        root.setSpacing(8)

        # ── Top row: icon left, trend badge right ─────────
        top = QHBoxLayout(); top.setSpacing(0)

        # Image icon — 150×150 adaptive (transparent PNG)
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(56, 56)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("background:transparent;border:none;")
        icon_path = os.path.join(_ICON_DIR, icon_file)
        px = QPixmap(icon_path)
        if not px.isNull():
            px = px.scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_lbl.setPixmap(px)
        else:
            # Fallback: colored letter badge if image missing
            icon_lbl.setText(icon_file[0].upper())
            bc = QColor(color)
            icon_lbl.setStyleSheet(
                f"QLabel{{background:rgba({bc.red()},{bc.green()},{bc.blue()},30);"
                f"color:{color};font-size:20px;font-weight:800;"
                f"border-radius:14px;border:none;}}")

        self._trend = QLabel("--")
        self._trend.setStyleSheet(
            f"color:{_c('SUCCESS')};font-size:11px;font-weight:700;"
            f"background:transparent;border:none;")
        self._trend.setAlignment(Qt.AlignTop | Qt.AlignRight)

        top.addWidget(icon_lbl, 0, Qt.AlignTop)
        top.addStretch()
        top.addWidget(self._trend, 0, Qt.AlignTop)
        root.addLayout(top)

        # ── Label ─────────────────────────────────────────
        lbl = QLabel(label.upper())
        lbl.setStyleSheet(
            f"color:{_c('TEXT_MUTED')};font-size:10px;font-weight:700;"
            f"letter-spacing:1.2px;background:transparent;border:none;")
        root.addWidget(lbl)

        # ── Value ─────────────────────────────────────────
        self._val = QLabel("--")
        self._val.setStyleSheet(
            f"font-size:26px;font-weight:800;color:{color};"
            f"background:transparent;border:none;")
        root.addWidget(self._val)

        # ── Spark line ────────────────────────────────────
        self._spark = SparkLine(color)
        root.addWidget(self._spark)

    def _apply_style(self):
        self.setStyleSheet(f"""
            StatCard {{
                background: {_c('CARD_BG')};
                border: 1px solid {_c('BORDER')};
                border-radius: 16px;
            }}
        """)

    def set_value(self, text, trend=""):
        self._val.setText(text)
        if trend:
            self._trend.setText(trend)

    def push_spark(self, v: float):
        self._spark.push(v)

    def push_history(self, values: list):
        self._spark.push_history(values)


# ── TxRow ─────────────────────────────────────────────────────
class TxRow(QWidget):
    def __init__(self, name, date, amount, color, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 8, 0, 8); lay.setSpacing(10)
        dot = QLabel("●"); dot.setFixedWidth(16)
        dot.setStyleSheet(f"color:{color};font-size:14px;background:transparent;")
        info = QVBoxLayout(); info.setSpacing(1)
        nm = QLabel(name)
        nm.setStyleSheet(f"font-size:12px;font-weight:600;color:{_c('TEXT_PRIMARY')};background:transparent;")
        nm.setWordWrap(False)
        nm.setMinimumWidth(0)
        dt = QLabel(date)
        dt.setStyleSheet(f"font-size:10px;color:{_c('TEXT_MUTED')};background:transparent;")
        info.addWidget(nm); info.addWidget(dt)
        amt = QLabel(amount)
        amt.setStyleSheet(f"font-size:12px;font-weight:700;color:{color};background:transparent;")
        amt.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        amt.setMinimumWidth(90)   # reserve space so amount never clips
        lay.addWidget(dot)
        lay.addLayout(info, 1)
        lay.addWidget(amt, 0, Qt.AlignVCenter)


# ── DashboardTab ──────────────────────────────────────────────
# FIX: no custom paintEvent — background set via stylesheet only.
class DashboardTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # FIX: warm gradient via stylesheet — crash-safe, no paintEvent needed
        self.setStyleSheet(f"DashboardTab {{ background: {_c('BG')}; }}")

        root = QHBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(20)

        # LEFT column
        left = QVBoxLayout(); left.setSpacing(16)

        title_lbl = QLabel("Dashboard"); title_lbl.setProperty("title", True)
        sub_lbl   = QLabel("Live overview of your inventory & sales activity")
        sub_lbl.setProperty("subtitle", True)
        left.addWidget(title_lbl)
        left.addWidget(sub_lbl)

        # KPI 2×2 grid
        self._c_prod = StatCard("Total Products", "products.png", AMBER)
        self._c_stk  = StatCard("Units in Stock", "stocks.png",   "#10B981")
        self._c_sal  = StatCard("Total Sales",    "sales.png",    ORANGE)
        self._c_rev  = StatCard("Revenue",        "revenue.png",  "#A78BFA")
        kpi = QGridLayout(); kpi.setSpacing(14)
        kpi.addWidget(self._c_prod, 0, 0); kpi.addWidget(self._c_stk,  0, 1)
        kpi.addWidget(self._c_sal,  1, 0); kpi.addWidget(self._c_rev,  1, 1)
        left.addLayout(kpi, 1)

        # Low stock card
        low_card = GlassCard(radius=14)
        low_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        low_card.setMinimumHeight(190)
        low_card.setMaximumHeight(240)
        low_inner = QVBoxLayout()
        low_inner.setContentsMargins(16, 12, 16, 8); low_inner.setSpacing(8)
        low_card.body_layout.addLayout(low_inner)

        lh = QHBoxLayout()
        lt = QLabel("Low Stock Alerts")
        lt.setStyleSheet(f"font-size:13px;font-weight:700;color:{_c('TEXT_PRIMARY')};background:transparent;")
        ls = QLabel("Items with 5 or fewer units")
        ls.setStyleSheet(f"font-size:11px;color:{_c('TEXT_MUTED')};background:transparent;")
        lh.addWidget(lt); lh.addStretch(); lh.addWidget(ls)
        low_inner.addLayout(lh)

        self.low_table = self._mktable(["ID", "Product", "Category", "Stock"])
        self.low_table.setStyleSheet(
            f"QTableWidget{{border:none;background:transparent;}}"
            f"QScrollBar:vertical{{width:5px;background:transparent;}}"
            f"QScrollBar::handle:vertical{{background:rgba(245,158,11,0.4);"
            f"border-radius:3px;min-height:16px;}}"
            f"QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}")
        low_inner.addWidget(self.low_table, 1)
        left.addWidget(low_card)

        # RIGHT column — min 400px, expands up to ~420px via stretch ratio
        right = QVBoxLayout(); right.setSpacing(16)
        rw = QWidget()
        rw.setMinimumWidth(400)
        rw.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        rw.setLayout(right)
        rw.setStyleSheet("background:transparent;")

        # Analytics card
        an_card = GlassCard(radius=14)
        an_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        an_card.setFixedHeight(310)
        an_inner = QVBoxLayout()
        an_inner.setContentsMargins(16, 12, 16, 12); an_inner.setSpacing(10)
        an_card.body_layout.addLayout(an_inner)
        an_title = QLabel("Analytics")
        an_title.setStyleSheet(
            f"font-size:14px;font-weight:700;color:{_c('TEXT_PRIMARY')};background:transparent;")
        an_inner.addWidget(an_title)
        self._donut = DonutChart()
        self._donut.setFixedHeight(210)
        an_inner.addWidget(self._donut)
        leg = QHBoxLayout(); leg.setSpacing(6)
        self._leg_labels = []
        for color, lbl_txt in [(AMBER, "Products"), ("#10B981", "Stock"),
                               ("#A78BFA", "Sales"), ("#38BDF8", "Revenue")]:
            d = QLabel(f"* {lbl_txt}")
            d.setStyleSheet(f"color:{color};font-size:10px;background:transparent;")
            leg.addWidget(d)
            self._leg_labels.append(d)
        leg.addStretch(); an_inner.addLayout(leg)
        right.addWidget(an_card)

        # Transactions card
        tx_card = GlassCard(radius=14)
        tx_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        tx_inner = QVBoxLayout()
        tx_inner.setContentsMargins(18, 14, 18, 10); tx_inner.setSpacing(0)
        tx_card.body_layout.addLayout(tx_inner)
        tx_title = QLabel("Transactions")
        tx_title.setStyleSheet(
            f"font-size:14px;font-weight:700;color:{_c('TEXT_PRIMARY')};background:transparent;")
        tx_inner.addWidget(tx_title)
        tx_inner.addSpacing(6)

        tx_scroll = QScrollArea()
        tx_scroll.setWidgetResizable(True)
        tx_scroll.setFrameShape(QFrame.NoFrame)
        tx_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        tx_scroll.setStyleSheet(
            f"QScrollArea{{background:transparent;border:none;}}"
            f"QScrollBar:vertical{{width:5px;background:transparent;}}"
            f"QScrollBar::handle:vertical{{background:rgba(245,158,11,0.4);"
            f"border-radius:3px;min-height:16px;}}"
            f"QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}")
        self._tx_widget = QWidget()
        self._tx_widget.setStyleSheet("background:transparent;")
        self._tx_layout = QVBoxLayout(self._tx_widget)
        self._tx_layout.setContentsMargins(0, 0, 4, 0)
        self._tx_layout.setSpacing(0)
        self._tx_layout.addStretch()
        tx_scroll.setWidget(self._tx_widget)
        tx_inner.addWidget(tx_scroll, 1)
        right.addWidget(tx_card, 1)

        root.addLayout(left, 5)
        root.addWidget(rw, 3)

    def _mktable(self, headers):
        t = QTableWidget()
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        t.setEditTriggers(QTableWidget.NoEditTriggers)
        t.setSelectionBehavior(QTableWidget.SelectRows)
        t.setAlternatingRowColors(True)
        t.verticalHeader().setVisible(False)
        return t

    def refresh(self):
        with get_connection() as conn:
            n_prod  = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            n_stock = conn.execute("SELECT COALESCE(SUM(stock),0) FROM products").fetchone()[0]
            n_sales = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
            rev     = conn.execute("SELECT COALESCE(SUM(total),0) FROM sales").fetchone()[0]
            low     = conn.execute(
                "SELECT id,name,category,stock FROM products WHERE stock<=5 ORDER BY stock"
            ).fetchall()
            recent  = conn.execute("""
                SELECT s.id, p.name, s.quantity, s.unit_price, s.total, s.sold_at
                FROM sales s JOIN products p ON p.id = s.product_id
                ORDER BY s.id DESC LIMIT 50""").fetchall()
            days_sales = conn.execute("""
                SELECT date(sold_at) AS d, COUNT(*), SUM(total)
                FROM sales
                WHERE sold_at >= date('now','-30 days')
                GROUP BY d ORDER BY d""").fetchall()
            days_qty = conn.execute("""
                SELECT date(sold_at) AS d, SUM(quantity)
                FROM sales
                WHERE sold_at >= date('now','-30 days')
                GROUP BY d ORDER BY d""").fetchall()
            cat_rev = conn.execute("""
                SELECT p.category, SUM(s.total)
                FROM sales s JOIN products p ON p.id = s.product_id
                GROUP BY p.category ORDER BY SUM(s.total) DESC LIMIT 4""").fetchall()

        sales_hist = [float(r[1]) for r in days_sales] or [0.0, 0.0]
        rev_hist   = [float(r[2]) for r in days_sales] or [0.0, 0.0]
        qty_hist   = [float(r[1]) for r in days_qty]   or [0.0, 0.0]

        self._c_prod.set_value(str(n_prod))
        self._c_prod.push_spark(float(n_prod))

        self._c_stk.set_value(str(n_stock))
        self._c_stk.push_history(qty_hist)

        self._c_sal.set_value(str(n_sales))
        self._c_sal.push_history(sales_hist)

        self._c_rev.set_value(f"P{rev:,.2f}")
        self._c_rev.push_history(rev_hist)

        if cat_rev:
            self._donut.set_values([(str(r[0]), float(r[1])) for r in cat_rev])
            colors = [AMBER, "#10B981", "#A78BFA", "#38BDF8"]
            for i, (cat, _) in enumerate(cat_rev[:4]):
                short = cat.split("&")[0].strip()[:12]
                if i < len(self._leg_labels):
                    self._leg_labels[i].setText(f"* {short}")

        self.low_table.setRowCount(len(low))
        for r, row in enumerate(low):
            for col, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                if col == 3:
                    item.setForeground(QColor(
                        _c("DANGER") if int(val) == 0 else _c("ACCENT2")))
                self.low_table.setItem(r, col, item)

        while self._tx_layout.count() > 1:
            it = self._tx_layout.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        palette = [AMBER, "#10B981", "#A78BFA", ORANGE, "#38BDF8", "#EC4899"]
        for i, row in enumerate(recent):
            clr = palette[i % len(palette)]
            self._tx_layout.insertWidget(
                self._tx_layout.count() - 1,
                TxRow(row[1], row[5][:16], f"P{row[4]:,.2f}", clr))
            if i < len(recent) - 1:
                div = QFrame()
                div.setFixedHeight(1)
                div.setStyleSheet(f"background:{_c('BORDER')};")
                self._tx_layout.insertWidget(self._tx_layout.count() - 1, div)


# ── BottomPillNav ─────────────────────────────────────────────
class BottomPillNav(QWidget):
    tab_changed      = pyqtSignal(int)
    theme_toggled    = pyqtSignal()
    logout_requested = pyqtSignal()
    exit_requested   = pyqtSignal()
    NAV = ["Dashboard", "Add Product", "Products", "Record Sale", "Sales History"]

    def __init__(self, username, parent=None):
        super().__init__(parent)
        self._username = username
        self._cur = 0
        self.setFixedHeight(90)
        self.setAttribute(Qt.WA_StyledBackground, False)
        self._build()

    def _build(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(40, 12, 40, 14)
        outer.setSpacing(0)

        self._pill = QWidget(self)
        self._pill.setAttribute(Qt.WA_StyledBackground, False)
        self._pill.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(self._pill)
        lay.setContentsMargins(18, 0, 18, 0)
        lay.setSpacing(0)

        logo = QLabel("SI")
        logo.setFixedSize(42, 42)
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(
            "QLabel{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "stop:0 #F59E0B,stop:1 #F97316);color:#111111;font-size:13px;"
            "font-weight:800;border-radius:21px;border:none;}")
        lay.addWidget(logo, 0, Qt.AlignVCenter)
        lay.addSpacing(10)

        brand = QLabel("SalesTrack")
        brand.setStyleSheet(
            f"font-size:14px;font-weight:800;color:{_c('TEXT_PRIMARY')};background:transparent;")
        lay.addWidget(brand, 0, Qt.AlignVCenter)
        lay.addStretch(1)

        self._btns = []
        for i, name in enumerate(self.NAV):
            btn = QPushButton(name)
            btn.setFixedHeight(40)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("nav_idx", i)
            btn.clicked.connect(self._clicked)
            self._style_btn(btn, i == 0)
            lay.addWidget(btn, 0, Qt.AlignVCenter)
            lay.addSpacing(4)
            self._btns.append(btn)
        lay.addStretch(1)

        self.lbl_time = QLabel()
        self.lbl_time.setStyleSheet(
            f"font-size:11px;color:{_c('TEXT_MUTED')};background:transparent;")
        lay.addWidget(self.lbl_time, 0, Qt.AlignVCenter)
        lay.addSpacing(12)

        def _ub(txt, w=30):
            b = QPushButton(txt)
            b.setFixedSize(w, 36)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(self._util_style())
            return b

        bt = _ub("🌙" if not styles.is_dark() else "☀️")
        bt.clicked.connect(self.theme_toggled.emit)
        lay.addWidget(bt, 0, Qt.AlignVCenter)
        lay.addSpacing(8)

        ub = QLabel(f"  {self._username}  ")
        ub.setFixedHeight(34)
        ub.setStyleSheet(
            f"font-size:12px;font-weight:700;color:{AMBER};"
            f"background:rgba(245,158,11,0.12);border-radius:14px;padding:0 4px;")
        lay.addWidget(ub, 0, Qt.AlignVCenter)
        lay.addSpacing(8)

        bl = QPushButton("LOGOUT")
        bl.setFixedSize(80, 36)
        bl.setCursor(Qt.PointingHandCursor)
        bl.setStyleSheet(self._util_style())
        bl.clicked.connect(self.logout_requested.emit)
        lay.addWidget(bl, 0, Qt.AlignVCenter)
        lay.addSpacing(6)

        bx = QPushButton("X")
        bx.setFixedSize(36, 36)
        bx.setCursor(Qt.PointingHandCursor)
        bx.setStyleSheet(
            f"QPushButton{{background:transparent;color:{_c('TEXT_MUTED')};"
            f"border:none;border-radius:14px;font-size:12px;font-weight:700;}}"
            f"QPushButton:hover{{background:{_c('DANGER')};color:white;}}")
        bx.clicked.connect(self.exit_requested.emit)
        lay.addWidget(bx, 0, Qt.AlignVCenter)
        outer.addWidget(self._pill)

    def _util_style(self):
        if styles.is_dark():
            return (
                f"QPushButton{{background:rgba(255,255,255,0.08);color:{_c('TEXT_MUTED')};"
                f"border:none;border-radius:14px;padding:10px;font-size:12px;font-weight:600;}}"
                f"QPushButton:hover{{background:rgba(245,158,11,0.20);color:{AMBER};}}")
        return (
            f"QPushButton{{background:rgba(0,0,0,0.05);color:{_c('TEXT_MUTED')};"
            f"border:none;border-radius:14px;padding:10px;font-size:12px;font-weight:600;}}"
            f"QPushButton:hover{{background:rgba(245,158,11,0.14);color:{AMBER};}}")

    def _style_btn(self, btn, active):
        if active:
            btn.setStyleSheet(
                f"QPushButton{{background:{AMBER};color:#111111;border:none;"
                f"border-radius:17px;font-size:12px;font-weight:700;padding:0 18px;}}"
                f"QPushButton:hover{{background:#FBBF24;}}")
        else:
            btn.setStyleSheet(
                f"QPushButton{{background:transparent;color:{_c('TEXT_MUTED')};"
                f"border:none;border-radius:17px;font-size:12px;font-weight:500;"
                f"padding:0 14px;}}"
                f"QPushButton:hover{{background:rgba(245,158,11,0.10);color:{AMBER};}}")

    def _clicked(self):
        idx = self.sender().property("nav_idx")
        self.set_active(idx)
        self.tab_changed.emit(idx)

    def set_active(self, idx):
        self._cur = idx
        for i, b in enumerate(self._btns):
            self._style_btn(b, i == idx)

    def tick(self, txt):
        self.lbl_time.setText(txt)

    def resizeEvent(self, event):
        m = self.contentsMargins()
        self._pill.setGeometry(
            m.left(), m.top(),
            self.width() - m.left() - m.right(),
            self.height() - m.top() - m.bottom())
        super().resizeEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        m  = self.contentsMargins()
        px, py = m.left(), m.top()
        pw = w - m.left() - m.right()
        ph = h - m.top() - m.bottom()
        r  = ph // 2

        for i in range(6, 0, -1):
            sp  = i * 3
            a   = max(0, 14 - i * 2)
            shc = QColor(155, 105, 15, a) if not styles.is_dark() else QColor(0, 0, 0, a * 2)
            p.setBrush(QBrush(shc)); p.setPen(Qt.NoPen)
            shp = QPainterPath()
            shp.addRoundedRect(
                QRectF(px - sp, py + sp * 0.55, pw + sp * 2, ph + sp * 0.4),
                r + sp, r + sp)
            p.drawPath(shp)

        if styles.is_dark():
            fill = QLinearGradient(px, py, px, py + ph)
            fill.setColorAt(0.0, QColor(28, 30, 44, 228))
            fill.setColorAt(1.0, QColor(20, 22, 34, 232))
        else:
            fill = QLinearGradient(px, py, px, py + ph)
            fill.setColorAt(0.0, QColor(255, 255, 255, 218))
            fill.setColorAt(0.5, QColor(255, 252, 242, 212))
            fill.setColorAt(1.0, QColor(255, 248, 228, 208))

        p.setBrush(QBrush(fill)); p.setPen(Qt.NoPen)
        pill = QPainterPath()
        pill.addRoundedRect(QRectF(px, py, pw, ph), r, r)
        p.drawPath(pill)

        sheen = QLinearGradient(px, py, px, py + ph * 0.45)
        sheen.setColorAt(0.0, QColor(255, 255, 255, 70 if not styles.is_dark() else 15))
        sheen.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(sheen))
        sp2 = QPainterPath()
        sp2.addRoundedRect(QRectF(px, py, pw, ph * 0.45), r, r)
        p.drawPath(sp2)
        p.end()
        # FIX: do NOT call super().paintEvent(event) — causes recursive repaint crash


# ── MainWindow ────────────────────────────────────────────────
class MainWindow(QMainWindow):
    logout_signal = pyqtSignal()

    def __init__(self, username="admin"):
        super().__init__()
        self._username = username
        self.setWindowTitle("SalesTrack")
        self.setMinimumSize(1280, 850)
        self._build_ui()
        self.showFullScreen()
        cur = _make_cursor()
        self.setCursor(cur)
        QApplication.instance().setOverrideCursor(cur)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        central.setStyleSheet(f"background:{_c('BG')};")

        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background:transparent;")

        self.tab_dashboard = DashboardTab()
        self.tab_add       = AddProductTab()
        self.tab_products  = ViewAllProductsTab()
        self.tab_sale      = RecordSaleTab()
        self.tab_sales     = ViewAllSalesTab()

        for t in (self.tab_dashboard, self.tab_add, self.tab_products,
                  self.tab_sale, self.tab_sales):
            self._stack.addWidget(t)

        root.addWidget(self._stack, 1)

        self._nav = BottomPillNav(self._username)
        self._nav.tab_changed.connect(self._on_nav)
        self._nav.theme_toggled.connect(self._toggle_theme)
        self._nav.logout_requested.connect(self._on_logout)
        self._nav.exit_requested.connect(self._on_exit)
        root.addWidget(self._nav)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)
        self._tick()
        self._stack.setCurrentIndex(0)
        self.tab_dashboard.refresh()

    def _tick(self):
        self._nav.tick(datetime.now().strftime("%b %d  %I:%M %p"))

    def _on_nav(self, idx):
        self._stack.setCurrentIndex(idx)
        tabs = [self.tab_dashboard, self.tab_add, self.tab_products,
                self.tab_sale, self.tab_sales]
        tabs[idx].refresh()

    def _toggle_theme(self):
        styles.set_theme(not styles.is_dark())
        QApplication.instance().setStyleSheet(styles.build_stylesheet())
        cur_idx = self._stack.currentIndex()
        self._build_ui()
        self._nav.set_active(cur_idx)
        self._stack.setCurrentIndex(cur_idx)
        cur = _make_cursor()
        self.setCursor(cur)
        QApplication.instance().setOverrideCursor(cur)

    def _on_logout(self):
        if QMessageBox.question(
                self, "Log Out", "Log out of SalesTrack?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No) == QMessageBox.Yes:
            QApplication.instance().restoreOverrideCursor()
            self.logout_signal.emit()
            self.close()

    def _on_exit(self):
        if QMessageBox.question(
                self, "Exit", "Exit SalesTrack?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No) == QMessageBox.Yes:
            QApplication.instance().restoreOverrideCursor()
            QApplication.instance().quit()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_F11:
            self.showNormal() if self.isFullScreen() else self.showFullScreen()
        elif e.key() == Qt.Key_Escape and self.isFullScreen():
            self.showNormal()
        super().keyPressEvent(e)

    def refresh_all(self):
        for t in (self.tab_dashboard, self.tab_add, self.tab_products,
                  self.tab_sale, self.tab_sales):
            t.refresh()