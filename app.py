from db import get_session, Users, Payments
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QComboBox, QLineEdit, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QDateEdit, QHBoxLayout, QMessageBox, QDialog, QSpinBox, QDoubleSpinBox
from PySide6.QtCore import Qt, QDate
from datetime import datetime
from db import get_session, Users
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os, csv

from fpdf import FPDF
from PySide6.QtWidgets import QMessageBox
import os


class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Вход в систему')
        self.setGeometry(100, 100, 400, 200)
        self.user = None  # Для сохранения информации об авторизованном пользователе

        self.layout = QVBoxLayout()

        self.label = QLabel('Введите логин и пароль')
        self.layout.addWidget(self.label)

        self.user_combo = QComboBox()
        self.layout.addWidget(self.user_combo)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.layout.addWidget(self.password_input)

        self.login_button = QPushButton('Войти')
        self.login_button.clicked.connect(self.handle_login)
        self.layout.addWidget(self.login_button)

        self.exit_button = QPushButton('Выход')
        self.exit_button.clicked.connect(self.reject)  # Закрывает окно авторизации
        self.layout.addWidget(self.exit_button)

        self.setLayout(self.layout)
        self.load_users()

    def load_users(self):
        """Загружаем пользователей в выпадающий список"""
        session = get_session()
        users = session.query(Users).all()
        self.user_combo.clear()
        for user in users:
            self.user_combo.addItem(user.login)
        session.close()

    def handle_login(self):
        """Обрабатываем вход пользователя"""
        login = self.user_combo.currentText()
        password = self.password_input.text()

        session = get_session()
        user = session.query(Users).filter(Users.login == login).first()
        session.close()

        if user and user.password == password:
            self.user = user  # Сохраняем авторизованного пользователя
            self.accept()  # Закрываем окно авторизации с успехом
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль!")

    def accept_login(self, user):
        """Переход в основное окно"""
        self.main_window = MainWindow(user)
        self.main_window.show()
        self.close()

    def show_error(self, message):
        """Отображаем ошибку"""
        error_window = QWidget()
        error_window.setWindowTitle("Ошибка")
        layout = QVBoxLayout()
        error_label = QLabel(message, error_window)
        layout.addWidget(error_label)
        error_window.setLayout(layout)
        error_window.show()


class AddPaymentWindow(QDialog):
    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("Добавить платеж")
        self.setGeometry(200, 200, 300, 200)

        self.layout = QVBoxLayout()

        # Поле для категории
        self.category_label = QLabel("Категория:")
        self.layout.addWidget(self.category_label)

        self.category_combo = QComboBox(self)
        self.load_categories()
        self.layout.addWidget(self.category_combo)

        # Поле для названия платежа
        self.name_label = QLabel("Название платежа:")
        self.layout.addWidget(self.name_label)

        self.name_input = QLineEdit(self)
        self.layout.addWidget(self.name_input)

        # Поле для количества
        self.quantity_label = QLabel("Количество:")
        self.layout.addWidget(self.quantity_label)

        self.quantity_input = QSpinBox(self)
        self.quantity_input.setValue(1)
        self.layout.addWidget(self.quantity_input)

        # Поле для цены
        self.price_label = QLabel("Цена:")
        self.layout.addWidget(self.price_label)

        self.price_input = QDoubleSpinBox(self)
        self.price_input.setPrefix("₽ ")
        self.price_input.setDecimals(2)
        self.layout.addWidget(self.price_input)

        # Кнопки добавления и отмены
        self.button_layout = QHBoxLayout()

        self.add_button = QPushButton("Добавить", self)
        self.add_button.clicked.connect(self.add_payment)
        self.button_layout.addWidget(self.add_button)

        self.cancel_button = QPushButton("Отменить", self)
        self.cancel_button.clicked.connect(self.reject)
        self.button_layout.addWidget(self.cancel_button)

        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout)

    def load_categories(self):
        """Загружаем категории в выпадающий список"""
        session = get_session()
        categories = session.query(Payments.category).distinct().all()
        self.category_combo.addItem("-")
        for category in categories:
            self.category_combo.addItem(category[0])
        session.close()

    def add_payment(self):
        """Добавление платежа в базу данных"""
        category = self.category_combo.currentText()
        name = self.name_input.text()
        quantity = self.quantity_input.value()
        price = self.price_input.value()

        if not name.strip():
            QMessageBox.warning(self, "Ошибка", "Название платежа не может быть пустым!")
            return

        session = get_session()
        new_payment = Payments(
            user_id=self.user.user_id,
            date=datetime.utcnow(),  # Правильное использование datetime.utcnow()
            category=category,
            name=name,
            quantity=quantity,
            price=price,
            total=quantity * price
            # Не указываем поле `date`, чтобы база данных заполнила его автоматически
        )
        session.add(new_payment)
        session.commit()
        session.close()

        QMessageBox.information(self, "Успех", "Платеж успешно добавлен!")
        self.accept()  # Закрываем окно


class MainWindow(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setWindowTitle('Основное окно')
        self.setGeometry(100, 100, 900, 600)

        self.layout = QVBoxLayout()
        self.filter_panel = QHBoxLayout()

        self.add_button = QPushButton("+")
        self.delete_button = QPushButton("-")
        self.filter_panel.addWidget(self.add_button)
        self.filter_panel.addWidget(self.delete_button)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate(2015, 1, 1))
        self.filter_panel.addWidget(QLabel("С"))
        self.filter_panel.addWidget(self.date_from)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate(2015, 12, 31))
        self.filter_panel.addWidget(QLabel("По"))
        self.filter_panel.addWidget(self.date_to)

        self.category_combo = QComboBox()
        self.filter_panel.addWidget(QLabel("Категория:"))
        self.filter_panel.addWidget(self.category_combo)

        self.filter_button = QPushButton("Выбрать")
        self.clear_button = QPushButton("Очистить")
        self.report_button = QPushButton("Генерировать отчет")
        self.filter_panel.addWidget(self.filter_button)
        self.filter_panel.addWidget(self.clear_button)
        self.filter_panel.addWidget(self.report_button)

        self.filter_button.clicked.connect(self.open_login_window)

        # Связываем кнопку с методом генерации отчета
        self.report_button.clicked.connect(self.generate_report)

        self.layout.addLayout(self.filter_panel)

        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Наименование платежа", "Количество", "Цена", "Сумма", "Категория"])
        self.layout.addWidget(self.table)

        self.setLayout(self.layout)

        self.load_categories()
        self.load_data()

    def generate_report(self):
        try:
            # Загружаем данные из базы данных
            session = get_session()  # Получаем сессию для работы с базой данных
            payments = session.query(Payments).filter(Payments.user_id == self.user.user_id).all()

            # Создаем объект PDF
            pdf = FPDF()
            pdf.add_page()

            # Проверяем наличие шрифта и добавляем его
            font_path = './FreeSans.ttf'  # Путь к шрифту
            if os.path.exists(font_path):
                pdf.add_font('FreeSans', '', font_path, uni=True)
                pdf.set_font('FreeSans', '', 12)
            else:
                QMessageBox.warning(self, "Ошибка шрифта", "Шрифт FreeSans не найден.")
                return

            # Заголовок отчета
            pdf.cell(200, 10, txt="Список платежей", ln=True, align='C')
            pdf.ln(10)  # Отступ

            # Группируем платежи по категориям
            categories = {}  # Словарь для категорий
            for payment in payments:
                if payment.category not in categories:
                    categories[payment.category] = []
                categories[payment.category].append(payment)

            total_amount = 0  # Общая сумма всех платежей

            # Добавляем данные по категориям
            for category, category_payments in categories.items():
                # Заголовок категории
                pdf.set_font('FreeSans','',  12)
                pdf.cell(200, 10, category, ln=True, align='L')
                pdf.set_font('FreeSans', '', 12)

                # Строки для каждого платежа
                for payment in category_payments:
                    pdf.cell(100, 10, payment.name, border=0)
                    pdf.cell(40, 10, f"{payment.price:.2f} р.", border=0, align='R')
                    pdf.ln()
                    total_amount += payment.price

                pdf.ln(5)  # Отступ между категориями

            # Итоговая сумма
            pdf.set_font('FreeSans', '', 12)
            pdf.cell(40, 20, "Итого: " + f"{total_amount:.2f} р.", ln=True, align='R')

            # Сохраняем PDF на диск
            pdf_output_path = f"./report_{self.user.user_id}.pdf"  # Путь для сохранения отчета
            pdf.output(pdf_output_path)

            # Показать сообщение о завершении
            QMessageBox.information(self, "Экспорт завершен", f"Отчет был успешно экспортирован в {pdf_output_path}.")

            session.close()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка экспорта", f"Произошла ошибка при экспорте в PDF: {str(e)}")

    def load_data(self):
        """Загрузка данных платежей"""
        session = get_session()
        payments = session.query(Payments).filter(Payments.user_id == self.user.user_id).all()
        self.table.setRowCount(len(payments))
        for row, payment in enumerate(payments):
            self.table.setItem(row, 0, QTableWidgetItem(payment.name))
            self.table.setItem(row, 1, QTableWidgetItem(str(payment.quantity)))
            self.table.setItem(row, 2, QTableWidgetItem(f"{payment.price:.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{payment.total:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(payment.category))
        session.close()

    def load_categories(self):
        """Загрузка категорий в выпадающий список"""
        session = get_session()
        categories = session.query(Payments.category).distinct().all()
        self.category_combo.clear()
        self.category_combo.addItem("-")
        for category in categories:
            self.category_combo.addItem(category[0])
        session.close()

    def open_login_window(self):
        """Закрыть текущее окно и открыть окно авторизации"""
        self.close()  # Закрываем текущее окно

        login_window = LoginWindow()
        if login_window.exec() == QDialog.Accepted:  # Если авторизация прошла успешно
            new_user = login_window.user
            if new_user:
                self.new_main_window = MainWindow(new_user)  # Создаем новое окно
                self.new_main_window.show()

            
    def handle_login(self):
        """Обрабатываем вход пользователя"""
        login = self.user_combo.currentText()
        password = self.password_input.text()

        session = get_session()
        user = session.query(Users).filter(Users.login == login).first()
        session.close()

        if user and user.password == password:
            QMessageBox.information(self, "Успех", "Добро пожаловать!")
            self.accept_login(user)  # Передаем авторизованного пользователя
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль!")


    def load_data(self):
        """Загрузка данных о платежах"""
        session = get_session()
        payments = session.query(Payments).filter(Payments.user_id == self.user.user_id).all()

        self.table.setRowCount(len(payments))
        for row, payment in enumerate(payments):
            self.table.setItem(row, 0, QTableWidgetItem(payment.name))
            self.table.setItem(row, 1, QTableWidgetItem(str(payment.quantity)))
            self.table.setItem(row, 2, QTableWidgetItem(f"{payment.price:.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{payment.total:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(payment.category))

        session.close()

    def load_categories(self):
        """Загрузка категорий в выпадающий список"""
        session = get_session()
        categories = session.query(Payments.category).distinct().all()
        self.category_combo.clear()
        self.category_combo.addItem("-")
        for category in categories:
            self.category_combo.addItem(category[0])
        session.close()

    def delete_payment(self):
        """Удаление выбранного платежа"""
        self.load_data()
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, выберите запись для удаления!")
            return

        record_name = self.table.item(selected_row, 0).text()
        payment_id = self.get_payment_id(selected_row)

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить запись «{record_name}»?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            session = get_session()
            payment = session.query(Payments).get(payment_id)
            if payment:
                session.delete(payment)
                session.commit()
                session.close()

                QMessageBox.information(self, "Успех", "Запись успешно удалена!")
                self.load_data()
            else:
                session.close()
                QMessageBox.warning(self, "Ошибка", "Запись не найдена!")

    def get_payment_id(self, row):
        """Получить ID платежа из строки таблицы"""
        session = get_session()
        payment_name = self.table.item(row, 0).text()
        payment = session.query(Payments).filter_by(name=payment_name, user_id=self.user.user_id).first()
        session.close()
        return payment.id if payment else None

    def open_add_payment_window(self):
        """Открыть окно добавления платежа"""
        add_payment_window = AddPaymentWindow(self, user=self.user)
        if add_payment_window.exec():
            self.load_data()

    def filter_by_category(self):
        """Фильтрует платежи при выборе категории"""
        selected_category = self.category_combo.currentText()

        session = get_session()

        if selected_category == "-":
            payments = session.query(Payments).filter(Payments.user_id == self.user.user_id).all()
        else:
            payments = (
                session.query(Payments)
                .filter(Payments.user_id == self.user.user_id, Payments.category == selected_category)
                .all()
            )

        self.table.setRowCount(len(payments))
        for row, payment in enumerate(payments):
            self.table.setItem(row, 0, QTableWidgetItem(payment.name))
            self.table.setItem(row, 1, QTableWidgetItem(str(payment.quantity)))
            self.table.setItem(row, 2, QTableWidgetItem(f"{payment.price:.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{payment.total:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(payment.category))

        session.close()
