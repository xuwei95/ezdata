# coding: utf-8
"""
Prometheus模型测试
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from etl.registry import get_registry, get_reader
from etl.data_models.prometheus_models import PromQlModel, PromMetricModel


def test_prometheus_registration():
    """测试Prometheus模型注册"""
    registry = get_registry()

    # 检查是否注册成功
    reader_map = registry.get_reader_map()

    assert 'prometheus:None' in reader_map, "prometheus:None 未注册"
    assert 'prometheus:promql' in reader_map, "prometheus:promql 未注册"
    assert 'prometheus:metric' in reader_map, "prometheus:metric 未注册"

    print("✓ Prometheus模型注册成功")


def test_connection_args():
    """测试获取连接参数"""
    from etl.data_models.prometheus_models import BasePromModel

    conn_args = BasePromModel.get_connection_args()

    assert 'url' in conn_args, "缺少url参数"
    assert conn_args['url']['required'] is True, "url应该是必填参数"
    assert 'disable_ssl' in conn_args, "缺少disable_ssl参数"

    print("✓ 连接参数定义正确")
    print(f"  连接参数: {list(conn_args.keys())}")


def test_promql_form_config():
    """测试PromQL模型表单配置"""
    form_config = PromQlModel.get_form_config()

    assert len(form_config) > 0, "表单配置为空"

    # 检查是否包含promql字段
    fields = [item['field'] for item in form_config]
    assert 'promql' in fields, "缺少promql字段"
    assert 'auth_type' in fields, "缺少auth_type字段"

    print("✓ PromQL模型表单配置正确")
    print(f"  配置字段: {fields}")


def test_metric_form_config():
    """测试Metric模型表单配置"""
    form_config = PromMetricModel.get_form_config()

    assert len(form_config) > 0, "表单配置为空"

    # 检查是否包含name字段
    fields = [item['field'] for item in form_config]
    assert 'name' in fields, "缺少name字段"
    assert 'auth_type' in fields, "缺少auth_type字段"

    print("✓ Metric模型表单配置正确")
    print(f"  配置字段: {fields}")


def test_create_promql_reader():
    """测试创建PromQL Reader"""
    model_info = {
        'source': {
            'type': 'prometheus',
            'conn_conf': {
                'url': 'http://localhost:9090'
            }
        },
        'model': {
            'type': 'promql',
            'model_conf': {
                'promql': 'up',
                'auth_type': 'query,extract'
            }
        },
        'extract_info': {}
    }

    flag, reader = get_reader(model_info)

    assert flag is True, f"创建Reader失败: {reader}"
    assert isinstance(reader, PromQlModel), "Reader类型不正确"
    assert reader.promql == 'up', "PromQL未正确设置"

    print("✓ PromQL Reader创建成功")
    print(f"  Reader类型: {type(reader).__name__}")


def test_create_metric_reader():
    """测试创建Metric Reader"""
    model_info = {
        'source': {
            'type': 'prometheus',
            'conn_conf': {
                'url': 'http://localhost:9090'
            }
        },
        'model': {
            'type': 'metric',
            'model_conf': {
                'name': 'node_cpu_seconds_total',
                'auth_type': 'query,extract'
            }
        },
        'extract_info': {}
    }

    flag, reader = get_reader(model_info)

    assert flag is True, f"创建Reader失败: {reader}"
    assert isinstance(reader, PromMetricModel), "Reader类型不正确"
    assert reader.metric == 'node_cpu_seconds_total', "Metric名称未正确设置"

    print("✓ Metric Reader创建成功")
    print(f"  Reader类型: {type(reader).__name__}")


def test_query_methods():
    """测试query方法存在性"""
    model_info = {
        'source': {
            'type': 'prometheus',
            'conn_conf': {
                'url': 'http://localhost:9090'
            }
        },
        'model': {
            'type': 'promql',
            'model_conf': {
                'promql': 'up',
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
    assert hasattr(reader, 'get_extract_rules'), "缺少get_extract_rules方法"

    print("✓ 所有必要方法都已实现")


def test_extract_rules():
    """测试筛选规则"""
    model_info = {
        'source': {
            'type': 'prometheus',
            'conn_conf': {
                'url': 'http://localhost:9090'
            }
        },
        'model': {
            'type': 'promql',
            'model_conf': {
                'promql': 'up',
                'auth_type': 'query,extract'
            }
        },
        'extract_info': {}
    }

    flag, reader = get_reader(model_info)
    assert flag is True

    rules = reader.get_extract_rules()
    assert len(rules) > 0, "筛选规则为空"

    # 检查时间相关规则
    rule_values = [rule['value'] for rule in rules]
    assert 'start_time' in rule_values, "缺少start_time规则"
    assert 'end_time' in rule_values, "缺少end_time规则"
    assert 'step' in rule_values, "缺少step规则"

    print("✓ 筛选规则配置正确")
    print(f"  规则: {rule_values}")


if __name__ == '__main__':
    print("=" * 60)
    print("开始测试 Prometheus 模型")
    print("=" * 60)

    try:
        test_prometheus_registration()
        test_connection_args()
        test_promql_form_config()
        test_metric_form_config()
        test_create_promql_reader()
        test_create_metric_reader()
        test_query_methods()
        test_extract_rules()

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
