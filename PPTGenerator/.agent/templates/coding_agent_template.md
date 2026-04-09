# 编码Agent通用模板

## 角色定义
你是项目的编码Agent。你的任务是进行增量开发，每次只完成一个功能，并在会话结束时留下清晰的进度记录。

## 项目配置
请先读取项目配置文件：`.agent/templates/project_config.json`

## 关键原则

### ⚠️ 绝对禁止的行为
1. **不要一次性完成多个功能** - 每次只做一个功能
2. **不要删除或修改feature_list.json中的功能描述** - 只能修改`passes`字段
3. **不要在验证通过前标记功能为完成**
4. **不要留下未完成的代码** - 确保每次提交的代码都是可运行状态
5. **不要只依赖代码层测试** - 必须进行目标环境验证

### ✅ 必须执行的行为
1. **会话开始时** - 阅读进度文件和Git日志
2. **开发前** - 确认当前代码可以正常运行
3. **开发中** - 遵循TDD原则
4. **开发后** - 三层验证（代码→目标环境→用户视角）
5. **会话结束时** - 提交Git并更新进度文件

## 每次会话的标准流程

### 第一步：了解当前状态
```bash
pwd                                    # 确认工作目录
git log --oneline -10                  # 查看Git日志
git status                             # 查看当前状态
cat .agent/agent-progress.txt          # 阅读进度文件
cat .agent/feature_list.json           # 阅读功能列表
```

### 第二步：选择要开发的功能
从feature_list.json中选择：
1. 优先级最高的
2. `passes`为`false`的
3. `blocked_by`中的依赖都已完成的

### 第三步：验证当前环境
根据`project_config.json`中的`commands.test`运行测试：
```bash
python -m pytest tests/ -v
```

### 第四步：开发功能
按照feature_list.json中的steps逐一实现。

### 第五步：三层验证（关键！）

#### 层级1：代码层测试
```bash
python -m pytest tests/ -v
```

#### 层级2：目标环境验证
根据`project_config.json`中的`target_environment`配置进行验证：

| 项目类型 | 验证方法 |
|----------|----------|
| ppt_generator | PowerPoint COM API |
| excel_generator | Excel COM API |
| web_app | 浏览器自动化 |
| gui_app | 启动应用手动验证 |

**示例代码**：
```python
# 读取project_config.json中的verification_api并执行
# 确保生成的文件在目标软件中显示正确
```

#### 层级3：用户视角验证
- 打开生成的文件在目标软件中检查
- 确认效果符合预期

### 第六步：更新功能状态
**只有在三层验证全部通过后**，更新feature_list.json：
```json
{
  "id": "F001",
  "passes": true
}
```

### 第七步：提交代码
```bash
git status
git diff
git add .
git commit -m "feat(F001): 功能描述"
```

### 第八步：更新进度文件
在`.agent/agent-progress.txt`中添加记录。

## 故障排除

### 如果"测试通过但实际不正确"
1. 用目标环境API验证实际效果
2. 查阅`.skills/`目录的相关skill
3. 对比模板找差异
4. 解决后创建新skill

### 使用Skills系统
遇到问题时查阅`.skills/`目录：
```
.skills/
├── ppt_color_verification.md
└── ...
```

## 完成标准
每次会话结束时确认：
- [ ] 选定的功能已完成
- [ ] 三层验证全部通过
- [ ] feature_list.json已更新
- [ ] Git提交已完成
- [ ] agent-progress.txt已更新
- [ ] 代码处于可运行状态
