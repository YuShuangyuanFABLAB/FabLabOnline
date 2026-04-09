# 桌面扩展（Desktop Extensions）

> 来源：https://www.anthropic.com/engineering/desktop-extensions
> 发布日期：2025-06-26

---

## 一、桌面扩展概述

### 1.1 什么是桌面扩展

桌面扩展是Claude Desktop的应用扩展机制，允许开发者创建自定义集成，增强Claude与本地系统的交互能力。

### 1.2 核心能力

| 能力 | 说明 |
|------|------|
| **文件访问** | 读写本地文件系统 |
| **进程控制** | 启动和管理本地进程 |
| **系统集成** | 与操作系统功能交互 |
| **自定义UI** | 扩展界面元素 |

### 1.3 架构设计

```
桌面扩展架构：
├── Extension Host
│   ├── 生命周期管理
│   ├── 权限控制
│   └── 消息路由
├── Extension Runtime
│   ├── JavaScript引擎
│   ├── API绑定
│   └── 沙箱隔离
└── Extension APIs
    ├── 文件系统API
    ├── 进程API
    ├── 网络API
    └── UI API
```

---

## 二、扩展开发基础

### 2.1 扩展清单

每个扩展需要一个manifest.json文件：

```json
{
  "name": "my-extension",
  "version": "1.0.0",
  "description": "我的扩展",
  "permissions": ["filesystem", "process"],
  "main": "index.js",
  "contributes": {
    "commands": [...],
    "menus": [...]
  }
}
```

### 2.2 权限模型

扩展需要在manifest中声明所需权限：

- `filesystem`: 文件系统访问
- `process`: 进程管理
- `network`: 网络访问
- `clipboard`: 剪贴板访问

---

## 三、实战案例

### 案例1：文件管理扩展

**场景**：创建一个文件管理扩展

**解决方案**：

```javascript
// manifest.json
{
  "name": "file-manager",
  "version": "1.0.0",
  "permissions": ["filesystem"],
  "main": "index.js"
}

// index.js
class FileManagerExtension {
    constructor(api) {
        this.api = api;
        this.registerCommands();
    }

    registerCommands() {
        // 注册命令
        this.api.registerCommand('fileManager.listFiles', async (dirPath) => {
            return await this.listFiles(dirPath);
        });

        this.api.registerCommand('fileManager.readFile', async (filePath) => {
            return await this.readFile(filePath);
        });

        this.api.registerCommand('fileManager.writeFile', async (filePath, content) => {
            return await this.writeFile(filePath, content);
        });

        this.api.registerCommand('fileManager.search', async (pattern, dirPath) => {
            return await this.searchFiles(pattern, dirPath);
        });
    }

    async listFiles(dirPath) {
        try {
            const entries = await this.api.fs.readdir(dirPath);
            const items = [];

            for (const entry of entries) {
                const stat = await this.api.fs.stat(`${dirPath}/${entry}`);
                items.push({
                    name: entry,
                    type: stat.isDirectory() ? 'directory' : 'file',
                    size: stat.size,
                    modified: stat.mtime
                });
            }

            return { success: true, items };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async readFile(filePath) {
        try {
            const content = await this.api.fs.readFile(filePath, 'utf-8');
            return { success: true, content };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async writeFile(filePath, content) {
        try {
            await this.api.fs.writeFile(filePath, content, 'utf-8');
            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async searchFiles(pattern, dirPath) {
        const results = [];
        const regex = new RegExp(pattern, 'i');

        async function search(dir, api) {
            const entries = await api.fs.readdir(dir);

            for (const entry of entries) {
                const fullPath = `${dir}/${entry}`;
                const stat = await api.fs.stat(fullPath);

                if (stat.isDirectory()) {
                    await search(fullPath, api);
                } else if (regex.test(entry)) {
                    results.push({
                        path: fullPath,
                        name: entry,
                        size: stat.size
                    });
                }
            }
        }

        try {
            await search(dirPath, this.api);
            return { success: true, results };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    activate() {
        console.log('File Manager Extension activated');
    }

    deactivate() {
        console.log('File Manager Extension deactivated');
    }
}

module.exports = FileManagerExtension;
```

**关键设计点**：
1. 权限声明
2. 错误处理
3. 异步操作
4. 递归搜索

---

### 案例2：代码运行扩展

**场景**：创建一个代码执行扩展

**解决方案**：

```javascript
// manifest.json
{
  "name": "code-runner",
  "version": "1.0.0",
  "permissions": ["filesystem", "process"],
  "main": "index.js",
  "configuration": {
    "timeout": 30000,
    "maxOutputSize": 100000
  }
}

// index.js
class CodeRunnerExtension {
    constructor(api, config) {
        this.api = api;
        this.config = config;
        this.runningProcesses = new Map();
    }

    async runCode(code, language) {
        const runners = {
            python: this.runPython.bind(this),
            javascript: this.runJavaScript.bind(this),
            bash: this.runBash.bind(this)
        };

        const runner = runners[language];
        if (!runner) {
            return { success: false, error: `不支持的语言: ${language}` };
        }

        return await runner(code);
    }

    async runPython(code) {
        const tempFile = await this.createTempFile(code, '.py');

        try {
            const result = await this.executeProcess('python', [tempFile]);
            return result;
        } finally {
            await this.api.fs.unlink(tempFile);
        }
    }

    async runJavaScript(code) {
        const tempFile = await this.createTempFile(code, '.js');

        try {
            const result = await this.executeProcess('node', [tempFile]);
            return result;
        } finally {
            await this.api.fs.unlink(tempFile);
        }
    }

    async runBash(code) {
        return await this.executeProcess('bash', ['-c', code]);
    }

    async createTempFile(content, extension) {
        const tempDir = this.api.paths.temp;
        const fileName = `code_${Date.now()}${extension}`;
        const filePath = `${tempDir}/${fileName}`;

        await this.api.fs.writeFile(filePath, content);
        return filePath;
    }

    async executeProcess(command, args) {
        return new Promise((resolve) => {
            const process = this.api.process.spawn(command, args);
            const processId = process.pid;

            let stdout = '';
            let stderr = '';
            let timeout;

            // 设置超时
            timeout = setTimeout(() => {
                process.kill();
                resolve({
                    success: false,
                    error: '执行超时',
                    stdout,
                    stderr
                });
            }, this.config.timeout);

            process.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            process.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            process.on('close', (code) => {
                clearTimeout(timeout);
                this.runningProcesses.delete(processId);

                resolve({
                    success: code === 0,
                    exitCode: code,
                    stdout: stdout.slice(0, this.config.maxOutputSize),
                    stderr
                });
            });

            this.runningProcesses.set(processId, process);
        });
    }

    stopProcess(processId) {
        const process = this.runningProcesses.get(processId);
        if (process) {
            process.kill();
            return { success: true };
        }
        return { success: false, error: '进程不存在' };
    }

    activate() {
        this.api.registerCommand('codeRunner.run', this.runCode.bind(this));
        this.api.registerCommand('codeRunner.stop', this.stopProcess.bind(this));
    }

    deactivate() {
        // 停止所有运行中的进程
        for (const [id, process] of this.runningProcesses) {
            process.kill();
        }
        this.runningProcesses.clear();
    }
}

module.exports = CodeRunnerExtension;
```

---

### 案例3：Git集成扩展

**场景**：创建Git版本控制集成扩展

**解决方案**：

```javascript
class GitExtension {
    constructor(api) {
        this.api = api;
    }

    async executeGit(args, cwd) {
        return new Promise((resolve) => {
            const process = this.api.process.spawn('git', args, { cwd });

            let stdout = '';
            let stderr = '';

            process.stdout.on('data', (data) => stdout += data);
            process.stderr.on('data', (data) => stderr += data);

            process.on('close', (code) => {
                resolve({
                    success: code === 0,
                    output: stdout,
                    error: stderr
                });
            });
        });
    }

    async status(repoPath) {
        return await this.executeGit(['status', '--porcelain'], repoPath);
    }

    async log(repoPath, options = {}) {
        const args = ['log', '--oneline'];
        if (options.limit) {
            args.push(`-${options.limit}`);
        }
        return await this.executeGit(args, repoPath);
    }

    async diff(repoPath, options = {}) {
        const args = ['diff'];
        if (options.cached) {
            args.push('--cached');
        }
        return await this.executeGit(args, repoPath);
    }

    async commit(repoPath, message) {
        return await this.executeGit(['commit', '-m', message], repoPath);
    }

    async branch(repoPath, action, branchName) {
        const actions = {
            list: ['branch'],
            create: ['branch', branchName],
            delete: ['branch', '-d', branchName],
            switch: ['checkout', branchName]
        };

        return await this.executeGit(actions[action], repoPath);
    }

    activate() {
        this.api.registerCommand('git.status', this.status.bind(this));
        this.api.registerCommand('git.log', this.log.bind(this));
        this.api.registerCommand('git.diff', this.diff.bind(this));
        this.api.registerCommand('git.commit', this.commit.bind(this));
        this.api.registerCommand('git.branch', this.branch.bind(this));
    }
}

module.exports = GitExtension;
```

---

### 案例4：终端集成扩展

**场景**：创建终端集成扩展

**解决方案**：

```javascript
class TerminalExtension {
    constructor(api) {
        this.api = api;
        this.sessions = new Map();
    }

    async createSession(options = {}) {
        const sessionId = `term_${Date.now()}`;
        const shell = options.shell || process.env.SHELL || 'bash';

        const termProcess = this.api.process.spawn(shell, [], {
            cwd: options.cwd || process.cwd(),
            env: process.env,
            pty: true  // 使用伪终端
        });

        const session = {
            id: sessionId,
            process: termProcess,
            history: [],
            outputCallbacks: []
        };

        termProcess.on('data', (data) => {
            const output = data.toString();
            session.history.push({ type: 'output', data: output, timestamp: Date.now() });

            // 通知所有监听器
            session.outputCallbacks.forEach(callback => callback(output));
        });

        this.sessions.set(sessionId, session);

        return { sessionId };
    }

    async sendInput(sessionId, input) {
        const session = this.sessions.get(sessionId);
        if (!session) {
            return { success: false, error: '会话不存在' };
        }

        session.process.stdin.write(input);
        session.history.push({ type: 'input', data: input, timestamp: Date.now() });

        return { success: true };
    }

    async resize(sessionId, cols, rows) {
        const session = this.sessions.get(sessionId);
        if (!session) {
            return { success: false, error: '会话不存在' };
        }

        session.process.resize(cols, rows);
        return { success: true };
    }

    onOutput(sessionId, callback) {
        const session = this.sessions.get(sessionId);
        if (!session) {
            return () => {};
        }

        session.outputCallbacks.push(callback);

        // 返回取消订阅函数
        return () => {
            const index = session.outputCallbacks.indexOf(callback);
            if (index > -1) {
                session.outputCallbacks.splice(index, 1);
            }
        };
    }

    async closeSession(sessionId) {
        const session = this.sessions.get(sessionId);
        if (!session) {
            return { success: false, error: '会话不存在' };
        }

        session.process.kill();
        this.sessions.delete(sessionId);

        return { success: true };
    }

    activate() {
        this.api.registerCommand('terminal.create', this.createSession.bind(this));
        this.api.registerCommand('terminal.input', this.sendInput.bind(this));
        this.api.registerCommand('terminal.resize', this.resize.bind(this));
        this.api.registerCommand('terminal.close', this.closeSession.bind(this));
        this.api.registerEvent('terminal.onOutput', this.onOutput.bind(this));
    }

    deactivate() {
        for (const [id, session] of this.sessions) {
            session.process.kill();
        }
        this.sessions.clear();
    }
}

module.exports = TerminalExtension;
```

---

### 案例5：剪贴板扩展

**场景**：创建剪贴板管理扩展

**解决方案**：

```javascript
class ClipboardExtension {
    constructor(api) {
        this.api = api;
        this.history = [];
        this.maxHistory = 100;
        this.watchInterval = null;
    }

    async read() {
        const content = await this.api.clipboard.readText();
        return { success: true, content };
    }

    async write(content) {
        await this.api.clipboard.writeText(content);
        this.addToHistory(content);
        return { success: true };
    }

    addToHistory(content) {
        // 避免重复
        const existing = this.history.findIndex(h => h.content === content);
        if (existing > -1) {
            this.history.splice(existing, 1);
        }

        this.history.unshift({
            content,
            timestamp: Date.now()
        });

        // 限制历史长度
        if (this.history.length > this.maxHistory) {
            this.history = this.history.slice(0, this.maxHistory);
        }
    }

    getHistory(limit = 20) {
        return {
            success: true,
            items: this.history.slice(0, limit)
        };
    }

    clearHistory() {
        this.history = [];
        return { success: true };
    }

    startWatching(callback) {
        let lastContent = '';

        this.watchInterval = setInterval(async () => {
            try {
                const content = await this.api.clipboard.readText();
                if (content !== lastContent) {
                    lastContent = content;
                    this.addToHistory(content);
                    if (callback) {
                        callback(content);
                    }
                }
            } catch (error) {
                // 忽略读取错误
            }
        }, 1000);

        return { success: true };
    }

    stopWatching() {
        if (this.watchInterval) {
            clearInterval(this.watchInterval);
            this.watchInterval = null;
        }
        return { success: true };
    }

    async readImage() {
        const image = await this.api.clipboard.readImage();
        if (image) {
            return {
                success: true,
                image: {
                    width: image.width,
                    height: image.height,
                    dataUrl: image.toDataURL()
                }
            };
        }
        return { success: false, error: '剪贴板中没有图片' };
    }

    activate() {
        this.api.registerCommand('clipboard.read', this.read.bind(this));
        this.api.registerCommand('clipboard.write', this.write.bind(this));
        this.api.registerCommand('clipboard.getHistory', this.getHistory.bind(this));
        this.api.registerCommand('clipboard.clearHistory', this.clearHistory.bind(this));
        this.api.registerCommand('clipboard.startWatching', this.startWatching.bind(this));
        this.api.registerCommand('clipboard.stopWatching', this.stopWatching.bind(this));
        this.api.registerCommand('clipboard.readImage', this.readImage.bind(this));
    }

    deactivate() {
        this.stopWatching();
    }
}

module.exports = ClipboardExtension;
```

---

## 四、最佳实践

### 4.1 扩展开发原则

| 原则 | 说明 |
|------|------|
| **最小权限** | 只请求必要的权限 |
| **错误处理** | 优雅处理所有错误 |
| **资源清理** | deactivate时清理资源 |
| **文档完善** | 提供清晰的使用说明 |

### 4.2 安全考虑

- 验证所有输入
- 限制文件访问范围
- 控制进程执行权限
- 过滤敏感信息

### 4.3 性能优化

- 异步操作
- 缓存机制
- 资源限制
- 延迟加载

---

## 五、总结

桌面扩展的核心价值：

1. **系统深度集成**：充分利用本地能力
2. **自定义扩展**：满足特定需求
3. **安全可控**：权限明确、沙箱隔离
4. **生态丰富**：可共享和复用
