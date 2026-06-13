import sys
import os
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, get_db
from app.models.user import User, Role
from app.services.auth import get_password_hash, create_access_token
from app.main import app

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test.db")
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_role(db_session):
    role = Role(
        name="测试管理员",
        code="test_admin",
        description="测试用管理员角色"
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role


@pytest.fixture(scope="function")
def test_user(db_session, test_role):
    user = User(
        username="testuser",
        password_hash=get_password_hash("testpass123"),
        real_name="测试用户",
        email="test@example.com",
        phone="13800138000",
        department="测试部",
        position="测试工程师",
        role_id=test_role.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def inactive_user(db_session, test_role):
    user = User(
        username="inactiveuser",
        password_hash=get_password_hash("testpass123"),
        real_name="已禁用用户",
        email="inactive@example.com",
        role_id=test_role.id,
        is_active=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(client, test_user):
    response = client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "testpass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def invalid_auth_headers():
    return {"Authorization": "Bearer invalid.token.string"}


@pytest.fixture(scope="function")
def expired_auth_headers():
    from datetime import timedelta
    token = create_access_token(
        data={"sub": "testuser", "user_id": 999},
        expires_delta=timedelta(days=-1)
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def test_process_parameter(db_session):
    from app.models.production import ProcessParameter
    param = ProcessParameter(
        name="进水COD浓度",
        code="INFLUENT_COD",
        unit="mg/L",
        current_value=350.0,
        min_value=100.0,
        max_value=500.0,
        standard_value=300.0,
        process_section="进水段",
        status="normal"
    )
    db_session.add(param)
    db_session.commit()
    db_session.refresh(param)
    return param


@pytest.fixture(scope="function")
def test_production_plan(db_session, test_user):
    from app.models.production import ProductionPlan
    from datetime import datetime
    plan = ProductionPlan(
        plan_no="PP20260115000001",
        plan_date=datetime(2026, 1, 15),
        target_volume=15000.0,
        actual_volume=14500.0,
        operation_mode="standard",
        description="测试生产计划",
        status="pending",
        created_by=test_user.id
    )
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)
    return plan


@pytest.fixture(scope="function")
def test_production_log(db_session, test_user):
    from app.models.production import ProductionLog
    from datetime import datetime
    log = ProductionLog(
        log_date=datetime(2026, 1, 15),
        shift="早班",
        log_type="manual",
        content="今日生产运行正常，设备状态良好",
        operator_id=test_user.id,
        operator_name=test_user.real_name
    )
    db_session.add(log)
    db_session.commit()
    db_session.refresh(log)
    return log


@pytest.fixture(scope="function")
def test_abnormal_alarm(db_session):
    from app.models.production import AbnormalAlarm
    from datetime import datetime
    alarm = AbnormalAlarm(
        alarm_no="ALM202601150001",
        alarm_type="水质超标",
        alarm_level="warning",
        title="出水COD超标告警",
        description="出水COD浓度超过排放标准",
        source="在线监测仪",
        current_value=85.0,
        threshold_value=60.0,
        status="pending",
        alarm_time=datetime(2026, 1, 15, 14, 30, 0)
    )
    db_session.add(alarm)
    db_session.commit()
    db_session.refresh(alarm)
    return alarm


@pytest.fixture(scope="function")
def test_process_optimization(db_session, test_user):
    from app.models.production import ProcessOptimization
    opt = ProcessOptimization(
        title="优化曝气池溶解氧控制策略",
        optimization_type="智能调节",
        current_situation="当前曝气池DO控制精度不足，能耗偏高",
        suggestion="采用模糊PID控制算法，根据进水负荷动态调节曝气量",
        expected_effect="预计可降低曝气能耗10%-15%",
        priority=2,
        status="pending",
        created_by=test_user.id
    )
    db_session.add(opt)
    db_session.commit()
    db_session.refresh(opt)
    return opt
