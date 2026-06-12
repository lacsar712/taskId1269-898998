from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.models.message import Message, UserMessageRead, MessageType, MessagePriority
from app.schemas.common import PaginatedResponse, MessageResponse
from app.services.auth import get_current_active_user
import json

router = APIRouter(prefix="/api/messages", tags=["消息通知"])


class MessageResponseSchema(BaseModel):
    id: int
    title: str
    content: Optional[str]
    summary: Optional[str]
    message_type: str
    priority: str
    sender_name: Optional[str]
    related_type: Optional[str]
    related_id: Optional[int]
    related_url: Optional[str]
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    title: str
    content: Optional[str] = None
    summary: Optional[str] = None
    message_type: MessageType
    priority: MessagePriority = MessagePriority.MEDIUM
    sender_id: Optional[int] = None
    sender_name: Optional[str] = None
    related_type: Optional[str] = None
    related_id: Optional[int] = None
    related_url: Optional[str] = None
    is_global: bool = False
    target_user_ids: Optional[List[int]] = None


class UnreadCountResponse(BaseModel):
    total: int
    by_type: dict


def _get_user_messages_query(db: Session, user_id: int, is_read: Optional[bool] = None,
                             message_type: Optional[str] = None,
                             start_date: Optional[str] = None,
                             end_date: Optional[str] = None):
    query = db.query(
        Message,
        UserMessageRead.is_read,
        UserMessageRead.read_at
    ).outerjoin(
        UserMessageRead,
        and_(
            UserMessageRead.message_id == Message.id,
            UserMessageRead.user_id == user_id
        )
    ).filter(
        or_(
            Message.is_global == True,
            func.find_in_set(str(user_id), Message.target_user_ids) > 0
        )
    )

    if is_read is not None:
        if is_read:
            query = query.filter(UserMessageRead.is_read == True)
        else:
            query = query.filter(
                or_(
                    UserMessageRead.is_read == False,
                    UserMessageRead.id.is_(None)
                )
            )

    if message_type:
        query = query.filter(Message.message_type == message_type)

    if start_date:
        query = query.filter(Message.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))

    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query = query.filter(Message.created_at < end_dt)

    return query


@router.get("", response_model=PaginatedResponse[MessageResponseSchema])
def get_messages(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    is_read: Optional[bool] = None,
    message_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = _get_user_messages_query(db, current_user.id, is_read, message_type, start_date, end_date)

    total = query.count()
    results = query.order_by(Message.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for msg, is_read_val, read_at_val in results:
        item = MessageResponseSchema(
            id=msg.id,
            title=msg.title,
            content=msg.content,
            summary=msg.summary,
            message_type=msg.message_type.value,
            priority=msg.priority.value,
            sender_name=msg.sender_name,
            related_type=msg.related_type,
            related_id=msg.related_id,
            related_url=msg.related_url,
            is_read=is_read_val if is_read_val is not None else False,
            read_at=read_at_val,
            created_at=msg.created_at
        )
        items.append(item)

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/recent", response_model=List[MessageResponseSchema])
def get_recent_messages(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = _get_user_messages_query(db, current_user.id)
    results = query.order_by(Message.created_at.desc()).limit(limit).all()

    items = []
    for msg, is_read_val, read_at_val in results:
        item = MessageResponseSchema(
            id=msg.id,
            title=msg.title,
            content=msg.content,
            summary=msg.summary,
            message_type=msg.message_type.value,
            priority=msg.priority.value,
            sender_name=msg.sender_name,
            related_type=msg.related_type,
            related_id=msg.related_id,
            related_url=msg.related_url,
            is_read=is_read_val if is_read_val is not None else False,
            read_at=read_at_val,
            created_at=msg.created_at
        )
        items.append(item)

    return items


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = _get_user_messages_query(db, current_user.id, is_read=False)
    total = query.count()

    by_type = {}
    for msg_type in MessageType:
        type_query = _get_user_messages_query(db, current_user.id, is_read=False, message_type=msg_type.value)
        by_type[msg_type.value] = type_query.count()

    return UnreadCountResponse(total=total, by_type=by_type)


@router.put("/{message_id}/read", response_model=MessageResponse)
def mark_message_read(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")

    user_read = db.query(UserMessageRead).filter(
        UserMessageRead.message_id == message_id,
        UserMessageRead.user_id == current_user.id
    ).first()

    if not user_read:
        user_read = UserMessageRead(
            user_id=current_user.id,
            message_id=message_id,
            is_read=True,
            read_at=datetime.now()
        )
        db.add(user_read)
    else:
        user_read.is_read = True
        user_read.read_at = datetime.now()

    db.commit()
    return MessageResponse(message="标记已读成功")


@router.put("/read-all", response_model=MessageResponse)
def mark_all_messages_read(
    message_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = _get_user_messages_query(db, current_user.id, is_read=False, message_type=message_type)
    results = query.all()

    for msg, _, _ in results:
        user_read = db.query(UserMessageRead).filter(
            UserMessageRead.message_id == msg.id,
            UserMessageRead.user_id == current_user.id
        ).first()

        if not user_read:
            user_read = UserMessageRead(
                user_id=current_user.id,
                message_id=msg.id,
                is_read=True,
                read_at=datetime.now()
            )
            db.add(user_read)
        else:
            user_read.is_read = True
            user_read.read_at = datetime.now()

    db.commit()
    return MessageResponse(message=f"已将 {len(results)} 条消息标记为已读")


@router.post("", response_model=MessageResponse)
def create_message(
    data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    target_user_ids_str = None
    if data.target_user_ids:
        target_user_ids_str = ",".join(map(str, data.target_user_ids))

    message = Message(
        title=data.title,
        content=data.content,
        summary=data.summary,
        message_type=data.message_type,
        priority=data.priority,
        sender_id=data.sender_id or current_user.id,
        sender_name=data.sender_name or current_user.real_name or current_user.username,
        related_type=data.related_type,
        related_id=data.related_id,
        related_url=data.related_url,
        is_global=data.is_global,
        target_user_ids=target_user_ids_str
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    return MessageResponse(message="消息创建成功")


@router.delete("/{message_id}", response_model=MessageResponse)
def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")

    db.delete(message)
    db.commit()

    return MessageResponse(message="消息删除成功")


def init_sample_messages(db: Session):
    """初始化示例消息数据"""
    if db.query(Message).count() > 0:
        return

    sample_messages = [
        {
            "title": "出水COD超标告警",
            "content": "检测到出水COD浓度为35mg/L，超过排放标准30mg/L，请及时处理。",
            "summary": "出水COD浓度超标，需要立即处理",
            "message_type": MessageType.ALARM,
            "priority": MessagePriority.URGENT,
            "sender_name": "系统监测",
            "related_type": "alarm",
            "related_id": 1,
            "related_url": "/production/alarm",
            "is_global": True
        },
        {
            "title": "作业许可审批待处理",
            "content": "您有一条新的作业许可申请等待审批，申请人：张三，作业类型：高处作业。",
            "summary": "作业许可审批待处理",
            "message_type": MessageType.APPROVAL,
            "priority": MessagePriority.HIGH,
            "sender_name": "张三",
            "related_type": "permit",
            "related_id": 1,
            "related_url": "/safety/permit",
            "is_global": False,
            "target_user_ids": [1, 2]
        },
        {
            "title": "新工单指派",
            "content": "您被指派处理新的工单：曝气风机#1异常振动检查，工单编号：WO20240115001。",
            "summary": "新工单：曝气风机#1异常振动检查",
            "message_type": MessageType.WORKORDER,
            "priority": MessagePriority.HIGH,
            "sender_name": "李四",
            "related_type": "workorder",
            "related_id": 1,
            "related_url": "/workorder-center",
            "is_global": False,
            "target_user_ids": [2, 3]
        },
        {
            "title": "系统维护公告",
            "content": "系统将于2024年01月20日22:00-24:00进行例行维护，期间可能影响部分功能使用，请提前做好相关工作安排。",
            "summary": "系统将于1月20日晚进行例行维护",
            "message_type": MessageType.ANNOUNCEMENT,
            "priority": MessagePriority.MEDIUM,
            "sender_name": "系统管理员",
            "is_global": True
        },
        {
            "title": "生化池DO偏低告警",
            "content": "生化池溶解氧浓度为1.2mg/L，低于设定阈值1.5mg/L，请检查曝气系统运行状态。",
            "summary": "生化池DO浓度偏低，需要检查曝气系统",
            "message_type": MessageType.ALARM,
            "priority": MessagePriority.HIGH,
            "sender_name": "系统监测",
            "related_type": "alarm",
            "related_id": 2,
            "related_url": "/production/alarm",
            "is_global": True
        },
        {
            "title": "设备维护提醒",
            "content": "刮泥机设备维护时间已到，请安排维护人员进行定期维护保养。",
            "summary": "刮泥机需要进行定期维护",
            "message_type": MessageType.WORKORDER,
            "priority": MessagePriority.MEDIUM,
            "sender_name": "系统提醒",
            "related_type": "equipment",
            "related_id": 7,
            "related_url": "/equipment/maintenance",
            "is_global": False,
            "target_user_ids": [2, 5]
        },
        {
            "title": "月度绩效考核通知",
            "content": "2024年1月绩效考核已开始，请各部门于1月25日前完成绩效数据填报工作。",
            "summary": "1月绩效考核已开始，请按时填报",
            "message_type": MessageType.ANNOUNCEMENT,
            "priority": MessagePriority.MEDIUM,
            "sender_name": "人力资源部",
            "is_global": True
        },
        {
            "title": "安全培训审批通过",
            "content": "您提交的安全培训申请已通过审批，培训时间：2024年01月18日14:00-16:00。",
            "summary": "安全培训申请已通过审批",
            "message_type": MessageType.APPROVAL,
            "priority": MessagePriority.MEDIUM,
            "sender_name": "赵六",
            "related_type": "training",
            "related_id": 1,
            "related_url": "/safety/training",
            "is_global": False,
            "target_user_ids": [3, 4]
        }
    ]

    for msg_data in sample_messages:
        target_user_ids = msg_data.pop("target_user_ids", None)
        target_user_ids_str = None
        if target_user_ids:
            target_user_ids_str = ",".join(map(str, target_user_ids))

        message = Message(
            **msg_data,
            target_user_ids=target_user_ids_str
        )
        db.add(message)

    db.commit()
    print("示例消息数据初始化完成")
