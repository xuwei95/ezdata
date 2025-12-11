# coding: utf-8
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from etl.data_models.mindsdb_table import MindsDBTableModel
import logging
from elasticsearch import helpers
import pandas as pd
import json
from utils.common_utils import gen_json_response, df_to_list
logger = logging.getLogger(__name__)


class ElasticsearchTableModel(MindsDBTableModel):
    """
    Elasticsearch table model, inherits from MindsDBTableModel
    Override write method to use ES native bulk write API
    Override query method to support native ES DSL queries
    """

    def __init__(self, model_info):
        super().__init__(model_info)

    def get_info_prompt(self, model_prompt=''):
        """
        获取使用提示及数据库元数据信息
        """
        if not self.standalone_handler:
            self.connect()
        try:
            # 获取索引 mapping
            es_client = self.handler.connection
            mapping = es_client.indices.get_mapping(index=self.table_name)
            mapping_info = json.dumps(mapping, indent=2, ensure_ascii=False)

            info_prompt = f"""
Elasticsearch 数据源封装类
# 使用示例：
# 1. 执行原生查询返回原始结果
query_body = {{"query": {{"match_all": {{}}}}, "size": 100}}
response = reader.query(query_body)
records = [hit['_source'] for hit in response['hits']['hits']]
df = pd.DataFrame(records)

# DataSource type: {self.db_type}

# MetaData:

# Index: {self.table_name}
# Mapping:
{mapping_info}
                """
            return info_prompt
        except Exception as e:
            logger.error(f"获取元数据信息失败: {e}")
            return f"获取元数据信息失败: {e}"

    def get_search_type_list(self):
        """
        获取可用高级查询类型
        """
        return [{
            'name': 'query_body',
            'value': 'query_body',
            "default": ''
        }]

    def _build_native_query(self):
        """
        从筛选规则构建 Elasticsearch DSL 查询
        Returns:
            (dict, list): ES query DSL 和 sort_list
        """
        query_body = {
            "bool": {
                "must": []
            }
        }
        sort_list = []
        if not self.extract_rules:
            return {"match_all": {}}, []

        # 处理筛选规则
        for rule in self.extract_rules:
            field = rule.get('field')
            operator = rule.get('rule')
            value = rule.get('value')

            if not field or not operator:
                continue
            # 根据操作符构建查询条件
            if operator == 'eq':
                query_body["bool"]["must"].append({"term": {field: value}})
            elif operator == 'neq':
                if "must_not" not in query_body["bool"]:
                    query_body["bool"]["must_not"] = []
                query_body["bool"]["must_not"].append({"term": {field: value}})
            elif operator == 'gt':
                query_body["bool"]["must"].append({"range": {field: {"gt": value}}})
            elif operator == 'gte':
                query_body["bool"]["must"].append({"range": {field: {"gte": value}}})
            elif operator == 'lt':
                query_body["bool"]["must"].append({"range": {field: {"lt": value}}})
            elif operator == 'lte':
                query_body["bool"]["must"].append({"range": {field: {"lte": value}}})
            elif operator == 'contain':
                # ES 使用 wildcard 查询实现 LIKE
                wildcard_value = value.replace('%', '*').replace('_', '?')
                query_body["bool"]["must"].append({"wildcard": {field: wildcard_value}})
            elif operator == 'not_contain':
                # ES 使用 wildcard 查询实现 LIKE
                wildcard_value = value.replace('%', '*').replace('_', '?')
                query_body["bool"]["must_not"].append({"wildcard": {field: wildcard_value}})
            elif operator in ['sort_desc', 'sort_asc']:
                sort_order = 'desc' if operator == 'sort_desc' else 'asc'
                sort_list.append({field: {"order": sort_order}})

        # 如果没有添加任何条件，返回 match_all
        if not query_body["bool"]["must"] and not query_body["bool"].get("must_not"):
            return {"match_all": {}}, sort_list

        return query_body, sort_list

    def _prepare_query_dsl(self):
        """
        准备查询 DSL，优先使用自定义 query_body，否则从 extract_rules 构建
        Returns:
            (dict, list, bool): query_dsl, sort_list, is_custom_query
                - query_dsl: 查询 DSL（可能是完整的 search body 或仅 query 部分）
                - sort_list: 排序列表
                - is_custom_query: 是否是自定义查询（True 表示直接使用，不添加分页等参数）
        """
        query_dsl = None
        sort_list = []
        is_custom_query = False

        # 检查 extract_rules 中是否有自定义 query_body
        if hasattr(self, 'extract_rules') and self.extract_rules:
            query_body_rules = [i for i in self.extract_rules if i.get('field') == 'search_text' and i.get('rule') == 'query_body' and i.get('value')]
            if query_body_rules:
                query_body_str = query_body_rules[0].get('value')
                # query_body 不是默认值或空，直接使用自定义 query_body
                if query_body_str not in ['{"match_all": {}}', '']:
                    try:
                        query_dsl = json.loads(query_body_str)
                        is_custom_query = True
                        logger.info(f"Using custom query_body from extract_rules: {query_dsl}")
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse query_body JSON: {e}, falling back to default")

        # 如果没有自定义 query_body，则从 extract_rules 构建查询
        if query_dsl is None:
            query_dsl, sort_list = self._build_native_query()

        return query_dsl, sort_list, is_custom_query

    def query(self, query_body):
        """
        执行原生 Elasticsearch 查询，返回原始数据

        Args:
            query_body: Elasticsearch 查询体（完整的 search body）

        Returns:
            dict: ES 原始响应结果
        """
        if not self.handler:
            flag, msg = self.connect()
            if not flag:
                raise RuntimeError(f'connect failed: {msg}')

        logger.info(f"ES Query Body: {json.dumps(query_body, indent=2)}")

        # 执行查询
        es_client = self.handler.connection
        response = es_client.search(
            index=self.table_name,
            body=query_body
        )

        logger.info(f"ES Query returned {len(response.get('hits', {}).get('hits', []))} hits")
        return response

    def read_page(self, page=1, pagesize=20):
        """
        分页读取数据，解析条件生成 query 并执行查询
        注意：如果是自定义 query_body，将直接使用自定义查询，禁用分页参数

        Args:
            page: 页码，从1开始
            pagesize: 每页记录数

        Returns:
            (bool, dict): 成功标志和响应数据
        """
        if not self.standalone_handler:
            flag, msg = self.connect()
            if not flag:
                return False, msg
        try:
            # 准备查询 DSL
            query_dsl, sort_list, is_custom_query = self._prepare_query_dsl()

            # 如果是自定义查询，直接使用，不添加分页参数
            if is_custom_query:
                search_body = query_dsl
                logger.info("Using custom query body, pagination disabled")
            else:
                # 构建完整的搜索请求，添加分页参数
                search_body = {
                    "query": query_dsl,
                    "size": pagesize,
                    "from": (page - 1) * pagesize
                }
                if sort_list:
                    search_body["sort"] = sort_list

            # 调用 query 方法执行查询
            response = self.query(search_body)

            # 解析结果
            hits = response.get('hits', {}).get('hits', [])
            records = [{'_id': hit['_id'], **hit.get('_source', {})} for hit in hits]

            # 获取总数
            total_info = response.get('hits', {}).get('total', {})
            total_count = total_info.get('value', 0) if isinstance(total_info, dict) else total_info
            res_data = {
                'records': records,
                'total': total_count,
                'aggregations': response.get('aggregations', {}),
                'pagination': False if is_custom_query else True
            }
            return True, gen_json_response(data=res_data)
        except Exception as e:
            logger.error(f"读取分页数据失败: {str(e)}")
            return False, str(e)

    def read_batch(self):
        """
        批量读取数据，使用 Elasticsearch scroll 查询分批读取
        注意：如果是自定义 query_body，将直接查询返回结果数据，不使用 scroll

        Yields:
            (bool, dict): 成功标志和批次数据
        """
        if not self.standalone_handler:
            flag, msg = self.connect()
            if not flag:
                yield False, msg
                return
        try:
            # 准备查询 DSL
            query_dsl, sort_list, is_custom_query = self._prepare_query_dsl()

            es_client = self.handler.connection

            # 如果是自定义查询，直接查询返回结果，不使用 scroll
            if is_custom_query:
                logger.info("Using custom query body, direct query without scroll")
                search_body = query_dsl

                # 执行查询
                response = es_client.search(
                    index=self.table_name,
                    body=search_body
                )

                # 解析结果
                hits = response.get('hits', {}).get('hits', [])
                records = [{'_id': hit['_id'], **hit.get('_source', {})} for hit in hits]

                # 获取总数
                total_info = response.get('hits', {}).get('total', {})
                total_count = total_info.get('value', 0) if isinstance(total_info, dict) else total_info

                batch_info = {
                    'records': records,
                    'total': total_count,
                    'aggregations': response.get('aggregations', {})
                }

                logger.info(f"Custom query returned {len(records)} records, total: {total_count}")
                yield True, gen_json_response(data=batch_info)

            else:
                # 使用 scroll 查询
                search_body = {
                    "query": query_dsl,
                    "size": self.batch_size
                }
                if sort_list:
                    search_body["sort"] = sort_list

                # 初始化 scroll 查询
                logger.info(f"Starting scroll query with body: {json.dumps(search_body, indent=2)}")
                response = es_client.search(
                    index=self.table_name,
                    body=search_body,
                    scroll='2m'
                )

                # 获取 scroll_id 和总数
                scroll_id = response.get('_scroll_id')
                total_info = response.get('hits', {}).get('total', {})
                total_count = total_info.get('value', 0) if isinstance(total_info, dict) else total_info

                batch_num = 0
                processed_count = 0

                # 处理批次数据
                while True:
                    hits = response.get('hits', {}).get('hits', [])
                    if not hits:
                        break

                    # 解析结果
                    records = [{'_id': hit['_id'], **hit.get('_source', {})} for hit in hits]
                    batch_num += 1
                    processed_count += len(records)

                    batch_info = {
                        'records': records,
                        'total': total_count,
                        'aggregations': response.get('aggregations', {})
                    }

                    logger.info(f"Batch {batch_num}: {len(records)} records, processed: {processed_count}/{total_count}")
                    yield True, gen_json_response(data=batch_info)

                    # 获取下一批数据
                    response = es_client.scroll(scroll_id=scroll_id, scroll='2m')
                    scroll_id = response.get('_scroll_id')

                # 清除 scroll 上下文
                if scroll_id:
                    try:
                        es_client.clear_scroll(scroll_id=scroll_id)
                        logger.info("Scroll context cleared")
                    except Exception as e:
                        logger.warning(f"Failed to clear scroll context: {e}")

        except Exception as e:
            logger.error(f"批量读取数据失败: {str(e)}")
            yield False, str(e)

    def update_data_bulk(self, index_name, row_obj_list, upsert=False):
        '''
        批量更新
        :param index_name: 索引名
        :param row_obj_list: 记录列表，每条需要有_id
        :return:
        '''
        load_data = []
        for row_obj in row_obj_list:
            # new
            action = {}
            if "_id" in row_obj:
                action['_id'] = row_obj.get('_id', 'None')
                row_obj.pop("_id")
                action['_op_type'] = 'update'
                action['doc'] = {}
                for r_o_i in row_obj:
                    action['doc'][r_o_i] = row_obj.get(r_o_i, None)
                if upsert:
                    action['doc_as_upsert'] = True
                load_data.append(action)
        result = {}
        if load_data:
            success, failed = helpers.bulk(
                self.handler.connection, load_data, index=index_name, raise_on_error=True, request_timeout=1000)
            result['success'] = success
            result['failed'] = failed
        return result

    def add_data_bulk(self, index_name, row_obj_list):
        '''
        批量插入
        :param index_name:
        :param row_obj_list:
        :return:
        '''
        load_data = []
        for row_obj in row_obj_list:
            # new
            action = {}
            action['_index'] = index_name
            if '_id' in row_obj:
                action['_id'] = row_obj.get('_id', 'None')
                row_obj.pop("_id")
            action['_source'] = {}
            for r_o_i in row_obj:
                action['_source'][r_o_i] = row_obj.get(r_o_i, None)
            load_data.append(action)
        result = {}
        if load_data:
            success, failed = helpers.bulk(
                self.handler.connection, load_data, index=index_name, raise_on_error=True, request_timeout=1000)
            result['success'] = success
            result['failed'] = failed
        return result

    def write(self, res_data):
        """
        Override write method, use ES native bulk write API

        Args:
            res_data: data to write, can be list or dict

        Returns:
            (bool, str): success flag and message
        """
        if not self.standalone_handler:
            self.connect()
        # Check permission
        if 'load' not in self.auth_types:
            return False, 'no write permission'

        # Get write type
        self.load_type = self._load_info.get('load_type', '')
        if self.load_type not in ['insert', 'update', 'upsert']:
            return False, f'invalid write type: {self.load_type}'

        # Get fields for matching (for update and upsert)
        self.only_fields = self._load_info.get('only_fields', [])

        # Ensure connection is established
        if not self.handler:
            flag, msg = self.connect()
            if not flag:
                return False, msg

        # Process input data
        records = []
        if isinstance(res_data, list) and res_data != []:
            records = res_data
        elif isinstance(res_data, dict):
            if 'records' in res_data and res_data['records'] != []:
                records = res_data['records']
            else:
                records = [res_data]

        if not records:
            return False, 'no data to write'
        try:
            if self.load_type == 'insert':
                self.add_data_bulk(self.table_name, records)
            elif self.load_type == 'update':
                self.update_data_bulk(self.table_name, records)
            elif self.load_type == 'upsert':
                self.update_data_bulk(self.table_name, records, upsert=True)
        except Exception as e:
            error_msg = str(e)[:200]
            logger.error(f"ES write failed: {error_msg}")
            return False, error_msg

        return True, records