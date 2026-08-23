import unittest
from datetime import date, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from people_engine import (
    analyze_hr,
    manage_anniversaries,
    recommend_approval_path,
    search_contacts,
    suggest_permissions,
)


def _safe_target(days: int = 10) -> date:
    """Return a target date `days` out that is not Feb 29 (not valid in non-leap anchor years)."""
    target = date.today() + timedelta(days=days)
    while target.month == 2 and target.day == 29:
        days += 1
        target = date.today() + timedelta(days=days)
    return target


class PeopleEngineTests(unittest.TestCase):
    def test_permission_normal_and_high_risk_on_system_config(self):
        users = [
            {"name": "张工", "role": "管理员", "permissions": ["数据读写", "用户管理", "财务审批", "系统配置"]},
            {"name": "李工", "role": "员工", "permissions": ["个人考勤", "系统配置"]},
        ]
        result = suggest_permissions(users)
        self.assertEqual(result["count"], 2)
        ranks = {item["name"]: item["rank"] for item in result["users"]}
        self.assertEqual(ranks["张工"], "正常")
        self.assertEqual(ranks["李工"], "高危")  # 系统配置越权
        li = [item for item in result["users"] if item["name"] == "李工"][0]
        self.assertIn("系统配置", li["excessive"])

    def test_permission_missing_user_management_is_high_risk(self):
        users = [
            {"name": "王工", "role": "管理员", "permissions": ["数据读写", "财务审批", "系统配置"]},
        ]
        result = suggest_permissions(users)
        self.assertEqual(result["users"][0]["rank"], "高危")
        self.assertIn("用户管理", result["users"][0]["missing"])

    def test_contact_search_filters_by_keyword(self):
        people = [
            {"name": "王芳", "department": "财务部", "title": "财务主管", "phone": "13800001111", "email": "wangfang@zhiyun.cn", "skills": ["预算", "报销审核"]},
            {"name": "陈明", "department": "研发部", "title": "机械工程师", "phone": "13800002222", "email": "chenming@zhiyun.cn", "skills": ["电机设计", "铸造工艺"]},
        ]
        result = search_contacts(people, "电机")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["contacts"][0]["name"], "陈明")

    def test_contact_search_skill_string_and_empty_keyword(self):
        people = [{"name": "zhang", "department": "研发部", "title": "工程师", "phone": "1", "email": "z@z.cn", "skills": "电机设计,铸造"}]
        self.assertEqual(search_contacts(people, "铸造")["count"], 1)
        self.assertEqual(search_contacts(people)["count"], 1)

    def test_approval_path_tiers_by_amount(self):
        self.assertEqual(len(recommend_approval_path({"amount": 120000})["path"]), 4)
        self.assertEqual(len(recommend_approval_path({"amount": 40000})["path"]), 3)
        self.assertEqual(len(recommend_approval_path({"amount": 20000})["path"]), 2)
        self.assertEqual(len(recommend_approval_path({"amount": 1000})["path"]), 1)

    def test_approval_path_urgent_compresses(self):
        result = recommend_approval_path({"amount": 40000, "level": "紧急", "department": "采购部", "requester": "张工"})
        self.assertEqual(len(result["path"]), 2)
        self.assertEqual(result["final_approver"], "部门经理")

    def test_anniversary_upcoming_within_window(self):
        target = _safe_target(10)
        hire_year = date.today().year - 11
        employees = [
            {"name": "刘华", "birthday": str(target.replace(year=1990)), "hire_date": str(target.replace(year=hire_year)), "department": "生产部"},
        ]
        result = manage_anniversaries(employees, window_days=30)
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["birthdays"][0]["name"], "刘华")
        self.assertEqual(result["birthdays"][0]["days_away"], 10)
        self.assertEqual(result["anniversaries"][0]["years"], 11)

    def test_hr_turnover_hiring_cycle_and_gap(self):
        today = date.today()
        employees = [
            {"name": "刘华", "department": "生产部", "hire_date": str(today - timedelta(days=60)), "planned_headcount": 60},
            {"name": "赵敏", "department": "质量部", "hire_date": str(today - timedelta(days=30)), "planned_headcount": 20},
        ]
        departures = [{"name": "钱进", "department": "生产部", "departure_date": str(today - timedelta(days=10))}]
        result = analyze_hr(employees, departures)
        self.assertEqual(result["summary"]["headcount"], 2)
        self.assertGreater(result["summary"]["turnover_rate"], 0)
        self.assertEqual(result["summary"]["recent_hires"], 2)
        self.assertEqual(result["summary"]["planned_headcount"], 60)
        self.assertEqual(result["summary"]["headcount_gap"], 58)


if __name__ == "__main__":
    unittest.main()
