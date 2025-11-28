# -*- coding: utf-8 -*-
"""
测试优化后的LocalFileModel连接方式（使用conn_conf）
"""

import os
import sys
import pandas as pd
from pathlib import Path

# 解决Windows终端编码问题
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from etl2.registry import get_registry
from etl2.data_models.local_file import LocalFileModel


def create_test_files():
    """创建测试文件"""
    test_dir = Path("test_files")
    test_dir.mkdir(exist_ok=True)

    # 创建CSV测试文件
    csv_data = {
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'age': [25, 30, 35, 40, 45],
        'city': ['Beijing', 'Shanghai', 'Guangzhou', 'Shenzhen', 'Hangzhou'],
        'salary': [50000.0, 60000.0, 70000.0, 80000.0, 90000.0]
    }
    csv_path = test_dir / "test.csv"
    pd.DataFrame(csv_data).to_csv(csv_path, index=False)
    print(f"创建CSV测试文件: {csv_path}")

    # 创建Excel测试文件
    excel_path = test_dir / "test.xlsx"
    with pd.ExcelWriter(excel_path) as writer:
        pd.DataFrame(csv_data).to_excel(writer, sheet_name='Sheet1', index=False)
        # 添加第二个sheet
        sales_data = {
            'product': ['Apple', 'Banana', 'Orange'],
            'price': [5.0, 3.0, 4.0],
            'quantity': [100, 200, 150]
        }
        pd.DataFrame(sales_data).to_excel(writer, sheet_name='Sales', index=False)
    print(f"创建Excel测试文件: {excel_path}")

    # 创建TSV测试文件
    tsv_path = test_dir / "test.tsv"
    pd.DataFrame(csv_data).to_csv(tsv_path, sep='\t', index=False)
    print(f"创建TSV测试文件: {tsv_path}")

    return csv_path, excel_path, tsv_path


def test_new_conn_conf_structure():
    """测试新的conn_conf连接结构"""
    print("=" * 80)
    print("测试优化后的LocalFileModel连接方式（使用conn_conf）")
    print("=" * 80)

    # 创建测试文件
    csv_path, excel_path, tsv_path = create_test_files()

    # 获取注册中心
    registry = get_registry()

    # 测试1: 使用新的conn_conf结构读取CSV文件
    print("\n1. 测试CSV文件读取（新conn_conf结构）:")
    csv_model_info_new = {
        'source': {
            'type': 'file',
            'conn_conf': {
                'path': str(csv_path),
                'encoding': 'utf-8',
                'delimiter': ','
            }
        },
        'model': {
            'name': 'test_csv_new',
            'type': 'None'
        },
        'extract_info': {
            'batch_size': 2
        }
    }

    success, csv_model_new = registry.get_reader(csv_model_info_new)
    if success:
        print(f"[OK] 成功创建CSV读取器（新结构）: {type(csv_model_new).__name__}")

        # 测试连接
        if csv_model_new.connect():
            print("[OK] CSV文件连接成功")

            # 测试获取模型信息
            info_prompt = csv_model_new.get_info_prompt()
            print("[OK] 模型信息:")
            for line in info_prompt.strip().split('\n')[:8]:  # 显示前8行
                print(f"     {line}")

            # 获取字段信息
            fields = csv_model_new.get_res_fields()
            print(f"[OK] 字段列表: {fields}")

            # 读取数据
            result = csv_model_new.read_page(page=1, pagesize=10)
            print(f"[OK] 读取数据:")
            print(result)

        else:
            print("[ERROR] CSV文件连接失败")
    else:
        print(f"[ERROR] 创建CSV读取器失败: {csv_model_new}")

    # 测试2: 使用直接类实例化（新conn_conf结构）
    print("\n2. 测试直接使用LocalFileModel类（新conn_conf结构）:")
    direct_model_info_new = {
        'source': {
            'type': 'file',
            'conn_conf': {
                'path': str(csv_path),
                'delimiter': ',',
                'encoding': 'utf-8'
            }
        },
        'model': {
            'name': 'direct_test_new',
            'type': 'None'
        },
        'extract_info': {
            'batch_size': 2
        }
    }

    local_file_model_new = LocalFileModel(direct_model_info_new)
    if local_file_model_new.connect():
        print("[OK] 直接使用LocalFileModel连接成功（新结构）")

        # 验证配置是否正确加载
        print(f"[OK] 文件路径: {local_file_model_new.file_path}")
        print(f"[OK] 编码: {local_file_model_new.encoding}")
        print(f"[OK] 分隔符: {local_file_model_new.delimiter}")
        print(f"[OK] 批处理大小: {local_file_model_new.chunk_size}")

        # 测试批量读取
        batches = list(local_file_model_new.read_batch())
        print(f"[OK] 批量读取结果 ({len(batches)} 个批次):")
        for i, batch in enumerate(batches):
            print(f"  批次 {i + 1}: {len(batch)} 行")

    else:
        print("[ERROR] 直接使用LocalFileModel连接失败")

    # 测试3: Excel文件读取（新conn_conf结构）
    print("\n3. 测试Excel文件读取（新conn_conf结构）:")
    excel_model_info_new = {
        'source': {
            'type': 'file',
            'conn_conf': {
                'path': str(excel_path),
                'sheet_name': 'Sales'  # 指定工作表
            }
        },
        'model': {
            'name': 'test_excel_new',
            'type': 'None'
        },
        'extract_info': {
            'batch_size': 10
        }
    }

    success, excel_model_new = registry.get_reader(excel_model_info_new)
    if success:
        print(f"[OK] 成功创建Excel读取器（新结构）: {type(excel_model_new).__name__}")

        # 测试连接
        if excel_model_new.connect():
            print("[OK] Excel文件连接成功")

            # 读取数据
            res = excel_model_new.read_page(page=1, pagesize=10)
            print(f"[OK] 读取Sales工作表数据:")
            print(res)

        else:
            print("[ERROR] Excel文件连接失败")
    else:
        print(f"[ERROR] 创建Excel读取器失败: {excel_model_new}")

    # 测试4: TSV文件读取（新conn_conf结构）
    print("\n4. 测试TSV文件读取（新conn_conf结构）:")
    tsv_model_info_new = {
        'source': {
            'type': 'file',
            'conn_conf': {
                'path': str(tsv_path),
                'delimiter': '\t',  # 明确指定分隔符
                'encoding': 'utf-8'
            }
        },
        'model': {
            'name': 'test_tsv_new',
            'type': 'None'
        },
        'extract_info': {
            'batch_size': 3
        }
    }

    success, tsv_model_new = registry.get_reader(tsv_model_info_new)
    if success:
        print(f"[OK] 成功创建TSV读取器（新结构）: {type(tsv_model_new).__name__}")

        # 测试连接
        if tsv_model_new.connect():
            print("[OK] TSV文件连接成功")

            # 读取数据
            res = tsv_model_new.read_page(page=1, pagesize=5)
            print(f"[OK] 读取TSV数据:")
            print(res)

        else:
            print("[ERROR] TSV文件连接失败")
    else:
        print(f"[ERROR] 创建TSV读取器失败: {tsv_model_new}")

    # 测试5: 连接参数定义
    print("\n5. 测试连接参数定义:")
    if 'local_file_model_new' in locals():
        conn_args = local_file_model_new.get_connection_args()
        print(f"[OK] 连接参数定义:")
        for param, config in conn_args.items():
            print(f"     - {param}: {config.get('description')} (类型: {config.get('type')}, 必需: {config.get('required')})")

    # 清理测试文件
    print("\n6. 清理测试文件:")
    import shutil
    import time
    if os.path.exists("test_files_conn_conf"):
        try:
            time.sleep(1)  # 等待文件释放
            shutil.rmtree("test_files_conn_conf")
            print("[OK] 测试文件清理完成")
        except Exception as e:
            print(f"[WARNING] 清理测试文件失败: {e}")

    print("\n" + "=" * 80)
    print("测试完成 - LocalFileModel连接方式优化成功")
    print("=" * 80)


if __name__ == "__main__":
    test_new_conn_conf_structure()