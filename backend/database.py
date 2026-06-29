from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

DATABASE_URL = "sqlite:///./prospectiq.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# ── Models ────────────────────────────────────────────────────

class DiscoverySession(Base):
    __tablename__ = "sessions"

    id               = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at       = Column(DateTime, default=datetime.utcnow)
    product_description = Column(Text)
    target_industry  = Column(String)
    company_size     = Column(String)
    target_persona   = Column(String)
    target_location  = Column(String)
    status           = Column(String, default="completed")  # completed / approved / rejected

    # Agent outputs
    plan                = Column(Text)
    icp_profile         = Column(Text)
    companies_found     = Column(Text)
    validated_companies = Column(Text)
    decision_makers     = Column(Text)
    enriched_contacts   = Column(Text)
    recommendations     = Column(Text)


# ── Init ──────────────────────────────────────────────────────

def init_db():
    Base.metadata.create_all(bind=engine)


# ── CRUD ──────────────────────────────────────────────────────

def save_session(inputs: dict, results: dict) -> str:
    db = SessionLocal()
    try:
        session = DiscoverySession(
            id                  = str(uuid.uuid4()),
            product_description = inputs.get("product_description"),
            target_industry     = inputs.get("target_industry"),
            company_size        = inputs.get("target_company_size"),
            target_persona      = inputs.get("target_role"),
            target_location     = inputs.get("target_location"),
            plan                = results.get("plan"),
            icp_profile         = results.get("icp_profile"),
            companies_found     = results.get("companies_found"),
            validated_companies = results.get("validated_companies"),
            decision_makers     = results.get("decision_makers"),
            enriched_contacts   = results.get("enriched_contacts"),
            recommendations     = results.get("recommendations"),
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session.id
    finally:
        db.close()


def get_all_sessions() -> list:
    db = SessionLocal()
    try:
        sessions = db.query(DiscoverySession).order_by(
            DiscoverySession.created_at.desc()
        ).all()
        return [
            {
                "id":               s.id,
                "created_at":       s.created_at.strftime("%d %b %Y, %I:%M %p"),
                "target_industry":  s.target_industry,
                "target_location":  s.target_location,
                "target_persona":   s.target_persona,
                "company_size":     s.company_size,
                "product_description": s.product_description,
                "status":           s.status,
            }
            for s in sessions
        ]
    finally:
        db.close()


def get_session_by_id(session_id: str) -> dict | None:
    db = SessionLocal()
    try:
        s = db.query(DiscoverySession).filter(DiscoverySession.id == session_id).first()
        if not s:
            return None
        return {
            "id":                   s.id,
            "created_at":           s.created_at.strftime("%d %b %Y, %I:%M %p"),
            "product_description":  s.product_description,
            "target_industry":      s.target_industry,
            "company_size":         s.company_size,
            "target_persona":       s.target_persona,
            "target_location":      s.target_location,
            "status":               s.status,
            "plan":                 s.plan,
            "icp_profile":          s.icp_profile,
            "companies_found":      s.companies_found,
            "validated_companies":  s.validated_companies,
            "decision_makers":      s.decision_makers,
            "enriched_contacts":    s.enriched_contacts,
            "recommendations":      s.recommendations,
        }
    finally:
        db.close()


def update_session_status(session_id: str, status: str):
    db = SessionLocal()
    try:
        s = db.query(DiscoverySession).filter(DiscoverySession.id == session_id).first()
        if s:
            s.status = status
            db.commit()
    finally:
        db.close()