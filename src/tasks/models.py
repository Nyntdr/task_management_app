from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from src.utils.db import Base

class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    is_completed = Column(Boolean, nullable=False, default=False)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))  # Foreign key to the users table
    