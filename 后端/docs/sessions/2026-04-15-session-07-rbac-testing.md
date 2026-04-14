# Session 07 — RBAC 角色过滤验证 + 角色名对齐修复

> **日期**: 2026-04-15
> **状态**: 全部完成
> **分支**: master → origin/master

---

## 背景

Phase 4 全部代码修复完成后，需验证 Docker 部署环境下的 RBAC 权限系统是否按预期工作。重点验证非 super_admin 用户的角色过滤和 API 权限控制。

---

## 工作内容

### 1. 创建测试用户

通过 backend 容器直接执行 Python 脚本创建：

| 用户 | 密码 | 角色 | 用途 |
|------|------|------|------|
| `teacher1` | `teacher123` | teacher | 验证最低权限 |
| `orgadmin1` | `orgadmin123` | admin | 验证中间权限层 |

### 2. 后端 RBAC 验证

| 端点 | super_admin | admin (orgadmin1) | teacher (teacher1) |
|------|:-----------:|:------------------:|:-------------------:|
| POST /auth/heartbeat | OK | OK | OK |
| GET /users | 200 | **403** | **403** |
| GET /roles | 200 | **403** | **403** |
| GET /campuses | 200 | **403** | **403** |
| GET /apps | 200 | **403** | **403** |
| GET /audit/logs | 200 | **403** | **403** |
| GET /config | 200 | **403** | **403** |

后端 RBAC 权限校验工作正常。admin 和 teacher 角色未分配任何权限（种子数据仅给 super_admin 分配了 17 个权限）。

### 3. 前端菜单过滤 Bug

**问题**：`orgadmin1` 登录后只显示「数据看板」，预期应显示用户、校区、分析、审计。

**根因**：前端角色名与后端不一致。

| 前端期望 | 后端实际 |
|----------|---------|
| `org_admin` | `admin` |
| `campus_admin` | _(不存在)_ |

`auth.ts` 的 `highestRole` 优先级列表使用 `org_admin`，但后端返回的角色名是 `admin`，导致匹配失败。

### 4. 修复

| 文件 | 修改 |
|------|------|
| `admin-web/src/stores/auth.ts` | 优先级 `org_admin` → `admin`，移除 `campus_admin` |
| `admin-web/src/components/Layout.vue` | menuVisibility `org_admin` → `admin` |

修复后浏览器验证通过：
- `admin`（super_admin）：全部菜单可见
- `orgadmin1`（admin）：用户、校区、分析、审计可见（API 403 因为无权限）
- `teacher1`（teacher）：仅数据看板

### 5. URL 直接触达测试

`teacher1` 手动输入 `/users` 和 `/roles` URL：
- 页面加载但 API 返回 403
- 前端不阻止页面渲染，但数据为空 + Console 报错
- 后端安全防线有效

---

## 关键经验

### 前后端角色名必须统一
- 后端数据库的角色 ID 是真实标识符（`admin`、`teacher`）
- 前端菜单过滤逻辑直接比对角色名字符串
- 角色名不一致时不会报错，只是静默失败（所有菜单隐藏）

---

## 提交记录

| Commit | 说明 |
|--------|------|
| `72bf15a` | fix(frontend): 对齐角色名称 — org_admin→admin，修复菜单过滤失效 |
