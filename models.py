from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class UserRole(enum.Enum):
    ADMIN = "관리자"
    DREAM = "관세법인 드림"
    KEITI = "한국환경산업기술원"
    COMPANY = "지원기업"

    @property
    def label(self) -> str:
        return self.value


class ExportStep(enum.Enum):
    DOC_PREP = "서류준비"
    PRE_SHIPMENT = "선적준비"
    EXPORT_CLEARANCE = "수출통관"
    PICKUP = "픽업"
    WAITING_DEPARTURE = "출항대기"
    DEPARTURE = "출항"
    INTERNATIONAL_TRANSPORT = "국제운송"
    ARRIVAL = "입항"
    IMPORT_CLEARANCE = "수입통관"
    ARRIVED_LOCAL = "현지 도착"

    @property
    def label(self) -> str:
        return self.value

    def __str__(self) -> str:  # for display in Streamlit selectbox
        return self.value


class Company(Base):
    """한국환경산업기술원이 등록한 지원기업."""
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    application_info = Column(Text, nullable=True)
    assigned_consultant = Column(String(255), nullable=True)
    assigned_at = Column(DateTime, nullable=True)  # 관세법인 드림 배정일자
    # 지원기업 등록 시 입력 정보
    contact_person = Column(String(255), nullable=True)   # 담당자
    contact_phone = Column(String(64), nullable=True)     # 연락처
    contact_email = Column(String(255), nullable=True)     # 이메일
    address = Column(Text, nullable=True)                  # 주소
    doc_checklist_completed = Column(Integer, default=0)   # 서류준비 완료 버튼
    doc_checklist_completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    pre_analyses = relationship("PreAnalysis", back_populates="company")
    execution_plans = relationship("ExecutionPlan", back_populates="company")
    close_supports = relationship("CloseSupport", back_populates="company")
    hs_code_reports = relationship("HSCodeReport", back_populates="company")
    doc_checklist_statuses = relationship("DocChecklistStatus", back_populates="company")
    delivery_events = relationship("DeliveryTimelineEvent", back_populates="company")


class Consultant(Base):
    """관세법인 드림이 등록한 관세사 목록 (담당 관세사 배정 시 드롭다운용)."""
    __tablename__ = "consultants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ResultReport(Base):
    """결과보고서(배송완료 판단용) - 모든 역할 조회 가능, 업로드는 관세법인/관리자."""
    __tablename__ = "result_reports"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    file_path = Column(String(512), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", backref="result_reports")


class HistoryEntry(Base):
    """업체별 히스토리 (진행이력)"""
    __tablename__ = "history_entries"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    process = Column(String(128), nullable=False)  # 예: 사전진단, HS code확정, 수행계획서 등
    status = Column(Text, nullable=False)          # 상세 진행상태/메모
    actor = Column(String(255), nullable=True)     # 작업자 이름 또는 아이디
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    company = relationship("Company", backref="history_entries")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    login_id = Column(String(128), nullable=False, unique=True, index=True)
    password_hash = Column(String(128), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)  # 지원기업일 때만
    is_approved = Column(Integer, default=0)  # 0=대기, 1=승인(로그인 가능)

    # 회원가입 시 입력 항목
    company_name = Column(String(255), nullable=True)   # 업체명
    display_name = Column(String(255), nullable=True)   # 이름
    phone = Column(String(64), nullable=True)          # 전화번호
    email = Column(String(255), nullable=True)         # 메일주소

    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", backref="users")
    profile_update_requests = relationship("PendingProfileUpdate", back_populates="user", foreign_keys="PendingProfileUpdate.user_id")
    decided_profile_requests = relationship("PendingProfileUpdate", back_populates="decided_by_admin", foreign_keys="PendingProfileUpdate.decided_by")


class PendingProfileUpdate(Base):
    """회원 정보 수정 요청(비밀번호 제외) — 관리자 승인 후 반영."""
    __tablename__ = "pending_profile_updates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    requested_company_name = Column(String(255), nullable=True)
    requested_display_name = Column(String(255), nullable=True)
    requested_phone = Column(String(64), nullable=True)
    requested_email = Column(String(255), nullable=True)
    status = Column(String(20), default="pending")  # pending / approved / rejected
    requested_at = Column(DateTime, default=datetime.utcnow)
    decided_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    decided_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="profile_update_requests", foreign_keys=[user_id])
    decided_by_admin = relationship("User", back_populates="decided_profile_requests", foreign_keys=[decided_by])


class PreAnalysis(Base):
    __tablename__ = "pre_analyses"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    checklist_path = Column(String(512), nullable=True)
    trade_report_path = Column(String(512), nullable=True)
    benefit_analysis_path = Column(String(512), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="pre_analyses")


class PreDiagnosisChecklistTemplate(Base):
    """사전진단 체크리스트 양식(엑셀) 항목: 구분, 항목, 관련 서류, 비고/가이드."""
    __tablename__ = "pre_diagnosis_checklist_templates"

    id = Column(Integer, primary_key=True, index=True)
    section = Column(String(128), nullable=False)   # 구분
    item = Column(String(255), nullable=False)    # 항목
    related_doc = Column(String(255), nullable=True)  # 관련 서류
    guide_notes = Column(Text, nullable=True)      # 비고/가이드
    sort_order = Column(Integer, default=0)

    responses = relationship("PreDiagnosisChecklistResponse", back_populates="template")


class PreDiagnosisChecklistResponse(Base):
    """기업별 사전진단 체크리스트 응답: 내용, 수취/요청/없음, Comment."""
    __tablename__ = "pre_diagnosis_checklist_responses"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("pre_diagnosis_checklist_templates.id"), nullable=False, index=True)
    content = Column(Text, nullable=True)         # 내용
    received = Column(Integer, default=0)         # 수취 0/1
    requested = Column(Integer, default=0)        # 요청 0/1
    none_status = Column(Integer, default=0)      # 없음 0/1
    comment = Column(Text, nullable=True)         # Comment / Action Item
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", backref="pre_diagnosis_responses")
    template = relationship("PreDiagnosisChecklistTemplate", back_populates="responses")


class PreDiagnosisAttachment(Base):
    """사전진단체크리스트 첨부자료 (제목 + 파일)."""
    __tablename__ = "pre_diagnosis_attachments"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", backref="pre_diagnosis_attachments")


class TradeEnvironmentReport(Base):
    """수입국 통상환경 분석 보고서(정형 항목)."""
    __tablename__ = "trade_environment_reports"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)

    # 해당 HS code 유효성 검토
    hs_code_validity = Column(Text, nullable=True)
    # 해당 국가 HS code 세부 분류 기준 검토 결과
    hs_detail_criteria = Column(Text, nullable=True)
    # 수입국 통관 상 제약사항 검토 결과
    import_constraints = Column(Text, nullable=True)
    # 수입국 통관 후 제약사항 검토 결과
    post_import_constraints = Column(Text, nullable=True)
    # 기타 관세납부, 인증, 요건 관련 검토 결과
    duty_cert_requirements = Column(Text, nullable=True)
    # 기타 물류 상 주요 고려사항 검토 결과
    logistics_considerations = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", backref="trade_environment_reports")


class ExecutionPlan(Base):
    __tablename__ = "execution_plans"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    plan_file_path = Column(String(512), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="execution_plans")


class CloseSupport(Base):
    __tablename__ = "close_supports"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)

    # 서류준비 체크리스트(간단 문자열 저장)
    doc_prep_checklist = Column(Text, nullable=True)
    checklist_file_path = Column(String(512), nullable=True)

    # 물류사 선정 및 물류비 비교
    logistics_report = Column(Text, nullable=True)
    logistics_cost_comparison = Column(Text, nullable=True)

    # 수출진행상황(10단계)
    export_step = Column(Enum(ExportStep), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="close_supports")


class HSCodeReport(Base):
    """품목분류(HS code) 결과보고서 - 관세법인 드림 업로드."""
    __tablename__ = "hs_code_reports"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    file_path = Column(String(512), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="hs_code_reports")


class DocumentItem(Base):
    """서류 항목: company_id=NULL이면 기본 요청서류, 아니면 관세법인이 해당 기업에 추가한 항목."""
    __tablename__ = "document_items"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)  # NULL = 기본
    name = Column(String(255), nullable=False)
    sort_order = Column(Integer, default=0)

    statuses = relationship("DocChecklistStatus", back_populates="document_item")


class DocChecklistStatus(Base):
    """기업별 서류준비 체크리스트 상태 (각 서류별 체크 + 파일)."""
    __tablename__ = "doc_checklist_statuses"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    document_item_id = Column(Integer, ForeignKey("document_items.id"), nullable=False, index=True)
    is_checked = Column(Integer, default=0)  # 0/1
    file_path = Column(String(512), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="doc_checklist_statuses")
    document_item = relationship("DocumentItem", back_populates="statuses")


class DeliveryTimelineEvent(Base):
    """배송일정 타임라인: 10단계별 계획일/완료일 기록."""
    __tablename__ = "delivery_timeline_events"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    stage = Column(Enum(ExportStep), nullable=False)
    planned_date = Column(DateTime, nullable=True)
    actual_completed_at = Column(DateTime, nullable=True)  # 달성 시 관세법인 드림이 기록
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="delivery_events")

