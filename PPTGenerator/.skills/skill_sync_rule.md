# Skill同步规则

## 规则

**所有新生成的skill必须同步到全局目录**，确保在任何项目中都可以访问。

## 全局目录位置

```
Windows: C:\Users\<用户名>\.skills\
Linux/Mac: ~/.skills/
```

## 同步流程

当创建或更新skill时，必须执行以下步骤：

### 1. 创建skill文件
在项目的 `.skills/` 目录创建skill文件

### 2. 更新skill_index.json
在项目的 `.skills/skill_index.json` 中添加索引条目

### 3. 同步到全局目录
```bash
# 复制skill文件
cp .skills/<skill_name>.md ~/.skills/

# 复制更新后的索引
cp .skills/skill_index.json ~/.skills/
```

### 4. Git提交并推送
```bash
cd ~/.skills
git add .
git commit -m "feat: 更新skill描述"
git push
```

### 5. 验证同步
```bash
# 测试全局skill是否可用
python .agent/test_runner.py skill <关键词>
```

---

## Git Push 故障排除

### 常见错误信息

```
fatal: unable to access '...': Connection was reset
fatal: unable to access '...': Failed to connect to github.com port 443 after 21xxx ms
Recv failure: Connection was reset
```

### 诊断方法

**使用详细日志模式**：
```bash
GIT_CURL_VERBOSE=1 git push 2>&1 | head -30
```

这会显示：
- DNS解析
- TCP连接状态
- TLS握手过程
- 证书验证

### 为什么有时失败有时成功

| 情况 | 原因 | 解决方案 |
|------|------|----------|
| "Connection was reset" | 网络临时中断 | 重试 |
| "Failed to connect after XXms" | 超时时间不够 | 增加超时或重试 |
| 成功但显示"Everything up-to-date" | 之前的push可能部分成功 | 用git status确认 |

### 重试策略

**方案1：简单重试**
```bash
# 直接重试，给足够时间
git push
```

**方案2：诊断后重试**
```bash
# 先诊断
GIT_CURL_VERBOSE=1 git push 2>&1 | head -30

# 如果看到TLS握手成功，再次尝试
git push
```

**方案3：检查实际状态**
```bash
# 如果push后显示"Everything up-to-date"
# 检查本地是否与远程同步
git status
git log --oneline -3
```

### 重要发现

**"Everything up-to-date"的含义**：

当git push失败后重试，如果显示"Everything up-to-date"，通常意味着：
1. 之前的push实际上已经成功（尽管显示了错误）
2. 或者本地commit已经存在于远程

**验证方法**：
```bash
git status
# 如果显示 "Your branch is up to date with 'origin/main'"
# 说明同步成功
```

### 案例：2026-02-20 push经历

```
第1次: Connection was reset ❌
第2次: Failed to connect after 21101ms ❌
第3次: Failed to connect after 21125ms ❌
第4次: GIT_CURL_VERBOSE=1，看到TLS握手成功但后续中断
第5次: 成功，显示 "Everything up-to-date" ✓
```

**结论**：
- 网络不稳定时，多试几次
- 详细日志可以帮助判断是网络问题还是配置问题
- 不要因为错误信息就认为完全失败

---

## skill_index.json 结构

```json
{
  "version": "1.x",
  "updated": "YYYY-MM-DD",
  "skills": {
    "skill_id": {
      "file": "skill_file.md",
      "keywords": ["关键词1", "关键词2"],
      "problem": "解决的问题",
      "solution": "解决方案"
    }
  },
  "quick_reference": {
    "关键词": "skill_id"
  }
}
```

## 检查清单

- [ ] skill文件已创建
- [ ] skill_index.json已更新
- [ ] 已复制到全局目录
- [ ] git commit完成
- [ ] git push成功（或重试后成功）
- [ ] 全局查找测试通过

## 重要说明

- **优先级**: 全局目录优先于项目目录
- **冲突处理**: 全局和项目都有时，使用全局版本
- **更新时**: 必须同时更新两个位置的文件
- **Push失败**: 网络不稳定时重试，用GIT_CURL_VERBOSE诊断
