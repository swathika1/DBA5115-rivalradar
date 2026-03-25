import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from db.database import Base
from db import schemas  # noqa: F401


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_tables_created(db):
    engine = db.bind
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "users" in tables
    assert "pipeline_jobs" in tables
    assert "pipeline_runs" in tables
    assert "scrape_cache" in tables


def test_create_user(db):
    user = schemas.User(email="test@example.com", hashed_password="hash")
    db.add(user)
    db.commit()
    fetched = db.query(schemas.User).filter_by(email="test@example.com").first()
    assert fetched is not None
    assert fetched.id is not None
