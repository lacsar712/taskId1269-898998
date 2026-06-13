import sys
import os
from typing import Dict, Any

import pytest
import schemathesis
from hypothesis import settings, HealthCheck
from schemathesis.checks import ResponseError
from schemathesis.models import Case

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database import get_db
from app.models.user import User, Role
from app.services.auth import get_password_hash

schema = schemathesis.from_asgi("/openapi.json", app)

ALLOWED_STATUS_CODES = {200, 201, 204, 301, 302, 304, 400, 401, 403, 404, 405, 409, 422}


@pytest.fixture(scope="module")
def contract_test_client():
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.database import Base

    TEST_DATABASE_URL = "sqlite:///./contract_test.db"
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        role = Role(name="契约测试管理员", code="contract_admin", description="契约测试用管理员角色")
        db.add(role)
        db.commit()
        db.refresh(role)

        user = User(
            username="contract_test_user",
            password_hash=get_password_hash("contract_test_pass123"),
            real_name="契约测试用户",
            email="contract@example.com",
            phone="13900139000",
            department="测试部",
            position="契约测试工程师",
            role_id=role.id,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    finally:
        db.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        response = test_client.post(
            "/api/auth/login",
            json={"username": "contract_test_user", "password": "contract_test_pass123"}
        )
        token = response.json()["access_token"]
        test_client.headers = {"Authorization": f"Bearer {token}"}
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "contract_test.db")
    if os.path.exists(db_path):
        os.remove(db_path)


def check_status_code_whitelist(response, case):
    if response.status_code == 500:
        raise ResponseError(
            f"Server error (500) at {case.method} {case.path}: {response.text}",
            context={"status_code": 500, "response": response.text}
        )
    if response.status_code not in ALLOWED_STATUS_CODES:
        raise ResponseError(
            f"Unexpected status code {response.status_code} at {case.method} {case.path}. "
            f"Allowed: {sorted(ALLOWED_STATUS_CODES)}",
            context={"status_code": response.status_code, "allowed": sorted(ALLOWED_STATUS_CODES)}
        )
    return True


def check_no_undeclared_fields(response, case: Case):
    if response.status_code not in {200, 201}:
        return True
    try:
        data = response.json()
    except (ValueError, AttributeError):
        return True

    if case.operation is None or case.operation.responses is None:
        return True

    response_definition = case.operation.responses.get(str(response.status_code))
    if response_definition is None:
        return True

    content = getattr(response_definition, "content", None)
    if not content:
        return True

    json_content = content.get("application/json")
    if json_content is None or not hasattr(json_content, "schema") or json_content.schema is None:
        return True

    schema_props = json_content.schema.get("properties", {}) if isinstance(json_content.schema, dict) else {}
    if not schema_props or not isinstance(data, dict):
        return True

    undeclared = set(data.keys()) - set(schema_props.keys())
    if undeclared:
        raise ResponseError(
            f"Undeclared fields in response at {case.method} {case.path}: {sorted(undeclared)}. "
            f"Declared: {sorted(schema_props.keys())}",
            context={"undeclared_fields": sorted(undeclared), "declared_fields": sorted(schema_props.keys())}
        )
    return True


def check_no_server_errors_on_boundary_inputs(response, case):
    if response.status_code >= 500:
        raise ResponseError(
            f"Server error ({response.status_code}) with boundary input at {case.method} {case.path}. "
            f"Request: {case.body}, Query: {case.query}, Path: {case.path_parameters}",
            context={
                "status_code": response.status_code,
                "body": case.body,
                "query": case.query,
                "path_params": case.path_parameters
            }
        )
    return True


@schema.parametrize(endpoint="^/api/")
@settings(
    max_examples=20,
    suppress_health_check=[
        HealthCheck.filter_too_much,
        HealthCheck.too_slow,
        HealthCheck.data_too_large,
        HealthCheck.function_scoped_fixture
    ],
    deadline=None
)
def test_api_contract(case: Case, contract_test_client):
    case.call_and_validate(
        session=contract_test_client,
        checks=[
            check_status_code_whitelist,
            check_no_undeclared_fields,
            check_no_server_errors_on_boundary_inputs,
        ]
    )


@schema.parametrize(endpoint="^(?!/api/)")
@settings(
    max_examples=10,
    suppress_health_check=[
        HealthCheck.filter_too_much,
        HealthCheck.too_slow,
        HealthCheck.function_scoped_fixture
    ],
    deadline=None
)
def test_root_contract(case: Case, contract_test_client):
    case.call_and_validate(
        session=contract_test_client,
        checks=[
            check_status_code_whitelist,
            check_no_server_errors_on_boundary_inputs,
        ]
    )
