# coding: utf-8
"""
HTTP模型测试
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from etl.registry import get_registry, get_reader
from etl.data_models.http_models import HttpApiModel, HttpHtmlModel, BaseHttpModel


def test_http_registration():
    """测试HTTP模型注册"""
    registry = get_registry()

    # 检查是否注册成功
    reader_map = registry.get_reader_map()

    assert 'http:None' in reader_map, "http:None 未注册"
    assert 'http:http_json' in reader_map, "http:http_json 未注册"
    assert 'http:http_html' in reader_map, "http:http_html 未注册"

    print("✓ HTTP模型注册成功")


def test_connection_args():
    """测试获取连接参数"""
    conn_args = BaseHttpModel.get_connection_args()

    assert 'url' in conn_args, "缺少url参数"
    assert conn_args['url']['required'] is True, "url应该是必填参数"
    assert 'method' in conn_args, "缺少method参数"
    assert 'headers' in conn_args, "缺少headers参数"
    assert 'timeout' in conn_args, "缺少timeout参数"

    print("✓ 连接参数定义正确")
    print(f"  连接参数: {list(conn_args.keys())}")


def test_api_form_config():
    """测试API模型表单配置"""
    form_config = HttpApiModel.get_form_config()

    assert len(form_config) > 0, "表单配置为空"

    # 检查是否包含auth_type字段
    fields = [item['field'] for item in form_config]
    assert 'auth_type' in fields, "缺少auth_type字段"

    print("✓ HTTP API模型表单配置正确")
    print(f"  配置字段: {fields}")


def test_html_form_config():
    """测试HTML模型表单配置"""
    form_config = HttpHtmlModel.get_form_config()

    assert len(form_config) > 0, "表单配置为空"

    # 检查是否包含auth_type字段
    fields = [item['field'] for item in form_config]
    assert 'auth_type' in fields, "缺少auth_type字段"

    print("✓ HTTP HTML模型表单配置正确")
    print(f"  配置字段: {fields}")


def test_create_api_reader():
    """测试创建HTTP API Reader"""
    model_info = {
        'source': {
            'type': 'http',
            'conn_conf': {
                'url': 'https://api.github.com',
                'method': 'GET'
            }
        },
        'model': {
            'type': 'http_json',
            'model_conf': {
                'auth_type': 'query,extract'
            }
        },
        'extract_info': {}
    }

    flag, reader = get_reader(model_info)

    assert flag is True, f"创建Reader失败: {reader}"
    assert isinstance(reader, HttpApiModel), "Reader类型不正确"
    assert reader.url == 'https://api.github.com', "URL未正确设置"
    assert reader.method == 'GET', "Method未正确设置"

    print("✓ HTTP API Reader创建成功")
    print(f"  Reader类型: {type(reader).__name__}")


def test_create_html_reader():
    """测试创建HTTP HTML Reader"""
    model_info = {
        'source': {
            'type': 'http',
            'conn_conf': {
                'url': 'https://www.example.com',
                'method': 'GET'
            }
        },
        'model': {
            'type': 'http_html',
            'model_conf': {
                'auth_type': 'query,extract'
            }
        },
        'extract_info': {}
    }

    flag, reader = get_reader(model_info)

    assert flag is True, f"创建Reader失败: {reader}"
    assert isinstance(reader, HttpHtmlModel), "Reader类型不正确"
    assert reader.url == 'https://www.example.com', "URL未正确设置"

    print("✓ HTTP HTML Reader创建成功")
    print(f"  Reader类型: {type(reader).__name__}")


def test_query_methods():
    """测试query方法存在性"""
    model_info = {
        'source': {
            'type': 'http',
            'conn_conf': {
                'url': 'https://api.github.com',
                'method': 'GET'
            }
        },
        'model': {
            'type': 'http_json',
            'model_conf': {
                'auth_type': 'query,extract'
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

    print("✓ 所有必要方法都已实现")


def test_html_res_fields():
    """测试HTML模型字段"""
    model_info = {
        'source': {
            'type': 'http',
            'conn_conf': {
                'url': 'https://www.example.com',
                'method': 'GET'
            }
        },
        'model': {
            'type': 'http_html',
            'model_conf': {
                'auth_type': 'query,extract'
            }
        },
        'extract_info': {}
    }

    flag, reader = get_reader(model_info)
    assert flag is True

    fields = reader.get_res_fields()
    assert len(fields) > 0, "字段列表为空"

    # 检查HTML相关字段
    field_names = [field['field_name'] for field in fields]
    assert 'html' in field_names, "缺少html字段"
    assert 'status_code' in field_names, "缺少status_code字段"

    print("✓ HTML模型字段配置正确")
    print(f"  字段: {field_names}")


def test_gen_models():
    """测试生成子模型"""
    model_info = {
        'source': {
            'type': 'http',
            'conn_conf': {
                'url': 'https://api.github.com',
                'method': 'GET'
            }
        },
        'model': {
            'type': 'http_json',
            'model_conf': {
                'auth_type': 'query,extract'
            }
        },
        'extract_info': {}
    }

    flag, reader = get_reader(model_info)
    assert flag is True

    # 检查gen_models方法
    assert hasattr(reader, 'gen_models'), "缺少gen_models方法"

    print("✓ gen_models方法存在")


def test_post_method():
    """测试POST方法配置"""
    model_info = {
        'source': {
            'type': 'http',
            'conn_conf': {
                'url': 'https://httpbin.org/post',
                'method': 'POST',
                'req_body': '{"key": "value"}',
                'headers': '{"Content-Type": "application/json"}'
            }
        },
        'model': {
            'type': 'http_json',
            'model_conf': {
                'auth_type': 'query,extract'
            }
        },
        'extract_info': {}
    }

    flag, reader = get_reader(model_info)
    assert flag is True
    assert reader.method == 'POST', "Method未正确设置为POST"
    assert isinstance(reader.req_body, dict), "req_body应该被解析为dict"
    assert isinstance(reader.headers, dict), "headers应该被解析为dict"

    print("✓ POST方法配置正确")


if __name__ == '__main__':
    print("=" * 60)
    print("开始测试 HTTP 模型")
    print("=" * 60)

    try:
        test_http_registration()
        test_connection_args()
        test_api_form_config()
        test_html_form_config()
        test_create_api_reader()
        test_create_html_reader()
        test_query_methods()
        test_html_res_fields()
        test_gen_models()
        test_post_method()

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
