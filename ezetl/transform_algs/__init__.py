from ezetl.transform_algs import filter_algs, count_algs, map_algs, content_algs
from ezetl.transform_algs.content_algs import df_to_data

# 算法字典
transform_alg_dict = {
    # 内容提取类算法
    'code_transform': content_algs.code_transform,
    'gen_records_list': content_algs.gen_records_list,
    'data_to_df': content_algs.data_to_df,
    'df_to_data': content_algs.df_to_data,
    'gen_es_aggs_buckets': content_algs.gen_es_aggs_buckets,
    'gen_es_aggs_value': content_algs.gen_es_aggs_value,
    'gen_contents_first': content_algs.gen_contents_first,
    'gen_contents_total': content_algs.gen_contents_total,
    # 映射类算法
    'map_field_names': map_algs.map_field_names,
    'map_values': map_algs.map_values,
    'trans_time_format': map_algs.trans_time_format,
    'trans_field_type': map_algs.trans_field_type,
    'gen_only_id': map_algs.gen_only_id,
    'add_field': map_algs.add_field,
    # 数据清洗类算法
    'clean_empty': filter_algs.clean_empty,
    'empty_to_null': filter_algs.empty_to_null,
    # 统计聚合类算法
    'group_agg_count': count_algs.group_agg_count
}
