from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Float, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.pool import StaticPool

DATABASE_URL = "sqlite:///./coding_platform.db"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    constraints = Column(Text)
    time_limit_ms = Column(Integer, default=1000) # Default 1 sec
    
    test_cases = relationship("TestCase", back_populates="question", cascade="all, delete-orphan")

class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    input_data = Column(Text)
    expected_output = Column(Text)
    is_sample = Column(Boolean, default=False)
    
    question = relationship("Question", back_populates="test_cases")

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
