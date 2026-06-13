import pytest
from datetime import datetime


class TestLogin:

    def test_login_success(self, client, test_user):
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpass123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_login_wrong_password(self, client, test_user):
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        data = response.json()
        assert "用户名或密码错误" in data["detail"]

    def test_login_wrong_username(self, client, test_user):
        response = client.post(
            "/api/auth/login",
            json={"username": "nonexistent", "password": "testpass123"}
        )
        assert response.status_code == 401
        data = response.json()
        assert "用户名或密码错误" in data["detail"]

    def test_login_inactive_user(self, client, inactive_user):
        response = client.post(
            "/api/auth/login",
            json={"username": "inactiveuser", "password": "testpass123"}
        )
        assert response.status_code == 403
        data = response.json()
        assert "用户已被禁用" in data["detail"]

    def test_login_missing_username(self, client):
        response = client.post(
            "/api/auth/login",
            json={"password": "testpass123"}
        )
        assert response.status_code == 422
        data = response.json()
        assert data["detail"][0]["loc"] == ["body", "username"]

    def test_login_missing_password(self, client):
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser"}
        )
        assert response.status_code == 422
        data = response.json()
        assert data["detail"][0]["loc"] == ["body", "password"]

    def test_login_empty_body(self, client):
        response = client.post("/api/auth/login", json={})
        assert response.status_code == 422

    def test_login_wrong_content_type(self, client):
        response = client.post(
            "/api/auth/login",
            data={"username": "testuser", "password": "testpass123"}
        )
        assert response.status_code == 422

    def test_login_updates_last_login(self, client, test_user, db_session):
        before_login = test_user.last_login
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpass123"}
        )
        assert response.status_code == 200
        db_session.refresh(test_user)
        assert test_user.last_login is not None
        if before_login:
            assert test_user.last_login > before_login

    def test_login_token_is_jwt_format(self, client, test_user):
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpass123"}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        parts = token.split(".")
        assert len(parts) == 3

    def test_login_token_contains_user_info(self, client, test_user):
        from app.services.auth import decode_token
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpass123"}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert payload["user_id"] == test_user.id
        assert "exp" in payload

    def test_login_returns_correct_token_type(self, client, test_user):
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpass123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["token_type"] == "bearer"

    def test_login_empty_username(self, client):
        response = client.post(
            "/api/auth/login",
            json={"username": "", "password": "testpass123"}
        )
        assert response.status_code == 401

    def test_login_empty_password(self, client, test_user):
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": ""}
        )
        assert response.status_code == 401

    def test_login_whitespace_username(self, client, test_user):
        response = client.post(
            "/api/auth/login",
            json={"username": " testuser ", "password": "testpass123"}
        )
        assert response.status_code == 401


class TestGetCurrentUser:

    def test_get_me_success(self, client, auth_headers, test_user):
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["real_name"] == "测试用户"
        assert data["email"] == "test@example.com"
        assert data["is_active"] is True
        assert "id" in data
        assert "role_name" in data

    def test_get_me_no_token(self, client):
        response = client.get("/api/auth/me")
        assert response.status_code == 401
        data = response.json()
        assert "Not authenticated" in data["detail"]

    def test_get_me_invalid_token(self, client, invalid_auth_headers):
        response = client.get("/api/auth/me", headers=invalid_auth_headers)
        assert response.status_code == 401
        data = response.json()
        assert "无法验证凭据" in data["detail"]

    def test_get_me_expired_token(self, client, expired_auth_headers):
        response = client.get("/api/auth/me", headers=expired_auth_headers)
        assert response.status_code == 401
        data = response.json()
        assert "无法验证凭据" in data["detail"]

    def test_get_me_wrong_scheme(self, client, auth_headers):
        headers = {"Authorization": f"Basic {auth_headers['Authorization'].split(' ')[1]}"}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401

    def test_get_me_response_has_all_fields(self, client, auth_headers):
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        expected_fields = [
            "id", "username", "real_name", "email", "phone",
            "department", "position", "role_id", "is_active",
            "last_login", "created_at", "role_name"
        ]
        for field in expected_fields:
            assert field in data

    def test_get_me_returns_correct_role_name(self, client, auth_headers, test_role):
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["role_name"] == test_role.name


class TestLogout:

    def test_logout_success(self, client, auth_headers):
        response = client.post("/api/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "退出成功" in data["message"]

    def test_logout_no_token(self, client):
        response = client.post("/api/auth/logout")
        assert response.status_code == 401

    def test_logout_invalid_token(self, client, invalid_auth_headers):
        response = client.post("/api/auth/logout", headers=invalid_auth_headers)
        assert response.status_code == 401
