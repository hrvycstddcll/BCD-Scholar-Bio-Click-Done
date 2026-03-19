import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
import styles
from database.database import init_db
from assets.ui.login import LoginWindow
from dashboard import MainWindow


def main():
    styles.set_theme(dark=False)
    init_db()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setWindowIcon(QIcon("icon.png"))
    app.setStyleSheet(styles.build_stylesheet())

    _main_window = None
    _login_window = None

    def show_login():
        nonlocal _login_window
        _login_window = LoginWindow()
        _login_window.login_success.connect(on_login)
        _login_window.show()

    def on_login(username: str):
        nonlocal _main_window
        if _login_window:
            _login_window.close()
        _main_window = MainWindow(username=username)
        _main_window.logout_signal.connect(show_login)
        _main_window.show()

    show_login()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()