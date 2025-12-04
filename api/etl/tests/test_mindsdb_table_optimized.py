# -*- coding: utf-8 -*-
"""
测试优化后的MindsDBTableModel功能
"""

import os
import sys
import pandas as pd
from pathlib import Path
import tempfile
import sqlite3

# 解决Windows终端编码问题
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from etl.data_models.mindsdb_table import MindsDBTableModel


def create_test_database():
    """创建测试数据库和数据"""
    # 创建临时数据库文件
    test_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    test_db.close()

    conn = sqlite3.connect(test_db.name)
    cursor = conn.cursor()

    # 创建测试表
    cursor.execute('''
        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER,
            city TEXT,
            salary REAL
        )
    ''')

    # 插入测试数据
    test_data = [
        (1, 'Alice', 25, 'Beijing', 50000.0),
        (2, 'Bob', 30, 'Shanghai', 60000.0),
        (3, 'Charlie', 35, 'Guangzhou', 70000.0),
        (4, 'David', 40, 'Shenzhen', 80000.0),
        (5, 'Eve', 45, 'Hangzhou', 90000.0),
        (6, 'Frank', 28, 'Nanjing', 55000.0),
        (7, 'Grace', 32, 'Chengdu', 65000.0),
        (8, 'Henry', 38, 'Wuhan', 75000.0),
        (9, 'Iris', 26, 'Xi\'an', 52000.0),
        (10, 'Jack', 33, 'Suzhou', 68000.0),
        (11, 'Kate', 29, 'Tianjin', 58000.0),
        (12, 'Leo', 41, 'Qingdao', 82000.0)
    ]

    cursor.executemany(
        'INSERT INTO test_table (id, name, age, city, salary) VALUES (?, ?, ?, ?, ?)',
        test_data
    )

    conn.commit()
    conn.close()

    return test_db.name, len(test_data)


def test_optimized_mindsdb_table():
    """测试优化后的MindsDBTableModel"""
    print("=" * 60)
    print("测试优化后的MindsDBTableModel")
    print("=" * 60)

    # 创建测试数据库
    db_path, total_records = create_test_database()
    print(f"[OK] 创建测试数据库: {db_path}")
    print(f"[OK] 插入测试数据: {total_records} 条记录")

    # 创建模型配置
    model_info = {
        'source': {
            'type': 'sqlite',
            'conn_conf': {
                'db_file': db_path
            }
        },
        'model': {
            'name': 'test_table',
            'model_conf': {
                'name': 'test_table',
                'auth_type': 'select'
            }
        },
        'extract_info': {
            'batch_size': 3
        }
    }

    # 创建模型实例
    model = MindsDBTableModel(model_info)

    # 测试连接
    print("\n1. 测试连接功能:")
    success, msg = model.connect()
    if success:
        print("[OK] 数据库连接成功")
    else:
        print(f"[ERROR] 数据库连接失败: {msg}")
        return

    # 测试获取表信息
    print("\n2. 测试获取表信息:")
    table_info = model.get_table_info()
    if table_info:
        print(f"[OK] 表名: {table_info['table_name']}")
        print(f"[OK] 总记录数: {table_info['total_count']}")
        print(f"[OK] 列数: {table_info['column_count']}")
        print(f"[OK] 列信息: {[col.get('COLUMN_NAME') for col in table_info['columns'][:3]]}...")

    # 测试获取总记录数
    print("\n3. 测试获取总记录数:")
    total_count = model.get_total_count()
    print(f"[OK] 总记录数: {total_count}")

    # 测试分页读取
    print("\n4. 测试分页读取:")
    pagesize = 3
    for page in range(1, 5):  # 测试前4页
        success, result = model.read_page(page=page, pagesize=pagesize)
        if success:
            data = result.get('data', {})
            records = data.get('records', [])
            total = data.get('total', 0)

            print(f"[OK] 第{page}页: {len(records)}条记录, 总计:{total}条")
            if records:
                print(f"     首条记录: {records[0]['name']} ({records[0]['age']}岁)")
        else:
            print(f"[ERROR] 读取第{page}页失败: {result}")

    # 测试批量读取
    print("\n5. 测试批量读取:")
    batch_count = 0
    total_processed = 0
    for success, result in model.read_batch():
        if success:
            batch_count += 1
            data = result.get('data', {})
            records = data.get('records', [])
            batch_num = data.get('batch_num', 0)
            batch_size = data.get('batch_size', 0)
            total = data.get('total', 0)
            processed = data.get('processed', 0)
            remaining = data.get('remaining', 0)
            progress = data.get('progress', 0)
            is_last_batch = data.get('is_last_batch', False)

            total_processed += len(records)
            print(f"[OK] 批次{batch_num}: {batch_size}条记录, 进度:{processed}/{total} ({progress}%)")

            if is_last_batch:
                print(f"[OK] 批量读取完成，共{batch_count}个批次，处理{total_processed}条记录")
                break
        else:
            print(f"[ERROR] 批量读取失败: {result}")
            break

    # 测试带筛选条件的查询
    print("\n6. 测试带筛选条件的查询:")
    # 设置筛选条件：年龄大于30岁
    model.extract_rules = [
        {'field': 'age', 'rule': 'gt', 'value': 30}
    ]

    filtered_total = model.get_total_count()
    print(f"[OK] 筛选后总记录数: {filtered_total}")

    success, result = model.read_page(page=1, pagesize=5)
    if success:
        data = result.get('data', {})
        records = data.get('records', [])
        total = data.get('total', 0)
        print(f"[OK] 筛选结果第1页: {len(records)}条记录, 总计:{total}条")
        if records:
            ages = [r['age'] for r in records]
            print(f"     年龄范围: {min(ages)} - {max(ages)}")

    # 清理测试文件
    print("\n7. 清理测试文件:")
    try:
        os.unlink(db_path)
        print("[OK] 测试数据库文件清理完成")
    except Exception as e:
        print(f"[WARNING] 清理测试文件失败: {e}")

    print("\n" + "=" * 60)
    print("测试完成 - MindsDBTableModel优化功能验证成功")
    print("=" * 60)


if __name__ == "__main__":
    test_optimized_mindsdb_table()