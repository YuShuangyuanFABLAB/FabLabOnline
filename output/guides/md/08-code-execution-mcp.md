# 代码执行与MCP（Code Execution with MCP）

> 来源：https://www.anthropic.com/engineering/model-context-protocol
> 发布日期：2025-11-04

---

## 一、MCP协议概述

### 1.1 什么是MCP

Model Context Protocol (MCP) 是一个开放标准，用于连接AI助手与外部系统。它提供了一种标准化的方式让模型与工具、数据源进行交互。

### 1.2 核心优势

| 优势 | 说明 |
|------|------|
| **标准化** | 统一的接口规范 |
| **可扩展** | 轻松添加新工具 |
| **安全** | 受控的访问机制 |
| **解耦** | 模型与工具独立演进 |

### 1.3 架构组件

```
MCP架构：
├── MCP Server（服务端）
│   ├── 工具定义
│   ├── 资源暴露
│   └── 提示模板
├── MCP Client（客户端）
│   ├── 连接管理
│   ├── 能力发现
│   └── 请求执行
└── Transport（传输层）
    ├── Stdio
    ├── HTTP/SSE
    └── 自定义
```

---

## 二、工具定义与实现

### 2.1 工具规范

每个MCP工具需要定义：
- 名称和描述
- 输入参数schema
- 执行逻辑
- 输出格式

### 2.2 资源访问

MCP支持暴露各种资源：
- 文件系统
- 数据库
- API端点
- 内存数据

---

## 三、代码执行安全

### 3.1 安全原则

1. **最小权限**：只授予必要权限
2. **沙箱隔离**：限制代码执行环境
3. **输入验证**：验证所有输入
4. **输出过滤**：过滤敏感信息

### 3.2 执行环境

- 容器化隔离
- 资源限制
- 超时控制
- 日志审计

---

## 四、实战案例

### 案例1：构建MCP代码执行服务器

**场景**：创建一个安全的代码执行MCP服务器

**解决方案**：

```python
import json
import subprocess
import tempfile
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import docker

class Language(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    GO = "go"
    RUST = "rust"

@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    output: str
    error: Optional[str]
    execution_time: float
    memory_used: int

class MCPCodeExecutionServer:
    """MCP代码执行服务器"""

    def __init__(self, timeout: int = 30, max_memory: str = "256m"):
        self.timeout = timeout
        self.max_memory = max_memory
        self.docker_client = None
        self._init_docker()

    def _init_docker(self):
        """初始化Docker客户端"""
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            print(f"Docker初始化失败: {e}")

    # MCP工具定义
    @property
    def tools(self) -> List[Dict]:
        """返回工具定义"""
        return [
            {
                "name": "execute_code",
                "description": "在安全沙箱中执行代码",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "要执行的代码"
                        },
                        "language": {
                            "type": "string",
                            "enum": ["python", "javascript", "go"],
                            "description": "编程语言"
                        },
                        "inputs": {
                            "type": "object",
                            "description": "代码输入参数"
                        }
                    },
                    "required": ["code", "language"]
                }
            },
            {
                "name": "run_tests",
                "description": "运行代码测试",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "tests": {"type": "string"}
                    },
                    "required": ["code", "tests"]
                }
            },
            {
                "name": "analyze_code",
                "description": "分析代码质量",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "language": {"type": "string"}
                    },
                    "required": ["code"]
                }
            }
        ]

    async def execute_code(
        self,
        code: str,
        language: str,
        inputs: Dict = None
    ) -> ExecutionResult:
        """执行代码"""
        import time
        start_time = time.time()

        try:
            if self.docker_client:
                result = await self._execute_in_docker(code, language, inputs)
            else:
                result = await self._execute_locally(code, language, inputs)

            result.execution_time = time.time() - start_time
            return result

        except asyncio.TimeoutError:
            return ExecutionResult(
                success=False,
                output="",
                error="执行超时",
                execution_time=self.timeout,
                memory_used=0
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                execution_time=time.time() - start_time,
                memory_used=0
            )

    async def _execute_in_docker(
        self,
        code: str,
        language: str,
        inputs: Dict
    ) -> ExecutionResult:
        """在Docker中执行"""
        # 选择镜像
        image_map = {
            "python": "python:3.11-slim",
            "javascript": "node:18-slim",
            "go": "golang:1.21-alpine"
        }
        image = image_map.get(language, "python:3.11-slim")

        # 准备代码文件
        ext_map = {"python": ".py", "javascript": ".js", "go": ".go"}
        ext = ext_map.get(language, ".py")

        # 创建容器并执行
        try:
            container = self.docker_client.containers.run(
                image,
                command=f"python -c '{code}'" if language == "python" else f"node -e '{code}'",
                mem_limit=self.max_memory,
                timeout=self.timeout,
                remove=True,
                detach=False
            )

            return ExecutionResult(
                success=True,
                output=container.decode('utf-8') if isinstance(container, bytes) else str(container),
                error=None,
                execution_time=0,
                memory_used=0
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                execution_time=0,
                memory_used=0
            )

    async def _execute_locally(
        self,
        code: str,
        language: str,
        inputs: Dict
    ) -> ExecutionResult:
        """本地执行（仅用于可信代码）"""
        if language == "python":
            return await self._execute_python(code, inputs)
        elif language == "javascript":
            return await self._execute_javascript(code)
        else:
            return ExecutionResult(
                success=False,
                output="",
                error=f"不支持的语言: {language}",
                execution_time=0,
                memory_used=0
            )

    async def _execute_python(self, code: str, inputs: Dict) -> ExecutionResult:
        """执行Python代码"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False
        ) as f:
            f.write(code)
            temp_file = f.name

        try:
            # 使用subprocess安全执行
            process = await asyncio.create_subprocess_exec(
                'python', temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )

                return ExecutionResult(
                    success=process.returncode == 0,
                    output=stdout.decode('utf-8'),
                    error=stderr.decode('utf-8') if stderr else None,
                    execution_time=0,
                    memory_used=0
                )
            except asyncio.TimeoutError:
                process.kill()
                raise

        finally:
            os.unlink(temp_file)

    async def _execute_javascript(self, code: str) -> ExecutionResult:
        """执行JavaScript代码"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.js',
            delete=False
        ) as f:
            f.write(code)
            temp_file = f.name

        try:
            process = await asyncio.create_subprocess_exec(
                'node', temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )

            return ExecutionResult(
                success=process.returncode == 0,
                output=stdout.decode('utf-8'),
                error=stderr.decode('utf-8') if stderr else None,
                execution_time=0,
                memory_used=0
            )

        finally:
            os.unlink(temp_file)

    async def run_tests(self, code: str, tests: str) -> Dict:
        """运行测试"""
        # 合并代码和测试
        full_code = f"""
{code}

# Tests
{tests}

if __name__ == "__main__":
    import unittest
    unittest.main()
"""

        result = await self.execute_code(full_code, "python")

        return {
            "passed": result.success,
            "output": result.output,
            "errors": result.error
        }

    async def analyze_code(self, code: str, language: str) -> Dict:
        """分析代码"""
        analysis = {
            "lines_of_code": len(code.split('\n')),
            "complexity": self._estimate_complexity(code),
            "issues": []
        }

        # 检查常见问题
        if "eval(" in code:
            analysis["issues"].append({
                "severity": "high",
                "message": "使用eval()可能存在安全风险"
            })

        if "exec(" in code:
            analysis["issues"].append({
                "severity": "high",
                "message": "使用exec()可能存在安全风险"
            })

        return analysis

    def _estimate_complexity(self, code: str) -> int:
        """估算圈复杂度"""
        complexity = 1
        keywords = ["if", "elif", "else", "for", "while", "and", "or"]

        for keyword in keywords:
            complexity += code.count(f" {keyword} ")

        return complexity

# MCP协议处理
class MCPProtocolHandler:
    """MCP协议处理器"""

    def __init__(self, server: MCPCodeExecutionServer):
        self.server = server

    async def handle_request(self, request: Dict) -> Dict:
        """处理MCP请求"""
        method = request.get("method")
        params = request.get("params", {})

        if method == "tools/list":
            return {"tools": self.server.tools}

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "execute_code":
                result = await self.server.execute_code(
                    arguments["code"],
                    arguments["language"],
                    arguments.get("inputs")
                )
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({
                            "success": result.success,
                            "output": result.output,
                            "error": result.error
                        })
                    }]
                }

            elif tool_name == "run_tests":
                result = await self.server.run_tests(
                    arguments["code"],
                    arguments["tests"]
                )
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(result)
                    }]
                }

            elif tool_name == "analyze_code":
                result = await self.server.analyze_code(
                    arguments["code"],
                    arguments.get("language", "python")
                )
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(result)
                    }]
                }

        return {"error": "Unknown method"}

# 使用示例
async def demo_mcp_server():
    server = MCPCodeExecutionServer(timeout=10)
    handler = MCPProtocolHandler(server)

    # 列出可用工具
    tools_request = {"method": "tools/list"}
    tools_response = await handler.handle_request(tools_request)
    print("可用工具:", [t["name"] for t in tools_response["tools"]])

    # 执行代码
    exec_request = {
        "method": "tools/call",
        "params": {
            "name": "execute_code",
            "arguments": {
                "code": "print('Hello, MCP!')",
                "language": "python"
            }
        }
    }
    result = await handler.handle_request(exec_request)
    print("执行结果:", result)

# asyncio.run(demo_mcp_server())
```

**关键设计点**：
1. 标准MCP工具定义
2. Docker沙箱隔离
3. 超时和资源限制
4. 多语言支持

---

### 案例2：文件系统MCP服务器

**场景**：创建安全的文件系统访问MCP服务器

**解决方案**：

```python
import os
from pathlib import Path
from typing import List, Dict, Optional
import aiofiles

class FileSystemMCPServer:
    """文件系统MCP服务器"""

    def __init__(self, allowed_root: str, max_file_size: int = 10 * 1024 * 1024):
        self.allowed_root = Path(allowed_root).resolve()
        self.max_file_size = max_file_size

    def _validate_path(self, path: str) -> Path:
        """验证路径安全性"""
        full_path = (self.allowed_root / path).resolve()

        # 防止路径遍历攻击
        if not str(full_path).startswith(str(self.allowed_root)):
            raise PermissionError("访问路径超出允许范围")

        return full_path

    @property
    def tools(self) -> List[Dict]:
        """工具定义"""
        return [
            {
                "name": "read_file",
                "description": "读取文件内容",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "文件路径"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "write_file",
                "description": "写入文件内容",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "list_directory",
                "description": "列出目录内容",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "default": "."}
                    }
                }
            },
            {
                "name": "search_files",
                "description": "搜索文件",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string"},
                        "path": {"type": "string", "default": "."}
                    },
                    "required": ["pattern"]
                }
            }
        ]

    async def read_file(self, path: str) -> Dict:
        """读取文件"""
        try:
            full_path = self._validate_path(path)

            if not full_path.exists():
                return {"error": "文件不存在"}

            if full_path.stat().st_size > self.max_file_size:
                return {"error": "文件过大"}

            async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
                content = await f.read()

            return {
                "path": str(path),
                "content": content,
                "size": len(content)
            }

        except PermissionError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"读取失败: {e}"}

    async def write_file(self, path: str, content: str) -> Dict:
        """写入文件"""
        try:
            full_path = self._validate_path(path)

            # 检查大小
            if len(content) > self.max_file_size:
                return {"error": "内容过大"}

            # 确保目录存在
            full_path.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(full_path, 'w', encoding='utf-8') as f:
                await f.write(content)

            return {
                "success": True,
                "path": str(path),
                "bytes_written": len(content)
            }

        except PermissionError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"写入失败: {e}"}

    async def list_directory(self, path: str = ".") -> Dict:
        """列出目录"""
        try:
            full_path = self._validate_path(path)

            if not full_path.is_dir():
                return {"error": "不是目录"}

            items = []
            for item in full_path.iterdir():
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })

            return {
                "path": str(path),
                "items": items
            }

        except PermissionError as e:
            return {"error": str(e)}

    async def search_files(self, pattern: str, path: str = ".") -> Dict:
        """搜索文件"""
        try:
            full_path = self._validate_path(path)

            matches = []
            for root, dirs, files in os.walk(full_path):
                for name in files:
                    if pattern.lower() in name.lower():
                        rel_path = Path(root) / name
                        matches.append({
                            "name": name,
                            "path": str(rel_path.relative_to(self.allowed_root))
                        })

            return {
                "pattern": pattern,
                "matches": matches
            }

        except PermissionError as e:
            return {"error": str(e)}
```

---

### 案例3：数据库MCP服务器

**场景**：创建安全的数据库访问MCP服务器

**解决方案**：

```python
import sqlite3
from typing import List, Dict, Any
from contextlib import contextmanager

class DatabaseMCPServer:
    """数据库MCP服务器"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.allowed_tables = self._get_tables()

    def _get_tables(self) -> List[str]:
        """获取允许访问的表"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            return [row[0] for row in cursor.fetchall()]

    @contextmanager
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @property
    def tools(self) -> List[Dict]:
        """工具定义"""
        return [
            {
                "name": "query",
                "description": "执行只读SQL查询",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sql": {"type": "string"},
                        "params": {"type": "array"}
                    },
                    "required": ["sql"]
                }
            },
            {
                "name": "describe_table",
                "description": "描述表结构",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "table": {"type": "string"}
                    },
                    "required": ["table"]
                }
            },
            {
                "name": "list_tables",
                "description": "列出所有表",
                "inputSchema": {"type": "object"}
            }
        ]

    async def query(self, sql: str, params: List = None) -> Dict:
        """执行查询（只读）"""
        # 安全检查：只允许SELECT
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT"):
            return {"error": "只允许SELECT查询"}

        # 检查危险操作
        dangerous = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE"]
        for word in dangerous:
            if word in sql_upper:
                return {"error": f"不允许的操作: {word}"}

        try:
            with self._get_connection() as conn:
                cursor = conn.execute(sql, params or [])
                columns = [desc[0] for desc in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

                return {
                    "success": True,
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows)
                }

        except Exception as e:
            return {"error": str(e)}

    async def describe_table(self, table: str) -> Dict:
        """描述表结构"""
        if table not in self.allowed_tables:
            return {"error": f"表 '{table}' 不存在或无权访问"}

        with self._get_connection() as conn:
            cursor = conn.execute(f"PRAGMA table_info({table})")
            columns = [
                {
                    "name": row["name"],
                    "type": row["type"],
                    "nullable": not row["notnull"],
                    "primary_key": row["pk"]
                }
                for row in cursor.fetchall()
            ]

            return {
                "table": table,
                "columns": columns
            }

    async def list_tables(self) -> Dict:
        """列出所有表"""
        return {
            "tables": self.allowed_tables
        }
```

---

### 案例4：API集成MCP服务器

**场景**：创建外部API集成MCP服务器

**解决方案**：

```python
import aiohttp
from typing import Dict, List, Optional
import asyncio

class APIMCPServer:
    """API集成MCP服务器"""

    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = None

    async def _get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        if self.session:
            await self.session.close()

    @property
    def tools(self) -> List[Dict]:
        """工具定义"""
        return [
            {
                "name": "api_get",
                "description": "执行GET请求",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "endpoint": {"type": "string"},
                        "params": {"type": "object"}
                    },
                    "required": ["endpoint"]
                }
            },
            {
                "name": "api_post",
                "description": "执行POST请求",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "endpoint": {"type": "string"},
                        "data": {"type": "object"}
                    },
                    "required": ["endpoint", "data"]
                }
            }
        ]

    async def api_get(self, endpoint: str, params: Dict = None) -> Dict:
        """GET请求"""
        session = await self._get_session()

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            async with session.get(url, params=params, headers=headers) as response:
                data = await response.json()

                return {
                    "success": response.status == 200,
                    "status": response.status,
                    "data": data
                }

        except Exception as e:
            return {"error": str(e)}

    async def api_post(self, endpoint: str, data: Dict) -> Dict:
        """POST请求"""
        session = await self._get_session()

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            async with session.post(url, json=data, headers=headers) as response:
                response_data = await response.json()

                return {
                    "success": response.status in [200, 201],
                    "status": response.status,
                    "data": response_data
                }

        except Exception as e:
            return {"error": str(e)}
```

---

### 案例5：组合多个MCP服务器

**场景**：创建组合多个能力的MCP服务器

**解决方案**：

```python
from typing import Dict, List, Any

class CompositeMCPServer:
    """组合MCP服务器"""

    def __init__(self):
        self.servers = {}

    def register_server(self, name: str, server: Any):
        """注册子服务器"""
        self.servers[name] = server

    @property
    def tools(self) -> List[Dict]:
        """合并所有工具"""
        all_tools = []

        for server_name, server in self.servers.items():
            for tool in server.tools:
                # 添加前缀以避免冲突
                prefixed_tool = {
                    **tool,
                    "name": f"{server_name}_{tool['name']}"
                }
                all_tools.append(prefixed_tool)

        return all_tools

    async def call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """调用工具"""
        # 解析服务器名和工具名
        parts = tool_name.split("_", 1)
        if len(parts) != 2:
            return {"error": "无效的工具名"}

        server_name, actual_tool = parts

        if server_name not in self.servers:
            return {"error": f"未知服务器: {server_name}"}

        server = self.servers[server_name]

        # 调用对应方法
        method_name = actual_tool
        if hasattr(server, method_name):
            method = getattr(server, method_name)
            return await method(**arguments)

        return {"error": f"未知工具: {actual_tool}"}

# 使用示例
async def create_composite_server():
    composite = CompositeMCPServer()

    # 注册文件系统服务器
    # composite.register_server("fs", FileSystemMCPServer("/data"))

    # 注册数据库服务器
    # composite.register_server("db", DatabaseMCPServer("app.db"))

    # 注册API服务器
    # composite.register_server("api", APIMCPServer("https://api.example.com"))

    return composite
```

---

## 五、最佳实践

### 5.1 安全设计

| 原则 | 实践 |
|------|------|
| 最小权限 | 只授予必要权限 |
| 输入验证 | 验证所有输入 |
| 沙箱隔离 | 限制执行环境 |
| 审计日志 | 记录所有操作 |

### 5.2 性能优化

- 使用连接池
- 实现缓存机制
- 异步处理请求
- 资源限制和超时

### 5.3 错误处理

- 统一错误格式
- 详细的错误信息
- 优雅的降级
- 重试机制

---

## 六、总结

MCP代码执行的核心要素：

1. **标准化协议**：统一的工具接口
2. **安全隔离**：受控的执行环境
3. **灵活扩展**：易于添加新能力
4. **组合复用**：多个服务器可组合
