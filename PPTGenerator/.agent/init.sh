#!/bin/bash
# 课程反馈PPT自动生成器 - 初始化脚本
# 用于设置开发环境和运行测试

set -e

echo "=========================================="
echo "课程反馈PPT自动生成器 - 开发环境初始化"
echo "=========================================="

# 检查Python版本
echo ""
echo "[1/5] 检查Python版本..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Python版本: $python_version"

# 创建虚拟环境（如果不存在）
echo ""
echo "[2/5] 检查虚拟环境..."
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python -m venv venv
    echo "虚拟环境创建成功"
else
    echo "虚拟环境已存在"
fi

# 激活虚拟环境
echo ""
echo "[3/5] 激活虚拟环境..."
source venv/Scripts/activate 2>/dev/null || source venv/bin/activate
echo "虚拟环境已激活"

# 安装依赖
echo ""
echo "[4/5] 安装依赖包..."
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
echo "依赖安装完成"

# 检查项目结构
echo ""
echo "[5/5] 检查项目结构..."
required_dirs=("src" "src/core" "src/ui" "src/widgets" "src/utils" "config" "resources" "output" "templates")
for dir in "${required_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "创建目录: $dir"
        mkdir -p "$dir"
    fi
done

# 检查必要文件
required_files=("requirements.txt" "main.py" "templates/课程反馈.pptx")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "警告: 文件不存在 - $file"
    else
        echo "文件检查通过: $file"
    fi
done

echo ""
echo "=========================================="
echo "初始化完成！"
echo "=========================================="
echo ""
echo "运行测试: python -m pytest tests/"
echo "启动程序: python main.py"
echo ""
