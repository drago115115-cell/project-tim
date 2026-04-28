from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    university = Column(String, nullable=True)
    faculty = Column(String, nullable=True)
    course = Column(Integer, nullable=True)
    skills = Column(Text, default="")
    soft_skills = Column(Text, default="")
    role = Column(String, nullable=True)
    portfolio_links = Column(Text, default="")
    about = Column(Text, nullable=True)
    interests = Column(Text, default="")
    rating = Column(Float, default=5.0)
    level = Column(Integer, default=1)
    team_coins = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    projects = relationship("Project", back_populates="creator")
    reviews_received = relationship("Review", foreign_keys="[Review.reviewee_id]", back_populates="reviewee")
    reviews_given = relationship("Review", foreign_keys="[Review.reviewer_id]", back_populates="reviewer")
    badges = relationship("Badge", back_populates="user")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    required_skills = Column(Text, default="")
    required_roles = Column(Text, default="")
    creator_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="open")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    creator = relationship("User", back_populates="projects")

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    reviewee_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    professionalism = Column(Integer, nullable=False)
    deadline_compliance = Column(Integer, nullable=False)
    communication = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    reviewer = relationship("User", foreign_keys=[reviewer_id], back_populates="reviews_given")
    reviewee = relationship("User", foreign_keys=[reviewee_id], back_populates="reviews_received")

class Badge(Base):
    __tablename__ = "badges"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    icon = Column(String, default="🏆")
    earned_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="badges")
