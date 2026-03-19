import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QGraphicsOpacityEffect, QSizePolicy,
)
from PyQt5.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    QPoint, pyqtSignal, QRectF,
)
from PyQt5.QtGui import (
    QColor, QPainter, QBrush, QRadialGradient, QPen,
    QLinearGradient, QFont, QPainterPath, QCursor, QPixmap,
)
from database.database import verify_login

AMBER    = "#F59E0B"
AMBER_LT = "#FCD34D"
ORANGE   = "#F97316"
TEXT_DK  = "#1A1B25"
TEXT_MD  = "#4B5563"
TEXT_SF  = "#9CA3AF"
DANGER   = "#EF4444"


def _make_cursor():
    sz = 26
    px = QPixmap(sz, sz); px.fill(Qt.transparent)
    p = QPainter(px); p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor(AMBER), 2.0)); p.setBrush(Qt.NoBrush)
    p.drawEllipse(2, 2, sz-4, sz-4)
    p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(AMBER)))
    p.drawEllipse(sz//2-3, sz//2-3, 6, 6)
    p.end()
    return QCursor(px, sz//2, sz//2)


# ─────────────────────────────────────────────
#  FloatField — subclass QLineEdit directly
#  FIX: monkey-patching focusInEvent caused
#       recursive calls → stack overflow.
#       Subclassing is safe.
# ─────────────────────────────────────────────
class _InnerEdit(QLineEdit):
    focus_in  = pyqtSignal()
    focus_out = pyqtSignal()

    def focusInEvent(self, e):
        super().focusInEvent(e)
        self.focus_in.emit()

    def focusOutEvent(self, e):
        super().focusOutEvent(e)
        self.focus_out.emit()


class FloatField(QWidget):
    """
    Borderless input with:
    - floating label that slides up when focused/filled
    - amber underline that expands from center on focus
    Both animated with independent QTimers (lerp, no QPropertyAnimation
    so no proxy/effect conflicts).
    """
    def __init__(self, label: str, password: bool = False, parent=None):
        super().__init__(parent)
        self.setFixedHeight(70)
        self._label    = label
        self._focused  = False
        self._has_text = False
        self._line_v   = 0.0   # current underline width fraction
        self._line_t   = 0.0   # target
        self._lbl_v    = 0.0   # current label float (0=down, 1=up)
        self._lbl_t    = 0.0   # target
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

        self._input = _InnerEdit(self)
        if password:
            self._input.setEchoMode(QLineEdit.Password)
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: {TEXT_DK};
                font-size: 15px;
                padding: 0px;
                selection-background-color: {AMBER};
                selection-color: {TEXT_DK};
            }}
        """)
        self._input.focus_in.connect(self._on_focus_in)
        self._input.focus_out.connect(self._on_focus_out)
        self._input.textChanged.connect(self._on_text_changed)

        # Single shared timer — animate both values together
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(12)

    def _on_focus_in(self):
        self._focused = True
        self._line_t  = 1.0
        self._lbl_t   = 1.0

    def _on_focus_out(self):
        self._focused = False
        self._line_t  = 0.0
        if not self._has_text:
            self._lbl_t = 0.0

    def _on_text_changed(self, txt):
        self._has_text = bool(txt)
        if self._has_text:
            self._lbl_t = 1.0
        elif not self._focused:
            self._lbl_t = 0.0

    def _lerp(self, cur, tgt, spd=0.14):
        d = tgt - cur
        return tgt if abs(d) < 0.008 else cur + d * spd

    def _tick(self):
        new_line = self._lerp(self._line_v, self._line_t)
        new_lbl  = self._lerp(self._lbl_v,  self._lbl_t)
        changed  = (new_line != self._line_v or new_lbl != self._lbl_v)
        self._line_v = new_line
        self._lbl_v  = new_lbl
        if changed:
            self.update()

    def resizeEvent(self, e):
        # Input sits in the lower half of the widget
        self._input.setGeometry(0, 38, self.width(), 28)
        super().resizeEvent(e)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Track line — subtle gray
        p.setPen(QPen(QColor(180, 185, 200, 140), 1.0))
        p.drawLine(0, h - 3, w, h - 3)

        # Amber underline — expands from center
        if self._line_v > 0.005:
            half = (w * self._line_v) / 2.0
            cx   = w / 2.0
            p.setPen(QPen(QColor(AMBER), 2.2))
            p.drawLine(int(cx - half), h - 3, int(cx + half), h - 3)

        # Floating label
        # lbl_v=0: y=42 (placeholder position), lbl_v=1: y=6 (floated)
        lbl_y = 42.0 - self._lbl_v * 30.0

        # FIX: QFont only accepts int point size — float caused crash
        pt = 12 if self._lbl_v > 0.5 else 13
        font = QFont("Segoe UI", pt)
        font.setWeight(QFont.Medium if self._lbl_v > 0.5 else QFont.Normal)
        p.setFont(font)

        if self._focused:
            lbl_color = QColor(AMBER)
        elif self._has_text:
            lbl_color = QColor(TEXT_MD)
        else:
            lbl_color = QColor(TEXT_SF)

        p.setPen(lbl_color)
        p.drawText(QRectF(0, lbl_y, w, 20), Qt.AlignLeft | Qt.AlignVCenter, self._label)
        p.end()

    # Public API
    def text(self):           return self._input.text()
    def clear(self):          self._input.clear()
    def setFocus(self):       self._input.setFocus()
    def set_echo(self, show): self._input.setEchoMode(
                                  QLineEdit.Normal if show else QLineEdit.Password)
    def on_return(self, fn):  self._input.returnPressed.connect(fn)
    def on_tab(self, fn):     self._input.returnPressed.connect(fn)


# ─────────────────────────────────────────────
#  DotToggle — show/hide password
#  FIX: removed conflicting QGraphicsEffect.
#       Pure QPainter, no transparency tricks.
# ─────────────────────────────────────────────
class DotToggle(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(38, 38)
        self.setCursor(Qt.PointingHandCursor)
        self._alpha  = 255
        self._target = 255
        self._timer  = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(12)
        self.toggled.connect(lambda on: self.__setattr__('_target', 0 if on else 255))
        self.setStyleSheet("QPushButton { background: transparent; border: none; }")

    def _tick(self):
        d = self._target - self._alpha
        if abs(d) < 5:
            self._alpha = self._target
        else:
            self._alpha += int(d * 0.3)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx, cy, r = self.width()//2, self.height()//2, 7

        solid = QColor(AMBER); solid.setAlpha(self._alpha)
        p.setBrush(QBrush(solid)); p.setPen(Qt.NoPen)
        p.drawEllipse(cx-r, cy-r, r*2, r*2)

        ra = 255 - self._alpha
        ring = QColor(AMBER); ring.setAlpha(ra)
        p.setPen(QPen(ring, 2.0)); p.setBrush(Qt.NoBrush)
        p.drawEllipse(cx-r, cy-r, r*2, r*2)

        inner = QColor(AMBER); inner.setAlpha(ra)
        p.setBrush(QBrush(inner)); p.setPen(Qt.NoPen)
        p.drawEllipse(cx-3, cy-3, 6, 6)
        p.end()


# ─────────────────────────────────────────────
#  GlassCard — white/yellow glassmorphism
#  FIX: removed WA_TranslucentBackground.
#       WA_TranslucentBackground + QGraphicsOpacityEffect
#       on Windows = access violation (0xC0000409).
#       We simulate glass with a near-opaque white
#       gradient + painted shadow layers instead.
# ─────────────────────────────────────────────
class GlassCard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(420)
        # No WA_TranslucentBackground — kills Windows rendering

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        r = 20

        # Layered drop shadow (drawn outside card bounds, amber-tinted)
        for i in range(6, 0, -1):
            spread = i * 5
            alpha  = max(0, 18 - i * 2)
            shadow = QColor(200, 155, 40, alpha)
            p.setBrush(QBrush(shadow))
            p.setPen(Qt.NoPen)
            sx, sy = -spread, spread // 2
            path = QPainterPath()
            path.addRoundedRect(
                QRectF(sx, sy, w + spread*2, h + spread),
                r + spread//2, r + spread//2)
            p.drawPath(path)

        # Card body — warm white gradient (not transparent)
        body = QLinearGradient(0, 0, 0, h)
        body.setColorAt(0.0, QColor(255, 255, 255))
        body.setColorAt(0.5, QColor(255, 253, 245))
        body.setColorAt(1.0, QColor(255, 250, 230))
        p.setBrush(QBrush(body))
        p.setPen(Qt.NoPen)
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), r, r)
        p.drawPath(path)

        # Top sheen — faint white band at top edge
        sheen = QLinearGradient(0, 0, 0, 40)
        sheen.setColorAt(0.0, QColor(255, 255, 255, 180))
        sheen.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(sheen))
        sheen_path = QPainterPath()
        sheen_path.addRoundedRect(QRectF(0, 0, w, 40), r, r)
        p.drawPath(sheen_path)

        p.end()


# ─────────────────────────────────────────────
#  Left Panel — Animated Orb Canvas
# ─────────────────────────────────────────────
class OrbCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, False)
        self._t = 0.0
        self._orbs = [
            (0.42, 0.45, 190, 0.0,  0.38, ("#F97316", "#FBBF24")),
            (0.74, 0.20, 105, 1.2,  0.55, ("#F59E0B", "#FDE68A")),
            (0.16, 0.74,  65, 2.5,  0.75, ("#FB923C", "#FCD34D")),
            (0.10, 0.26,  38, 0.8,  1.05, ("#FBBF24", "#FEF3C7")),
            (0.84, 0.78,  46, 1.9,  0.85, ("#F97316", "#FDBA74")),
        ]
        t = QTimer(self); t.timeout.connect(self._tick); t.start(16)

    def _tick(self):
        self._t += 0.016
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        bg = QLinearGradient(0, 0, w, h)
        bg.setColorAt(0.0, QColor("#090A0D"))
        bg.setColorAt(0.5, QColor("#0F1118"))
        bg.setColorAt(1.0, QColor("#0D0E12"))
        p.fillRect(0, 0, w, h, QBrush(bg))

        pulse = 0.5 + 0.18 * math.sin(self._t * 1.6)
        cx0 = int(self._orbs[0][0] * w)
        cy0 = int(self._orbs[0][1] * h + 20 * math.sin(self._t * self._orbs[0][4]))
        glow = QRadialGradient(cx0, cy0, 300)
        glow.setColorAt(0.0,  QColor(249, 115, 22, int(75 * pulse)))
        glow.setColorAt(0.45, QColor(245, 158, 11, int(30 * pulse)))
        glow.setColorAt(1.0,  QColor(0, 0, 0, 0))
        p.setBrush(QBrush(glow)); p.setPen(Qt.NoPen)
        p.drawEllipse(cx0-300, cy0-300, 600, 600)

        pen = QPen(QColor(255, 255, 255, 7)); pen.setWidthF(1.0)
        p.setPen(pen)
        for x in range(0, w, 40):
            for y in range(0, h, 40):
                p.drawPoint(x, y)

        for i, (cx_f, cy_f, r, phase, speed, cols) in enumerate(self._orbs):
            fy = 20 * math.sin(self._t * speed + phase)
            fx =  7 * math.cos(self._t * speed * 0.65 + phase)
            self._draw_orb(p, int(cx_f*w+fx), int(cy_f*h+fy), r, cols, i==0)

        # Logo
        p.setPen(Qt.NoPen)
        lx, ly = 32, 32
        lg = QLinearGradient(lx, ly, lx+34, ly+34)
        lg.setColorAt(0, QColor(AMBER)); lg.setColorAt(1, QColor(ORANGE))
        p.setBrush(QBrush(lg))
        badge = QPainterPath(); badge.addRoundedRect(lx, ly, 34, 34, 7, 7)
        p.drawPath(badge)
        p.setFont(QFont("Segoe UI", 10, QFont.Bold))
        p.setPen(QColor("#0D0E12"))
        p.drawText(lx, ly, 34, 34, Qt.AlignCenter, "SI")
        p.setFont(QFont("Segoe UI", 13, QFont.Bold))
        p.setPen(QColor("#E8E9EF"))
        p.drawText(lx+44, ly, 200, 34, Qt.AlignVCenter|Qt.AlignLeft, "SalesTrack")

        # Tagline
        p.setFont(QFont("Segoe UI", 27, QFont.Bold))
        p.setPen(QColor("#E8E9EF"))
        p.drawText(32, h-172, w-64, 38, Qt.AlignLeft|Qt.AlignVCenter, "Inventory")
        p.drawText(32, h-130, w-64, 38, Qt.AlignLeft|Qt.AlignVCenter, "Management")
        p.setPen(QColor(AMBER))
        p.drawText(32, h-88,  w-64, 38, Qt.AlignLeft|Qt.AlignVCenter, "Software")
        p.setFont(QFont("Segoe UI", 11))
        p.setPen(QColor("#5A5F72"))
        p.drawText(32, h-46, w-64, 30, Qt.AlignLeft|Qt.AlignVCenter,
                   "Smart. Efficient. Built for your business.")
        p.end()

    def _draw_orb(self, p, cx, cy, r, colors, hero):
        c1, c2 = colors
        sh = QRadialGradient(cx, cy+int(r*0.15), r+20)
        sh.setColorAt(0.5, QColor(0,0,0,50))
        sh.setColorAt(1.0, QColor(0,0,0,0))
        p.setBrush(QBrush(sh)); p.setPen(Qt.NoPen)
        p.drawEllipse(cx-r-20, cy-r-10, (r+20)*2, (r+20)*2)

        g = QRadialGradient(cx-int(r*0.28), cy-int(r*0.28), int(r*1.15))
        top=QColor(c2); mid=QColor(c1)
        bot=QColor(c1); bot.setAlphaF(0.55)
        drk=QColor(c1).darker(210); drk.setAlphaF(0.92)
        g.setColorAt(0.00,top); g.setColorAt(0.38,mid)
        g.setColorAt(0.72,bot); g.setColorAt(1.00,drk)
        p.setBrush(QBrush(g)); p.drawEllipse(cx-r,cy-r,r*2,r*2)

        hr=int(r*0.30); hx=cx-int(r*0.36); hy=cy-int(r*0.36)
        hl=QRadialGradient(hx,hy,hr)
        hl.setColorAt(0.0,QColor(255,255,255,210))
        hl.setColorAt(0.5,QColor(255,255,255,55))
        hl.setColorAt(1.0,QColor(255,255,255,0))
        p.setBrush(QBrush(hl)); p.drawEllipse(hx-hr,hy-hr,hr*2,hr*2)

        rim=QColor(c2); rim.setAlphaF(0.38)
        p.setPen(QPen(rim, 2.2 if hero else 1.3))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(cx-r,cy-r,r*2,r*2)
        p.setPen(Qt.NoPen)


# ─────────────────────────────────────────────
#  Right Panel — Login Form
# ─────────────────────────────────────────────
class LoginForm(QWidget):
    login_attempted = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Warm white/yellow gradient — no transparency
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #FFFBF0, stop:1 #FFF6DC);
            }
        """)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch(1)

        self._card = GlassCard()
        card_lay = QVBoxLayout(self._card)
        card_lay.setContentsMargins(44, 40, 44, 40)
        card_lay.setSpacing(0)

        # Header
        greet = QLabel("Welcome back")
        greet.setStyleSheet(f"color:{TEXT_SF}; font-size:13px; font-weight:500; background:transparent;")
        card_lay.addWidget(greet)
        card_lay.addSpacing(4)

        title = QLabel("Sign in to your account")
        title.setStyleSheet(f"color:{TEXT_DK}; font-size:23px; font-weight:800; background:transparent;")
        card_lay.addWidget(title)
        card_lay.addSpacing(10)

        bar = QFrame()
        bar.setFixedSize(40, 3)
        bar.setStyleSheet(f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {AMBER},stop:1 {ORANGE}); border-radius:2px;")
        card_lay.addWidget(bar)
        card_lay.addSpacing(32)

        # Username
        self._user = FloatField("Username")
        card_lay.addWidget(self._user)
        card_lay.addSpacing(20)

        # Password row
        pw_row = QHBoxLayout()
        pw_row.setSpacing(6)
        pw_row.setContentsMargins(0,0,0,0)
        self._pass = FloatField("Password", password=True)
        self._dot  = DotToggle()
        self._dot.toggled.connect(lambda on: self._pass.set_echo(on))
        pw_row.addWidget(self._pass)
        pw_row.addWidget(self._dot, alignment=Qt.AlignBottom)
        card_lay.addLayout(pw_row)
        card_lay.addSpacing(12)

        # Error
        self._err = QLabel("")
        self._err.setStyleSheet(f"color:{DANGER}; font-size:12px; font-weight:500; background:transparent;")
        self._err.setVisible(False)
        card_lay.addWidget(self._err)
        card_lay.addSpacing(22)

        # Sign in button
        self.btn_login = QPushButton("Sign In  →")
        self.btn_login.setFixedHeight(52)
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {AMBER},stop:1 {ORANGE});
                color: #1A1B25; border: none; border-radius: 12px;
                font-size: 15px; font-weight: 800;
            }}
            QPushButton:hover  {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {AMBER_LT},stop:1 {AMBER}); }}
            QPushButton:pressed {{ background: {ORANGE}; color: #fff; }}
        """)
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.clicked.connect(self._submit)
        self._pass.on_return(self._submit)
        self._user.on_tab(self._pass.setFocus)
        card_lay.addWidget(self.btn_login)
        card_lay.addSpacing(24)

        # Divider
        div = QFrame(); div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("background: rgba(0,0,0,0.07); max-height:1px; border:none;")
        card_lay.addWidget(div)
        card_lay.addSpacing(18)

        # Hint box
        hint = QFrame()
        hint.setStyleSheet("QFrame { background: rgba(245,158,11,0.08); border-radius:10px; }")
        hl = QVBoxLayout(hint)
        hl.setContentsMargins(16, 12, 16, 12);
        hl.setSpacing(4)
        hl.addWidget(QLabel("TEAM:",
                            styleSheet=f"color:{TEXT_SF}; font-size:11px; font-weight:600; background:transparent;"))
        hl.addWidget(QLabel("Harvey Dacillo   ·   Jedrick Villanueva",
                            styleSheet=f"color:{AMBER}; font-size:13px; font-weight:700; background:transparent;"))
        card_lay.addWidget(hint)

        row = QHBoxLayout()
        row.addStretch(); row.addWidget(self._card); row.addStretch()
        outer.addLayout(row)
        outer.addStretch(1)

    def show_error(self, msg):
        self._err.setText(msg); self._err.setVisible(True)

    def clear_error(self):
        self._err.setVisible(False)

    def _submit(self):
        self.login_attempted.emit(self._user.text().strip(), self._pass.text())


# ─────────────────────────────────────────────
#  Login Window
#  FIX: QGraphicsOpacityEffect only applied to
#       simple non-transparent widgets.
#       Never stack on top of WA_TranslucentBackground.
# ─────────────────────────────────────────────
class LoginWindow(QMainWindow):
    login_success = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SalesTrack — Sign In")
        self.setMinimumSize(960, 620)
        self.resize(1140, 700)
        cur = _make_cursor()
        self.setCursor(cur)

        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet("background: #0D0E12;")

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        self._canvas = OrbCanvas()
        layout.addWidget(self._canvas, 55)

        self._form = LoginForm()
        self._form.login_attempted.connect(self._handle_login)
        layout.addWidget(self._form, 45)

        # FIX: Only one QGraphicsOpacityEffect on the form panel (opaque widget).
        # Never apply effects to GlassCard (custom-painted, causes crash on Win).
        eff = QGraphicsOpacityEffect(self._form)
        self._form.setGraphicsEffect(eff)
        eff.setOpacity(0.0)
        self._fade = QPropertyAnimation(eff, b"opacity")
        self._fade.setDuration(700)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.setEasingCurve(QEasingCurve.OutCubic)
        QTimer.singleShot(100, self._fade.start)

    def _handle_login(self, username, password):
        self._form.clear_error()
        if not username:
            self._form.show_error("⚠  Please enter your username.")
            return
        if not password:
            self._form.show_error("⚠  Please enter your password.")
            return
        user = verify_login(username, password)
        if user:
            self.login_success.emit(user["username"])
        else:
            self._form.show_error("⚠  Incorrect username or password.")
            self._form._pass.clear()
            self._form._pass.setFocus()
            self._shake(self._form._card)

    def _shake(self, widget):
        orig = widget.pos()
        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(360)
        anim.setKeyValueAt(0.00, orig)
        anim.setKeyValueAt(0.12, QPoint(orig.x()-13, orig.y()))
        anim.setKeyValueAt(0.28, QPoint(orig.x()+13, orig.y()))
        anim.setKeyValueAt(0.44, QPoint(orig.x()-9,  orig.y()))
        anim.setKeyValueAt(0.60, QPoint(orig.x()+9,  orig.y()))
        anim.setKeyValueAt(0.78, QPoint(orig.x()-4,  orig.y()))
        anim.setKeyValueAt(1.00, orig)
        anim.setEasingCurve(QEasingCurve.InOutSine)
        anim.start()
        self._shake_anim = anim