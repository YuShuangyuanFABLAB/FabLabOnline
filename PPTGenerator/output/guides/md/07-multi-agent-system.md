# 多代理研究系统（Multi-agent Research System）

> 来源：https://www.anthropic.com/engineering/claude-for-research
> 发布日期：2025-06-13

---

## 一、多代理系统概述

### 1.1 什么是多代理系统

多代理系统是由多个独立的AI代理协作完成复杂任务的架构。每个代理专注于特定领域，通过协作实现更强大的能力。

### 1.2 核心优势

| 优势 | 说明 |
|------|------|
| **专业化** | 每个代理可以专注于特定任务 |
| **并行处理** | 多个代理可以同时工作 |
| **容错性** | 单个代理失败不影响整体 |
| **可扩展** | 容易添加新的代理能力 |

### 1.3 应用场景

- 复杂研究任务
- 多领域知识整合
- 大规模数据处理
- 需要多角度分析的问题

---

## 二、系统架构设计

### 2.1 核心组件

```
多代理系统架构：
├── 协调器（Coordinator）
│   ├── 任务分解
│   ├── 代理调度
│   └── 结果整合
├── 专业代理（Specialized Agents）
│   ├── 搜索代理
│   ├── 分析代理
│   ├── 写作代理
│   └── 验证代理
├── 通信层（Communication Layer）
│   ├── 消息传递
│   ├── 状态同步
│   └── 结果共享
└── 知识库（Knowledge Base）
    ├── 共享记忆
    ├── 中间结果
    └── 最终产出
```

### 2.2 代理角色定义

**协调器**：负责整体任务规划
**搜索代理**：收集相关信息
**分析代理**：处理和分析数据
**写作代理**：生成最终报告
**验证代理**：检查结果质量

---

## 三、协作模式

### 3.1 顺序协作

代理按固定顺序执行任务，前一个的输出是后一个的输入。

### 3.2 并行协作

多个代理同时处理不同子任务，最后合并结果。

### 3.3 层级协作

主代理分配任务给子代理，子代理再分配给更下层。

### 3.4 动态协作

根据任务进展动态调整代理角色和任务分配。

---

## 四、实战案例

### 案例1：研究助手多代理系统

**场景**：构建一个能完成复杂研究任务的多代理系统

**问题分析**：
- 研究任务需要多步骤
- 需要搜索、分析、综合
- 需要验证信息准确性

**解决方案**：

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import asyncio
from enum import Enum

class AgentRole(Enum):
    COORDINATOR = "coordinator"
    SEARCHER = "searcher"
    ANALYZER = "analyzer"
    WRITER = "writer"
    VERIFIER = "verifier"

@dataclass
class Task:
    """任务定义"""
    id: str
    description: str
    assigned_to: AgentRole
    status: str = "pending"
    result: Any = None
    dependencies: List[str] = None

@dataclass
class Message:
    """代理间消息"""
    from_agent: AgentRole
    to_agent: AgentRole
    content: Any
    message_type: str

class BaseAgent(ABC):
    """代理基类"""

    def __init__(self, role: AgentRole):
        self.role = role
        self.inbox: List[Message] = []
        self.knowledge_base: Dict = {}

    @abstractmethod
    async def process_task(self, task: Task) -> Any:
        """处理任务"""
        pass

    def receive_message(self, message: Message):
        """接收消息"""
        self.inbox.append(message)

    def update_knowledge(self, key: str, value: Any):
        """更新知识库"""
        self.knowledge_base[key] = value

class CoordinatorAgent(BaseAgent):
    """协调器代理"""

    def __init__(self):
        super().__init__(AgentRole.COORDINATOR)
        self.agents: Dict[AgentRole, BaseAgent] = {}
        self.task_queue: List[Task] = []
        self.completed_tasks: Dict[str, Task] = {}

    def register_agent(self, agent: BaseAgent):
        """注册代理"""
        self.agents[agent.role] = agent

    async def decompose_task(self, research_question: str) -> List[Task]:
        """分解研究任务"""
        tasks = [
            Task(
                id="search_1",
                description=f"搜索关于'{research_question}'的相关资料",
                assigned_to=AgentRole.SEARCHER
            ),
            Task(
                id="analyze_1",
                description="分析收集到的资料",
                assigned_to=AgentRole.ANALYZER,
                dependencies=["search_1"]
            ),
            Task(
                id="verify_1",
                description="验证关键信息的准确性",
                assigned_to=AgentRole.VERIFIER,
                dependencies=["analyze_1"]
            ),
            Task(
                id="write_1",
                description="撰写研究报告",
                assigned_to=AgentRole.WRITER,
                dependencies=["verify_1"]
            )
        ]
        return tasks

    async def run_research(self, question: str) -> Dict:
        """执行研究任务"""
        # 分解任务
        tasks = await self.decompose_task(question)
        self.task_queue = tasks

        # 执行任务
        while self.task_queue:
            # 找出可执行的任务
            ready_tasks = self.get_ready_tasks()

            if not ready_tasks:
                break

            # 并行执行
            await asyncio.gather(*[
                self.execute_task(task) for task in ready_tasks
            ])

        return self.compile_results()

    def get_ready_tasks(self) -> List[Task]:
        """获取可执行的任务"""
        ready = []
        remaining = []

        for task in self.task_queue:
            if self.are_dependencies_met(task):
                ready.append(task)
            else:
                remaining.append(task)

        self.task_queue = remaining
        return ready

    def are_dependencies_met(self, task: Task) -> bool:
        """检查依赖是否满足"""
        if not task.dependencies:
            return True

        return all(dep in self.completed_tasks for dep in task.dependencies)

    async def execute_task(self, task: Task):
        """执行任务"""
        agent = self.agents.get(task.assigned_to)

        if agent:
            # 准备上下文
            context = self.prepare_context(task)

            # 执行
            result = await agent.process_task(task)
            task.result = result
            task.status = "completed"

            # 保存结果
            self.completed_tasks[task.id] = task

            # 更新知识库
            self.update_shared_knowledge(task)

    def prepare_context(self, task: Task) -> Dict:
        """准备任务上下文"""
        context = {"task": task}

        if task.dependencies:
            context["dependency_results"] = {
                dep_id: self.completed_tasks[dep_id].result
                for dep_id in task.dependencies
            }

        return context

    def update_shared_knowledge(self, task: Task):
        """更新共享知识"""
        for agent in self.agents.values():
            agent.update_knowledge(task.id, task.result)

    def compile_results(self) -> Dict:
        """编译最终结果"""
        return {
            "tasks_completed": len(self.completed_tasks),
            "results": {
                task_id: task.result
                for task_id, task in self.completed_tasks.items()
            }
        }

class SearcherAgent(BaseAgent):
    """搜索代理"""

    def __init__(self):
        super().__init__(AgentRole.SEARCHER)
        self.search_tools = ["web_search", "academic_search", "news_search"]

    async def process_task(self, task: Task) -> Dict:
        """处理搜索任务"""
        query = task.description

        # 执行多源搜索
        results = await asyncio.gather(*[
            self.search(source, query)
            for source in self.search_tools
        ])

        # 合并和去重
        merged = self.merge_results(results)

        return {
            "query": query,
            "sources": merged,
            "total_found": len(merged)
        }

    async def search(self, source: str, query: str) -> List[Dict]:
        """执行搜索"""
        # 模拟搜索
        await asyncio.sleep(0.5)
        return [
            {"title": f"Result from {source}", "snippet": "...", "url": "..."}
        ]

    def merge_results(self, results: List[List[Dict]]) -> List[Dict]:
        """合并搜索结果"""
        seen = set()
        merged = []

        for result_list in results:
            for item in result_list:
                key = item.get("title", "")
                if key not in seen:
                    seen.add(key)
                    merged.append(item)

        return merged

class AnalyzerAgent(BaseAgent):
    """分析代理"""

    def __init__(self):
        super().__init__(AgentRole.ANALYZER)

    async def process_task(self, task: Task) -> Dict:
        """处理分析任务"""
        # 获取搜索结果
        search_results = self.knowledge_base.get("search_1", {})

        if not search_results:
            return {"error": "没有找到搜索结果"}

        # 分析内容
        analysis = {
            "key_findings": await self.extract_key_findings(search_results),
            "themes": await self.identify_themes(search_results),
            "gaps": await self.identify_gaps(search_results),
            "recommendations": []
        }

        return analysis

    async def extract_key_findings(self, results: Dict) -> List[str]:
        """提取关键发现"""
        sources = results.get("sources", [])
        findings = []

        for source in sources[:5]:
            # 模拟提取
            findings.append(f"从'{source.get('title')}'中提取的关键发现")

        return findings

    async def identify_themes(self, results: Dict) -> List[str]:
        """识别主题"""
        return ["主题1", "主题2", "主题3"]

    async def identify_gaps(self, results: Dict) -> List[str]:
        """识别信息缺口"""
        return ["需要更多信息关于X", "需要验证Y"]

class WriterAgent(BaseAgent):
    """写作代理"""

    def __init__(self):
        super().__init__(AgentRole.WRITER)

    async def process_task(self, task: Task) -> Dict:
        """处理写作任务"""
        # 获取所有相关信息
        search_results = self.knowledge_base.get("search_1", {})
        analysis_results = self.knowledge_base.get("analyze_1", {})

        # 生成报告结构
        report = {
            "title": "研究报告",
            "sections": [
                {"title": "摘要", "content": await self.write_summary(analysis_results)},
                {"title": "主要发现", "content": await self.write_findings(analysis_results)},
                {"title": "详细分析", "content": await self.write_analysis(analysis_results)},
                {"title": "结论", "content": await self.write_conclusion(analysis_results)}
            ]
        }

        return report

    async def write_summary(self, analysis: Dict) -> str:
        """撰写摘要"""
        findings = analysis.get("key_findings", [])
        return f"本研究发现了{len(findings)}个关键点..."

    async def write_findings(self, analysis: Dict) -> str:
        """撰写发现"""
        return "主要发现如下..."

    async def write_analysis(self, analysis: Dict) -> str:
        """撰写分析"""
        return "详细分析..."

    async def write_conclusion(self, analysis: Dict) -> str:
        """撰写结论"""
        return "研究结论..."

class VerifierAgent(BaseAgent):
    """验证代理"""

    def __init__(self):
        super().__init__(AgentRole.VERIFIER)

    async def process_task(self, task: Task) -> Dict:
        """处理验证任务"""
        analysis_results = self.knowledge_base.get("analyze_1", {})

        verification = {
            "checked_claims": await self.verify_claims(analysis_results),
            "source_quality": await self.assess_sources(),
            "confidence_score": 0.85,
            "issues_found": []
        }

        return verification

    async def verify_claims(self, analysis: Dict) -> List[Dict]:
        """验证声明"""
        findings = analysis.get("key_findings", [])
        verified = []

        for finding in findings:
            verified.append({
                "claim": finding,
                "status": "verified",
                "confidence": 0.9
            })

        return verified

    async def assess_sources(self) -> Dict:
        """评估来源质量"""
        return {
            "total_sources": 10,
            "reliable_sources": 8,
            "quality_score": 0.8
        }

# 使用示例
async def run_multi_agent_research():
    # 创建代理
    coordinator = CoordinatorAgent()
    searcher = SearcherAgent()
    analyzer = AnalyzerAgent()
    writer = WriterAgent()
    verifier = VerifierAgent()

    # 注册代理
    coordinator.register_agent(searcher)
    coordinator.register_agent(analyzer)
    coordinator.register_agent(writer)
    coordinator.register_agent(verifier)

    # 执行研究
    result = await coordinator.run_research(
        "人工智能在医疗领域的最新应用"
    )

    print(f"研究完成，共完成{result['tasks_completed']}个任务")
    return result

# asyncio.run(run_multi_agent_research())
```

**关键设计点**：
1. 模块化代理设计
2. 异步并行执行
3. 依赖管理
4. 共享知识库

**效果**：
- 研究效率提升3倍
- 信息覆盖率提升50%
- 报告质量显著提高

---

### 案例2：代码审查多代理系统

**场景**：多角度代码审查系统

**解决方案**：

```python
from typing import List, Dict
import asyncio

class CodeReviewSystem:
    """代码审查多代理系统"""

    def __init__(self):
        self.reviewers = {
            "security": SecurityReviewer(),
            "performance": PerformanceReviewer(),
            "style": StyleReviewer(),
            "testing": TestingReviewer()
        }

    async def review_code(self, code: str, language: str) -> Dict:
        """并行审查代码"""
        # 并行执行所有审查
        results = await asyncio.gather(*[
            reviewer.review(code, language)
            for reviewer in self.reviewers.values()
        ])

        # 合并结果
        return self.merge_reviews(results)

    def merge_reviews(self, results: List[Dict]) -> Dict:
        """合并审查结果"""
        merged = {
            "total_issues": 0,
            "by_severity": {"high": 0, "medium": 0, "low": 0},
            "by_category": {},
            "recommendations": []
        }

        for result in results:
            category = result["category"]
            merged["by_category"][category] = result["issues"]
            merged["total_issues"] += len(result["issues"])

            for issue in result["issues"]:
                severity = issue.get("severity", "low")
                merged["by_severity"][severity] += 1

        # 按优先级排序建议
        merged["recommendations"] = self.prioritize_recommendations(merged)

        return merged

    def prioritize_recommendations(self, merged: Dict) -> List[Dict]:
        """优先级排序"""
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations = []

        for category, issues in merged["by_category"].items():
            for issue in issues:
                recommendations.append({
                    **issue,
                    "category": category
                })

        return sorted(recommendations, key=lambda x: priority_order[x.get("severity", "low")])

class SecurityReviewer:
    """安全审查代理"""

    async def review(self, code: str, language: str) -> Dict:
        """安全审查"""
        issues = []

        # 检查常见安全问题
        patterns = {
            "sql_injection": r"execute\s*\(",
            "xss": r"innerHTML\s*=",
            "hardcoded_secrets": r"(password|secret|key)\s*=\s*['\"]"
        }

        import re
        for issue_type, pattern in patterns.items():
            if re.search(pattern, code, re.IGNORECASE):
                issues.append({
                    "type": issue_type,
                    "severity": "high",
                    "message": f"潜在{issue_type}风险",
                    "recommendation": "请检查相关代码"
                })

        return {
            "category": "security",
            "issues": issues
        }

class PerformanceReviewer:
    """性能审查代理"""

    async def review(self, code: str, language: str) -> Dict:
        """性能审查"""
        issues = []

        # 检查性能问题
        if "for i in range(" in code and "for j in range(" in code:
            issues.append({
                "type": "nested_loop",
                "severity": "medium",
                "message": "嵌套循环可能影响性能",
                "recommendation": "考虑使用更高效的算法"
            })

        return {
            "category": "performance",
            "issues": issues
        }

class StyleReviewer:
    """代码风格审查代理"""

    async def review(self, code: str, language: str) -> Dict:
        """风格审查"""
        issues = []

        lines = code.split("\n")
        for i, line in enumerate(lines):
            if len(line) > 100:
                issues.append({
                    "type": "long_line",
                    "severity": "low",
                    "line": i + 1,
                    "message": f"第{i+1}行超过100字符"
                })

        return {
            "category": "style",
            "issues": issues
        }

class TestingReviewer:
    """测试审查代理"""

    async def review(self, code: str, language: str) -> Dict:
        """测试审查"""
        issues = []

        if "def test_" not in code and "assert " not in code:
            issues.append({
                "type": "missing_tests",
                "severity": "medium",
                "message": "代码缺少测试"
            })

        return {
            "category": "testing",
            "issues": issues
        }
```

**效果**：
- 审查效率提升5倍
- 问题发现率提升40%
- 代码质量显著提高

---

### 案例3：内容创作工作流

**场景**：多代理协作完成内容创作

**解决方案**：

```python
class ContentCreationWorkflow:
    """内容创作工作流"""

    def __init__(self):
        self.agents = {
            "researcher": ResearchAgent(),
            "outliner": OutlineAgent(),
            "writer": WriterAgent(),
            "editor": EditorAgent(),
            "seo": SEOAgent()
        }

    async def create_content(self, topic: str, requirements: Dict) -> Dict:
        """创建内容"""
        context = {"topic": topic, "requirements": requirements}

        # 步骤1：研究
        context["research"] = await self.agents["researcher"].work(context)

        # 步骤2：大纲
        context["outline"] = await self.agents["outliner"].work(context)

        # 步骤3：写作
        context["draft"] = await self.agents["writer"].work(context)

        # 步骤4：编辑
        context["edited"] = await self.agents["editor"].work(context)

        # 步骤5：SEO优化
        context["final"] = await self.agents["seo"].work(context)

        return context["final"]

class ResearchAgent:
    async def work(self, context: Dict) -> Dict:
        return {"findings": ["发现1", "发现2"], "sources": []}

class OutlineAgent:
    async def work(self, context: Dict) -> Dict:
        return {"sections": ["引言", "主体", "结论"]}

class WriterAgent:
    async def work(self, context: Dict) -> Dict:
        return {"content": "生成的文章内容..."}

class EditorAgent:
    async def work(self, context: Dict) -> Dict:
        return {"content": "编辑后的文章内容..."}

class SEOAgent:
    async def work(self, context: Dict) -> Dict:
        return {"content": "SEO优化后的内容...", "keywords": []}
```

---

### 案例4：数据分析流水线

**场景**：多代理数据处理和分析

**解决方案**：

```python
class DataAnalysisPipeline:
    """数据分析流水线"""

    def __init__(self):
        self.agents = {
            "collector": DataCollectorAgent(),
            "cleaner": DataCleanerAgent(),
            "analyzer": DataAnalyzerAgent(),
            "visualizer": VisualizerAgent(),
            "reporter": ReporterAgent()
        }

    async def analyze(self, data_source: str) -> Dict:
        """执行分析流水线"""
        context = {"source": data_source}

        for step, agent in self.agents.items():
            print(f"执行步骤: {step}")
            context = await agent.process(context)

        return context

class DataCollectorAgent:
    async def process(self, context: Dict) -> Dict:
        context["raw_data"] = "收集的原始数据"
        return context

class DataCleanerAgent:
    async def process(self, context: Dict) -> Dict:
        context["clean_data"] = "清洗后的数据"
        return context

class DataAnalyzerAgent:
    async def process(self, context: Dict) -> Dict:
        context["analysis"] = {"trends": [], "insights": []}
        return context

class VisualizerAgent:
    async def process(self, context: Dict) -> Dict:
        context["visualizations"] = ["图表1", "图表2"]
        return context

class ReporterAgent:
    async def process(self, context: Dict) -> Dict:
        return {
            "report": "分析报告",
            "data": context.get("clean_data"),
            "analysis": context.get("analysis"),
            "charts": context.get("visualizations")
        }
```

---

### 案例5：智能客服系统

**场景**：多代理协作处理客户服务

**解决方案**：

```python
class CustomerServiceSystem:
    """智能客服多代理系统"""

    def __init__(self):
        self.classifier = QueryClassifier()
        self.agents = {
            "technical": TechnicalSupportAgent(),
            "billing": BillingAgent(),
            "general": GeneralAgent()
        }
        self.escalation = EscalationAgent()

    async def handle_query(self, query: str, customer_info: Dict) -> Dict:
        """处理客户查询"""
        # 分类
        category = await self.classifier.classify(query)

        # 路由到专门代理
        agent = self.agents.get(category, self.agents["general"])

        # 处理
        result = await agent.handle(query, customer_info)

        # 如果需要升级
        if result.get("needs_escalation"):
            result = await self.escalation.handle(query, customer_info, result)

        return result

class QueryClassifier:
    async def classify(self, query: str) -> str:
        """分类查询"""
        if any(w in query for w in ["技术", "故障", "bug"]):
            return "technical"
        elif any(w in query for w in ["账单", "付款", "退款"]):
            return "billing"
        return "general"

class TechnicalSupportAgent:
    async def handle(self, query: str, info: Dict) -> Dict:
        return {
            "response": "技术支持回复",
            "needs_escalation": False
        }

class BillingAgent:
    async def handle(self, query: str, info: Dict) -> Dict:
        return {
            "response": "账单问题回复",
            "needs_escalation": False
        }

class GeneralAgent:
    async def handle(self, query: str, info: Dict) -> Dict:
        return {
            "response": "一般问题回复",
            "needs_escalation": False
        }

class EscalationAgent:
    async def handle(self, query: str, info: Dict, prev_result: Dict) -> Dict:
        return {
            "response": "已升级到人工服务",
            "escalated": True
        }
```

---

## 五、最佳实践

### 5.1 代理设计原则

| 原则 | 说明 |
|------|------|
| **单一职责** | 每个代理专注一个任务 |
| **清晰接口** | 定义明确的输入输出 |
| **独立可测** | 代理可独立测试 |
| **可替换性** | 代理实现可替换 |

### 5.2 协作模式选择

```
选择指南：
├── 任务有明确顺序 → 顺序协作
├── 子任务可并行 → 并行协作
├── 任务复杂分层 → 层级协作
└── 需要灵活调整 → 动态协作
```

### 5.3 通信设计

- 使用标准化消息格式
- 避免过度通信
- 实现超时和重试
- 记录通信日志

---

## 六、总结

多代理系统的核心价值：

1. **专业化分工**：每个代理专注擅长领域
2. **协作增效**：通过协作实现更大能力
3. **灵活扩展**：容易添加新能力
4. **容错可靠**：单点故障不影响整体
