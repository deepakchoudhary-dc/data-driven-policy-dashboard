from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class File(Base):
    __tablename__ = 'files'
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    upload_time = Column(DateTime, default=datetime.utcnow)
    uploader_id = Column(Integer, ForeignKey('users.id'))
    file_url = Column(String, nullable=True)
    extracted_data = relationship('ExtractedData', back_populates='file')

class ExtractedData(Base):
    __tablename__ = 'extracted_data'
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey('files.id'))
    raw_text = Column(Text)
    summary = Column(Text)
    policies = Column(Text)  # JSON-encoded list
    file = relationship('File', back_populates='extracted_data')

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default='user')

class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey('files.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    policy_text = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = relationship('User')
    file = relationship('File') 