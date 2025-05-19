from datetime import datetime

from sqlalchemy import create_engine, String, Integer, DateTime, BigInteger, Column
from sqlalchemy.orm import DeclarativeBase, Session, Mapped, mapped_column

# engine = create_engine('sqlite:///taksi_bot.db', echo=True)
engine = create_engine('postgresql://postgres:1@localhost:5432/taksidb', echo=True)

session = Session(bind=engine)


class Base(DeclarativeBase):
    __abstract__ = True


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True)
    chat_id = Column(BigInteger)
    username = Column(String)
    last_permission_granted = Column(DateTime, nullable=True)
    date_adding = Column(DateTime, default=datetime.utcnow)


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[str] = mapped_column(String, nullable=True)
    full_name: Mapped[str] = mapped_column(String)
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    city: Mapped[str] = mapped_column(String, nullable=True)
    town: Mapped[str] = mapped_column(String, nullable=True)
    type_of_car: Mapped[str] = mapped_column(String, nullable=True)
    tariff: Mapped[str] = mapped_column(String, nullable=False)
    phone_number: Mapped[int] = mapped_column(Integer, nullable=False)
    document: Mapped[str] = mapped_column(String, nullable=True)
    tex_passport: Mapped[str] = mapped_column(String, nullable=True)
    queue: Mapped[int] = mapped_column(Integer, nullable=True)
    route: Mapped[str] = mapped_column(String, nullable=True)
    delivery_time: Mapped[str] = mapped_column(String, nullable=True)

    date_added: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    client_count: Mapped[int] = mapped_column(Integer, nullable=True)

    def __repr__(self):
        return f"<Driver {self.full_name}, Queue: {self.queue}>"


def get_today_drivers():
    today = datetime.now().date()
    today_drivers = session.query(Driver).filter(Driver.date_added >= today).order_by(Driver.queue).all()
    return today_drivers


Base.metadata.create_all(engine)
