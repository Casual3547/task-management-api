from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, Enum, DateTime, func, ForeignKey
from werkzeug.security import check_password_hash,generate_password_hash
# from datetime import datetime

class Base(DeclarativeBase):
    pass

class BaseTable:
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}



db = SQLAlchemy(model_class=Base)

class User(Base,BaseTable):
    __tablename__ = 'users'
    username:Mapped[str] = mapped_column(String(150),nullable=False)
    email:Mapped[str] = mapped_column(String(150),nullable=False,unique=True)
    password_hash:Mapped[str] = mapped_column(String(150),nullable=False)
    tasks:Mapped[list['Task']] = relationship(back_populates="user")
    def set_password(self,password):
        self.password_hash = generate_password_hash(password,method='pbkdf2:sha256',salt_length=8,)
    def check_password(self,password):
        return check_password_hash(self.password_hash,password)
class Task(Base,BaseTable):
    __tablename__ = "tasks"
    title: Mapped[str] = mapped_column(String(150),nullable=False)
    description:Mapped[str] = mapped_column(String(300),nullable=False)
    status:Mapped[str] = mapped_column(Enum("Pending", "In Progress", "Completed",name="task_status"))
    priority: Mapped[str] = mapped_column(Enum("Low", "Medium", "High",name="task_priority"))
    created_at: Mapped[DateTime] = mapped_column(DateTime,default=func.now())
    due_date:Mapped[DateTime] = mapped_column(DateTime,nullable=True)
    user_id:Mapped[int] = mapped_column(ForeignKey('users.id'))
    user:Mapped['User'] = relationship(back_populates='tasks')


class RevokedToken(Base,BaseTable):
    __tablename__ = "revoked_tokens"
    jti:Mapped[str] = mapped_column(String(200),nullable=False,unique=True)
    token_type:Mapped[str] = mapped_column(Enum("access","refresh",name="token_type"),nullable=False)
    revoked_at:Mapped[DateTime] = mapped_column(DateTime,default=func.now())