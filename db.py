import datetime
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base


# Подключение к базе данных PostgreSQL
DATABASE_URI = 'postgresql://postgres:1234@localhost:5432/asd'  # Замените на свои данные
engine = create_engine(DATABASE_URI)


# Базовый класс для создания моделей
Base = declarative_base()


# Создание сессии для работы с БД
Session = sessionmaker(bind=engine)
session = Session()


# Модель для пользователей
class Users(Base):
    __tablename__ = 'users'
   
    user_id = Column(Integer, primary_key=True)
    fio = Column(String(255), nullable=False)
    login = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)  # Пароль хранится в открытом виде
    pin_code = Column(String(10))


# Модель для платежей
class Payments(Base):
    __tablename__ = 'payments'
   
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)  # Исправлено на datetime.datetime.utcnow
    category = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)  # Цена в рублях
    total = Column(Integer, nullable=False)  # Стоимость платежа

    # Связь с таблицей пользователей
    user = relationship("Users")


def get_session():
    """Возвращаем сессию для работы с базой данных"""
    return session
