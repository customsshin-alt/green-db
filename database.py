from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from auth import hash_password
from models import Base, DocumentItem, PreDiagnosisChecklistTemplate, User, UserRole
from seed_pre_diagnosis import PRE_DIAGNOSIS_TEMPLATE_ROWS

DB_PATH = Path(__file__).resolve().parent / "app.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# PostgreSQL: st.secrets["postgres"] 에서 연결 정보 로드 (Streamlit Cloud / 클라우드 DB)
def _get_postgres_url():
    try:
        import streamlit as st
        if not hasattr(st, "secrets") or not st.secrets:
            return None
        pg = st.secrets.get("postgres")
        if not pg:
            return None
        if isinstance(pg, str):
            return _ensure_sslmode(pg)
        if pg.get("url"):
            return _ensure_sslmode(pg["url"])
        if pg.get("postgres"):
            return _ensure_sslmode(pg["postgres"])
        # dict 형태: host, port, database, user, password
        host = pg.get("host", "localhost")
        port = pg.get("port", 5432)
        database = pg.get("database") or pg.get("dbname", "")
        user = pg.get("user", "")
        password = pg.get("password", "")
        if not database or not user:
            return None
        password = quote_plus(password) if password else ""
        url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        # 클라우드 DB는 대부분 SSL 필요
        url = _ensure_sslmode(url)
        return url
    except Exception:
        return None


def _ensure_sslmode(url: str) -> str:
    """PostgreSQL URL에 sslmode 없으면 require 추가 (클라우드 연결용)."""
    if "postgresql://" not in url and "postgres://" not in url:
        return url
    if "sslmode=" in url or "ssl=" in url:
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}sslmode=require"


_postgres_url = _get_postgres_url()
if _postgres_url:
    DATABASE_URL = _postgres_url

_is_sqlite = DATABASE_URL.startswith("sqlite")
_connect_args = {} if not _is_sqlite else {"check_same_thread": False}
engine = create_engine(DATABASE_URL, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

DEFAULT_DOC_ITEMS = [
    "계약서",
    "상업송장",
    "포장명세서",
    "원산지증명서",
    "보험증권",
]


def init_db() -> None:
    """Create all tables if they do not exist and seed default document items."""
    Base.metadata.create_all(bind=engine)
    # SQLite 기존 DB 마이그레이션 전용 (PostgreSQL 은 create_all 로 스키마 일치)
    from sqlalchemy import text
    if _is_sqlite:
        with engine.connect() as conn:
            for col_sql in [
                "ALTER TABLE users ADD COLUMN is_approved INTEGER DEFAULT 0",
                "ALTER TABLE users ADD COLUMN company_name VARCHAR(255)",
                "ALTER TABLE users ADD COLUMN phone VARCHAR(64)",
                "ALTER TABLE users ADD COLUMN email VARCHAR(255)",
            ]:
                try:
                    conn.execute(text(col_sql))
                    conn.commit()
                except Exception:
                    pass
            try:
                conn.execute(text("UPDATE users SET is_approved=1 WHERE login_id='admin'"))
                conn.commit()
            except Exception:
                pass
            for col_sql in [
                "ALTER TABLE companies ADD COLUMN contact_person VARCHAR(255)",
                "ALTER TABLE companies ADD COLUMN contact_phone VARCHAR(64)",
                "ALTER TABLE companies ADD COLUMN contact_email VARCHAR(255)",
                "ALTER TABLE companies ADD COLUMN address TEXT",
                "ALTER TABLE companies ADD COLUMN assigned_at DATETIME",
                "ALTER TABLE companies ADD COLUMN doc_checklist_completed INTEGER DEFAULT 0",
                "ALTER TABLE companies ADD COLUMN doc_checklist_completed_at DATETIME",
            ]:
                try:
                    conn.execute(text(col_sql))
                    conn.commit()
                except Exception:
                    pass
    session = SessionLocal()
    try:
        existing = session.query(DocumentItem).filter(DocumentItem.company_id.is_(None)).count()
        if existing == 0:
            for i, name in enumerate(DEFAULT_DOC_ITEMS):
                session.add(DocumentItem(company_id=None, name=name, sort_order=i))
            session.commit()
        # 사전진단 체크리스트 양식 템플릿 시드
        template_count = session.query(PreDiagnosisChecklistTemplate).count()
        if template_count == 0:
            for i, (section, item, related_doc, guide_notes) in enumerate(PRE_DIAGNOSIS_TEMPLATE_ROWS):
                session.add(
                    PreDiagnosisChecklistTemplate(
                        section=section,
                        item=item,
                        related_doc=related_doc.strip() or None,
                        guide_notes=guide_notes.strip() or None,
                        sort_order=i,
                    )
                )
            session.commit()
        # 기본 관리자 계정 (admin / 1234)
        admin = session.query(User).filter(User.login_id == "admin").first()
        if not admin:
            session.add(
                User(
                    login_id="admin",
                    password_hash=hash_password("1234"),
                    role=UserRole.ADMIN,
                    is_approved=1,
                    display_name="시스템관리자",
                )
            )
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    # 클라우드 DB 등에서 admin 이 없을 수 있으므로 별도 세션으로 한 번 더 확보
    session2 = SessionLocal()
    try:
        admin = session2.query(User).filter(User.login_id == "admin").first()
        if not admin:
            session2.add(
                User(
                    login_id="admin",
                    password_hash=hash_password("1234"),
                    role=UserRole.ADMIN,
                    is_approved=1,
                    display_name="시스템관리자",
                )
            )
            session2.commit()
    except Exception:
        session2.rollback()
    finally:
        session2.close()


def get_session():
    """Return a new SQLAlchemy session (caller is responsible for closing)."""
    return SessionLocal()


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

