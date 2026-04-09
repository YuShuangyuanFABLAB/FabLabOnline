# 高级工具使用（Advanced Tool Use）

> 来源：https://www.anthropic.com/engineering/tool-use
> 发布日期：2025-11-24

---

## 一、工具使用概述

### 1.1 什么是工具使用

工具使用是让LLM调用外部函数/API的能力，使模型能够与外部世界交互，执行计算、查询数据、操作文件等。

### 1.2 核心组件

| 组件 | 说明 |
|------|------|
| **工具定义** | 描述工具的名称、参数、功能 |
| **参数验证** | 验证模型生成的参数 |
| **执行引擎** | 实际执行工具调用 |
| **结果处理** | 将结果返回给模型 |

### 1.3 工具使用流程

```
工具使用流程：
├── 1. 工具定义
│   └── 向模型描述可用工具
├── 2. 模型决策
│   └── 模型决定是否使用工具
├── 3. 参数生成
│   └── 模型生成调用参数
├── 4. 执行调用
│   └── 系统执行工具函数
├── 5. 结果返回
│   └── 将结果返回给模型
└── 6. 继续对话
    └── 模型基于结果继续响应
```

---

## 二、工具定义最佳实践

### 2.1 清晰的描述

每个工具应该有：
- 清晰的名称
- 详细的功能描述
- 完整的参数schema
- 使用示例

### 2.2 参数设计

- 使用明确的类型
- 提供默认值
- 添加验证规则
- 描述参数用途

---

## 三、高级模式

### 3.1 工具链

多个工具按顺序或并行执行。

### 3.2 条件调用

根据上下文决定是否调用工具。

### 3.3 错误恢复

处理工具调用失败的情况。

---

## 四、实战案例

### 案例1：构建完整的工具使用系统

**场景**：创建一个支持多种工具的智能助手

**解决方案**：

```python
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum
import json
import inspect

class ToolCategory(Enum):
    """工具类别"""
    SEARCH = "search"
    COMPUTATION = "computation"
    FILE = "file"
    API = "api"
    DATABASE = "database"

@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    enum: List[str] = None

@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    description: str
    parameters: List[ToolParameter]
    category: ToolCategory
    handler: Callable
    examples: List[Dict] = None

    def to_schema(self) -> Dict:
        """转换为JSON Schema"""
        properties = {}
        required = []

        for param in self.parameters:
            prop = {
                "type": param.type,
                "description": param.description
            }
            if param.enum:
                prop["enum"] = param.enum
            properties[param.name] = prop

            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }

class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition):
        """注册工具"""
        self.tools[tool.name] = tool

    def get(self, name: str) -> Optional[ToolDefinition]:
        """获取工具"""
        return self.tools.get(name)

    def list_tools(self) -> List[Dict]:
        """列出所有工具的schema"""
        return [tool.to_schema() for tool in self.tools.values()]

    def list_by_category(self, category: ToolCategory) -> List[ToolDefinition]:
        """按类别列出工具"""
        return [t for t in self.tools.values() if t.category == category]

class ToolExecutor:
    """工具执行器"""

    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.call_history = []

    async def execute(self, tool_name: str, arguments: Dict) -> Dict:
        """执行工具"""
        tool = self.registry.get(tool_name)

        if not tool:
            return {
                "success": False,
                "error": f"工具 '{tool_name}' 不存在"
            }

        # 验证参数
        validation_result = self.validate_arguments(tool, arguments)
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": f"参数验证失败: {validation_result['error']}"
            }

        # 执行工具
        try:
            result = await tool.handler(**arguments)

            # 记录调用历史
            self.call_history.append({
                "tool": tool_name,
                "arguments": arguments,
                "result": result,
                "success": True
            })

            return {
                "success": True,
                "result": result
            }

        except Exception as e:
            self.call_history.append({
                "tool": tool_name,
                "arguments": arguments,
                "error": str(e),
                "success": False
            })

            return {
                "success": False,
                "error": str(e)
            }

    def validate_arguments(self, tool: ToolDefinition, arguments: Dict) -> Dict:
        """验证参数"""
        for param in tool.parameters:
            if param.required and param.name not in arguments:
                return {
                    "valid": False,
                    "error": f"缺少必需参数: {param.name}"
                }

            if param.name in arguments:
                value = arguments[param.name]

                # 类型检查
                if param.type == "string" and not isinstance(value, str):
                    return {
                        "valid": False,
                        "error": f"参数 '{param.name}' 应为字符串"
                    }
                elif param.type == "number" and not isinstance(value, (int, float)):
                    return {
                        "valid": False,
                        "error": f"参数 '{param.name}' 应为数字"
                    }
                elif param.type == "boolean" and not isinstance(value, bool):
                    return {
                        "valid": False,
                        "error": f"参数 '{param.name}' 应为布尔值"
                    }
                elif param.type == "array" and not isinstance(value, list):
                    return {
                        "valid": False,
                        "error": f"参数 '{param.name}' 应为数组"
                    }

                # 枚举检查
                if param.enum and value not in param.enum:
                    return {
                        "valid": False,
                        "error": f"参数 '{param.name}' 必须是: {param.enum}"
                    }

        return {"valid": True}

class ToolUseAgent:
    """工具使用Agent"""

    def __init__(self, llm_client, registry: ToolRegistry):
        self.llm = llm_client
        self.registry = registry
        self.executor = ToolExecutor(registry)

    async def process(self, user_input: str, context: Dict = None) -> str:
        """处理用户输入"""
        # 获取可用工具
        tools_schema = self.registry.list_tools()

        # 构建提示
        messages = [
            {"role": "system", "content": self.build_system_prompt(tools_schema)},
            {"role": "user", "content": user_input}
        ]

        if context:
            messages.insert(1, {
                "role": "system",
                "content": f"上下文: {json.dumps(context)}"
            })

        # 循环处理
        max_iterations = 10
        for _ in range(max_iterations):
            response = await self.llm.chat(messages, tools=tools_schema)

            # 检查是否需要调用工具
            if response.get("tool_calls"):
                for tool_call in response["tool_calls"]:
                    tool_name = tool_call["function"]["name"]
                    arguments = json.loads(tool_call["function"]["arguments"])

                    # 执行工具
                    result = await self.executor.execute(tool_name, arguments)

                    # 添加结果到消息
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(result)
                    })

            else:
                # 返回最终响应
                return response.get("content", "")

        return "达到最大迭代次数"

    def build_system_prompt(self, tools: List[Dict]) -> str:
        """构建系统提示"""
        tool_descriptions = "\n".join([
            f"- {t['name']}: {t['description']}"
            for t in tools
        ])

        return f"""你是一个智能助手，可以使用以下工具：

{tool_descriptions}

当你需要使用工具时，请按照工具的schema提供参数。
如果不需要使用工具，直接回答用户问题。
"""

# 定义具体工具
async def search_web(query: str, num_results: int = 5) -> List[Dict]:
    """搜索网络"""
    # 模拟搜索
    return [
        {"title": f"结果 {i+1}", "snippet": f"关于 {query} 的内容...", "url": f"https://example.com/{i}"}
        for i in range(num_results)
    ]

async def calculate(expression: str) -> float:
    """执行数学计算"""
    # 安全计算
    allowed_chars = set("0123456789+-*/.() ")
    if not all(c in allowed_chars for c in expression):
        raise ValueError("表达式包含不允许的字符")

    return eval(expression)

async def get_weather(city: str, unit: str = "celsius") -> Dict:
    """获取天气"""
    # 模拟天气API
    return {
        "city": city,
        "temperature": 22 if unit == "celsius" else 72,
        "condition": "晴朗",
        "humidity": 60
    }

async def query_database(sql: str) -> List[Dict]:
    """查询数据库"""
    # 模拟数据库查询
    return [
        {"id": 1, "name": "张三", "age": 30},
        {"id": 2, "name": "李四", "age": 25}
    ]

# 创建注册表并注册工具
registry = ToolRegistry()

# 搜索工具
registry.register(ToolDefinition(
    name="search_web",
    description="在网络上搜索信息",
    parameters=[
        ToolParameter("query", "string", "搜索查询词", required=True),
        ToolParameter("num_results", "number", "返回结果数量", required=False, default=5)
    ],
    category=ToolCategory.SEARCH,
    handler=search_web
))

# 计算工具
registry.register(ToolDefinition(
    name="calculate",
    description="执行数学计算",
    parameters=[
        ToolParameter("expression", "string", "数学表达式", required=True)
    ],
    category=ToolCategory.COMPUTATION,
    handler=calculate
))

# 天气工具
registry.register(ToolDefinition(
    name="get_weather",
    description="获取城市天气信息",
    parameters=[
        ToolParameter("city", "string", "城市名称", required=True),
        ToolParameter("unit", "string", "温度单位", required=False, default="celsius", enum=["celsius", "fahrenheit"])
    ],
    category=ToolCategory.API,
    handler=get_weather
))

# 数据库工具
registry.register(ToolDefinition(
    name="query_database",
    description="执行SQL查询",
    parameters=[
        ToolParameter("sql", "string", "SQL查询语句", required=True)
    ],
    category=ToolCategory.DATABASE,
    handler=query_database
))

# 使用示例
async def demo():
    # 列出所有工具
    print("可用工具:")
    for tool in registry.list_tools():
        print(f"  - {tool['name']}: {tool['description']}")

    # 执行工具
    executor = ToolExecutor(registry)

    # 搜索
    result = await executor.execute("search_web", {"query": "Python教程"})
    print(f"搜索结果: {result}")

    # 计算
    result = await executor.execute("calculate", {"expression": "2 + 3 * 4"})
    print(f"计算结果: {result}")

# asyncio.run(demo())
```

---

### 案例2：工具链执行

**场景**：实现多个工具按顺序执行

**解决方案**：

```python
from typing import List, Dict, Any
import asyncio

class ToolChain:
    """工具链"""

    def __init__(self, executor: ToolExecutor):
        self.executor = executor
        self.steps = []

    def add_step(self, tool_name: str, arguments: Dict, output_key: str = None):
        """添加步骤"""
        self.steps.append({
            "tool": tool_name,
            "arguments": arguments,
            "output_key": output_key
        })
        return self

    async def execute(self, initial_context: Dict = None) -> Dict:
        """执行工具链"""
        context = initial_context or {}
        results = []

        for i, step in enumerate(self.steps):
            # 解析参数中的引用
            resolved_args = self.resolve_arguments(step["arguments"], context)

            # 执行工具
            result = await self.executor.execute(step["tool"], resolved_args)

            results.append({
                "step": i + 1,
                "tool": step["tool"],
                "arguments": resolved_args,
                "result": result
            })

            # 保存结果到上下文
            if step["output_key"] and result["success"]:
                context[step["output_key"]] = result["result"]

        return {
            "success": all(r["result"]["success"] for r in results),
            "context": context,
            "steps": results
        }

    def resolve_arguments(self, arguments: Dict, context: Dict) -> Dict:
        """解析参数中的引用"""
        resolved = {}

        for key, value in arguments.items():
            if isinstance(value, str) and value.startswith("$"):
                # 从上下文中获取值
                ref_key = value[1:]
                resolved[key] = context.get(ref_key)
            elif isinstance(value, dict):
                resolved[key] = self.resolve_arguments(value, context)
            else:
                resolved[key] = value

        return resolved

# 使用示例
async def demo_tool_chain():
    registry = ToolRegistry()
    # 注册工具...
    executor = ToolExecutor(registry)

    # 创建工具链
    chain = ToolChain(executor)
    chain.add_step("search_web", {"query": "Python教程", "num_results": 3}, output_key="search_results")
    chain.add_step("calculate", {"expression": "10 * 5"}, output_key="calculation")

    # 执行
    result = await chain.execute()
    print(f"工具链执行结果: {result}")
```

---

### 案例3：并行工具调用

**场景**：同时调用多个独立的工具

**解决方案**：

```python
class ParallelToolExecutor:
    """并行工具执行器"""

    def __init__(self, executor: ToolExecutor):
        self.executor = executor

    async def execute_parallel(self, calls: List[Dict]) -> List[Dict]:
        """并行执行多个工具调用"""
        tasks = [
            self.executor.execute(call["tool"], call["arguments"])
            for call in calls
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return [
            {
                "tool": call["tool"],
                "arguments": call["arguments"],
                "result": result if not isinstance(result, Exception) else None,
                "error": str(result) if isinstance(result, Exception) else None
            }
            for call, result in zip(calls, results)
        ]

    async def execute_with_fallback(
        self,
        primary_call: Dict,
        fallback_calls: List[Dict]
    ) -> Dict:
        """带降级的执行"""
        # 尝试主工具
        result = await self.executor.execute(
            primary_call["tool"],
            primary_call["arguments"]
        )

        if result["success"]:
            return result

        # 尝试降级工具
        for fallback in fallback_calls:
            result = await self.executor.execute(
                fallback["tool"],
                fallback["arguments"]
            )
            if result["success"]:
                return result

        return {"success": False, "error": "所有工具都执行失败"}

# 使用示例
async def demo_parallel():
    registry = ToolRegistry()
    executor = ToolExecutor(registry)
    parallel_executor = ParallelToolExecutor(executor)

    # 并行调用多个工具
    calls = [
        {"tool": "get_weather", "arguments": {"city": "北京"}},
        {"tool": "get_weather", "arguments": {"city": "上海"}},
        {"tool": "get_weather", "arguments": {"city": "广州"}}
    ]

    results = await parallel_executor.execute_parallel(calls)
    print(f"并行调用结果: {results}")
```

---

### 案例4：错误处理和重试

**场景**：实现健壮的工具调用

**解决方案**：

```python
from enum import Enum
from typing import Callable

class RetryStrategy(Enum):
    """重试策略"""
    NONE = "none"
    FIXED = "fixed"
    EXPONENTIAL = "exponential"

class RobustToolExecutor:
    """健壮的工具执行器"""

    def __init__(self, executor: ToolExecutor):
        self.executor = executor
        self.error_handlers = {}

    def register_error_handler(self, tool_name: str, error_type: type, handler: Callable):
        """注册错误处理器"""
        if tool_name not in self.error_handlers:
            self.error_handlers[tool_name] = {}
        self.error_handlers[tool_name][error_type] = handler

    async def execute_with_retry(
        self,
        tool_name: str,
        arguments: Dict,
        max_retries: int = 3,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    ) -> Dict:
        """带重试的执行"""
        last_error = None

        for attempt in range(max_retries):
            result = await self.executor.execute(tool_name, arguments)

            if result["success"]:
                return result

            last_error = result.get("error")

            # 检查是否有错误处理器
            if tool_name in self.error_handlers:
                for error_type, handler in self.error_handlers[tool_name].items():
                    if error_type.__name__ in str(last_error):
                        handled_result = await handler(arguments, last_error)
                        if handled_result:
                            return handled_result

            # 计算等待时间
            if strategy == RetryStrategy.EXPONENTIAL:
                wait_time = 2 ** attempt
            elif strategy == RetryStrategy.FIXED:
                wait_time = 1
            else:
                break

            await asyncio.sleep(wait_time)

        return {
            "success": False,
            "error": f"重试{max_retries}次后仍失败: {last_error}"
        }

    async def execute_with_timeout(
        self,
        tool_name: str,
        arguments: Dict,
        timeout: float = 10.0
    ) -> Dict:
        """带超时的执行"""
        try:
            result = await asyncio.wait_for(
                self.executor.execute(tool_name, arguments),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"工具执行超时（{timeout}秒）"
            }

    async def execute_with_validation(
        self,
        tool_name: str,
        arguments: Dict,
        validators: List[Callable]
    ) -> Dict:
        """带结果验证的执行"""
        result = await self.executor.execute(tool_name, arguments)

        if not result["success"]:
            return result

        # 运行验证器
        for validator in validators:
            validation_result = validator(result["result"])
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"结果验证失败: {validation_result['error']}"
                }

        return result

# 使用示例
async def demo_robust():
    registry = ToolRegistry()
    executor = ToolExecutor(registry)
    robust_executor = RobustToolExecutor(executor)

    # 带重试的执行
    result = await robust_executor.execute_with_retry(
        "get_weather",
        {"city": "北京"},
        max_retries=3
    )

    # 带超时的执行
    result = await robust_executor.execute_with_timeout(
        "search_web",
        {"query": "test"},
        timeout=5.0
    )

    # 带验证的执行
    def validate_weather_result(result):
        if "temperature" not in result:
            return {"valid": False, "error": "缺少温度数据"}
        return {"valid": True}

    result = await robust_executor.execute_with_validation(
        "get_weather",
        {"city": "北京"},
        validators=[validate_weather_result]
    )
```

---

### 案例5：工具使用监控

**场景**：监控和记录工具使用情况

**解决方案**：

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict
import json

@dataclass
class ToolCallRecord:
    """工具调用记录"""
    timestamp: str
    tool_name: str
    arguments: Dict
    result: Dict
    success: bool
    duration_ms: float

class ToolUsageMonitor:
    """工具使用监控"""

    def __init__(self):
        self.records: List[ToolCallRecord] = []
        self.metrics = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "by_tool": {}
        }

    def record(self, record: ToolCallRecord):
        """记录调用"""
        self.records.append(record)

        # 更新指标
        self.metrics["total_calls"] += 1
        if record.success:
            self.metrics["successful_calls"] += 1
        else:
            self.metrics["failed_calls"] += 1

        # 按工具统计
        if record.tool_name not in self.metrics["by_tool"]:
            self.metrics["by_tool"][record.tool_name] = {
                "calls": 0,
                "success": 0,
                "failed": 0,
                "avg_duration_ms": 0
            }

        tool_metrics = self.metrics["by_tool"][record.tool_name]
        tool_metrics["calls"] += 1
        if record.success:
            tool_metrics["success"] += 1
        else:
            tool_metrics["failed"] += 1

        # 更新平均耗时
        old_avg = tool_metrics["avg_duration_ms"]
        n = tool_metrics["calls"]
        tool_metrics["avg_duration_ms"] = old_avg + (record.duration_ms - old_avg) / n

    def get_summary(self) -> Dict:
        """获取摘要"""
        return {
            "total_calls": self.metrics["total_calls"],
            "success_rate": (
                self.metrics["successful_calls"] / self.metrics["total_calls"]
                if self.metrics["total_calls"] > 0 else 0
            ),
            "by_tool": self.metrics["by_tool"]
        }

    def get_recent_errors(self, limit: int = 10) -> List[Dict]:
        """获取最近的错误"""
        errors = [r for r in self.records if not r.success]
        return [
            {
                "timestamp": r.timestamp,
                "tool": r.tool_name,
                "error": r.result.get("error")
            }
            for r in errors[-limit:]
        ]

    def export_to_json(self, filepath: str):
        """导出到JSON"""
        data = {
            "metrics": self.metrics,
            "records": [
                {
                    "timestamp": r.timestamp,
                    "tool": r.tool_name,
                    "arguments": r.arguments,
                    "success": r.success,
                    "duration_ms": r.duration_ms
                }
                for r in self.records
            ]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

class MonitoredToolExecutor:
    """带监控的工具执行器"""

    def __init__(self, executor: ToolExecutor, monitor: ToolUsageMonitor):
        self.executor = executor
        self.monitor = monitor

    async def execute(self, tool_name: str, arguments: Dict) -> Dict:
        """执行并记录"""
        import time

        start_time = time.time()
        result = await self.executor.execute(tool_name, arguments)
        duration_ms = (time.time() - start_time) * 1000

        record = ToolCallRecord(
            timestamp=datetime.now().isoformat(),
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            success=result["success"],
            duration_ms=duration_ms
        )

        self.monitor.record(record)

        return result

# 使用示例
async def demo_monitored():
    registry = ToolRegistry()
    executor = ToolExecutor(registry)
    monitor = ToolUsageMonitor()
    monitored_executor = MonitoredToolExecutor(executor, monitor)

    # 执行一些调用
    await monitored_executor.execute("get_weather", {"city": "北京"})
    await monitored_executor.execute("calculate", {"expression": "1+1"})
    await monitored_executor.execute("search_web", {"query": "test"})

    # 获取统计
    print(monitor.get_summary())
```

---

## 五、最佳实践

### 5.1 工具设计原则

| 原则 | 说明 |
|------|------|
| **单一职责** | 每个工具只做一件事 |
| **清晰命名** | 名称应反映功能 |
| **完整文档** | 提供详细描述和示例 |
| **合理参数** | 最小化必需参数 |

### 5.2 错误处理

- 提供有意义的错误消息
- 实现适当的重试策略
- 记录错误日志
- 提供降级方案

### 5.3 安全考虑

- 验证所有输入
- 限制敏感操作
- 实施访问控制
- 记录审计日志

---

## 六、总结

高级工具使用的核心要素：

1. **清晰的定义**：工具描述和参数要明确
2. **健壮的执行**：错误处理和重试机制
3. **智能的编排**：工具链和并行调用
4. **完善的监控**：记录和分析使用情况
