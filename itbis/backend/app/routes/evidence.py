from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Incident, Evidence
from app.schemas import EvidenceCreate


router = APIRouter(
    prefix="/evidence",
    tags=["Evidence"]
)


@router.post("/{incident_id}")
def add_evidence(
    incident_id: int,
    evidence_data: EvidenceCreate,
    db: Session = Depends(get_db)
):
    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id)
        .first()
    )

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found"
        )

    evidence = Evidence(
        incident_id=incident_id,
        note=evidence_data.note,
        added_by=evidence_data.added_by
    )

    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    return {
        "message": "Evidence added successfully",
        "evidence_id": evidence.id,
        "incident_id": evidence.incident_id,
        "note": evidence.note,
        "added_by": evidence.added_by,
        "added_at": evidence.added_at
    }


@router.get("/{incident_id}")
def get_evidence(
    incident_id: int,
    db: Session = Depends(get_db)
):
    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id)
        .first()
    )

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found"
        )

    evidence = (
        db.query(Evidence)
        .filter(Evidence.incident_id == incident_id)
        .order_by(Evidence.added_at.asc())
        .all()
    )

    return {
        "incident_id": incident_id,
        "evidence_count": len(evidence),
        "evidence": [
            {
                "evidence_id": item.id,
                "note": item.note,
                "added_by": item.added_by,
                "added_at": item.added_at
            }
            for item in evidence
        ]
    }
