from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
import uuid

from app.models.audit import AuditLog
from app.models.user import User

class AuditService:
    @staticmethod
    def log_action(
        db: Session,
        action: str,
        entity_type: str,
        user_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        details_json: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        log_entry = AuditLog(
            id=str(uuid.uuid4()),
            actor_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            after_json=details_json or {},
            request_id=ip_address
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry

    @staticmethod
    def get_logs(
        db: Session,
        page: int = 1,
        page_size: int = 25,
        action_filter: Optional[str] = None,
        entity_type_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        query = db.query(AuditLog)

        if action_filter:
            query = query.filter(AuditLog.action == action_filter)
        if entity_type_filter:
            query = query.filter(AuditLog.entity_type == entity_type_filter)

        total = query.count()
        offset = (page - 1) * page_size
        logs = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(page_size).all()

        formatted_items = []
        for l in logs:
            user_name = "System Process"
            if l.actor_id:
                u = db.query(User).filter(User.id == l.actor_id).first()
                if u:
                    user_name = u.full_name or u.username

            formatted_items.append({
                "id": l.id,
                "user_id": l.actor_id,
                "user_name": user_name,
                "action": l.action,
                "entity_type": l.entity_type,
                "entity_id": l.entity_id,
                "details_json": l.after_json or {},
                "ip_address": l.request_id,
                "created_at": l.created_at
            })

        return {
            "items": formatted_items,
            "page": page,
            "pageSize": page_size,
            "total": total
        }
