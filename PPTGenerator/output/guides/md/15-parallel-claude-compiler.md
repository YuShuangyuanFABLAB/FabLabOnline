# 并行Claude编译器（Building C Compiler）

> 来源：https://www.anthropic.com/engineering/claude-c-compiler
> 发布日期：2026-02-05

---

## 一、项目概述

### 1.1 项目背景

使用Claude从零开始构建一个C语言编译器，展示AI辅助复杂系统开发的能力。

### 1.2 编译器结构

```
编译器架构：
├── 词法分析（Lexer）
│   └── 源代码 → Token流
├── 语法分析（Parser）
│   └── Token流 → AST
├── 语义分析（Semantic）
│   └── AST → 带类型的AST
├── 中间代码生成（IR）
│   └── AST → 中间表示
├── 优化（Optimizer）
│   └── IR → 优化后的IR
└── 代码生成（CodeGen）
    └── IR → 目标代码
```

### 1.3 开发方法

- 迭代式开发
- 测试驱动
- 模块化设计
- 持续重构

---

## 二、词法分析器

### 2.1 Token定义

```python
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional

class TokenType(Enum):
    """Token类型"""
    # 字面量
    INT_LITERAL = auto()
    FLOAT_LITERAL = auto()
    STRING_LITERAL = auto()
    CHAR_LITERAL = auto()

    # 标识符和关键字
    IDENTIFIER = auto()

    # 关键字
    INT = auto()
    FLOAT = auto()
    CHAR = auto()
    VOID = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    RETURN = auto()
    STRUCT = auto()

    # 运算符
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    EQ = auto()
    NE = auto()
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    ASSIGN = auto()

    # 分隔符
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    SEMICOLON = auto()
    COMMA = auto()

    # 特殊
    EOF = auto()

@dataclass
class Token:
    """Token"""
    type: TokenType
    value: any
    line: int
    column: int

class Lexer:
    """词法分析器"""

    KEYWORDS = {
        "int": TokenType.INT,
        "float": TokenType.FLOAT,
        "char": TokenType.CHAR,
        "void": TokenType.VOID,
        "if": TokenType.IF,
        "else": TokenType.ELSE,
        "while": TokenType.WHILE,
        "for": TokenType.FOR,
        "return": TokenType.RETURN,
        "struct": TokenType.STRUCT,
    }

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens = []

    def tokenize(self) -> List[Token]:
        """词法分析"""
        while self.pos < len(self.source):
            self.skip_whitespace()

            if self.pos >= len(self.source):
                break

            char = self.source[self.pos]

            # 处理注释
            if char == '/' and self.peek() == '/':
                self.skip_line_comment()
                continue
            elif char == '/' and self.peek() == '*':
                self.skip_block_comment()
                continue

            # 处理数字
            if char.isdigit():
                self.read_number()
                continue

            # 处理标识符和关键字
            if char.isalpha() or char == '_':
                self.read_identifier()
                continue

            # 处理字符串
            if char == '"':
                self.read_string()
                continue

            # 处理字符
            if char == "'":
                self.read_char()
                continue

            # 处理运算符和分隔符
            self.read_operator()

        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens

    def skip_whitespace(self):
        """跳过空白"""
        while self.pos < len(self.source) and self.source[self.pos].isspace():
            if self.source[self.pos] == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.pos += 1

    def skip_line_comment(self):
        """跳过行注释"""
        while self.pos < len(self.source) and self.source[self.pos] != '\n':
            self.pos += 1

    def skip_block_comment(self):
        """跳过块注释"""
        self.pos += 2  # 跳过 /*
        while self.pos < len(self.source) - 1:
            if self.source[self.pos] == '*' and self.source[self.pos + 1] == '/':
                self.pos += 2
                return
            self.pos += 1

    def peek(self, offset: int = 1) -> Optional[str]:
        """查看下一个字符"""
        pos = self.pos + offset
        if pos < len(self.source):
            return self.source[pos]
        return None

    def read_number(self):
        """读取数字"""
        start = self.pos
        has_dot = False

        while self.pos < len(self.source):
            char = self.source[self.pos]
            if char.isdigit():
                self.pos += 1
            elif char == '.' and not has_dot:
                has_dot = True
                self.pos += 1
            else:
                break

        value = self.source[start:self.pos]
        if has_dot:
            self.tokens.append(Token(TokenType.FLOAT_LITERAL, float(value), self.line, self.column))
        else:
            self.tokens.append(Token(TokenType.INT_LITERAL, int(value), self.line, self.column))

        self.column += self.pos - start

    def read_identifier(self):
        """读取标识符"""
        start = self.pos

        while self.pos < len(self.source):
            char = self.source[self.pos]
            if char.isalnum() or char == '_':
                self.pos += 1
            else:
                break

        value = self.source[start:self.pos]

        # 检查是否为关键字
        token_type = self.KEYWORDS.get(value, TokenType.IDENTIFIER)
        self.tokens.append(Token(token_type, value, self.line, self.column))
        self.column += self.pos - start

    def read_string(self):
        """读取字符串"""
        self.pos += 1  # 跳过开头引号
        start = self.pos

        while self.pos < len(self.source) and self.source[self.pos] != '"':
            if self.source[self.pos] == '\\':
                self.pos += 1
            self.pos += 1

        value = self.source[start:self.pos]
        self.pos += 1  # 跳过结尾引号
        self.tokens.append(Token(TokenType.STRING_LITERAL, value, self.line, self.column))

    def read_char(self):
        """读取字符"""
        self.pos += 1  # 跳过开头引号
        char = self.source[self.pos]

        if char == '\\':
            self.pos += 1
            char = self.escape_char(self.source[self.pos])

        self.pos += 2  # 跳过字符和结尾引号
        self.tokens.append(Token(TokenType.CHAR_LITERAL, char, self.line, self.column))

    def escape_char(self, char: str) -> str:
        """转义字符"""
        escapes = {'n': '\n', 't': '\t', 'r': '\r', '\\': '\\', "'": "'", '"': '"'}
        return escapes.get(char, char)

    def read_operator(self):
        """读取运算符"""
        char = self.source[self.pos]
        next_char = self.peek()

        operators = {
            '+': TokenType.PLUS,
            '-': TokenType.MINUS,
            '*': TokenType.STAR,
            '/': TokenType.SLASH,
            '%': TokenType.PERCENT,
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
            '{': TokenType.LBRACE,
            '}': TokenType.RBRACE,
            '[': TokenType.LBRACKET,
            ']': TokenType.RBRACKET,
            ';': TokenType.SEMICOLON,
            ',': TokenType.COMMA,
        }

        double_operators = {
            '==': TokenType.EQ,
            '!=': TokenType.NE,
            '<=': TokenType.LE,
            '>=': TokenType.GE,
            '&&': TokenType.AND,
            '||': TokenType.OR,
        }

        # 检查双字符运算符
        if next_char and char + next_char in double_operators:
            self.tokens.append(Token(double_operators[char + next_char], char + next_char, self.line, self.column))
            self.pos += 2
            self.column += 2
        elif char in operators:
            self.tokens.append(Token(operators[char], char, self.line, self.column))
            self.pos += 1
            self.column += 1
        elif char == '<':
            self.tokens.append(Token(TokenType.LT, char, self.line, self.column))
            self.pos += 1
        elif char == '>':
            self.tokens.append(Token(TokenType.GT, char, self.line, self.column))
            self.pos += 1
        elif char == '=':
            self.tokens.append(Token(TokenType.ASSIGN, char, self.line, self.column))
            self.pos += 1
        elif char == '!':
            self.tokens.append(Token(TokenType.NOT, char, self.line, self.column))
            self.pos += 1
        else:
            raise SyntaxError(f"未知字符: {char} at line {self.line}")

# 使用示例
source = """
int main() {
    int x = 10;
    int y = 20;
    return x + y;
}
"""

lexer = Lexer(source)
tokens = lexer.tokenize()
for token in tokens:
    print(token)
```

---

## 三、语法分析器

### 3.1 AST节点定义

```python
from abc import ABC, abstractmethod
from typing import List, Optional

class ASTNode(ABC):
    """AST节点基类"""
    pass

@dataclass
class Program(ASTNode):
    """程序"""
    declarations: List[ASTNode]

@dataclass
class FunctionDecl(ASTNode):
    """函数声明"""
    return_type: str
    name: str
    params: List['Param']
    body: 'Block'

@dataclass
class Param(ASTNode):
    """参数"""
    type: str
    name: str

@dataclass
class Block(ASTNode):
    """代码块"""
    statements: List[ASTNode]

@dataclass
class VarDecl(ASTNode):
    """变量声明"""
    var_type: str
    name: str
    init: Optional[ASTNode] = None

@dataclass
class IfStmt(ASTNode):
    """if语句"""
    condition: ASTNode
    then_branch: ASTNode
    else_branch: Optional[ASTNode] = None

@dataclass
class WhileStmt(ASTNode):
    """while语句"""
    condition: ASTNode
    body: ASTNode

@dataclass
class ForStmt(ASTNode):
    """for语句"""
    init: Optional[ASTNode]
    condition: Optional[ASTNode]
    update: Optional[ASTNode]
    body: ASTNode

@dataclass
class ReturnStmt(ASTNode):
    """return语句"""
    value: Optional[ASTNode]

@dataclass
class ExprStmt(ASTNode):
    """表达式语句"""
    expr: ASTNode

@dataclass
class BinaryExpr(ASTNode):
    """二元表达式"""
    left: ASTNode
    op: str
    right: ASTNode

@dataclass
class UnaryExpr(ASTNode):
    """一元表达式"""
    op: str
    operand: ASTNode

@dataclass
class CallExpr(ASTNode):
    """函数调用"""
    name: str
    args: List[ASTNode]

@dataclass
class VarExpr(ASTNode):
    """变量表达式"""
    name: str

@dataclass
class IntLiteral(ASTNode):
    """整数字面量"""
    value: int

@dataclass
class FloatLiteral(ASTNode):
    """浮点数字面量"""
    value: float

@dataclass
class StringLiteral(ASTNode):
    """字符串字面量"""
    value: str

class Parser:
    """语法分析器"""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current(self) -> Token:
        """当前Token"""
        return self.tokens[self.pos]

    def peek(self, offset: int = 1) -> Token:
        """查看Token"""
        pos = self.pos + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return self.tokens[-1]  # EOF

    def consume(self, expected: TokenType) -> Token:
        """消费Token"""
        if self.current().type != expected:
            raise SyntaxError(f"期望 {expected}, 得到 {self.current().type} at line {self.current().line}")
        token = self.current()
        self.pos += 1
        return token

    def match(self, *types: TokenType) -> bool:
        """匹配Token类型"""
        return self.current().type in types

    def parse(self) -> Program:
        """解析程序"""
        declarations = []

        while not self.match(TokenType.EOF):
            declarations.append(self.parse_declaration())

        return Program(declarations)

    def parse_declaration(self) -> ASTNode:
        """解析声明"""
        type_token = self.parse_type()
        name = self.consume(TokenType.IDENTIFIER).value

        if self.match(TokenType.LPAREN):
            return self.parse_function(type_token, name)
        else:
            return self.parse_global_var(type_token, name)

    def parse_type(self) -> str:
        """解析类型"""
        if self.match(TokenType.INT, TokenType.FLOAT, TokenType.CHAR, TokenType.VOID):
            type_name = self.current().value
            self.pos += 1
            return type_name
        raise SyntaxError(f"期望类型, 得到 {self.current().type}")

    def parse_function(self, return_type: str, name: str) -> FunctionDecl:
        """解析函数"""
        self.consume(TokenType.LPAREN)
        params = self.parse_params()
        self.consume(TokenType.RPAREN)
        body = self.parse_block()

        return FunctionDecl(return_type, name, params, body)

    def parse_params(self) -> List[Param]:
        """解析参数列表"""
        params = []

        if not self.match(TokenType.RPAREN):
            params.append(self.parse_param())

            while self.match(TokenType.COMMA):
                self.consume(TokenType.COMMA)
                params.append(self.parse_param())

        return params

    def parse_param(self) -> Param:
        """解析参数"""
        type_name = self.parse_type()
        name = self.consume(TokenType.IDENTIFIER).value
        return Param(type_name, name)

    def parse_block(self) -> Block:
        """解析代码块"""
        self.consume(TokenType.LBRACE)
        statements = []

        while not self.match(TokenType.RBRACE):
            statements.append(self.parse_statement())

        self.consume(TokenType.RBRACE)
        return Block(statements)

    def parse_statement(self) -> ASTNode:
        """解析语句"""
        if self.match(TokenType.IF):
            return self.parse_if()
        elif self.match(TokenType.WHILE):
            return self.parse_while()
        elif self.match(TokenType.FOR):
            return self.parse_for()
        elif self.match(TokenType.RETURN):
            return self.parse_return()
        elif self.match(TokenType.LBRACE):
            return self.parse_block()
        elif self.match(TokenType.INT, TokenType.FLOAT, TokenType.CHAR):
            return self.parse_var_decl()
        else:
            return self.parse_expr_stmt()

    def parse_if(self) -> IfStmt:
        """解析if语句"""
        self.consume(TokenType.IF)
        self.consume(TokenType.LPAREN)
        condition = self.parse_expression()
        self.consume(TokenType.RPAREN)
        then_branch = self.parse_statement()

        else_branch = None
        if self.match(TokenType.ELSE):
            self.consume(TokenType.ELSE)
            else_branch = self.parse_statement()

        return IfStmt(condition, then_branch, else_branch)

    def parse_while(self) -> WhileStmt:
        """解析while语句"""
        self.consume(TokenType.WHILE)
        self.consume(TokenType.LPAREN)
        condition = self.parse_expression()
        self.consume(TokenType.RPAREN)
        body = self.parse_statement()

        return WhileStmt(condition, body)

    def parse_for(self) -> ForStmt:
        """解析for语句"""
        self.consume(TokenType.FOR)
        self.consume(TokenType.LPAREN)

        # init
        init = None
        if not self.match(TokenType.SEMICOLON):
            init = self.parse_expression()
        self.consume(TokenType.SEMICOLON)

        # condition
        condition = None
        if not self.match(TokenType.SEMICOLON):
            condition = self.parse_expression()
        self.consume(TokenType.SEMICOLON)

        # update
        update = None
        if not self.match(TokenType.RPAREN):
            update = self.parse_expression()
        self.consume(TokenType.RPAREN)

        body = self.parse_statement()

        return ForStmt(init, condition, update, body)

    def parse_return(self) -> ReturnStmt:
        """解析return语句"""
        self.consume(TokenType.RETURN)

        value = None
        if not self.match(TokenType.SEMICOLON):
            value = self.parse_expression()

        self.consume(TokenType.SEMICOLON)
        return ReturnStmt(value)

    def parse_var_decl(self) -> VarDecl:
        """解析变量声明"""
        var_type = self.parse_type()
        name = self.consume(TokenType.IDENTIFIER).value

        init = None
        if self.match(TokenType.ASSIGN):
            self.consume(TokenType.ASSIGN)
            init = self.parse_expression()

        self.consume(TokenType.SEMICOLON)
        return VarDecl(var_type, name, init)

    def parse_expr_stmt(self) -> ExprStmt:
        """解析表达式语句"""
        expr = self.parse_expression()
        self.consume(TokenType.SEMICOLON)
        return ExprStmt(expr)

    def parse_expression(self) -> ASTNode:
        """解析表达式"""
        return self.parse_assignment()

    def parse_assignment(self) -> ASTNode:
        """解析赋值表达式"""
        expr = self.parse_comparison()

        if self.match(TokenType.ASSIGN):
            self.consume(TokenType.ASSIGN)
            value = self.parse_assignment()
            return BinaryExpr(expr, '=', value)

        return expr

    def parse_comparison(self) -> ASTNode:
        """解析比较表达式"""
        expr = self.parse_additive()

        while self.match(TokenType.LT, TokenType.LE, TokenType.GT, TokenType.GE, TokenType.EQ, TokenType.NE):
            op = self.current().value
            self.pos += 1
            right = self.parse_additive()
            expr = BinaryExpr(expr, op, right)

        return expr

    def parse_additive(self) -> ASTNode:
        """解析加减表达式"""
        expr = self.parse_multiplicative()

        while self.match(TokenType.PLUS, TokenType.MINUS):
            op = self.current().value
            self.pos += 1
            right = self.parse_multiplicative()
            expr = BinaryExpr(expr, op, right)

        return expr

    def parse_multiplicative(self) -> ASTNode:
        """解析乘除表达式"""
        expr = self.parse_unary()

        while self.match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self.current().value
            self.pos += 1
            right = self.parse_unary()
            expr = BinaryExpr(expr, op, right)

        return expr

    def parse_unary(self) -> ASTNode:
        """解析一元表达式"""
        if self.match(TokenType.MINUS, TokenType.NOT):
            op = self.current().value
            self.pos += 1
            operand = self.parse_unary()
            return UnaryExpr(op, operand)

        return self.parse_primary()

    def parse_primary(self) -> ASTNode:
        """解析基本表达式"""
        if self.match(TokenType.INT_LITERAL):
            value = self.current().value
            self.pos += 1
            return IntLiteral(value)

        if self.match(TokenType.FLOAT_LITERAL):
            value = self.current().value
            self.pos += 1
            return FloatLiteral(value)

        if self.match(TokenType.STRING_LITERAL):
            value = self.current().value
            self.pos += 1
            return StringLiteral(value)

        if self.match(TokenType.IDENTIFIER):
            name = self.current().value
            self.pos += 1

            # 函数调用
            if self.match(TokenType.LPAREN):
                self.consume(TokenType.LPAREN)
                args = self.parse_args()
                self.consume(TokenType.RPAREN)
                return CallExpr(name, args)

            return VarExpr(name)

        if self.match(TokenType.LPAREN):
            self.consume(TokenType.LPAREN)
            expr = self.parse_expression()
            self.consume(TokenType.RPAREN)
            return expr

        raise SyntaxError(f"意外的Token: {self.current().type}")

    def parse_args(self) -> List[ASTNode]:
        """解析参数列表"""
        args = []

        if not self.match(TokenType.RPAREN):
            args.append(self.parse_expression())

            while self.match(TokenType.COMMA):
                self.consume(TokenType.COMMA)
                args.append(self.parse_expression())

        return args
```

---

## 四、代码生成器

### 4.1 目标代码生成

```python
class CodeGenerator:
    """代码生成器 - 生成x86-64汇编"""

    def __init__(self):
        self.output = []
        self.label_count = 0
        self.variables = {}  # 变量到栈偏移的映射
        self.stack_offset = 0

    def generate(self, program: Program) -> str:
        """生成代码"""
        self.output = []

        # 汇编头部
        self.emit(".section .data")
        self.emit(".section .text")

        for decl in program.declarations:
            self.generate_declaration(decl)

        return "\n".join(self.output)

    def emit(self, instruction: str):
        """输出指令"""
        self.output.append(instruction)

    def new_label(self) -> str:
        """生成新标签"""
        label = f".L{self.label_count}"
        self.label_count += 1
        return label

    def generate_declaration(self, decl: ASTNode):
        """生成声明代码"""
        if isinstance(decl, FunctionDecl):
            self.generate_function(decl)

    def generate_function(self, func: FunctionDecl):
        """生成函数代码"""
        self.variables = {}
        self.stack_offset = 0

        # 函数标签
        self.emit(f".globl {func.name}")
        self.emit(f"{func.name}:")

        # 函数序言
        self.emit("pushq %rbp")
        self.emit("movq %rsp, %rbp")

        # 分配栈空间（先预留足够空间）
        self.emit("subq $256, %rsp")

        # 生成函数体
        self.generate_block(func.body)

        # 函数返回（如果没有显式return）
        self.emit("movq $0, %rax")
        self.emit("leave")
        self.emit("ret")

    def generate_block(self, block: Block):
        """生成代码块"""
        for stmt in block.statements:
            self.generate_statement(stmt)

    def generate_statement(self, stmt: ASTNode):
        """生成语句"""
        if isinstance(stmt, VarDecl):
            self.generate_var_decl(stmt)
        elif isinstance(stmt, ReturnStmt):
            self.generate_return(stmt)
        elif isinstance(stmt, IfStmt):
            self.generate_if(stmt)
        elif isinstance(stmt, WhileStmt):
            self.generate_while(stmt)
        elif isinstance(stmt, ExprStmt):
            self.generate_expression(stmt.expr)
        elif isinstance(stmt, Block):
            self.generate_block(stmt)

    def generate_var_decl(self, decl: VarDecl):
        """生成变量声明"""
        # 分配栈空间
        self.stack_offset += 8
        self.variables[decl.name] = self.stack_offset

        # 如果有初始化
        if decl.init:
            self.generate_expression(decl.init)
            self.emit(f"movq %rax, -{self.stack_offset}(%rbp)")

    def generate_return(self, stmt: ReturnStmt):
        """生成return语句"""
        if stmt.value:
            self.generate_expression(stmt.value)

        self.emit("leave")
        self.emit("ret")

    def generate_if(self, stmt: IfStmt):
        """生成if语句"""
        else_label = self.new_label()
        end_label = self.new_label()

        # 条件
        self.generate_expression(stmt.condition)
        self.emit("cmpq $0, %rax")
        self.emit(f"je {else_label}")

        # then分支
        self.generate_statement(stmt.then_branch)
        self.emit(f"jmp {end_label}")

        # else分支
        self.emit(f"{else_label}:")
        if stmt.else_branch:
            self.generate_statement(stmt.else_branch)

        self.emit(f"{end_label}:")

    def generate_while(self, stmt: WhileStmt):
        """生成while语句"""
        start_label = self.new_label()
        end_label = self.new_label()

        self.emit(f"{start_label}:")

        # 条件
        self.generate_expression(stmt.condition)
        self.emit("cmpq $0, %rax")
        self.emit(f"je {end_label}")

        # 循环体
        self.generate_statement(stmt.body)
        self.emit(f"jmp {start_label}")

        self.emit(f"{end_label}:")

    def generate_expression(self, expr: ASTNode):
        """生成表达式"""
        if isinstance(expr, IntLiteral):
            self.emit(f"movq ${expr.value}, %rax")

        elif isinstance(expr, FloatLiteral):
            # 浮点数处理
            pass

        elif isinstance(expr, VarExpr):
            offset = self.variables.get(expr.name, 0)
            self.emit(f"movq -{offset}(%rbp), %rax")

        elif isinstance(expr, BinaryExpr):
            self.generate_binary(expr)

        elif isinstance(expr, UnaryExpr):
            self.generate_unary(expr)

        elif isinstance(expr, CallExpr):
            self.generate_call(expr)

    def generate_binary(self, expr: BinaryExpr):
        """生成二元表达式"""
        # 特殊处理赋值
        if expr.op == '=':
            self.generate_expression(expr.right)
            offset = self.variables.get(expr.left.name, 0)
            self.emit(f"movq %rax, -{offset}(%rbp)")
            return

        # 生成右操作数
        self.generate_expression(expr.right)
        self.emit("pushq %rax")

        # 生成左操作数
        self.generate_expression(expr.left)
        self.emit("popq %rcx")  # 右操作数在rcx

        # 执行运算
        if expr.op == '+':
            self.emit("addq %rcx, %rax")
        elif expr.op == '-':
            self.emit("subq %rcx, %rax")
        elif expr.op == '*':
            self.emit("imulq %rcx, %rax")
        elif expr.op == '/':
            self.emit("cqto")  # 符号扩展
            self.emit("idivq %rcx")
        elif expr.op == '<':
            self.emit("cmpq %rcx, %rax")
            self.emit("setl %al")
            self.emit("movzbq %al, %rax")
        elif expr.op == '>':
            self.emit("cmpq %rcx, %rax")
            self.emit("setg %al")
            self.emit("movzbq %al, %rax")
        elif expr.op == '==':
            self.emit("cmpq %rcx, %rax")
            self.emit("sete %al")
            self.emit("movzbq %al, %rax")

    def generate_unary(self, expr: UnaryExpr):
        """生成一元表达式"""
        self.generate_expression(expr.operand)

        if expr.op == '-':
            self.emit("negq %rax")
        elif expr.op == '!':
            self.emit("notq %rax")

    def generate_call(self, expr: CallExpr):
        """生成函数调用"""
        # 保存参数
        for i, arg in enumerate(expr.args):
            self.generate_expression(arg)
            self.emit("pushq %rax")

        # 调用函数
        self.emit(f"call {expr.name}")

        # 清理参数
        if expr.args:
            cleanup = len(expr.args) * 8
            self.emit(f"addq ${cleanup}, %rsp")
```

---

## 五、完整编译器

### 5.1 编译器主类

```python
class CCompiler:
    """C编译器"""

    def __init__(self):
        self.lexer = None
        self.parser = None
        self.codegen = CodeGenerator()

    def compile(self, source: str, output_file: str = None) -> str:
        """编译源代码"""
        # 词法分析
        self.lexer = Lexer(source)
        tokens = self.lexer.tokenize()

        # 语法分析
        self.parser = Parser(tokens)
        ast = self.parser.parse()

        # 代码生成
        assembly = self.codegen.generate(ast)

        # 如果指定了输出文件
        if output_file:
            with open(output_file, 'w') as f:
                f.write(assembly)

        return assembly

    def compile_to_executable(self, source: str, output: str):
        """编译到可执行文件"""
        # 生成汇编
        asm_file = output.replace('.exe', '.s')
        assembly = self.compile(source, asm_file)

        # 调用gcc汇编和链接
        import subprocess
        subprocess.run(['gcc', '-o', output, asm_file], check=True)

# 使用示例
compiler = CCompiler()

source = """
int main() {
    int x = 10;
    int y = 20;
    int z = x + y;
    return z;
}
"""

assembly = compiler.compile(source)
print(assembly)
```

---

## 六、最佳实践

### 6.1 开发策略

| 阶段 | 重点 |
|------|------|
| 词法分析 | 完整的Token定义 |
| 语法分析 | 清晰的AST结构 |
| 语义分析 | 类型检查 |
| 代码生成 | 正确性优先 |

### 6.2 测试策略

- 单元测试每个阶段
- 使用简单测试用例开始
- 逐步增加复杂度
- 回归测试

---

## 七、总结

构建编译器的关键：

1. **模块化设计**：每个阶段独立
2. **迭代开发**：从简单到复杂
3. **充分测试**：保证正确性
4. **清晰的数据结构**：Token、AST
