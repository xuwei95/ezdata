#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安装 MindsDB handlers 的 requirements
从环境变量 MINDSDB_HANDLERS 读取 handler 名称列表（逗号分隔），
然后在 mindsdb/integrations/handlers 目录下查找对应的 handler，
如果找到 requirements.txt 文件，则安装其中的依赖。
"""
import os
import sys
import subprocess
from pathlib import Path

def install_requirements(requirements_file, work_dir):
    """安装 requirements.txt 文件中的依赖"""
    try:
        print(f"正在安装: {requirements_file}")
        # 将 requirements_file 转换为相对于工作目录的路径
        # 工作目录设置为 api 目录，这样 requirements.txt 中的相对路径引用能正常工作
        # 例如: -r mindsdb/integrations/handlers/... 会解析为 api/mindsdb/integrations/handlers/...
        try:
            requirements_path = requirements_file.relative_to(work_dir)
        except ValueError:
            # 如果无法计算相对路径，使用绝对路径
            requirements_path = requirements_file.resolve()
        
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
            check=True,
            capture_output=True,
            text=True,
            cwd=str(work_dir)
        )
        print(f"✓ 成功安装: {requirements_file}")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 安装失败: {requirements_file}")
        print(f"错误: {e.stderr}")
        return False

def find_and_install_handler(handler_name, handlers_dir):
    """查找并安装指定 handler 的 requirements"""
    handler_name = handler_name.strip()
    if not handler_name:
        return False
    
    # 构建 handler 目录路径
    handler_dir = handlers_dir / f"{handler_name}_handler"
    
    # 检查目录是否存在
    if not handler_dir.exists() or not handler_dir.is_dir():
        print(f"⚠ 未找到 handler: {handler_name} (路径: {handler_dir})")
        return False
    
    # 查找 requirements.txt
    requirements_file = handler_dir / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"⚠ {handler_name} 没有 requirements.txt 文件")
        return False
    
    # 安装 requirements
    # 工作目录设置为 api 目录（脚本所在目录）
    script_dir = handlers_dir.parent.parent.parent  # api 目录
    return install_requirements(requirements_file, script_dir)

def main():
    """主函数"""
    # 获取环境变量
    handlers_env = os.environ.get("MINDSDB_HANDLERS", "")
    
    if not handlers_env:
        print("未设置 MINDSDB_HANDLERS 环境变量，跳过 handler 依赖安装")
        return
    
    # 获取当前脚本所在目录，然后定位到 mindsdb/integrations/handlers
    script_dir = Path(__file__).parent
    handlers_dir = script_dir / "mindsdb" / "integrations" / "handlers"
    
    if not handlers_dir.exists():
        print(f"错误: handlers 目录不存在: {handlers_dir}")
        sys.exit(1)
    
    # 按逗号切分 handler 名称
    handler_names = [name.strip() for name in handlers_env.split(",") if name.strip()]
    
    if not handler_names:
        print("MINDSDB_HANDLERS 环境变量为空，跳过 handler 依赖安装")
        return
    
    print(f"开始安装 {len(handler_names)} 个 handler 的依赖...")
    print(f"Handlers: {', '.join(handler_names)}")
    print(f"Handlers 目录: {handlers_dir}\n")
    
    success_count = 0
    failed_count = 0
    
    for handler_name in handler_names:
        print(f"\n处理 handler: {handler_name}")
        if find_and_install_handler(handler_name, handlers_dir):
            success_count += 1
        else:
            failed_count += 1
    
    print(f"\n安装完成: 成功 {success_count}, 失败 {failed_count}")
    
    if failed_count > 0:
        print("警告: 部分 handler 安装失败，但继续执行")
        # 不退出，允许继续构建

if __name__ == "__main__":
    main()

