# Effective Harnesses for Long-Running Agents
# 长时间运行Agent的有效控制系统

> **Original Source / 原文链接**: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
>
> **Author / 作者**: Justin Young (Anthropic)
>
> **Translation Date / 翻译日期**: 2026-02-16

---

## Introduction / 简介

**[EN]** As AI agents become more capable, developers are increasingly asking them to take on complex tasks requiring work that spans hours, or even days. However, getting agents to make consistent progress across multiple context windows remains an open problem.

**[CN]** 随着AI Agent变得越来越强大，开发者越来越多地要求它们承担需要数小时甚至数天工作的复杂任务。然而，让Agent在多个上下文窗口中保持一致的进度仍然是一个未解决的问题。

---

**[EN]** The core challenge of long-running agents is that they must work in discrete sessions, and each new session begins with no memory of what came before. Imagine a software project staffed by engineers working in shifts, where each new engineer arrives with no memory of what happened on the previous shift. Because context windows are limited, and because most complex projects cannot be completed within a single window, agents need a way to bridge the gap between coding sessions.

**[CN]** 长时间运行Agent的核心挑战在于它们必须在离散的会话中工作，每个新会话开始时都没有之前的记忆。想象一个由轮班工程师组成的软件项目，每个新工程师到来时都不知道上一班发生了什么。由于上下文窗口有限，而且大多数复杂项目无法在单个窗口内完成，Agent需要一种方法来弥合编码会话之间的差距。

---

**[EN]** We developed a two-fold solution to enable the Claude Agent SDK to work effectively across many context windows: an **initializer agent** that sets up the environment on the first run, and a **coding agent** that is tasked with making incremental progress in every session, while leaving clear artifacts for the next session.

**[CN]** 我们开发了一个双重解决方案，使Claude Agent SDK能够在多个上下文窗口中有效工作：一个**初始化Agent**在首次运行时设置环境，以及一个**编码Agent**负责在每个会话中取得增量进展，同时为下一个会话留下清晰的记录。

---

## The Long-Running Agent Problem
## 长时间运行Agent的问题

**[EN]** The Claude Agent SDK is a powerful, general-purpose agent harness adept at coding, as well as other tasks that require the model to use tools to gather context, plan, and execute. It has context management capabilities such as compaction, which enables an agent to work on a task without exhausting the context window. Theoretically, given this setup, it should be possible for an agent to continue to do useful work for an arbitrarily long time.

**[CN]** Claude Agent SDK是一个强大的通用Agent框架，擅长编码以及其他需要模型使用工具来收集上下文、规划和执行的任务。它具有上下文管理功能（如压缩），使Agent能够在不耗尽上下文窗口的情况下处理任务。理论上，有了这个设置，Agent应该可以无限期地继续做有用的工作。

---

**[EN]** However, compaction isn't sufficient. Out of the box, even a frontier coding model like Opus 4.5 running on the Claude Agent SDK in a loop across multiple context windows will fall short of building a production-quality web app if it's only given a high-level prompt, such as "build a clone of claude.ai."

**[CN]** 然而，压缩是不够的。开箱即用，即使是像Opus 4.5这样的前沿编码模型在Claude Agent SDK上跨多个上下文窗口循环运行，如果只给它一个高级提示（如"构建一个claude.ai的克隆"），也无法构建出生产质量的Web应用。

---

### Failure Mode 1: Doing Too Much at Once
### 失败模式1：一次性做太多

**[EN]** Claude's failures manifested in two patterns. First, the agent tended to try to do too much at once—essentially to attempt to one-shot the app. Often, this led to the model running out of context in the middle of its implementation, leaving the next session to start with a feature half-implemented and undocumented. The agent would then have to guess at what had happened, and spend substantial time trying to get the basic app working again. This happens even with compaction, which doesn't always pass perfectly clear instructions to the next agent.

**[CN]** Claude的失败表现为两种模式。首先，Agent倾向于一次性做太多——本质上是试图一次性完成整个应用。通常，这会导致模型在实现过程中耗尽上下文，使下一个会话开始时面对一个半成品且没有文档的功能。然后Agent不得不猜测发生了什么，并花费大量时间试图让基本应用重新运行。即使有压缩功能，这种情况也会发生，因为压缩并不总是能传递完全清晰的指令给下一个Agent。

---

### Failure Mode 2: Premature Completion
### 失败模式2：过早完成

**[EN]** A second failure mode would often occur later in a project. After some features had already been built, a later agent instance would look around, see that progress had been made, and declare the job done.

**[CN]** 第二种失败模式通常发生在项目后期。在已经构建了一些功能后，后来的Agent实例会环顾四周，看到已经取得了进展，然后宣布工作完成。

---

### The Two-Part Solution
### 双重解决方案

**[EN]** This decomposes the problem into two parts. First, we need to set up an initial environment that lays the foundation for *all* the features that a given prompt requires, which sets up the agent to work step-by-step and feature-by-feature. Second, we should prompt each agent to make incremental progress towards its goal while also leaving the environment in a clean state at the end of a session.

**[CN]** 这将问题分解为两部分。首先，我们需要设置一个初始环境，为给定提示所需的*所有*功能奠定基础，这使Agent能够逐步地、逐个功能地工作。其次，我们应该提示每个Agent朝着目标取得增量进展，同时在会话结束时使环境保持干净状态。

---

**[EN]** By "clean state" we mean the kind of code that would be appropriate for merging to a main branch: there are no major bugs, the code is orderly and well-documented, and in general, a developer could easily begin work on a new feature without first having to clean up an unrelated mess.

**[CN]** 所谓"干净状态"，我们指的是适合合并到主分支的代码：没有重大bug，代码有序且有良好的文档，总的来说，开发者可以轻松开始新功能的开发，而不必先清理无关的混乱。

---

**[EN]** When experimenting internally, we addressed these problems using a two-part solution:

**[CN]** 在内部实验中，我们使用双重解决方案解决了这些问题：

---

**[EN]** 1. **Initializer agent**: The very first agent session uses a specialized prompt that asks the model to set up the initial environment: an `init.sh` script, a claude-progress.txt file that keeps a log of what agents have done, and an initial git commit that shows what files were added.

**[CN]** 1. **初始化Agent**：第一个Agent会话使用专门的提示，要求模型设置初始环境：一个`init.sh`脚本，一个记录Agent所做工作的claude-progress.txt文件，以及一个显示添加了哪些文件的初始git提交。

---

**[EN]** 2. **Coding agent**: Every subsequent session asks the model to make incremental progress, then leave structured updates.

**[CN]** 2. **编码Agent**：随后的每个会话要求模型取得增量进展，然后留下结构化的更新。

---

**[EN]** The key insight here was finding a way for agents to quickly understand the state of work when starting with a fresh context window, which is accomplished with the claude-progress.txt file alongside the git history. Inspiration for these practices came from knowing what effective software engineers do every day.

**[CN]** 这里的关键见解是找到一种方法，让Agent在开始新的上下文窗口时能够快速理解工作状态，这是通过claude-progress.txt文件和git历史来实现的。这些做法的灵感来自于了解有效的软件工程师每天所做的工作。

---

## Environment Management
## 环境管理

**[EN]** In the updated Claude 4 prompting guide, we shared some best practices for multi-context window workflows, including a harness structure that uses "a different prompt for the very first context window." This "different prompt" requests that the initializer agent set up the environment with all the necessary context that future coding agents will need to work effectively. Here, we provide a deeper dive on some of the key components of such an environment.

**[CN]** 在更新的Claude 4提示指南中，我们分享了一些多上下文窗口工作流的最佳实践，包括一个使用"第一个上下文窗口使用不同的提示"的框架结构。这个"不同的提示"要求初始化Agent设置环境，包含未来编码Agent有效工作所需的所有必要上下文。在这里，我们深入探讨这种环境的一些关键组件。

---

### Feature List
### 功能列表

**[EN]** To address the problem of the agent one-shotting an app or prematurely considering the project complete, we prompted the initializer agent to write a comprehensive file of feature requirements expanding on the user's initial prompt. In the claude.ai clone example, this meant over 200 features, such as "a user can open a new chat, type in a query, press enter, and see an AI response." These features were all initially marked as "failing" so that later coding agents would have a clear outline of what full functionality looked like.

**[CN]** 为了解决Agent一次性完成应用或过早认为项目完成的问题，我们提示初始化Agent编写一个全面的功能需求文件，扩展用户的初始提示。在claude.ai克隆示例中，这意味着超过200个功能，如"用户可以打开新聊天，输入查询，按回车，并看到AI响应"。这些功能最初都标记为"失败"，以便后来的编码Agent能够清楚地了解完整功能的样子。

---

**Feature List Example / 功能列表示例:**

```json
{
    "category": "functional",
    "description": "New chat button creates a fresh conversation",
    "steps": [
      "Navigate to main interface",
      "Click the 'New Chat' button",
      "Verify a new conversation is created",
      "Check that chat area shows welcome state",
      "Verify conversation appears in sidebar"
    ],
    "passes": false
}
```

---

**[EN]** We prompt coding agents to edit this file only by changing the status of a passes field, and we use strongly-worded instructions like "It is unacceptable to remove or edit tests because this could lead to missing or buggy functionality." After some experimentation, we landed on using JSON for this, as the model is less likely to inappropriately change or overwrite JSON files compared to Markdown files.

**[CN]** 我们提示编码Agent只能通过更改passes字段的状态来编辑此文件，并使用强硬措辞的指令，如"删除或编辑测试是不可接受的，因为这可能导致功能缺失或出错"。经过一些实验，我们决定使用JSON格式，因为与Markdown文件相比，模型不太可能不当地更改或覆盖JSON文件。

---

### Incremental Progress
### 增量进展

**[EN]** Given this initial environment scaffolding, the next iteration of the coding agent was then asked to work on only one feature at a time. This incremental approach turned out to be critical to addressing the agent's tendency to do too much at once.

**[CN]** 有了这个初始环境框架，编码Agent的下一个迭代被要求一次只处理一个功能。这种增量方法对于解决Agent一次性做太多的倾向至关重要。

---

**[EN]** Once working incrementally, it's still essential that the model leaves the environment in a clean state after making a code change. In our experiments, we found that the best way to elicit this behavior was to ask the model to commit its progress to git with descriptive commit messages and to write summaries of its progress in a progress file. This allowed the model to use git to revert bad code changes and recover working states of the code base.

**[CN]** 一旦进行增量工作，模型在做出代码更改后使环境保持干净状态仍然至关重要。在我们的实验中，我们发现引发这种行为的最有效方法是要求模型使用描述性提交消息将其进度提交到git，并在进度文件中编写其进度的摘要。这使模型能够使用git恢复不良的代码更改并恢复代码库的工作状态。

---

**[EN]** These approaches also increased efficiency, as they eliminated the need for an agent to have to guess at what had happened and spend its time trying to get the basic app working again.

**[CN]** 这些方法也提高了效率，因为它们消除了Agent需要猜测发生了什么并花时间试图让基本应用重新运行的需要。

---

### Testing
### 测试

**[EN]** One final major failure mode that we observed was Claude's tendency to mark a feature as complete without proper testing. Absent explicit prompting, Claude tended to make code changes, and even do testing with unit tests or `curl` commands against a development server, but would fail to recognize that the feature didn't work end-to-end.

**[CN]** 我们观察到的最后一个主要失败模式是Claude倾向于在没有适当测试的情况下将功能标记为完成。在没有明确提示的情况下，Claude倾向于进行代码更改，甚至使用单元测试或对开发服务器进行`curl`命令测试，但未能识别出功能端到端不工作。

---

**[EN]** In the case of building a web app, Claude mostly did well at verifying features end-to-end once explicitly prompted to use browser automation tools and do all testing as a human user would.

**[CN]** 在构建Web应用的情况下，一旦明确提示使用浏览器自动化工具并像人类用户一样进行所有测试，Claude在端到端验证功能方面表现得很好。

---

**[EN]** Providing Claude with these kinds of testing tools dramatically improved performance, as the agent was able to identify and fix bugs that weren't obvious from the code alone.

**[CN]** 为Claude提供这些测试工具显著提高了性能，因为Agent能够识别和修复仅从代码中不明显可见的bug。

---

**[EN]** Some issues remain, like limitations to Claude's vision and to browser automation tools making it difficult to identify every kind of bug. For example, Claude can't see browser-native alert modals through the Puppeteer MCP, and features relying on these modals tended to be buggier as a result.

**[CN]** 一些问题仍然存在，比如Claude视觉的限制和浏览器自动化工具的限制，使得难以识别每种类型的bug。例如，Claude无法通过Puppeteer MCP看到浏览器原生警告模态框，依赖这些模态框的功能因此更容易出错。

---

## Getting Up to Speed
## 快速上手

**[EN]** With all of the above in place, every coding agent is prompted to run through a series of steps to get its bearings, some quite basic but still helpful:

**[CN]** 有了以上所有内容，每个编码Agent都被提示运行一系列步骤来了解情况，有些非常基本但仍然有帮助：

---

**[EN]** 1. *Run `pwd` to see the directory you're working in. You'll only be able to edit files in this directory.*

**[CN]** 1. *运行`pwd`查看你正在工作的目录。你只能编辑此目录中的文件。*

---

**[EN]** 2. *Read the git logs and progress files to get up to speed on what was recently worked on.*

**[CN]** 2. *阅读git日志和进度文件，了解最近进行了什么工作。*

---

**[EN]** 3. *Read the features list file and choose the highest-priority feature that's not yet done to work on.*

**[CN]** 3. *阅读功能列表文件，选择尚未完成的最高优先级功能进行处理。*

---

**[EN]** This approach saves Claude some tokens in every session since it doesn't have to figure out how to test the code. It also helps to ask the initializer agent to write an init.sh script that can run the development server, and then run through a basic end-to-end test before implementing a new feature.

**[CN]** 这种方法在每个会话中为Claude节省一些token，因为它不必弄清楚如何测试代码。还有助于要求初始化Agent编写一个可以运行开发服务器的init.sh脚本，然后在实现新功能之前运行基本端到端测试。

---

**[EN]** In the case of the claude.ai clone, this meant that the agent always started the local development server and used the Puppeteer MCP to start a new chat, send a message, and receive a response. This ensured that Claude could quickly identify if the app had been left in a broken state, and immediately fix any existing bugs. If the agent had instead started implementing a new feature, it would likely make the problem worse.

**[CN]** 在claude.ai克隆的案例中，这意味着Agent总是启动本地开发服务器并使用Puppeteer MCP开始新聊天、发送消息并接收响应。这确保了Claude能够快速识别应用是否处于损坏状态，并立即修复任何现有bug。如果Agent反而开始实现新功能，它可能会使问题变得更糟。

---

### Typical Session Flow
### 典型会话流程

```
[Assistant] I'll start by getting my bearings and understanding the current state of the project.
[Tool Use] <bash - pwd>
[Tool Use] <read - claude-progress.txt>
[Tool Use] <read - feature_list.json>
[Assistant] Let me check the git log to see recent work.
[Tool Use] <bash - git log --oneline -20>
[Assistant] Now let me check if there's an init.sh script to restart the servers.
<Starts the development server>
[Assistant] Excellent! Now let me navigate to the application and verify that some fundamental features are still working.
<Tests basic functionality>
[Assistant] Based on my verification testing, I can see that the fundamental functionality is working well. The core chat features, theme switching, conversation loading, and error handling are all functioning correctly. Now let me review the tests.json file more comprehensively to understand what needs to be implemented next.
<Starts work on a new feature>
```

---

## Agent Failure Modes and Solutions Summary
## Agent失败模式与解决方案总结

| Problem / 问题 | Initializer Agent Behavior / 初始化Agent行为 | Coding Agent Behavior / 编码Agent行为 |
| --- | --- | --- |
| **Claude declares victory on the entire project too early.** / **Claude过早宣布整个项目完成。** | Set up a feature list file: based on the input spec, set up a structured JSON file with a list of end-to-end feature descriptions. / 设置功能列表文件：基于输入规范，设置一个包含端到端功能描述列表的结构化JSON文件。 | Read the feature list file at the beginning of a session. Choose a single feature to start working on. / 在会话开始时阅读功能列表文件。选择一个单一功能开始工作。 |
| **Claude leaves the environment in a state with bugs or undocumented progress.** / **Claude使环境处于有bug或未记录进度状态。** | An initial git repo and progress notes file is written. / 编写初始git仓库和进度说明文件。 | Start the session by reading the progress notes file and git commit logs, and run a basic test on the development server to catch any undocumented bugs. End the session by writing a git commit and progress update. / 通过阅读进度说明文件和git提交日志开始会话，并在开发服务器上运行基本测试以捕获任何未记录的bug。通过编写git提交和进度更新结束会话。 |
| **Claude marks features as done prematurely.** / **Claude过早将功能标记为完成。** | Set up a feature list file. / 设置功能列表文件。 | Self-verify all features. Only mark features as "passing" after careful testing. / 自我验证所有功能。只有在仔细测试后才将功能标记为"通过"。 |
| **Claude has to spend time figuring out how to run the app.** / **Claude必须花时间弄清楚如何运行应用。** | Write an `init.sh` script that can run the development server. / 编写一个可以运行开发服务器的`init.sh`脚本。 | Start the session by reading `init.sh`. / 通过阅读`init.sh`开始会话。 |

---

## Future Work
## 未来工作

**[EN]** This research demonstrates one possible set of solutions in a long-running agent harness to enable the model to make incremental progress across many context windows. However, there remain open questions.

**[CN]** 这项研究展示了一组可能的解决方案，在长时间运行的Agent框架中使模型能够在多个上下文窗口中取得增量进展。然而，仍然存在未解决的问题。

---

**[EN]** Most notably, it's still unclear whether a single, general-purpose coding agent performs best across contexts, or if better performance can be achieved through a multi-agent architecture. It seems reasonable that specialized agents like a testing agent, a quality assurance agent, or a code cleanup agent, could do an even better job at sub-tasks across the software development lifecycle.

**[CN]** 最值得注意的是，目前尚不清楚单个通用编码Agent在跨上下文时是否表现最佳，或者是否可以通过多Agent架构实现更好的性能。专业化Agent（如测试Agent、质量保证Agent或代码清理Agent）似乎可以在软件开发生命周期的子任务中做得更好。

---

**[EN]** Additionally, this demo is optimized for full-stack web app development. A future direction is to generalize these findings to other fields. It's likely that some or all of these lessons can be applied to the types of long-running agentic tasks required in, for example, scientific research or financial modeling.

**[CN]** 此外，此演示针对全栈Web应用开发进行了优化。未来的一个方向是将这些发现推广到其他领域。这些经验教训中的部分或全部可能适用于需要长时间运行Agent任务的领域，例如科学研究或金融建模。

---

## Acknowledgements
## 致谢

**[EN]** Written by Justin Young. Special thanks to David Hershey, Prithvi Rajasakeran, Jeremy Hadfield, Naia Bouscal, Michael Tingley, Jesse Mu, Jake Eaton, Marius Buleandara, Maggie Vo, Pedram Navid, Nadine Yasser, and Alex Notov for their contributions.

**[CN]** 由Justin Young撰写。特别感谢David Hershey、Prithvi Rajasakeran、Jeremy Hadfield、Naia Bouscal、Michael Tingley、Jesse Mu、Jake Eaton、Marius Buleandara、Maggie Vo、Pedram Navid、Nadine Yasser和Alex Notov的贡献。

---

**[EN]** This work reflects the collective efforts of several teams across Anthropic who made it possible for Claude to safely do long-horizon autonomous software engineering, especially the code RL & Claude Code teams. Interested candidates who would like to contribute are welcome to apply at anthropic.com/careers.

**[CN]** 这项工作反映了Anthropic多个团队的集体努力，他们使Claude能够安全地进行长期自主软件工程，特别是代码RL和Claude Code团队。有兴趣贡献的候选人欢迎在anthropic.com/careers申请。

---

## Footnotes
## 脚注

**[EN]** 1. We refer to these as separate agents in this context only because they have different initial user prompts. The system prompt, set of tools, and overall agent harness was otherwise identical.

**[CN]** 1. 我们在这些上下文中将它们称为单独的Agent，只是因为它们有不同的初始用户提示。系统提示、工具集和整体Agent框架在其他方面是相同的。

---

## Key Takeaways / 关键要点

1. **Use a two-phase agent system / 使用两阶段Agent系统**
   - Initializer agent sets up the environment / 初始化Agent设置环境
   - Coding agent makes incremental progress / 编码Agent取得增量进展

2. **Maintain a feature list in JSON format / 以JSON格式维护功能列表**
   - Mark features as "passes: false" initially / 最初将功能标记为"passes: false"
   - Only update the passes field / 只更新passes字段

3. **Leave clear artifacts after each session / 每个会话后留下清晰的记录**
   - Git commits with descriptive messages / 带有描述性消息的Git提交
   - Progress file updates / 进度文件更新

4. **Test thoroughly before marking complete / 在标记完成前彻底测试**
   - Use browser automation for web apps / 对Web应用使用浏览器自动化
   - Test as a human user would / 像人类用户一样测试

5. **Start each session with orientation steps / 以定位步骤开始每个会话**
   - Check working directory / 检查工作目录
   - Read git logs and progress files / 阅读git日志和进度文件
   - Review feature list / 审查功能列表

---

*Document saved for reference in future projects.*
*本文档保存用于未来项目参考。*
