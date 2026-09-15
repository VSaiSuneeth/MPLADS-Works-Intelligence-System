from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
import uuid
from datetime import datetime, timezone

from app.models.case import Case, CaseAction
from app.models.work import Work
from app.models.user import User
from app.services.audit_service import AuditService

class CaseService:
    @staticmethod
    def create_case(
        db: Session,
        creator_id: str,
        work_id: str,
        summary: str,
        priority: str = "HIGH",
        initial_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        work = db.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise ValueError(f"Work with ID {work_id} not found.")

        # Check existing open cases for work
        existing = db.query(Case).filter(
            Case.work_id == work_id,
            Case.status.in_(["DETECTED", "TRIAGED", "ASSIGNED", "UNDER_REVIEW", "CLARIFICATION_REQUESTED"])
        ).first()

        if existing:
            return CaseService.get_case_detail(db, existing.id)

        case_count = db.query(Case).count() + 1
        case_number = f"CASE-2026-{case_count:04d}"

        case_obj = Case(
            id=str(uuid.uuid4()),
            case_number=case_number,
            work_id=work_id,
            created_by=creator_id,
            status="DETECTED",
            priority=priority,
            summary=summary
        )
        db.add(case_obj)
        db.flush()

        # Record Initial Action
        initial_action = CaseAction(
            id=str(uuid.uuid4()),
            case_id=case_obj.id,
            actor_id=creator_id,
            action_type="CASE_CREATED",
            from_status=None,
            to_status="DETECTED",
            note=initial_notes or f"Case opened for review on work {work.external_id}."
        )
        db.add(initial_action)
        db.commit()

        AuditService.log_action(
            db,
            action="CASE_CREATED",
            entity_type="Case",
            user_id=creator_id,
            entity_id=case_obj.id,
            details_json={"case_number": case_number, "work_id": work_id, "priority": priority}
        )

        return CaseService.get_case_detail(db, case_obj.id)

    @staticmethod
    def list_cases(
        db: Session,
        authorized_jurisdiction_ids: List[str],
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        jurisdiction_id: Optional[str] = None,
        work_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 25
    ) -> Dict[str, Any]:
        query = db.query(Case).join(Work)

        if jurisdiction_id:
            if jurisdiction_id in authorized_jurisdiction_ids or "ALL" in authorized_jurisdiction_ids:
                query = query.filter(Work.jurisdiction_id == jurisdiction_id)
            else:
                query = query.filter(Work.id == "none")
        elif "ALL" not in authorized_jurisdiction_ids:
            query = query.filter(Work.jurisdiction_id.in_(authorized_jurisdiction_ids))

        if status_filter and status_filter != "ALL":
            if status_filter == "OPEN":
                query = query.filter(Case.status.in_(["DETECTED", "TRIAGED", "ASSIGNED", "UNDER_REVIEW"]))
            else:
                query = query.filter(Case.status == status_filter)

        if priority_filter and priority_filter != "ALL":
            query = query.filter(Case.priority == priority_filter)

        if work_id:
            query = query.filter(Case.work_id == work_id)

        total = query.count()
        offset = (page - 1) * page_size
        cases = query.options(
            joinedload(Case.work),
            joinedload(Case.creator),
            joinedload(Case.assignee)
        ).order_by(desc(Case.created_at)).offset(offset).limit(page_size).all()

        items = []
        for c in cases:
            items.append({
                "id": c.id,
                "case_number": c.case_number,
                "work_id": c.work_id,
                "workExternalId": c.work.external_id,
                "workTitle": c.work.title,
                "status": c.status,
                "priority": c.priority,
                "summary": c.summary,
                "createdByName": c.creator.full_name if c.creator else "System",
                "assigned_to_id": c.assigned_to,
                "assigned_to_name": c.assignee.full_name if c.assignee else None,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
                "actions": []
            })

        return {
            "items": items,
            "page": page,
            "pageSize": page_size,
            "total": total
        }

    @staticmethod
    def get_case_detail(db: Session, case_id: str) -> Dict[str, Any]:
        c = db.query(Case).options(
            joinedload(Case.work),
            joinedload(Case.creator),
            joinedload(Case.assignee),
            joinedload(Case.actions).joinedload(CaseAction.actor)
        ).filter(Case.id == case_id).first()

        if not c:
            raise ValueError(f"Case with ID {case_id} not found.")

        action_items = []
        for act in sorted(c.actions, key=lambda a: a.created_at, reverse=True):
            action_items.append({
                "id": act.id,
                "case_id": act.case_id,
                "actor_id": act.actor_id,
                "actorName": act.actor.full_name if act.actor else "System",
                "action_type": act.action_type,
                "previous_status": act.from_status,
                "new_status": act.to_status,
                "notes": act.note or "",
                "created_at": act.created_at
            })

        return {
            "id": c.id,
            "case_number": c.case_number,
            "work_id": c.work_id,
            "workExternalId": c.work.external_id,
            "workTitle": c.work.title,
            "status": c.status,
            "priority": c.priority,
            "summary": c.summary,
            "createdByName": c.creator.full_name if c.creator else "System",
            "assigned_to_id": c.assigned_to,
            "assigned_to_name": c.assignee.full_name if c.assignee else None,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
            "actions": action_items
        }

    @staticmethod
    def add_case_action(
        db: Session,
        actor_id: str,
        case_id: str,
        action_type: str,
        notes: str,
        new_status: Optional[str] = None,
        assigned_to_id: Optional[str] = None
    ) -> Dict[str, Any]:
        c = db.query(Case).filter(Case.id == case_id).first()
        if not c:
            raise ValueError(f"Case with ID {case_id} not found.")

        prev_status = c.status
        valid_transitions = {
            "NEW": {"DETECTED", "TRIAGED", "ASSIGNED", "UNDER_REVIEW", "CLARIFICATION_REQUESTED", "RECOMMENDED_ACTION", "ESCALATED", "CLOSED", "RESOLVED"},
            "DETECTED": {"DETECTED", "TRIAGED", "ASSIGNED", "UNDER_REVIEW", "CLARIFICATION_REQUESTED", "RECOMMENDED_ACTION", "ESCALATED", "CLOSED", "RESOLVED"},
            "TRIAGED": {"TRIAGED", "ASSIGNED", "UNDER_REVIEW", "CLARIFICATION_REQUESTED", "RECOMMENDED_ACTION", "ESCALATED", "CLOSED", "RESOLVED"},
            "ASSIGNED": {"ASSIGNED", "UNDER_REVIEW", "CLARIFICATION_REQUESTED", "RECOMMENDED_ACTION", "ESCALATED", "CLOSED", "RESOLVED"},
            "UNDER_REVIEW": {"UNDER_REVIEW", "CLARIFICATION_REQUESTED", "RECOMMENDED_ACTION", "ESCALATED", "CLOSED", "RESOLVED"},
            "CLARIFICATION_REQUESTED": {"CLARIFICATION_REQUESTED", "UNDER_REVIEW", "RECOMMENDED_ACTION", "ESCALATED", "CLOSED", "RESOLVED"},
            "RECOMMENDED_ACTION": {"RECOMMENDED_ACTION", "UNDER_REVIEW", "ESCALATED", "CLOSED", "RESOLVED"},
            "ESCALATED": {"ESCALATED", "UNDER_REVIEW", "RECOMMENDED_ACTION", "CLOSED", "RESOLVED"},
            "CLOSED": set(),
            "RESOLVED": {"RESOLVED", "CLOSED", "ESCALATED"}
        }

        if new_status and new_status != prev_status:
            if prev_status == "CLOSED":
                raise ValueError(f"Invalid state transition: Case {c.case_number} is CLOSED and cannot be transitioned to '{new_status}'.")
            allowed = valid_transitions.get(prev_status, set())
            if new_status not in allowed:
                raise ValueError(f"Invalid state transition: Cannot transition case from '{prev_status}' to '{new_status}'.")
            c.status = new_status

        if assigned_to_id:
            c.assigned_to = assigned_to_id

        c.updated_at = datetime.now(timezone.utc)


        action = CaseAction(
            id=str(uuid.uuid4()),
            case_id=c.id,
            actor_id=actor_id,
            action_type=action_type,
            from_status=prev_status,
            to_status=new_status or prev_status,
            note=notes
        )
        db.add(action)
        db.commit()

        AuditService.log_action(
            db,
            action=action_type,
            entity_type="Case",
            user_id=actor_id,
            entity_id=c.id,
            details_json={
                "case_number": c.case_number,
                "previous_status": prev_status,
                "new_status": new_status or prev_status,
                "notes": notes
            }
        )

        return CaseService.get_case_detail(db, c.id)
