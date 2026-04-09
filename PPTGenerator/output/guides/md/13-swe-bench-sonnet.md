# SWE-bench Sonnet（SWE-bench Verified）

> 来源：https://www.anthropic.com/engineering/swe-bench-sonnet
> 发布日期：2025-01-06

---

## 一、SWE-bench概述

### 1.1 什么是SWE-bench

SWE-bench是一个评估AI模型解决真实软件工程问题能力的基准测试。它包含来自真实GitHub issue的问题，需要模型理解代码、定位问题并生成修复。

### 1.2 评估指标

| 指标 | 说明 |
|------|------|
| **解决率** | 成功解决问题的比例 |
| **Pass@1** | 第一次尝试即通过的比例 |
| **Pass@k** | k次尝试内通过的比例 |
| **类别准确率** | 不同类型问题的解决率 |

### 1.3 挑战

- 理解大型代码库
- 定位相关代码
- 生成正确且完整的补丁
- 处理各种编程语言和框架

---

## 二、方法论

### 2.1 问题解决流程

```
SWE-bench解决流程：
├── 1. 问题理解
│   ├── 阅读issue描述
│   ├── 理解错误信息
│   └── 识别相关文件
├── 2. 代码探索
│   ├── 浏览代码结构
│   ├── 查找相关代码
│   └── 理解代码逻辑
├── 3. 问题定位
│   ├── 确定问题位置
│   ├── 分析根本原因
│   └── 设计修复方案
├── 4. 补丁生成
│   ├── 编写修复代码
│   ├── 添加测试用例
│   └── 验证修复正确
└── 5. 结果验证
    ├── 运行测试
    ├── 检查副作用
    └── 确认解决
```

### 2.2 关键技术

- 代码检索
- 上下文理解
- 精确编辑
- 测试驱动

---

## 三、实战案例

### 案例1：构建SWE-bench求解器

**场景**：创建一个自动解决SWE-bench问题的系统

**解决方案**：

```python
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import os
import subprocess
import json

@dataclass
class SWEBenchProblem:
    """SWE-bench问题定义"""
    instance_id: str
    repo: str
    version: str
    problem_statement: str
    hints_text: str
    created_at: str
    patch: str  # 参考补丁
    test_patch: str  # 测试补丁
    fail_to_pass: List[str]  # 失败到通过的测试
    pass_to_pass: List[str]  # 应该保持通过的测试

@dataclass
class SolutionResult:
    """解决结果"""
    instance_id: str
    success: bool
    patch: Optional[str]
    error_message: Optional[str]
    tests_passed: int
    tests_failed: int

class SWEBenchSolver:
    """SWE-bench求解器"""

    def __init__(self, llm_client, work_dir: str):
        self.llm = llm_client
        self.work_dir = work_dir
        self.max_iterations = 10

    async def solve(self, problem: SWEBenchProblem) -> SolutionResult:
        """解决问题"""
        # 1. 克隆仓库
        repo_dir = await self.clone_repo(problem.repo, problem.version)

        # 2. 理解问题
        understanding = await self.understand_problem(problem)

        # 3. 探索代码
        exploration = await self.explore_code(repo_dir, understanding)

        # 4. 定位问题
        localization = await self.localize_issue(repo_dir, problem, exploration)

        # 5. 生成修复
        patch = await self.generate_patch(repo_dir, problem, localization)

        if not patch:
            return SolutionResult(
                instance_id=problem.instance_id,
                success=False,
                patch=None,
                error_message="无法生成补丁",
                tests_passed=0,
                tests_failed=len(problem.fail_to_pass)
            )

        # 6. 应用补丁
        await self.apply_patch(repo_dir, patch)

        # 7. 运行测试
        test_result = await self.run_tests(repo_dir, problem.fail_to_pass)

        return SolutionResult(
            instance_id=problem.instance_id,
            success=test_result["all_passed"],
            patch=patch,
            error_message=test_result.get("error"),
            tests_passed=test_result["passed"],
            tests_failed=test_result["failed"]
        )

    async def clone_repo(self, repo: str, version: str) -> str:
        """克隆仓库"""
        repo_name = repo.split("/")[-1]
        repo_dir = os.path.join(self.work_dir, f"{repo_name}_{version}")

        if not os.path.exists(repo_dir):
            subprocess.run([
                "git", "clone",
                f"https://github.com/{repo}.git",
                repo_dir,
                "-b", version,
                "--depth", "1"
            ], check=True)

        return repo_dir

    async def understand_problem(self, problem: SWEBenchProblem) -> Dict:
        """理解问题"""
        prompt = f"""
分析以下软件问题：

问题描述：
{problem.problem_statement}

提示：
{problem.hints_text}

请分析：
1. 问题的核心是什么？
2. 涉及哪些功能或模块？
3. 预期的正确行为是什么？
4. 可能的原因是什么？

以JSON格式返回分析结果。
"""
        response = await self.llm.generate(prompt)
        return json.loads(response)

    async def explore_code(self, repo_dir: str, understanding: Dict) -> Dict:
        """探索代码"""
        # 获取代码结构
        structure = self.get_repo_structure(repo_dir)

        # 根据理解搜索相关文件
        relevant_files = []

        for keyword in understanding.get("keywords", []):
            files = self.search_files(repo_dir, keyword)
            relevant_files.extend(files)

        # 读取关键文件
        file_contents = {}
        for file_path in set(relevant_files)[:10]:  # 限制数量
            full_path = os.path.join(repo_dir, file_path)
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    file_contents[file_path] = f.read()

        return {
            "structure": structure,
            "relevant_files": list(set(relevant_files)),
            "file_contents": file_contents
        }

    def get_repo_structure(self, repo_dir: str) -> Dict:
        """获取仓库结构"""
        structure = {
            "directories": [],
            "files": []
        }

        for root, dirs, files in os.walk(repo_dir):
            # 跳过隐藏目录和常见排除目录
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv']]

            rel_root = os.path.relpath(root, repo_dir)
            if rel_root != '.':
                structure["directories"].append(rel_root)

            for file in files:
                if not file.startswith('.'):
                    structure["files"].append(os.path.join(rel_root, file) if rel_root != '.' else file)

        return structure

    def search_files(self, repo_dir: str, keyword: str) -> List[str]:
        """搜索包含关键词的文件"""
        matches = []

        for root, _, files in os.walk(repo_dir):
            for file in files:
                if file.endswith(('.py', '.js', '.java', '.go', '.ts')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if keyword.lower() in content.lower():
                                matches.append(os.path.relpath(file_path, repo_dir))
                    except:
                        pass

        return matches

    async def localize_issue(self, repo_dir: str, problem: SWEBenchProblem, exploration: Dict) -> Dict:
        """定位问题"""
        prompt = f"""
基于以下信息定位问题：

问题理解：
{json.dumps(exploration.get('understanding', {}), ensure_ascii=False, indent=2)}

相关文件：
{json.dumps(exploration['relevant_files'], ensure_ascii=False, indent=2)}

文件内容：
{self._format_file_contents(exploration['file_contents'])}

请确定：
1. 问题位于哪个文件？
2. 具体在哪个函数或类？
3. 需要修改哪些代码行？

以JSON格式返回定位结果。
"""
        response = await self.llm.generate(prompt)
        return json.loads(response)

    def _format_file_contents(self, contents: Dict) -> str:
        """格式化文件内容"""
        formatted = []
        for path, content in contents.items():
            formatted.append(f"\n### {path}\n```\n{content[:3000]}\n```\n")
        return "\n".join(formatted)

    async def generate_patch(self, repo_dir: str, problem: SWEBenchProblem, localization: Dict) -> Optional[str]:
        """生成补丁"""
        target_file = localization.get("target_file")
        if not target_file:
            return None

        file_path = os.path.join(repo_dir, target_file)
        with open(file_path, 'r') as f:
            original_content = f.read()

        prompt = f"""
你需要修复以下代码问题：

问题描述：
{problem.problem_statement}

定位信息：
- 文件：{target_file}
- 位置：{localization.get('location')}
- 原因分析：{localization.get('root_cause')}

原始代码：
```
{original_content}
```

请生成修复补丁。补丁应该是可以直接应用的diff格式或完整的新文件内容。
"""
        response = await self.llm.generate(prompt)

        # 解析补丁
        patch = self.parse_patch(response)
        return patch

    def parse_patch(self, response: str) -> Optional[str]:
        """解析补丁"""
        # 尝试提取代码块中的内容
        if "```diff" in response:
            start = response.find("```diff") + 7
            end = response.find("```", start)
            return response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            return response[start:end].strip()
        return response

    async def apply_patch(self, repo_dir: str, patch: str):
        """应用补丁"""
        # 写入补丁文件
        patch_file = os.path.join(repo_dir, "fix.patch")
        with open(patch_file, 'w') as f:
            f.write(patch)

        # 应用补丁
        subprocess.run(
            ["git", "apply", "fix.patch"],
            cwd=repo_dir,
            check=False
        )

    async def run_tests(self, repo_dir: str, test_files: List[str]) -> Dict:
        """运行测试"""
        results = {
            "passed": 0,
            "failed": 0,
            "all_passed": False,
            "details": []
        }

        for test in test_files:
            try:
                # 运行pytest
                result = subprocess.run(
                    ["python", "-m", "pytest", test, "-v"],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode == 0:
                    results["passed"] += 1
                    results["details"].append({"test": test, "status": "passed"})
                else:
                    results["failed"] += 1
                    results["details"].append({
                        "test": test,
                        "status": "failed",
                        "output": result.stdout + result.stderr
                    })

            except subprocess.TimeoutExpired:
                results["failed"] += 1
                results["details"].append({"test": test, "status": "timeout"})
            except Exception as e:
                results["failed"] += 1
                results["details"].append({"test": test, "status": "error", "error": str(e)})

        results["all_passed"] = results["failed"] == 0
        return results

# 使用示例
async def demo_swe_bench():
    class MockLLM:
        async def generate(self, prompt):
            if "分析" in prompt:
                return json.dumps({
                    "keywords": ["database", "connection", "pool"],
                    "core_issue": "连接池耗尽"
                })
            elif "定位" in prompt:
                return json.dumps({
                    "target_file": "src/db/pool.py",
                    "location": "ConnectionPool类",
                    "root_cause": "连接未正确释放"
                })
            else:
                return "补丁内容..."

    problem = SWEBenchProblem(
        instance_id="test-001",
        repo="example/repo",
        version="v1.0.0",
        problem_statement="数据库连接池耗尽",
        hints_text="检查连接释放逻辑",
        created_at="2025-01-01",
        patch="",
        test_patch="",
        fail_to_pass=["tests/test_pool.py"],
        pass_to_pass=[]
    )

    solver = SWEBenchSolver(MockLLM(), "/tmp/swe_bench")
    result = await solver.solve(problem)
    print(f"解决结果: {result.success}")
```

---

### 案例2：迭代式问题解决

**场景**：使用迭代方法改进解决方案

**解决方案**：

```python
class IterativeSWESolver:
    """迭代式SWE-bench求解器"""

    def __init__(self, llm_client, max_iterations: int = 5):
        self.llm = llm_client
        self.max_iterations = max_iterations

    async def solve_iteratively(self, problem: SWEBenchProblem) -> SolutionResult:
        """迭代解决"""
        best_result = None

        for iteration in range(self.max_iterations):
            print(f"迭代 {iteration + 1}/{self.max_iterations}")

            # 生成解决方案
            solution = await self.generate_solution(problem, iteration, best_result)

            # 验证解决方案
            result = await self.verify_solution(problem, solution)

            if result.success:
                return result

            # 保存最佳结果
            if best_result is None or result.tests_passed > best_result.tests_passed:
                best_result = result

            # 基于反馈改进
            problem = await self.refine_understanding(problem, result)

        return best_result or SolutionResult(
            instance_id=problem.instance_id,
            success=False,
            patch=None,
            error_message="达到最大迭代次数",
            tests_passed=0,
            tests_failed=0
        )

    async def generate_solution(self, problem: SWEBenchProblem, iteration: int, previous_result: SolutionResult) -> str:
        """生成解决方案"""
        prompt = f"""
问题：{problem.problem_statement}

迭代次数：{iteration + 1}

{'之前尝试的结果：' + previous_result.error_message if previous_result else '这是第一次尝试。'}

请{'改进之前的解决方案' if previous_result else '生成初始解决方案'}。
"""
        return await self.llm.generate(prompt)

    async def verify_solution(self, problem: SWEBenchProblem, solution: str) -> SolutionResult:
        """验证解决方案"""
        # 实现验证逻辑
        return SolutionResult(
            instance_id=problem.instance_id,
            success=False,
            patch=solution,
            error_message="验证失败",
            tests_passed=0,
            tests_failed=1
        )

    async def refine_understanding(self, problem: SWEBenchProblem, result: SolutionResult) -> SWEBenchProblem:
        """基于结果改进理解"""
        # 添加失败信息到问题描述
        problem.hints_text += f"\n\n之前的尝试失败原因：{result.error_message}"
        return problem
```

---

### 案例3：多模型协作求解

**场景**：使用多个专门模型协作解决问题

**解决方案**：

```python
class MultiModelSWESolver:
    """多模型协作求解器"""

    def __init__(self, models: Dict[str, Any]):
        self.models = models  # {"analyzer": model1, "coder": model2, "reviewer": model3}

    async def solve(self, problem: SWEBenchProblem) -> SolutionResult:
        """多模型协作解决"""
        # 1. 分析模型理解问题
        analysis = await self.analyze_problem(problem)

        # 2. 编码模型生成补丁
        patch = await self.generate_patch(problem, analysis)

        # 3. 审查模型检查补丁
        review = await self.review_patch(patch, problem)

        # 4. 如果审查不通过，迭代改进
        iterations = 0
        while not review["approved"] and iterations < 3:
            patch = await self.improve_patch(patch, review, problem)
            review = await self.review_patch(patch, problem)
            iterations += 1

        return SolutionResult(
            instance_id=problem.instance_id,
            success=review["approved"],
            patch=patch,
            error_message=None if review["approved"] else review["issues"],
            tests_passed=1 if review["approved"] else 0,
            tests_failed=0 if review["approved"] else 1
        )

    async def analyze_problem(self, problem: SWEBenchProblem) -> Dict:
        """分析模型处理"""
        analyzer = self.models["analyzer"]
        prompt = f"分析问题：{problem.problem_statement}"
        return await analyzer.generate(prompt)

    async def generate_patch(self, problem: SWEBenchProblem, analysis: Dict) -> str:
        """编码模型处理"""
        coder = self.models["coder"]
        prompt = f"基于分析生成补丁：{analysis}"
        return await coder.generate(prompt)

    async def review_patch(self, patch: str, problem: SWEBenchProblem) -> Dict:
        """审查模型处理"""
        reviewer = self.models["reviewer"]
        prompt = f"""
审查补丁：
{patch}

原问题：{problem.problem_statement}

检查：
1. 是否解决了问题？
2. 是否引入新问题？
3. 代码风格是否一致？

返回JSON：{{"approved": true/false, "issues": []}}
"""
        response = await reviewer.generate(prompt)
        return json.loads(response)

    async def improve_patch(self, patch: str, review: Dict, problem: SWEBenchProblem) -> str:
        """改进补丁"""
        coder = self.models["coder"]
        prompt = f"""
原补丁：
{patch}

审查意见：
{review['issues']}

请改进补丁。
"""
        return await coder.generate(prompt)
```

---

### 案例4：测试驱动修复

**场景**：先编写测试，再修复代码

**解决方案**：

```python
class TestDrivenSolver:
    """测试驱动求解器"""

    async def solve(self, problem: SWEBenchProblem) -> SolutionResult:
        """测试驱动解决"""
        # 1. 理解预期行为
        expected_behavior = await self.understand_expected_behavior(problem)

        # 2. 编写复现测试
        reproduction_test = await self.write_reproduction_test(problem, expected_behavior)

        # 3. 确认测试失败
        test_fails = await self.run_test(reproduction_test)
        if not test_fails:
            return SolutionResult(
                instance_id=problem.instance_id,
                success=False,
                patch=None,
                error_message="复现测试未失败",
                tests_passed=0,
                tests_failed=0
            )

        # 4. 修复代码使测试通过
        patch = await self.fix_code(problem, reproduction_test)

        # 5. 确认测试通过
        final_result = await self.run_final_tests(patch, problem.fail_to_pass)

        return SolutionResult(
            instance_id=problem.instance_id,
            success=final_result["passed"],
            patch=patch,
            error_message=final_result.get("error"),
            tests_passed=final_result["passed_count"],
            tests_failed=final_result["failed_count"]
        )

    async def understand_expected_behavior(self, problem: SWEBenchProblem) -> str:
        """理解预期行为"""
        prompt = f"""
问题描述：{problem.problem_statement}

请描述正确的行为应该是什么。
"""
        return await self.llm.generate(prompt)

    async def write_reproduction_test(self, problem: SWEBenchProblem, expected: str) -> str:
        """编写复现测试"""
        prompt = f"""
问题：{problem.problem_statement}
预期行为：{expected}

请编写一个测试用例来复现这个问题。
"""
        return await self.llm.generate(prompt)

    async def run_test(self, test_code: str) -> bool:
        """运行测试"""
        # 执行测试，返回是否失败
        return True

    async def fix_code(self, problem: SWEBenchProblem, test: str) -> str:
        """修复代码"""
        prompt = f"""
测试用例：
{test}

请修改代码使测试通过。
"""
        return await self.llm.generate(prompt)

    async def run_final_tests(self, patch: str, tests: List[str]) -> Dict:
        """运行最终测试"""
        return {"passed": True, "passed_count": 1, "failed_count": 0}
```

---

### 案例5：批量评估系统

**场景**：批量评估SWE-bench性能

**解决方案**：

```python
class SWEBenchEvaluator:
    """批量评估器"""

    def __init__(self, solver: SWEBenchSolver):
        self.solver = solver

    async def evaluate_batch(self, problems: List[SWEBenchProblem]) -> Dict:
        """批量评估"""
        results = []

        for problem in problems:
            result = await self.solver.solve(problem)
            results.append(result)

        return self.compute_metrics(results)

    def compute_metrics(self, results: List[SolutionResult]) -> Dict:
        """计算指标"""
        total = len(results)
        solved = sum(1 for r in results if r.success)

        # 按类别统计
        by_category = {}
        for r in results:
            category = self.categorize_problem(r.instance_id)
            if category not in by_category:
                by_category[category] = {"total": 0, "solved": 0}
            by_category[category]["total"] += 1
            if r.success:
                by_category[category]["solved"] += 1

        return {
            "total_problems": total,
            "solved": solved,
            "solve_rate": solved / total if total > 0 else 0,
            "by_category": {
                cat: {
                    "solve_rate": data["solved"] / data["total"],
                    **data
                }
                for cat, data in by_category.items()
            },
            "average_tests_passed": sum(r.tests_passed for r in results) / total,
            "results": results
        }

    def categorize_problem(self, instance_id: str) -> str:
        """问题分类"""
        # 简化分类
        return "general"

    def generate_report(self, metrics: Dict) -> str:
        """生成报告"""
        return f"""
# SWE-bench评估报告

## 总体结果
- 总问题数：{metrics['total_problems']}
- 解决数：{metrics['solved']}
- 解决率：{metrics['solve_rate']:.2%}

## 分类结果
{self._format_category_results(metrics['by_category'])}

## 详细结果
{self._format_detailed_results(metrics['results'])}
"""

    def _format_category_results(self, by_category: Dict) -> str:
        """格式化分类结果"""
        lines = []
        for cat, data in by_category.items():
            lines.append(f"- {cat}: {data['solve_rate']:.2%} ({data['solved']}/{data['total']})")
        return "\n".join(lines)

    def _format_detailed_results(self, results: List[SolutionResult]) -> str:
        """格式化详细结果"""
        lines = []
        for r in results[:10]:  # 只显示前10个
            status = "✓" if r.success else "✗"
            lines.append(f"- {status} {r.instance_id}: {r.tests_passed} passed, {r.tests_failed} failed")
        return "\n".join(lines)
```

---

## 四、最佳实践

### 4.1 问题理解

- 仔细阅读issue描述
- 理解错误堆栈
- 查看相关PR/commit
- 研究测试用例

### 4.2 代码探索

- 使用grep/搜索定位代码
- 阅读相关测试
- 理解代码结构
- 检查依赖关系

### 4.3 补丁生成

- 最小化修改范围
- 保持代码风格一致
- 添加必要注释
- 考虑边界情况

---

## 五、总结

SWE-bench的核心价值：

1. **真实评估**：真实世界问题测试
2. **能力度量**：量化模型编程能力
3. **研究方向**：指导模型改进
4. **实践参考**：了解模型实际能力
