

def data_to_df(source_data=[], rule_dict={}, context={}):
    '''
    将数据转为dataframe
    [{
        "name": "dataframe类型",
        "value": "engine",
        "form_type": "select",
        "required": true,
        "default": "pandas",
        "options": [{"label": "pandas", "value": "pandas"},{"label": "xorbits", "value": "xorbits"}],
        "tips": ""
    }]
    '''
    engine = rule_dict.get('engine', 'pandas')
    if isinstance(source_data, dict):
        source_data = [source_data]
    if engine == 'xorbits':
        import xorbits
        xorbits_cluster = rule_dict.get('xorbits_cluster')
        if xorbits_cluster is None:
            from config import XORBITS_CLUSTER
            xorbits_cluster = XORBITS_CLUSTER
        if xorbits_cluster != 'local':
            xorbits.init(xorbits_cluster)
        import xorbits.pandas as pd
    else:
        import pandas as pd
    df = pd.DataFrame(source_data)
    return True, df