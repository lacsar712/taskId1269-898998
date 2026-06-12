from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import List, Optional
from app.database import get_db
from app.models.schedule import Team, TeamMember, ShiftSchedule
from app.models.user import User
from app.schemas.schedule import (
    TeamCreate, TeamUpdate, TeamResponse,
    TeamMemberCreate, TeamMemberResponse,
    ShiftScheduleCreate, ShiftScheduleUpdate, ShiftScheduleResponse,
    ShiftScheduleBatchCreate, ShiftScheduleWeekCopy,
    UserShiftStats
)

router = APIRouter(prefix="/api/schedule", tags=["排班管理"])


@router.get("/teams", response_model=List[TeamResponse])
def get_teams(is_active: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Team)
    if is_active is not None:
        query = query.filter(Team.is_active == is_active)
    return query.order_by(Team.id).all()


@router.post("/teams", response_model=TeamResponse)
def create_team(team_data: TeamCreate, db: Session = Depends(get_db)):
    existing = db.query(Team).filter(
        (Team.name == team_data.name) | (Team.code == team_data.code)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="班组名称或编码已存在")
    team = Team(**team_data.model_dump())
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


@router.put("/teams/{team_id}", response_model=TeamResponse)
def update_team(team_id: int, team_data: TeamUpdate, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="班组不存在")
    update_data = team_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(team, key, value)
    db.commit()
    db.refresh(team)
    return team


@router.delete("/teams/{team_id}")
def delete_team(team_id: int, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="班组不存在")
    db.delete(team)
    db.commit()
    return {"message": "删除成功"}


@router.get("/teams/{team_id}/members", response_model=List[TeamMemberResponse])
def get_team_members(team_id: int, db: Session = Depends(get_db)):
    members = db.query(TeamMember).filter(TeamMember.team_id == team_id).all()
    result = []
    for member in members:
        user = db.query(User).filter(User.id == member.user_id).first()
        resp = TeamMemberResponse(
            id=member.id,
            team_id=member.team_id,
            user_id=member.user_id,
            position=member.position,
            user_name=user.username if user else None,
            real_name=user.real_name if user else None,
            created_at=member.created_at
        )
        result.append(resp)
    return result


@router.post("/teams/members", response_model=TeamMemberResponse)
def add_team_member(member_data: TeamMemberCreate, db: Session = Depends(get_db)):
    existing = db.query(TeamMember).filter(
        TeamMember.team_id == member_data.team_id,
        TeamMember.user_id == member_data.user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该成员已在班组中")
    member = TeamMember(**member_data.model_dump())
    db.add(member)
    db.commit()
    db.refresh(member)
    user = db.query(User).filter(User.id == member.user_id).first()
    return TeamMemberResponse(
        id=member.id,
        team_id=member.team_id,
        user_id=member.user_id,
        position=member.position,
        user_name=user.username if user else None,
        real_name=user.real_name if user else None,
        created_at=member.created_at
    )


@router.delete("/teams/members/{member_id}")
def remove_team_member(member_id: int, db: Session = Depends(get_db)):
    member = db.query(TeamMember).filter(TeamMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="成员不存在")
    db.delete(member)
    db.commit()
    return {"message": "移除成功"}


@router.get("/shift/{team_id}", response_model=List[ShiftScheduleResponse])
def get_weekly_schedule(
    team_id: int,
    week_start: date = Query(..., description="周起始日期"),
    db: Session = Depends(get_db)
):
    week_end = week_start + timedelta(days=6)
    schedules = db.query(ShiftSchedule).filter(
        ShiftSchedule.team_id == team_id,
        ShiftSchedule.shift_date >= week_start,
        ShiftSchedule.shift_date <= week_end
    ).all()
    result = []
    for s in schedules:
        user = db.query(User).filter(User.id == s.user_id).first()
        resp = ShiftScheduleResponse(
            id=s.id,
            team_id=s.team_id,
            user_id=s.user_id,
            shift_date=s.shift_date,
            shift_type=s.shift_type,
            remark=s.remark,
            user_name=user.username if user else None,
            real_name=user.real_name if user else None,
            created_at=s.created_at,
            updated_at=s.updated_at
        )
        result.append(resp)
    return result


@router.post("/shift", response_model=ShiftScheduleResponse)
def create_shift_schedule(schedule_data: ShiftScheduleCreate, db: Session = Depends(get_db)):
    existing = db.query(ShiftSchedule).filter(
        ShiftSchedule.team_id == schedule_data.team_id,
        ShiftSchedule.user_id == schedule_data.user_id,
        ShiftSchedule.shift_date == schedule_data.shift_date
    ).first()
    if existing:
        existing.shift_type = schedule_data.shift_type
        existing.remark = schedule_data.remark
        db.commit()
        db.refresh(existing)
        user = db.query(User).filter(User.id == existing.user_id).first()
        return ShiftScheduleResponse(
            id=existing.id,
            team_id=existing.team_id,
            user_id=existing.user_id,
            shift_date=existing.shift_date,
            shift_type=existing.shift_type,
            remark=existing.remark,
            user_name=user.username if user else None,
            real_name=user.real_name if user else None,
            created_at=existing.created_at,
            updated_at=existing.updated_at
        )
    schedule = ShiftSchedule(**schedule_data.model_dump())
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    user = db.query(User).filter(User.id == schedule.user_id).first()
    return ShiftScheduleResponse(
        id=schedule.id,
        team_id=schedule.team_id,
        user_id=schedule.user_id,
        shift_date=schedule.shift_date,
        shift_type=schedule.shift_type,
        remark=schedule.remark,
        user_name=user.username if user else None,
        real_name=user.real_name if user else None,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at
    )


@router.put("/shift/{schedule_id}", response_model=ShiftScheduleResponse)
def update_shift_schedule(
    schedule_id: int,
    schedule_data: ShiftScheduleUpdate,
    db: Session = Depends(get_db)
):
    schedule = db.query(ShiftSchedule).filter(ShiftSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="排班记录不存在")
    update_data = schedule_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(schedule, key, value)
    db.commit()
    db.refresh(schedule)
    user = db.query(User).filter(User.id == schedule.user_id).first()
    return ShiftScheduleResponse(
        id=schedule.id,
        team_id=schedule.team_id,
        user_id=schedule.user_id,
        shift_date=schedule.shift_date,
        shift_type=schedule.shift_type,
        remark=schedule.remark,
        user_name=user.username if user else None,
        real_name=user.real_name if user else None,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at
    )


@router.delete("/shift/{schedule_id}")
def delete_shift_schedule(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.query(ShiftSchedule).filter(ShiftSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="排班记录不存在")
    db.delete(schedule)
    db.commit()
    return {"message": "删除成功"}


@router.post("/shift/batch")
def batch_create_shift(batch_data: ShiftScheduleBatchCreate, db: Session = Depends(get_db)):
    created_count = 0
    for user_id in batch_data.user_ids:
        existing = db.query(ShiftSchedule).filter(
            ShiftSchedule.team_id == batch_data.team_id,
            ShiftSchedule.user_id == user_id,
            ShiftSchedule.shift_date == batch_data.shift_date
        ).first()
        if existing:
            existing.shift_type = batch_data.shift_type
            existing.remark = batch_data.remark
        else:
            schedule = ShiftSchedule(
                team_id=batch_data.team_id,
                user_id=user_id,
                shift_date=batch_data.shift_date,
                shift_type=batch_data.shift_type,
                remark=batch_data.remark
            )
            db.add(schedule)
        created_count += 1
    db.commit()
    return {"message": f"批量排班成功，共{created_count}条记录"}


@router.post("/shift/week-copy")
def copy_week_schedule(copy_data: ShiftScheduleWeekCopy, db: Session = Depends(get_db)):
    source_end = copy_data.source_week_start + timedelta(days=6)
    source_schedules = db.query(ShiftSchedule).filter(
        ShiftSchedule.team_id == copy_data.team_id,
        ShiftSchedule.shift_date >= copy_data.source_week_start,
        ShiftSchedule.shift_date <= source_end
    ).all()
    
    day_offset = (copy_data.target_week_start - copy_data.source_week_start).days
    copied_count = 0
    
    for s in source_schedules:
        target_date = s.shift_date + timedelta(days=day_offset)
        existing = db.query(ShiftSchedule).filter(
            ShiftSchedule.team_id == s.team_id,
            ShiftSchedule.user_id == s.user_id,
            ShiftSchedule.shift_date == target_date
        ).first()
        if existing:
            existing.shift_type = s.shift_type
            existing.remark = s.remark
        else:
            new_schedule = ShiftSchedule(
                team_id=s.team_id,
                user_id=s.user_id,
                shift_date=target_date,
                shift_type=s.shift_type,
                remark=s.remark
            )
            db.add(new_schedule)
        copied_count += 1
    
    db.commit()
    return {"message": f"整周复制成功，共{copied_count}条记录"}


@router.get("/user/{user_id}/monthly-stats", response_model=UserShiftStats)
def get_user_monthly_stats(
    user_id: int,
    month: date = Query(..., description="统计月份（传入该月任意一天）"),
    db: Session = Depends(get_db)
):
    import calendar
    year = month.year
    month_num = month.month
    _, last_day = calendar.monthrange(year, month_num)
    month_start = date(year, month_num, 1)
    month_end = date(year, month_num, last_day)
    
    schedules = db.query(ShiftSchedule).filter(
        ShiftSchedule.user_id == user_id,
        ShiftSchedule.shift_date >= month_start,
        ShiftSchedule.shift_date <= month_end
    ).all()
    
    morning_count = sum(1 for s in schedules if s.shift_type == "morning")
    afternoon_count = sum(1 for s in schedules if s.shift_type == "afternoon")
    night_count = sum(1 for s in schedules if s.shift_type == "night")
    rest_count = sum(1 for s in schedules if s.shift_type == "rest")
    
    work_hours_map = {
        "morning": 8.0,
        "afternoon": 8.0,
        "night": 8.0,
        "rest": 0.0
    }
    total_work_hours = sum(work_hours_map.get(s.shift_type, 0) for s in schedules)
    
    user = db.query(User).filter(User.id == user_id).first()
    
    return UserShiftStats(
        user_id=user_id,
        real_name=user.real_name if user else "",
        morning_count=morning_count,
        afternoon_count=afternoon_count,
        night_count=night_count,
        rest_count=rest_count,
        total_work_hours=total_work_hours,
        total_days=len(schedules)
    )


@router.get("/shift/matrix/{team_id}")
def get_schedule_matrix(
    team_id: int,
    week_start: date = Query(..., description="周起始日期"),
    db: Session = Depends(get_db)
):
    week_end = week_start + timedelta(days=6)
    
    members = db.query(TeamMember).filter(TeamMember.team_id == team_id).all()
    member_ids = [m.user_id for m in members]
    
    schedules = db.query(ShiftSchedule).filter(
        ShiftSchedule.team_id == team_id,
        ShiftSchedule.user_id.in_(member_ids),
        ShiftSchedule.shift_date >= week_start,
        ShiftSchedule.shift_date <= week_end
    ).all()
    
    schedule_map = {}
    for s in schedules:
        key = f"{s.user_id}_{s.shift_date}"
        schedule_map[key] = {
            "id": s.id,
            "shift_type": s.shift_type,
            "remark": s.remark
        }
    
    dates = []
    current = week_start
    while current <= week_end:
        dates.append(current.isoformat())
        current += timedelta(days=1)
    
    users = []
    for member in members:
        user = db.query(User).filter(User.id == member.user_id).first()
        if user:
            user_schedules = {}
            for d in dates:
                key = f"{user.id}_{d}"
                user_schedules[d] = schedule_map.get(key, None)
            users.append({
                "user_id": user.id,
                "username": user.username,
                "real_name": user.real_name,
                "position": member.position,
                "schedules": user_schedules
            })
    
    return {
        "team_id": team_id,
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "dates": dates,
        "users": users
    }
