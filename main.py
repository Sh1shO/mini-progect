from PySide6.QtWidgets import QApplication, QDialog
from app import LoginWindow, MainWindow

if __name__ == "__main__":
    app = QApplication([])

    login_window = LoginWindow()
    if login_window.exec() == QDialog.Accepted:
        main_window = MainWindow(login_window.user)
        main_window.show()

    app.exec()
