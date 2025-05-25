from web_apps.llm.agents.data_chat_agent import DataChatAgent
from web_apps.llm.llm_utils import get_llm

if __name__ == '__main__':
    from etl.utils import get_reader
    llm = get_llm()
    reader_info = {
        'source': {
            "name": "test",
            "type": "mysql",
            "conn_conf": {
                "host": "110.40.157.36",
                "port": 3306,
                "username": "root",
                "password": "ezdata123",
                "database_name": "ezdata"
            },
            "ext_params": {}
        },
        'model': {
            "name": "task_instance",
            "type": "mysql_table",
            "model_conf": {
                "name": "task_instance",
            },
            "ext_params": {},
            "fields": []
        },
        'extract_info': {
            'batch_size': 1000,
            'extract_rules': [],
            'search_text': '',
            'search_type': ''
        }
    }

    flag, reader = get_reader(reader_info)
    print(flag, reader)
    flag, res = reader.connect()
    print(flag, res)
    prompt = f"""
    找出最近7天数据，按任务id分组统计数量，画出统计图
    """
    agent = DataChatAgent(llm, reader)
    res = agent.run(prompt)
    print(res)