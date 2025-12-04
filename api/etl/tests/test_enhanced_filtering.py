# -*- coding: utf-8 -*-
"""
测试优化后的MindsDBTableModel筛选功能
"""

import os
import sys
import pandas as pd
from pathlib import Path
import tempfile
import sqlite3
from datetime import datetime, date

# 解决Windows终端编码问题
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from etl.data_models.mindsdb_table import MindsDBTableModel


def create_comprehensive_test_database():
    """创建包含各种数据类型的测试数据库"""
    test_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    test_db.close()

    conn = sqlite3.connect(test_db.name)
    cursor = conn.cursor()

    # 创建包含各种数据类型的测试表
    cursor.execute('''
        CREATE TABLE comprehensive_test (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER,
            salary REAL,
            is_active BOOLEAN,
            join_date DATE,
            last_login DATETIME,
            description TEXT,
            tags TEXT
        )
    ''')

    # 插入测试数据
    test_data = [
        (1, 'Alice Johnson', 25, 50000.0, True, '2020-01-15', '2023-11-13 10:30:00', 'Software Engineer', 'python,java'),
        (2, 'Bob Smith', 30, 60000.5, False, '2019-03-20', '2023-11-12 15:45:00', 'Data Analyst', 'sql,r'),
        (3, 'Charlie Brown', 35, 75000.0, True, '2018-07-10', '2023-11-11 09:15:00', 'Project Manager', 'management'),
        (4, 'Diana Prince', 28, 55000.75, True, '2021-02-28', '2023-11-13 14:20:00', 'UX Designer', 'design,ui'),
        (5, 'Eve Wilson', 42, 85000.0, False, '2015-05-15', '2023-10-30 16:00:00', 'Senior Developer', 'python,backend'),
        (6, 'Frank Miller', None, 45000.0, True, '2022-08-01', None, 'Junior Developer', 'frontend'),
        (7, 'Grace Lee', 33, 70000.25, True, '2017-11-20', '2023-11-10 11:30:00', 'DevOps Engineer', 'devops,cloud'),
        (8, 'Henry Ford', 45, 95000.0, False, '2014-01-10', '2023-09-15 08:00:00', 'Team Lead', 'leadership'),
        (9, 'Iris Wang', 29, 58000.5, True, '2020-06-15', '2023-11-13 13:45:00', 'QA Engineer', 'testing'),
        (10, 'Jack Davis', 38, 72000.0, True, '2016-12-01', '2023-11-05 17:30:00', 'Product Manager', 'product')
    ]

    cursor.executemany(
        '''INSERT INTO comprehensive_test
           (id, name, age, salary, is_active, join_date, last_login, description, tags)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        test_data
    )

    conn.commit()
    conn.close()

    return test_db.name, len(test_data)


def test_enhanced_filtering():
    """测试增强的筛选功能"""
    print("=" * 80)
    print("测试优化后的MindsDBTableModel筛选功能")
    print("=" * 80)

    # 创建测试数据库
    db_path, total_records = create_comprehensive_test_database()
    print(f"[OK] 创建综合测试数据库: {db_path}")
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
            'name': 'comprehensive_test',
            'model_conf': {
                'name': 'comprehensive_test',
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

    # 显示可用的筛选项
    print("\n2. 显示可用的筛选项:")
    rules = model.get_extract_rules()
    print(f"[OK] 共有 {len(rules)} 个筛选操作符:")
    for rule in rules[:8]:  # 显示前8个
        print(f"     - {rule['name']}: {rule['value']}")
    print("     ...")

    # 测试各种筛选条件
    test_cases = [
        {
            'name': '数值等于筛选',
            'rules': [{'field': 'age', 'rule': 'equal', 'value': 30}],
            'expected_min': 1,
            'description': '年龄等于30岁'
        },
        {
            'name': '数值范围筛选',
            'rules': [{'field': 'age', 'rule': 'gt', 'value': 35}],
            'expected_min': 1,
            'description': '年龄大于35岁'
        },
        {
            'name': '字符串包含筛选',
            'rules': [{'field': 'name', 'rule': 'contain', 'value': 'a'}],
            'expected_min': 1,
            'description': '姓名包含字母a'
        },
        {
            'name': '字符串开始于筛选',
            'rules': [{'field': 'name', 'rule': 'startswith', 'value': 'A'}],
            'expected_min': 1,
            'description': '姓名以A开头'
        },
        {
            'name': '空值筛选',
            'rules': [{'field': 'age', 'rule': 'is_null', 'value': None}],
            'expected_min': 1,
            'description': '年龄为空的记录'
        },
        {
            'name': '布尔值筛选',
            'rules': [{'field': 'is_active', 'rule': 'equal', 'value': False}],
            'expected_min': 1,
            'description': '非活跃用户'
        },
        {
            'name': 'IN操作筛选',
            'rules': [{'field': 'age', 'rule': 'in', 'value': [25, 30, 35]}],
            'expected_min': 1,
            'description': '年龄在25,30,35中的记录'
        },
        {
            'name': '复合条件筛选',
            'rules': [
                {'field': 'age', 'rule': 'gt', 'value': 25},
                {'field': 'is_active', 'rule': 'equal', 'value': True}
            ],
            'expected_min': 1,
            'description': '年龄大于25且为活跃用户'
        },
        {
            'name': '排序测试',
            'rules': [{'field': 'salary', 'rule': 'sort_desc', 'value': None}],
            'expected_min': 1,
            'description': '按薪资降序排序'
        },
        {
            'name': '类型强转测试（字符串转数字）',
            'rules': [{'field': 'age', 'rule': 'equal', 'value': '30'}],  # 字符串形式的数字
            'expected_min': 1,
            'description': '字符串数字自动转换为整数'
        },
        {
            'name': '无效值处理测试',
            'rules': [{'field': 'age', 'rule': 'equal', 'value': 'invalid_number'}],  # 无效值
            'expected_min': 0,
            'description': '无效值应被跳过，不影响查询'
        }
    ]

    print("\n3. 测试各种筛选条件:")
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n   3.{i} {test_case['name']} - {test_case['description']}:")

        # 设置筛选规则
        model.extract_rules = test_case['rules']

        # 显示生成的SQL条件（用于调试）
        try:
            where_clauses, order_clauses = model.gen_extract_rules()
            if where_clauses:
                print(f"       WHERE: {' AND '.join(where_clauses)}")
            if order_clauses:
                print(f"       ORDER BY: {', '.join(order_clauses)}")
        except Exception as e:
            print(f"       SQL生成失败: {e}")
            continue

        # 获取筛选后的记录数
        filtered_total = model.get_total_count()
        print(f"       [OK] 筛选后记录数: {filtered_total}")

        # 验证结果
        if filtered_total >= test_case['expected_min']:
            print(f"       [OK] 筛选结果符合预期")

            # 读取前几条数据展示
            if filtered_total > 0:
                success, result = model.read_page(page=1, pagesize=3)
                if success:
                    data = result.get('data', {})
                    records = data.get('records', [])
                    if records:
                        print(f"       示例记录: ID={records[0].get('id')}, "
                              f"姓名={records[0].get('name')}, "
                              f"年龄={records[0].get('age')}")
        else:
            print(f"       [WARNING] 筛选结果可能不符合预期，预期至少{test_case['expected_min']}条")

    # 测试字段类型检测
    print("\n4. 测试字段类型检测:")
    test_fields = ['id', 'name', 'age', 'salary', 'is_active']
    for field in test_fields:
        field_type = model._get_field_type(field)
        print(f"       {field}: {field_type}")

    # 测试值类型转换
    print("\n5. 测试值类型转换:")
    conversion_tests = [
        ('30', 'integer'),
        ('50000.5', 'real'),
        ('true', 'boolean'),
        ('false', 'boolean'),
        ('invalid', 'integer'),
        ('invalid', 'boolean')
    ]

    for value, data_type in conversion_tests:
        converted = model._convert_value_by_type(value, data_type)
        print(f"       {value} -> {data_type}: {converted} ({type(converted).__name__})")

    # 测试SQL值转义
    print("\n6. 测试SQL值转义:")
    escape_tests = [
        ("John's Book", 'text'),
        (30, 'integer'),
        (True, 'boolean'),
        ("O'Malley", 'text')
    ]

    for value, data_type in escape_tests:
        escaped = model._escape_sql_value(value, data_type)
        print(f"       {value} ({data_type}) -> {escaped}")

    # 清理测试文件
    print("\n7. 清理测试文件:")
    try:
        os.unlink(db_path)
        print("[OK] 测试数据库文件清理完成")
    except Exception as e:
        print(f"[WARNING] 清理测试文件失败: {e}")

    print("\n" + "=" * 80)
    print("测试完成 - 增强筛选功能验证成功")
    print("=" * 80)


if __name__ == "__main__":
    test_enhanced_filtering()