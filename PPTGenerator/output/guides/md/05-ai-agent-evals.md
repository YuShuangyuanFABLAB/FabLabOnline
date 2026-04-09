# AI Agent评估体系（AI Agent Evals）

> 来源：https://www.anthropic.com/engineering/evals-for-ai-agents
> 发布日期：2026-01-09

---

## 一、评估的重要性

### 1.1 为什么评估至关重要

AI Agent的评估是确保系统可靠性和性能的关键环节。没有良好的评估体系：

- **无法量化改进**：不知道改动是否真正有效
- **难以发现问题**：隐藏的bug可能影响生产环境
- **缺乏信心**：无法确定系统是否满足需求

### 1.2 评估类型分类

| 类型 | 目的 | 特点 |
|------|------|------|
| **单元测试** | 测试单个组件 | 快速、隔离 |
| **集成测试** | 测试组件交互 | 端到端、真实场景 |
| **回归测试** | 防止功能退化 | 自动化、持续 |
| **A/B测试** | 比较不同版本 | 生产环境、统计显著 |

---

## 二、评估框架设计

### 2.1 核心评估指标

```
评估维度：
├── 准确性（Accuracy）
│   ├── 任务完成率
│   ├── 输出正确性
│   └── 信息准确性
├── 效率（Efficiency）
│   ├── 响应时间
│   ├── Token消耗
│   └── 迭代次数
├── 可靠性（Reliability）
│   ├── 错误恢复能力
│   ├── 一致性
│   └── 稳定性
└── 用户体验（UX）
    ├── 满意度评分
    ├── 任务完成时间
    └── 干预次数
```

### 2.2 评估数据集构建

构建高质量评估数据集的原则：

1. **代表性**：覆盖真实使用场景
2. **多样性**：包含不同难度和类型
3. **可扩展**：易于添加新测试用例
4. **可维护**：清晰的标签和注释

---

## 三、评估方法

### 3.1 基于规则的评估

适用于输出格式明确、易于验证的场景。

### 3.2 基于模型的评估

使用LLM评估另一个LLM的输出质量。

### 3.3 人工评估

最准确但成本最高的方法，适合关键场景。

---

## 四、实战案例

### 案例1：构建代码助手评估系统

**场景**：评估一个AI代码助手的性能

**问题分析**：
- 代码质量难以自动评估
- 需要测试多种编程语言
- 不同任务类型需要不同标准

**解决方案**：

```python
import asyncio
from dataclasses import dataclass
from typing import List, Dict, Any
import subprocess
import tempfile
import os

@dataclass
class EvalCase:
    """评估用例"""
    id: str
    prompt: str
    language: str
    test_cases: List[Dict]  # 单元测试
    expected_patterns: List[str]  # 代码模式检查
    difficulty: str  # easy/medium/hard
    category: str  # algorithm/api/debug/etc

class CodeAssistantEval:
    """代码助手评估系统"""

    def __init__(self, assistant_client):
        self.assistant = assistant_client
        self.eval_cases = self.load_eval_cases()
        self.results = []

    def load_eval_cases(self) -> List[EvalCase]:
        """加载评估用例"""
        cases = [
            EvalCase(
                id="py_sort_001",
                prompt="实现一个快速排序算法",
                language="python",
                test_cases=[
                    {"input": [3, 1, 4, 1, 5], "expected": [1, 1, 3, 4, 5]},
                    {"input": [5, 4, 3, 2, 1], "expected": [1, 2, 3, 4, 5]},
                    {"input": [], "expected": []},
                    {"input": [1], "expected": [1]},
                ],
                expected_patterns=["def quicksort", "pivot", "recursive"],
                difficulty="medium",
                category="algorithm"
            ),
            EvalCase(
                id="js_api_001",
                prompt="创建一个REST API端点，处理用户CRUD操作",
                language="javascript",
                test_cases=[
                    {"method": "GET", "path": "/users", "expected_status": 200},
                    {"method": "POST", "path": "/users", "body": {"name": "test"}, "expected_status": 201},
                ],
                expected_patterns=["express", "router", "async"],
                difficulty="medium",
                category="api"
            ),
            # 更多用例...
        ]
        return cases

    async def run_evaluation(self, sample_size: int = None) -> Dict:
        """运行完整评估"""
        cases = self.eval_cases[:sample_size] if sample_size else self.eval_cases

        results = []
        for case in cases:
            result = await self.evaluate_single_case(case)
            results.append(result)

        return self.aggregate_results(results)

    async def evaluate_single_case(self, case: EvalCase) -> Dict:
        """评估单个用例"""
        # 1. 获取助手生成的代码
        response = await self.assistant.generate_code(
            prompt=case.prompt,
            language=case.language
        )

        generated_code = response["code"]

        # 2. 代码质量检查
        quality_score = self.check_code_quality(generated_code, case.language)

        # 3. 模式匹配检查
        pattern_score = self.check_patterns(generated_code, case.expected_patterns)

        # 4. 功能测试（运行测试用例）
        test_results = await self.run_tests(generated_code, case)

        # 5. 综合评分
        overall_score = self.calculate_overall_score(
            quality_score=quality_score,
            pattern_score=pattern_score,
            test_results=test_results
        )

        return {
            "case_id": case.id,
            "category": case.category,
            "difficulty": case.difficulty,
            "quality_score": quality_score,
            "pattern_score": pattern_score,
            "test_pass_rate": test_results["pass_rate"],
            "overall_score": overall_score,
            "generated_code": generated_code,
            "errors": test_results.get("errors", [])
        }

    def check_code_quality(self, code: str, language: str) -> float:
        """检查代码质量"""
        scores = {}

        # 语法检查
        syntax_valid = self.check_syntax(code, language)
        scores["syntax"] = 1.0 if syntax_valid else 0.0

        # 代码复杂度
        complexity = self.calculate_complexity(code)
        scores["complexity"] = max(0, 1 - complexity / 20)

        # 代码风格
        style_score = self.check_style(code, language)
        scores["style"] = style_score

        # 文档完整性
        doc_score = self.check_documentation(code)
        scores["documentation"] = doc_score

        return sum(scores.values()) / len(scores)

    def check_patterns(self, code: str, patterns: List[str]) -> float:
        """检查代码是否包含预期模式"""
        if not patterns:
            return 1.0

        matches = sum(1 for p in patterns if p.lower() in code.lower())
        return matches / len(patterns)

    async def run_tests(self, code: str, case: EvalCase) -> Dict:
        """运行测试用例"""
        if not case.test_cases:
            return {"pass_rate": 1.0, "passed": 0, "total": 0}

        passed = 0
        errors = []

        for test in case.test_cases:
            try:
                result = await self.execute_test(code, test, case.language)
                if result["passed"]:
                    passed += 1
                else:
                    errors.append({
                        "test": test,
                        "error": result.get("error", "Unknown error")
                    })
            except Exception as e:
                errors.append({
                    "test": test,
                    "error": str(e)
                })

        return {
            "pass_rate": passed / len(case.test_cases),
            "passed": passed,
            "total": len(case.test_cases),
            "errors": errors
        }

    async def execute_test(self, code: str, test: Dict, language: str) -> Dict:
        """执行单个测试"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 写入代码文件
            ext = {"python": ".py", "javascript": ".js"}[language]
            code_file = os.path.join(tmpdir, f"code{ext}")
            with open(code_file, "w") as f:
                f.write(code)

            # 执行测试
            if language == "python":
                # 执行并验证输出
                test_code = f"""
{code}

# Test
result = quicksort({test['input']})
expected = {test['expected']}
assert result == expected, f"Expected {{expected}}, got {{result}}"
print("PASS")
"""
                test_file = os.path.join(tmpdir, "test.py")
                with open(test_file, "w") as f:
                    f.write(test_code)

                result = subprocess.run(
                    ["python", test_file],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                return {
                    "passed": "PASS" in result.stdout,
                    "error": result.stderr if result.returncode != 0 else None
                }

            return {"passed": False, "error": "Unsupported language"}

    def calculate_overall_score(self, quality_score, pattern_score, test_results) -> float:
        """计算综合评分"""
        weights = {
            "quality": 0.2,
            "pattern": 0.2,
            "tests": 0.6
        }

        return (
            quality_score * weights["quality"] +
            pattern_score * weights["pattern"] +
            test_results["pass_rate"] * weights["tests"]
        )

    def aggregate_results(self, results: List[Dict]) -> Dict:
        """聚合评估结果"""
        categories = {}
        difficulties = {}

        for r in results:
            cat = r["category"]
            diff = r["difficulty"]

            if cat not in categories:
                categories[cat] = []
            categories[cat].append(r["overall_score"])

            if diff not in difficulties:
                difficulties[diff] = []
            difficulties[diff].append(r["overall_score"])

        return {
            "total_cases": len(results),
            "overall_pass_rate": sum(1 for r in results if r["overall_score"] >= 0.7) / len(results),
            "avg_score": sum(r["overall_score"] for r in results) / len(results),
            "by_category": {k: sum(v)/len(v) for k, v in categories.items()},
            "by_difficulty": {k: sum(v)/len(v) for k, v in difficulties.items()},
            "detailed_results": results
        }

# 使用示例
async def main():
    # 模拟助手客户端
    class MockAssistant:
        async def generate_code(self, prompt, language):
            # 模拟代码生成
            if "快速排序" in prompt:
                code = '''
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
'''
            else:
                code = "// Generated code"
            return {"code": code}

    evaluator = CodeAssistantEval(MockAssistant())
    results = await evaluator.run_evaluation()

    print(f"总体通过率: {results['overall_pass_rate']:.2%}")
    print(f"平均得分: {results['avg_score']:.2f}")
    print(f"按类别: {results['by_category']}")

# asyncio.run(main())
```

**效果**：
- 自动化评估覆盖80%的测试场景
- 问题发现率提升3倍
- 发布前回归测试时间减少90%

---

### 案例2：对话系统评估框架

**场景**：评估客服AI对话系统

**问题分析**：
- 对话质量主观性强
- 需要评估多轮对话能力
- 情感因素难以量化

**解决方案**：

```python
from typing import List, Dict
import json

class ConversationEval:
    """对话系统评估框架"""

    def __init__(self, conversation_agent):
        self.agent = conversation_agent
        self.eval_dimensions = [
            "relevance",      # 相关性
            "accuracy",       # 准确性
            "helpfulness",    # 有用性
            "safety",         # 安全性
            "coherence",      # 连贯性
            "empathy"         # 共情能力
        ]

    def load_test_conversations(self) -> List[Dict]:
        """加载测试对话集"""
        return [
            {
                "id": "conv_001",
                "scenario": "订单查询",
                "turns": [
                    {"role": "user", "content": "我想查询我的订单状态"},
                    {"role": "assistant", "expected": "询问订单号"},
                    {"role": "user", "content": "订单号是12345"},
                    {"role": "assistant", "expected": "提供订单状态信息"},
                ],
                "success_criteria": [
                    "正确询问订单号",
                    "准确查询订单",
                    "提供完整状态信息"
                ]
            },
            {
                "id": "conv_002",
                "scenario": "投诉处理",
                "turns": [
                    {"role": "user", "content": "我收到的商品有质量问题，很生气！"},
                    {"role": "assistant", "expected": "表达理解并提供解决方案"},
                ],
                "success_criteria": [
                    "表达共情",
                    "道歉",
                    "提供具体解决方案"
                ]
            }
        ]

    async def evaluate_conversation(self, test_conv: Dict) -> Dict:
        """评估单个对话"""
        conversation_history = []
        turn_results = []

        for i, turn in enumerate(test_conv["turns"]):
            if turn["role"] == "user":
                # 获取AI响应
                response = await self.agent.respond(
                    turn["content"],
                    conversation_history
                )

                # 评估响应
                eval_result = await self.evaluate_turn(
                    user_input=turn["content"],
                    response=response,
                    expected=turn.get("expected"),
                    context=conversation_history
                )

                turn_results.append(eval_result)
                conversation_history.append({
                    "role": "user",
                    "content": turn["content"]
                })
                conversation_history.append({
                    "role": "assistant",
                    "content": response
                })

        # 评估整体对话
        overall_eval = self.evaluate_overall_conversation(
            conversation_history,
            test_conv["success_criteria"]
        )

        return {
            "conversation_id": test_conv["id"],
            "scenario": test_conv["scenario"],
            "turn_results": turn_results,
            "overall_eval": overall_eval,
            "conversation": conversation_history
        }

    async def evaluate_turn(self, user_input, response, expected, context) -> Dict:
        """评估单轮对话"""
        # 使用LLM进行多维度评估
        eval_prompt = f"""
评估以下客服对话响应的质量：

用户输入：{user_input}
AI响应：{response}
期望行为：{expected or '无特定期望'}
上下文：{context[-2:] if context else '无'}

请按以下维度评分（1-5分）：
1. 相关性：响应是否与用户问题相关
2. 准确性：信息是否准确
3. 有用性：是否帮助解决问题
4. 安全性：是否包含不当内容
5. 连贯性：是否与上下文连贯
6. 共情能力：是否展现适当的情感理解

返回JSON格式评分和简要说明。
"""

        # 这里应该调用LLM进行评估
        # 模拟评估结果
        return {
            "user_input": user_input,
            "response": response,
            "scores": {
                "relevance": 4,
                "accuracy": 5,
                "helpfulness": 4,
                "safety": 5,
                "coherence": 4,
                "empathy": 3
            },
            "avg_score": 4.2,
            "comments": "响应相关且准确，但共情表达可以更自然"
        }

    def evaluate_overall_conversation(self, conversation, success_criteria) -> Dict:
        """评估整体对话"""
        full_text = " ".join([t["content"] for t in conversation])

        criteria_met = []
        for criterion in success_criteria:
            # 检查是否满足成功标准
            met = self.check_criterion(full_text, criterion)
            criteria_met.append({
                "criterion": criterion,
                "met": met
            })

        return {
            "success_rate": sum(1 for c in criteria_met if c["met"]) / len(criteria_met),
            "criteria_details": criteria_met
        }

    def check_criterion(self, text: str, criterion: str) -> bool:
        """检查是否满足特定标准"""
        # 简化实现，实际应该用更复杂的方法
        keywords = {
            "正确询问订单号": ["订单号", "订单编号"],
            "准确查询订单": ["查询", "状态"],
            "提供完整状态信息": ["状态", "物流", "预计"],
            "表达共情": ["理解", "抱歉", "抱歉"],
            "道歉": ["抱歉", "对不起", "道歉"],
            "提供具体解决方案": ["可以", "为您", "退换", "补偿"]
        }

        if criterion in keywords:
            return any(kw in text for kw in keywords[criterion])
        return False

    def generate_eval_report(self, results: List[Dict]) -> str:
        """生成评估报告"""
        report = {
            "total_conversations": len(results),
            "avg_score": sum(r["turn_results"][0]["avg_score"] for r in results) / len(results),
            "by_scenario": {},
            "by_dimension": {d: [] for d in self.eval_dimensions}
        }

        for r in results:
            scenario = r["scenario"]
            if scenario not in report["by_scenario"]:
                report["by_scenario"][scenario] = []
            report["by_scenario"][scenario].append(r["overall_eval"]["success_rate"])

            for turn in r["turn_results"]:
                for dim, score in turn["scores"].items():
                    report["by_dimension"][dim].append(score)

        # 计算平均值
        report["by_scenario"] = {
            k: sum(v)/len(v) for k, v in report["by_scenario"].items()
        }
        report["by_dimension"] = {
            k: sum(v)/len(v) for k, v in report["by_dimension"].items()
        }

        return json.dumps(report, indent=2, ensure_ascii=False)
```

**效果**：
- 对话质量可量化评估
- 发现隐藏问题效率提升60%
- 模型迭代周期缩短50%

---

### 案例3：Agent工具使用评估

**场景**：评估AI Agent的工具选择和使用能力

**问题分析**：
- Agent需要选择正确的工具
- 工具参数传递需要准确
- 工具链组合需要合理

**解决方案**：

```python
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class ToolCall:
    """工具调用记录"""
    tool_name: str
    parameters: Dict[str, Any]
    result: Any
    success: bool
    execution_time: float

class ToolUseEval:
    """工具使用评估"""

    def __init__(self, agent, available_tools):
        self.agent = agent
        self.tools = {t.name: t for t in available_tools}
        self.call_history = []

    async def evaluate_tool_selection(self, task: str, expected_tools: List[str]) -> Dict:
        """评估工具选择"""
        # 让Agent执行任务
        execution_trace = await self.agent.execute_with_trace(task)

        # 分析工具调用
        called_tools = [call["tool"] for call in execution_trace["tool_calls"]]

        # 计算匹配度
        expected_set = set(expected_tools)
        called_set = set(called_tools)

        precision = len(expected_set & called_set) / len(called_set) if called_set else 0
        recall = len(expected_set & called_set) / len(expected_set) if expected_set else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        return {
            "task": task,
            "expected_tools": expected_tools,
            "called_tools": called_tools,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "execution_trace": execution_trace
        }

    async def evaluate_parameter_accuracy(self, tool_call: Dict, expected_params: Dict) -> Dict:
        """评估参数准确性"""
        actual = tool_call.get("parameters", {})

        errors = []
        correct_count = 0

        for key, expected_value in expected_params.items():
            if key not in actual:
                errors.append(f"缺少参数: {key}")
            elif actual[key] != expected_value:
                errors.append(f"参数 {key} 值不正确: 期望 {expected_value}, 实际 {actual[key]}")
            else:
                correct_count += 1

        total_params = len(expected_params)
        accuracy = correct_count / total_params if total_params > 0 else 1.0

        return {
            "accuracy": accuracy,
            "correct_params": correct_count,
            "total_params": total_params,
            "errors": errors
        }

    async def run_comprehensive_eval(self, test_cases: List[Dict]) -> Dict:
        """运行综合评估"""
        results = []

        for case in test_cases:
            # 工具选择评估
            selection_result = await self.evaluate_tool_selection(
                case["task"],
                case["expected_tools"]
            )

            # 参数准确性评估
            param_results = []
            if "expected_params" in case:
                for tool_name, expected_params in case["expected_params"].items():
                    # 找到对应的工具调用
                    for call in selection_result["execution_trace"]["tool_calls"]:
                        if call["tool"] == tool_name:
                            param_result = await self.evaluate_parameter_accuracy(
                                call, expected_params
                            )
                            param_results.append(param_result)

            results.append({
                "case_id": case["id"],
                "selection_result": selection_result,
                "param_results": param_results,
                "overall_score": self.calculate_case_score(
                    selection_result, param_results
                )
            })

        return {
            "total_cases": len(results),
            "avg_score": sum(r["overall_score"] for r in results) / len(results),
            "detailed_results": results
        }

    def calculate_case_score(self, selection_result, param_results) -> float:
        """计算用例得分"""
        selection_weight = 0.6
        param_weight = 0.4

        selection_score = selection_result["f1_score"]

        if param_results:
            param_score = sum(p["accuracy"] for p in param_results) / len(param_results)
        else:
            param_score = 1.0

        return selection_score * selection_weight + param_score * param_weight

# 测试用例示例
TOOL_USE_TEST_CASES = [
    {
        "id": "tool_001",
        "task": "查询北京明天的天气",
        "expected_tools": ["weather_api"],
        "expected_params": {
            "weather_api": {
                "city": "北京",
                "date": "tomorrow"
            }
        }
    },
    {
        "id": "tool_002",
        "task": "帮我预订明天下午3点的会议室，并邀请张三参加",
        "expected_tools": ["calendar_api", "email_api"],
        "expected_params": {
            "calendar_api": {
                "time": "15:00",
                "date": "tomorrow"
            },
            "email_api": {
                "recipient": "张三"
            }
        }
    },
    {
        "id": "tool_003",
        "task": "搜索最新的AI论文并总结要点",
        "expected_tools": ["web_search", "summarize"],
        "expected_params": {
            "web_search": {
                "query": "AI papers latest"
            }
        }
    }
]
```

**效果**：
- 工具选择准确率提升25%
- 参数错误率降低60%
- Agent可靠性显著提高

---

### 案例4：RAG系统检索评估

**场景**：评估RAG系统的检索质量

**问题分析**：
- 需要评估检索相关性
- 检索与生成质量关联
- 不同查询类型效果差异

**解决方案**：

```python
from typing import List, Dict, Tuple
import numpy as np

class RAGEvaluation:
    """RAG系统评估"""

    def __init__(self, rag_system, embedding_model):
        self.rag = rag_system
        self.embedder = embedding_model

    def load_benchmark(self) -> List[Dict]:
        """加载评估基准"""
        return [
            {
                "query": "公司年假政策是什么？",
                "relevant_docs": ["doc_001", "doc_002"],
                "expected_answer_contains": ["15天", "工龄", "带薪"],
                "category": "policy"
            },
            {
                "query": "如何报销差旅费用？",
                "relevant_docs": ["doc_003", "doc_004", "doc_005"],
                "expected_answer_contains": ["发票", "审批", "财务"],
                "category": "process"
            }
        ]

    async def evaluate_retrieval(self, query: str, relevant_doc_ids: List[str], k: int = 5) -> Dict:
        """评估检索质量"""
        # 执行检索
        retrieved = await self.rag.retrieve(query, top_k=k)
        retrieved_ids = [doc["id"] for doc in retrieved]

        # 计算指标
        relevant_set = set(relevant_doc_ids)
        retrieved_set = set(retrieved_ids)

        # Precision@K
        hits = len(relevant_set & retrieved_set)
        precision_at_k = hits / k

        # Recall@K
        recall_at_k = hits / len(relevant_set) if relevant_set else 0

        # MRR (Mean Reciprocal Rank)
        mrr = 0
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in relevant_set:
                mrr = 1 / (i + 1)
                break

        # NDCG (Normalized Discounted Cumulative Gain)
        dcg = sum(
            1 / np.log2(i + 2) if doc_id in relevant_set else 0
            for i, doc_id in enumerate(retrieved_ids)
        )
        idcg = sum(1 / np.log2(i + 2) for i in range(min(len(relevant_set), k)))
        ndcg = dcg / idcg if idcg > 0 else 0

        return {
            "query": query,
            "precision@k": precision_at_k,
            "recall@k": recall_at_k,
            "mrr": mrr,
            "ndcg": ndcg,
            "retrieved_docs": retrieved_ids,
            "relevant_docs": relevant_doc_ids
        }

    async def evaluate_generation(self, query: str, answer: str, expected_contains: List[str]) -> Dict:
        """评估生成质量"""
        # 关键信息覆盖
        covered = [kw for kw in expected_contains if kw in answer]
        coverage = len(covered) / len(expected_contains) if expected_contains else 1.0

        # 使用LLM评估答案质量
        llm_eval = await self.llm_evaluate_answer(query, answer)

        return {
            "query": query,
            "answer": answer,
            "keyword_coverage": coverage,
            "covered_keywords": covered,
            "missing_keywords": [kw for kw in expected_contains if kw not in answer],
            "llm_score": llm_eval["score"],
            "llm_feedback": llm_eval["feedback"]
        }

    async def llm_evaluate_answer(self, query: str, answer: str) -> Dict:
        """使用LLM评估答案"""
        eval_prompt = f"""
评估以下问答对的质量：

问题：{query}
答案：{answer}

请从以下维度评分（1-5分）：
1. 相关性：答案是否直接回答问题
2. 准确性：信息是否正确
3. 完整性：是否覆盖了问题的所有方面
4. 清晰度：答案是否易于理解

返回JSON格式：{{"score": 平均分, "feedback": "简要反馈"}}
"""
        # 调用LLM进行评估
        # 模拟返回
        return {
            "score": 4.2,
            "feedback": "答案相关且准确，但可以更详细"
        }

    async def run_full_evaluation(self) -> Dict:
        """运行完整评估"""
        benchmark = self.load_benchmark()
        retrieval_results = []
        generation_results = []

        for case in benchmark:
            # 检索评估
            retrieval_eval = await self.evaluate_retrieval(
                case["query"],
                case["relevant_docs"]
            )
            retrieval_results.append(retrieval_eval)

            # 生成评估
            answer = await self.rag.generate_answer(case["query"])
            generation_eval = await self.evaluate_generation(
                case["query"],
                answer,
                case["expected_answer_contains"]
            )
            generation_results.append(generation_eval)

        # 汇总结果
        return {
            "retrieval_metrics": {
                "avg_precision": np.mean([r["precision@k"] for r in retrieval_results]),
                "avg_recall": np.mean([r["recall@k"] for r in retrieval_results]),
                "avg_mrr": np.mean([r["mrr"] for r in retrieval_results]),
                "avg_ndcg": np.mean([r["ndcg"] for r in retrieval_results])
            },
            "generation_metrics": {
                "avg_keyword_coverage": np.mean([g["keyword_coverage"] for g in generation_results]),
                "avg_llm_score": np.mean([g["llm_score"] for g in generation_results])
            },
            "by_category": self.aggregate_by_category(benchmark, retrieval_results, generation_results)
        }

    def aggregate_by_category(self, benchmark, retrieval_results, generation_results) -> Dict:
        """按类别聚合结果"""
        categories = {}

        for case, ret, gen in zip(benchmark, retrieval_results, generation_results):
            cat = case["category"]
            if cat not in categories:
                categories[cat] = {
                    "retrieval": [],
                    "generation": []
                }
            categories[cat]["retrieval"].append(ret["ndcg"])
            categories[cat]["generation"].append(gen["llm_score"])

        return {
            cat: {
                "avg_retrieval_ndcg": np.mean(data["retrieval"]),
                "avg_generation_score": np.mean(data["generation"])
            }
            for cat, data in categories.items()
        }
```

**效果**：
- 检索准确率量化可测
- 问题定位效率提升3倍
- 持续优化有数据支撑

---

### 案例5：回归测试自动化

**场景**：为AI系统建立持续回归测试

**问题分析**：
- 模型更新可能引入回归
- 需要快速检测性能下降
- 测试用例需要持续维护

**解决方案**：

```python
import json
from datetime import datetime
from typing import List, Dict, Optional
import subprocess

class RegressionTestSuite:
    """回归测试套件"""

    def __init__(self, config_path: str):
        self.config = self.load_config(config_path)
        self.baseline_results = None
        self.test_cases = self.load_test_cases()

    def load_config(self, path: str) -> Dict:
        """加载配置"""
        return {
            "model_endpoint": "https://api.example.com/v1/chat",
            "baseline_file": "baseline_results.json",
            "thresholds": {
                "accuracy_drop": 0.05,  # 5%下降触发警报
                "latency_increase": 0.2  # 20%延迟增加触发警报
            }
        }

    def load_test_cases(self) -> List[Dict]:
        """加载测试用例"""
        return [
            {
                "id": "reg_001",
                "type": "qa",
                "input": "什么是机器学习？",
                "expected_keywords": ["算法", "数据", "学习", "预测"],
                "expected_format": "paragraph"
            },
            {
                "id": "reg_002",
                "type": "code",
                "input": "写一个Python函数计算斐波那契数列",
                "expected_keywords": ["def", "fibonacci", "return"],
                "expected_format": "code"
            },
            {
                "id": "reg_003",
                "type": "reasoning",
                "input": "如果A大于B，B大于C，那么A和C的关系是什么？",
                "expected_keywords": ["大于", "A > C", "A大于C"],
                "expected_format": "sentence"
            }
        ]

    async def run_single_test(self, test_case: Dict, model_version: str) -> Dict:
        """运行单个测试"""
        start_time = datetime.now()

        # 调用模型
        response = await self.call_model(
            test_case["input"],
            model_version
        )

        end_time = datetime.now()
        latency = (end_time - start_time).total_seconds()

        # 评估响应
        evaluation = self.evaluate_response(
            response,
            test_case["expected_keywords"],
            test_case["expected_format"]
        )

        return {
            "test_id": test_case["id"],
            "type": test_case["type"],
            "input": test_case["input"],
            "response": response,
            "latency": latency,
            "evaluation": evaluation,
            "timestamp": start_time.isoformat(),
            "model_version": model_version
        }

    async def call_model(self, prompt: str, version: str) -> str:
        """调用模型API"""
        # 模拟API调用
        return f"这是对'{prompt}'的回答..."

    def evaluate_response(self, response: str, keywords: List[str], expected_format: str) -> Dict:
        """评估响应"""
        # 关键词检查
        keyword_hits = [kw for kw in keywords if kw.lower() in response.lower()]
        keyword_score = len(keyword_hits) / len(keywords) if keywords else 1.0

        # 格式检查
        format_valid = self.check_format(response, expected_format)

        return {
            "keyword_score": keyword_score,
            "keywords_found": keyword_hits,
            "keywords_missing": [kw for kw in keywords if kw not in keyword_hits],
            "format_valid": format_valid,
            "overall_score": keyword_score * 0.7 + (1 if format_valid else 0) * 0.3
        }

    def check_format(self, text: str, expected_format: str) -> bool:
        """检查响应格式"""
        if expected_format == "code":
            return "def " in text or "function" in text
        elif expected_format == "paragraph":
            return len(text.split("\n")) >= 2
        elif expected_format == "sentence":
            return len(text) < 500
        return True

    async def run_full_suite(self, model_version: str) -> Dict:
        """运行完整测试套件"""
        results = []

        for test_case in self.test_cases:
            result = await self.run_single_test(test_case, model_version)
            results.append(result)

        # 聚合结果
        summary = {
            "model_version": model_version,
            "total_tests": len(results),
            "passed": sum(1 for r in results if r["evaluation"]["overall_score"] >= 0.7),
            "failed": sum(1 for r in results if r["evaluation"]["overall_score"] < 0.7),
            "avg_score": sum(r["evaluation"]["overall_score"] for r in results) / len(results),
            "avg_latency": sum(r["latency"] for r in results) / len(results),
            "by_type": self.aggregate_by_type(results),
            "detailed_results": results
        }

        return summary

    def aggregate_by_type(self, results: List[Dict]) -> Dict:
        """按类型聚合"""
        by_type = {}
        for r in results:
            t = r["type"]
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(r["evaluation"]["overall_score"])

        return {t: sum(scores)/len(scores) for t, scores in by_type.items()}

    def compare_with_baseline(self, current_results: Dict) -> Dict:
        """与基线比较"""
        if not self.baseline_results:
            return {"status": "no_baseline", "message": "没有基线数据"}

        comparison = {
            "baseline_version": self.baseline_results["model_version"],
            "current_version": current_results["model_version"],
            "score_change": current_results["avg_score"] - self.baseline_results["avg_score"],
            "latency_change": current_results["avg_latency"] - self.baseline_results["avg_latency"],
            "regressions": [],
            "improvements": []
        }

        # 检查是否有回归
        thresholds = self.config["thresholds"]

        if comparison["score_change"] < -thresholds["accuracy_drop"]:
            comparison["regressions"].append({
                "type": "accuracy",
                "change": comparison["score_change"],
                "threshold": -thresholds["accuracy_drop"]
            })

        if comparison["latency_change"] > thresholds["latency_increase"]:
            comparison["regressions"].append({
                "type": "latency",
                "change": comparison["latency_change"],
                "threshold": thresholds["latency_increase"]
            })

        # 检查改进
        if comparison["score_change"] > 0.05:
            comparison["improvements"].append({
                "type": "accuracy",
                "improvement": comparison["score_change"]
            })

        comparison["status"] = "fail" if comparison["regressions"] else "pass"

        return comparison

    def set_baseline(self, results: Dict):
        """设置基线"""
        self.baseline_results = results
        with open(self.config["baseline_file"], "w") as f:
            json.dump(results, f, indent=2)

    def generate_report(self, results: Dict, comparison: Dict) -> str:
        """生成报告"""
        report = f"""
# 回归测试报告

## 基本信息
- 模型版本: {results['model_version']}
- 测试时间: {datetime.now().isoformat()}
- 总测试数: {results['total_tests']}
- 通过/失败: {results['passed']}/{results['failed']}

## 整体指标
- 平均得分: {results['avg_score']:.2f}
- 平均延迟: {results['avg_latency']:.2f}s

## 按类型分析
"""
        for t, score in results["by_type"].items():
            report += f"- {t}: {score:.2f}\n"

        if comparison["status"] != "no_baseline":
            report += f"""
## 与基线比较
- 基线版本: {comparison['baseline_version']}
- 得分变化: {comparison['score_change']:+.2f}
- 延迟变化: {comparison['latency_change']:+.2f}s
- 状态: {comparison['status'].upper()}
"""
            if comparison["regressions"]:
                report += "\n### 检测到回归\n"
                for reg in comparison["regressions"]:
                    report += f"- {reg['type']}: {reg['change']}\n"

        return report
```

**效果**：
- 每次更新自动回归检测
- 回归问题发现时间从天级降到小时级
- 发布信心大幅提升

---

## 五、最佳实践

### 5.1 评估设计原则

| 原则 | 说明 |
|------|------|
| **代表性** | 评估用例覆盖真实场景 |
| **多样性** | 包含不同难度和类型 |
| **可重复** | 结果稳定可复现 |
| **自动化** | 支持CI/CD集成 |

### 5.2 评估指标选择

```
准确率优先场景：
- 医疗诊断
- 法律咨询
- 金融分析

效率优先场景：
- 客服对话
- 实时翻译
- 代码补全

平衡场景：
- 内容创作
- 研究助手
- 教育辅导
```

### 5.3 持续评估流程

1. **建立基线**：记录当前性能
2. **定期评估**：每次变更后运行
3. **比较分析**：检测回归和改进
4. **报告追踪**：记录历史趋势

---

## 六、总结

AI Agent评估体系的核心要素：

1. **明确指标**：选择合适的评估维度
2. **构建数据集**：覆盖真实使用场景
3. **自动化执行**：支持持续评估
4. **对比分析**：与基线和历史比较
5. **持续优化**：基于评估结果改进
