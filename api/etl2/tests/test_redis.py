# coding: utf-8
"""
Redis模型测试
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from etl2.registry import get_registry, get_reader
from etl2.data_models.redis_models import (
    RedisStringModel,
    RedisListModel,
    RedisMapModel,
    RedisListStreamModel,
    BaseRedisModel
)


def test_redis_registration():
    """测试Redis模型注册"""
    registry = get_registry()

    # 检查是否注册成功
    reader_map = registry.get_reader_map()
    writer_map = registry.get_writer_map()

    assert 'redis:None' in reader_map, "redis:None 未注册"
    assert 'redis:redis_string' in reader_map, "redis:redis_string 未注册"
    assert 'redis:redis_list' in reader_map, "redis:redis_list 未注册"
    assert 'redis:redis_map' in reader_map, "redis:redis_map 未注册"

    # 检查是否标记为可写
    assert 'redis:None' in writer_map, "redis:None 未标记为可写"
    assert 'redis:redis_string' in writer_map, "redis:redis_string 未标记为可写"
    assert 'redis:redis_list' in writer_map, "redis:redis_list 未标记为可写"
    assert 'redis:redis_map' in writer_map, "redis:redis_map 未标记为可写"

    print("✓ Redis模型注册成功")
    print(f"  Reader类型: {list([k for k in reader_map.keys() if k.startswith('redis')])}")
    print(f"  Writer类型: {list([k for k in writer_map.keys() if k.startswith('redis')])}")


def test_connection_args():
    """测试获取连接参数"""
    conn_args = BaseRedisModel.get_connection_args()

    assert 'host' in conn_args, "缺少host参数"
    assert conn_args['host']['required'] is True, "host应该是必填参数"
    assert 'port' in conn_args, "缺少port参数"
    assert 'password' in conn_args, "缺少password参数"
    assert 'db' in conn_args, "缺少db参数"

    print("✓ 连接参数定义正确")
    print(f"  连接参数: {list(conn_args.keys())}")


def test_string_model_form_config():
    """测试String模型表单配置"""
    form_config = RedisStringModel.get_form_config()

    assert len(form_config) > 0, "表单配置为空"

    # 检查字段
    fields = [item['field'] for item in form_config]
    assert 'redis_key' in fields, "缺少redis_key字段"
    assert 'auth_type' in fields, "缺少auth_type字段"

    print("✓ Redis String模型表单配置正确")
    print(f"  配置字段: {fields}")


def test_list_model_form_config():
    """测试List模型表单配置"""
    form_config = RedisListModel.get_form_config()

    assert len(form_config) > 0, "表单配置为空"

    # 检查字段
    fields = [item['field'] for item in form_config]
    assert 'redis_key' in fields, "缺少redis_key字段"
    assert 'auth_type' in fields, "缺少auth_type字段"

    print("✓ Redis List模型表单配置正确")
    print(f"  配置字段: {fields}")


def test_create_string_reader():
    """测试创建Redis String Reader"""
    model_info = {
        'source': {
            'type': 'redis',
            'conn_conf': {
                'host': 'localhost',
                'port': 6379,
                'password': '',
                'db': 0
            }
        },
        'model': {
            'type': 'redis_string',
            'model_conf': {
                'redis_key': 'test:string',
                'auth_type': 'query,extract,load'
            }
        },
        'extract_info': {}
    }

    flag, reader = get_reader(model_info)

    assert flag is True, f"创建Reader失败: {reader}"
    assert isinstance(reader, RedisStringModel), "Reader类型不正确"
    assert reader.redis_key == 'test:string', "Redis key未正确设置"

    print("✓ Redis String Reader创建成功")
    print(f"  Reader类型: {type(reader).__name__}")


def test_create_list_reader():
    """测试创建Redis List Reader"""
    model_info = {
        'source': {
            'type': 'redis',
            'conn_conf': {
                'host': 'localhost',
                'port': 6379,
                'password': '',
                'db': 0
            }
        },
        'model': {
            'type': 'redis_list',
            'model_conf': {
                'redis_key': 'test:list',
                'auth_type': 'query,extract,load'
            }
        },
        'extract_info': {}
    }

    flag, reader = get_reader(model_info)

    assert flag is True, f"创建Reader失败: {reader}"
    assert isinstance(reader, RedisListModel), "Reader类型不正确"
    assert reader.redis_key == 'test:list', "Redis key未正确设置"

    print("✓ Redis List Reader创建成功")
    print(f"  Reader类型: {type(reader).__name__}")


def test_create_map_reader():
    """测试创建Redis Map Reader"""
    model_info = {
        'source': {
            'type': 'redis',
            'conn_conf': {
                'host': 'localhost',
                'port': 6379,
                'password': '',
                'db': 0
            }
        },
        'model': {
            'type': 'redis_map',
            'model_conf': {
                'redis_key': 'test:hash',
                'auth_type': 'query,extract,load'
            }
        },
        'extract_info': {}
    }

    flag, reader = get_reader(model_info)

    assert flag is True, f"创建Reader失败: {reader}"
    assert isinstance(reader, RedisMapModel), "Reader类型不正确"
    assert reader.redis_key == 'test:hash', "Redis key未正确设置"

    print("✓ Redis Map Reader创建成功")
    print(f"  Reader类型: {type(reader).__name__}")


def test_query_methods():
    """测试query方法存在性"""
    model_info = {
        'source': {
            'type': 'redis',
            'conn_conf': {
                'host': 'localhost',
                'port': 6379,
                'password': '',
                'db': 0
            }
        },
        'model': {
            'type': 'redis_string',
            'model_conf': {
                'redis_key': 'test:string',
                'auth_type': 'query,extract,load'
            }
        },
        'extract_info': {}
    }

    flag, reader = get_reader(model_info)
    assert flag is True

    # 检查关键方法
    assert hasattr(reader, 'query'), "缺少query方法"
    assert hasattr(reader, 'connect'), "缺少connect方法"
    assert hasattr(reader, 'read_page'), "缺少read_page方法"
    assert hasattr(reader, 'read_batch'), "缺少read_batch方法"
    assert hasattr(reader, 'get_res_fields'), "缺少get_res_fields方法"
    assert hasattr(reader, 'write'), "缺少write方法"
    assert hasattr(reader, 'gen_models'), "缺少gen_models方法"

    print("✓ 所有必要方法都已实现")


def test_string_res_fields():
    """测试String模型字段"""
    model_info = {
        'source': {
            'type': 'redis',
            'conn_conf': {
                'host': 'localhost',
                'port': 6379,
                'password': '',
                'db': 0
            }
        },
        'model': {
            'type': 'redis_string',
            'model_conf': {
                'redis_key': 'test:string',
                'auth_type': 'query,extract,load'
            }
        },
        'extract_info': {}
    }

    flag, reader = get_reader(model_info)
    assert flag is True

    fields = reader.get_res_fields()
    assert len(fields) > 0, "字段列表为空"

    # 检查String相关字段
    field_names = [field['field_name'] for field in fields]
    assert 'value' in field_names, "缺少value字段"

    print("✓ String模型字段配置正确")
    print(f"  字段: {field_names}")


def test_list_res_fields():
    """测试List模型字段"""
    model_info = {
        'source': {
            'type': 'redis',
            'conn_conf': {
                'host': 'localhost',
                'port': 6379,
                'password': '',
                'db': 0
            }
        },
        'model': {
            'type': 'redis_list',
            'model_conf': {
                'redis_key': 'test:list',
                'auth_type': 'query,extract,load'
            }
        },
        'extract_info': {}
    }

    flag, reader = get_reader(model_info)
    assert flag is True

    fields = reader.get_res_fields()
    assert len(fields) > 0, "字段列表为空"

    # 检查List相关字段
    field_names = [field['field_name'] for field in fields]
    assert 'value' in field_names, "缺少value字段"
    assert 'index' in field_names, "缺少index字段"

    print("✓ List模型字段配置正确")
    print(f"  字段: {field_names}")


def test_map_res_fields():
    """测试Map模型字段"""
    model_info = {
        'source': {
            'type': 'redis',
            'conn_conf': {
                'host': 'localhost',
                'port': 6379,
                'password': '',
                'db': 0
            }
        },
        'model': {
            'type': 'redis_map',
            'model_conf': {
                'redis_key': 'test:hash',
                'auth_type': 'query,extract,load'
            }
        },
        'extract_info': {}
    }

    flag, reader = get_reader(model_info)
    assert flag is True

    fields = reader.get_res_fields()
    assert len(fields) > 0, "字段列表为空"

    # 检查Hash相关字段
    field_names = [field['field_name'] for field in fields]
    assert 'key' in field_names, "缺少key字段"
    assert 'value' in field_names, "缺少value字段"

    print("✓ Map模型字段配置正确")
    print(f"  字段: {field_names}")


def test_gen_models():
    """测试生成子模型"""
    model_info = {
        'source': {
            'type': 'redis',
            'conn_conf': {
                'host': 'localhost',
                'port': 6379,
                'password': '',
                'db': 0
            }
        },
        'model': {
            'type': 'redis_string',
            'model_conf': {
                'redis_key': 'test:string',
                'auth_type': 'query,extract,load'
            }
        },
        'extract_info': {}
    }

    flag, reader = get_reader(model_info)
    assert flag is True

    # 检查gen_models方法
    assert hasattr(reader, 'gen_models'), "缺少gen_models方法"

    print("✓ gen_models方法存在")


def test_stream_model():
    """测试Stream模型"""
    model_info = {
        'source': {
            'type': 'redis',
            'conn_conf': {
                'host': 'localhost',
                'port': 6379,
                'password': '',
                'db': 0
            }
        },
        'model': {
            'type': 'redis_list_stream',
            'model_conf': {
                'redis_key': 'test:stream',
                'auth_type': 'query,extract'
            }
        },
        'extract_info': {}
    }

    flag, reader = get_reader(model_info)
    assert flag is True
    assert isinstance(reader, RedisListStreamModel), "Reader类型不正确"

    print("✓ Redis Stream模型创建成功")


if __name__ == '__main__':
    print("=" * 60)
    print("开始测试 Redis 模型")
    print("=" * 60)

    try:
        test_redis_registration()
        test_connection_args()
        test_string_model_form_config()
        test_list_model_form_config()
        test_create_string_reader()
        test_create_list_reader()
        test_create_map_reader()
        test_query_methods()
        test_string_res_fields()
        test_list_res_fields()
        test_map_res_fields()
        test_gen_models()
        test_stream_model()

        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
