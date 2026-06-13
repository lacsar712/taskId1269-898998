from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.production import (
    AbnormalAlarm,
    ProcessOptimization,
    ProcessParameter,
    ProductionLog,
    ProductionPlan,
)
from app.schemas.common import PaginatedResponse


def query_process_parameters(
    db: Session, process_section: Optional[str] = None
) -> List[ProcessParameter]:
    query = db.query(ProcessParameter)
    if process_section:
        query = query.filter(ProcessParameter.process_section == process_section)
    return query.order_by(ProcessParameter.process_section).all()


def get_process_parameter(db: Session, param_id: int) -> Optional[ProcessParameter]:
    return db.query(ProcessParameter).filter(ProcessParameter.id == param_id).first()


def query_production_plans(
    db: Session, page: int, page_size: int, status: Optional[str] = None
) -> PaginatedResponse:
    query = db.query(ProductionPlan)
    if status:
        query = query.filter(ProductionPlan.status == status)

    total = query.count()
    items = (
        query.order_by(ProductionPlan.plan_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


def create_production_plan(
    db: Session,
    plan_date: datetime,
    target_volume: Optional[float],
    operation_mode: Optional[str],
    description: Optional[str],
    user_id: int,
) -> ProductionPlan:
    plan_no = f"PP{datetime.now().strftime('%Y%m%d%H%M%S')}"
    plan = ProductionPlan(
        plan_no=plan_no,
        plan_date=plan_date,
        target_volume=target_volume,
        operation_mode=operation_mode,
        description=description,
        created_by=user_id,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def query_production_logs(
    db: Session,
    page: int,
    page_size: int,
    log_type: Optional[str] = None,
    shift: Optional[str] = None,
) -> PaginatedResponse:
    query = db.query(ProductionLog)
    if log_type:
        query = query.filter(ProductionLog.log_type == log_type)
    if shift:
        query = query.filter(ProductionLog.shift == shift)

    total = query.count()
    items = (
        query.order_by(ProductionLog.log_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


def create_production_log(
    db: Session,
    log_date: datetime,
    shift: Optional[str],
    log_type: str,
    content: str,
    user_id: int,
    user_name: str,
) -> ProductionLog:
    log = ProductionLog(
        log_date=log_date,
        shift=shift,
        log_type=log_type,
        content=content,
        operator_id=user_id,
        operator_name=user_name,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def _normalize_alarm(alarm: AbnormalAlarm) -> dict:
    return {
        "id": alarm.id,
        "alarm_no": alarm.alarm_no,
        "alarm_type": alarm.alarm_type,
        "alarm_level": alarm.alarm_level if alarm.alarm_level else "normal",
        "title": alarm.title,
        "description": alarm.description,
        "source": alarm.source,
        "current_value": alarm.current_value,
        "threshold_value": alarm.threshold_value,
        "status": alarm.status if alarm.status else "pending",
        "handler_name": alarm.handler_name,
        "handle_time": alarm.handle_time,
        "alarm_time": alarm.alarm_time,
    }


def query_abnormal_alarms(
    db: Session,
    page: int,
    page_size: int,
    alarm_level: Optional[str] = None,
    status: Optional[str] = None,
) -> PaginatedResponse:
    query = db.query(AbnormalAlarm)
    if alarm_level:
        query = query.filter(AbnormalAlarm.alarm_level == alarm_level)
    if status:
        query = query.filter(AbnormalAlarm.status == status)

    total = query.count()
    items = (
        query.order_by(AbnormalAlarm.alarm_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedResponse(
        items=[_normalize_alarm(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


def resolve_alarm(
    db: Session,
    alarm_id: int,
    handle_result: str,
    user_id: int,
    user_name: str,
) -> None:
    alarm = db.query(AbnormalAlarm).filter(AbnormalAlarm.id == alarm_id).first()
    if not alarm:
        raise ValueError("告警不存在")

    alarm.status = "resolved"
    alarm.handler_id = user_id
    alarm.handler_name = user_name
    alarm.handle_time = datetime.now()
    alarm.handle_result = handle_result
    db.commit()


def query_process_optimizations(
    db: Session,
    optimization_type: Optional[str] = None,
    status: Optional[str] = None,
) -> List[ProcessOptimization]:
    query = db.query(ProcessOptimization)
    if optimization_type:
        query = query.filter(ProcessOptimization.optimization_type == optimization_type)
    if status:
        query = query.filter(ProcessOptimization.status == status)
    return query.order_by(ProcessOptimization.priority.desc()).all()
