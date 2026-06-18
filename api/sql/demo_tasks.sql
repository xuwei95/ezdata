-- 数据集成 / 流式摄取 演示任务(依赖 demo_mysql / demo_minio / demo_binlog 数据源)
-- 重复执行安全:先删后插
DELETE FROM task WHERE id IN ('demo_etl_m2m','demo_etl_m2file','demo_etl_tf','demo_stream_cdc');

INSERT INTO task (id,template_code,task_type,name,params,status,trigger_type,run_queue,priority,retry,countdown,create_by,create_time,tenant_id,remark) VALUES
('demo_etl_m2m','DataIntegrationTask',1,'演示-MySQL→MySQL(原生查询)',
 '{"extract":{"datasource_code":"demo_mysql","object":"demo_orders","native":"SELECT id,order_no,amount,status FROM demo_orders LIMIT 500"},"transform":{"enabled":false,"code":""},"load":{"datasource_code":"demo_mysql","table":"demo_orders_paid","mode":"replace","dataset":"dwh","format":"csv"}}',
 1,1,'default',1,0,0,'admin',now(),100,'抽 demo_orders 装载到 dwh 库'),

('demo_etl_m2file','DataIntegrationTask',1,'演示-MySQL→文件CSV(MinIO)',
 '{"extract":{"datasource_code":"demo_mysql","object":"demo_orders","native":"SELECT id,order_no,amount,status FROM demo_orders LIMIT 200"},"transform":{"enabled":false,"code":""},"load":{"datasource_code":"demo_minio","table":"exports/demo_orders.csv","mode":"replace","dataset":"public","format":"csv"}}',
 1,1,'default',1,0,0,'admin',now(),100,'抽 demo_orders 写成 CSV 到对象存储'),

('demo_etl_tf','DataIntegrationTask',1,'演示-MySQL+转换→MySQL',
 '{"extract":{"datasource_code":"demo_mysql","object":"demo_orders","native":"SELECT id,order_no,amount,status FROM demo_orders LIMIT 200"},"transform":{"enabled":true,"code":"def transform(row):\\n    row[\\"source_tag\\"] = \\"etl-demo\\"\\n    return row"},"load":{"datasource_code":"demo_mysql","table":"demo_orders_tagged","mode":"replace","dataset":"dwh","format":"csv"}}',
 1,1,'default',1,0,0,'admin',now(),100,'抽数后逐行打标再装载'),

('demo_stream_cdc','DataIntegrationTask',1,'演示-Binlog CDC→MySQL(有界流式)',
 '{"extract":{"datasource_code":"demo_binlog","object":"demo_orders","native":"","max_events":100},"transform":{"enabled":false,"code":""},"load":{"datasource_code":"demo_mysql","table":"cdc_demo_orders","mode":"replace","dataset":"cdc","format":"csv"}}',
 1,1,'default',1,0,0,'admin',now(),100,'流式源:有界读取 binlog 变更装载(max_events 留空则持续消费)');
