import pytest
from datetime import datetime, timedelta


PLAN_DATE = "2026-01-15T00:00:00"


def _create_plan_payload(**overrides):
    base = {
        "plan_date": PLAN_DATE,
        "target_volume": 15000.0,
        "operation_mode": "standard",
        "description": "测试生产计划"
    }
    base.update(overrides)
    return base


class TestProductionPlanAuth:

    def test_create_plan_no_token(self, client):
        response = client.post("/api/production/plans", json=_create_plan_payload())
        assert response.status_code == 401

    def test_create_plan_invalid_token(self, client, invalid_auth_headers):
        response = client.post(
            "/api/production/plans",
            json=_create_plan_payload(),
            headers=invalid_auth_headers
        )
        assert response.status_code == 401

    def test_list_plans_no_token(self, client):
        response = client.get("/api/production/plans")
        assert response.status_code == 401

    def test_get_plan_no_token(self, client):
        response = client.get("/api/production/plans/1")
        assert response.status_code == 401

    def test_update_plan_no_token(self, client):
        response = client.put("/api/production/plans/1", json={"status": "executing"})
        assert response.status_code == 401

    def test_delete_plan_no_token(self, client):
        response = client.delete("/api/production/plans/1")
        assert response.status_code == 401


class TestProductionPlanCreate:

    def test_create_plan_success(self, client, auth_headers):
        payload = _create_plan_payload()
        response = client.post(
            "/api/production/plans",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["plan_no"].startswith("PP")
        assert data["target_volume"] == 15000.0
        assert data["operation_mode"] == "standard"
        assert data["description"] == "测试生产计划"
        assert data["status"] == "pending"
        assert "id" in data
        assert "created_at" in data

    def test_create_plan_minimal_payload(self, client, auth_headers):
        payload = {"plan_date": PLAN_DATE}
        response = client.post(
            "/api/production/plans",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["plan_no"].startswith("PP")
        assert data["target_volume"] is None
        assert data["operation_mode"] is None
        assert data["description"] is None

    def test_create_plan_missing_required_field(self, client, auth_headers):
        response = client.post(
            "/api/production/plans",
            json={"target_volume": 10000},
            headers=auth_headers
        )
        assert response.status_code == 422
        data = response.json()
        assert data["detail"][0]["loc"] == ["body", "plan_date"]

    def test_create_plan_invalid_date_type(self, client, auth_headers):
        response = client.post(
            "/api/production/plans",
            json={"plan_date": "not-a-date"},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_create_plan_invalid_volume_type(self, client, auth_headers):
        response = client.post(
            "/api/production/plans",
            json={"plan_date": PLAN_DATE, "target_volume": "not-a-number"},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_create_plan_empty_body(self, client, auth_headers):
        response = client.post(
            "/api/production/plans",
            json={},
            headers=auth_headers
        )
        assert response.status_code == 422


class TestProductionPlanList:

    def test_list_plans_empty(self, client, auth_headers):
        response = client.get("/api/production/plans", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["total_pages"] == 0

    def test_list_plans_with_data(self, client, auth_headers):
        for i in range(3):
            client.post(
                "/api/production/plans",
                json=_create_plan_payload(
                    plan_date=f"2026-01-{10+i:02d}T00:00:00",
                    description=f"计划{i+1}"
                ),
                headers=auth_headers
            )

        response = client.get("/api/production/plans", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_list_plans_pagination(self, client, auth_headers):
        for i in range(15):
            client.post(
                "/api/production/plans",
                json=_create_plan_payload(
                    plan_date=f"2026-01-{(i % 28) + 1:02d}T00:00:00",
                    description=f"计划{i+1}"
                ),
                headers=auth_headers
            )

        response = client.get("/api/production/plans?page=1&page_size=5", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 15
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert data["total_pages"] == 3
        assert len(data["items"]) == 5

        response = client.get("/api/production/plans?page=2&page_size=5", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert len(data["items"]) == 5

    def test_list_plans_invalid_page(self, client, auth_headers):
        response = client.get("/api/production/plans?page=0", headers=auth_headers)
        assert response.status_code == 422

    def test_list_plans_invalid_page_size(self, client, auth_headers):
        response = client.get("/api/production/plans?page_size=0", headers=auth_headers)
        assert response.status_code == 422

    def test_list_plans_page_size_too_large(self, client, auth_headers):
        response = client.get("/api/production/plans?page_size=200", headers=auth_headers)
        assert response.status_code == 422

    def test_list_plans_filter_by_status(self, client, auth_headers):
        statuses = ["pending", "executing", "completed"]
        for i, status in enumerate(statuses):
            create_resp = client.post(
                "/api/production/plans",
                json=_create_plan_payload(
                    plan_date=f"2026-01-{10+i:02d}T00:00:00",
                    description=f"{status}计划"
                ),
                headers=auth_headers
            )
            plan_id = create_resp.json()["id"]
            client.put(
                f"/api/production/plans/{plan_id}",
                json={"status": status},
                headers=auth_headers
            )

        response = client.get("/api/production/plans?status=pending", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "pending"

        response = client.get("/api/production/plans?status=executing", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "executing"

    def test_list_plans_ordered_by_date_desc(self, client, auth_headers):
        dates = ["2026-01-10T00:00:00", "2026-01-15T00:00:00", "2026-01-05T00:00:00"]
        for i, date in enumerate(dates):
            client.post(
                "/api/production/plans",
                json=_create_plan_payload(plan_date=date, description=f"计划{i+1}"),
                headers=auth_headers
            )

        response = client.get("/api/production/plans", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        plan_dates = [item["plan_date"] for item in data["items"]]
        assert plan_dates == sorted(plan_dates, reverse=True)

    def test_plan_response_fields(self, client, auth_headers):
        create_resp = client.post(
            "/api/production/plans",
            json=_create_plan_payload(),
            headers=auth_headers
        )
        plan_id = create_resp.json()["id"]

        response = client.get(f"/api/production/plans/{plan_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        expected_fields = [
            "id", "plan_no", "plan_date", "target_volume",
            "actual_volume", "operation_mode", "description",
            "status", "created_at"
        ]
        for field in expected_fields:
            assert field in data


class TestProductionPlanGet:

    def test_get_plan_success(self, client, auth_headers):
        create_resp = client.post(
            "/api/production/plans",
            json=_create_plan_payload(),
            headers=auth_headers
        )
        plan_id = create_resp.json()["id"]

        response = client.get(f"/api/production/plans/{plan_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == plan_id
        assert data["target_volume"] == 15000.0
        assert data["description"] == "测试生产计划"

    def test_get_plan_not_found(self, client, auth_headers):
        response = client.get("/api/production/plans/99999", headers=auth_headers)
        assert response.status_code == 404
        data = response.json()
        assert "生产计划不存在" in data["detail"]

    def test_get_plan_invalid_id_type(self, client, auth_headers):
        response = client.get("/api/production/plans/not-an-int", headers=auth_headers)
        assert response.status_code == 422


class TestProductionPlanUpdate:

    def test_update_plan_success(self, client, auth_headers):
        create_resp = client.post(
            "/api/production/plans",
            json=_create_plan_payload(),
            headers=auth_headers
        )
        plan_id = create_resp.json()["id"]

        update_data = {
            "target_volume": 20000.0,
            "status": "executing",
            "description": "更新后的描述"
        }
        response = client.put(
            f"/api/production/plans/{plan_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == plan_id
        assert data["target_volume"] == 20000.0
        assert data["status"] == "executing"
        assert data["description"] == "更新后的描述"

    def test_update_plan_partial_fields(self, client, auth_headers):
        create_resp = client.post(
            "/api/production/plans",
            json=_create_plan_payload(),
            headers=auth_headers
        )
        plan_id = create_resp.json()["id"]

        response = client.put(
            f"/api/production/plans/{plan_id}",
            json={"status": "completed"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["target_volume"] == 15000.0

    def test_update_plan_not_found(self, client, auth_headers):
        response = client.put(
            "/api/production/plans/99999",
            json={"status": "executing"},
            headers=auth_headers
        )
        assert response.status_code == 404
        data = response.json()
        assert "生产计划不存在" in data["detail"]

    def test_update_plan_invalid_id_type(self, client, auth_headers):
        response = client.put(
            "/api/production/plans/not-an-int",
            json={"status": "executing"},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_update_plan_invalid_volume_type(self, client, auth_headers):
        create_resp = client.post(
            "/api/production/plans",
            json=_create_plan_payload(),
            headers=auth_headers
        )
        plan_id = create_resp.json()["id"]

        response = client.put(
            f"/api/production/plans/{plan_id}",
            json={"target_volume": "not-a-number"},
            headers=auth_headers
        )
        assert response.status_code == 422


class TestProductionPlanDelete:

    def test_delete_plan_success(self, client, auth_headers):
        create_resp = client.post(
            "/api/production/plans",
            json=_create_plan_payload(),
            headers=auth_headers
        )
        plan_id = create_resp.json()["id"]

        response = client.delete(
            f"/api/production/plans/{plan_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "删除成功" in data["message"]
        assert data["success"] is True

        get_resp = client.get(f"/api/production/plans/{plan_id}", headers=auth_headers)
        assert get_resp.status_code == 404

    def test_delete_plan_not_found(self, client, auth_headers):
        response = client.delete("/api/production/plans/99999", headers=auth_headers)
        assert response.status_code == 404
        data = response.json()
        assert "生产计划不存在" in data["detail"]

    def test_delete_plan_invalid_id_type(self, client, auth_headers):
        response = client.delete("/api/production/plans/not-an-int", headers=auth_headers)
        assert response.status_code == 422


class TestProductionPlanIsolation:

    def test_first_creates_a_plan(self, client, auth_headers):
        response = client.post(
            "/api/production/plans",
            json=_create_plan_payload(description="独立测试计划A"),
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_second_starts_clean(self, client, auth_headers):
        response = client.get("/api/production/plans", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0


class TestProcessParameterAuth:

    def test_list_parameters_no_token(self, client):
        response = client.get("/api/production/parameters")
        assert response.status_code == 401

    def test_get_parameter_no_token(self, client):
        response = client.get("/api/production/parameters/1")
        assert response.status_code == 401

    def test_list_parameters_invalid_token(self, client, invalid_auth_headers):
        response = client.get(
            "/api/production/parameters",
            headers=invalid_auth_headers
        )
        assert response.status_code == 401


class TestProcessParameter:

    def test_list_parameters_empty(self, client, auth_headers):
        response = client.get("/api/production/parameters", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_parameters_with_data(self, client, auth_headers, test_process_parameter):
        response = client.get("/api/production/parameters", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["name"] == "进水COD浓度"
        assert data[0]["code"] == "INFLUENT_COD"

    def test_list_parameters_filter_by_section(self, client, auth_headers, test_process_parameter):
        response = client.get(
            "/api/production/parameters?process_section=进水段",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        for item in data:
            assert item["process_section"] == "进水段"

    def test_get_parameter_success(self, client, auth_headers, test_process_parameter):
        response = client.get(
            f"/api/production/parameters/{test_process_parameter.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_process_parameter.id
        assert data["name"] == "进水COD浓度"
        assert data["unit"] == "mg/L"
        assert data["current_value"] == 350.0

    def test_get_parameter_not_found(self, client, auth_headers):
        response = client.get("/api/production/parameters/99999", headers=auth_headers)
        assert response.status_code == 404
        data = response.json()
        assert "参数不存在" in data["detail"]

    def test_get_parameter_invalid_id_type(self, client, auth_headers):
        response = client.get("/api/production/parameters/not-an-int", headers=auth_headers)
        assert response.status_code == 422

    def test_parameter_response_fields(self, client, auth_headers, test_process_parameter):
        response = client.get(
            f"/api/production/parameters/{test_process_parameter.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        expected_fields = [
            "id", "name", "code", "unit", "current_value",
            "min_value", "max_value", "standard_value",
            "process_section", "status", "recorded_at"
        ]
        for field in expected_fields:
            assert field in data


class TestProductionLogAuth:

    def test_list_logs_no_token(self, client):
        response = client.get("/api/production/logs")
        assert response.status_code == 401

    def test_create_log_no_token(self, client):
        response = client.post(
            "/api/production/logs",
            json={"log_date": PLAN_DATE, "content": "测试日志"}
        )
        assert response.status_code == 401


class TestProductionLog:

    def test_list_logs_empty(self, client, auth_headers):
        response = client.get("/api/production/logs", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_logs_with_data(self, client, auth_headers, test_production_log):
        response = client.get("/api/production/logs", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    def test_create_log_success(self, client, auth_headers):
        payload = {
            "log_date": PLAN_DATE,
            "shift": "中班",
            "log_type": "manual",
            "content": "中班生产运行记录"
        }
        response = client.post(
            "/api/production/logs",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "中班生产运行记录"
        assert data["shift"] == "中班"
        assert data["log_type"] == "manual"
        assert "id" in data
        assert "operator_name" in data

    def test_create_log_minimal_payload(self, client, auth_headers):
        payload = {
            "log_date": PLAN_DATE,
            "content": "仅必填字段的日志"
        }
        response = client.post(
            "/api/production/logs",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "仅必填字段的日志"
        assert data["log_type"] == "manual"

    def test_create_log_missing_content(self, client, auth_headers):
        response = client.post(
            "/api/production/logs",
            json={"log_date": PLAN_DATE},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_create_log_missing_date(self, client, auth_headers):
        response = client.post(
            "/api/production/logs",
            json={"content": "缺少日期的日志"},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_create_log_invalid_date(self, client, auth_headers):
        response = client.post(
            "/api/production/logs",
            json={"log_date": "not-a-date", "content": "测试"},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_list_logs_filter_by_type(self, client, auth_headers):
        for i in range(2):
            client.post(
                "/api/production/logs",
                json={
                    "log_date": PLAN_DATE,
                    "log_type": "manual",
                    "content": f"手动记录{i}"
                },
                headers=auth_headers
            )
        client.post(
            "/api/production/logs",
            json={
                "log_date": PLAN_DATE,
                "log_type": "auto",
                "content": "自动记录"
            },
            headers=auth_headers
        )
        response = client.get(
            "/api/production/logs?log_type=manual",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_list_logs_filter_by_shift(self, client, auth_headers):
        for shift in ["早班", "中班", "晚班"]:
            client.post(
                "/api/production/logs",
                json={
                    "log_date": PLAN_DATE,
                    "shift": shift,
                    "content": f"{shift}日志"
                },
                headers=auth_headers
            )
        response = client.get(
            "/api/production/logs?shift=早班",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["shift"] == "早班"

    def test_list_logs_pagination(self, client, auth_headers):
        for i in range(12):
            client.post(
                "/api/production/logs",
                json={
                    "log_date": f"2026-01-{(i % 28) + 1:02d}T00:00:00",
                    "content": f"日志{i+1}"
                },
                headers=auth_headers
            )
        response = client.get(
            "/api/production/logs?page=1&page_size=5",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 12
        assert len(data["items"]) == 5
        assert data["total_pages"] == 3

    def test_list_logs_invalid_page(self, client, auth_headers):
        response = client.get("/api/production/logs?page=0", headers=auth_headers)
        assert response.status_code == 422

    def test_list_logs_invalid_page_size(self, client, auth_headers):
        response = client.get("/api/production/logs?page_size=0", headers=auth_headers)
        assert response.status_code == 422


class TestAbnormalAlarmAuth:

    def test_list_alarms_no_token(self, client):
        response = client.get("/api/production/alarms")
        assert response.status_code == 401

    def test_handle_alarm_no_token(self, client):
        response = client.put(
            "/api/production/alarms/1/handle",
            json={"handle_result": "已处理"}
        )
        assert response.status_code == 401


class TestAbnormalAlarm:

    def test_list_alarms_empty(self, client, auth_headers):
        response = client.get("/api/production/alarms", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_alarms_with_data(self, client, auth_headers, test_abnormal_alarm):
        response = client.get("/api/production/alarms", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    def test_list_alarms_filter_by_level(self, client, auth_headers, test_abnormal_alarm):
        response = client.get(
            "/api/production/alarms?alarm_level=warning",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["alarm_level"] == "warning"

    def test_list_alarms_filter_by_status(self, client, auth_headers, test_abnormal_alarm):
        response = client.get(
            "/api/production/alarms?status=pending",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["status"] == "pending"

    def test_handle_alarm_success(self, client, auth_headers, test_abnormal_alarm, test_user):
        response = client.put(
            f"/api/production/alarms/{test_abnormal_alarm.id}/handle",
            json={"handle_result": "已调整工艺参数，恢复正常"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "处理成功" in data["message"]
        assert data["success"] is True

    def test_handle_alarm_not_found(self, client, auth_headers):
        response = client.put(
            "/api/production/alarms/99999/handle",
            json={"handle_result": "测试"},
            headers=auth_headers
        )
        assert response.status_code == 404
        data = response.json()
        assert "告警不存在" in data["detail"]

    def test_handle_alarm_invalid_id_type(self, client, auth_headers):
        response = client.put(
            "/api/production/alarms/not-an-int/handle",
            json={"handle_result": "测试"},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_handle_alarm_missing_result(self, client, auth_headers, test_abnormal_alarm):
        response = client.put(
            f"/api/production/alarms/{test_abnormal_alarm.id}/handle",
            json={},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_alarm_response_fields(self, client, auth_headers, test_abnormal_alarm):
        response = client.get("/api/production/alarms", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        item = data["items"][0]
        expected_fields = [
            "id", "alarm_no", "alarm_type", "alarm_level", "title",
            "description", "source", "current_value", "threshold_value",
            "status", "handler_name", "handle_time", "alarm_time"
        ]
        for field in expected_fields:
            assert field in item


class TestProcessOptimizationAuth:

    def test_list_optimizations_no_token(self, client):
        response = client.get("/api/production/optimizations")
        assert response.status_code == 401

    def test_list_optimizations_invalid_token(self, client, invalid_auth_headers):
        response = client.get(
            "/api/production/optimizations",
            headers=invalid_auth_headers
        )
        assert response.status_code == 401


class TestProcessOptimization:

    def test_list_optimizations_empty(self, client, auth_headers):
        response = client.get("/api/production/optimizations", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_optimizations_with_data(self, client, auth_headers, test_process_optimization):
        response = client.get("/api/production/optimizations", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["title"] == "优化曝气池溶解氧控制策略"

    def test_list_optimizations_filter_by_type(self, client, auth_headers, test_process_optimization):
        response = client.get(
            "/api/production/optimizations?optimization_type=智能调节",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["optimization_type"] == "智能调节"

    def test_list_optimizations_filter_by_status(self, client, auth_headers, test_process_optimization):
        response = client.get(
            "/api/production/optimizations?status=pending",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["status"] == "pending"

    def test_optimization_response_fields(self, client, auth_headers, test_process_optimization):
        response = client.get("/api/production/optimizations", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        item = data[0]
        expected_fields = [
            "id", "title", "optimization_type", "current_situation",
            "suggestion", "expected_effect", "priority", "status", "created_at"
        ]
        for field in expected_fields:
            assert field in item

    def test_optimization_ordered_by_priority_desc(self, client, auth_headers, db_session, test_user):
        from app.models.production import ProcessOptimization
        opts = [
            ProcessOptimization(title="低优先级", suggestion="建议1", priority=1, status="pending", created_by=test_user.id),
            ProcessOptimization(title="高优先级", suggestion="建议2", priority=3, status="pending", created_by=test_user.id),
            ProcessOptimization(title="中优先级", suggestion="建议3", priority=2, status="pending", created_by=test_user.id),
        ]
        for opt in opts:
            db_session.add(opt)
        db_session.commit()

        response = client.get("/api/production/optimizations", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        priorities = [item["priority"] for item in data]
        assert priorities == sorted(priorities, reverse=True)
