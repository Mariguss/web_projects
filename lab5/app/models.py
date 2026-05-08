from typing import Optional
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    users: Mapped[list["User"]] = relationship(back_populates="role")

from flask_login import UserMixin

class User(Base, UserMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    middle_name: Mapped[Optional[str]] = mapped_column(String(50))
    
    role_id: Mapped[Optional[int]] = mapped_column(ForeignKey("roles.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    role: Mapped[Optional["Role"]] = relationship(back_populates="users")
    visit_logs: Mapped[list["VisitLogs"]] = relationship(back_populates="user")
    
    @property
    def fio(self):
        parts = [self.last_name, self.first_name, self.middle_name]
        return " ".join([p for p in parts if p])

class VisitLogs(Base):
    __tablename__ = "visit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String(100))
    
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    user: Mapped[Optional["User"]] = relationship(back_populates="visit_logs")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

