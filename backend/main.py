# -*- coding: utf-8 -*-
"""People Studio HTTP and Agent entrypoint."""

from __future__ import annotations

import json
import sys
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
from qwenpaw.plugins.api import PluginApi

try:
    from .people_engine import (
        analyze_hr,
        manage_anniversaries,
        recommend_approval_path,
        search_contacts,
        suggest_permissions,
    )
    from .people_workflow import PeopleWorkflowStore
except ImportError:
    backend_dir = str(Path(__file__).resolve().parent)
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from people_engine import (
        analyze_hr,
        manage_anniversaries,
        recommend_approval_path,
        search_contacts,
        suggest_permissions,
    )
    from people_workflow import PeopleWorkflowStore

router = APIRouter()
PLUGIN_VERSION = "0.2.0"


def _store() -> PeopleWorkflowStore:
    try:
        return PeopleWorkflowStore()
    except (OSError, sqlite3.Error) as exc:
        raise HTTPException(status_code=503, detail=f"人力持久化依赖不可用：{exc}") from exc


class UsersRequest(BaseModel):
    users: list[dict[str, Any]] = Field(max_length=5000)


class ContactRequest(BaseModel):
    people: list[dict[str, Any]] = Field(max_length=20000)
    keyword: str = Field(default="", max_length=100)


class ApprovalRequest(BaseModel):
    rule: dict[str, Any]


class EmployeesRequest(BaseModel):
    employees: list[dict[str, Any]] = Field(max_length=20000)


class HrRequest(BaseModel):
    employees: list[dict[str, Any]] = Field(max_length=20000)
    departures: list[dict[str, Any]] = Field(default=[], max_length=50000)


class ArtifactReviewRequest(BaseModel):
    action: str
    reviewer: str = Field(min_length=1, max_length=100)
    note: str | None = Field(default=None, max_length=2000)


@router.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "available", "version": PLUGIN_VERSION}


@router.post("/permission/suggest")
async def permission_suggest(request: UsersRequest) -> dict[str, Any]:
    try:
        return suggest_permissions(request.users)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/contact/search")
async def contact_search(request: ContactRequest) -> dict[str, Any]:
    try:
        return search_contacts(request.people, request.keyword)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/approval/recommend")
async def approval_recommend(request: ApprovalRequest) -> dict[str, Any]:
    try:
        return recommend_approval_path(request.rule)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/anniversary/upcoming")
async def anniversary_upcoming(request: EmployeesRequest) -> dict[str, Any]:
    try:
        return manage_anniversaries(request.employees)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/hr/analyze")
async def hr_analyze(request: HrRequest) -> dict[str, Any]:
    try:
        return analyze_hr(request.employees, request.departures)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/artifacts/permission")
async def create_permission_artifact(request: UsersRequest) -> dict[str, Any]:
    try:
        payload = suggest_permissions(request.users)
        return _store().create_artifact("permission", "权限与组织建议", payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail=f"人力持久化依赖不可用：{exc}") from exc


@router.post("/artifacts/contact")
async def create_contact_artifact(request: ContactRequest) -> dict[str, Any]:
    try:
        payload = search_contacts(request.people, request.keyword)
        return _store().create_artifact("contact", "通讯录检索", payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail=f"人力持久化依赖不可用：{exc}") from exc


@router.post("/artifacts/approval")
async def create_approval_artifact(request: ApprovalRequest) -> dict[str, Any]:
    try:
        payload = recommend_approval_path(request.rule)
        return _store().create_artifact("approval", "审批路径建议", payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail=f"人力持久化依赖不可用：{exc}") from exc


@router.post("/artifacts/anniversary")
async def create_anniversary_artifact(request: EmployeesRequest) -> dict[str, Any]:
    try:
        payload = manage_anniversaries(request.employees)
        return _store().create_artifact("anniversary", "生日与司龄提醒", payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail=f"人力持久化依赖不可用：{exc}") from exc


@router.post("/artifacts/hr")
async def create_hr_artifact(request: HrRequest) -> dict[str, Any]:
    try:
        payload = analyze_hr(request.employees, request.departures)
        return _store().create_artifact("hr", "人力分析", payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail=f"人力持久化依赖不可用：{exc}") from exc


@router.get("/artifacts")
async def list_artifacts(kind: str | None = None, limit: int = 100) -> dict[str, Any]:
    try:
        return _store().list_artifacts(kind, limit)
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail=f"人力持久化依赖不可用：{exc}") from exc


@router.get("/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str) -> dict[str, Any]:
    try:
        return _store().get_artifact(artifact_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="人力工件不存在") from exc


@router.post("/artifacts/{artifact_id}/reviews")
async def review_artifact(artifact_id: str, request: ArtifactReviewRequest) -> dict[str, Any]:
    try:
        return _store().review_artifact(artifact_id, request.action, request.reviewer, request.note)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="人力工件不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/artifacts/{artifact_id}/export")
async def export_artifact(artifact_id: str) -> Response:
    try:
        content, media_type = _store().export_artifact(artifact_id)
        return Response(content=content, media_type=media_type,
                        headers={"Content-Disposition": 'attachment; filename="people-artifact.json"'})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="人力工件不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


def review_permission_suggestions(users: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare real users to a role permission matrix and persist a reviewable suggestion artifact."""
    payload = suggest_permissions(users)
    return _store().create_artifact("permission", "权限与组织建议", payload)


def review_contact_search(people: list[dict[str, Any]], keyword: str = "") -> dict[str, Any]:
    """Search a real contact directory and persist a reviewable contact artifact."""
    payload = search_contacts(people, keyword)
    return _store().create_artifact("contact", "通讯录检索", payload)


def review_approval_path(rule: dict[str, Any]) -> dict[str, Any]:
    """Recommend an approval chain for a real request and persist a reviewable artifact."""
    payload = recommend_approval_path(rule)
    return _store().create_artifact("approval", "审批路径建议", payload)


def review_anniversaries(employees: list[dict[str, Any]]) -> dict[str, Any]:
    """Find upcoming birthdays and hire anniversaries and persist a reviewable reminder artifact."""
    payload = manage_anniversaries(employees)
    return _store().create_artifact("anniversary", "生日与司龄提醒", payload)


def review_hr_analytics(employees: list[dict[str, Any]], departures: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Compute turnover, hiring cycle and headcount gap and persist a reviewable HR artifact."""
    payload = analyze_hr(employees, departures)
    return _store().create_artifact("hr", "人力分析", payload)


class PeopleStudioPlugin:
    def register(self, api: PluginApi) -> None:
        api.register_http_router(router, prefix="/zhiyun-people-studio", tags=["zhiyun-people-studio"])
        api.register_tool(
            tool_name="review_permission_suggestions",
            tool_func=review_permission_suggestions,
            description="对照角色权限矩阵分析真实用户的缺失/越权权限，按高危/关注/正常分级并生成可审阅权限建议工件。",
            icon="🔐",
            tool_type="internal",
        )
        api.register_tool(
            tool_name="review_contact_search",
            tool_func=review_contact_search,
            description="按姓名、部门、职位、电话、邮箱或技能检索真实通讯录并生成可审阅联系人工件。",
            icon="📇",
            tool_type="internal",
        )
        api.register_tool(
            tool_name="review_approval_path",
            tool_func=review_approval_path,
            description="按金额、部门与紧急程度为真实审批请求推荐审批链(主管/经理/财务/总经理)并生成可审阅工件。",
            icon="🚦",
            tool_type="internal",
        )
        api.register_tool(
            tool_name="review_anniversaries",
            tool_func=review_anniversaries,
            description="按真实员工生日与入职日期计算未来30天内纪念日，输出生日与司龄提醒并生成可审阅工件。",
            icon="🎂",
            tool_type="internal",
        )
        api.register_tool(
            tool_name="review_hr_analytics",
            tool_func=review_hr_analytics,
            description="按真实员工与离职记录计算离职率、招聘周期、部门分布与编制缺口并生成可审阅人力分析工件。",
            icon="🧮",
            tool_type="internal",
        )


plugin = PeopleStudioPlugin()
