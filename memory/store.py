"""
Persistent memory layer — SQLite via SQLAlchemy.
Stores tasks, notes, reminders, and recent conversation context.
"""
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Text,
    DateTime, Boolean, Float
)
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import DB_PATH

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()


class Task(Base):
    __tablename__ = "tasks"
    id        = Column(Integer, primary_key=True)
    user_id   = Column(Integer, nullable=False)
    content   = Column(Text, nullable=False)
    done      = Column(Boolean, default=False)
    priority  = Column(String(10), default="normal")   # low | normal | high
    created   = Column(DateTime, default=datetime.utcnow)
    due       = Column(DateTime, nullable=True)


class Note(Base):
    __tablename__ = "notes"
    id        = Column(Integer, primary_key=True)
    user_id   = Column(Integer, nullable=False)
    content   = Column(Text, nullable=False)
    tags      = Column(String(255), default="")
    created   = Column(DateTime, default=datetime.utcnow)


class Reminder(Base):
    __tablename__ = "reminders"
    id        = Column(Integer, primary_key=True)
    user_id   = Column(Integer, nullable=False)
    content   = Column(Text, nullable=False)
    fire_at   = Column(DateTime, nullable=False)
    sent      = Column(Boolean, default=False)
    created   = Column(DateTime, default=datetime.utcnow)


class ConversationContext(Base):
    __tablename__ = "context"
    id        = Column(Integer, primary_key=True)
    user_id   = Column(Integer, nullable=False)
    role      = Column(String(16))   # user | assistant
    content   = Column(Text)
    created   = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(engine)


# ── Task helpers ──────────────────────────────────────────────

def add_task(user_id: int, content: str, priority: str = "normal", due: datetime = None) -> Task:
    with Session() as s:
        t = Task(user_id=user_id, content=content, priority=priority, due=due)
        s.add(t)
        s.commit()
        s.refresh(t)
        return t


def list_tasks(user_id: int, done: bool = False):
    with Session() as s:
        return s.query(Task).filter_by(user_id=user_id, done=done).all()


def complete_task(task_id: int) -> bool:
    with Session() as s:
        t = s.get(Task, task_id)
        if not t:
            return False
        t.done = True
        s.commit()
        return True


# ── Note helpers ─────────────────────────────────────────────

def add_note(user_id: int, content: str, tags: str = "") -> Note:
    with Session() as s:
        n = Note(user_id=user_id, content=content, tags=tags)
        s.add(n)
        s.commit()
        s.refresh(n)
        return n


def list_notes(user_id: int, limit: int = 10):
    with Session() as s:
        return (
            s.query(Note)
            .filter_by(user_id=user_id)
            .order_by(Note.created.desc())
            .limit(limit)
            .all()
        )


# ── Reminder helpers ─────────────────────────────────────────

def add_reminder(user_id: int, content: str, fire_at: datetime) -> Reminder:
    with Session() as s:
        r = Reminder(user_id=user_id, content=content, fire_at=fire_at)
        s.add(r)
        s.commit()
        s.refresh(r)
        return r


def get_pending_reminders():
    with Session() as s:
        return (
            s.query(Reminder)
            .filter(Reminder.sent == False, Reminder.fire_at <= datetime.utcnow())
            .all()
        )


def mark_reminder_sent(reminder_id: int):
    with Session() as s:
        r = s.get(Reminder, reminder_id)
        if r:
            r.sent = True
            s.commit()


# ── Context helpers ───────────────────────────────────────────

def append_context(user_id: int, role: str, content: str, max_turns: int = 10):
    with Session() as s:
        s.add(ConversationContext(user_id=user_id, role=role, content=content))
        s.commit()
        # Keep only the last max_turns * 2 rows per user
        rows = (
            s.query(ConversationContext)
            .filter_by(user_id=user_id)
            .order_by(ConversationContext.created.desc())
            .all()
        )
        if len(rows) > max_turns * 2:
            for old in rows[max_turns * 2:]:
                s.delete(old)
            s.commit()


def get_context(user_id: int, max_turns: int = 5):
    with Session() as s:
        rows = (
            s.query(ConversationContext)
            .filter_by(user_id=user_id)
            .order_by(ConversationContext.created.asc())
            .all()
        )
        return [{"role": r.role, "content": r.content} for r in rows[-(max_turns * 2):]]
