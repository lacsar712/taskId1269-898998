from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class TemplateType(str, enum.Enum):
    DAILY = "daily"
    SHIFT = "shift"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class FieldType(str, enum.Enum):
    NUMBER = "number"
    TEXT = "text"
    SELECT = "select"


class FieldDataTemplate(Base):
    """现场数据采集模板"""
    __tablename__ = "field_data_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="模板名称")
    code = Column(String(50), unique=True, nullable=False, comment="模板编码")
    description = Column(String(500), comment="模板描述")
    template_type = Column(String(20), default="daily", comment="模板类型：daily日报/shift班报/weekly周报/monthly月报")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_by = Column(Integer, comment="创建人ID")
    created_by_name = Column(String(50), comment="创建人姓名")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    fields = relationship("FieldDataTemplateField", back_populates="template", cascade="all, delete-orphan")
    records = relationship("FieldDataRecord", back_populates="template")


class FieldDataTemplateField(Base):
    """模板字段"""
    __tablename__ = "field_data_template_fields"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("field_data_templates.id"), nullable=False, comment="模板ID")
    field_name = Column(String(100), nullable=False, comment="字段名称")
    field_code = Column(String(50), nullable=False, comment="字段编码")
    field_type = Column(String(20), default="text", comment="字段类型：number数字/text文本/select单选下拉")
    is_required = Column(Boolean, default=False, comment="是否必填")
    default_value = Column(String(500), comment="默认值")
    options = Column(Text, comment="下拉选项(JSON数组格式)")
    unit = Column(String(20), comment="单位(数字类型使用)")
    sort_order = Column(Integer, default=0, comment="排序")
    created_at = Column(DateTime, server_default=func.now())

    template = relationship("FieldDataTemplate", back_populates="fields")
    values = relationship("FieldDataRecordValue", back_populates="field")


class FieldDataRecord(Base):
    """填报记录"""
    __tablename__ = "field_data_records"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("field_data_templates.id"), nullable=False, comment="模板ID")
    record_date = Column(DateTime, nullable=False, comment="填报日期")
    shift = Column(String(20), comment="班次：morning早班/afternoon中班/night晚班")
    operator_id = Column(Integer, comment="填报人ID")
    operator_name = Column(String(50), comment="填报人姓名")
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime, server_default=func.now())

    template = relationship("FieldDataTemplate", back_populates="records")
    values = relationship("FieldDataRecordValue", back_populates="record", cascade="all, delete-orphan")


class FieldDataRecordValue(Base):
    """填报记录数据值"""
    __tablename__ = "field_data_record_values"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("field_data_records.id"), nullable=False, comment="记录ID")
    field_id = Column(Integer, ForeignKey("field_data_template_fields.id"), nullable=False, comment="字段ID")
    field_name = Column(String(100), nullable=False, comment="字段名称(快照)")
    field_value = Column(Text, comment="字段值")
    created_at = Column(DateTime, server_default=func.now())

    record = relationship("FieldDataRecord", back_populates="values")
    field = relationship("FieldDataTemplateField", back_populates="values")
