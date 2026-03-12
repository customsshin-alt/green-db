# -*- coding: utf-8 -*-
"""로그인/인증 유틸 (해시 비밀번호, 세션)."""
from __future__ import annotations

import hashlib
from typing import Optional

from sqlalchemy.orm import Session

from models import Company, User


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, stored_hash: str) -> bool:
    return hash_password(password) == stored_hash


def get_user_by_login(session: Session, login_id: str) -> Optional[User]:
    return session.query(User).filter(User.login_id == login_id.strip()).first()


def authenticate(session: Session, login_id: str, password: str) -> Optional[User]:
    user = get_user_by_login(session, login_id)
    if not user or not verify_password(password, user.password_hash):
        return None
    if getattr(user, "is_approved", 0) != 1:
        return None
    return user


def get_company_for_user(session: Session, user: User) -> Optional[Company]:
    if not user.company_id:
        return None
    return session.query(Company).filter(Company.id == user.company_id).first()
