# -*- coding: utf-8 -*-
"""
统一SQL规则构建器
用于table和file模型的筛选拼接SQL规则
"""

import logging
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


class SQLRuleBuilder:
    """
    统一SQL规则构建器
    支持标准化的操作符和类型安全的SQL条件生成
    """

    # 支持的操作符定义 - 简化版本
    SUPPORTED_OPERATORS = [
        {'name': '等于', 'value': 'eq'},
        {'name': '不等于', 'value': 'neq'},
        {'name': '包含', 'value': 'contain'},
        {'name': '不包含', 'value': 'not_contain'}
    ]

    def __init__(self, field_type_getter=None):
        """
        初始化SQL规则构建器

        Args:
            field_type_getter: 获取字段类型的函数，签名(field_name) -> field_type
        """
        self.field_type_getter = field_type_getter

    def build_sql_clauses(self, rules: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
        """
        从规则列表构建SQL子句

        Args:
            rules: 规则列表，每个规则包含field, rule, value等字段

        Returns:
            Tuple[List[str], List[str]]: (where_clauses, order_clauses)
        """
        where_clauses = []
        order_clauses = []

        for rule_dict in rules:
            field = rule_dict.get('field')
            operator = rule_dict.get('rule')
            value = rule_dict.get('value')

            if not field:
                continue

            # 获取字段类型
            field_type = self._get_field_type(field)

            # 只处理 eq, neq, contain, not_contain 四种操作符

            # 转换值类型
            converted_value = self._convert_value_by_type(value, field_type)
            if converted_value is None and operator not in ['is_null', 'is_not_null']:
                logger.warning(f"跳过无效的筛选条件: {field} {operator} {value}")
                continue

            # 生成SQL条件
            sql_clause = self._build_where_clause(field, operator, converted_value, field_type)
            if sql_clause:
                where_clauses.append(sql_clause)

        return where_clauses, order_clauses

    def build_sql_query(self,
                       table_name: str,
                       rules: List[Dict[str, Any]],
                       select_columns: List[str] = None,
                       limit: int = None,
                       offset: int = None) -> str:
        """
        构建完整的SQL查询

        Args:
            table_name: 表名
            rules: 规则列表
            select_columns: 选择的列，None表示选择所有列
            limit: 限制行数
            offset: 偏移量

        Returns:
            str: 完整的SQL查询语句
        """
        where_clauses, order_clauses = self.build_sql_clauses(rules)

        # SELECT子句
        if select_columns:
            columns_str = ', '.join(select_columns)
        else:
            columns_str = '*'

        sql_parts = [f"SELECT {columns_str} FROM {table_name}"]

        # WHERE子句
        if where_clauses:
            sql_parts.append(f"WHERE {' AND '.join(where_clauses)}")

        # ORDER BY子句
        if order_clauses:
            sql_parts.append(f"ORDER BY {', '.join(order_clauses)}")

        # LIMIT和OFFSET子句
        if limit is not None:
            sql_parts.append(f"LIMIT {limit}")
        if offset is not None and offset > 0:
            sql_parts.append(f"OFFSET {offset}")

        return ' '.join(sql_parts)

    def get_supported_operators(self) -> List[Dict[str, str]]:
        """
        获取支持的操作符列表

        Returns:
            List[Dict[str, str]]: 支持的操作符列表
        """
        return self.SUPPORTED_OPERATORS.copy()

    def _get_field_type(self, field_name: str) -> str:
        """
        获取字段类型

        Args:
            field_name: 字段名

        Returns:
            str: 字段类型
        """
        if self.field_type_getter:
            return self.field_type_getter(field_name) or 'text'
        return 'text'

    def _convert_value_by_type(self, value: Any, field_type: str) -> Any:
        """
        根据字段类型转换值

        Args:
            value: 原始值
            field_type: 字段类型

        Returns:
            Any: 转换后的值
        """
        if value is None or value == '':
            return None

        # 处理列表值（用于IN操作）
        if isinstance(value, (list, tuple)):
            converted_list = []
            for v in value:
                converted = self._convert_single_value_by_type(v, field_type)
                if converted is not None:
                    converted_list.append(converted)
            return converted_list

        return self._convert_single_value_by_type(value, field_type)

    def _convert_single_value_by_type(self, value: Any, field_type: str) -> Any:
        """
        转换单个值

        Args:
            value: 原始值
            field_type: 字段类型

        Returns:
            Any: 转换后的值
        """
        try:
            field_type = field_type.lower()

            # 数值类型
            if field_type in ['int', 'integer', 'bigint', 'smallint', 'tinyint']:
                return int(float(str(value)))  # 支持字符串数字转换

            # 浮点类型
            elif field_type in ['float', 'double', 'decimal', 'numeric', 'real']:
                return float(str(value))

            # 日期时间类型
            elif field_type in ['date', 'datetime', 'timestamp', 'time']:
                if isinstance(value, str):
                    return value  # 保持原样，让数据库处理

            # 布尔类型
            elif field_type in ['boolean', 'bool']:
                if isinstance(value, str):
                    value_lower = value.lower()
                    if value_lower in ['true', '1', 'yes', 'on']:
                        return True
                    elif value_lower in ['false', '0', 'no', 'off']:
                        return False
                    else:
                        return None  # 无法转换，跳过
                return bool(value)

            # 文本类型（默认）
            else:
                return str(value) if value is not None else None

        except (ValueError, TypeError) as e:
            logger.warning(f"值转换失败: {value} -> {field_type}, 错误: {str(e)}")
            return None  # 转换失败，返回None表示跳过此条件

    def _build_where_clause(self, field: str, operator: str, value: Any, field_type: str) -> Optional[str]:
        """
        构建WHERE子句 - 简化版本，只支持eq, neq, contain, not_contain

        Args:
            field: 字段名
            operator: 操作符
            value: 值
            field_type: 字段类型

        Returns:
            Optional[str]: SQL WHERE子句，失败时返回None
        """
        try:
            if operator == 'eq':
                sql_value = self._escape_sql_value(value, field_type)
                return f"{field} = {sql_value}"

            elif operator == 'neq':
                sql_value = self._escape_sql_value(value, field_type)
                return f"{field} != {sql_value}"

            elif operator == 'contain':
                # 字符串包含操作
                if isinstance(value, str):
                    escaped_value = value.replace("'", "''")
                    return f"CAST({field} AS VARCHAR) LIKE '%{escaped_value}%'"

            elif operator == 'not_contain':
                # 字符串不包含操作
                if isinstance(value, str):
                    escaped_value = value.replace("'", "''")
                    return f"CAST({field} AS VARCHAR) NOT LIKE '%{escaped_value}%'"

        except Exception as e:
            logger.error(f"生成SQL条件失败: {field} {operator} {value}, 错误: {str(e)}")
            return None

    def _escape_sql_value(self, value: Any, field_type: str) -> str:
        """
        根据类型转义SQL值

        Args:
            value: 值
            field_type: 字段类型

        Returns:
            str: 转义后的SQL值
        """
        # 处理列表值
        if isinstance(value, (list, tuple)):
            return '(' + ', '.join(self._escape_sql_value(v, field_type) for v in value) + ')'

        # 处理None值
        if value is None:
            return 'NULL'

        # 数值类型
        if field_type.lower() in ['int', 'integer', 'bigint', 'smallint', 'tinyint',
                                 'float', 'double', 'decimal', 'numeric', 'real']:
            return str(value)

        # 布尔类型
        elif field_type.lower() in ['boolean', 'bool']:
            return '1' if value else '0'

        # 字符串类型（包括日期时间）
        else:
            # 转义单引号
            if isinstance(value, str):
                escaped = value.replace("'", "''")
                return f"'{escaped}'"
            else:
                escaped = str(value).replace("'", "''")
                return f"'{escaped}'"


# 便捷函数
def create_sql_rule_builder(field_type_getter=None) -> SQLRuleBuilder:
    """
    创建SQL规则构建器实例

    Args:
        field_type_getter: 获取字段类型的函数

    Returns:
        SQLRuleBuilder: SQL规则构建器实例
    """
    return SQLRuleBuilder(field_type_getter)


def get_supported_filter_operators() -> List[Dict[str, str]]:
    """
    获取支持的筛选操作符列表

    Returns:
        List[Dict[str, str]]: 支持的操作符列表
    """
    builder = SQLRuleBuilder()
    return builder.get_supported_operators()