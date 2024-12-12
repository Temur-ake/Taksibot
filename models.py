from sqlalchemy import create_engine, BIGINT
from sqlalchemy.dialects.mysql import VARCHAR
from sqlalchemy.orm import DeclarativeBase, declared_attr, Session
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

engine = create_engine(f'postgresql+psycopg2://postgres:1@localhost:5449/taksi_bot')
session = Session(bind=engine)


class Base(DeclarativeBase):
    @declared_attr
    def __tablename__(self) -> str:
        return self.__name__.lower() + 's'


# models.py
from datetime import datetime, timedelta


class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BIGINT)
    username: Mapped[str] = mapped_column(VARCHAR(255), nullable=True)
    chat_id: Mapped[str] = mapped_column(VARCHAR(255), nullable=True)
    last_permission_granted: Mapped[datetime] = mapped_column(nullable=True)

    def grant_permission(self, duration: timedelta):
        self.last_permission_granted = datetime.now() + duration


Base.metadata.create_all(engine)
