(function () {
  var Q = window.QwenPaw;
  if (!Q || !Q.host || !Q.host.React || !Q.registerRoutes) return;
  var React = Q.host.React, antd = Q.host.antd, h = React.createElement;
  function request(path, body) {
    return Q.host.fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: body === undefined ? undefined : JSON.stringify(body) }).then(function (response) {
      return response.json().then(function (data) { if (!response.ok) throw new Error(data.detail || "操作失败"); return data; });
    });
  }
  function PeopleStudio() {
    var permTextState = React.useState(""), permText = permTextState[0], setPermText = permTextState[1];
    var permResultState = React.useState(null), permResult = permResultState[0], setPermResult = permResultState[1];
    var contactTextState = React.useState(""), contactText = contactTextState[0], setContactText = contactTextState[1];
    var keywordState = React.useState(""), keyword = keywordState[0], setKeyword = keywordState[1];
    var contactResultState = React.useState(null), contactResult = contactResultState[0], setContactResult = contactResultState[1];
    var approvalTextState = React.useState(""), approvalText = approvalTextState[0], setApprovalText = approvalTextState[1];
    var approvalResultState = React.useState(null), approvalResult = approvalResultState[0], setApprovalResult = approvalResultState[1];
    var careTextState = React.useState(""), careText = careTextState[0], setCareText = careTextState[1];
    var careResultState = React.useState(null), careResult = careResultState[0], setCareResult = careResultState[1];
    var hrTextState = React.useState(""), hrText = hrTextState[0], setHrText = hrTextState[1];
    var depTextState = React.useState(""), depText = depTextState[0], setDepText = depTextState[1];
    var hrResultState = React.useState(null), hrResult = hrResultState[0], setHrResult = hrResultState[1];
    var reviewerState = React.useState(""), reviewer = reviewerState[0], setReviewer = reviewerState[1];
    var recentState = React.useState([]), recent = recentState[0], setRecent = recentState[1];
    var loadingState = React.useState(false), loading = loadingState[0], setLoading = loadingState[1];
    var message = antd.App.useApp().message;
    function parseJson(text, label, object) {
      var parsed;
      try { parsed = JSON.parse(text); } catch (err) { message.error(label + "必须是" + (object ? "JSON对象" : "JSON数组")); return null; }
      if (object) {
        if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) { message.error(label + "必须是JSON对象"); return null; }
      } else if (!Array.isArray(parsed) || !parsed.length) { message.warning("请提供至少一条" + label); return null; }
      return parsed;
    }
    function loadRecent() {
      return Q.host.fetch("/zhiyun-people-studio/artifacts").then(function (response) { return response.json(); })
        .then(function (data) { setRecent(data.artifacts || []); }).catch(function () {});
    }
    function runPerm() {
      var users = parseJson(permText, "用户");
      if (!users) return;
      setLoading(true);
      request("/zhiyun-people-studio/artifacts/permission", { users: users }).then(function (data) { setPermResult(data); message.success("已生成权限建议工件，等待审阅"); loadRecent(); })
        .catch(function (e) { message.error(e.message); }).finally(function () { setLoading(false); });
    }
    function runContact() {
      var people = parseJson(contactText, "通讯录");
      if (!people) return;
      setLoading(true);
      request("/zhiyun-people-studio/artifacts/contact", { people: people, keyword: keyword }).then(function (data) { setContactResult(data); message.success("已生成通讯录工件，等待审阅"); loadRecent(); })
        .catch(function (e) { message.error(e.message); }).finally(function () { setLoading(false); });
    }
    function runApproval() {
      var rule = parseJson(approvalText, "审批规则", true);
      if (!rule) return;
      setLoading(true);
      request("/zhiyun-people-studio/artifacts/approval", { rule: rule }).then(function (data) { setApprovalResult(data); message.success("已生成审批路径建议，等待审阅"); loadRecent(); })
        .catch(function (e) { message.error(e.message); }).finally(function () { setLoading(false); });
    }
    function runCare() {
      var employees = parseJson(careText, "员工");
      if (!employees) return;
      setLoading(true);
      request("/zhiyun-people-studio/artifacts/anniversary", { employees: employees }).then(function (data) { setCareResult(data); message.success("已生成员工关怀提醒，等待审阅"); loadRecent(); })
        .catch(function (e) { message.error(e.message); }).finally(function () { setLoading(false); });
    }
    function runHr() {
      var employees = parseJson(hrText, "在职员工");
      if (!employees) return;
      var departures = depText.trim() ? parseJson(depText, "离职记录") : [];
      if (depText.trim() && !departures) return;
      setLoading(true);
      request("/zhiyun-people-studio/artifacts/hr", { employees: employees, departures: departures || [] }).then(function (data) { setHrResult(data); message.success("已生成人力分析工件，等待审阅"); loadRecent(); })
        .catch(function (e) { message.error(e.message); }).finally(function () { setLoading(false); });
    }
    function decide(kind, action) {
      if (!reviewer.trim()) { message.warning("请输入审阅人"); return; }
      var result = kind === "permission" ? permResult : kind === "contact" ? contactResult : kind === "approval" ? approvalResult : kind === "anniversary" ? careResult : hrResult;
      if (!result) { message.warning("请先生成工件"); return; }
      request("/zhiyun-people-studio/artifacts/" + result.id + "/reviews", { action: action, reviewer: reviewer }).then(function (data) {
        if (kind === "permission") setPermResult(data); else if (kind === "contact") setContactResult(data); else if (kind === "approval") setApprovalResult(data); else if (kind === "anniversary") setCareResult(data); else setHrResult(data);
        message.success(action === "accept" ? "工件已接受" : "工件已驳回"); loadRecent();
      }).catch(function (e) { message.error(e.message); });
    }
    function exportArtifact(result) {
      if (!result) return;
      window.open("/zhiyun-people-studio/artifacts/" + result.id + "/export", "_blank");
    }
    function reviewRow(result, kind) {
      return h("div", { style: { display: "flex", gap: 8, marginTop: 12 } },
        h(antd.Input, { value: reviewer, onChange: function (e) { setReviewer(e.target.value); }, placeholder: "审阅人", style: { width: 180 } }),
        h(antd.Button, { type: "primary", onClick: function () { decide(kind, "accept"); } }, "接受"),
        h(antd.Button, { danger: true, onClick: function () { decide(kind, "reject"); } }, "驳回"),
        h(antd.Button, { disabled: result.status !== "accepted", onClick: function () { exportArtifact(result); } }, "导出")
      );
    }
    function tagStatus(v) {
      return h(antd.Tag, { color: v === "accepted" ? "green" : v === "rejected" ? "red" : "orange" }, v);
    }
    var permExample = '[{"name":"张工","role":"管理员","permissions":["数据读写","用户管理"]},{"name":"李工","role":"销售","permissions":["客户查看","订单查看","系统配置"]}]';
    var contactExample = '[{"name":"王芳","department":"财务部","title":"财务主管","phone":"13800001111","email":"wangfang@zhiyun.cn","skills":"预算,报销审核"},{"name":"陈明","department":"研发部","title":"机械工程师","phone":"13800002222","email":"chenming@zhiyun.cn","skills":"电机设计,铸造工艺"}]';
    var approvalExample = '{"requester":"张工","department":"采购部","amount":120000,"level":"普通"}';
    var careExample = '[{"name":"刘华","birthday":"1990-08-30","hire_date":"2020-03-15","department":"生产部"},{"name":"赵敏","birthday":"1992-09-05","hire_date":"2019-08-20","department":"质量部"}]';
    var hrExample = '[{"name":"刘华","department":"生产部","hire_date":"2020-03-15","planned_headcount":60},{"name":"赵敏","department":"质量部","hire_date":"2019-08-20","planned_headcount":20}]';
    var depExample = '[{"name":"钱进","department":"生产部","departure_date":"2026-07-01"}]';
    var intents = [
      { key: "permission", label: "权限建议" },
      { key: "contact", label: "通讯录协作" },
      { key: "approval", label: "审批路径" },
      { key: "anniversary", label: "员工关怀" },
      { key: "hr", label: "人力分析" }
    ];
    var activeState = React.useState("permission"), active = activeState[0], setActive = activeState[1];
    React.useEffect(function () { loadRecent(); }, []);
    return h("div", { style: { padding: 28, height: "100%", overflow: "auto", background: "#f7f8fa" } }, h("div", { style: { maxWidth: 1080, margin: "0 auto" } },
      h("h2", null, "智能人力与协同中心"), h("p", { style: { color: "#667085" } }, "权限与组织建议、全员通讯录检索、审批路径推荐、员工关怀提醒与人力数据分析。"),
      h(antd.Tabs, { activeKey: active, onChange: setActive, items: intents.map(function (item) {
        return { key: item.key, label: item.label, children: item.key === "permission" ? (
          h("div", null,
            h(antd.Alert, { type: "info", showIcon: true, message: "权限与组织架构", description: "粘贴用户JSON数组，每项含 name、role、permissions 数组。" }),
            h(antd.Input.TextArea, { style: { marginTop: 12 }, value: permText, rows: 8, onChange: function (e) { setPermText(e.target.value); }, placeholder: permExample }),
            h(antd.Button, { type: "primary", loading: loading, style: { marginTop: 12 }, onClick: runPerm }, "分析并生成工件"),
            permResult ? h("div", null,
              h(antd.Card, { size: "small", title: "权限建议", style: { marginTop: 16 }, extra: tagStatus(permResult.status) },
                h(antd.Table, { size: "small", rowKey: "name", dataSource: permResult.payload.users, pagination: { pageSize: 8 }, columns: [
                  { title: "用户", dataIndex: "name" }, { title: "角色", dataIndex: "role" },
                  { title: "分级", dataIndex: "rank", render: function (v) { return h(antd.Tag, { color: v === "高危" ? "red" : v === "关注" ? "orange" : "green" }, v); } },
                  { title: "缺失", dataIndex: "missing", render: function (v) { return (v || []).join("、") || "无"; } },
                  { title: "越权", dataIndex: "excessive", render: function (v) { return (v || []).join("、") || "无"; } }
                ] }),
                reviewRow(permResult, "permission")
              )
            ) : null
          )
        ) : item.key === "contact" ? (
          h("div", null,
            h(antd.Alert, { type: "info", showIcon: true, message: "全员通讯录", description: "粘贴联系人JSON数组，每项含 name、department、title、phone、email、skills。" }),
            h(antd.Input.TextArea, { style: { marginTop: 12 }, value: contactText, rows: 8, onChange: function (e) { setContactText(e.target.value); }, placeholder: contactExample }),
            h("div", { style: { display: "flex", gap: 8, marginTop: 12 } },
              h(antd.Input, { value: keyword, onChange: function (e) { setKeyword(e.target.value); }, placeholder: "检索关键词（可留空）", style: { width: 220 } }),
              h(antd.Button, { type: "primary", loading: loading, onClick: runContact }, "检索并生成工件")
            ),
            contactResult ? h("div", null,
              h(antd.Card, { size: "small", title: "联系人（" + contactResult.payload.count + " 位）", style: { marginTop: 16 }, extra: tagStatus(contactResult.status) },
                h(antd.Table, { size: "small", rowKey: "name", dataSource: contactResult.payload.contacts, pagination: { pageSize: 8 }, columns: [
                  { title: "姓名", dataIndex: "name" }, { title: "部门", dataIndex: "department" },
                  { title: "职位", dataIndex: "title" }, { title: "电话", dataIndex: "phone" },
                  { title: "邮箱", dataIndex: "email" }, { title: "技能", dataIndex: "skills", render: function (v) { return (v || []).join("、"); } }
                ] }),
                reviewRow(contactResult, "contact")
              )
            ) : null
          )
        ) : item.key === "approval" ? (
          h("div", null,
            h(antd.Alert, { type: "info", showIcon: true, message: "审批路径推荐", description: "粘贴审批规则JSON对象，含 requester、department、amount、level(普通/紧急)。" }),
            h(antd.Input.TextArea, { style: { marginTop: 12 }, value: approvalText, rows: 5, onChange: function (e) { setApprovalText(e.target.value); }, placeholder: approvalExample }),
            h(antd.Button, { type: "primary", loading: loading, style: { marginTop: 12 }, onClick: runApproval }, "推荐并生成工件"),
            approvalResult ? h("div", null,
              h(antd.Card, { size: "small", title: "审批路径", style: { marginTop: 16 }, extra: tagStatus(approvalResult.status) },
                h("div", null,
                  h("p", null, "发起人：" + approvalResult.payload.requester + "，部门：" + approvalResult.payload.department + "，金额：" + approvalResult.payload.amount),
                  h(antd.Tag, { color: "blue" }, "最终审批：" + approvalResult.payload.final_approver),
                  h("div", { style: { marginTop: 8 } }, approvalResult.payload.path.map(function (step, index) {
                    return h(antd.Tag, { key: index, color: index === approvalResult.payload.path.length - 1 ? "green" : "default" }, (index + 1) + ". " + step);
                  })),
                  h("p", { style: { color: "#667085", marginTop: 8 } }, "依据：" + approvalResult.payload.reason)
                ),
                reviewRow(approvalResult, "approval")
              )
            ) : null
          )
        ) : item.key === "anniversary" ? (
          h("div", null,
            h(antd.Alert, { type: "info", showIcon: true, message: "员工关怀", description: "粘贴员工JSON数组，每项含 name、birthday、hire_date、department，引擎计算未来30天生日与司龄纪念日。" }),
            h(antd.Input.TextArea, { style: { marginTop: 12 }, value: careText, rows: 8, onChange: function (e) { setCareText(e.target.value); }, placeholder: careExample }),
            h(antd.Button, { type: "primary", loading: loading, style: { marginTop: 12 }, onClick: runCare }, "提醒并生成工件"),
            careResult ? h("div", null,
              h(antd.Card, { size: "small", title: "生日提醒（" + careResult.payload.birthdays.length + "）", style: { marginTop: 16 }, extra: tagStatus(careResult.status) },
                h(antd.Table, { size: "small", rowKey: "name", dataSource: careResult.payload.birthdays, pagination: false, columns: [
                  { title: "员工", dataIndex: "name" }, { title: "部门", dataIndex: "department" }, { title: "剩余天数", dataIndex: "days_away" }
                ] }),
                h("div", null, careResult.payload.birthdays.length ? null : h("p", { style: { color: "#667085" } }, "未来30天无生日。")),
                reviewRow(careResult, "anniversary")
              )
            ) : null
          )
        ) : (
          h("div", null,
            h(antd.Alert, { type: "info", showIcon: true, message: "人力数据分析", description: "粘贴在职员工JSON数组（含 department、hire_date、planned_headcount），可选离职记录数组。" }),
            h(antd.Input.TextArea, { style: { marginTop: 12 }, value: hrText, rows: 8, onChange: function (e) { setHrText(e.target.value); }, placeholder: hrExample }),
            h(antd.Input.TextArea, { style: { marginTop: 12 }, value: depText, rows: 4, onChange: function (e) { setDepText(e.target.value); }, placeholder: "离职记录(可选)：" + depExample }),
            h(antd.Button, { type: "primary", loading: loading, style: { marginTop: 12 }, onClick: runHr }, "分析并生成工件"),
            hrResult ? h("div", null,
              h(antd.Row, { gutter: 16, style: { marginTop: 16 } },
                ["在职人数", "离职率%", "今年新聘", "编制缺口"].map(function (label, index) {
                  var value = [hrResult.payload.summary.headcount, hrResult.payload.summary.turnover_rate, hrResult.payload.summary.recent_hires, hrResult.payload.summary.headcount_gap][index];
                  return h(antd.Col, { span: 6, key: label }, h(antd.Card, { size: "small" }, h(antd.Statistic, { title: label, value: value, precision: index === 1 ? 1 : 0 })));
                })
              ),
              h(antd.Card, { size: "small", title: "部门分布", style: { marginTop: 12 } },
                h(antd.Table, { size: "small", rowKey: "department", dataSource: Object.keys(hrResult.payload.departments).map(function (dep) { return { department: dep, count: hrResult.payload.departments[dep] }; }), pagination: false, columns: [
                  { title: "部门", dataIndex: "department" }, { title: "人数", dataIndex: "count" }
                ] })
              ),
              h(antd.Card, { size: "small", title: "招聘周期", style: { marginTop: 12 } }, h("p", null, "平均入职天数：" + hrResult.payload.hiring_cycle + " 天")),
              reviewRow(hrResult, "hr")
            ) : null
          )
        )};
      }) }
    )));
  }
  Q.registerRoutes("zhiyun-people-studio", [{ path: "/apps/zhiyun-people-studio", component: PeopleStudio, label: "智能人力与协同", icon: "🧑‍🤝‍🧑", priority: 79 }]);
})();
