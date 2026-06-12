from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.models.field_data import (
    FieldDataTemplate, FieldDataTemplateField,
    FieldDataRecord, FieldDataRecordValue
)
from app.schemas.common import PaginatedResponse, MessageResponse
from app.services.auth import get_current_active_user
import json

router = APIRouter(prefix="/api/field-data", tags=["现场数据填报"])


# Schema: 模板字段
class TemplateFieldBase(BaseModel):
    field_name: str
    field_code: str
    field_type: str = "text"
    is_required: bool = False
    default_value: Optional[str] = None
    options: Optional[str] = None
    unit: Optional[str] = None
    sort_order: int = 0


class TemplateFieldCreate(TemplateFieldBase):
    pass


class TemplateFieldUpdate(TemplateFieldBase):
    id: Optional[int] = None


class TemplateFieldResponse(TemplateFieldBase):
    id: int
    template_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Schema: 模板
class TemplateBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    template_type: str = "daily"
    is_active: bool = True


class TemplateCreate(TemplateBase):
    fields: List[TemplateFieldCreate]


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    template_type: Optional[str] = None
    is_active: Optional[bool] = None
    fields: Optional[List[TemplateFieldUpdate]] = None


class TemplateResponse(TemplateBase):
    id: int
    created_by: Optional[int] = None
    created_by_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    fields: List[TemplateFieldResponse] = []

    class Config:
        from_attributes = True


class TemplateSimpleResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    template_type: str
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Schema: 填报记录值
class RecordValueBase(BaseModel):
    field_id: int
    field_value: Optional[str] = None


class RecordValueCreate(RecordValueBase):
    field_name: str


class RecordValueResponse(RecordValueBase):
    id: int
    record_id: int
    field_name: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Schema: 填报记录
class RecordBase(BaseModel):
    template_id: int
    record_date: datetime
    shift: Optional[str] = None
    remark: Optional[str] = None


class RecordCreate(RecordBase):
    values: List[RecordValueCreate]


class RecordResponse(RecordBase):
    id: int
    operator_id: Optional[int] = None
    operator_name: Optional[str] = None
    created_at: Optional[datetime] = None
    values: List[RecordValueResponse] = []

    class Config:
        from_attributes = True


class RecordListResponse(BaseModel):
    id: int
    template_id: int
    template_name: str
    template_type: str
    record_date: datetime
    shift: Optional[str] = None
    operator_name: Optional[str] = None
    remark: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 模板管理
@router.get("/templates", response_model=PaginatedResponse[TemplateSimpleResponse])
def get_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    template_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(FieldDataTemplate)
    if template_type:
        query = query.filter(FieldDataTemplate.template_type == template_type)
    if is_active is not None:
        query = query.filter(FieldDataTemplate.is_active == is_active)
    if keyword:
        query = query.filter(
            (FieldDataTemplate.name.like(f"%{keyword}%")) |
            (FieldDataTemplate.code.like(f"%{keyword}%"))
        )

    total = query.count()
    items = query.order_by(FieldDataTemplate.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/templates/all", response_model=List[TemplateSimpleResponse])
def get_all_active_templates(
    template_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(FieldDataTemplate).filter(FieldDataTemplate.is_active == True)
    if template_type:
        query = query.filter(FieldDataTemplate.template_type == template_type)
    return query.order_by(FieldDataTemplate.created_at.desc()).all()


@router.get("/templates/{template_id}", response_model=TemplateResponse)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    template = db.query(FieldDataTemplate).filter(FieldDataTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template


@router.post("/templates", response_model=TemplateResponse)
def create_template(
    template_data: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    existing = db.query(FieldDataTemplate).filter(FieldDataTemplate.code == template_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="模板编码已存在")

    template = FieldDataTemplate(
        name=template_data.name,
        code=template_data.code,
        description=template_data.description,
        template_type=template_data.template_type,
        is_active=template_data.is_active,
        created_by=current_user.id,
        created_by_name=current_user.real_name or current_user.username
    )

    for field_data in template_data.fields:
        field = FieldDataTemplateField(
            field_name=field_data.field_name,
            field_code=field_data.field_code,
            field_type=field_data.field_type,
            is_required=field_data.is_required,
            default_value=field_data.default_value,
            options=field_data.options,
            unit=field_data.unit,
            sort_order=field_data.sort_order
        )
        template.fields.append(field)

    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.put("/templates/{template_id}", response_model=TemplateResponse)
def update_template(
    template_id: int,
    template_data: TemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    template = db.query(FieldDataTemplate).filter(FieldDataTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    if template_data.name is not None:
        template.name = template_data.name
    if template_data.description is not None:
        template.description = template_data.description
    if template_data.template_type is not None:
        template.template_type = template_data.template_type
    if template_data.is_active is not None:
        template.is_active = template_data.is_active

    if template_data.fields is not None:
        existing_field_ids = [f.id for f in template.fields]
        new_field_ids = [f.id for f in template_data.fields if f.id]

        for field_id in existing_field_ids:
            if field_id not in new_field_ids:
                field = db.query(FieldDataTemplateField).filter(FieldDataTemplateField.id == field_id).first()
                if field:
                    db.delete(field)

        for field_data in template_data.fields:
            if field_data.id:
                field = db.query(FieldDataTemplateField).filter(FieldDataTemplateField.id == field_data.id).first()
                if field:
                    field.field_name = field_data.field_name
                    field.field_code = field_data.field_code
                    field.field_type = field_data.field_type
                    field.is_required = field_data.is_required
                    field.default_value = field_data.default_value
                    field.options = field_data.options
                    field.unit = field_data.unit
                    field.sort_order = field_data.sort_order
            else:
                field = FieldDataTemplateField(
                    template_id=template_id,
                    field_name=field_data.field_name,
                    field_code=field_data.field_code,
                    field_type=field_data.field_type,
                    is_required=field_data.is_required,
                    default_value=field_data.default_value,
                    options=field_data.options,
                    unit=field_data.unit,
                    sort_order=field_data.sort_order
                )
                db.add(field)

    db.commit()
    db.refresh(template)
    return template


@router.put("/templates/{template_id}/toggle-status", response_model=MessageResponse)
def toggle_template_status(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    template = db.query(FieldDataTemplate).filter(FieldDataTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    template.is_active = not template.is_active
    db.commit()

    status_text = "启用" if template.is_active else "停用"
    return MessageResponse(message=f"模板已{status_text}")


@router.delete("/templates/{template_id}", response_model=MessageResponse)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    template = db.query(FieldDataTemplate).filter(FieldDataTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    record_count = db.query(FieldDataRecord).filter(FieldDataRecord.template_id == template_id).count()
    if record_count > 0:
        raise HTTPException(status_code=400, detail="该模板已有填报记录，无法删除")

    db.delete(template)
    db.commit()
    return MessageResponse(message="删除成功")


# 填报记录
@router.get("/records", response_model=PaginatedResponse[RecordListResponse])
def get_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    template_id: Optional[int] = None,
    template_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    shift: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(
        FieldDataRecord,
        FieldDataTemplate.name.label("template_name"),
        FieldDataTemplate.template_type.label("template_type")
    ).join(FieldDataTemplate, FieldDataRecord.template_id == FieldDataTemplate.id)

    if template_id:
        query = query.filter(FieldDataRecord.template_id == template_id)
    if template_type:
        query = query.filter(FieldDataTemplate.template_type == template_type)
    if start_date:
        query = query.filter(FieldDataRecord.record_date >= start_date)
    if end_date:
        query = query.filter(FieldDataRecord.record_date <= end_date)
    if shift:
        query = query.filter(FieldDataRecord.shift == shift)

    total = query.count()
    results = query.order_by(FieldDataRecord.record_date.desc(), FieldDataRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for record, template_name, template_type in results:
        items.append(RecordListResponse(
            id=record.id,
            template_id=record.template_id,
            template_name=template_name,
            template_type=template_type,
            record_date=record.record_date,
            shift=record.shift,
            operator_name=record.operator_name,
            remark=record.remark,
            created_at=record.created_at
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/records/{record_id}", response_model=RecordResponse)
def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    record = db.query(FieldDataRecord).filter(FieldDataRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return record


@router.post("/records", response_model=RecordResponse)
def create_record(
    record_data: RecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    template = db.query(FieldDataTemplate).filter(FieldDataTemplate.id == record_data.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    if not template.is_active:
        raise HTTPException(status_code=400, detail="该模板已停用，无法填报")

    field_map = {f.id: f for f in template.fields}
    for value_data in record_data.values:
        field = field_map.get(value_data.field_id)
        if not field:
            raise HTTPException(status_code=400, detail=f"字段ID {value_data.field_id} 不存在")
        if field.is_required and (value_data.field_value is None or value_data.field_value == ""):
            raise HTTPException(status_code=400, detail=f"字段 {field.field_name} 为必填项")
        if field.field_type == "number" and value_data.field_value:
            try:
                float(value_data.field_value)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"字段 {field.field_name} 必须是数字")

    record = FieldDataRecord(
        template_id=record_data.template_id,
        record_date=record_data.record_date,
        shift=record_data.shift,
        operator_id=current_user.id,
        operator_name=current_user.real_name or current_user.username,
        remark=record_data.remark
    )

    for value_data in record_data.values:
        value = FieldDataRecordValue(
            field_id=value_data.field_id,
            field_name=value_data.field_name,
            field_value=value_data.field_value
        )
        record.values.append(value)

    db.add(record)
    db.commit()
    db.refresh(record)
    return record
