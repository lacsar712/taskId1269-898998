from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from datetime import datetime, date, timedelta
from pydantic import BaseModel
import uuid
import secrets
from app.database import get_db
from app.models.user import User
from app.models.safety import (
    InspectionPlan, InspectionRecord, RiskPoint, EmergencyPlan, SafetyTraining, WorkPermit,
    VideoCameraPoint, VideoInspectionRecord, EmergencyDrill, DrillCheckIn
)
from sqlalchemy import desc, and_, func
from app.schemas.common import PaginatedResponse, MessageResponse
from app.services.auth import get_current_active_user

router = APIRouter(prefix="/api/safety", tags=["安全管理"])


# Schemas
class InspectionPlanResponse(BaseModel):
    id: int
    plan_no: str
    plan_name: str
    inspection_type: Optional[str]
    frequency: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    status: str
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class InspectionPlanCreate(BaseModel):
    plan_name: str
    inspection_type: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class InspectionRecordResponse(BaseModel):
    id: int
    record_no: str
    inspector_name: Optional[str]
    inspection_date: datetime
    findings: Optional[str]
    status: str
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class InspectionRecordCreate(BaseModel):
    plan_id: Optional[int] = None
    inspection_date: datetime
    check_points: Optional[str] = None
    findings: Optional[str] = None
    status: str = "normal"


class RiskPointResponse(BaseModel):
    id: int
    name: str
    code: str
    location: Optional[str]
    risk_type: Optional[str]
    risk_level: Optional[str]
    description: Optional[str]
    control_measures: Optional[str]
    responsible_person: Optional[str]
    status: str
    
    class Config:
        from_attributes = True


class RiskPointCreate(BaseModel):
    name: str
    location: Optional[str] = None
    risk_type: Optional[str] = None
    risk_level: Optional[str] = None
    description: Optional[str] = None
    control_measures: Optional[str] = None
    responsible_person: Optional[str] = None


class EmergencyPlanResponse(BaseModel):
    id: int
    plan_no: str
    plan_name: str
    emergency_type: Optional[str]
    plan_level: Optional[str]
    drill_date: Optional[date]
    status: str
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class SafetyTrainingResponse(BaseModel):
    id: int
    training_no: str
    title: str
    training_type: Optional[str]
    trainer: Optional[str]
    training_date: Optional[datetime]
    duration: Optional[int]
    status: str
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class WorkPermitResponse(BaseModel):
    id: int
    permit_no: str
    work_type: str
    work_location: Optional[str]
    work_content: Optional[str]
    applicant_name: Optional[str]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    status: str
    approver_name: Optional[str]
    
    class Config:
        from_attributes = True


class WorkPermitCreate(BaseModel):
    work_type: str
    work_location: Optional[str] = None
    work_content: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    safety_measures: Optional[str] = None


# 安全巡检
@router.get("/inspections/plans", response_model=PaginatedResponse[InspectionPlanResponse])
def get_inspection_plans(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(InspectionPlan)
    if status:
        query = query.filter(InspectionPlan.status == status)
    
    total = query.count()
    items = query.order_by(InspectionPlan.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.post("/inspections/plans", response_model=InspectionPlanResponse)
def create_inspection_plan(
    data: InspectionPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    plan_no = f"IP{datetime.now().strftime('%Y%m%d%H%M%S')}"
    plan = InspectionPlan(
        plan_no=plan_no,
        plan_name=data.plan_name,
        inspection_type=data.inspection_type,
        frequency=data.frequency,
        route=data.route,
        start_date=data.start_date,
        end_date=data.end_date
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.get("/inspections/records", response_model=PaginatedResponse[InspectionRecordResponse])
def get_inspection_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(InspectionRecord)
    if status:
        query = query.filter(InspectionRecord.status == status)
    
    total = query.count()
    items = query.order_by(InspectionRecord.inspection_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.post("/inspections/records", response_model=InspectionRecordResponse)
def create_inspection_record(
    data: InspectionRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    record_no = f"IR{datetime.now().strftime('%Y%m%d%H%M%S')}"
    record = InspectionRecord(
        plan_id=data.plan_id,
        record_no=record_no,
        inspector_id=current_user.id,
        inspector_name=current_user.real_name or current_user.username,
        inspection_date=data.inspection_date,
        check_points=data.check_points,
        findings=data.findings,
        status=data.status
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# 风险管控
@router.get("/risks", response_model=PaginatedResponse[RiskPointResponse])
def get_risk_points(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(RiskPoint)
    if risk_level:
        query = query.filter(RiskPoint.risk_level == risk_level)
    
    total = query.count()
    items = query.order_by(RiskPoint.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.post("/risks", response_model=RiskPointResponse)
def create_risk_point(
    data: RiskPointCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    code = f"RP{datetime.now().strftime('%Y%m%d%H%M%S')}"
    risk = RiskPoint(
        name=data.name,
        code=code,
        location=data.location,
        risk_type=data.risk_type,
        risk_level=data.risk_level,
        description=data.description,
        control_measures=data.control_measures,
        responsible_person=data.responsible_person
    )
    db.add(risk)
    db.commit()
    db.refresh(risk)
    return risk


# 应急管理
@router.get("/emergency/plans", response_model=List[EmergencyPlanResponse])
def get_emergency_plans(
    emergency_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(EmergencyPlan)
    if emergency_type:
        query = query.filter(EmergencyPlan.emergency_type == emergency_type)
    return query.all()


# 安全培训
@router.get("/trainings", response_model=PaginatedResponse[SafetyTrainingResponse])
def get_safety_trainings(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(SafetyTraining)
    if status:
        query = query.filter(SafetyTraining.status == status)
    
    total = query.count()
    items = query.order_by(SafetyTraining.training_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


# 作业许可
@router.get("/permits", response_model=PaginatedResponse[WorkPermitResponse])
def get_work_permits(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(WorkPermit)
    if status:
        query = query.filter(WorkPermit.status == status)
    
    total = query.count()
    items = query.order_by(WorkPermit.apply_time.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.post("/permits", response_model=WorkPermitResponse)
def create_work_permit(
    data: WorkPermitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    permit_no = f"WP{datetime.now().strftime('%Y%m%d%H%M%S')}"
    permit = WorkPermit(
        permit_no=permit_no,
        work_type=data.work_type,
        work_location=data.work_location,
        work_content=data.work_content,
        applicant_id=current_user.id,
        applicant_name=current_user.real_name or current_user.username,
        start_time=data.start_time,
        end_time=data.end_time,
        safety_measures=data.safety_measures
    )
    db.add(permit)
    db.commit()
    db.refresh(permit)
    return permit


@router.put("/permits/{permit_id}/approve", response_model=MessageResponse)
def approve_work_permit(
    permit_id: int,
    approved: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    permit = db.query(WorkPermit).filter(WorkPermit.id == permit_id).first()
    if not permit:
        raise HTTPException(status_code=404, detail="许可不存在")
    
    permit.status = "approved" if approved else "rejected"
    permit.approver_id = current_user.id
    permit.approver_name = current_user.real_name or current_user.username
    permit.approve_time = datetime.now()
    db.commit()
    
    return MessageResponse(message="审批完成")


# ==================== 视频巡检点位 ====================

class VideoCameraPointResponse(BaseModel):
    id: int
    point_no: str
    point_name: str
    install_location: Optional[str]
    coverage_area: Optional[str]
    device_model: Optional[str]
    online_status: str
    ip_address: Optional[str]
    responsible_person: Optional[str]
    install_date: Optional[date]
    status: str
    remark: Optional[str]
    last_inspection_time: Optional[datetime] = None
    last_inspector: Optional[str] = None
    last_inspection_result: Optional[str] = None
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class VideoCameraPointCreate(BaseModel):
    point_name: str
    install_location: Optional[str] = None
    coverage_area: Optional[str] = None
    device_model: Optional[str] = None
    online_status: str = "online"
    ip_address: Optional[str] = None
    responsible_person: Optional[str] = None
    install_date: Optional[date] = None
    remark: Optional[str] = None


class VideoCameraPointUpdate(BaseModel):
    point_name: Optional[str] = None
    install_location: Optional[str] = None
    coverage_area: Optional[str] = None
    device_model: Optional[str] = None
    online_status: Optional[str] = None
    ip_address: Optional[str] = None
    responsible_person: Optional[str] = None
    install_date: Optional[date] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class VideoInspectionRecordResponse(BaseModel):
    id: int
    record_no: str
    camera_point_id: int
    camera_point_name: Optional[str]
    inspector_name: Optional[str]
    inspection_time: datetime
    result: str
    severity: Optional[str]
    remark: Optional[str]
    abnormal_description: Optional[str]
    handle_status: str
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class VideoInspectionRecordCreate(BaseModel):
    camera_point_id: int
    inspection_time: datetime
    result: str = "normal"
    severity: Optional[str] = None
    remark: Optional[str] = None
    abnormal_description: Optional[str] = None


class VideoInspectionHandleUpdate(BaseModel):
    handle_status: str


@router.get("/video-camera-points", response_model=PaginatedResponse[VideoCameraPointResponse])
def get_video_camera_points(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    online_status: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(VideoCameraPoint)
    if keyword:
        query = query.filter(
            (VideoCameraPoint.point_name.like(f"%{keyword}%")) |
            (VideoCameraPoint.install_location.like(f"%{keyword}%")) |
            (VideoCameraPoint.point_no.like(f"%{keyword}%"))
        )
    if online_status:
        query = query.filter(VideoCameraPoint.online_status == online_status)
    if status:
        query = query.filter(VideoCameraPoint.status == status)

    total = query.count()
    items = query.order_by(VideoCameraPoint.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    result_items = []
    for point in items:
        last_record = db.query(VideoInspectionRecord).filter(
            VideoInspectionRecord.camera_point_id == point.id
        ).order_by(desc(VideoInspectionRecord.inspection_time)).first()

        point_dict = {
            "id": point.id,
            "point_no": point.point_no,
            "point_name": point.point_name,
            "install_location": point.install_location,
            "coverage_area": point.coverage_area,
            "device_model": point.device_model,
            "online_status": point.online_status,
            "ip_address": point.ip_address,
            "responsible_person": point.responsible_person,
            "install_date": point.install_date,
            "status": point.status,
            "remark": point.remark,
            "created_at": point.created_at,
            "last_inspection_time": last_record.inspection_time if last_record else None,
            "last_inspector": last_record.inspector_name if last_record else None,
            "last_inspection_result": last_record.result if last_record else None
        }
        result_items.append(point_dict)

    return PaginatedResponse(
        items=result_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/video-camera-points/all", response_model=List[VideoCameraPointResponse])
def get_all_video_camera_points(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    items = db.query(VideoCameraPoint).filter(VideoCameraPoint.status == "active").all()
    return items


@router.post("/video-camera-points", response_model=VideoCameraPointResponse)
def create_video_camera_point(
    data: VideoCameraPointCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    point_no = f"VCP{datetime.now().strftime('%Y%m%d%H%M%S')}"
    point = VideoCameraPoint(
        point_no=point_no,
        point_name=data.point_name,
        install_location=data.install_location,
        coverage_area=data.coverage_area,
        device_model=data.device_model,
        online_status=data.online_status,
        ip_address=data.ip_address,
        responsible_person=data.responsible_person,
        install_date=data.install_date,
        remark=data.remark
    )
    db.add(point)
    db.commit()
    db.refresh(point)
    return point


@router.put("/video-camera-points/{point_id}", response_model=VideoCameraPointResponse)
def update_video_camera_point(
    point_id: int,
    data: VideoCameraPointUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    point = db.query(VideoCameraPoint).filter(VideoCameraPoint.id == point_id).first()
    if not point:
        raise HTTPException(status_code=404, detail="点位不存在")

    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(point, key, value)

    db.commit()
    db.refresh(point)
    return point


@router.delete("/video-camera-points/{point_id}", response_model=MessageResponse)
def delete_video_camera_point(
    point_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    point = db.query(VideoCameraPoint).filter(VideoCameraPoint.id == point_id).first()
    if not point:
        raise HTTPException(status_code=404, detail="点位不存在")

    point.status = "inactive"
    db.commit()
    return MessageResponse(message="删除成功")


@router.get("/video-inspection/records", response_model=PaginatedResponse[VideoInspectionRecordResponse])
def get_video_inspection_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    camera_point_id: Optional[int] = None,
    result: Optional[str] = None,
    severity: Optional[str] = None,
    handle_status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(VideoInspectionRecord)
    if camera_point_id:
        query = query.filter(VideoInspectionRecord.camera_point_id == camera_point_id)
    if result:
        query = query.filter(VideoInspectionRecord.result == result)
    if severity:
        query = query.filter(VideoInspectionRecord.severity == severity)
    if handle_status:
        query = query.filter(VideoInspectionRecord.handle_status == handle_status)

    total = query.count()

    severity_order = {"critical": 0, "severe": 1, "moderate": 2, "mild": 3, None: 4}
    items = query.order_by(
        desc(VideoInspectionRecord.created_at)
    ).offset((page - 1) * page_size).limit(page_size).all()

    sorted_items = sorted(items, key=lambda x: (
        severity_order.get(x.severity, 4),
        -x.inspection_time.timestamp() if x.inspection_time else 0
    ))

    return PaginatedResponse(
        items=sorted_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/video-inspection/abnormal-list", response_model=PaginatedResponse[VideoInspectionRecordResponse])
def get_video_inspection_abnormal_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    severity: Optional[str] = None,
    handle_status: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(VideoInspectionRecord).filter(VideoInspectionRecord.result == "abnormal")
    if severity:
        query = query.filter(VideoInspectionRecord.severity == severity)
    if handle_status:
        query = query.filter(VideoInspectionRecord.handle_status == handle_status)
    if keyword:
        query = query.filter(
            (VideoInspectionRecord.camera_point_name.like(f"%{keyword}%")) |
            (VideoInspectionRecord.abnormal_description.like(f"%{keyword}%"))
        )

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    severity_order = {"critical": 0, "severe": 1, "moderate": 2, "mild": 3}
    sorted_items = sorted(items, key=lambda x: (
        severity_order.get(x.severity, 99),
        -x.inspection_time.timestamp() if x.inspection_time else 0
    ))

    return PaginatedResponse(
        items=sorted_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.post("/video-inspection/records", response_model=VideoInspectionRecordResponse)
def create_video_inspection_record(
    data: VideoInspectionRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    record_no = f"VIR{datetime.now().strftime('%Y%m%d%H%M%S')}"

    camera_point = db.query(VideoCameraPoint).filter(VideoCameraPoint.id == data.camera_point_id).first()

    handle_status = "pending" if data.result == "abnormal" else "closed"

    record = VideoInspectionRecord(
        record_no=record_no,
        camera_point_id=data.camera_point_id,
        camera_point_name=camera_point.point_name if camera_point else None,
        inspector_id=current_user.id,
        inspector_name=current_user.real_name or current_user.username,
        inspection_time=data.inspection_time,
        result=data.result,
        severity=data.severity,
        remark=data.remark,
        abnormal_description=data.abnormal_description,
        handle_status=handle_status
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/video-inspection/records/{record_id}/handle-status", response_model=MessageResponse)
def update_video_inspection_handle_status(
    record_id: int,
    data: VideoInspectionHandleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    record = db.query(VideoInspectionRecord).filter(VideoInspectionRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="巡检记录不存在")

    record.handle_status = data.handle_status
    db.commit()
    return MessageResponse(message="状态更新成功")


@router.get("/video-inspection/statistics")
def get_video_inspection_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    total_points = db.query(VideoCameraPoint).filter(VideoCameraPoint.status == "active").count()
    online_points = db.query(VideoCameraPoint).filter(
        and_(VideoCameraPoint.status == "active", VideoCameraPoint.online_status == "online")
    ).count()

    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_inspections = db.query(VideoInspectionRecord).filter(
        VideoInspectionRecord.inspection_time >= today_start
    ).count()

    pending_abnormal = db.query(VideoInspectionRecord).filter(
        and_(
            VideoInspectionRecord.result == "abnormal",
            VideoInspectionRecord.handle_status == "pending"
        )
    ).count()

    total_abnormal = db.query(VideoInspectionRecord).filter(
        VideoInspectionRecord.result == "abnormal"
    ).count()

    severity_counts = {
        "critical": db.query(VideoInspectionRecord).filter(
            and_(VideoInspectionRecord.result == "abnormal", VideoInspectionRecord.severity == "critical")
        ).count(),
        "severe": db.query(VideoInspectionRecord).filter(
            and_(VideoInspectionRecord.result == "abnormal", VideoInspectionRecord.severity == "severe")
        ).count(),
        "moderate": db.query(VideoInspectionRecord).filter(
            and_(VideoInspectionRecord.result == "abnormal", VideoInspectionRecord.severity == "moderate")
        ).count(),
        "mild": db.query(VideoInspectionRecord).filter(
            and_(VideoInspectionRecord.result == "abnormal", VideoInspectionRecord.severity == "mild")
        ).count()
    }

    return {
        "total_points": total_points,
        "online_points": online_points,
        "offline_points": total_points - online_points,
        "today_inspections": today_inspections,
        "pending_abnormal": pending_abnormal,
        "total_abnormal": total_abnormal,
        "severity_counts": severity_counts
    }


def init_default_video_camera_points(db: Session):
    count = db.query(VideoCameraPoint).count()
    if count > 0:
        return

    sample_points = [
        {
            "point_name": "粗格栅间监控点",
            "install_location": "厂区北区-粗格栅间",
            "coverage_area": "粗格栅设备及周围通道",
            "device_model": "海康威视DS-2CD3T46WD-I3",
            "online_status": "online",
            "ip_address": "192.168.1.101",
            "responsible_person": "张工",
            "remark": "24小时监控粗格栅运行状态"
        },
        {
            "point_name": "进水泵房监控点",
            "install_location": "厂区北区-进水泵房",
            "coverage_area": "进水泵组及控制机柜",
            "device_model": "海康威视DS-2CD3T46WD-I3",
            "online_status": "online",
            "ip_address": "192.168.1.102",
            "responsible_person": "李工",
            "remark": "监控进水泵运行情况"
        },
        {
            "point_name": "生化池A区监控点",
            "install_location": "厂区中区-生化池A区",
            "coverage_area": "生化池曝气区及搅拌设备",
            "device_model": "大华DH-IPC-HFW4433M-I1",
            "online_status": "online",
            "ip_address": "192.168.1.103",
            "responsible_person": "王工",
            "remark": "监控生化池曝气状态"
        },
        {
            "point_name": "生化池B区监控点",
            "install_location": "厂区中区-生化池B区",
            "coverage_area": "生化池沉淀区及污泥回流",
            "device_model": "大华DH-IPC-HFW4433M-I1",
            "online_status": "offline",
            "ip_address": "192.168.1.104",
            "responsible_person": "王工",
            "remark": "网络故障待维修"
        },
        {
            "point_name": "二沉池监控点",
            "install_location": "厂区南区-二沉池",
            "coverage_area": "二沉池出水堰及刮泥机",
            "device_model": "海康威视DS-2CD3T46WD-I5",
            "online_status": "online",
            "ip_address": "192.168.1.105",
            "responsible_person": "赵工",
            "remark": "监控二沉池出水情况"
        },
        {
            "point_name": "污泥脱水间监控点",
            "install_location": "厂区东区-污泥脱水间",
            "coverage_area": "脱水机及污泥输送带",
            "device_model": "海康威视DS-2CD2T46WD-I3",
            "online_status": "online",
            "ip_address": "192.168.1.106",
            "responsible_person": "孙工",
            "remark": "监控污泥脱水作业"
        },
        {
            "point_name": "消毒池监控点",
            "install_location": "厂区南区-消毒池",
            "coverage_area": "紫外消毒设备及出水渠道",
            "device_model": "大华DH-IPC-HFW2433M-I1",
            "online_status": "maintenance",
            "ip_address": "192.168.1.107",
            "responsible_person": "赵工",
            "remark": "定期维护中"
        },
        {
            "point_name": "变电所监控点",
            "install_location": "厂区西区-变电所",
            "coverage_area": "高低压配电柜及变压器",
            "device_model": "海康威视DS-2CD3T66WD-I3",
            "online_status": "online",
            "ip_address": "192.168.1.108",
            "responsible_person": "周工",
            "remark": "重点区域安全监控"
        },
        {
            "point_name": "加药间监控点",
            "install_location": "厂区中区-加药间",
            "coverage_area": "PAC/PAM投加系统及储罐",
            "device_model": "大华DH-IPC-HFW4433M-I2",
            "online_status": "online",
            "ip_address": "192.168.1.109",
            "responsible_person": "李工",
            "remark": "监控药剂投加情况"
        },
        {
            "point_name": "厂区大门监控点",
            "install_location": "厂区主入口",
            "coverage_area": "大门通道及车辆进出",
            "device_model": "海康威视DS-2CD3T46WD-I3",
            "online_status": "online",
            "ip_address": "192.168.1.110",
            "responsible_person": "保安队",
            "remark": "人员车辆出入监控"
        }
    ]

    for i, p in enumerate(sample_points):
        point_no = f"VCP{datetime.now().strftime('%Y%m%d')}{str(i+1).zfill(4)}"
        point = VideoCameraPoint(
            point_no=point_no,
            point_name=p["point_name"],
            install_location=p["install_location"],
            coverage_area=p["coverage_area"],
            device_model=p["device_model"],
            online_status=p["online_status"],
            ip_address=p["ip_address"],
            responsible_person=p["responsible_person"],
            remark=p["remark"]
        )
        db.add(point)
    db.commit()

    sample_records = [
        {
            "point_name": "粗格栅间监控点",
            "inspection_time": datetime(2026, 6, 12, 9, 30, 0),
            "result": "normal",
            "remark": "画面清晰，设备运行正常"
        },
        {
            "point_name": "生化池A区监控点",
            "inspection_time": datetime(2026, 6, 12, 10, 15, 0),
            "result": "abnormal",
            "severity": "moderate",
            "abnormal_description": "发现曝气不均匀，局部区域无气泡产生，疑似曝气头堵塞",
            "remark": "已通知维修班，待处理"
        },
        {
            "point_name": "二沉池监控点",
            "inspection_time": datetime(2026, 6, 12, 11, 0, 0),
            "result": "normal",
            "remark": "出水清澈，刮泥机运转正常"
        },
        {
            "point_name": "进水泵房监控点",
            "inspection_time": datetime(2026, 6, 12, 14, 20, 0),
            "result": "abnormal",
            "severity": "severe",
            "abnormal_description": "画面出现大量雪花噪点，疑似摄像头进水故障",
            "remark": "严重影响监控效果，需紧急处理"
        },
        {
            "point_name": "变电所监控点",
            "inspection_time": datetime(2026, 6, 12, 15, 45, 0),
            "result": "abnormal",
            "severity": "critical",
            "abnormal_description": "监控发现1号变压器附近有烟雾产生，疑似电气故障",
            "remark": "已立即上报，启动应急预案"
        },
        {
            "point_name": "污泥脱水间监控点",
            "inspection_time": datetime(2026, 6, 12, 16, 30, 0),
            "result": "abnormal",
            "severity": "mild",
            "abnormal_description": "摄像头画面轻微偏移，部分区域遮挡",
            "remark": "下次维护时调整角度"
        },
        {
            "point_name": "加药间监控点",
            "inspection_time": datetime(2026, 6, 13, 8, 40, 0),
            "result": "normal",
            "remark": "药剂投加系统运行正常"
        },
        {
            "point_name": "厂区大门监控点",
            "inspection_time": datetime(2026, 6, 13, 9, 10, 0),
            "result": "normal",
            "remark": "人员车辆出入正常，无异常情况"
        }
    ]

    camera_points = db.query(VideoCameraPoint).all()
    point_map = {p.point_name: p for p in camera_points}

    for i, r in enumerate(sample_records):
        cp = point_map.get(r["point_name"])
        if cp:
            record_no = f"VIR{datetime.now().strftime('%Y%m%d')}{str(i+1).zfill(4)}"
            handle_status = "pending" if r["result"] == "abnormal" else "closed"
            record = VideoInspectionRecord(
                record_no=record_no,
                camera_point_id=cp.id,
                camera_point_name=cp.point_name,
                inspector_id=1,
                inspector_name="系统管理员",
                inspection_time=r["inspection_time"],
                result=r["result"],
                severity=r.get("severity"),
                remark=r.get("remark"),
                abnormal_description=r.get("abnormal_description"),
                handle_status=handle_status
            )
            db.add(record)
    db.commit()


# ==================== 应急演练签到 ====================

class ExpectedTeam(BaseModel):
    team_id: Optional[int] = None
    team_name: str
    expected_count: int = 0


class DrillResponse(BaseModel):
    id: int
    drill_no: str
    drill_name: str
    drill_type: Optional[str]
    location: Optional[str]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    expected_teams: Optional[Any]
    check_in_code: Optional[str]
    check_in_token: Optional[str]
    organizer_id: Optional[int]
    organizer_name: Optional[str]
    description: Optional[str]
    status: str
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class DrillDetailResponse(DrillResponse):
    check_in_count: int = 0
    expected_count: int = 0
    attendance_rate: float = 0.0
    check_ins: List[dict] = []


class DrillCreate(BaseModel):
    drill_name: str
    drill_type: Optional[str] = None
    location: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    expected_teams: List[ExpectedTeam] = []
    description: Optional[str] = None


class DrillUpdate(BaseModel):
    drill_name: Optional[str] = None
    drill_type: Optional[str] = None
    location: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    expected_teams: Optional[List[ExpectedTeam]] = None
    description: Optional[str] = None
    status: Optional[str] = None


class CheckInCreate(BaseModel):
    participant_name: str
    team_name: Optional[str] = None
    team_id: Optional[int] = None
    check_in_code: Optional[str] = None
    drill_token: Optional[str] = None


class CheckInResponse(BaseModel):
    id: int
    drill_id: int
    participant_name: str
    team_id: Optional[int]
    team_name: Optional[str]
    check_in_time: Optional[datetime]
    check_in_type: Optional[str]

    class Config:
        from_attributes = True


def _generate_check_in_code() -> str:
    while True:
        code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        return code


def _generate_check_in_token() -> str:
    return secrets.token_urlsafe(32)


@router.get("/drills", response_model=PaginatedResponse[DrillResponse])
def get_drills(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(EmergencyDrill)
    if status:
        query = query.filter(EmergencyDrill.status == status)
    if keyword:
        query = query.filter(
            (EmergencyDrill.drill_name.like(f"%{keyword}%")) |
            (EmergencyDrill.drill_no.like(f"%{keyword}%"))
        )

    total = query.count()
    items = query.order_by(desc(EmergencyDrill.created_at)).offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/drills/{drill_id}", response_model=DrillDetailResponse)
def get_drill_detail(
    drill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    drill = db.query(EmergencyDrill).filter(EmergencyDrill.id == drill_id).first()
    if not drill:
        raise HTTPException(status_code=404, detail="演练不存在")

    check_ins = db.query(DrillCheckIn).filter(DrillCheckIn.drill_id == drill_id).order_by(desc(DrillCheckIn.check_in_time)).all()
    check_in_count = len(check_ins)

    expected_count = 0
    if drill.expected_teams and isinstance(drill.expected_teams, list):
        for t in drill.expected_teams:
            expected_count += t.get("expected_count", 0) or 0

    attendance_rate = round((check_in_count / expected_count * 100), 2) if expected_count > 0 else 0.0

    check_in_list = [
        {
            "id": c.id,
            "participant_name": c.participant_name,
            "team_id": c.team_id,
            "team_name": c.team_name,
            "check_in_time": c.check_in_time,
            "check_in_type": c.check_in_type
        }
        for c in check_ins
    ]

    return DrillDetailResponse(
        id=drill.id,
        drill_no=drill.drill_no,
        drill_name=drill.drill_name,
        drill_type=drill.drill_type,
        location=drill.location,
        start_time=drill.start_time,
        end_time=drill.end_time,
        expected_teams=drill.expected_teams,
        check_in_code=drill.check_in_code,
        check_in_token=drill.check_in_token,
        organizer_id=drill.organizer_id,
        organizer_name=drill.organizer_name,
        description=drill.description,
        status=drill.status,
        created_at=drill.created_at,
        check_in_count=check_in_count,
        expected_count=expected_count,
        attendance_rate=attendance_rate,
        check_ins=check_in_list
    )


@router.post("/drills", response_model=DrillResponse)
def create_drill(
    data: DrillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    drill_no = f"DR{datetime.now().strftime('%Y%m%d%H%M%S')}"
    check_in_code = _generate_check_in_code()
    check_in_token = _generate_check_in_token()

    teams_data = [t.model_dump() for t in data.expected_teams] if data.expected_teams else []

    drill = EmergencyDrill(
        drill_no=drill_no,
        drill_name=data.drill_name,
        drill_type=data.drill_type,
        location=data.location,
        start_time=data.start_time,
        end_time=data.end_time,
        expected_teams=teams_data,
        check_in_code=check_in_code,
        check_in_token=check_in_token,
        organizer_id=current_user.id,
        organizer_name=current_user.real_name or current_user.username,
        description=data.description,
        status="draft"
    )
    db.add(drill)
    db.commit()
    db.refresh(drill)
    return drill


@router.put("/drills/{drill_id}", response_model=DrillResponse)
def update_drill(
    drill_id: int,
    data: DrillUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    drill = db.query(EmergencyDrill).filter(EmergencyDrill.id == drill_id).first()
    if not drill:
        raise HTTPException(status_code=404, detail="演练不存在")

    update_data = data.model_dump(exclude_unset=True)
    if "expected_teams" in update_data and update_data["expected_teams"] is not None:
        teams_data = [t.model_dump() if hasattr(t, 'model_dump') else t for t in update_data["expected_teams"]]
        update_data["expected_teams"] = teams_data

    for key, value in update_data.items():
        setattr(drill, key, value)

    db.commit()
    db.refresh(drill)
    return drill


@router.post("/drills/{drill_id}/start", response_model=MessageResponse)
def start_drill(
    drill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    drill = db.query(EmergencyDrill).filter(EmergencyDrill.id == drill_id).first()
    if not drill:
        raise HTTPException(status_code=404, detail="演练不存在")
    drill.status = "ongoing"
    db.commit()
    return MessageResponse(message="演练已开始，签到入口已开启")


@router.post("/drills/{drill_id}/end", response_model=MessageResponse)
def end_drill(
    drill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    drill = db.query(EmergencyDrill).filter(EmergencyDrill.id == drill_id).first()
    if not drill:
        raise HTTPException(status_code=404, detail="演练不存在")
    drill.status = "ended"
    db.commit()
    return MessageResponse(message="演练已结束，签到入口已关闭")


@router.delete("/drills/{drill_id}", response_model=MessageResponse)
def delete_drill(
    drill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    drill = db.query(EmergencyDrill).filter(EmergencyDrill.id == drill_id).first()
    if not drill:
        raise HTTPException(status_code=404, detail="演练不存在")
    db.delete(drill)
    db.query(DrillCheckIn).filter(DrillCheckIn.drill_id == drill_id).delete()
    db.commit()
    return MessageResponse(message="删除成功")


@router.post("/drills/{drill_id}/refresh-code", response_model=DrillResponse)
def refresh_check_in_code(
    drill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    drill = db.query(EmergencyDrill).filter(EmergencyDrill.id == drill_id).first()
    if not drill:
        raise HTTPException(status_code=404, detail="演练不存在")
    drill.check_in_code = _generate_check_in_code()
    drill.check_in_token = _generate_check_in_token()
    db.commit()
    db.refresh(drill)
    return drill


@router.get("/drills/{drill_id}/check-ins", response_model=PaginatedResponse[CheckInResponse])
def get_drill_check_ins(
    drill_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    team_name: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    drill = db.query(EmergencyDrill).filter(EmergencyDrill.id == drill_id).first()
    if not drill:
        raise HTTPException(status_code=404, detail="演练不存在")

    query = db.query(DrillCheckIn).filter(DrillCheckIn.drill_id == drill_id)
    if team_name:
        query = query.filter(DrillCheckIn.team_name == team_name)
    if keyword:
        query = query.filter(DrillCheckIn.participant_name.like(f"%{keyword}%"))

    total = query.count()
    items = query.order_by(desc(DrillCheckIn.check_in_time)).offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/drills/{drill_id}/export")
def export_drill_check_ins(
    drill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    drill = db.query(EmergencyDrill).filter(EmergencyDrill.id == drill_id).first()
    if not drill:
        raise HTTPException(status_code=404, detail="演练不存在")

    check_ins = db.query(DrillCheckIn).filter(DrillCheckIn.drill_id == drill_id).order_by(DrillCheckIn.check_in_time).all()

    expected_count = 0
    team_stats = {}
    if drill.expected_teams and isinstance(drill.expected_teams, list):
        for t in drill.expected_teams:
            tname = t.get("team_name", "")
            team_stats[tname] = {"expected": t.get("expected_count", 0), "actual": 0}
            expected_count += t.get("expected_count", 0) or 0

    rows = []
    for idx, c in enumerate(check_ins, 1):
        if c.team_name in team_stats:
            team_stats[c.team_name]["actual"] += 1
        rows.append({
            "序号": idx,
            "姓名": c.participant_name,
            "班组": c.team_name or "-",
            "签到时间": c.check_in_time.strftime("%Y-%m-%d %H:%M:%S") if c.check_in_time else "",
            "签到方式": "签到码" if c.check_in_type == "code" else "签到链接"
        })

    summary = [
        {"项目": "演练名称", "值": drill.drill_name},
        {"项目": "演练编号", "值": drill.drill_no},
        {"项目": "演练类型", "值": drill.drill_type or "-"},
        {"项目": "演练地点", "值": drill.location or "-"},
        {"项目": "开始时间", "值": drill.start_time.strftime("%Y-%m-%d %H:%M:%S") if drill.start_time else "-"},
        {"项目": "结束时间", "值": drill.end_time.strftime("%Y-%m-%d %H:%M:%S") if drill.end_time else "-"},
        {"项目": "组织人", "值": drill.organizer_name or "-"},
        {"项目": "预期参与人数", "值": expected_count},
        {"项目": "实际签到人数", "值": len(check_ins)},
        {"项目": "到场率", "值": f"{round((len(check_ins) / expected_count * 100), 2) if expected_count > 0 else 0}%"}
    ]

    team_summary_rows = []
    for tname, stats in team_stats.items():
        rate = round((stats["actual"] / stats["expected"] * 100), 2) if stats["expected"] > 0 else 0
        team_summary_rows.append({
            "班组": tname,
            "预期人数": stats["expected"],
            "实际签到": stats["actual"],
            "到场率": f"{rate}%"
        })

    return {
        "drill_info": summary,
        "team_summary": team_summary_rows,
        "check_in_records": rows
    }


@router.get("/drills/public/{token}")
def get_drill_public(
    token: str,
    db: Session = Depends(get_db)
):
    drill = db.query(EmergencyDrill).filter(EmergencyDrill.check_in_token == token).first()
    if not drill:
        raise HTTPException(status_code=404, detail="签到链接无效")
    if drill.status != "ongoing":
        return {
            "id": drill.id,
            "drill_name": drill.drill_name,
            "drill_type": drill.drill_type,
            "location": drill.location,
            "start_time": drill.start_time,
            "end_time": drill.end_time,
            "status": drill.status,
            "can_check_in": False,
            "message": "签到入口已关闭"
        }

    teams = []
    if drill.expected_teams and isinstance(drill.expected_teams, list):
        teams = [{"team_id": t.get("team_id"), "team_name": t.get("team_name")} for t in drill.expected_teams]

    return {
        "id": drill.id,
        "drill_name": drill.drill_name,
        "drill_type": drill.drill_type,
        "location": drill.location,
        "start_time": drill.start_time,
        "end_time": drill.end_time,
        "status": drill.status,
        "can_check_in": True,
        "teams": teams
    }


@router.post("/drills/check-in", response_model=MessageResponse)
async def drill_check_in(
    data: CheckInCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    drill = None
    check_in_type = "code"

    if data.drill_token:
        drill = db.query(EmergencyDrill).filter(EmergencyDrill.check_in_token == data.drill_token).first()
        check_in_type = "link"
    elif data.check_in_code:
        drill = db.query(EmergencyDrill).filter(EmergencyDrill.check_in_code == data.check_in_code).first()
        check_in_type = "code"

    if not drill:
        raise HTTPException(status_code=400, detail="签到码或链接无效")
    if drill.status != "ongoing":
        raise HTTPException(status_code=400, detail="签到入口已关闭")

    existing = db.query(DrillCheckIn).filter(
        DrillCheckIn.drill_id == drill.id,
        DrillCheckIn.participant_name == data.participant_name,
        DrillCheckIn.team_name == (data.team_name or "")
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="您已完成签到，请勿重复签到")

    client_ip = request.client.host if request.client else ""
    user_agent = request.headers.get("user-agent", "")[:500]

    check_in = DrillCheckIn(
        drill_id=drill.id,
        participant_name=data.participant_name,
        team_id=data.team_id,
        team_name=data.team_name,
        check_in_type=check_in_type,
        ip_address=client_ip,
        user_agent=user_agent
    )
    db.add(check_in)
    db.commit()

    return MessageResponse(message=f"{data.participant_name} 签到成功！")


@router.get("/drills/statistics/summary")
def get_drill_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    total_drills = db.query(EmergencyDrill).count()
    ongoing_drills = db.query(EmergencyDrill).filter(EmergencyDrill.status == "ongoing").count()
    ended_drills = db.query(EmergencyDrill).filter(EmergencyDrill.status == "ended").count()
    draft_drills = db.query(EmergencyDrill).filter(EmergencyDrill.status == "draft").count()
    total_check_ins = db.query(DrillCheckIn).count()

    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_check_ins = db.query(DrillCheckIn).filter(DrillCheckIn.created_at >= today_start).count()

    return {
        "total_drills": total_drills,
        "ongoing_drills": ongoing_drills,
        "ended_drills": ended_drills,
        "draft_drills": draft_drills,
        "total_check_ins": total_check_ins,
        "today_check_ins": today_check_ins
    }


def init_default_drills(db: Session):
    count = db.query(EmergencyDrill).count()
    if count > 0:
        return

    sample_drills = [
        {
            "drill_name": "2026年度消防安全应急演练",
            "drill_type": "消防演练",
            "location": "厂区主干道及消防集合点",
            "start_time": datetime(2026, 6, 20, 9, 0, 0),
            "end_time": datetime(2026, 6, 20, 11, 30, 0),
            "expected_teams": [
                {"team_id": 1, "team_name": "运行甲班", "expected_count": 12},
                {"team_id": 2, "team_name": "运行乙班", "expected_count": 12},
                {"team_id": 3, "team_name": "维修班", "expected_count": 8},
                {"team_id": 4, "team_name": "化验班", "expected_count": 6}
            ],
            "description": "模拟火灾场景，检验应急预案有效性及人员疏散能力",
            "status": "draft"
        },
        {
            "drill_name": "化学品泄漏应急处置演练",
            "drill_type": "泄漏演练",
            "location": "加药间及应急处置区域",
            "start_time": datetime(2026, 6, 15, 14, 0, 0),
            "end_time": datetime(2026, 6, 15, 16, 0, 0),
            "expected_teams": [
                {"team_id": 3, "team_name": "维修班", "expected_count": 8},
                {"team_id": 5, "team_name": "安全环保班", "expected_count": 5}
            ],
            "description": "模拟PAC药剂储罐泄漏应急处置",
            "status": "ongoing"
        }
    ]

    for i, d in enumerate(sample_drills):
        drill_no = f"DR{datetime.now().strftime('%Y%m%d')}{str(i+1).zfill(4)}"
        check_in_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        check_in_token = secrets.token_urlsafe(32)

        drill = EmergencyDrill(
            drill_no=drill_no,
            drill_name=d["drill_name"],
            drill_type=d["drill_type"],
            location=d["location"],
            start_time=d["start_time"],
            end_time=d["end_time"],
            expected_teams=d["expected_teams"],
            check_in_code=check_in_code,
            check_in_token=check_in_token,
            organizer_id=1,
            organizer_name="系统管理员",
            description=d["description"],
            status=d["status"]
        )
        db.add(drill)
        db.flush()

        if d["status"] == "ongoing":
            sample_checkins = [
                {"participant_name": "李建国", "team_name": "维修班", "check_in_time": datetime(2026, 6, 15, 13, 55, 0)},
                {"participant_name": "王志强", "team_name": "维修班", "check_in_time": datetime(2026, 6, 15, 13, 56, 0)},
                {"participant_name": "刘晓燕", "team_name": "维修班", "check_in_time": datetime(2026, 6, 15, 13, 57, 0)},
                {"participant_name": "张伟", "team_name": "安全环保班", "check_in_time": datetime(2026, 6, 15, 13, 58, 0)},
                {"participant_name": "陈敏", "team_name": "安全环保班", "check_in_time": datetime(2026, 6, 15, 13, 59, 0)}
            ]
            for ci in sample_checkins:
                check_in = DrillCheckIn(
                    drill_id=drill.id,
                    participant_name=ci["participant_name"],
                    team_name=ci["team_name"],
                    check_in_time=ci["check_in_time"],
                    check_in_type="code"
                )
                db.add(check_in)

    db.commit()
