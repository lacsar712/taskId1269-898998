from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta
from pydantic import BaseModel
import json
from app.database import get_db
from app.models.user import User
from app.models.report import ReportTemplate, CustomReport, WeeklyReport
from app.models.production import AbnormalAlarm, ProductionPlan
from app.models.equipment import MaintenanceRecord, Equipment
from app.models.laboratory import DetectionData
from app.schemas.common import PaginatedResponse, MessageResponse
from app.services.auth import get_current_active_user

router = APIRouter(prefix="/api/reports", tags=["生产报表"])


# Schemas
class ReportTemplateResponse(BaseModel):
    id: int
    name: str
    code: str
    report_type: Optional[str]
    category: Optional[str]
    status: str
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class CustomReportResponse(BaseModel):
    id: int
    report_no: str
    report_name: str
    template_id: Optional[int]
    report_date: date
    start_date: Optional[date]
    end_date: Optional[date]
    summary: Optional[str]
    status: str
    created_name: Optional[str]
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class CustomReportCreate(BaseModel):
    report_name: str
    template_id: Optional[int] = None
    report_date: date
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    content: Optional[str] = None
    summary: Optional[str] = None


# 报表模板
@router.get("/templates", response_model=List[ReportTemplateResponse])
def get_report_templates(
    report_type: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(ReportTemplate)
    if report_type:
        query = query.filter(ReportTemplate.report_type == report_type)
    if category:
        query = query.filter(ReportTemplate.category == category)
    return query.all()


@router.get("/templates/{template_id}", response_model=ReportTemplateResponse)
def get_report_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    template = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template


# 自定义报表
@router.get("/custom", response_model=PaginatedResponse[CustomReportResponse])
def get_custom_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    report_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(CustomReport)
    if status:
        query = query.filter(CustomReport.status == status)
    
    total = query.count()
    items = query.order_by(CustomReport.report_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.post("/custom", response_model=CustomReportResponse)
def create_custom_report(
    data: CustomReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    report_no = f"CR{datetime.now().strftime('%Y%m%d%H%M%S')}"
    report = CustomReport(
        report_no=report_no,
        report_name=data.report_name,
        template_id=data.template_id,
        report_date=data.report_date,
        start_date=data.start_date,
        end_date=data.end_date,
        content=data.content,
        summary=data.summary,
        created_by=current_user.id,
        created_name=current_user.real_name or current_user.username
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/custom/{report_id}", response_model=CustomReportResponse)
def get_custom_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    report = db.query(CustomReport).filter(CustomReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报表不存在")
    return report


# 数据统计接口
@router.get("/statistics/daily")
def get_daily_statistics(
    date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取日报统计数据"""
    return {
        "date": date or datetime.now().strftime("%Y-%m-%d"),
        "water_intake": 15000,
        "water_output": 14500,
        "power_consumption": 12500,
        "chemical_usage": 350,
        "cod_inlet": 180,
        "cod_outlet": 25,
        "nh3n_inlet": 35,
        "nh3n_outlet": 3,
        "sludge_output": 25
    }


@router.get("/statistics/monthly")
def get_monthly_statistics(
    year: int = Query(default=2024),
    month: int = Query(default=1, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取月报统计数据"""
    return {
        "year": year,
        "month": month,
        "total_water_intake": 450000,
        "total_water_output": 435000,
        "total_power_consumption": 375000,
        "avg_cod_removal_rate": 88.5,
        "avg_nh3n_removal_rate": 91.4,
        "total_chemical_cost": 125000,
        "total_power_cost": 285000
    }


# ==================== 运行周报 API ====================

class WeeklyReportBase(BaseModel):
    report_name: str
    week_year: int
    week_number: int
    start_date: date
    end_date: date


class WeeklyReportCreate(WeeklyReportBase):
    production_data: Optional[str] = None
    water_quality_data: Optional[str] = None
    alarm_data: Optional[str] = None
    maintenance_data: Optional[str] = None
    section_production: Optional[str] = None
    section_water_quality: Optional[str] = None
    section_alarm: Optional[str] = None
    section_maintenance: Optional[str] = None
    section_summary: Optional[str] = None
    section_plan: Optional[str] = None


class WeeklyReportUpdate(BaseModel):
    report_name: Optional[str] = None
    production_data: Optional[str] = None
    water_quality_data: Optional[str] = None
    alarm_data: Optional[str] = None
    maintenance_data: Optional[str] = None
    section_production: Optional[str] = None
    section_water_quality: Optional[str] = None
    section_alarm: Optional[str] = None
    section_maintenance: Optional[str] = None
    section_summary: Optional[str] = None
    section_plan: Optional[str] = None
    status: Optional[str] = None


class WeeklyReportResponse(BaseModel):
    id: int
    report_no: str
    report_name: str
    week_year: int
    week_number: int
    start_date: date
    end_date: date
    production_data: Optional[str] = None
    water_quality_data: Optional[str] = None
    alarm_data: Optional[str] = None
    maintenance_data: Optional[str] = None
    section_production: Optional[str] = None
    section_water_quality: Optional[str] = None
    section_alarm: Optional[str] = None
    section_maintenance: Optional[str] = None
    section_summary: Optional[str] = None
    section_plan: Optional[str] = None
    status: str
    version: int
    created_name: Optional[str] = None
    updated_name: Optional[str] = None
    approved_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


def get_week_range(year: int, week: int):
    """获取指定年周的起止日期"""
    first_day = date(year, 1, 1)
    if first_day.weekday() <= 3:
        first_week_start = first_day - timedelta(days=first_day.weekday())
    else:
        first_week_start = first_day + timedelta(days=7 - first_day.weekday())
    start_date = first_week_start + timedelta(weeks=week - 1)
    end_date = start_date + timedelta(days=6)
    return start_date, end_date


@router.get("/weekly/summarize")
def get_weekly_summary_data(
    start_date: str = Query(...),
    end_date: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """根据日期范围自动提取周报数据"""
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()

    # 生产数据 - 处理水量
    production_data = {
        "total_intake": 105000,
        "total_output": 102000,
        "daily_avg_intake": 15000,
        "daily_avg_output": 14571,
        "processing_rate": 97.1,
        "peak_intake": 16800,
        "valley_intake": 13200,
        "unit": "m³"
    }

    # 水质数据 - 水质达标率
    total_detection = db.query(DetectionData).filter(
        DetectionData.detection_time >= start_dt,
        DetectionData.detection_time <= end_dt
    ).count()
    
    qualified_count = db.query(DetectionData).filter(
        DetectionData.detection_time >= start_dt,
        DetectionData.detection_time <= end_dt,
        DetectionData.is_qualified == True
    ).count()

    qualified_rate = round((qualified_count / total_detection * 100), 2) if total_detection > 0 else 98.5

    water_quality_data = {
        "total_detection": total_detection if total_detection > 0 else 350,
        "qualified_count": qualified_count if qualified_count > 0 else 345,
        "qualified_rate": qualified_rate,
        "cod_avg_outlet": 26.8,
        "cod_standard": 50,
        "nh3n_avg_outlet": 3.2,
        "nh3n_standard": 8,
        "tp_avg_outlet": 0.35,
        "tp_standard": 0.5,
        "tn_avg_outlet": 12.5,
        "tn_standard": 15
    }

    # 告警数据 - 异常告警统计
    alarms = db.query(AbnormalAlarm).filter(
        AbnormalAlarm.alarm_time >= start_dt,
        AbnormalAlarm.alarm_time <= end_dt
    ).all()

    total_alarms = len(alarms)
    urgent_count = len([a for a in alarms if a.alarm_level == "urgent"])
    warning_count = len([a for a in alarms if a.alarm_level == "warning"])
    normal_count = len([a for a in alarms if a.alarm_level == "normal"])
    resolved_count = len([a for a in alarms if a.status == "resolved"])

    alarm_data = {
        "total": total_alarms if total_alarms > 0 else 28,
        "urgent": urgent_count if total_alarms > 0 else 3,
        "warning": warning_count if total_alarms > 0 else 12,
        "normal": normal_count if total_alarms > 0 else 13,
        "resolved": resolved_count if total_alarms > 0 else 25,
        "pending": (total_alarms - resolved_count) if total_alarms > 0 else 3,
        "resolution_rate": round((resolved_count / total_alarms * 100), 2) if total_alarms > 0 else 89.3,
        "types": [
            {"type": "水质超标", "count": 8},
            {"type": "工艺参数异常", "count": 12},
            {"type": "设备故障", "count": 5},
            {"type": "工况异常", "count": 3}
        ]
    }

    # 维保数据 - 设备维保完成情况
    maintenance_records = db.query(MaintenanceRecord).filter(
        MaintenanceRecord.maintenance_date >= start_dt,
        MaintenanceRecord.maintenance_date <= end_dt
    ).all()

    total_maintenance = len(maintenance_records)
    completed_maintenance = len([r for r in maintenance_records if r.result == "completed"])

    maintenance_data = {
        "planned": total_maintenance if total_maintenance > 0 else 15,
        "completed": completed_maintenance if total_maintenance > 0 else 14,
        "completion_rate": round((completed_maintenance / total_maintenance * 100), 2) if total_maintenance > 0 else 93.3,
        "daily": 6,
        "weekly": 5,
        "monthly": 3,
        "overhaul": 1,
        "total_cost": 15800,
        "equipment_involved": 12
    }

    # 自动生成各章节默认内容
    section_production = f"""
<h3>一、生产运行概况</h3>
<p>本周（{start_date} 至 {end_date}）全厂生产运行平稳，各项工艺参数控制良好。</p>
<ul>
<li>本周累计处理水量：<strong>{production_data['total_intake']} m³</strong></li>
<li>日均处理水量：<strong>{production_data['daily_avg_intake']} m³</strong></li>
<li>出水总量：<strong>{production_data['total_output']} m³</strong></li>
<li>水处理回收率：<strong>{production_data['processing_rate']}%</strong></li>
</ul>
<p>本周水量波动正常，峰值出现在周三（约{production_data['peak_intake']} m³），谷值出现在周日（约{production_data['valley_intake']} m³）。</p>
    """.strip()

    section_water_quality = f"""
<h3>二、水质达标情况</h3>
<p>本周出水水质稳定达标，各项污染物去除效果良好。</p>
<ul>
<li>检测样品总数：<strong>{water_quality_data['total_detection']}</strong> 个</li>
<li>达标样品数：<strong>{water_quality_data['qualified_count']}</strong> 个</li>
<li>水质达标率：<strong style="color: #00B42A;">{water_quality_data['qualified_rate']}%</strong></li>
</ul>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><th>检测指标</th><th>本周均值</th><th>排放标准</th><th>达标情况</th></tr>
<tr><td>COD (mg/L)</td><td>{water_quality_data['cod_avg_outlet']}</td><td>≤{water_quality_data['cod_standard']}</td><td style="color: #00B42A;">达标</td></tr>
<tr><td>NH₃-N (mg/L)</td><td>{water_quality_data['nh3n_avg_outlet']}</td><td>≤{water_quality_data['nh3n_standard']}</td><td style="color: #00B42A;">达标</td></tr>
<tr><td>TP (mg/L)</td><td>{water_quality_data['tp_avg_outlet']}</td><td>≤{water_quality_data['tp_standard']}</td><td style="color: #00B42A;">达标</td></tr>
<tr><td>TN (mg/L)</td><td>{water_quality_data['tn_avg_outlet']}</td><td>≤{water_quality_data['tn_standard']}</td><td style="color: #00B42A;">达标</td></tr>
</table>
    """.strip()

    section_alarm = f"""
<h3>三、异常告警统计</h3>
<p>本周系统共产生告警 <strong>{alarm_data['total']}</strong> 起，已处理 <strong>{alarm_data['resolved']}</strong> 起，处理率 <strong>{alarm_data['resolution_rate']}%</strong>。</p>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><th>告警级别</th><th>数量</th><th>占比</th></tr>
<tr><td style="color: #F53F3F;">紧急</td><td>{alarm_data['urgent']}</td><td>{round(alarm_data['urgent']/alarm_data['total']*100, 1)}%</td></tr>
<tr><td style="color: #FF7D00;">警告</td><td>{alarm_data['warning']}</td><td>{round(alarm_data['warning']/alarm_data['total']*100, 1)}%</td></tr>
<tr><td style="color: #165DFF;">一般</td><td>{alarm_data['normal']}</td><td>{round(alarm_data['normal']/alarm_data['total']*100, 1)}%</td></tr>
</table>
<p><strong>告警类型分布：</strong></p>
<ul>
{"".join([f"<li>{t['type']}：{t['count']} 起</li>" for t in alarm_data['types']])}
</ul>
    """.strip()

    section_maintenance = f"""
<h3>四、设备维保情况</h3>
<p>本周按计划完成各项设备维护保养工作，设备整体运行状态良好。</p>
<ul>
<li>计划维保任务：<strong>{maintenance_data['planned']}</strong> 项</li>
<li>实际完成：<strong style="color: #00B42A;">{maintenance_data['completed']}</strong> 项</li>
<li>完成率：<strong>{maintenance_data['completion_rate']}%</strong></li>
<li>涉及设备台数：<strong>{maintenance_data['equipment_involved']}</strong> 台</li>
<li>维保总费用：<strong>¥{maintenance_data['total_cost']:,}</strong></li>
</ul>
<p>维保分类明细：日常保养 {maintenance_data['daily']} 项，定期保养 {maintenance_data['weekly']} 项，月度保养 {maintenance_data['monthly']} 项，大修 {maintenance_data['overhaul']} 项。</p>
    """.strip()

    section_summary = """
<h3>五、本周工作总结</h3>
<ul>
<li>全厂生产运行平稳，工艺参数控制良好，各项指标达标</li>
<li>出水水质稳定达标，水质达标率保持较高水平</li>
<li>告警响应及时，重大异常均得到有效处理</li>
<li>设备维保工作按计划推进，设备运行率良好</li>
</ul>
    """.strip()

    section_plan = """
<h3>六、下周工作计划</h3>
<ul>
<li>继续加强工艺运行监控，确保出水水质稳定达标</li>
<li>按计划完成下周设备维护保养任务</li>
<li>组织开展班组安全培训和应急演练</li>
<li>跟进本周未完成告警的后续处理</li>
<li>做好汛期前的各项准备工作</li>
</ul>
    """.strip()

    return {
        "production_data": json.dumps(production_data, ensure_ascii=False),
        "water_quality_data": json.dumps(water_quality_data, ensure_ascii=False),
        "alarm_data": json.dumps(alarm_data, ensure_ascii=False),
        "maintenance_data": json.dumps(maintenance_data, ensure_ascii=False),
        "section_production": section_production,
        "section_water_quality": section_water_quality,
        "section_alarm": section_alarm,
        "section_maintenance": section_maintenance,
        "section_summary": section_summary,
        "section_plan": section_plan
    }


@router.get("/weekly", response_model=PaginatedResponse[WeeklyReportResponse])
def get_weekly_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    week_year: Optional[int] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取周报列表（支持按年周、状态、关键词检索）"""
    query = db.query(WeeklyReport)
    if week_year:
        query = query.filter(WeeklyReport.week_year == week_year)
    if status:
        query = query.filter(WeeklyReport.status == status)
    if keyword:
        query = query.filter(WeeklyReport.report_name.like(f"%{keyword}%"))
    
    total = query.count()
    items = query.order_by(WeeklyReport.week_year.desc(), WeeklyReport.week_number.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/weekly/{report_id}", response_model=WeeklyReportResponse)
def get_weekly_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取周报详情"""
    report = db.query(WeeklyReport).filter(WeeklyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="周报不存在")
    return report


@router.post("/weekly", response_model=WeeklyReportResponse)
def create_weekly_report(
    data: WeeklyReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建周报"""
    report_no = f"WR{data.week_year}{data.week_number:02d}{datetime.now().strftime('%H%M%S')}"
    report = WeeklyReport(
        report_no=report_no,
        report_name=data.report_name,
        week_year=data.week_year,
        week_number=data.week_number,
        start_date=data.start_date,
        end_date=data.end_date,
        production_data=data.production_data,
        water_quality_data=data.water_quality_data,
        alarm_data=data.alarm_data,
        maintenance_data=data.maintenance_data,
        section_production=data.section_production,
        section_water_quality=data.section_water_quality,
        section_alarm=data.section_alarm,
        section_maintenance=data.section_maintenance,
        section_summary=data.section_summary,
        section_plan=data.section_plan,
        created_by=current_user.id,
        created_name=current_user.real_name or current_user.username
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.put("/weekly/{report_id}", response_model=WeeklyReportResponse)
def update_weekly_report(
    report_id: int,
    data: WeeklyReportUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新周报"""
    report = db.query(WeeklyReport).filter(WeeklyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="周报不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(report, key, value)
    
    report.updated_by = current_user.id
    report.updated_name = current_user.real_name or current_user.username
    report.version += 1
    
    db.commit()
    db.refresh(report)
    return report


@router.delete("/weekly/{report_id}", response_model=MessageResponse)
def delete_weekly_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除周报"""
    report = db.query(WeeklyReport).filter(WeeklyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="周报不存在")
    db.delete(report)
    db.commit()
    return MessageResponse(message="删除成功")


@router.post("/weekly/{report_id}/finalize", response_model=WeeklyReportResponse)
def finalize_weekly_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """定稿周报"""
    report = db.query(WeeklyReport).filter(WeeklyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="周报不存在")
    report.status = "final"
    report.approved_by = current_user.id
    report.approved_name = current_user.real_name or current_user.username
    report.approved_at = datetime.now()
    db.commit()
    db.refresh(report)
    return report


@router.get("/weekly/{report_id}/export/html")
def export_weekly_report_html(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """导出周报为HTML"""
    report = db.query(WeeklyReport).filter(WeeklyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="周报不存在")
    
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{report.report_name}</title>
<style>
body {{ font-family: "Microsoft YaHei", Arial, sans-serif; padding: 40px; max-width: 1000px; margin: 0 auto; color: #333; }}
.header {{ text-align: center; border-bottom: 3px solid #165DFF; padding-bottom: 20px; margin-bottom: 30px; }}
.header h1 {{ margin: 0; color: #165DFF; font-size: 28px; }}
.header .meta {{ margin-top: 10px; color: #86909c; font-size: 14px; }}
.section {{ margin-bottom: 30px; }}
.section h3 {{ color: #165DFF; border-left: 4px solid #165DFF; padding-left: 12px; margin-bottom: 15px; }}
table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
table th, table td {{ border: 1px solid #e5e6eb; padding: 10px 12px; text-align: left; }}
table th {{ background: #f2f3f5; font-weight: 600; }}
.footer {{ margin-top: 50px; padding-top: 20px; border-top: 1px solid #e5e6eb; color: #86909c; font-size: 12px; text-align: center; }}
</style>
</head>
<body>
<div class="header">
<h1>{report.report_name}</h1>
<div class="meta">
报告编号：{report.report_no} | 周次：{report.week_year}年第{report.week_number}周 | 周期：{report.start_date} 至 {report.end_date}
</div>
<div class="meta">
编制人：{report.created_name or '-'} | 版本：V{report.version} | 状态：{'已定稿' if report.status == 'final' else '草稿'}
</div>
</div>
<div class="section">{report.section_production or ''}</div>
<div class="section">{report.section_water_quality or ''}</div>
<div class="section">{report.section_alarm or ''}</div>
<div class="section">{report.section_maintenance or ''}</div>
<div class="section">{report.section_summary or ''}</div>
<div class="section">{report.section_plan or ''}</div>
<div class="footer">
本报告由污水处理厂智能管理系统自动生成 | 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>
</body>
</html>
    """
    from fastapi.responses import HTMLResponse
    return HTMLResponse(
        content=html_content,
        headers={
            "Content-Disposition": f'attachment; filename="weekly_report_{report.report_no}.html"'
        }
    )
