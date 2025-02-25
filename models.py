from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    email = Column(String, unique=True, index=True)
    is_admin = Column(Boolean, default=False)
    activities = relationship("Activity", back_populates="user")
    leaves = relationship("Leave", back_populates="user")
    expenses = relationship("Expense", back_populates="user")

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date)
    client = Column(String)
    project = Column(String)
    activity_type = Column(String)
    achievements = Column(String)
    challenges = Column(String)
    hours = Column(Float)
    user = relationship("User", back_populates="activities")

class Leave(Base):
    __tablename__ = "leaves"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    start_date = Column(Date)
    end_date = Column(Date)
    leave_type = Column(String)
    description = Column(String)
    status = Column(String, default="în așteptare")
    user = relationship("User", back_populates="leaves")

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date)
    project = Column(String)
    amount = Column(Float)
    description = Column(String)
    category = Column(String)
    status = Column(String, default="în așteptare")
    user = relationship("User", back_populates="expenses")

# Funcții helper pentru conversia între modele și dicționare
def user_to_dict(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_admin": user.is_admin
    }

def activity_to_dict(activity):
    return {
        "id": activity.id,
        "user_id": activity.user_id,
        "date": activity.date.isoformat(),
        "client": activity.client,
        "project": activity.project,
        "activity_type": activity.activity_type,
        "achievements": activity.achievements,
        "challenges": activity.challenges,
        "hours": activity.hours
    }

def leave_to_dict(leave):
    return {
        "id": leave.id,
        "user_id": leave.user_id,
        "start_date": leave.start_date.isoformat(),
        "end_date": leave.end_date.isoformat(),
        "leave_type": leave.leave_type,
        "description": leave.description,
        "status": leave.status
    }

def expense_to_dict(expense):
    return {
        "id": expense.id,
        "user_id": expense.user_id,
        "date": expense.date.isoformat(),
        "project": expense.project,
        "amount": expense.amount,
        "description": expense.description,
        "category": expense.category,
        "status": expense.status
    }