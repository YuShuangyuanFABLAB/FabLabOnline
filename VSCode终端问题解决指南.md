# VSCode 终端问题解决指南

## 问题1：命令未找到

### 错误信息
```
claude : 无法将"claude"项识别为 cmdlet、函数、脚本文件或可运行程序的名称。
```

### 原因
Claude CLI 未安装或未添加到系统 PATH 中。

### 解决方案
```bash
npm install -g @anthropic-ai/claude-code
```

---

## 问题2：PowerShell 执行策略限制

### 错误信息
```
npm : 无法加载文件 C:\Program Files\nodejs\npm.ps1，因为在此系统上禁止运行脚本。
```

### 原因
Windows PowerShell 默认有安全策略，阻止运行脚本文件（.ps1）。

### 解决方案

#### 方案1：切换到 CMD（推荐）
1. 点击 VSCode 终端右上角的 **∨** 下拉箭头
2. 选择 **Command Prompt**
3. 在 CMD 中运行命令

#### 方案2：修改执行策略（一劳永逸）
以**管理员身份**打开 PowerShell，运行：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
输入 `Y` 确认。

#### 方案3：临时绕过（仅当前会话有效）
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

---

## CMD vs PowerShell 对比

| 特性 | Command Prompt (CMD) | PowerShell |
|------|---------------------|------------|
| 年代 | 1980年代（DOS时代） | 2006年推出 |
| 功能 | 基本命令行操作 | 强大的脚本和自动化 |
| 脚本 | .bat 批处理文件 | .ps1 脚本（面向对象） |
| 执行策略 | 无限制 | 默认有安全限制 |

### 建议
- 日常开发（npm、git、python 等）→ **CMD 或 Git Bash**
- Windows 系统管理/自动化 → **PowerShell**

---

## 常见问题

### Q1: npm 全局安装的包需要每次重新安装吗？
**不需要**。`npm install -g` 是全局安装，只安装一次，关机重启后依然存在。

### Q2: 安装 Claude CLI 后，用 CMD 还是 PowerShell 运行？
**两个都可以**。安装后的 `claude` 是可执行程序（.cmd 文件），不受 PowerShell 执行策略限制。

### Q3: 推荐的长期配置？
1. 修改 PowerShell 执行策略（运行一次即可）
2. 之后随意使用 CMD 或 PowerShell

---

## 快速参考命令

```bash
# 检查 Node.js 版本
node -v

# 检查 npm 版本
npm -v

# 安装 Claude CLI
npm install -g @anthropic-ai/claude-code

# 运行 Claude
claude

# 修改 PowerShell 执行策略（管理员）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
