# Claude Code最佳实践

> 来源：https://www.anthropic.com/engineering/claude-code-best-practices
> 发布日期：2025-04-18

---

## 一、环境设置

### 1.1 CLAUDE.md文件

CLAUDE.md是自动拉入上下文的特殊文件，Claude Code会在会话开始时自动读取它。

**放置位置**：
| 位置 | 适用场景 |
|------|----------|
| 仓库根目录 | 最常用，适用于大多数项目 |
| 运行目录的父目录 | Monorepo场景 |
| 运行目录的子目录 | 特定功能模块 |
| `~/.claude/CLAUDE.md` | 全局配置，适用所有会话 |

**推荐内容结构**：

```markdown
# 项目名称

## 常用命令
- 启动开发服务器：`npm run dev`
- 运行测试：`npm test`
- 构建生产版本：`npm run build`

## 核心文件
- `src/index.ts` - 入口文件
- `src/config.ts` - 配置管理
- `src/utils/` - 工具函数

## 代码风格
- 使用TypeScript
- 函数命名：camelCase
- 组件命名：PascalCase
- 每个函数必须有JSDoc注释

## 测试规范
- 测试文件放在`__tests__/`目录
- 使用Jest测试框架
- 测试覆盖率要求：80%以上

## 分支规范
- feature/* - 新功能
- fix/* - Bug修复
- refactor/* - 重构

## IMPORTANT
- 不要直接修改.env文件
- 所有API调用必须有错误处理
- 提交前必须运行测试
```

### 1.2 调优CLAUDE.md

**优化技巧**：
- 像优化提示词一样优化CLAUDE.md
- 使用`#`键给Claude指令，自动合并到相关CLAUDE.md
- 添加强调词如"IMPORTANT"、"YOU MUST"改善遵循度
- 偶尔通过提示改进器运行CLAUDE.md

---

## 二、工具扩展

### 2.1 Bash工具

Claude Code继承bash环境，可以：
1. 告诉Claude工具名称和使用示例
2. 让Claude运行`--help`查看文档
3. 在CLAUDE.md中记录常用工具

**最佳实践**：

```markdown
## 可用工具

### 代码质量
- ESLint: `npm run lint`
- Prettier: `npm run format`
- TypeScript检查: `npm run typecheck`

### 数据库
- 迁移: `npm run db:migrate`
- 回滚: `npm run db:rollback`
- 重置: `npm run db:reset`

### Docker
- 启动: `docker-compose up -d`
- 停止: `docker-compose down`
- 日志: `docker-compose logs -f`
```

### 2.2 MCP服务器

Claude Code可作为MCP服务器和客户端：

**配置位置**：
- 项目配置（特定目录可用）
- 全局配置（所有项目可用）
- 检入的`.mcp.json`文件（团队成员可用）

### 2.3 自定义斜杠命令

将提示模板存储在`.claude/commands`文件夹：

```
.claude/
└── commands/
    ├── review.md      # /review 命令
    ├── test.md        # /test 命令
    └── deploy.md      # /deploy 命令
```

---

## 三、常用工作流

### 3.1 探索-计划-编码-提交

**标准流程**：

```
Step 1: 探索
├── 让Claude读取相关文件/图片/URL
├── 明确不要写代码
└── 收集足够信息

Step 2: 计划
├── 让Claude制定方案
├── 使用"think"触发扩展思考
└── 确认方案后再继续

Step 3: 编码
├── 实现解决方案
├── 遵循项目代码风格
└── 添加必要的测试

Step 4: 提交
├── 运行测试确保通过
├── 创建有意义的commit
└── 必要时创建PR和更新文档
```

### 3.2 测试驱动开发

```
1. 让Claude基于预期输入/输出编写测试
2. 运行测试确认失败（红）
3. 提交测试
4. 编写代码通过测试（绿），不修改测试
5. 满意后提交代码
6. 可选：重构优化
```

### 3.3 视觉迭代

```
1. 提供浏览器截图能力
2. 提供视觉设计稿
3. 让Claude实现设计
4. 截图结果对比设计
5. 迭代直到匹配
6. 满意后提交
```

### 3.4 Safe YOLO模式

```bash
claude --dangerously-skip-permissions
```

跳过所有权限检查，适合无网络访问的容器环境。

### 3.5 代码库问答

用于学习和探索新代码库：
- 搜索代码库回答一般问题
- 理解特定代码行的作用
- 找出API设计原因

### 3.6 Git交互

Claude可以处理90%+的git操作：
- 搜索git历史
- 编写提交消息
- 处理复杂git操作

---

## 四、工作流优化

### 4.1 具体化指令

| 糟糕 | 良好 |
|------|------|
| add tests for foo.py | write a new test case for foo.py, covering the edge case where the user is logged out. avoid mocks |
| fix the bug | the login button on the homepage doesn't work when clicked. investigate the click handler in Header.tsx and fix it |
| improve performance | the dashboard page takes 5+ seconds to load. profile it and identify the top 3 bottlenecks |
| refactor this | split the monolithic processOrder function into smaller, testable functions. keep the same behavior |

### 4.2 提供图片

- 粘贴截图
- 拖放图片
- 提供图片文件路径

### 4.3 及早纠正

- 让Claude先做计划再编码
- 按Escape中断
- 双击Escape跳回历史编辑提示
- 要求Claude撤销更改

### 4.4 使用/clear保持上下文聚焦

长会话中，上下文窗口可能填满无关内容，使用`/clear`重置。

### 4.5 使用检查清单

对于大型任务，让Claude使用Markdown文件作为检查清单和工作草稿。

---

## 五、多Claude工作流

### 5.1 代码编写与验证分离

```
1. 用Claude A编写代码
2. 运行/clear或启动Claude B
3. Claude B审查Claude A的工作
4. 启动Claude C根据反馈编辑代码
```

### 5.2 多仓库检出

```
1. 创建3-4个git检出
2. 在不同终端标签打开
3. 在每个文件夹启动Claude执行不同任务
4. 循环检查进度
```

### 5.3 Git Worktrees

```bash
git worktree add ../project-feature-a feature-a
cd ../project-feature-a && claude

git worktree add ../project-bugfix bug-123
cd ../project-bugfix && claude
```

---

## 六、实战案例

### 案例1：CLAUDE.md配置模板

**场景**：为一个Next.js项目创建CLAUDE.md

**问题分析**：
- 需要让Claude理解项目结构
- 需要知道常用命令
- 需要遵循特定代码风格

**解决方案**：创建全面的CLAUDE.md

```markdown
# E-Commerce Platform

## 项目概述
这是一个Next.js 14电商平台，使用App Router、TypeScript、Prisma、Tailwind CSS。

## 常用命令
```bash
# 开发
npm run dev          # 启动开发服务器 (http://localhost:3000)
npm run build        # 构建生产版本
npm run start        # 启动生产服务器

# 测试
npm run test         # 运行Jest测试
npm run test:e2e     # 运行Playwright E2E测试
npm run test:watch   # 监视模式

# 数据库
npm run db:push      # 推送schema变更
npm run db:migrate   # 运行迁移
npm run db:studio    # 打开Prisma Studio

# 代码质量
npm run lint         # ESLint检查
npm run format       # Prettier格式化
npm run typecheck    # TypeScript类型检查
```

## 项目结构
```
src/
├── app/              # Next.js App Router页面
│   ├── (auth)/       # 认证相关页面组
│   ├── (shop)/       # 商店相关页面组
│   └── api/          # API路由
├── components/       # React组件
│   ├── ui/           # 基础UI组件
│   └── features/     # 功能组件
├── lib/              # 工具库
│   ├── db.ts         # Prisma客户端
│   ├── auth.ts       # NextAuth配置
│   └── stripe.ts     # Stripe集成
└── types/            # TypeScript类型定义
```

## 代码风格
- 使用函数组件和hooks
- 组件使用命名导出
- 服务端组件优先，按需使用'use client'
- 使用Zod进行数据验证
- API路由返回类型使用NextResponse

## 环境变量
```
DATABASE_URL=        # PostgreSQL连接
NEXTAUTH_SECRET=     # NextAuth密钥
STRIPE_SECRET_KEY=   # Stripe密钥
```

## IMPORTANT规则
1. 所有数据库操作必须使用Prisma
2. 用户输入必须用Zod验证
3. 价格使用分(cents)存储，显示时转换
4. 订单状态变更必须记录日志
5. 不要直接操作process.env，使用lib/config.ts
```

**效果**：
- Claude能快速理解项目结构
- 生成的代码符合项目风格
- 减少了重复解释

---

### 案例2：自定义斜杠命令

**场景**：创建常用操作的快捷命令

**问题分析**：
- 经常需要执行代码审查
- 需要标准化的PR创建流程
- 需要一致的测试编写方式

**解决方案**：创建自定义命令文件

**`.claude/commands/review.md`**：
```markdown
请对当前代码变更进行全面的代码审查：

## 审查清单

### 代码质量
- [ ] 代码是否清晰易读
- [ ] 命名是否有意义
- [ ] 是否有重复代码
- [ ] 函数是否过长（超过50行需要拆分）

### 功能正确性
- [ ] 是否满足需求
- [ ] 边缘情况是否处理
- [ ] 错误处理是否完善

### 性能
- [ ] 是否有不必要的循环
- [ ] 是否有N+1查询问题
- [ ] 大数据量时的性能考虑

### 安全
- [ ] 用户输入是否验证
- [ ] 是否有XSS/SQL注入风险
- [ ] 敏感数据是否正确处理

### 测试
- [ ] 是否有足够的测试覆盖
- [ ] 测试是否有意义

请提供具体的改进建议，包括代码示例。
```

**`.claude/commands/pr.md`**：
```markdown
请帮我创建一个规范的Pull Request：

1. 查看当前的git diff
2. 分析变更内容
3. 生成PR标题（遵循Conventional Commits）
4. 生成PR描述，包括：
   - 变更摘要
   - 变更类型（feature/fix/refactor/docs）
   - 测试说明
   - 截图（如有UI变更）
   - Breaking Changes（如有）

PR标题格式：
- feat: 新功能
- fix: Bug修复
- refactor: 重构
- docs: 文档更新
- test: 测试相关
- chore: 构建/工具相关
```

**`.claude/commands/test.md`**：
```markdown
请为指定代码编写测试：

1. 首先阅读代码理解功能
2. 识别所有代码路径和边缘情况
3. 编写测试用例覆盖：
   - 正常路径
   - 边缘情况
   - 错误处理
   - 边界值

测试要求：
- 使用项目现有的测试框架
- 每个测试用例有清晰的描述
- 使用AAA模式（Arrange-Act-Assert）
- Mock外部依赖
- 测试覆盖率目标：80%+

请输出完整的测试文件内容。
```

**使用方式**：
```bash
# 代码审查
/review

# 创建PR
/pr

# 编写测试
/test src/utils/calculator.ts
```

---

### 案例3：TDD工作流实践

**场景**：实现一个购物车功能

**问题分析**：
- 需要确保功能正确性
- 需要处理各种边缘情况
- 希望有可维护的测试

**解决方案**：TDD工作流

```
# 第一步：让Claude编写测试

用户：请为购物车功能编写测试。
要求：
- 可以添加商品
- 可以移除商品
- 可以更新数量
- 可以计算总价
- 数量不能为负数
- 空购物车总价为0

Claude生成的测试：
```typescript
// __tests__/cart.test.ts
import { Cart } from '../src/cart';

describe('Cart', () => {
  let cart: Cart;

  beforeEach(() => {
    cart = new Cart();
  });

  describe('addItem', () => {
    it('should add item to cart', () => {
      cart.addItem({ id: '1', name: 'Apple', price: 1.5, quantity: 2 });
      expect(cart.items).toHaveLength(1);
      expect(cart.items[0].quantity).toBe(2);
    });

    it('should increase quantity if item already exists', () => {
      cart.addItem({ id: '1', name: 'Apple', price: 1.5, quantity: 2 });
      cart.addItem({ id: '1', name: 'Apple', price: 1.5, quantity: 3 });
      expect(cart.items).toHaveLength(1);
      expect(cart.items[0].quantity).toBe(5);
    });
  });

  describe('removeItem', () => {
    it('should remove item from cart', () => {
      cart.addItem({ id: '1', name: 'Apple', price: 1.5, quantity: 2 });
      cart.removeItem('1');
      expect(cart.items).toHaveLength(0);
    });

    it('should do nothing if item not found', () => {
      cart.removeItem('non-existent');
      expect(cart.items).toHaveLength(0);
    });
  });

  describe('updateQuantity', () => {
    it('should update item quantity', () => {
      cart.addItem({ id: '1', name: 'Apple', price: 1.5, quantity: 2 });
      cart.updateQuantity('1', 5);
      expect(cart.items[0].quantity).toBe(5);
    });

    it('should throw error for negative quantity', () => {
      cart.addItem({ id: '1', name: 'Apple', price: 1.5, quantity: 2 });
      expect(() => cart.updateQuantity('1', -1)).toThrow('Quantity cannot be negative');
    });
  });

  describe('getTotal', () => {
    it('should return 0 for empty cart', () => {
      expect(cart.getTotal()).toBe(0);
    });

    it('should calculate total correctly', () => {
      cart.addItem({ id: '1', name: 'Apple', price: 1.5, quantity: 2 });
      cart.addItem({ id: '2', name: 'Banana', price: 2, quantity: 3 });
      expect(cart.getTotal()).toBe(9); // 1.5*2 + 2*3 = 9
    });
  });
});
```

# 第二步：运行测试确认失败

用户：运行测试

Claude：运行 npm test，所有测试都失败了，因为Cart类还不存在。

# 第三步：编写实现代码

用户：请编写代码让所有测试通过。不要修改测试。

Claude生成的实现：
```typescript
// src/cart.ts
export interface CartItem {
  id: string;
  name: string;
  price: number;
  quantity: number;
}

export class Cart {
  private _items: CartItem[] = [];

  get items(): CartItem[] {
    return [...this._items];
  }

  addItem(item: CartItem): void {
    const existingIndex = this._items.findIndex(i => i.id === item.id);
    if (existingIndex >= 0) {
      this._items[existingIndex].quantity += item.quantity;
    } else {
      this._items.push(item);
    }
  }

  removeItem(id: string): void {
    const index = this._items.findIndex(i => i.id === id);
    if (index >= 0) {
      this._items.splice(index, 1);
    }
  }

  updateQuantity(id: string, quantity: number): void {
    if (quantity < 0) {
      throw new Error('Quantity cannot be negative');
    }
    const item = this._items.find(i => i.id === id);
    if (item) {
      item.quantity = quantity;
    }
  }

  getTotal(): number {
    return this._items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  }
}
```

# 第四步：运行测试确认通过

用户：运行测试

Claude：所有测试通过！

# 第五步：提交

用户：提交代码

Claude：已创建commit "feat: implement Cart class with TDD"
```

**效果**：
- 测试覆盖率高
- 代码质量有保证
- 回归测试方便

---

### 案例4：多Agent协作开发

**场景**：大型重构任务

**问题分析**：
- 重构涉及多个文件
- 需要保证功能不变
- 单一会话可能上下文溢出

**解决方案**：使用Git Worktrees多Claude协作

```bash
# 创建多个worktree
git worktree add ../project-refactor-auth refactor/auth
git worktree add ../project-refactor-api refactor/api
git worktree add ../project-refactor-ui refactor/ui

# 在不同终端启动Claude
# 终端1
cd ../project-refactor-auth
claude
> 重构认证模块，将session管理从JWT迁移到OAuth

# 终端2
cd ../project-refactor-api
claude
> 重构API层，添加统一的错误处理中间件

# 终端3
cd ../project-refactor-ui
claude
> 重构UI组件，使用新的设计系统
```

**协调流程**：
```
1. 主仓库：保持main分支稳定
2. 每个worktree：独立Claude会话处理特定模块
3. 定期同步：
   - 完成一个模块后合并回主feature分支
   - 更新其他worktree
   - 解决冲突

4. 最终合并：
   - 集成测试
   - 合并到main
```

**效果**：
- 重构时间缩短60%
- 每个模块专注度高
- 冲突最小化

---

### 案例5：视觉迭代开发

**场景**：实现一个复杂的UI组件

**问题分析**：
- 设计稿细节多
- 需要像素级还原
- 颜色、间距要求精确

**解决方案**：视觉迭代工作流

```
# 第一步：提供设计稿

用户：请根据这个设计稿实现登录页面组件
[上传Figma截图]

要求：
- 使用Tailwind CSS
- 响应式设计
- 深色/浅色主题支持

# 第二步：Claude实现

Claude：已创建LoginForm组件，包含：
- 响应式布局
- 表单验证
- 主题切换

# 第三步：截图对比

用户：请截图当前效果，对比设计稿

Claude：[截图]
与设计稿的差异：
1. 按钮圆角应该是8px，当前是4px
2. 输入框高度应该是48px，当前是40px
3. 间距应该是24px，当前是16px

# 第四步：迭代修正

用户：请修正这些差异

Claude：已更新：
- rounded-lg → rounded-xl (8px圆角)
- h-10 → h-12 (48px高度)
- gap-4 → gap-6 (24px间距)

# 第五步：再次验证

用户：截图确认

Claude：[截图] 已与设计稿匹配

# 第六步：测试不同主题

用户：切换到深色主题截图

Claude：[截图] 深色主题效果

用户：深色主题的输入框背景太暗，请调整

Claude：已将深色主题输入框背景从bg-gray-800改为bg-gray-700

# 第七步：完成

用户：完成，请提交

Claude：已创建commit "feat: add LoginForm component with theme support"
```

**关键工具**：
- 浏览器截图能力
- 设计稿对比
- 迭代反馈

**效果**：
- UI还原度高
- 减少返工
- 开发效率提升

---

## 七、最佳实践总结

### 7.1 CLAUDE.md最佳实践

| 实践 | 说明 |
|------|------|
| 保持简洁 | 只包含必要信息 |
| 定期更新 | 项目变化时同步更新 |
| 添加强调 | 重要规则使用IMPORTANT标记 |
| 提供示例 | 复杂规则附带代码示例 |

### 7.2 指令编写最佳实践

| 糟糕 | 良好 |
|------|------|
| 模糊的指令 | 具体的指令 |
| 缺少上下文 | 提供文件路径和行号 |
| 没有约束 | 明确约束和边界 |
| 期望过高 | 分步骤执行 |

### 7.3 工作流选择

| 场景 | 推荐工作流 |
|------|------------|
| 新功能开发 | 探索-计划-编码-提交 |
| Bug修复 | 定位-测试-修复-验证 |
| UI开发 | 视觉迭代 |
| 代码质量 | TDD |
| 大型重构 | 多Claude协作 |

---

## 八、总结

Claude Code最佳实践的核心：

1. **充分利用CLAUDE.md**：让Claude理解项目上下文
2. **具体化指令**：越具体，结果越好
3. **选择合适的工作流**：匹配任务特点
4. **利用多Claude**：大型任务分解并行
5. **迭代优化**：不追求一次完美
