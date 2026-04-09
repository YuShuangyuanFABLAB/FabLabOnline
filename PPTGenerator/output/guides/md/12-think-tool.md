# 思考工具（The Think Tool）

> 来源：https://www.anthropic.com/engineering/think-tool
> 发布日期：2025-03-20

---

## 一、思考工具概述

### 1.1 什么是思考工具

思考工具是一种让模型在进行响应前进行内部"思考"的机制。它允许模型在生成最终答案前，先进行推理、规划和自我检查。

### 1.2 为什么需要思考工具

| 问题 | 思考工具如何解决 |
|------|------------------|
| **推理不完整** | 允许分步推理 |
| **遗漏条件** | 系统性检查 |
| **格式错误** | 先规划后输出 |
| **不一致性** | 自我验证 |

### 1.3 工作原理

```
用户输入
    ↓
[思考阶段]
├── 理解问题
├── 收集信息
├── 规划回答
├── 验证逻辑
└── 检查约束
    ↓
[输出阶段]
└── 生成最终答案
```

---

## 二、思考模式

### 2.1 链式思考（Chain of Thought）

逐步推理，每一步都明确展示。

### 2.2 自我反思（Self-Reflection）

生成答案后自我检查和修正。

### 2.3 分解思考（Decomposition）

将复杂问题分解为子问题。

---

## 三、实战案例

### 案例1：实现基础思考工具

**场景**：为LLM添加思考能力

**解决方案**：

```python
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import json

class ThinkingStage(Enum):
    """思考阶段"""
    UNDERSTAND = "understand"
    ANALYZE = "analyze"
    PLAN = "plan"
    EXECUTE = "execute"
    VERIFY = "verify"

@dataclass
class ThinkingStep:
    """思考步骤"""
    stage: ThinkingStage
    thought: str
    action: Optional[str] = None
    result: Optional[str] = None

class ThinkTool:
    """思考工具"""

    def __init__(self, llm_client):
        self.llm = llm_client
        self.thinking_history: List[ThinkingStep] = []

    async def think(self, context: str, task: str) -> Dict:
        """执行思考过程"""
        self.thinking_history = []

        # 阶段1：理解问题
        understanding = await self._understand(context, task)
        self.thinking_history.append(understanding)

        # 阶段2：分析
        analysis = await self._analyze(understanding.result)
        self.thinking_history.append(analysis)

        # 阶段3：规划
        plan = await self._plan(analysis.result)
        self.thinking_history.append(plan)

        # 阶段4：执行规划
        execution = await self._execute(plan.result)
        self.thinking_history.append(execution)

        # 阶段5：验证
        verification = await self._verify(execution.result)
        self.thinking_history.append(verification)

        return {
            "thinking_process": [
                {
                    "stage": step.stage.value,
                    "thought": step.thought,
                    "result": step.result
                }
                for step in self.thinking_history
            ],
            "final_result": verification.result
        }

    async def _understand(self, context: str, task: str) -> ThinkingStep:
        """理解问题"""
        prompt = f"""
上下文：{context}

任务：{task}

请理解上述任务，回答以下问题：
1. 任务的核心目标是什么？
2. 有哪些约束条件？
3. 需要什么信息？

以JSON格式返回你的理解。
"""
        response = await self.llm.generate(prompt)

        return ThinkingStep(
            stage=ThinkingStage.UNDERSTAND,
            thought="分析任务的核心要素",
            result=response
        )

    async def _analyze(self, understanding: str) -> ThinkingStep:
        """分析问题"""
        prompt = f"""
基于以下理解：
{understanding}

请分析：
1. 问题的关键组成部分
2. 各部分之间的关系
3. 潜在的挑战和解决方案

以JSON格式返回分析结果。
"""
        response = await self.llm.generate(prompt)

        return ThinkingStep(
            stage=ThinkingStage.ANALYZE,
            thought="分解和分析问题结构",
            result=response
        )

    async def _plan(self, analysis: str) -> ThinkingStep:
        """规划解决方案"""
        prompt = f"""
基于以下分析：
{analysis}

请制定详细的解决计划：
1. 列出所有步骤
2. 标注步骤之间的依赖关系
3. 预期每个步骤的输出

以JSON格式返回计划。
"""
        response = await self.llm.generate(prompt)

        return ThinkingStep(
            stage=ThinkingStage.PLAN,
            thought="制定执行计划",
            result=response
        )

    async def _execute(self, plan: str) -> ThinkingStep:
        """执行计划"""
        prompt = f"""
执行以下计划：
{plan}

请逐步执行，记录每一步的结果。
"""
        response = await self.llm.generate(prompt)

        return ThinkingStep(
            stage=ThinkingStage.EXECUTE,
            thought="执行解决计划",
            result=response
        )

    async def _verify(self, execution_result: str) -> ThinkingStep:
        """验证结果"""
        prompt = f"""
验证以下执行结果：
{execution_result}

请检查：
1. 是否完成了所有任务目标
2. 是否满足所有约束条件
3. 结果的准确性和完整性

如发现问题，请提供修正建议。
"""
        response = await self.llm.generate(prompt)

        return ThinkingStep(
            stage=ThinkingStage.VERIFY,
            thought="验证执行结果",
            result=response
        )

    def get_thinking_summary(self) -> str:
        """获取思考摘要"""
        summary_parts = []

        for step in self.thinking_history:
            summary_parts.append(f"""
### {step.stage.value.upper()}
{step.thought}
结果：{step.result[:200]}...
""")

        return "\n".join(summary_parts)

# 使用示例
async def demo_think_tool():
    class MockLLM:
        async def generate(self, prompt):
            return f"对提示的分析结果..."

    think = ThinkTool(MockLLM())

    result = await think.think(
        context="用户想预订明天下午3点的会议室",
        task="检查会议室可用性并完成预订"
    )

    print("思考过程:")
    for step in result["thinking_process"]:
        print(f"  {step['stage']}: {step['thought']}")

    print(f"\n最终结果: {result['final_result']}")

# asyncio.run(demo_think_tool())
```

---

### 案例2：带自我修正的思考

**场景**：实现能自我修正的思考过程

**解决方案**：

```python
class SelfCorrectingThinker:
    """带自我修正的思考者"""

    def __init__(self, llm_client, max_corrections: int = 3):
        self.llm = llm_client
        self.max_corrections = max_corrections

    async def think_and_correct(self, question: str) -> Dict:
        """思考并自我修正"""
        # 初始思考
        initial_thought = await self._initial_think(question)

        # 迭代修正
        current_thought = initial_thought
        corrections = []

        for i in range(self.max_corrections):
            # 检查是否需要修正
            critique = await self._critique(current_thought, question)

            if critique["needs_correction"]:
                # 应用修正
                correction = await self._correct(
                    current_thought,
                    critique["issues"]
                )
                corrections.append({
                    "iteration": i + 1,
                    "issues": critique["issues"],
                    "correction": correction
                })
                current_thought = correction
            else:
                break

        return {
            "initial_thought": initial_thought,
            "corrections": corrections,
            "final_thought": current_thought,
            "total_iterations": len(corrections) + 1
        }

    async def _initial_think(self, question: str) -> str:
        """初始思考"""
        prompt = f"""
问题：{question}

请进行深度思考，逐步分析问题并给出答案。
展示你的推理过程。

思考过程：
"""
        return await self.llm.generate(prompt)

    async def _critique(self, thought: str, question: str) -> Dict:
        """批评当前思考"""
        prompt = f"""
原问题：{question}

当前思考：
{thought}

请审视以上思考，检查：
1. 逻辑是否正确？
2. 是否遗漏重要信息？
3. 推理是否有漏洞？
4. 结论是否合理？

如果需要修正，列出具体问题。
如果不需要修正，说明"无需修正"。

以JSON格式返回：
{{
    "needs_correction": true/false,
    "issues": ["问题1", "问题2"],
    "strengths": ["优点1"]
}}
"""
        response = await self.llm.generate(prompt)
        return json.loads(response)

    async def _correct(self, thought: str, issues: List[str]) -> str:
        """修正思考"""
        prompt = f"""
当前思考：
{thought}

发现的问题：
{json.dumps(issues, ensure_ascii=False, indent=2)}

请修正上述问题，提供改进后的思考过程。
"""
        return await self.llm.generate(prompt)

# 使用示例
async def demo_self_correcting():
    class MockLLM:
        async def generate(self, prompt):
            if "审视" in prompt:
                return json.dumps({
                    "needs_correction": True,
                    "issues": ["遗漏了边界情况", "推理有一处逻辑跳跃"],
                    "strengths": ["结构清晰"]
                })
            return f"思考内容..."

    thinker = SelfCorrectingThinker(MockLLM())
    result = await thinker.think_and_correct(
        "如何设计一个高可用的分布式系统？"
    )

    print(f"进行了{result['total_iterations']}轮迭代")
    print(f"修正次数：{len(result['corrections'])}")
```

---

### 案例3：结构化思考框架

**场景**：使用固定框架进行思考

**解决方案**：

```python
from typing import List, Dict, Any
from abc import ABC, abstractmethod

class ThinkingFramework(ABC):
    """思考框架基类"""

    @abstractmethod
    async def think(self, question: str) -> Dict:
        pass

class SoarFramework(ThinkingFramework):
    """SOAR思考框架"""

    def __init__(self, llm_client):
        self.llm = llm_client

    async def think(self, question: str) -> Dict:
        """SOAR：Situation, Obstacle, Action, Result"""
        return {
            "framework": "SOAR",
            "situation": await self._situation(question),
            "obstacle": await self._obstacle(question),
            "action": await self._action(question),
            "result": await self._result(question)
        }

    async def _situation(self, question: str) -> str:
        return await self.llm.generate(f"描述当前情况：{question}")

    async def _obstacle(self, question: str) -> str:
        return await self.llm.generate(f"识别主要障碍：{question}")

    async def _action(self, question: str) -> str:
        return await self.llm.generate(f"制定行动方案：{question}")

    async def _result(self, question: str) -> str:
        return await self.llm.generate(f"预期结果：{question}")

class SmartFramework(ThinkingFramework):
    """SMART思考框架"""

    def __init__(self, llm_client):
        self.llm = llm_client

    async def think(self, goal: str) -> Dict:
        """SMART：Specific, Measurable, Achievable, Relevant, Time-bound"""
        return {
            "framework": "SMART",
            "specific": await self._specific(goal),
            "measurable": await self._measurable(goal),
            "achievable": await self._achievable(goal),
            "relevant": await self._relevant(goal),
            "time_bound": await self._time_bound(goal)
        }

    async def _specific(self, goal: str) -> str:
        prompt = f"目标：{goal}\n具体化这个目标，明确要达成什么。"
        return await self.llm.generate(prompt)

    async def _measurable(self, goal: str) -> str:
        prompt = f"目标：{goal}\n定义如何衡量目标的完成程度。"
        return await self.llm.generate(prompt)

    async def _achievable(self, goal: str) -> str:
        prompt = f"目标：{goal}\n评估目标的可实现性。"
        return await self.llm.generate(prompt)

    async def _relevant(self, goal: str) -> str:
        prompt = f"目标：{goal}\n说明这个目标为什么重要。"
        return await self.llm.generate(prompt)

    async def _time_bound(self, goal: str) -> str:
        prompt = f"目标：{goal}\n设定时间限制和里程碑。"
        return await self.llm.generate(prompt)

class FirstPrinciplesFramework(ThinkingFramework):
    """第一性原理思考框架"""

    def __init__(self, llm_client):
        self.llm = llm_client

    async def think(self, problem: str) -> Dict:
        """第一性原理分析"""
        # 1. 分解问题
        decomposition = await self._decompose(problem)

        # 2. 识别基本原理
        principles = await self._identify_principles(decomposition)

        # 3. 重新组合
        synthesis = await self._synthesize(principles)

        return {
            "framework": "FirstPrinciples",
            "decomposition": decomposition,
            "principles": principles,
            "synthesis": synthesis
        }

    async def _decompose(self, problem: str) -> Dict:
        prompt = f"""
问题：{problem}

将这个问题分解为最基本的组成部分。
识别所有假设和前提。
"""
        return await self.llm.generate(prompt)

    async def _identify_principles(self, decomposition: Dict) -> List[str]:
        prompt = f"""
分解结果：{decomposition}

识别不可再分的基本原理和真理。
忽略类比和惯例。
"""
        return await self.llm.generate(prompt)

    async def _synthesize(self, principles: List[str]) -> str:
        prompt = f"""
基本原理：{principles}

从这些基本原理出发，重新构建解决方案。
"""
        return await self.llm.generate(prompt)

# 使用示例
async def demo_frameworks():
    class MockLLM:
        async def generate(self, prompt):
            return f"对提示的思考结果..."

    llm = MockLLM()

    # 使用SOAR框架
    soar = SoarFramework(llm)
    soar_result = await soar.think("如何提高团队效率？")
    print("SOAR结果:", soar_result)

    # 使用SMART框架
    smart = SmartFramework(llm)
    smart_result = await smart.think("学习新技能")
    print("SMART结果:", smart_result)

    # 使用第一性原理
    fp = FirstPrinciplesFramework(llm)
    fp_result = await fp.think("如何降低成本？")
    print("第一性原理结果:", fp_result)
```

---

### 案例4：多步骤问题分解

**场景**：将复杂问题分解为子问题

**解决方案**：

```python
class ProblemDecomposer:
    """问题分解器"""

    def __init__(self, llm_client):
        self.llm = llm_client

    async def decompose(self, problem: str, depth: int = 3) -> Dict:
        """分解问题"""
        tree = {
            "problem": problem,
            "sub_problems": [],
            "depth": 0
        }

        await self._decompose_recursive(tree, depth)

        return tree

    async def _decompose_recursive(self, node: Dict, max_depth: int):
        """递归分解"""
        if node["depth"] >= max_depth:
            return

        # 生成子问题
        sub_problems = await self._generate_sub_problems(node["problem"])

        for sub in sub_problems:
            sub_node = {
                "problem": sub,
                "sub_problems": [],
                "depth": node["depth"] + 1
            }
            node["sub_problems"].append(sub_node)

            # 递归分解
            await self._decompose_recursive(sub_node, max_depth)

    async def _generate_sub_problems(self, problem: str) -> List[str]:
        """生成子问题"""
        prompt = f"""
问题：{problem}

将这个问题分解为2-4个子问题。
每个子问题应该是原问题的一个方面。

以JSON数组格式返回：["子问题1", "子问题2", ...]
"""
        response = await self.llm.generate(prompt)

        try:
            return json.loads(response)
        except:
            return []

    async def solve_decomposed(self, tree: Dict) -> Dict:
        """解决分解后的问题"""
        # 自底向上解决
        await self._solve_recursive(tree)

        return {
            "problem": tree["problem"],
            "solution": tree.get("solution"),
            "sub_solutions": tree.get("sub_solutions", [])
        }

    async def _solve_recursive(self, node: Dict):
        """递归解决"""
        # 先解决子问题
        sub_solutions = []
        for sub_node in node["sub_problems"]:
            await self._solve_recursive(sub_node)
            sub_solutions.append({
                "problem": sub_node["problem"],
                "solution": sub_node.get("solution")
            })

        node["sub_solutions"] = sub_solutions

        # 基于子解决方案解决当前问题
        if sub_solutions:
            prompt = f"""
问题：{node['problem']}

子问题及其解决方案：
{json.dumps(sub_solutions, ensure_ascii=False, indent=2)}

基于子解决方案，给出原问题的综合解决方案。
"""
            node["solution"] = await self.llm.generate(prompt)
        else:
            # 叶子节点直接解决
            node["solution"] = await self.llm.generate(
                f"解决问题：{node['problem']}"
            )

# 使用示例
async def demo_decomposer():
    class MockLLM:
        async def generate(self, prompt):
            if "[" in prompt and "]" in prompt:
                return '["子问题1", "子问题2"]'
            return "解决方案..."

    decomposer = ProblemDecomposer(MockLLM())

    # 分解问题
    tree = await decomposer.decompose(
        "如何设计一个电商平台？",
        depth=2
    )

    # 解决问题
    result = await decomposer.solve_decomposed(tree)

    print(f"原问题: {result['problem']}")
    print(f"解决方案: {result['solution']}")
```

---

### 案例5：思考工具与工具调用结合

**场景**：将思考过程与工具调用结合

**解决方案**：

```python
from typing import Dict, List, Any
import json

class ThinkingWithTools:
    """带工具的思考"""

    def __init__(self, llm_client, tool_registry):
        self.llm = llm_client
        self.tools = tool_registry

    async def solve(self, question: str) -> Dict:
        """使用工具辅助思考"""
        state = {
            "question": question,
            "thoughts": [],
            "tool_calls": [],
            "current_understanding": ""
        }

        # 迭代思考
        for iteration in range(10):
            # 思考下一步
            thought = await self._think(state)
            state["thoughts"].append(thought)

            # 决定行动
            action = await self._decide_action(state)

            if action["type"] == "answer":
                return {
                    "answer": action["answer"],
                    "reasoning": state["thoughts"],
                    "tool_calls": state["tool_calls"]
                }

            elif action["type"] == "tool_call":
                # 执行工具
                tool_result = await self._execute_tool(
                    action["tool"],
                    action["arguments"]
                )
                state["tool_calls"].append({
                    "tool": action["tool"],
                    "arguments": action["arguments"],
                    "result": tool_result
                })

            elif action["type"] == "think_more":
                # 继续思考
                continue

        return {
            "answer": "未能在迭代限制内完成",
            "reasoning": state["thoughts"],
            "tool_calls": state["tool_calls"]
        }

    async def _think(self, state: Dict) -> str:
        """生成思考"""
        prompt = f"""
问题：{state['question']}

当前理解：{state['current_understanding']}

已有思考：
{chr(10).join(f'{i+1}. {t}' for i, t in enumerate(state['thoughts']))}

工具调用结果：
{json.dumps(state['tool_calls'], ensure_ascii=False, indent=2)}

请继续思考，分析当前状态并确定下一步。
"""
        return await self.llm.generate(prompt)

    async def _decide_action(self, state: Dict) -> Dict:
        """决定下一步行动"""
        available_tools = self.tools.list_tools()

        prompt = f"""
问题：{state['question']}

最新思考：{state['thoughts'][-1] if state['thoughts'] else '无'}

可用工具：
{json.dumps([t['name'] for t in available_tools], ensure_ascii=False)}

请决定下一步行动。返回JSON：
{{
    "type": "answer" | "tool_call" | "think_more",
    "answer": "如果type是answer，这里写最终答案",
    "tool": "如果type是tool_call，这里写工具名",
    "arguments": {{"如果type是tool_call，这里写参数"}}
}}
"""
        response = await self.llm.generate(prompt)
        return json.loads(response)

    async def _execute_tool(self, tool_name: str, arguments: Dict) -> Any:
        """执行工具"""
        tool = self.tools.get(tool_name)
        if tool:
            return await tool.handler(**arguments)
        return {"error": "工具不存在"}

# 使用示例
async def demo_thinking_with_tools():
    # 设置工具注册表
    registry = ToolRegistry()
    # ... 注册工具 ...

    class MockLLM:
        def __init__(self):
            self.call_count = 0

        async def generate(self, prompt):
            self.call_count += 1
            if "决定下一步" in prompt:
                if self.call_count > 3:
                    return json.dumps({
                        "type": "answer",
                        "answer": "这是最终答案"
                    })
                return json.dumps({
                    "type": "think_more"
                })
            return "思考内容..."

    thinker = ThinkingWithTools(MockLLM(), registry)
    result = await thinker.solve("如何提高销售额？")

    print(f"答案: {result['answer']}")
    print(f"思考步骤: {len(result['reasoning'])}")
```

---

## 四、最佳实践

### 4.1 思考工具设计原则

| 原则 | 说明 |
|------|------|
| **结构化** | 使用明确的思考框架 |
| **可追溯** | 记录思考过程 |
| **可中断** | 允许人工干预 |
| **可验证** | 支持结果验证 |

### 4.2 思考提示技巧

- 明确思考步骤
- 提供足够上下文
- 要求结构化输出
- 鼓励自我反思

### 4.3 常见陷阱

| 陷阱 | 解决方案 |
|------|----------|
| 过度思考 | 设置迭代限制 |
| 偏离主题 | 定期回归问题 |
| 无效循环 | 添加进展检测 |
| 过度依赖 | 平衡思考与行动 |

---

## 五、总结

思考工具的核心价值：

1. **提升推理质量**：系统性的思考过程
2. **增加透明度**：可见的推理过程
3. **自我修正**：发现和修正错误
4. **复杂问题求解**：分解和逐步解决
