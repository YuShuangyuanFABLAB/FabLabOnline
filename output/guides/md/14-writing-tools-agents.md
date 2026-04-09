# 为Agent编写工具（Writing Tools for Agents）

> 来源：https://www.anthropic.com/engineering/tools-for-agents
> 发布日期：2025-09-11

---

## 一、工具设计原则

### 1.1 核心原则

为AI Agent编写工具需要遵循特定原则，确保工具对模型友好。

| 原则 | 说明 |
|------|------|
| **明确性** | 工具名称和描述要清晰 |
| **原子性** | 每个工具只做一件事 |
| **可组合性** | 工具可以组合使用 |
| **容错性** | 优雅处理错误情况 |

### 1.2 与传统API的区别

```
传统API设计：
├── 面向人类开发者
├── 需要阅读文档
├── 复杂参数可选
└── 错误码需要解析

Agent工具设计：
├── 面向LLM
├── 名称即文档
├── 参数精简必需
└── 错误信息自解释
```

---

## 二、工具设计指南

### 2.1 命名规范

- 使用动词+名词格式
- 避免缩写
- 名称应自解释

### 2.2 描述规范

- 说明工具做什么
- 说明何时使用
- 说明返回什么

### 2.3 参数设计

- 最小化参数数量
- 提供默认值
- 清晰的类型定义

---

## 三、实战案例

### 案例1：设计友好的搜索工具

**场景**：为Agent设计搜索工具

**解决方案**：

```python
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class SearchType(Enum):
    """搜索类型"""
    WEB = "web"
    NEWS = "news"
    ACADEMIC = "academic"
    CODE = "code"

@dataclass
class SearchToolConfig:
    """搜索工具配置"""
    max_results: int = 10
    timeout: int = 30
    include_snippets: bool = True

# 好的设计
class GoodSearchTool:
    """
    搜索工具 - 搜索网络获取信息

    用途：当你需要查找最新信息、验证事实、或获取参考资料时使用此工具。

    参数：
    - query: 搜索查询词（必需）
    - search_type: 搜索类型，可选 web/news/academic/code（可选，默认web）
    - max_results: 返回结果数量（可选，默认5）
    """

    def __init__(self, config: SearchToolConfig = None):
        self.config = config or SearchToolConfig()

    @property
    def schema(self) -> Dict:
        """工具Schema"""
        return {
            "name": "search",
            "description": "搜索网络获取信息。当需要查找最新信息、验证事实、或获取参考资料时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询词，使用简洁的关键词"
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["web", "news", "academic", "code"],
                        "description": "搜索类型",
                        "default": "web"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "返回结果数量",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20
                    }
                },
                "required": ["query"]
            }
        }

    async def execute(self, query: str, search_type: str = "web", max_results: int = 5) -> Dict:
        """执行搜索"""
        try:
            # 执行搜索
            results = await self._do_search(query, search_type, max_results)

            return {
                "success": True,
                "results": results,
                "total": len(results),
                "query": query,
                "search_type": search_type
            }

        except Exception as e:
            return {
                "success": False,
                "error": self._format_error(e),
                "suggestion": self._get_error_suggestion(e)
            }

    async def _do_search(self, query: str, search_type: str, max_results: int) -> List[Dict]:
        """实际搜索逻辑"""
        # 模拟搜索
        return [
            {
                "title": f"搜索结果 {i+1}",
                "url": f"https://example.com/result/{i}",
                "snippet": f"关于 '{query}' 的内容摘要..."
            }
            for i in range(max_results)
        ]

    def _format_error(self, error: Exception) -> str:
        """格式化错误信息"""
        error_messages = {
            "TimeoutError": "搜索超时，请尝试简化查询词或稍后重试",
            "ConnectionError": "无法连接到搜索服务，请检查网络连接",
            "RateLimitError": "搜索请求过于频繁，请等待几秒后重试"
        }

        error_type = type(error).__name__
        return error_messages.get(error_type, f"搜索失败: {str(error)}")

    def _get_error_suggestion(self, error: Exception) -> str:
        """获取错误建议"""
        suggestions = {
            "TimeoutError": "可以尝试使用更短的查询词",
            "ConnectionError": "检查网络连接后重试",
            "RateLimitError": "等待10秒后重试"
        }

        error_type = type(error).__name__
        return suggestions.get(error_type, "请重试或换一种方式搜索")

# 不好的设计
class BadSearchTool:
    """搜索工具"""

    @property
    def schema(self) -> Dict:
        return {
            "name": "s",  # 名称不清晰
            "description": "search",  # 描述太简单
            "parameters": {
                "type": "object",
                "properties": {
                    "q": {"type": "string"},  # 参数名不清晰
                    "t": {"type": "integer"},  # 没有描述
                    "opt": {"type": "object"}  # 参数太复杂
                }
            }
        }
```

---

### 案例2：文件操作工具设计

**场景**：设计文件读写工具

**解决方案**：

```python
from pathlib import Path
from typing import Optional, List
import os

class FileTools:
    """文件操作工具集"""

    def __init__(self, allowed_dirs: List[str] = None):
        self.allowed_dirs = [Path(d).resolve() for d in (allowed_dirs or ["."])]

    def _validate_path(self, path: str) -> Path:
        """验证路径安全性"""
        full_path = Path(path).resolve()

        # 检查是否在允许的目录内
        for allowed_dir in self.allowed_dirs:
            try:
                full_path.relative_to(allowed_dir)
                return full_path
            except ValueError:
                continue

        raise PermissionError(f"路径 '{path}' 不在允许的目录内")

    @property
    def read_file_schema(self) -> Dict:
        """读取文件工具Schema"""
        return {
            "name": "read_file",
            "description": "读取文件内容。当需要查看文件内容时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径，相对或绝对路径"
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "起始行号（可选，从1开始）",
                        "default": 1
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "结束行号（可选）",
                        "default": null
                    }
                },
                "required": ["path"]
            }
        }

    async def read_file(
        self,
        path: str,
        start_line: int = 1,
        end_line: Optional[int] = None
    ) -> Dict:
        """读取文件"""
        try:
            validated_path = self._validate_path(path)

            if not validated_path.exists():
                return {
                    "success": False,
                    "error": f"文件不存在: {path}",
                    "suggestion": "请检查文件路径是否正确"
                }

            if not validated_path.is_file():
                return {
                    "success": False,
                    "error": f"路径不是文件: {path}",
                    "suggestion": "请提供文件路径而非目录路径"
                }

            # 读取文件
            with open(validated_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 行号处理
            start_idx = max(0, start_line - 1)
            end_idx = end_line if end_line else len(lines)

            selected_lines = lines[start_idx:end_idx]

            return {
                "success": True,
                "path": str(validated_path),
                "content": "".join(selected_lines),
                "total_lines": len(lines),
                "returned_lines": len(selected_lines),
                "start_line": start_line,
                "end_line": start_line + len(selected_lines) - 1
            }

        except PermissionError as e:
            return {
                "success": False,
                "error": str(e),
                "suggestion": "请使用允许目录内的文件路径"
            }
        except UnicodeDecodeError:
            return {
                "success": False,
                "error": "无法解码文件内容",
                "suggestion": "文件可能是二进制文件或使用非UTF-8编码"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"读取文件失败: {str(e)}",
                "suggestion": "请检查文件是否存在且可读"
            }

    @property
    def write_file_schema(self) -> Dict:
        """写入文件工具Schema"""
        return {
            "name": "write_file",
            "description": "写入或创建文件。当需要创建新文件或完全覆盖现有文件时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径"
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入的内容"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["write", "append"],
                        "description": "写入模式：write覆盖，append追加",
                        "default": "write"
                    }
                },
                "required": ["path", "content"]
            }
        }

    async def write_file(self, path: str, content: str, mode: str = "write") -> Dict:
        """写入文件"""
        try:
            validated_path = self._validate_path(path)

            # 创建目录
            validated_path.parent.mkdir(parents=True, exist_ok=True)

            # 写入模式
            write_mode = 'w' if mode == "write" else 'a'

            # 检查文件是否存在
            file_existed = validated_path.exists()

            with open(validated_path, write_mode, encoding='utf-8') as f:
                f.write(content)

            return {
                "success": True,
                "path": str(validated_path),
                "bytes_written": len(content.encode('utf-8')),
                "mode": mode,
                "file_created": not file_existed
            }

        except PermissionError as e:
            return {
                "success": False,
                "error": str(e),
                "suggestion": "请使用允许目录内的文件路径"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"写入文件失败: {str(e)}",
                "suggestion": "请检查目录权限"
            }

    @property
    def list_directory_schema(self) -> Dict:
        """列出目录工具Schema"""
        return {
            "name": "list_directory",
            "description": "列出目录内容。当需要查看目录中有哪些文件和子目录时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "目录路径",
                        "default": "."
                    },
                    "pattern": {
                        "type": "string",
                        "description": "文件名过滤模式（可选）",
                        "default": "*"
                    }
                }
            }
        }

    async def list_directory(self, path: str = ".", pattern: str = "*") -> Dict:
        """列出目录"""
        try:
            validated_path = self._validate_path(path)

            if not validated_path.exists():
                return {
                    "success": False,
                    "error": f"目录不存在: {path}"
                }

            if not validated_path.is_dir():
                return {
                    "success": False,
                    "error": f"路径不是目录: {path}"
                }

            items = []
            for item in validated_path.glob(pattern):
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                    "modified": item.stat().st_mtime
                })

            return {
                "success": True,
                "path": str(validated_path),
                "items": sorted(items, key=lambda x: (x["type"], x["name"])),
                "total": len(items)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"列出目录失败: {str(e)}"
            }
```

---

### 案例3：数据库查询工具

**场景**：设计安全的数据库查询工具

**解决方案**：

```python
import sqlite3
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

class DatabaseTool:
    """数据库查询工具"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_allowed_tables()

    def _init_allowed_tables(self):
        """初始化允许访问的表"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            self.allowed_tables = [row[0] for row in cursor.fetchall()]

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
    def schema(self) -> Dict:
        """工具Schema"""
        return {
            "name": "query_database",
            "description": f"""执行SQL查询。
可用表：{', '.join(self.allowed_tables)}
仅支持SELECT查询，用于查询数据。""",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SELECT SQL查询语句"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量限制",
                        "default": 100
                    }
                },
                "required": ["sql"]
            }
        }

    async def execute(self, sql: str, limit: int = 100) -> Dict:
        """执行查询"""
        # 安全检查
        sql_upper = sql.strip().upper()

        if not sql_upper.startswith("SELECT"):
            return {
                "success": False,
                "error": "只允许SELECT查询",
                "suggestion": "此工具仅用于查询数据，不能修改数据"
            }

        # 检查危险操作
        dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return {
                    "success": False,
                    "error": f"查询包含不允许的关键字: {keyword}",
                    "suggestion": "只允许SELECT查询"
                }

        # 检查表名
        for table in self.allowed_tables:
            if table in sql:
                break
        else:
            return {
                "success": False,
                "error": "查询的表不在允许列表中",
                "suggestion": f"可用表: {', '.join(self.allowed_tables)}"
            }

        try:
            with self._get_connection() as conn:
                # 添加LIMIT
                if "LIMIT" not in sql_upper:
                    sql = f"{sql.rstrip(';')} LIMIT {limit}"

                cursor = conn.execute(sql)
                columns = [desc[0] for desc in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

                return {
                    "success": True,
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows),
                    "sql": sql
                }

        except sqlite3.Error as e:
            return {
                "success": False,
                "error": f"SQL错误: {str(e)}",
                "suggestion": "请检查SQL语法是否正确"
            }

    @property
    def describe_table_schema(self) -> Dict:
        """描述表结构工具Schema"""
        return {
            "name": "describe_table",
            "description": "获取表的结构信息，包括列名、类型等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": f"表名，可选: {', '.join(self.allowed_tables)}"
                    }
                },
                "required": ["table_name"]
            }
        }

    async def describe_table(self, table_name: str) -> Dict:
        """描述表结构"""
        if table_name not in self.allowed_tables:
            return {
                "success": False,
                "error": f"表 '{table_name}' 不存在或无权访问",
                "available_tables": self.allowed_tables
            }

        try:
            with self._get_connection() as conn:
                cursor = conn.execute(f"PRAGMA table_info({table_name})")
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
                    "success": True,
                    "table_name": table_name,
                    "columns": columns
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
```

---

### 案例4：API调用工具

**场景**：设计通用的API调用工具

**解决方案**：

```python
import aiohttp
from typing import Dict, Any, Optional

class APICallTool:
    """API调用工具"""

    def __init__(self, base_url: str = "", default_headers: Dict = None):
        self.base_url = base_url.rstrip('/')
        self.default_headers = default_headers or {}
        self.session = None

    async def _get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        if self.session:
            await self.session.close()

    @property
    def schema(self) -> Dict:
        """工具Schema"""
        return {
            "name": "api_call",
            "description": "调用HTTP API。当需要与外部服务交互时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "enum": ["GET", "POST", "PUT", "DELETE"],
                        "description": "HTTP方法",
                        "default": "GET"
                    },
                    "endpoint": {
                        "type": "string",
                        "description": "API端点路径"
                    },
                    "params": {
                        "type": "object",
                        "description": "URL查询参数（可选）"
                    },
                    "body": {
                        "type": "object",
                        "description": "请求体（POST/PUT时使用）"
                    },
                    "headers": {
                        "type": "object",
                        "description": "额外的请求头（可选）"
                    }
                },
                "required": ["endpoint"]
            }
        }

    async def execute(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        body: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict:
        """执行API调用"""
        session = await self._get_session()

        # 构建URL
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # 合并headers
        request_headers = {**self.default_headers, **(headers or {})}

        try:
            async with session.request(
                method,
                url,
                params=params,
                json=body if body else None,
                headers=request_headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response_data = await response.json()

                if response.status >= 400:
                    return {
                        "success": False,
                        "status_code": response.status,
                        "error": f"HTTP错误: {response.status}",
                        "response": response_data,
                        "suggestion": self._get_status_suggestion(response.status)
                    }

                return {
                    "success": True,
                    "status_code": response.status,
                    "data": response_data,
                    "url": str(response.url)
                }

        except aiohttp.ClientError as e:
            return {
                "success": False,
                "error": f"网络错误: {str(e)}",
                "suggestion": "请检查网络连接和URL是否正确"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"请求失败: {str(e)}"
            }

    def _get_status_suggestion(self, status: int) -> str:
        """获取状态码建议"""
        suggestions = {
            400: "请求参数可能有误，请检查请求格式",
            401: "未授权，请检查认证信息",
            403: "无权限访问此资源",
            404: "资源不存在，请检查URL路径",
            429: "请求过于频繁，请稍后重试",
            500: "服务器错误，请稍后重试"
        }
        return suggestions.get(status, "请检查请求是否正确")
```

---

### 案例5：工具组合和编排

**场景**：设计可组合的工具系统

**解决方案**：

```python
from typing import Dict, List, Any, Callable

class ToolComposer:
    """工具组合器"""

    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.workflows: Dict[str, List[str]] = {}

    def register_tool(self, name: str, tool: Callable, schema: Dict):
        """注册工具"""
        self.tools[name] = {
            "handler": tool,
            "schema": schema
        }

    def register_workflow(self, name: str, tool_sequence: List[str]):
        """注册工作流"""
        self.workflows[name] = tool_sequence

    async def execute_workflow(self, name: str, initial_input: Dict) -> Dict:
        """执行工作流"""
        if name not in self.workflows:
            return {"success": False, "error": f"工作流 '{name}' 不存在"}

        context = initial_input
        results = []

        for tool_name in self.workflows[name]:
            if tool_name not in self.tools:
                return {
                    "success": False,
                    "error": f"工具 '{tool_name}' 不存在",
                    "completed_steps": results
                }

            tool = self.tools[tool_name]
            result = await tool["handler"](**context)

            results.append({
                "tool": tool_name,
                "result": result
            })

            # 更新上下文
            if result.get("success"):
                context.update(result)
            else:
                return {
                    "success": False,
                    "error": f"工具 '{tool_name}' 执行失败",
                    "results": results
                }

        return {
            "success": True,
            "results": results,
            "final_context": context
        }

    def get_all_schemas(self) -> List[Dict]:
        """获取所有工具Schema"""
        return [tool["schema"] for tool in self.tools.values()]

# 使用示例
async def demo_composer():
    composer = ToolComposer()

    # 注册工具
    composer.register_tool("search", search_tool, search_schema)
    composer.register_tool("extract", extract_tool, extract_schema)
    composer.register_tool("summarize", summarize_tool, summarize_schema)

    # 注册工作流
    composer.register_workflow("research", ["search", "extract", "summarize"])

    # 执行工作流
    result = await composer.execute_workflow("research", {"query": "AI trends 2025"})
```

---

## 四、最佳实践

### 4.1 工具描述模板

```
名称：{动词}_{名词}
描述：{功能}。{何时使用}。
参数：
- {参数1}：{描述}（{是否必需}）
- {参数2}：{描述}（{是否必需}，默认值：{默认}）
```

### 4.2 错误处理原则

| 原则 | 说明 |
|------|------|
| **自解释** | 错误信息应说明问题和解决方案 |
| **可恢复** | 提供重试或替代建议 |
| **一致性** | 使用统一的错误格式 |

### 4.3 性能考虑

- 设置合理的超时
- 限制返回数据量
- 实现缓存机制
- 支持分页

---

## 五、总结

为Agent编写工具的核心要点：

1. **清晰的接口**：名称和描述要自解释
2. **原子操作**：每个工具只做一件事
3. **友好的错误**：提供可操作的反馈
4. **安全的实现**：验证输入、限制权限
