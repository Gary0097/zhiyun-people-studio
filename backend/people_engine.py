# -*- coding: utf-8 -*-
"""Permission suggestion, contact directory, approval routing, anniversary and HR analytics."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Any


def _numeric(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(text[:19], fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def suggest_permissions(users: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare each user's role to a permission matrix and report gaps/excess."""
    if len(users) > 5000:
        raise ValueError("单次最多分析5000位用户")
    if not users:
        return {"users": [], "count": 0, "roles": {}, "method": "permission-suggest-v1"}

    role_matrix = {
        "管理员": ["数据读写", "用户管理", "财务审批", "系统配置"],
        "部门经理": ["数据读写", "本部门审批", "考勤管理", "报表查看"],
        "财务": ["财务审批", "财务查看", "报表查看"],
        "销售": ["客户查看", "订单查看", "业绩查看"],
        "采购": ["供应商查看", "订单查看", "采购审批"],
        "员工": ["个人考勤", "个人工资", "通讯录"],
    }
    ranked: list[dict[str, Any]] = []
    for user in users:
        name = str(user.get("name") or user.get("employee_name") or "未命名用户")
        role = str(user.get("role") or "员工")
        current = user.get("permissions") or []
        if isinstance(current, str):
            current = [item.strip() for item in current.split(",") if item.strip()]
        expected = role_matrix.get(role, ["个人考勤", "个人工资", "通讯录"])
        missing = [perm for perm in expected if perm not in current]
        excessive = [perm for perm in current if perm not in expected]
        rank = "高危" if ("系统配置" in excessive or "用户管理" in missing) else "关注" if (missing or excessive) else "正常"
        ranked.append({
            **user, "name": name, "role": role,
            "required": expected, "current": current,
            "missing": missing, "excessive": excessive, "rank": rank,
        })
    order = {"高危": 0, "关注": 1, "正常": 2}
    ranked.sort(key=lambda row: (order.get(row["rank"], 9), row["name"]))
    role_counts = defaultdict(int)
    for row in ranked:
        role_counts[row["role"]] += 1
    return {"users": ranked, "count": len(ranked), "roles": dict(role_counts), "method": "permission-suggest-v1"}


def search_contacts(people: list[dict[str, Any]], keyword: str = "") -> dict[str, Any]:
    """Search a real contact directory by name, department, title, phone or skills."""
    if len(people) > 20000:
        raise ValueError("单次最多检索20000位联系人")
    if not people:
        return {"contacts": [], "count": 0, "method": "contact-search-v1"}
    keyword = (keyword or "").strip().lower()
    contacts: list[dict[str, Any]] = []
    for person in people:
        name = str(person.get("name") or person.get("employee_name") or "")
        department = str(person.get("department") or "")
        title = str(person.get("title") or person.get("position") or "")
        phone = str(person.get("phone") or person.get("mobile") or "")
        email = str(person.get("email") or "")
        skills = person.get("skills") or []
        if isinstance(skills, str):
            skills = [item.strip() for item in skills.split(",") if item.strip()]
        haystack = " ".join([name, department, title, phone, email, " ".join(map(str, skills))]).lower()
        if keyword and keyword not in haystack:
            continue
        contacts.append({
            **person, "name": name, "department": department, "title": title,
            "phone": phone, "email": email, "skills": list(skills),
        })
    contacts.sort(key=lambda row: (row["department"], row["name"]))
    return {"contacts": contacts, "count": len(contacts), "keyword": keyword, "method": "contact-search-v1"}


def recommend_approval_path(rule: dict[str, Any]) -> dict[str, Any]:
    """Recommend the approval chain for a request based on amount, department and level."""
    amount = _numeric(rule.get("amount"), 0.0)
    department = str(rule.get("department") or "通用")
    requester = str(rule.get("requester") or "发起人")
    level = str(rule.get("level") or "普通")

    if amount > 100000:
        path = ["直属主管", "部门经理", "财务总监", "总经理"]
        reason = "金额超过10万元，需四级审批。"
        approver = "总经理"
    elif amount > 30000:
        path = ["直属主管", "部门经理", "财务负责人"]
        reason = "金额超过3万元，需三级审批。"
        approver = "财务负责人"
    elif amount > 5000:
        path = ["直属主管", "部门经理"]
        reason = "金额超过5000元，需两级审批。"
        approver = "部门经理"
    else:
        path = ["直属主管"]
        reason = "常规金额，直属主管审批即可。"
        approver = "直属主管"

    if level == "紧急" and len(path) > 1:
        path = [path[0], "部门经理"]
        reason = "紧急请求可压缩为两级快速通道。"
        approver = "部门经理"
    return {
        "requester": requester, "department": department, "amount": round(amount, 2),
        "level": level, "path": path, "final_approver": approver, "reason": reason,
        "method": "approval-path-v1",
    }


def manage_anniversaries(employees: list[dict[str, Any]], window_days: int = 30) -> dict[str, Any]:
    """Find upcoming birthdays and hire anniversaries within a rolling window."""
    if len(employees) > 20000:
        raise ValueError("单次最多处理20000位员工")
    if not employees:
        return {"birthdays": [], "anniversaries": [], "count": 0, "method": "anniversary-v1"}
    today = date.today()
    birthday_next: list[dict[str, Any]] = []
    anniversary_next: list[dict[str, Any]] = []
    for employee in employees:
        name = str(employee.get("name") or employee.get("employee_name") or "未命名员工")
        birth = _parse_date(employee.get("birthday"))
        hire = _parse_date(employee.get("hire_date") or employee.get("join_date"))

        def _next_days(anchor: date | None, today_ref: date = today) -> int | None:
            if anchor is None:
                return None
            try:
                next_anchor = anchor.replace(year=today_ref.year)
                if next_anchor < today_ref:
                    next_anchor = anchor.replace(year=today_ref.year + 1)
                return (next_anchor - today_ref).days
            except ValueError:
                return None

        if birth is not None:
            days = _next_days(birth)
            if days is not None and days <= window_days:
                birthday_next.append({**employee, "name": name, "days_away": days, "type": "生日"})
        if hire is not None:
            days = _next_days(hire)
            if days is not None and days <= window_days:
                years = today.year - hire.year
                anniversary_next.append({**employee, "name": name, "days_away": days, "years": years, "type": "司龄纪念"})
    birthday_next.sort(key=lambda row: row["days_away"])
    anniversary_next.sort(key=lambda row: row["days_away"])
    return {
        "birthdays": birthday_next, "anniversaries": anniversary_next,
        "count": len(birthday_next) + len(anniversary_next), "window_days": window_days,
        "method": "anniversary-v1",
    }


def analyze_hr(employees: list[dict[str, Any]], departures: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Compute turnover, hiring cycle, headcount gap and department distribution."""
    if len(employees) > 20000:
        raise ValueError("单次最多分析20000位员工")
    if not employees:
        return {"summary": {}, "departments": {}, "hiring_cycle": 0.0, "method": "hr-analytics-v1"}
    departures = departures or []
    today = date.today()
    department_count: dict[str, int] = defaultdict(int)
    for employee in employees:
        department_count[str(employee.get("department") or "未分配")] += 1

    headcount = len(employees)
    departures_in_year = 0
    for departure in departures:
        d = _parse_date(departure.get("departure_date") or departure.get("date"))
        if d is not None and (today - d).days <= 365:
            departures_in_year += 1
    turnover_rate = departures_in_year / headcount * 100.0 if headcount else 0.0

    today_dates = [_parse_date(employee.get("hire_date") or employee.get("join_date")) for employee in employees]
    recent_hires = [d for d in today_dates if d is not None and (today - d).days <= 90]
    hiring_cycle = sum((today - d).days for d in recent_hires) / len(recent_hires) if recent_hires else 0.0

    planned = _numeric(employees[0].get("planned_headcount"), headcount) if employees else headcount
    gap = int(planned - headcount)
    return {
        "summary": {
            "headcount": headcount,
            "departures_within_year": departures_in_year,
            "turnover_rate": round(turnover_rate, 1),
            "recent_hires": len(recent_hires),
            "planned_headcount": int(planned),
            "headcount_gap": gap,
        },
        "departments": {key: department_count[key] for key in sorted(department_count)},
        "hiring_cycle": round(hiring_cycle, 1),
        "method": "hr-analytics-v1",
    }
