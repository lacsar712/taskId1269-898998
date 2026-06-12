from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class TeamBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    shift_type: Optional[str] = "three"
    is_active: Optional[int] = 1


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    shift_type: Optional[str] = None
    is_active: Optional[int] = None


class TeamResponse(TeamBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TeamMemberBase(BaseModel):
    team_id: int
    user_id: int
    position: Optional[str] = None


class TeamMemberCreate(TeamMemberBase):
    pass


class TeamMemberResponse(TeamMemberBase):
    id: int
    user_name: Optional[str] = None
    real_name: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ShiftScheduleBase(BaseModel):
    team_id: int
    user_id: int
    shift_date: date
    shift_type: str
    remark: Optional[str] = None


class ShiftScheduleCreate(ShiftScheduleBase):
    pass


class ShiftScheduleUpdate(BaseModel):
    shift_type: Optional[str] = None
    remark: Optional[str] = None


class ShiftScheduleResponse(ShiftScheduleBase):
    id: int
    user_name: Optional[str] = None
    real_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ShiftScheduleBatchCreate(BaseModel):
    team_id: int
    user_ids: List[int]
    shift_date: date
    shift_type: str
    remark: Optional[str] = None


class ShiftScheduleWeekCopy(BaseModel):
    team_id: int
    source_week_start: date
    target_week_start: date


class UserShiftStats(BaseModel):
    user_id: int
    real_name: str
    morning_count: int
    afternoon_count: int
    night_count: int
    rest_count: int
    total_work_hours: float
    total_days: int
