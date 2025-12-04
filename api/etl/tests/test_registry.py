# -*- coding: utf-8 -*-
"""
测试 registry 功能
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from etl import registry


def test_get_reader_map():
    """测试获取 reader map"""
    print("=" * 60)
    print("测试 get_reader_map()")
    print("=" * 60)

    reader_map = registry.get_reader_map()
    print(f"总共 {len(reader_map)} 个 reader")

    # 显示前 20 个
    for i, (key, value) in enumerate(reader_map.items()):
        if i < 20:
            print(f"  {key}: {value}")
        else:
            break
    print(f"  ... 还有 {len(reader_map) - 20} 个")
    print()


def test_get_writer_map():
    """测试获取 writer map"""
    print("=" * 60)
    print("测试 get_writer_map()")
    print("=" * 60)

    writer_map = registry.get_writer_map()
    print(f"总共 {len(writer_map)} 个 writer")

    # 显示前 20 个
    for i, (key, value) in enumerate(writer_map.items()):
        if i < 20:
            print(f"  {key}: {value}")
        else:
            break
    if len(writer_map) > 20:
        print(f"  ... 还有 {len(writer_map) - 20} 个")
    print()


def test_get_all_source_names():
    """测试获取所有数据源名称"""
    print("=" * 60)
    print("测试 get_all_source_names()")
    print("=" * 60)

    sources = registry.get_all_source_names()
    print(f"总共 {len(sources)} 个数据源")

    # 分组显示
    print("\n自定义数据源:")
    custom_sources = ['akshare', 'ccxt', 'kafka', 'mysql']
    for source in sources:
        if any(cs in source for cs in custom_sources):
            print(f"  - {source}")

    print("\nMindsDB 数据源（前 20 个）:")
    count = 0
    for source in sources:
        if not any(cs in source for cs in custom_sources):
            print(f"  - {source}")
            count += 1
            if count >= 20:
                print(f"  ... 还有 {len(sources) - count - len([s for s in sources if any(cs in s for cs in custom_sources)])} 个")
                break
    print()


def test_list_available_sources():
    """测试 list_available_sources 方法"""
    print("=" * 60)
    print("测试 list_available_sources()")
    print("=" * 60)

    reg = registry.get_registry()
    sources_info = reg.list_available_sources()

    print(f"总共 {sources_info['total']} 个数据源")
    print(f"\n自定义数据源 ({len(sources_info['custom'])} 个):")
    for source in sources_info['custom']:
        print(f"  - {source}")

    print(f"\nMindsDB DATA 数据源 ({len(sources_info['mindsdb_data'])} 个，显示前 20 个):")
    for i, source in enumerate(sources_info['mindsdb_data']):
        if i < 20:
            print(f"  - {source}")
        else:
            print(f"  ... 还有 {len(sources_info['mindsdb_data']) - 20} 个")
            break
    print()


def test_get_sub_models():
    """测试获取子模型（示例，需要真实连接）"""
    print("=" * 60)
    print("测试 get_sub_models() - 需要真实数据库连接")
    print("=" * 60)
    print("跳过此测试（需要配置真实的数据库连接）")
    print()

    # 示例代码（需要真实连接才能运行）:
    """
    model_info = {
        'source': {
            'type': 'postgres',
            'conn_conf': {
                'host': 'localhost',
                'port': 5432,
                'user': 'postgres',
                'password': 'password',
                'database': 'mydb'
            }
        },
        'model': {
            'type': 'sql'
        }
    }

    flag, models = registry.get_sub_models(model_info)
    if flag:
        print(f"找到 {len(models)} 个子模型:")
        for model in models[:5]:
            print(f"  - {model}")
    else:
        print(f"获取失败: {models}")
    """


if __name__ == '__main__':
    print("\n")
    print("*" * 60)
    print(" Registry 功能测试")
    print("*" * 60)
    print("\n")

    test_get_reader_map()
    test_get_writer_map()
    test_get_all_source_names()
    # test_list_available_sources()
    # test_get_sub_models()

    print("=" * 60)
    print("测试完成!")
    print("=" * 60)
