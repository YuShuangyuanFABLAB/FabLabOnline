# 课程反馈 PPT 生成器 - 项目记忆

## 项目信息

**项目名称**: 课程反馈 PPT 自动生成器
**GitHub 仓库**: https://github.com/YuShuangyuanFABLAB/FeedbackPPTGenerator
**工作目录**: D:\claude code

---

## 项目规则

### 自动推送规则
- 每次功能升级或问题修复后
- 用户确认测试无问题
- **自动执行** `git push` 到 GitHub 仓库

### Git 提交规范
- `feat:` 新功能
- `fix:` 问题修复
- `docs:` 文档更新
- `style:` 代码格式
- `refactor:` 重构

---

## 技术栈

- Python 3.x
- PyQt5 (GUI)
- python-pptx (PPT 生成)

---

## 核心模块

| 模块 | 路径 | 功能 |
|------|------|------|
| 主窗口 | `src/ui/main_window.py` | 应用主界面 |
| 配置管理 | `src/core/config_manager.py` | 设置和配置 |
| PPT 生成 | `src/core/ppt_generator.py` | 生成 PPT 文件 |
| 内容填充 | `src/core/content_filler.py` | 填充 PPT 内容 |

---

## 已实现功能

- [x] 班级与学员管理
- [x] 学员标签栏（多学员数据缓存）
- [x] 课程系列选择
- [x] 富文本知识编辑器（重点/难点标记）
- [x] 12项课堂评价系统
- [x] 图片上传与管理
- [x] PPT 自动生成
- [x] 批量生成（多学员PPT，含图片展示页、系列名称、后处理）
- [x] 班级时间自动填充（根据班级名称"星期X HH:MM"自动填写上课日期和时间）

---

*最后更新: 2026-02-24*
