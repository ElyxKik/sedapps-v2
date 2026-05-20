"""Seed a demo organization + user. Idempotent."""
from __future__ import annotations

from app.auth.password import hash_password
from app.db.session import SessionLocal
from app.models.membership import Membership, Role
from app.models.organization import Organization
from app.models.user import User


def main() -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "demo@sedapps.cloud").first()
        if user:
            print("seed: demo user already exists")
            return
        user = User(
            email="demo@sedapps.cloud",
            password_hash=hash_password("demo1234"),
            full_name="Demo User",
        )
        org = Organization(name="Demo Org", plan="free")
        db.add_all([user, org])
        db.flush()
        db.add(Membership(user_id=user.id, org_id=org.id, role=Role.owner))
        db.commit()
        print(f"seed: created user demo@sedapps.cloud / demo1234  org_id={org.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
