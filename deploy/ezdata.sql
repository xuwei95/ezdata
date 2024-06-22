/*
 Navicat Premium Data Transfer

 Source Server         : txy
 Source Server Type    : MySQL
 Source Server Version : 80022
 Source Host           : 110.40.157.36:3306
 Source Schema         : ezdata

 Target Server Type    : MySQL
 Target Server Version : 80022
 File Encoding         : 65001

 Date: 23/06/2024 02:35:04
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for alert
-- ----------------------------
DROP TABLE IF EXISTS `alert`;
CREATE TABLE `alert` (
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '简介',
  `sort_no` float DEFAULT NULL COMMENT '排序',
  `del_flag` smallint DEFAULT NULL COMMENT '软删除标记',
  `create_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建者',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '修改者',
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'id',
  `strategy_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '告警策略id',
  `title` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '告警标题',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '告警内容',
  `level` int DEFAULT NULL COMMENT '告警等级',
  `status` smallint DEFAULT NULL COMMENT '告警状态',
  `rule_id` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '规则编码',
  `rule_name` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '规则名称',
  `biz` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '告警业务',
  `source` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '告警对象',
  `tags` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '告警标签',
  `metric` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '告警指标',
  `recover_time` timestamp NULL DEFAULT NULL COMMENT '恢复时间',
  `ext_params` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '额外参数',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Records of alert
-- ----------------------------
BEGIN;
INSERT INTO `alert` VALUES ('', 1, 0, 'system', '2023-10-24 07:01:42', '', '2023-10-24 07:01:42', '570d84a3-2930-4502-95b4-5cc65d31c7b8', '0af64e7c24d44c19908ee0034ddd10ec', '任务失败告警策略', '普通任务失败告警:失败任务示例 在重试2次后仍失败。任务报错：/Users/xuwei/Desktop/code/ezdata/ezdata/tasks/normal_task.py:48:division by zero', 3, 0, '6698d41fb678e8a0f51a3b001af9805c', '任务失败告警策略', 'scheduler', 'celery@localhost', '{\"task_uuid\": \"839f819b-76bd-43b9-be8a-78a9da7a0aec\", \"worker\": \"celery@localhost\", \"retries\": 2}', 'task_fail', NULL, '{}');
INSERT INTO `alert` VALUES ('', 1, 0, 'system', '2023-10-24 07:01:42', '', '2023-10-24 07:01:42', '980d4e21-5026-442a-9598-f39949751e18', '0af64e7c24d44c19908ee0034ddd10ec', '任务失败告警策略', '普通任务失败告警:失败任务示例 在重试2次后仍失败。任务报错：/Users/xuwei/Desktop/code/ezdata/ezdata/tasks/normal_task.py:48:division by zero', 3, 0, '4de8987857ebee47a546e8bfa674364b', '任务失败告警策略', 'scheduler', 'celery@localhost', '{\"task_uuid\": \"c23e39de-6a73-4d29-bfc8-f42d682820f1\", \"worker\": \"celery@localhost\", \"retries\": 2}', 'task_fail', NULL, '{}');
COMMIT;

-- ----------------------------
-- Table structure for alert_strategy
-- ----------------------------
DROP TABLE IF EXISTS `alert_strategy`;
CREATE TABLE `alert_strategy` (
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '简介',
  `sort_no` float DEFAULT NULL COMMENT '排序',
  `del_flag` smallint DEFAULT NULL COMMENT '软删除标记',
  `create_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建者',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '修改者',
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '策略名称',
  `template_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '策略模版',
  `trigger_conf` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '触发条件',
  `forward_conf` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '转发条件',
  `status` smallint DEFAULT NULL COMMENT '状态',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Records of alert_strategy
-- ----------------------------
BEGIN;
INSERT INTO `alert_strategy` VALUES ('', 1, 0, 'admin', '2023-08-11 19:39:35', 'admin', '2023-08-29 12:28:46', '0af64e7c24d44c19908ee0034ddd10ec', '任务失败告警策略', 'TaskFailStrategy', '{\n  \"level\": 3,\n  \"biz\": \"scheduler\",\n  \"metric\": \"task_fail\"\n}', '[\n  {\n    \"notice_users\": \"dev1,admin,test1\",\n    \"type\": \"notice\"\n  }\n]', 1);
COMMIT;

-- ----------------------------
-- Table structure for algorithm
-- ----------------------------
DROP TABLE IF EXISTS `algorithm`;
CREATE TABLE `algorithm` (
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '简介',
  `sort_no` float DEFAULT NULL COMMENT '排序',
  `del_flag` smallint DEFAULT NULL COMMENT '软删除标记',
  `create_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建者',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '修改者',
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '算法名称',
  `code` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '算法编码',
  `type` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '算法类型',
  `form_type` smallint DEFAULT NULL COMMENT '表单类型',
  `component` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '算法组件',
  `params` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '算法配置',
  `status` smallint DEFAULT NULL COMMENT '状态',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Records of algorithm
-- ----------------------------
BEGIN;
INSERT INTO `algorithm` VALUES ('', 1, 0, 'admin', '2023-04-04 09:08:44', '', '2023-04-04 09:08:44', '13bba9cd89ce4e4e9a7188649adda41c', '解析es接口返回聚合统计信息', 'gen_es_aggs_buckets', 'etl_algorithm', 2, '', '[{\"name\": \"统计字段\", \"value\": \"field\", \"form_type\": \"select_fields\", \"required\": true, \"default\": \"\", \"tips\": \"\"}, {\"name\": \"是否包含其它\", \"value\": \"include_other\", \"form_type\": \"switch\", \"required\": true, \"default\": false, \"tips\": \"\"}]', 1);
INSERT INTO `algorithm` VALUES ('', 98, 0, 'admin', '2023-04-04 09:08:18', 'admin', '2023-04-05 06:47:32', '1d03524c7f61429ca231e02b788a00ec', '获取总数', 'gen_contents_total', 'etl_algorithm', 2, '', '[]', 1);
INSERT INTO `algorithm` VALUES ('', 92, 0, 'admin', '2023-04-05 07:50:43', 'admin', '2023-04-24 16:36:37', '299b211bdfdb4ad2a8f535f28e63534d', '分组聚合统计', 'group_agg_count', 'etl_algorithm', 2, '', '[\n  {\n    \"name\": \"统计字段\",\n    \"value\": \"count_field\",\n    \"form_type\": \"select_field\",\n    \"required\": true,\n    \"default\": \"\",\n    \"tips\": \"\"\n  },\n  {\n    \"name\": \"分组字段列表\",\n    \"value\": \"group_fields\",\n    \"form_type\": \"select_fields\",\n    \"required\": true,\n    \"default\": \"\",\n    \"tips\": \"\"\n  },\n  {\n    \"name\": \"统计类型\",\n    \"value\": \"count_type\",\n    \"form_type\": \"select\",\n    \"required\": true,\n    \"default\": \"sum\",\n    \"options\": [\n      {\n        \"label\": \"数量\",\n        \"value\": \"count\"\n      },\n      {\n        \"label\": \"数值总和\",\n        \"value\": \"sum\"\n      },\n      {\n        \"label\": \"平均值\",\n        \"value\": \"mean\"\n      },\n      {\n        \"label\": \"算数平均值\",\n        \"value\": \"median\"\n      },\n      {\n        \"label\": \"标准差\",\n        \"value\": \"std\"\n      },\n      {\n        \"label\": \"方差\",\n        \"value\": \"var\"\n      },\n      {\n        \"label\": \"最小值\",\n        \"value\": \"min\"\n      },\n      {\n        \"label\": \"最大值\",\n        \"value\": \"max\"\n      },\n      {\n        \"label\": \"积\",\n        \"value\": \"prod\"\n      },\n      {\n        \"label\": \"第一个值\",\n        \"value\": \"first\"\n      },\n      {\n        \"label\": \"最后一个值\",\n        \"value\": \"last\"\n      }\n    ],\n    \"tips\": \"\"\n  }\n]', 1);
INSERT INTO `algorithm` VALUES ('', 1, 0, 'admin', '2023-08-10 07:20:40', '', '2023-08-10 07:20:40', '39c111c1701840248345fb0fcc6eac04', '转换字段格式', 'trans_field_type', 'etl_algorithm', 2, '', '[\n  {\n    \"name\": \"处理字段\",\n    \"value\": \"fields\",\n    \"form_type\": \"select_fields\",\n    \"required\": true,\n    \"default\": \"\",\n    \"tips\": \"\"\n  },\n  {\n    \"name\": \"转换类型类型\",\n    \"value\": \"trans_type\",\n    \"form_type\": \"select\",\n    \"required\": true,\n    \"default\": \"sum\",\n    \"options\": [\n      {\n        \"label\": \"字符串\",\n        \"value\": \"str\"\n      },\n      {\n        \"label\": \"整数\",\n        \"value\": \"int\"\n      },\n      {\n        \"label\": \"浮点数\",\n        \"value\": \"float\"\n      },\n      {\n        \"label\": \"日期字符串\",\n        \"value\": \"date\"\n      },\n      {\n        \"label\": \"日期时间\",\n        \"value\": \"datetime\"\n      },\n      {\n        \"label\": \"时间戳\",\n        \"value\": \"timestamp\"\n      }\n    ],\n    \"tips\": \"\"\n  }\n]', 1);
INSERT INTO `algorithm` VALUES ('', 96, 0, 'admin', '2023-04-04 09:01:12', 'admin', '2023-12-24 09:04:25', '426e64ecb8f4422986636ae68d280c12', 'dataframe转回原始数据', 'df_to_data', 'etl_algorithm', 2, '', '[]', 1);
INSERT INTO `algorithm` VALUES ('', 100, 0, 'admin', '2023-04-03 14:26:31', 'admin', '2023-04-18 03:17:15', '4a6c1cdb93224f3f90502f64cf201538', '获取内容列表', 'gen_records_list', 'etl_algorithm', 2, '', '[\n  {\n    \"name\": \"字段列表\",\n    \"value\": \"fields\",\n    \"form_type\": \"select_fields\",\n    \"required\": false,\n    \"default\": \"\",\n    \"tips\": \"\"\n  }\n]', 1);
INSERT INTO `algorithm` VALUES ('', 93, 0, 'admin', '2023-04-05 07:45:56', 'admin', '2023-04-24 03:38:35', '66fcaecbc68642359cf69824f27fb3a6', '字段映射', 'map_field_names', 'etl_algorithm', 2, '', '[\n  {\n    \"name\": \"字段映射\",\n    \"value\": \"field_map\",\n    \"form_type\": \"codeEditor\",\n    \"required\": true,\n    \"default\": \"{}\",\n    \"language\": \"json\",\n    \"tips\": \"\"\n  }\n]', 1);
INSERT INTO `algorithm` VALUES ('', 93, 0, 'admin', '2023-04-05 07:47:53', 'admin', '2023-04-24 03:22:15', '752dd6f66def4757bc7aa342e1eb7383', '字段值映射', 'map_values', 'etl_algorithm', 2, '', '[\n  {\n    \"name\": \"处理字段\",\n    \"value\": \"fields\",\n    \"form_type\": \"select_fields\",\n    \"required\": true,\n    \"default\": \"\",\n    \"tips\": \"\"\n  },\n  {\n    \"name\": \"映射字典\",\n    \"value\": \"value_map\",\n    \"form_type\": \"codeEditor\",\n    \"required\": true,\n    \"default\": \"{}\",\n    \"language\": \"json\",\n    \"tips\": \"\"\n  },\n  {\n    \"name\": \"处理错误时\",\n    \"value\": \"if_error\",\n    \"form_type\": \"RadioGroup\",\n    \"required\": true,\n    \"default\": \"original\",\n    \"options\": [\n      {\n        \"label\": \"原始值\",\n        \"value\": \"original\"\n      },\n      {\n        \"label\": \"置空\",\n        \"value\": \"empty\"\n      }\n    ],\n    \"tips\": \"\"\n  }\n]', 1);
INSERT INTO `algorithm` VALUES ('', 93, 0, 'admin', '2023-04-05 07:49:18', 'admin', '2023-04-24 16:36:10', '87c58ab9220d4532ab83f87fc817ce38', '生成唯一id', 'gen_only_id', 'etl_algorithm', 2, '', '[\n  {\n    \"name\": \"唯一字段列表\",\n    \"value\": \"only_fields\",\n    \"form_type\": \"select_fields\",\n    \"required\": true,\n    \"default\": \"\",\n    \"tips\": \"\"\n  },\n  {\n    \"name\": \"唯一号字段\",\n    \"value\": \"output_field\",\n    \"form_type\": \"input\",\n    \"required\": true,\n    \"default\": \"_id\",\n    \"tips\": \"\"\n  }\n]', 1);
INSERT INTO `algorithm` VALUES ('', 999.9, 0, 'admin', '2023-04-04 08:58:38', 'admin', '2023-08-10 07:26:56', '880bc3108df249e499c7aff1da8cf2a3', '自定义代码转换数据', 'code_transform', 'etl_algorithm', 2, '', '[\n  {\n    \"name\": \"语言\",\n    \"value\": \"language\",\n    \"form_type\": \"select\",\n    \"required\": true,\n    \"default\": \"python\",\n    \"options\": [\n      {\n        \"label\": \"python\",\n        \"value\": \"python\"\n      }\n    ],\n    \"tips\": \"\"\n  },\n  {\n    \"name\": \"代码\",\n    \"value\": \"code\",\n    \"form_type\": \"codeEditor\",\n    \"required\": true,\n    \"default\": \"\",\n    \"tips\": \"\"\n  }\n]', 1);
INSERT INTO `algorithm` VALUES ('', 99, 0, 'admin', '2023-04-04 09:07:37', 'admin', '2023-04-24 16:35:55', '9524f1f94a534dc0bc72a24092019531', '解析接口第一条数据', 'gen_contents_first', 'etl_algorithm', 2, '', '[\n  {\n    \"name\": \"字段\",\n    \"value\": \"fields\",\n    \"form_type\": \"select_fields\",\n    \"required\": true,\n    \"default\": \"\",\n    \"tips\": \"\"\n  }\n]', 1);
INSERT INTO `algorithm` VALUES ('', 97, 0, 'admin', '2023-04-04 08:59:11', 'admin', '2023-07-28 07:39:47', '9c926059a4164bdeac53491ea4d84d2a', '将数据转为dataframe', 'data_to_df', 'etl_algorithm', 2, '', '[\n  {\n    \"name\": \"dataframe类型\",\n    \"value\": \"engine\",\n    \"form_type\": \"select\",\n    \"required\": true,\n    \"default\": \"pandas\",\n    \"options\": [\n      {\n        \"label\": \"pandas\",\n        \"value\": \"pandas\"\n      },\n      {\n        \"label\": \"xorbits\",\n        \"value\": \"xorbits\"\n      }\n    ],\n    \"tips\": \"\"\n  }\n]', 1);
INSERT INTO `algorithm` VALUES ('', 1, 0, 'admin', '2023-04-04 09:09:17', 'admin', '2023-04-24 16:36:41', 'a232edca95da418d89b286c4d70666ba', '解析es接口聚类统计数值', 'gen_es_aggs_value', 'etl_algorithm', 2, '', '[\n  {\n    \"name\": \"字段\",\n    \"value\": \"field\",\n    \"form_type\": \"select_field\",\n    \"required\": true,\n    \"default\": \"\",\n    \"tips\": \"\"\n  }\n]', 1);
INSERT INTO `algorithm` VALUES ('', 94, 0, 'admin', '2023-04-05 06:57:12', 'admin', '2023-04-24 16:36:00', 'c43496ab3ba7427685c737184d29aa40', '清除空字符串和null', 'clean_empty', 'etl_algorithm', 2, '', '[\n  {\n    \"name\": \"处理字段列表\",\n    \"value\": \"fields\",\n    \"form_type\": \"select_fields\",\n    \"required\": true,\n    \"default\": \"\",\n    \"tips\": \"\"\n  }\n]', 1);
INSERT INTO `algorithm` VALUES ('', 1, 0, 'admin', '2023-04-05 07:49:53', 'admin', '2023-04-24 16:36:55', 'c9e0210186e14d50becd8653503f8620', '添加字段', 'add_field', 'etl_algorithm', 2, '', '[\n  {\n    \"name\": \"字段值\",\n    \"value\": \"field\",\n    \"form_type\": \"input\",\n    \"required\": true,\n    \"default\": \"\",\n    \"tips\": \"\"\n  },\n  {\n    \"name\": \"默认值\",\n    \"value\": \"default\",\n    \"form_type\": \"input\",\n    \"required\": true,\n    \"default\": \"\",\n    \"tips\": \"\"\n  }\n]', 1);
INSERT INTO `algorithm` VALUES ('', 93, 0, 'admin', '2023-04-05 07:48:35', 'admin', '2023-04-24 06:02:12', 'eaf615edde3f4362922950d84afbbc48', '转换时间格式', 'trans_time_format', 'etl_algorithm', 2, '', '[\n  {\n    \"name\": \"处理字段\",\n    \"value\": \"fields\",\n    \"form_type\": \"select_fields\",\n    \"required\": true,\n    \"default\": \"\",\n    \"tips\": \"\"\n  },\n  {\n    \"name\": \"日期格式\",\n    \"value\": \"format\",\n    \"form_type\": \"input\",\n    \"required\": true,\n    \"default\": \"%Y-%m-%d %H:%M:%S\",\n    \"tips\": \"\"\n  }\n]', 1);
INSERT INTO `algorithm` VALUES ('', 94, 0, 'admin', '2023-04-05 06:55:49', '', '2023-04-05 06:55:49', 'f40e035d77b04e5d99f8ac851d355de7', '空字符串转null', 'empty_to_null', 'etl_algorithm', 2, '', '[{\"name\": \"处理字段列表\", \"value\": \"fields\", \"form_type\": \"select_fields\", \"required\": true, \"default\": \"\", \"tips\": \"\"}]', 1);
COMMIT;

-- ----------------------------
-- Table structure for code_gen_model
-- ----------------------------
DROP TABLE IF EXISTS `code_gen_model`;
CREATE TABLE `code_gen_model` (
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '简介',
  `sort_no` float DEFAULT NULL COMMENT '排序',
  `del_flag` smallint DEFAULT NULL COMMENT '软删除标记',
  `create_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建者',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '修改者',
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '项目名称',
  `module_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '模块文件名称',
  `api_prefix` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'api接口前缀，不设默认使用模块文件名称',
  `model_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '模型名称',
  `model_value` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '模型值',
  `extend_base_model` smallint DEFAULT NULL COMMENT '是否继承基础模型类1是0不是',
  `table_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '数据库表名',
  `table_desc` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '数据库表描述',
  `model_type` smallint DEFAULT NULL COMMENT '模型类型1单表',
  `query_params` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '高级查询参数',
  `buttons` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '按钮设置',
  `fields` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '字段列表',
  `form_style` smallint DEFAULT NULL COMMENT '表单风格1一列2两列3三列4四列',
  `frontend_gen_type` smallint DEFAULT NULL COMMENT '前端生成代码类型1vue3模版,2vue3原生,3vue2',
  `backend_gen_type` smallint DEFAULT NULL COMMENT '后端生成代码类型1flaREDACTEDsqlalchemy模版',
  `is_scroll` smallint DEFAULT NULL COMMENT '滚动条1有0无',
  `modal_type` smallint DEFAULT NULL COMMENT '编辑弹窗类型1弹窗2抽屉',
  `modal_width` int DEFAULT NULL COMMENT '弹窗宽度，为0则全屏',
  `is_sync` smallint DEFAULT NULL COMMENT '是否已同步数据库1是0不是',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Records of code_gen_model
-- ----------------------------
BEGIN;
INSERT INTO `code_gen_model` VALUES ('', 1, 0, 'admin', '2023-02-16 09:49:59', '', '2023-02-16 09:49:59', '07f7e5c7eea748d08f1e6253b6b71022', '数据接口', 'DataInterface', '/', 'DataInterface', 'DataInterface', 1, 'data_interface', '', 1, '[]', '[{\"name\": \"列表查询\", \"slot\": \"hideApi\", \"function\": \"list\", \"is_show\": false, \"permissions\": \"\", \"id\": \"row_141\", \"sortNum\": 3}, {\"name\": \"全量列表\", \"slot\": \"hideApi\", \"function\": \"getAllList\", \"is_show\": false, \"permissions\": \"\", \"id\": \"row_142\", \"sortNum\": 4}, {\"name\": \"详情\", \"slot\": \"actionDropDown\", \"function\": \"handleDetail\", \"is_show\": true, \"permissions\": \"\", \"id\": \"row_143\", \"sortNum\": 5}, {\"name\": \"新增\", \"slot\": \"tableTitle\", \"function\": \"handleAdd\", \"is_show\": true, \"permissions\": \"\", \"id\": \"row_144\", \"sortNum\": 6}, {\"name\": \"编辑\", \"slot\": \"action\", \"function\": \"handleEdit\", \"is_show\": true, \"permissions\": \"\", \"id\": \"row_145\", \"sortNum\": 7}, {\"name\": \"删除\", \"slot\": \"actionDropDown\", \"function\": \"handleDelete\", \"is_show\": true, \"permissions\": \"\", \"id\": \"row_146\", \"sortNum\": 8}, {\"name\": \"批量删除\", \"slot\": \"overlay\", \"function\": \"batchHandleDelete\", \"is_show\": true, \"permissions\": \"\", \"id\": \"row_147\", \"sortNum\": 9}, {\"name\": \"导入\", \"slot\": \"tableTitle\", \"function\": \"onImportXls\", \"is_show\": false, \"permissions\": \"\", \"id\": \"row_148\", \"sortNum\": 10}, {\"name\": \"导出\", \"slot\": \"tableTitle\", \"function\": \"onExportXls\", \"is_show\": false, \"permissions\": \"\", \"id\": \"row_149\", \"sortNum\": 11}]', '[{\"label\": \"主键\", \"field\": \"id\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field_type\": \"String\", \"default_value\": \"\", \"length\": 36, \"nullable\": 1, \"primary_key\": 1, \"is_only\": 1, \"is_json\": 0, \"clearable\": 0, \"editable\": 0, \"customRender\": 0, \"list_show\": 1, \"table_show\": 1, \"edit_show\": 0, \"detail_show\": 1, \"all_list_show\": 1, \"id\": \"row_133\", \"sortNum\": 3}, {\"label\": \"创建者\", \"field\": \"create_by\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field_type\": \"String\", \"default_value\": \"\", \"length\": 100, \"nullable\": 1, \"primary_key\": 0, \"is_only\": 0, \"is_json\": 0, \"clearable\": 0, \"editable\": 0, \"customRender\": 0, \"list_show\": 1, \"table_show\": 1, \"edit_show\": 0, \"detail_show\": 1, \"all_list_show\": 0, \"id\": \"row_134\", \"sortNum\": 4}, {\"label\": \"创建时间\", \"field\": \"create_time\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field_type\": \"TIMESTAMP\", \"default_value\": \"server_default:CURRENT_TIMESTAMP\", \"length\": 0, \"nullable\": 1, \"primary_key\": 0, \"is_only\": 0, \"is_json\": 0, \"clearable\": 0, \"editable\": 0, \"list_show\": 1, \"customRender\": 0, \"table_show\": 1, \"edit_show\": 0, \"detail_show\": 1, \"all_list_show\": 0, \"id\": \"row_135\", \"sortNum\": 5}, {\"label\": \"修改者\", \"field\": \"update_by\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field_type\": \"String\", \"default_value\": \"\", \"length\": 100, \"nullable\": 1, \"primary_key\": 0, \"is_only\": 0, \"is_json\": 0, \"clearable\": 0, \"editable\": 0, \"customRender\": 0, \"list_show\": 1, \"table_show\": 1, \"edit_show\": 0, \"detail_show\": 1, \"all_list_show\": 0, \"id\": \"row_136\", \"sortNum\": 6}, {\"label\": \"修改时间\", \"field\": \"update_time\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field_type\": \"TIMESTAMP\", \"default_value\": \"server_default:CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP\", \"length\": 0, \"nullable\": 1, \"primary_key\": 0, \"is_only\": 0, \"is_json\": 0, \"clearable\": 0, \"editable\": 0, \"customRender\": 0, \"list_show\": 1, \"table_show\": 1, \"edit_show\": 0, \"detail_show\": 1, \"all_list_show\": 0, \"id\": \"row_137\", \"sortNum\": 7}, {\"label\": \"软删除标记\", \"field\": \"del_flag\", \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"field_type\": \"SmallInteger\", \"default_value\": 0, \"length\": 0, \"nullable\": 1, \"primary_key\": 0, \"is_only\": 0, \"is_json\": 0, \"clearable\": 0, \"editable\": 0, \"customRender\": 1, \"list_show\": 1, \"table_show\": 0, \"edit_show\": 0, \"detail_show\": 1, \"all_list_show\": 0, \"id\": \"row_138\", \"sortNum\": 8}, {\"label\": \"排序字段\", \"field\": \"sort_no\", \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"field_type\": \"Float\", \"default_value\": 1, \"length\": 0, \"nullable\": 1, \"primary_key\": 0, \"is_only\": 0, \"is_json\": 0, \"clearable\": 0, \"editable\": 0, \"customRender\": 0, \"list_show\": 1, \"table_show\": 0, \"edit_show\": 0, \"detail_show\": 1, \"all_list_show\": 0, \"id\": \"row_139\", \"sortNum\": 9}, {\"label\": \"简介描述\", \"field\": \"description\", \"component\": \"InputTextArea\", \"componentProps\": \"{}\", \"field_type\": \"Text\", \"default_value\": \"\", \"length\": 0, \"nullable\": 1, \"primary_key\": 0, \"is_only\": 0, \"is_json\": 0, \"clearable\": 0, \"editable\": 1, \"customRender\": 0, \"list_show\": 1, \"table_show\": 1, \"edit_show\": 1, \"detail_show\": 1, \"all_list_show\": 0, \"id\": \"row_140\", \"sortNum\": 10}]', 1, 1, 1, 1, 1, 800, 0);
INSERT INTO `code_gen_model` VALUES ('', 1, 0, 'admin', '2022-12-19 13:23:32', 'admin', '2022-12-19 16:47:58', '184307eeb5a34070988d1df9e8c6f237', '数据模型管理', 'datamodel', 'datamodel', '数据模型', 'DataModel', 1, 'datamodel', '数据模型', 1, '[{\"colProps\": \"{}\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field\": \"name\", \"id\": \"row_107\", \"label\": \"\\u540d\\u79f0\", \"sortNum\": 3}, {\"colProps\": \"{}\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field\": \"datasource_id\", \"id\": \"row_108\", \"label\": \"\\u6240\\u5c5e\\u6570\\u636e\\u6e90\", \"sortNum\": 4}, {\"colProps\": \"{}\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field\": \"type\", \"id\": \"row_109\", \"label\": \"\\u7c7b\\u578b\", \"sortNum\": 5}]', '[{\"function\": \"list\", \"id\": \"row_68\", \"is_show\": false, \"name\": \"\\u5217\\u8868\\u67e5\\u8be2\", \"permissions\": \"\", \"slot\": \"hideApi\", \"sortNum\": 3}, {\"function\": \"getAllList\", \"id\": \"row_69\", \"is_show\": false, \"name\": \"\\u5168\\u91cf\\u5217\\u8868\", \"permissions\": \"\", \"slot\": \"hideApi\", \"sortNum\": 4}, {\"function\": \"handleDetail\", \"id\": \"row_70\", \"is_show\": true, \"name\": \"\\u8be6\\u60c5\", \"permissions\": \"\", \"slot\": \"actionDropDown\", \"sortNum\": 5}, {\"function\": \"handleAdd\", \"id\": \"row_71\", \"is_show\": true, \"name\": \"\\u65b0\\u589e\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 6}, {\"function\": \"handleEdit\", \"id\": \"row_72\", \"is_show\": true, \"name\": \"\\u7f16\\u8f91\", \"permissions\": \"\", \"slot\": \"action\", \"sortNum\": 7}, {\"function\": \"handleDelete\", \"id\": \"row_73\", \"is_show\": true, \"name\": \"\\u5220\\u9664\", \"permissions\": \"\", \"slot\": \"actionDropDown\", \"sortNum\": 8}, {\"function\": \"batchHandleDelete\", \"id\": \"row_74\", \"is_show\": true, \"name\": \"\\u6279\\u91cf\\u5220\\u9664\", \"permissions\": \"\", \"slot\": \"overlay\", \"sortNum\": 9}, {\"function\": \"onImportXls\", \"id\": \"row_75\", \"is_show\": false, \"name\": \"\\u5bfc\\u5165\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 10}, {\"function\": \"onExportXls\", \"id\": \"row_76\", \"is_show\": false, \"name\": \"\\u5bfc\\u51fa\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 11}]', '[{\"all_list_show\": 1, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"id\", \"field_type\": \"String\", \"id\": \"row_60\", \"is_json\": 0, \"is_only\": 1, \"label\": \"\\u4e3b\\u952e\", \"length\": 36, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 1, \"sortNum\": 3, \"table_show\": 1}, {\"all_list_show\": 1, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"name\", \"field_type\": \"String\", \"id\": \"row_119\", \"is_json\": 0, \"is_only\": 1, \"label\": \"\\u540d\\u79f0\", \"length\": 200, \"list_show\": 1, \"nullable\": 0, \"primary_key\": 0, \"sortNum\": 4, \"table_show\": 1}, {\"all_list_show\": 1, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"datasource_id\", \"field_type\": \"String\", \"id\": \"row_120\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u6570\\u636e\\u6e90id\", \"length\": 36, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 5, \"table_show\": 0}, {\"all_list_show\": 1, \"clearable\": 0, \"component\": \"JDictSelectTag\", \"componentProps\": \"{ \\t\\\"dictCode\\\": \\\"datamodel_type\\\", \\t\\\"placeholder\\\": \\\"\\u8bf7\\u9009\\u62e9\\u6570\\u636e\\u6e90\\u7c7b\\u578b\\\", \\t\\\"stringToNumber\\\": false }\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"type\", \"field_type\": \"String\", \"id\": \"row_121\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u7c7b\\u578b\", \"length\": 200, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 6, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"customRender\": 1, \"default_value\": \"0\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"is_sync\", \"field_type\": \"SmallInteger\", \"id\": \"row_251\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u662f\\u5426\\u540c\\u6b65\", \"length\": 6, \"list_show\": 1, \"nullable\": 0, \"primary_key\": 0, \"sortNum\": 7, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 1, \"component\": \"InputTextArea\", \"componentProps\": \"{}\", \"customRender\": 1, \"default_value\": \"{}\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"model_conf\", \"field_type\": \"Text\", \"id\": \"row_252\", \"is_json\": 1, \"is_only\": 0, \"label\": \"\\u6a21\\u578b\\u914d\\u7f6e\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 8, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 1, \"component\": \"InputTextArea\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"{}\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"ext_params\", \"field_type\": \"Text\", \"id\": \"row_253\", \"is_json\": 1, \"is_only\": 0, \"label\": \"\\u989d\\u5916\\u53c2\\u6570\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 9, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"create_by\", \"field_type\": \"String\", \"id\": \"row_61\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u521b\\u5efa\\u8005\", \"length\": 100, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 10, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"server_default:CURRENT_TIMESTAMP\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"create_time\", \"field_type\": \"TIMESTAMP\", \"id\": \"row_62\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u521b\\u5efa\\u65f6\\u95f4\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 11, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"update_by\", \"field_type\": \"String\", \"id\": \"row_63\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u4fee\\u6539\\u8005\", \"length\": 100, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 12, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"server_default:CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"update_time\", \"field_type\": \"TIMESTAMP\", \"id\": \"row_64\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u4fee\\u6539\\u65f6\\u95f4\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 13, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"customRender\": 1, \"default_value\": 0, \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"del_flag\", \"field_type\": \"SmallInteger\", \"id\": \"row_65\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u8f6f\\u5220\\u9664\\u6807\\u8bb0\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 14, \"table_show\": 0}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": 1, \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"sort_no\", \"field_type\": \"Float\", \"id\": \"row_66\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u6392\\u5e8f\\u5b57\\u6bb5\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 15, \"table_show\": 0}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"TextArea\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"description\", \"field_type\": \"Text\", \"id\": \"row_67\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u7b80\\u4ecb\\u63cf\\u8ff0\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 16, \"table_show\": 1}]', 1, 1, 1, 1, 2, 800, 0);
INSERT INTO `code_gen_model` VALUES ('', 1, 0, 'admin', '2023-02-17 09:19:00', 'admin', '2023-02-17 09:20:40', '1a0d8c3e269c48f0bc4e8f2ebbd55035', '数据接口申请', 'data_interface_apply', '/', 'DataInterfaceApply', 'DataInterfaceApply', 1, 'data_interface_apply', '', 1, '[]', '[{\"function\": \"list\", \"id\": \"row_126\", \"is_show\": false, \"name\": \"\\u5217\\u8868\\u67e5\\u8be2\", \"permissions\": \"\", \"slot\": \"hideApi\", \"sortNum\": 3}, {\"function\": \"getAllList\", \"id\": \"row_127\", \"is_show\": false, \"name\": \"\\u5168\\u91cf\\u5217\\u8868\", \"permissions\": \"\", \"slot\": \"hideApi\", \"sortNum\": 4}, {\"function\": \"handleDetail\", \"id\": \"row_128\", \"is_show\": true, \"name\": \"\\u8be6\\u60c5\", \"permissions\": \"\", \"slot\": \"actionDropDown\", \"sortNum\": 5}, {\"function\": \"handleAdd\", \"id\": \"row_129\", \"is_show\": true, \"name\": \"\\u65b0\\u589e\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 6}, {\"function\": \"handleEdit\", \"id\": \"row_130\", \"is_show\": true, \"name\": \"\\u7f16\\u8f91\", \"permissions\": \"\", \"slot\": \"action\", \"sortNum\": 7}, {\"function\": \"handleDelete\", \"id\": \"row_131\", \"is_show\": true, \"name\": \"\\u5220\\u9664\", \"permissions\": \"\", \"slot\": \"actionDropDown\", \"sortNum\": 8}, {\"function\": \"batchHandleDelete\", \"id\": \"row_132\", \"is_show\": true, \"name\": \"\\u6279\\u91cf\\u5220\\u9664\", \"permissions\": \"\", \"slot\": \"overlay\", \"sortNum\": 9}, {\"function\": \"onImportXls\", \"id\": \"row_133\", \"is_show\": false, \"name\": \"\\u5bfc\\u5165\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 10}, {\"function\": \"onExportXls\", \"id\": \"row_134\", \"is_show\": false, \"name\": \"\\u5bfc\\u51fa\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 11}]', '[{\"all_list_show\": 1, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"id\", \"field_type\": \"String\", \"id\": \"row_118\", \"is_json\": 0, \"is_only\": 1, \"label\": \"\\u4e3b\\u952e\", \"length\": 36, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 1, \"sortNum\": 3, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"create_by\", \"field_type\": \"String\", \"id\": \"row_119\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u521b\\u5efa\\u8005\", \"length\": 100, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 4, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"server_default:CURRENT_TIMESTAMP\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"create_time\", \"field_type\": \"TIMESTAMP\", \"id\": \"row_120\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u521b\\u5efa\\u65f6\\u95f4\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 5, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"update_by\", \"field_type\": \"String\", \"id\": \"row_121\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u4fee\\u6539\\u8005\", \"length\": 100, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 6, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"server_default:CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"update_time\", \"field_type\": \"TIMESTAMP\", \"id\": \"row_122\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u4fee\\u6539\\u65f6\\u95f4\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 7, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"customRender\": 1, \"default_value\": 0, \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"del_flag\", \"field_type\": \"SmallInteger\", \"id\": \"row_123\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u8f6f\\u5220\\u9664\\u6807\\u8bb0\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 8, \"table_show\": 0}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": 1, \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"sort_no\", \"field_type\": \"Float\", \"id\": \"row_124\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u6392\\u5e8f\\u5b57\\u6bb5\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 9, \"table_show\": 0}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputTextArea\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"description\", \"field_type\": \"Text\", \"id\": \"row_125\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u7b80\\u4ecb\\u63cf\\u8ff0\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 10, \"table_show\": 1}]', 1, 1, 1, 1, 1, 800, 0);
INSERT INTO `code_gen_model` VALUES ('', 1, 0, 'admin', '2022-12-17 12:34:09', '', '2022-12-17 12:34:09', '3182c0d0f9e24011b19e59c66d982251', 'test2', 'test2', 'test2', 'Test2', 'Test2', 1, 'test2', '', 1, '[]', '[{\"name\": \"列表查询\", \"slot\": \"hideApi\", \"function\": \"list\", \"is_show\": false, \"permissions\": \"\", \"id\": \"row_127\", \"sortNum\": 3}, {\"name\": \"全量列表\", \"slot\": \"hideApi\", \"function\": \"getAllList\", \"is_show\": false, \"permissions\": \"\", \"id\": \"row_128\", \"sortNum\": 4}, {\"name\": \"详情\", \"slot\": \"actionDropDown\", \"function\": \"handleDetail\", \"is_show\": true, \"permissions\": \"\", \"id\": \"row_129\", \"sortNum\": 5}, {\"name\": \"新增\", \"slot\": \"tableTitle\", \"function\": \"handleAdd\", \"is_show\": true, \"permissions\": \"\", \"id\": \"row_130\", \"sortNum\": 6}, {\"name\": \"编辑\", \"slot\": \"action\", \"function\": \"handleEdit\", \"is_show\": true, \"permissions\": \"\", \"id\": \"row_131\", \"sortNum\": 7}, {\"name\": \"删除\", \"slot\": \"actionDropDown\", \"function\": \"handleDelete\", \"is_show\": true, \"permissions\": \"\", \"id\": \"row_132\", \"sortNum\": 8}, {\"name\": \"批量删除\", \"slot\": \"overlay\", \"function\": \"batchHandleDelete\", \"is_show\": true, \"permissions\": \"\", \"id\": \"row_133\", \"sortNum\": 9}]', '[{\"label\": \"主键\", \"field\": \"id\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field_type\": \"String\", \"default_value\": \"\", \"length\": 36, \"nullable\": 1, \"primary_key\": 1, \"is_only\": 1, \"is_json\": 0, \"clearable\": 0, \"editable\": 0, \"customRender\": 0, \"list_show\": 1, \"table_show\": 1, \"edit_show\": 0, \"detail_show\": 1, \"all_list_show\": 1, \"id\": \"row_119\", \"sortNum\": 3}, {\"label\": \"创建者\", \"field\": \"create_by\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field_type\": \"String\", \"default_value\": \"\", \"length\": 100, \"nullable\": 1, \"primary_key\": 0, \"is_only\": 0, \"is_json\": 0, \"clearable\": 0, \"editable\": 0, \"customRender\": 0, \"list_show\": 1, \"table_show\": 1, \"edit_show\": 0, \"detail_show\": 1, \"all_list_show\": 0, \"id\": \"row_120\", \"sortNum\": 4}, {\"label\": \"创建时间\", \"field\": \"create_time\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field_type\": \"TIMESTAMP\", \"default_value\": \"server_default:CURRENT_TIMESTAMP\", \"length\": 0, \"nullable\": 1, \"primary_key\": 0, \"is_only\": 0, \"is_json\": 0, \"clearable\": 0, \"editable\": 0, \"list_show\": 1, \"customRender\": 0, \"table_show\": 1, \"edit_show\": 0, \"detail_show\": 1, \"all_list_show\": 0, \"id\": \"row_121\", \"sortNum\": 5}, {\"label\": \"修改者\", \"field\": \"update_by\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field_type\": \"String\", \"default_value\": \"\", \"length\": 100, \"nullable\": 1, \"primary_key\": 0, \"is_only\": 0, \"is_json\": 0, \"clearable\": 0, \"editable\": 0, \"customRender\": 0, \"list_show\": 1, \"table_show\": 1, \"edit_show\": 0, \"detail_show\": 1, \"all_list_show\": 0, \"id\": \"row_122\", \"sortNum\": 6}, {\"label\": \"修改时间\", \"field\": \"update_time\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field_type\": \"TIMESTAMP\", \"default_value\": \"server_default:CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP\", \"length\": 0, \"nullable\": 1, \"primary_key\": 0, \"is_only\": 0, \"is_json\": 0, \"clearable\": 0, \"editable\": 0, \"customRender\": 0, \"list_show\": 1, \"table_show\": 1, \"edit_show\": 0, \"detail_show\": 1, \"all_list_show\": 0, \"id\": \"row_123\", \"sortNum\": 7}, {\"label\": \"软删除标记\", \"field\": \"del_flag\", \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"field_type\": \"SmallInteger\", \"default_value\": 0, \"length\": 0, \"nullable\": 1, \"primary_key\": 0, \"is_only\": 0, \"is_json\": 0, \"clearable\": 0, \"editable\": 0, \"customRender\": 1, \"list_show\": 1, \"table_show\": 0, \"edit_show\": 0, \"detail_show\": 1, \"all_list_show\": 0, \"id\": \"row_124\", \"sortNum\": 8}, {\"label\": \"排序字段\", \"field\": \"sort_no\", \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"field_type\": \"Float\", \"default_value\": 1, \"length\": 0, \"nullable\": 1, \"primary_key\": 0, \"is_only\": 0, \"is_json\": 0, \"clearable\": 0, \"editable\": 0, \"customRender\": 0, \"list_show\": 1, \"table_show\": 0, \"edit_show\": 0, \"detail_show\": 1, \"all_list_show\": 0, \"id\": \"row_125\", \"sortNum\": 9}, {\"label\": \"简介描述\", \"field\": \"description\", \"component\": \"TextArea\", \"componentProps\": \"{}\", \"field_type\": \"Text\", \"default_value\": \"\", \"length\": 0, \"nullable\": 1, \"primary_key\": 0, \"is_only\": 0, \"is_json\": 0, \"clearable\": 0, \"editable\": 1, \"customRender\": 0, \"list_show\": 1, \"table_show\": 1, \"edit_show\": 1, \"detail_show\": 1, \"all_list_show\": 0, \"id\": \"row_126\", \"sortNum\": 10}]', 1, 1, 1, 1, 1, 800, 0);
INSERT INTO `code_gen_model` VALUES ('', 1, 0, 'admin', '2023-06-14 14:25:04', 'admin', '2023-06-19 10:53:44', '3cadd1ec134e4149accb7460db62e88e', '告警', 'alert', '/alert', '告警', 'Alert', 1, 'alert', '告警', 1, '[{\"label\": \"\\u544a\\u8b66\\u6807\\u9898\", \"field\": \"title\", \"component\": \"Input\", \"componentProps\": \"{}\", \"colProps\": \"{}\", \"sortNum\": 3}, {\"label\": \"\\u544a\\u8b66\\u7b49\\u7ea7\", \"field\": \"level\", \"component\": \"Input\", \"componentProps\": \"{}\", \"colProps\": \"{}\", \"sortNum\": 4}, {\"label\": \"\\u544a\\u8b66\\u72b6\\u6001\", \"field\": \"status\", \"component\": \"Input\", \"componentProps\": \"{}\", \"colProps\": \"{}\", \"sortNum\": 5}, {\"label\": \"\\u544a\\u8b66\\u5185\\u5bb9\", \"field\": \"content\", \"component\": \"Input\", \"componentProps\": \"{}\", \"colProps\": \"{}\", \"sortNum\": 6}, {\"label\": \"\\u521b\\u5efa\\u65f6\\u95f4\", \"field\": \"create_time\", \"component\": \"Input\", \"componentProps\": \"{}\", \"colProps\": \"{}\", \"sortNum\": 7}]', '[{\"function\": \"list\", \"id\": \"row_68\", \"is_show\": false, \"name\": \"\\u5217\\u8868\\u67e5\\u8be2\", \"permissions\": \"\", \"slot\": \"hideApi\", \"sortNum\": 3}, {\"function\": \"getAllList\", \"id\": \"row_69\", \"is_show\": false, \"name\": \"\\u5168\\u91cf\\u5217\\u8868\", \"permissions\": \"\", \"slot\": \"hideApi\", \"sortNum\": 4}, {\"function\": \"handleDetail\", \"id\": \"row_70\", \"is_show\": true, \"name\": \"\\u8be6\\u60c5\", \"permissions\": \"\", \"slot\": \"actionDropDown\", \"sortNum\": 5}, {\"function\": \"handleAdd\", \"id\": \"row_71\", \"is_show\": true, \"name\": \"\\u65b0\\u589e\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 6}, {\"function\": \"handleEdit\", \"id\": \"row_72\", \"is_show\": true, \"name\": \"\\u7f16\\u8f91\", \"permissions\": \"\", \"slot\": \"action\", \"sortNum\": 7}, {\"function\": \"handleDelete\", \"id\": \"row_73\", \"is_show\": true, \"name\": \"\\u5220\\u9664\", \"permissions\": \"\", \"slot\": \"actionDropDown\", \"sortNum\": 8}, {\"function\": \"batchHandleDelete\", \"id\": \"row_74\", \"is_show\": true, \"name\": \"\\u6279\\u91cf\\u5220\\u9664\", \"permissions\": \"\", \"slot\": \"overlay\", \"sortNum\": 9}, {\"function\": \"onImportXls\", \"id\": \"row_75\", \"is_show\": false, \"name\": \"\\u5bfc\\u5165\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 10}, {\"function\": \"onExportXls\", \"id\": \"row_76\", \"is_show\": false, \"name\": \"\\u5bfc\\u51fa\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 11}]', '[{\"all_list_show\": 1, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"id\", \"field_type\": \"String\", \"id\": \"row_60\", \"is_json\": 0, \"is_only\": 1, \"label\": \"id\", \"length\": 36, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 1, \"sortNum\": 3, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"strategy_id\", \"field_type\": \"String\", \"id\": \"row_121\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u544a\\u8b66\\u7b56\\u7565id\", \"length\": 36, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 4, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"title\", \"field_type\": \"String\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u544a\\u8b66\\u6807\\u9898\", \"length\": 500, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 5, \"table_show\": 1, \"id\": \"row_239\"}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"content\", \"field_type\": \"Text\", \"id\": \"row_258\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u544a\\u8b66\\u5185\\u5bb9\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 6, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"JDictSelectTag\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"0\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"level\", \"field_type\": \"Integer\", \"id\": \"row_186\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u544a\\u8b66\\u7b49\\u7ea7\", \"length\": 11, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 7, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"JDictSelectTag\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"0\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"status\", \"field_type\": \"SmallInteger\", \"id\": \"row_187\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u544a\\u8b66\\u72b6\\u6001\", \"length\": 6, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 8, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"rule_id\", \"field_type\": \"Text\", \"id\": \"row_188\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u89c4\\u5219\\u7f16\\u7801\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 9, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"rule_name\", \"field_type\": \"Text\", \"id\": \"row_189\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u89c4\\u5219\\u540d\\u79f0\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 10, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"biz\", \"field_type\": \"Text\", \"id\": \"row_60\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u544a\\u8b66\\u4e1a\\u52a1\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 11, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"source\", \"field_type\": \"Text\", \"id\": \"row_259\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u544a\\u8b66\\u5bf9\\u8c61\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 12, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"tags\", \"field_type\": \"Text\", \"id\": \"row_260\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u544a\\u8b66\\u6807\\u7b7e\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 13, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"metric\", \"field_type\": \"Text\", \"id\": \"row_261\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u544a\\u8b66\\u6307\\u6807\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 14, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"recover_time\", \"field_type\": \"TIMESTAMP\", \"id\": \"row_262\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u6062\\u590d\\u65f6\\u95f4\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 15, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"{}\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"ext_params\", \"field_type\": \"Text\", \"id\": \"row_122\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u989d\\u5916\\u53c2\\u6570\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 16, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"create_by\", \"field_type\": \"String\", \"id\": \"row_123\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u521b\\u5efa\\u8005\", \"length\": 100, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 17, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"server_default:CURRENT_TIMESTAMP\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"create_time\", \"field_type\": \"TIMESTAMP\", \"id\": \"row_62\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u521b\\u5efa\\u65f6\\u95f4\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 18, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"update_by\", \"field_type\": \"String\", \"id\": \"row_63\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u4fee\\u6539\\u8005\", \"length\": 100, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 19, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"server_default:CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"update_time\", \"field_type\": \"TIMESTAMP\", \"id\": \"row_64\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u4fee\\u6539\\u65f6\\u95f4\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 20, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"customRender\": 1, \"default_value\": 0, \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"del_flag\", \"field_type\": \"SmallInteger\", \"id\": \"row_65\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u8f6f\\u5220\\u9664\\u6807\\u8bb0\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 21, \"table_show\": 0}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": 1, \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"sort_no\", \"field_type\": \"Float\", \"id\": \"row_66\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u6392\\u5e8f\\u5b57\\u6bb5\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 22, \"table_show\": 0}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputTextArea\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"description\", \"field_type\": \"Text\", \"id\": \"row_67\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u7b80\\u4ecb\\u63cf\\u8ff0\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 23, \"table_show\": 1}]', 1, 1, 1, 1, 1, 800, 0);
INSERT INTO `code_gen_model` VALUES ('', 1, 0, 'admin', '2023-04-11 17:26:58', '', '2023-04-11 17:26:58', '473a1edc8dff4c288160f3076e62f34a', 'worker管理', 'worker', '/scheduler', 'worker', 'Worker', 1, 'Worker', '', 1, '[{\"label\": \"名称\", \"field\": \"hostname\", \"component\": \"Input\", \"componentProps\": \"{}\", \"colProps\": \"{}\", \"sortNum\": 3}]', '[{\"name\": \"列表查询\", \"slot\": \"hideApi\", \"function\": \"list\", \"is_show\": false, \"permissions\": \"\", \"id\": \"row_144\", \"sortNum\": 3}, {\"name\": \"全量列表\", \"slot\": \"hideApi\", \"function\": \"getAllList\", \"is_show\": false, \"permissions\": \"\", \"id\": \"row_145\", \"sortNum\": 4}, {\"name\": \"详情\", \"slot\": \"actionDropDown\", \"function\": \"handleDetail\", \"is_show\": true, \"permissions\": \"\", \"id\": \"row_146\", \"sortNum\": 5}, {\"name\": \"新增\", \"slot\": \"tableTitle\", \"function\": \"handleAdd\", \"is_show\": true, \"permissions\": \"\", \"id\": \"row_147\", \"sortNum\": 6}, {\"name\": \"编辑\", \"slot\": \"action\", \"function\": \"handleEdit\", \"is_show\": true, \"permissions\": \"\", \"id\": \"row_148\", \"sortNum\": 7}, {\"name\": \"删除\", \"slot\": \"actionDropDown\", \"function\": \"handleDelete\", \"is_show\": false, \"permissions\": \"\", \"id\": \"row_149\", \"sortNum\": 8}, {\"name\": \"批量删除\", \"slot\": \"overlay\", \"function\": \"batchHandleDelete\", \"is_show\": false, \"permissions\": \"\", \"id\": \"row_150\", \"sortNum\": 9}, {\"name\": \"导入\", \"slot\": \"tableTitle\", \"function\": \"onImportXls\", \"is_show\": false, \"permissions\": \"\", \"id\": \"row_151\", \"sortNum\": 10}, {\"name\": \"导出\", \"slot\": \"tableTitle\", \"function\": \"onExportXls\", \"is_show\": false, \"permissions\": \"\", \"id\": \"row_152\", \"sortNum\": 11}]', '[{\"label\": \"pid\", \"field\": \"pid\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field_type\": \"Text\", \"default_value\": \"\", \"length\": 0, \"primary_key\": 0, \"is_json\": 0, \"is_only\": 0, \"nullable\": 1, \"editable\": 1, \"clearable\": 0, \"table_show\": 1, \"customRender\": 0, \"edit_show\": 1, \"list_show\": 1, \"detail_show\": 1, \"all_list_show\": 0, \"sortNum\": 3}, {\"label\": \"名称\", \"field\": \"hostname\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field_type\": \"Text\", \"default_value\": \"\", \"length\": 0, \"primary_key\": 0, \"is_json\": 0, \"is_only\": 0, \"nullable\": 1, \"editable\": 1, \"clearable\": 0, \"table_show\": 1, \"customRender\": 0, \"edit_show\": 1, \"list_show\": 1, \"detail_show\": 1, \"all_list_show\": 0, \"sortNum\": 4}, {\"label\": \"运行中任务\", \"field\": \"active\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field_type\": \"Text\", \"default_value\": \"\", \"length\": 0, \"primary_key\": 0, \"is_json\": 0, \"is_only\": 0, \"nullable\": 1, \"editable\": 1, \"clearable\": 0, \"table_show\": 1, \"customRender\": 0, \"edit_show\": 1, \"list_show\": 1, \"detail_show\": 1, \"all_list_show\": 0, \"sortNum\": 5}, {\"label\": \"已处理\", \"field\": \"processed\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field_type\": \"Text\", \"default_value\": \"\", \"length\": 0, \"primary_key\": 0, \"is_json\": 0, \"is_only\": 0, \"nullable\": 1, \"editable\": 1, \"clearable\": 0, \"table_show\": 1, \"customRender\": 0, \"edit_show\": 1, \"list_show\": 1, \"detail_show\": 1, \"all_list_show\": 0, \"sortNum\": 6}, {\"label\": \"状态\", \"field\": \"status\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field_type\": \"Text\", \"default_value\": \"\", \"length\": 0, \"primary_key\": 0, \"is_json\": 0, \"is_only\": 0, \"nullable\": 1, \"editable\": 1, \"clearable\": 0, \"table_show\": 1, \"customRender\": 0, \"edit_show\": 1, \"list_show\": 1, \"detail_show\": 1, \"all_list_show\": 0, \"sortNum\": 7}, {\"label\": \"负载\", \"field\": \"loadavg\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field_type\": \"Text\", \"default_value\": \"\", \"length\": 0, \"primary_key\": 0, \"is_json\": 0, \"is_only\": 0, \"nullable\": 1, \"editable\": 1, \"clearable\": 0, \"table_show\": 1, \"customRender\": 0, \"edit_show\": 1, \"list_show\": 1, \"detail_show\": 1, \"all_list_show\": 0, \"sortNum\": 8}]', 1, 1, 1, 1, 1, 800, 0);
INSERT INTO `code_gen_model` VALUES ('', 1, 0, 'admin', '2023-03-03 17:24:25', 'admin', '2023-03-05 17:20:47', '4b331074224e47c8a131b8a2b9ca740b', '任务模版', 'task_template', '/task/template', '任务模版', 'TaskTemplate', 1, 'task_template', '任务模版', 1, '[{\"colProps\": \"{}\", \"component\": \"JSelectInput\", \"componentProps\": \"{\\n      \\\"options\\\": [\\n        { \\\"label\\\": \\\"\\u7ec4\\u4ef6\\u578b\\\", \\\"value\\\": \\\"component\\\" },\\n        { \\\"label\\\": \\\"\\u914d\\u7f6e\\u578b\\\", \\\"value\\\": \\\"option\\\" },\\n      ]\\n    }\", \"field\": \"type\", \"id\": \"row_120\", \"label\": \"\\u6a21\\u7248\\u7c7b\\u578b\", \"sortNum\": 3}]', '[{\"function\": \"list\", \"id\": \"row_68\", \"is_show\": false, \"name\": \"\\u5217\\u8868\\u67e5\\u8be2\", \"permissions\": \"\", \"slot\": \"hideApi\", \"sortNum\": 3}, {\"function\": \"getAllList\", \"id\": \"row_69\", \"is_show\": false, \"name\": \"\\u5168\\u91cf\\u5217\\u8868\", \"permissions\": \"\", \"slot\": \"hideApi\", \"sortNum\": 4}, {\"function\": \"handleDetail\", \"id\": \"row_70\", \"is_show\": true, \"name\": \"\\u8be6\\u60c5\", \"permissions\": \"\", \"slot\": \"actionDropDown\", \"sortNum\": 5}, {\"function\": \"handleAdd\", \"id\": \"row_71\", \"is_show\": true, \"name\": \"\\u65b0\\u589e\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 6}, {\"function\": \"handleEdit\", \"id\": \"row_72\", \"is_show\": true, \"name\": \"\\u7f16\\u8f91\", \"permissions\": \"\", \"slot\": \"action\", \"sortNum\": 7}, {\"function\": \"handleDelete\", \"id\": \"row_73\", \"is_show\": true, \"name\": \"\\u5220\\u9664\", \"permissions\": \"\", \"slot\": \"actionDropDown\", \"sortNum\": 8}, {\"function\": \"batchHandleDelete\", \"id\": \"row_74\", \"is_show\": true, \"name\": \"\\u6279\\u91cf\\u5220\\u9664\", \"permissions\": \"\", \"slot\": \"overlay\", \"sortNum\": 9}, {\"function\": \"onImportXls\", \"id\": \"row_75\", \"is_show\": false, \"name\": \"\\u5bfc\\u5165\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 10}, {\"function\": \"onExportXls\", \"id\": \"row_76\", \"is_show\": false, \"name\": \"\\u5bfc\\u51fa\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 11}]', '[{\"all_list_show\": 1, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"id\", \"field_type\": \"String\", \"id\": \"row_60\", \"is_json\": 0, \"is_only\": 1, \"label\": \"\\u4e3b\\u952e\", \"length\": 36, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 1, \"sortNum\": 3, \"table_show\": 1}, {\"all_list_show\": 1, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"name\", \"field_type\": \"String\", \"id\": \"row_155\", \"is_json\": 0, \"is_only\": 1, \"label\": \"\\u6a21\\u7248\\u540d\\u79f0\", \"length\": 200, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 4, \"table_show\": 1}, {\"all_list_show\": 1, \"clearable\": 0, \"component\": \"JSelectInput\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"1\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"type\", \"field_type\": \"SmallInteger\", \"id\": \"row_156\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u6a21\\u7248\\u7c7b\\u578b\", \"length\": 6, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 5, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"JSelectInput\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"component\", \"field_type\": \"String\", \"id\": \"row_528\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u4efb\\u52a1\\u7ec4\\u4ef6\", \"length\": 500, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 6, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputTextArea\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"{}\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"params\", \"field_type\": \"Text\", \"id\": \"row_119\", \"is_json\": 1, \"is_only\": 0, \"label\": \"\\u6a21\\u7248\\u914d\\u7f6e\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 7, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"0\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"status\", \"field_type\": \"SmallInteger\", \"id\": \"row_125\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u72b6\\u6001\", \"length\": 6, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 8, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"create_by\", \"field_type\": \"String\", \"id\": \"row_61\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u521b\\u5efa\\u8005\", \"length\": 100, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 9, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"server_default:CURRENT_TIMESTAMP\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"create_time\", \"field_type\": \"TIMESTAMP\", \"id\": \"row_62\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u521b\\u5efa\\u65f6\\u95f4\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 10, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"update_by\", \"field_type\": \"String\", \"id\": \"row_63\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u4fee\\u6539\\u8005\", \"length\": 100, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 11, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"server_default:CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"update_time\", \"field_type\": \"TIMESTAMP\", \"id\": \"row_64\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u4fee\\u6539\\u65f6\\u95f4\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 12, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"customRender\": 1, \"default_value\": 0, \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"del_flag\", \"field_type\": \"SmallInteger\", \"id\": \"row_65\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u8f6f\\u5220\\u9664\\u6807\\u8bb0\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 13, \"table_show\": 0}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": 1, \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"sort_no\", \"field_type\": \"Float\", \"id\": \"row_66\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u6392\\u5e8f\\u5b57\\u6bb5\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 14, \"table_show\": 0}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputTextArea\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"description\", \"field_type\": \"Text\", \"id\": \"row_67\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u7b80\\u4ecb\\u63cf\\u8ff0\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 15, \"table_show\": 1}]', 1, 1, 1, 1, 1, 800, 0);
INSERT INTO `code_gen_model` VALUES ('', 1, 0, 'admin', '2023-03-03 17:24:25', 'admin', '2023-09-08 05:09:54', '4b331074224e47c8a131b8a2b9ca740f', '算法管理', 'algorithm', '/algorithm', '算法', 'Algorithm', 1, 'algorithm', '算法', 1, '[{\"colProps\": \"{}\", \"component\": \"JSelectInput\", \"componentProps\": \"{\\n      \\\"options\\\": [\\n        { \\\"label\\\": \\\"\\u7ec4\\u4ef6\\u578b\\\", \\\"value\\\": \\\"component\\\" },\\n        { \\\"label\\\": \\\"\\u914d\\u7f6e\\u578b\\\", \\\"value\\\": \\\"option\\\" },\\n      ]\\n    }\", \"field\": \"type\", \"id\": \"row_120\", \"label\": \"\\u6a21\\u7248\\u7c7b\\u578b\", \"sortNum\": 3}]', '[{\"function\": \"list\", \"id\": \"row_68\", \"is_show\": false, \"name\": \"\\u5217\\u8868\\u67e5\\u8be2\", \"permissions\": \"\", \"slot\": \"hideApi\", \"sortNum\": 3}, {\"function\": \"getAllList\", \"id\": \"row_69\", \"is_show\": false, \"name\": \"\\u5168\\u91cf\\u5217\\u8868\", \"permissions\": \"\", \"slot\": \"hideApi\", \"sortNum\": 4}, {\"function\": \"handleDetail\", \"id\": \"row_70\", \"is_show\": true, \"name\": \"\\u8be6\\u60c5\", \"permissions\": \"\", \"slot\": \"actionDropDown\", \"sortNum\": 5}, {\"function\": \"handleAdd\", \"id\": \"row_71\", \"is_show\": true, \"name\": \"\\u65b0\\u589e\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 6}, {\"function\": \"handleEdit\", \"id\": \"row_72\", \"is_show\": true, \"name\": \"\\u7f16\\u8f91\", \"permissions\": \"\", \"slot\": \"action\", \"sortNum\": 7}, {\"function\": \"handleDelete\", \"id\": \"row_73\", \"is_show\": true, \"name\": \"\\u5220\\u9664\", \"permissions\": \"\", \"slot\": \"actionDropDown\", \"sortNum\": 8}, {\"function\": \"batchHandleDelete\", \"id\": \"row_74\", \"is_show\": true, \"name\": \"\\u6279\\u91cf\\u5220\\u9664\", \"permissions\": \"\", \"slot\": \"overlay\", \"sortNum\": 9}, {\"function\": \"onImportXls\", \"id\": \"row_75\", \"is_show\": false, \"name\": \"\\u5bfc\\u5165\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 10}, {\"function\": \"onExportXls\", \"id\": \"row_76\", \"is_show\": false, \"name\": \"\\u5bfc\\u51fa\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 11}]', '[{\"all_list_show\": 1, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"id\", \"field_type\": \"String\", \"id\": \"row_121\", \"is_json\": 0, \"is_only\": 1, \"label\": \"\\u4e3b\\u952e\", \"length\": 36, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 1, \"sortNum\": 3, \"table_show\": 1}, {\"all_list_show\": 1, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"name\", \"field_type\": \"String\", \"id\": \"row_155\", \"is_json\": 0, \"is_only\": 1, \"label\": \"\\u7b97\\u6cd5\\u540d\\u79f0\", \"length\": 200, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 4, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"code\", \"field_type\": \"String\", \"id\": \"row_122\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u7b97\\u6cd5\\u7f16\\u7801\", \"length\": 200, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 5, \"table_show\": 1}, {\"all_list_show\": 1, \"clearable\": 0, \"component\": \"JSelectInput\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"type\", \"field_type\": \"String\", \"id\": \"row_156\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u7b97\\u6cd5\\u7c7b\\u578b\", \"length\": 200, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 6, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"JSelectInput\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"1\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"form_type\", \"field_type\": \"SmallInteger\", \"id\": \"row_60\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u8868\\u5355\\u7c7b\\u578b\", \"length\": 6, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 7, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"JSelectInput\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"component\", \"field_type\": \"String\", \"id\": \"row_528\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u7b97\\u6cd5\\u7ec4\\u4ef6\", \"length\": 500, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 8, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputTextArea\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"{}\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"params\", \"field_type\": \"Text\", \"id\": \"row_119\", \"is_json\": 1, \"is_only\": 0, \"label\": \"\\u7b97\\u6cd5\\u914d\\u7f6e\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 9, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"0\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"status\", \"field_type\": \"SmallInteger\", \"id\": \"row_61\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u72b6\\u6001\", \"length\": 6, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 10, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"create_by\", \"field_type\": \"String\", \"id\": \"row_124\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u521b\\u5efa\\u8005\", \"length\": 100, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 11, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"server_default:CURRENT_TIMESTAMP\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"create_time\", \"field_type\": \"TIMESTAMP\", \"id\": \"row_62\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u521b\\u5efa\\u65f6\\u95f4\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 12, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"update_by\", \"field_type\": \"String\", \"id\": \"row_63\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u4fee\\u6539\\u8005\", \"length\": 100, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 13, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"server_default:CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"update_time\", \"field_type\": \"TIMESTAMP\", \"id\": \"row_64\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u4fee\\u6539\\u65f6\\u95f4\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 14, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"customRender\": 1, \"default_value\": 0, \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"del_flag\", \"field_type\": \"SmallInteger\", \"id\": \"row_65\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u8f6f\\u5220\\u9664\\u6807\\u8bb0\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 15, \"table_show\": 0}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": 1, \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"sort_no\", \"field_type\": \"Float\", \"id\": \"row_66\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u6392\\u5e8f\\u5b57\\u6bb5\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 16, \"table_show\": 0}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputTextArea\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"description\", \"field_type\": \"Text\", \"id\": \"row_67\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u7b80\\u4ecb\\u63cf\\u8ff0\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 17, \"table_show\": 1}]', 1, 1, 1, 1, 2, 600, 0);
INSERT INTO `code_gen_model` VALUES ('', 1, 0, 'admin', '2022-12-01 16:56:24', 'admin', '2022-12-20 09:14:26', '5deb88593c024033ae6de2f9ed5e7806', '测试', 'test', '/test', '测试', 'Test', 1, 'test', '', 1, '[{\"colProps\": \"{}\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field\": \"search_text\", \"id\": \"row_441\", \"label\": \"\\u5173\\u952e\\u8bcd\", \"sortNum\": 3}, {\"colProps\": \"{ \\\"span\\\": 6 }\", \"component\": \"JDictSelectTag\", \"componentProps\": \"{ \\t\\\"dictCode\\\": \\\"code_gen_model_type\\\", \\t\\\"placeholder\\\": \\\"\\u8bf7\\u9009\\u62e9\\u6a21\\u578b\\u7c7b\\u578b\\\", \\t\\\"stringToNumber\\\": true }\", \"field\": \"model_type\", \"id\": \"row_59\", \"label\": \"\\u6a21\\u578b\\u7c7b\\u578b\", \"sortNum\": 4}]', '[{\"function\": \"list\", \"id\": \"row_504\", \"is_show\": false, \"name\": \"\\u5217\\u8868\\u67e5\\u8be2\", \"permissions\": \"test:query,aaa\", \"slot\": \"hideApi\", \"sortNum\": 3}, {\"function\": \"getAllList\", \"id\": \"row_505\", \"is_show\": false, \"name\": \"\\u5168\\u91cf\\u5217\\u8868\", \"permissions\": \"\", \"slot\": \"hideApi\", \"sortNum\": 4}, {\"function\": \"handleDetail\", \"id\": \"6\", \"is_show\": false, \"name\": \"\\u8be6\\u60c5\", \"permissions\": \"\", \"slot\": \"hideApi\", \"sortNum\": 5}, {\"function\": \"handleAdd\", \"id\": \"1\", \"is_show\": true, \"name\": \"\\u65b0\\u589e\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 6}, {\"function\": \"handleEdit\", \"id\": \"5\", \"is_show\": true, \"name\": \"\\u7f16\\u8f91\", \"permissions\": \"\", \"slot\": \"action\", \"sortNum\": 7}, {\"function\": \"handleDelete\", \"id\": \"7\", \"is_show\": true, \"name\": \"\\u5220\\u9664\", \"permissions\": \"\", \"slot\": \"actionDropDown\", \"sortNum\": 8}]', '[{\"all_list_show\": 1, \"base_list_show\": 1, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"id\", \"field_type\": \"String\", \"id\": \"row_147\", \"is_json\": 0, \"is_only\": 1, \"label\": \"\\u4e3b\\u952e\", \"length\": 36, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 1, \"sortNum\": 3, \"table_show\": 1}, {\"all_list_show\": 0, \"base_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"create_by\", \"field_type\": \"String\", \"id\": \"row_148\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u521b\\u5efa\\u8005\", \"length\": 100, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 4, \"table_show\": 1}, {\"all_list_show\": 0, \"base_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"default_value\": \"server_default:CURRENT_TIMESTAMP\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"create_time\", \"field_type\": \"TIMESTAMP\", \"id\": \"row_149\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u521b\\u5efa\\u65f6\\u95f4\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 5, \"table_show\": 1}, {\"all_list_show\": 0, \"base_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"update_by\", \"field_type\": \"String\", \"id\": \"row_150\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u4fee\\u6539\\u8005\", \"length\": 100, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 6, \"table_show\": 1}, {\"all_list_show\": 0, \"base_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"default_value\": \"server_default:CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"update_time\", \"field_type\": \"TIMESTAMP\", \"id\": \"row_151\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u4fee\\u6539\\u65f6\\u95f4\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 7, \"table_show\": 1}, {\"all_list_show\": 0, \"base_list_show\": 0, \"clearable\": 0, \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"default_value\": 0, \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"del_flag\", \"field_type\": \"SmallInteger\", \"id\": \"row_152\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u8f6f\\u5220\\u9664\\u6807\\u8bb0\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 8, \"table_show\": 0}, {\"all_list_show\": 0, \"base_list_show\": 0, \"clearable\": 0, \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"default_value\": 1, \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"sort_no\", \"field_type\": \"Float\", \"id\": \"row_153\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u6392\\u5e8f\\u5b57\\u6bb5\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 9, \"table_show\": 0}, {\"all_list_show\": 0, \"base_list_show\": 0, \"clearable\": 0, \"component\": \"InputTextArea\", \"componentProps\": \"{}\", \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"description\", \"field_type\": \"Text\", \"id\": \"row_154\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u7b80\\u4ecb\\u63cf\\u8ff0\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 10, \"table_show\": 1}, {\"all_list_show\": 1, \"base_list_show\": 1, \"clearable\": 1, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 1, \"default_value\": \"{}\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"test\", \"field_type\": \"Text\", \"id\": \"row_440\", \"is_json\": 0, \"is_only\": 1, \"label\": \"\\u6d4b\\u8bd5\\u5b57\\u6bb5\", \"length\": 0, \"list_show\": 1, \"nullable\": 0, \"primary_key\": 0, \"sortNum\": 11, \"table_show\": 1}, {\"all_list_show\": 1, \"clearable\": 1, \"component\": \"JDictSelectTag\", \"componentProps\": \"{ \\t\\\"dictCode\\\": \\\"code_gen_model_type\\\", \\t\\\"placeholder\\\": \\\"\\u8bf7\\u9009\\u62e9\\u6a21\\u578b\\u7c7b\\u578b\\\", \\t\\\"stringToNumber\\\": true }\", \"customRender\": 1, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"model_type\", \"field_type\": \"Text\", \"id\": \"row_180\", \"is_json\": 0, \"is_only\": 1, \"label\": \"\\u6a21\\u578b\\u7c7b\\u578b\", \"length\": 0, \"list_show\": 1, \"nullable\": 0, \"primary_key\": 0, \"sortNum\": 12, \"table_show\": 1}]', 1, 1, 1, 1, 1, 0, 0);
INSERT INTO `code_gen_model` VALUES ('', 1, 0, 'admin', '2022-12-17 15:33:49', 'admin', '2022-12-18 11:23:11', '817ee8d317004359ab68d1132aff8a28', '数据源管理', 'datasource', 'datasource', '数据源', 'DataSource', 1, 'datasource', '数据源表', 1, '[{\"colProps\": \"{}\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field\": \"name\", \"id\": \"row_440\", \"label\": \"\\u6570\\u636e\\u6e90\\u540d\\u79f0\", \"sortNum\": 3}, {\"colProps\": \"{}\", \"component\": \"JDictSelectTag\", \"componentProps\": \"{ \\t\\\"dictCode\\\": \\\"datasource_type\\\", \\t\\\"placeholder\\\": \\\"\\u8bf7\\u9009\\u62e9\\u6570\\u636e\\u6e90\\u7c7b\\u578b\\\", \\t\\\"stringToNumber\\\": false }\", \"field\": \"type\", \"id\": \"row_441\", \"label\": \"\\u6570\\u636e\\u6e90\\u7c7b\\u578b\", \"sortNum\": 4}]', '[{\"function\": \"list\", \"id\": \"row_149\", \"is_show\": false, \"name\": \"\\u5217\\u8868\\u67e5\\u8be2\", \"permissions\": \"\", \"slot\": \"hideApi\", \"sortNum\": 3}, {\"function\": \"getAllList\", \"id\": \"row_150\", \"is_show\": false, \"name\": \"\\u5168\\u91cf\\u5217\\u8868\", \"permissions\": \"\", \"slot\": \"hideApi\", \"sortNum\": 4}, {\"function\": \"handleDetail\", \"id\": \"row_151\", \"is_show\": true, \"name\": \"\\u8be6\\u60c5\", \"permissions\": \"\", \"slot\": \"actionDropDown\", \"sortNum\": 5}, {\"function\": \"handleAdd\", \"id\": \"row_152\", \"is_show\": true, \"name\": \"\\u65b0\\u589e\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 6}, {\"function\": \"handleEdit\", \"id\": \"row_153\", \"is_show\": true, \"name\": \"\\u7f16\\u8f91\", \"permissions\": \"\", \"slot\": \"action\", \"sortNum\": 7}, {\"function\": \"handleDelete\", \"id\": \"row_154\", \"is_show\": true, \"name\": \"\\u5220\\u9664\", \"permissions\": \"\", \"slot\": \"actionDropDown\", \"sortNum\": 8}, {\"function\": \"batchHandleDelete\", \"id\": \"row_155\", \"is_show\": true, \"name\": \"\\u6279\\u91cf\\u5220\\u9664\", \"permissions\": \"\", \"slot\": \"overlay\", \"sortNum\": 9}, {\"function\": \"onImportXls\", \"id\": \"row_156\", \"is_show\": false, \"name\": \"\\u5bfc\\u5165\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 10}, {\"function\": \"onExportXls\", \"id\": \"row_157\", \"is_show\": false, \"name\": \"\\u5bfc\\u51fa\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 11}]', '[{\"all_list_show\": 1, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"id\", \"field_type\": \"String\", \"id\": \"row_141\", \"is_json\": 0, \"is_only\": 1, \"label\": \"ID\", \"length\": 36, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 1, \"sortNum\": 3, \"table_show\": 1}, {\"all_list_show\": 1, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"name\", \"field_type\": \"String\", \"id\": \"row_369\", \"is_json\": 0, \"is_only\": 1, \"label\": \"\\u540d\\u79f0\", \"length\": 200, \"list_show\": 1, \"nullable\": 0, \"primary_key\": 0, \"sortNum\": 4, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"JDictSelectTag\", \"componentProps\": \"{ \\t\\\"dictCode\\\": \\\"datasource_type\\\", \\t\\\"placeholder\\\": \\\"\\u8bf7\\u9009\\u62e9\\u6570\\u636e\\u6e90\\u7c7b\\u578b\\\", \\t\\\"stringToNumber\\\": false }\", \"customRender\": 1, \"default_value\": \"mysql\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"type\", \"field_type\": \"String\", \"id\": \"row_370\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u7c7b\\u578b\", \"length\": 200, \"list_show\": 1, \"nullable\": 0, \"primary_key\": 0, \"sortNum\": 5, \"table_show\": 0}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputTextArea\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"{}\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"conn_conf\", \"field_type\": \"Text\", \"id\": \"row_371\", \"is_json\": 1, \"is_only\": 0, \"label\": \"\\u8fde\\u63a5\\u914d\\u7f6e\", \"length\": 0, \"list_show\": 1, \"nullable\": 0, \"primary_key\": 0, \"sortNum\": 6, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"0\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"status\", \"field_type\": \"Integer\", \"id\": \"row_372\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u72b6\\u6001\", \"length\": 11, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 7, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputTextArea\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"{}\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"ext_params\", \"field_type\": \"Text\", \"id\": \"row_373\", \"is_json\": 1, \"is_only\": 0, \"label\": \"\\u989d\\u5916\\u53c2\\u6570\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 8, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputTextArea\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"description\", \"field_type\": \"Text\", \"id\": \"row_148\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u63cf\\u8ff0\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 9, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"create_by\", \"field_type\": \"String\", \"id\": \"row_142\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u521b\\u5efa\\u8005\", \"length\": 100, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 10, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"server_default:CURRENT_TIMESTAMP\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"create_time\", \"field_type\": \"TIMESTAMP\", \"id\": \"row_143\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u521b\\u5efa\\u65f6\\u95f4\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 11, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"update_by\", \"field_type\": \"String\", \"id\": \"row_144\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u4fee\\u6539\\u8005\", \"length\": 100, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 12, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"server_default:CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"update_time\", \"field_type\": \"TIMESTAMP\", \"id\": \"row_145\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u4fee\\u6539\\u65f6\\u95f4\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 13, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": 1, \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"sort_no\", \"field_type\": \"Float\", \"id\": \"row_147\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u6392\\u5e8f\\u5b57\\u6bb5\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 14, \"table_show\": 0}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"customRender\": 1, \"default_value\": 0, \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"del_flag\", \"field_type\": \"SmallInteger\", \"id\": \"row_146\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u8f6f\\u5220\\u9664\\u6807\\u8bb0\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 15, \"table_show\": 0}]', 1, 1, 1, 1, 1, 800, 0);
INSERT INTO `code_gen_model` VALUES ('', 1, 0, 'admin', '2023-03-05 13:13:33', 'admin', '2023-03-05 17:20:29', '94e5800973314fde953ed0f579d14db9', '任务', 'task', '/task', '任务', 'Task', 1, 'task', '', 1, '[{\"label\": \"\\u4efb\\u52a1\\u6a21\\u7248\", \"field\": \"template_id\", \"component\": \"ApiSelect\", \"componentProps\": \"{}\", \"colProps\": \"{}\", \"sortNum\": 3}, {\"label\": \"\\u540d\\u79f0\", \"field\": \"name\", \"component\": \"Input\", \"componentProps\": \"{}\", \"colProps\": \"{}\", \"sortNum\": 4}]', '[{\"function\": \"list\", \"id\": \"row_191\", \"is_show\": false, \"name\": \"\\u5217\\u8868\\u67e5\\u8be2\", \"permissions\": \"\", \"slot\": \"hideApi\", \"sortNum\": 3}, {\"function\": \"getAllList\", \"id\": \"row_192\", \"is_show\": false, \"name\": \"\\u5168\\u91cf\\u5217\\u8868\", \"permissions\": \"\", \"slot\": \"hideApi\", \"sortNum\": 4}, {\"function\": \"handleDetail\", \"id\": \"row_193\", \"is_show\": true, \"name\": \"\\u8be6\\u60c5\", \"permissions\": \"\", \"slot\": \"actionDropDown\", \"sortNum\": 5}, {\"function\": \"handleAdd\", \"id\": \"row_194\", \"is_show\": true, \"name\": \"\\u65b0\\u589e\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 6}, {\"function\": \"handleEdit\", \"id\": \"row_195\", \"is_show\": true, \"name\": \"\\u7f16\\u8f91\", \"permissions\": \"\", \"slot\": \"action\", \"sortNum\": 7}, {\"function\": \"handleDelete\", \"id\": \"row_196\", \"is_show\": true, \"name\": \"\\u5220\\u9664\", \"permissions\": \"\", \"slot\": \"actionDropDown\", \"sortNum\": 8}, {\"function\": \"batchHandleDelete\", \"id\": \"row_197\", \"is_show\": true, \"name\": \"\\u6279\\u91cf\\u5220\\u9664\", \"permissions\": \"\", \"slot\": \"overlay\", \"sortNum\": 9}, {\"function\": \"onImportXls\", \"id\": \"row_198\", \"is_show\": false, \"name\": \"\\u5bfc\\u5165\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 10}, {\"function\": \"onExportXls\", \"id\": \"row_199\", \"is_show\": false, \"name\": \"\\u5bfc\\u51fa\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 11}]', '[{\"all_list_show\": 1, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"id\", \"field_type\": \"String\", \"id\": \"row_183\", \"is_json\": 0, \"is_only\": 1, \"label\": \"id\", \"length\": 36, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 1, \"sortNum\": 3, \"table_show\": 1}, {\"all_list_show\": 1, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"parent_id\", \"field_type\": \"String\", \"id\": \"row_400\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u7236\\u4efb\\u52a1id\", \"length\": 36, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 4, \"table_show\": 1}, {\"all_list_show\": 1, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"template_id\", \"field_type\": \"String\", \"id\": \"row_401\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u4efb\\u52a1\\u6a21\\u7248id\", \"length\": 36, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 5, \"table_show\": 1}, {\"all_list_show\": 1, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"name\", \"field_type\": \"String\", \"id\": \"row_402\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u540d\\u79f0\", \"length\": 100, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 6, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"{}\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"params\", \"field_type\": \"Text\", \"id\": \"row_403\", \"is_json\": 1, \"is_only\": 0, \"label\": \"\\u53c2\\u6570\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 7, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"0\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"status\", \"field_type\": \"SmallInteger\", \"id\": \"row_711\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u72b6\\u6001\", \"length\": 6, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 8, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"2\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"trigger_type\", \"field_type\": \"SmallInteger\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u89e6\\u53d1\\u65b9\\u5f0f\", \"length\": 6, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 9, \"table_show\": 1, \"id\": \"row_251\"}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"crontab\", \"field_type\": \"String\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u5b9a\\u65f6\\u8bbe\\u7f6e\", \"length\": 500, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 10, \"table_show\": 1, \"id\": \"row_252\"}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"create_by\", \"field_type\": \"String\", \"id\": \"row_184\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u521b\\u5efa\\u8005\", \"length\": 100, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 11, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"server_default:CURRENT_TIMESTAMP\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"create_time\", \"field_type\": \"TIMESTAMP\", \"id\": \"row_185\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u521b\\u5efa\\u65f6\\u95f4\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 12, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"update_by\", \"field_type\": \"String\", \"id\": \"row_186\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u4fee\\u6539\\u8005\", \"length\": 100, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 13, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"server_default:CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"update_time\", \"field_type\": \"TIMESTAMP\", \"id\": \"row_187\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u4fee\\u6539\\u65f6\\u95f4\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 14, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"customRender\": 1, \"default_value\": 0, \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"del_flag\", \"field_type\": \"SmallInteger\", \"id\": \"row_188\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u8f6f\\u5220\\u9664\\u6807\\u8bb0\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 15, \"table_show\": 0}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": 1, \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"sort_no\", \"field_type\": \"Float\", \"id\": \"row_189\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u6392\\u5e8f\\u5b57\\u6bb5\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 16, \"table_show\": 0}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputTextArea\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"description\", \"field_type\": \"Text\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u7b80\\u4ecb\\u63cf\\u8ff0\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 17, \"table_show\": 1, \"id\": \"row_253\"}]', 1, 1, 1, 1, 1, 800, 0);
INSERT INTO `code_gen_model` VALUES ('', 1, 0, 'admin', '2023-06-19 10:49:21', 'admin', '2023-06-19 11:57:40', '98f3b722dcb040ccb74cfd251b8764d5', '告警策略', 'alert_strategy', '/alert/strategy', '告警策略', 'AlertStrategy', 1, 'alert_strategy', '告警策略', 1, '[{\"colProps\": \"{}\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field\": \"name\", \"id\": \"row_579\", \"label\": \"\\u540d\\u79f0\", \"sortNum\": 3}, {\"colProps\": \"{}\", \"component\": \"JDictSelectTag\", \"componentProps\": \"{}\", \"field\": \"template_code\", \"id\": \"row_580\", \"label\": \"\\u7b56\\u7565\\u6a21\\u7248\", \"sortNum\": 4}]', '[{\"function\": \"list\", \"id\": \"row_312\", \"is_show\": false, \"name\": \"\\u5217\\u8868\\u67e5\\u8be2\", \"permissions\": \"\", \"slot\": \"hideApi\", \"sortNum\": 3}, {\"function\": \"getAllList\", \"id\": \"row_313\", \"is_show\": false, \"name\": \"\\u5168\\u91cf\\u5217\\u8868\", \"permissions\": \"\", \"slot\": \"hideApi\", \"sortNum\": 4}, {\"function\": \"handleDetail\", \"id\": \"row_314\", \"is_show\": true, \"name\": \"\\u8be6\\u60c5\", \"permissions\": \"\", \"slot\": \"actionDropDown\", \"sortNum\": 5}, {\"function\": \"handleAdd\", \"id\": \"row_315\", \"is_show\": true, \"name\": \"\\u65b0\\u589e\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 6}, {\"function\": \"handleEdit\", \"id\": \"row_316\", \"is_show\": true, \"name\": \"\\u7f16\\u8f91\", \"permissions\": \"\", \"slot\": \"action\", \"sortNum\": 7}, {\"function\": \"handleDelete\", \"id\": \"row_317\", \"is_show\": true, \"name\": \"\\u5220\\u9664\", \"permissions\": \"\", \"slot\": \"actionDropDown\", \"sortNum\": 8}, {\"function\": \"batchHandleDelete\", \"id\": \"row_318\", \"is_show\": true, \"name\": \"\\u6279\\u91cf\\u5220\\u9664\", \"permissions\": \"\", \"slot\": \"overlay\", \"sortNum\": 9}, {\"function\": \"onImportXls\", \"id\": \"row_319\", \"is_show\": false, \"name\": \"\\u5bfc\\u5165\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 10}, {\"function\": \"onExportXls\", \"id\": \"row_320\", \"is_show\": false, \"name\": \"\\u5bfc\\u51fa\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 11}]', '[{\"all_list_show\": 1, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"id\", \"field_type\": \"String\", \"id\": \"row_304\", \"is_json\": 0, \"is_only\": 1, \"label\": \"\\u4e3b\\u952e\", \"length\": 36, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 1, \"sortNum\": 3, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"name\", \"field_type\": \"String\", \"id\": \"row_441\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u7b56\\u7565\\u540d\\u79f0\", \"length\": 200, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 4, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"template_code\", \"field_type\": \"String\", \"id\": \"row_442\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u7b56\\u7565\\u6a21\\u7248\", \"length\": 100, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 5, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"{}\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"trigger_conf\", \"field_type\": \"Text\", \"id\": \"row_445\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u89e6\\u53d1\\u6761\\u4ef6\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 6, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"{}\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"forward_conf\", \"field_type\": \"Text\", \"id\": \"row_446\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u8f6c\\u53d1\\u6761\\u4ef6\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 7, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"create_by\", \"field_type\": \"String\", \"id\": \"row_305\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u521b\\u5efa\\u8005\", \"length\": 100, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 8, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"server_default:CURRENT_TIMESTAMP\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"create_time\", \"field_type\": \"TIMESTAMP\", \"id\": \"row_306\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u521b\\u5efa\\u65f6\\u95f4\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 9, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"update_by\", \"field_type\": \"String\", \"id\": \"row_307\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u4fee\\u6539\\u8005\", \"length\": 100, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 10, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"server_default:CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"update_time\", \"field_type\": \"TIMESTAMP\", \"id\": \"row_308\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u4fee\\u6539\\u65f6\\u95f4\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 11, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"customRender\": 1, \"default_value\": 0, \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"del_flag\", \"field_type\": \"SmallInteger\", \"id\": \"row_309\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u8f6f\\u5220\\u9664\\u6807\\u8bb0\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 12, \"table_show\": 0}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": 1, \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"sort_no\", \"field_type\": \"Float\", \"id\": \"row_310\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u6392\\u5e8f\\u5b57\\u6bb5\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 13, \"table_show\": 0}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputTextArea\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"description\", \"field_type\": \"Text\", \"id\": \"row_311\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u7b80\\u4ecb\\u63cf\\u8ff0\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 14, \"table_show\": 1}]', 1, 1, 1, 1, 1, 800, 0);
INSERT INTO `code_gen_model` VALUES ('', 1, 0, 'admin', '2023-02-16 03:39:13', 'admin', '2023-02-16 10:07:21', 'af9d3d6cc4fe4bc7a64e4b74afe5e41f', '数据接口', 'data_interface', '/', '数据接口', 'DataInterface', 1, 'data_interface', '', 1, '[]', '[{\"function\": \"list\", \"id\": \"row_112\", \"is_show\": false, \"name\": \"\\u5217\\u8868\\u67e5\\u8be2\", \"permissions\": \"\", \"slot\": \"hideApi\", \"sortNum\": 3}, {\"function\": \"getAllList\", \"id\": \"row_113\", \"is_show\": false, \"name\": \"\\u5168\\u91cf\\u5217\\u8868\", \"permissions\": \"\", \"slot\": \"hideApi\", \"sortNum\": 4}, {\"function\": \"handleDetail\", \"id\": \"row_114\", \"is_show\": true, \"name\": \"\\u8be6\\u60c5\", \"permissions\": \"\", \"slot\": \"actionDropDown\", \"sortNum\": 5}, {\"function\": \"handleAdd\", \"id\": \"row_115\", \"is_show\": true, \"name\": \"\\u65b0\\u589e\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 6}, {\"function\": \"handleEdit\", \"id\": \"row_116\", \"is_show\": true, \"name\": \"\\u7f16\\u8f91\", \"permissions\": \"\", \"slot\": \"action\", \"sortNum\": 7}, {\"function\": \"handleDelete\", \"id\": \"row_117\", \"is_show\": true, \"name\": \"\\u5220\\u9664\", \"permissions\": \"\", \"slot\": \"actionDropDown\", \"sortNum\": 8}, {\"function\": \"batchHandleDelete\", \"id\": \"row_118\", \"is_show\": true, \"name\": \"\\u6279\\u91cf\\u5220\\u9664\", \"permissions\": \"\", \"slot\": \"overlay\", \"sortNum\": 9}, {\"function\": \"onImportXls\", \"id\": \"row_119\", \"is_show\": true, \"name\": \"\\u5bfc\\u5165\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 10}, {\"function\": \"onExportXls\", \"id\": \"row_120\", \"is_show\": true, \"name\": \"\\u5bfc\\u51fa\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 11}]', '[{\"all_list_show\": 1, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"id\", \"field_type\": \"String\", \"id\": \"row_104\", \"is_json\": 0, \"is_only\": 1, \"label\": \"\\u4e3b\\u952e\", \"length\": 36, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 1, \"sortNum\": 3, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"create_by\", \"field_type\": \"String\", \"id\": \"row_105\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u521b\\u5efa\\u8005\", \"length\": 100, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 4, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"server_default:CURRENT_TIMESTAMP\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"create_time\", \"field_type\": \"TIMESTAMP\", \"id\": \"row_106\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u521b\\u5efa\\u65f6\\u95f4\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 5, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"update_by\", \"field_type\": \"String\", \"id\": \"row_107\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u4fee\\u6539\\u8005\", \"length\": 100, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 6, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"server_default:CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"update_time\", \"field_type\": \"TIMESTAMP\", \"id\": \"row_108\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u4fee\\u6539\\u65f6\\u95f4\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 7, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"customRender\": 1, \"default_value\": 0, \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"del_flag\", \"field_type\": \"SmallInteger\", \"id\": \"row_109\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u8f6f\\u5220\\u9664\\u6807\\u8bb0\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 8, \"table_show\": 0}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": 1, \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"sort_no\", \"field_type\": \"Float\", \"id\": \"row_110\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u6392\\u5e8f\\u5b57\\u6bb5\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 9, \"table_show\": 0}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputTextArea\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"description\", \"field_type\": \"Text\", \"id\": \"row_111\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u7b80\\u4ecb\\u63cf\\u8ff0\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 10, \"table_show\": 1}, {\"all_list_show\": 1, \"clearable\": 0, \"component\": \"ApiSelect\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"datamodel_id\", \"field_type\": \"String\", \"id\": \"row_466\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u6240\\u5c5e\\u6570\\u636e\\u6a21\\u578b\", \"length\": 36, \"list_show\": 1, \"nullable\": 0, \"primary_key\": 0, \"sortNum\": 11, \"table_show\": 1}, {\"all_list_show\": 1, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"name\", \"field_type\": \"String\", \"id\": \"row_467\", \"is_json\": 0, \"is_only\": 1, \"label\": \"\\u63a5\\u53e3\\u540d\\u79f0\", \"length\": 200, \"list_show\": 1, \"nullable\": 0, \"primary_key\": 0, \"sortNum\": 12, \"table_show\": 1}, {\"all_list_show\": 1, \"clearable\": 0, \"component\": \"JSelectInput\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"1\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"type\", \"field_type\": \"SmallInteger\", \"id\": \"row_468\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u7c7b\\u578b\", \"length\": 6, \"list_show\": 1, \"nullable\": 0, \"primary_key\": 0, \"sortNum\": 13, \"table_show\": 1}, {\"label\": \"\\u72b6\\u6001\", \"field\": \"status\", \"component\": \"JSelectInput\", \"componentProps\": \"{}\", \"field_type\": \"SmallInteger\", \"default_value\": \"1\", \"length\": 6, \"primary_key\": 0, \"is_json\": 0, \"is_only\": 0, \"nullable\": 0, \"editable\": 1, \"clearable\": 0, \"table_show\": 1, \"customRender\": 0, \"edit_show\": 1, \"list_show\": 1, \"detail_show\": 1, \"all_list_show\": 1, \"sortNum\": 14}]', 1, 1, 1, 1, 1, 800, 0);
INSERT INTO `code_gen_model` VALUES ('', 1, 0, 'admin', '2023-03-05 17:29:02', '', '2023-03-05 17:29:02', 'bdb2657c7cfa443bb8581ff22399337d', '任务实例', 'task_interface', '/task/instance', '任务实例', 'TaskInterface', 2, 'task_instance', '', 1, '[]', '[{\"name\": \"列表查询\", \"slot\": \"hideApi\", \"function\": \"list\", \"is_show\": false, \"permissions\": \"\", \"id\": \"row_385\", \"sortNum\": 3}, {\"name\": \"全量列表\", \"slot\": \"hideApi\", \"function\": \"getAllList\", \"is_show\": false, \"permissions\": \"\", \"id\": \"row_386\", \"sortNum\": 4}, {\"name\": \"详情\", \"slot\": \"actionDropDown\", \"function\": \"handleDetail\", \"is_show\": true, \"permissions\": \"\", \"id\": \"row_387\", \"sortNum\": 5}, {\"name\": \"新增\", \"slot\": \"tableTitle\", \"function\": \"handleAdd\", \"is_show\": true, \"permissions\": \"\", \"id\": \"row_388\", \"sortNum\": 6}, {\"name\": \"编辑\", \"slot\": \"action\", \"function\": \"handleEdit\", \"is_show\": true, \"permissions\": \"\", \"id\": \"row_389\", \"sortNum\": 7}, {\"name\": \"删除\", \"slot\": \"actionDropDown\", \"function\": \"handleDelete\", \"is_show\": true, \"permissions\": \"\", \"id\": \"row_390\", \"sortNum\": 8}, {\"name\": \"批量删除\", \"slot\": \"overlay\", \"function\": \"batchHandleDelete\", \"is_show\": true, \"permissions\": \"\", \"id\": \"row_391\", \"sortNum\": 9}, {\"name\": \"导入\", \"slot\": \"tableTitle\", \"function\": \"onImportXls\", \"is_show\": false, \"permissions\": \"\", \"id\": \"row_392\", \"sortNum\": 10}, {\"name\": \"导出\", \"slot\": \"tableTitle\", \"function\": \"onExportXls\", \"is_show\": false, \"permissions\": \"\", \"id\": \"row_393\", \"sortNum\": 11}]', '[{\"label\": \"id\", \"field\": \"id\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field_type\": \"String\", \"default_value\": \"\", \"length\": 36, \"nullable\": 1, \"primary_key\": 1, \"is_only\": 1, \"is_json\": 0, \"clearable\": 0, \"editable\": 0, \"customRender\": 0, \"list_show\": 1, \"table_show\": 1, \"edit_show\": 0, \"detail_show\": 1, \"all_list_show\": 1, \"id\": \"row_377\", \"sortNum\": 3}, {\"label\": \"任务id\", \"field\": \"task_id\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field_type\": \"String\", \"default_value\": \"\", \"length\": 36, \"primary_key\": 0, \"is_json\": 0, \"is_only\": 0, \"nullable\": 1, \"editable\": 1, \"clearable\": 0, \"table_show\": 1, \"customRender\": 0, \"edit_show\": 1, \"list_show\": 1, \"detail_show\": 1, \"all_list_show\": 0, \"sortNum\": 4}, {\"label\": \"状态\", \"field\": \"status\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field_type\": \"SmallInteger\", \"default_value\": \"0\", \"length\": 6, \"primary_key\": 0, \"is_json\": 0, \"is_only\": 0, \"nullable\": 1, \"editable\": 1, \"clearable\": 0, \"table_show\": 1, \"customRender\": 0, \"edit_show\": 1, \"list_show\": 1, \"detail_show\": 1, \"all_list_show\": 0, \"sortNum\": 5}, {\"label\": \"任务进度\", \"field\": \"progress\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field_type\": \"Float\", \"default_value\": \"0\", \"length\": 0, \"primary_key\": 0, \"is_json\": 0, \"is_only\": 0, \"nullable\": 1, \"editable\": 1, \"clearable\": 0, \"table_show\": 1, \"customRender\": 0, \"edit_show\": 1, \"list_show\": 1, \"detail_show\": 1, \"all_list_show\": 0, \"sortNum\": 6}, {\"label\": \"开始时间\", \"field\": \"start_time\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field_type\": \"String\", \"default_value\": \"\", \"length\": 100, \"nullable\": 1, \"primary_key\": 0, \"is_only\": 0, \"is_json\": 0, \"clearable\": 0, \"editable\": 0, \"customRender\": 0, \"list_show\": 1, \"table_show\": 1, \"edit_show\": 0, \"detail_show\": 1, \"all_list_show\": 0, \"id\": \"row_378\", \"sortNum\": 7}, {\"label\": \"结束时间\", \"field\": \"end_time\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field_type\": \"TIMESTAMP\", \"default_value\": \"\", \"length\": 0, \"primary_key\": 0, \"is_json\": 0, \"is_only\": 0, \"nullable\": 1, \"editable\": 1, \"clearable\": 0, \"table_show\": 1, \"customRender\": 0, \"edit_show\": 1, \"list_show\": 1, \"detail_show\": 1, \"all_list_show\": 0, \"sortNum\": 8}, {\"label\": \"执行结果\", \"field\": \"result\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field_type\": \"Text\", \"default_value\": \"\", \"length\": 0, \"primary_key\": 0, \"is_json\": 0, \"is_only\": 0, \"nullable\": 1, \"editable\": 1, \"clearable\": 0, \"table_show\": 1, \"customRender\": 0, \"edit_show\": 1, \"list_show\": 1, \"detail_show\": 1, \"all_list_show\": 0, \"sortNum\": 9}]', 1, 1, 1, 1, 1, 800, 0);
INSERT INTO `code_gen_model` VALUES ('', 1, 0, 'admin', '2022-12-19 16:19:38', 'admin', '2022-12-19 16:44:41', 'f9f5506db739408d89664b2e312740f6', '数据模型字段', 'datamodel_field', 'datamodel/field', '数据模型字段', 'DataModelField', 1, 'datamodel_field', '数据模型字段', 1, '[{\"colProps\": \"{}\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field\": \"field_name\", \"id\": \"row_66\", \"label\": \"\\u5b57\\u6bb5\\u540d\", \"sortNum\": 3}, {\"colProps\": \"{}\", \"component\": \"Input\", \"componentProps\": \"{}\", \"field\": \"field_value\", \"id\": \"row_67\", \"label\": \"\\u5b57\\u6bb5\\u503c\", \"sortNum\": 4}]', '[{\"function\": \"list\", \"id\": \"row_68\", \"is_show\": false, \"name\": \"\\u5217\\u8868\\u67e5\\u8be2\", \"permissions\": \"\", \"slot\": \"hideApi\", \"sortNum\": 3}, {\"function\": \"getAllList\", \"id\": \"row_69\", \"is_show\": false, \"name\": \"\\u5168\\u91cf\\u5217\\u8868\", \"permissions\": \"\", \"slot\": \"hideApi\", \"sortNum\": 4}, {\"function\": \"handleDetail\", \"id\": \"row_70\", \"is_show\": true, \"name\": \"\\u8be6\\u60c5\", \"permissions\": \"\", \"slot\": \"actionDropDown\", \"sortNum\": 5}, {\"function\": \"handleAdd\", \"id\": \"row_71\", \"is_show\": true, \"name\": \"\\u65b0\\u589e\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 6}, {\"function\": \"handleEdit\", \"id\": \"row_72\", \"is_show\": true, \"name\": \"\\u7f16\\u8f91\", \"permissions\": \"\", \"slot\": \"action\", \"sortNum\": 7}, {\"function\": \"handleDelete\", \"id\": \"row_73\", \"is_show\": true, \"name\": \"\\u5220\\u9664\", \"permissions\": \"\", \"slot\": \"actionDropDown\", \"sortNum\": 8}, {\"function\": \"batchHandleDelete\", \"id\": \"row_74\", \"is_show\": true, \"name\": \"\\u6279\\u91cf\\u5220\\u9664\", \"permissions\": \"\", \"slot\": \"overlay\", \"sortNum\": 9}, {\"function\": \"onImportXls\", \"id\": \"row_75\", \"is_show\": false, \"name\": \"\\u5bfc\\u5165\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 10}, {\"function\": \"onExportXls\", \"id\": \"row_76\", \"is_show\": false, \"name\": \"\\u5bfc\\u51fa\", \"permissions\": \"\", \"slot\": \"tableTitle\", \"sortNum\": 11}]', '[{\"all_list_show\": 1, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"id\", \"field_type\": \"String\", \"id\": \"row_60\", \"is_json\": 0, \"is_only\": 1, \"label\": \"\\u4e3b\\u952e\", \"length\": 36, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 1, \"sortNum\": 3, \"table_show\": 1}, {\"all_list_show\": 1, \"clearable\": 0, \"component\": \"ApiSelect\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"datamodel_id\", \"field_type\": \"String\", \"id\": \"row_60\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u6240\\u5c5e\\u6570\\u636e\\u6a21\\u578b\", \"length\": 36, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 4, \"table_show\": 1}, {\"all_list_show\": 1, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"field_name\", \"field_type\": \"String\", \"id\": \"row_61\", \"is_json\": 0, \"is_only\": 1, \"label\": \"\\u5b57\\u6bb5\\u540d\", \"length\": 200, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 5, \"table_show\": 1}, {\"all_list_show\": 1, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"field_value\", \"field_type\": \"String\", \"id\": \"row_62\", \"is_json\": 0, \"is_only\": 1, \"label\": \"\\u5b57\\u6bb5\\u503c\", \"length\": 200, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 6, \"table_show\": 1}, {\"all_list_show\": 1, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"field_type\", \"field_type\": \"String\", \"id\": \"row_63\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u5b57\\u6bb5\\u7c7b\\u578b\", \"length\": 100, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 7, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputTextArea\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"{}\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"ext_params\", \"field_type\": \"Text\", \"id\": \"row_64\", \"is_json\": 1, \"is_only\": 0, \"label\": \"\\u62d3\\u5c55\\u5b57\\u6bb5\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 8, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"JSelectInput\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"0\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"is_sync\", \"field_type\": \"SmallInteger\", \"id\": \"row_65\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u662f\\u5426\\u540c\\u6b65\", \"length\": 6, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 9, \"table_show\": 1}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"create_by\", \"field_type\": \"String\", \"id\": \"row_61\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u521b\\u5efa\\u8005\", \"length\": 100, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 10, \"table_show\": 0}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"server_default:CURRENT_TIMESTAMP\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"create_time\", \"field_type\": \"TIMESTAMP\", \"id\": \"row_62\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u521b\\u5efa\\u65f6\\u95f4\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 11, \"table_show\": 0}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"update_by\", \"field_type\": \"String\", \"id\": \"row_63\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u4fee\\u6539\\u8005\", \"length\": 100, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 12, \"table_show\": 0}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"Input\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"server_default:CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP\", \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"update_time\", \"field_type\": \"TIMESTAMP\", \"id\": \"row_64\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u4fee\\u6539\\u65f6\\u95f4\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 13, \"table_show\": 0}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"customRender\": 1, \"default_value\": 0, \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"del_flag\", \"field_type\": \"SmallInteger\", \"id\": \"row_65\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u8f6f\\u5220\\u9664\\u6807\\u8bb0\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 14, \"table_show\": 0}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputNumber\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": 1, \"detail_show\": 1, \"edit_show\": 0, \"editable\": 0, \"field\": \"sort_no\", \"field_type\": \"Float\", \"id\": \"row_66\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u6392\\u5e8f\\u5b57\\u6bb5\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 15, \"table_show\": 0}, {\"all_list_show\": 0, \"clearable\": 0, \"component\": \"InputTextArea\", \"componentProps\": \"{}\", \"customRender\": 0, \"default_value\": \"\", \"detail_show\": 1, \"edit_show\": 1, \"editable\": 1, \"field\": \"description\", \"field_type\": \"Text\", \"id\": \"row_67\", \"is_json\": 0, \"is_only\": 0, \"label\": \"\\u7b80\\u4ecb\\u63cf\\u8ff0\", \"length\": 0, \"list_show\": 1, \"nullable\": 1, \"primary_key\": 0, \"sortNum\": 16, \"table_show\": 1}]', 1, 1, 1, 1, 1, 800, 0);
COMMIT;

-- ----------------------------
-- Table structure for data_interface
-- ----------------------------
DROP TABLE IF EXISTS `data_interface`;
CREATE TABLE `data_interface` (
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '简介',
  `sort_no` float DEFAULT NULL COMMENT '排序',
  `del_flag` smallint DEFAULT NULL COMMENT '软删除标记',
  `create_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建者',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '修改者',
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `datamodel_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '所属数据模型id',
  `name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '接口名称',
  `api_key` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'api_key',
  `valid_fields` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '允许访问字段',
  `apply_user_id` int DEFAULT NULL COMMENT '申请人id',
  `apply_user` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '申请人',
  `apply_caption` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '申请说明',
  `apply_time` bigint DEFAULT NULL COMMENT '申请时间',
  `apply_time_length` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '申请时长',
  `review_user_id` int DEFAULT NULL COMMENT '审核人id',
  `review_user` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '审核人',
  `review_caption` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '审核说明',
  `review_time` bigint DEFAULT NULL COMMENT '审核时间',
  `review_time_length` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '授权时长',
  `status` smallint NOT NULL COMMENT '状态0禁用1启用',
  `valid_time` bigint DEFAULT NULL COMMENT '有效期限',
  PRIMARY KEY (`id`),
  KEY `ix_data_interface_api_key` (`api_key`),
  KEY `ix_data_interface_datamodel_id` (`datamodel_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Records of data_interface
-- ----------------------------
BEGIN;
COMMIT;

-- ----------------------------
-- Table structure for datamodel
-- ----------------------------
DROP TABLE IF EXISTS `datamodel`;
CREATE TABLE `datamodel` (
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '简介',
  `sort_no` float DEFAULT NULL COMMENT '排序',
  `del_flag` smallint DEFAULT NULL COMMENT '软删除标记',
  `create_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建者',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '修改者',
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '名称',
  `datasource_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '数据源id',
  `type` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '类型',
  `status` smallint DEFAULT NULL COMMENT '模型状态 0未建立，1已建立',
  `model_conf` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '模型配置',
  `ext_params` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '额外参数',
  `can_interface` smallint DEFAULT NULL COMMENT '是否可封装查询接口',
  `depart_list` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '关联部门列表',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Records of datamodel
-- ----------------------------
BEGIN;
INSERT INTO `datamodel` VALUES ('', 1, 0, 'admin', '2023-08-10 07:53:46', 'admin', '2023-09-15 17:48:53', '77b5008db89348348360893720a01b80', '任务实例表binlog流', 'fdf0938c7d5a44eca94ba093cc8be6c8', 'mysql_binlog', 1, '{\n  \"listen_dbs\": \"ezdata\",\n  \"listen_tables\": \"task_instance\",\n  \"auth_type\": \"extract\",\n  \"only_events\": \"write,update\"\n}', '{}', 0, '[]');
INSERT INTO `datamodel` VALUES ('', 1, 0, 'admin', '2024-06-22 16:12:31', '', '2024-06-22 16:12:31', '8a862fdf980245459ac9ef89734c166f', 'sql示例', 'fdf0938c7d5a44eca94ba093cc8be6c8', 'sql', 1, '{\n  \"name\": \"\",\n  \"sql\": \"select * from sys_dict\",\n  \"auth_type\": \"query,custom_sql,extract\"\n}', '{}', 1, '[]');
INSERT INTO `datamodel` VALUES ('', 1, 0, 'admin', '2023-10-24 06:52:59', 'admin', '2024-06-22 16:12:36', 'a7f25e1805a44ea5a546158da95ad726', '任务执行历史索引', '10a0f8f11faa41968f5e75ee5afce4e7', 'elasticsearch_index', 1, '{\n  \"name\": \"task_instance_history\",\n  \"auth_type\": \"query,create,edit_fields,delete,extract,load\"\n}', '{}', 1, '[]');
INSERT INTO `datamodel` VALUES ('', 1, 0, 'admin', '2023-10-22 07:09:49', 'admin', '2023-10-24 06:46:46', 'd88b859297224ebcba7fe21efe118ebb', '股票历史数据接口', 'c4eccdd3fd294ac6b9d663519df485bb', 'akshare_api', 1, '{\n  \"auth_type\": \"query,extract\",\n  \"method\": \"stock_zh_a_hist\"\n}', '{}', 1, '[]');
INSERT INTO `datamodel` VALUES ('', 10, 0, 'admin', '2023-10-24 06:23:11', 'admin', '2023-12-23 16:47:15', 'e222b61c62be4d09908a5bc94aebf22d', 'excel文件', 'd018f252ef6740e89e387d32de4c412f', 'file_table', 1, '{\n  \"auth_type\": \"query,extract\"\n}', '{}', 1, '[]');
INSERT INTO `datamodel` VALUES ('', 1, 0, 'admin', '2023-10-24 06:50:19', 'admin', '2024-06-22 16:12:41', 'f4f58112235f4625a72f880a373ff697', '股票历史数据索引', '10a0f8f11faa41968f5e75ee5afce4e7', 'elasticsearch_index', 1, '{\n  \"name\": \"stock_history\",\n  \"auth_type\": \"query,create,edit_fields,delete,extract,load\"\n}', '{}', 1, '[]');
COMMIT;

-- ----------------------------
-- Table structure for datamodel_field
-- ----------------------------
DROP TABLE IF EXISTS `datamodel_field`;
CREATE TABLE `datamodel_field` (
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '简介',
  `sort_no` float DEFAULT NULL COMMENT '排序',
  `del_flag` smallint DEFAULT NULL COMMENT '软删除标记',
  `create_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建者',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '修改者',
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `datamodel_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属数据模型',
  `field_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '字段名',
  `field_value` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '字段值',
  `field_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '字段类型',
  `ext_params` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '拓展字段',
  `is_sync` smallint DEFAULT NULL COMMENT '是否同步',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Records of datamodel_field
-- ----------------------------
BEGIN;
INSERT INTO `datamodel_field` VALUES ('', 1, 0, 'admin', '2023-10-24 07:07:51', '', '2023-10-24 07:07:51', '15494f1caa564bfc85c36bd82c9b7bdb', 'a7f25e1805a44ea5a546158da95ad726', 'parent_id', 'parent_id', NULL, '{\"type\": \"text\", \"length\": 0, \"is_primary_key\": 0, \"nullable\": 1, \"default\": \"\"}', 1);
INSERT INTO `datamodel_field` VALUES ('', 1, 0, 'admin', '2023-10-24 07:07:51', '', '2023-10-24 07:07:51', '1aca0a34c41747839d3030dae8e5c28d', 'a7f25e1805a44ea5a546158da95ad726', 'result', 'result', NULL, '{\"type\": \"text\", \"length\": 0, \"is_primary_key\": 0, \"nullable\": 1, \"default\": \"\"}', 1);
INSERT INTO `datamodel_field` VALUES ('', 1, 0, 'admin', '2023-10-24 07:07:46', '', '2023-10-24 07:07:46', '1c48ece65ea04fbca96fa96aa30a1ec7', 'f4f58112235f4625a72f880a373ff697', 'time', 'time', NULL, '{\"type\": \"date\", \"length\": 0, \"is_primary_key\": 0, \"nullable\": 1, \"default\": \"\"}', 1);
INSERT INTO `datamodel_field` VALUES ('', 1, 0, 'admin', '2023-10-24 07:07:46', '', '2023-10-24 07:07:46', '1e329877f2254bf484f0327c21264564', 'f4f58112235f4625a72f880a373ff697', 'high', 'high', NULL, '{\"type\": \"float\", \"length\": 0, \"is_primary_key\": 0, \"nullable\": 1, \"default\": \"\"}', 1);
INSERT INTO `datamodel_field` VALUES ('', 1, 0, 'admin', '2023-10-24 07:07:51', '', '2023-10-24 07:07:51', '3101f3704c3b477399d60b38555f102f', 'a7f25e1805a44ea5a546158da95ad726', 'task_id', 'task_id', NULL, '{\"type\": \"text\", \"length\": 0, \"is_primary_key\": 0, \"nullable\": 1, \"default\": \"\"}', 1);
INSERT INTO `datamodel_field` VALUES ('', 1, 0, 'admin', '2023-10-24 07:07:51', '', '2023-10-24 07:07:51', '441f38cac0b2413095d08966984577bb', 'a7f25e1805a44ea5a546158da95ad726', 'start_time', 'start_time', NULL, '{\"type\": \"date\", \"length\": 0, \"is_primary_key\": 0, \"nullable\": 1, \"default\": \"\"}', 1);
INSERT INTO `datamodel_field` VALUES ('', 1, 0, 'admin', '2023-10-24 07:07:46', '', '2023-10-24 07:07:46', '4f63bdc64f1c49338178d95f47097bf7', 'f4f58112235f4625a72f880a373ff697', 'volume', 'volume', NULL, '{\"type\": \"float\", \"length\": 0, \"is_primary_key\": 0, \"nullable\": 1, \"default\": \"\"}', 1);
INSERT INTO `datamodel_field` VALUES ('', 1, 0, 'admin', '2023-10-24 07:07:46', '', '2023-10-24 07:07:46', '5e3b3e0907944881a51645d9c56f6eeb', 'f4f58112235f4625a72f880a373ff697', 'open', 'open', NULL, '{\"type\": \"float\", \"length\": 0, \"is_primary_key\": 0, \"nullable\": 1, \"default\": \"\"}', 1);
INSERT INTO `datamodel_field` VALUES ('', 1, 0, 'admin', '2023-10-24 07:07:46', '', '2023-10-24 07:07:46', '6f21a29b62dc4f2ab277678d96387158', 'f4f58112235f4625a72f880a373ff697', 'low', 'low', NULL, '{\"type\": \"float\", \"length\": 0, \"is_primary_key\": 0, \"nullable\": 1, \"default\": \"\"}', 1);
INSERT INTO `datamodel_field` VALUES ('', 1, 0, 'admin', '2023-10-24 07:07:51', '', '2023-10-24 07:07:51', '802f54fa7071498ba3e0d1ca2d71c17e', 'a7f25e1805a44ea5a546158da95ad726', 'end_time', 'end_time', NULL, '{\"type\": \"date\", \"length\": 0, \"is_primary_key\": 0, \"nullable\": 1, \"default\": \"\"}', 1);
INSERT INTO `datamodel_field` VALUES ('', 1, 0, 'admin', '2023-10-24 07:07:51', '', '2023-10-24 07:07:51', '8868017cef614b76924ed4b54a6bcc8b', 'a7f25e1805a44ea5a546158da95ad726', 'progress', 'progress', NULL, '{\"type\": \"float\", \"length\": 0, \"is_primary_key\": 0, \"nullable\": 1, \"default\": \"\"}', 1);
INSERT INTO `datamodel_field` VALUES ('', 1, 0, 'admin', '2023-10-24 07:07:51', '', '2023-10-24 07:07:51', '895f2877e9744f2eb1711da3d7d137ae', 'a7f25e1805a44ea5a546158da95ad726', 'retry_num', 'retry_num', NULL, '{\"type\": \"long\", \"length\": 0, \"is_primary_key\": 0, \"nullable\": 1, \"default\": \"\"}', 1);
INSERT INTO `datamodel_field` VALUES ('', 1, 0, 'admin', '2023-10-24 07:07:46', '', '2023-10-24 07:07:46', '9e6fb46f86cd48568b552249a08bf2ff', 'f4f58112235f4625a72f880a373ff697', 'close', 'close', NULL, '{\"type\": \"float\", \"length\": 0, \"is_primary_key\": 0, \"nullable\": 1, \"default\": \"\"}', 1);
INSERT INTO `datamodel_field` VALUES ('', 1, 0, 'admin', '2023-10-24 07:07:46', '', '2023-10-24 07:07:46', 'bbe0914ab4e64ca48760de08f4e486de', 'f4f58112235f4625a72f880a373ff697', 'symbol', 'symbol', NULL, '{\"type\": \"text\", \"length\": 0, \"is_primary_key\": 0, \"nullable\": 1, \"default\": \"\"}', 1);
INSERT INTO `datamodel_field` VALUES ('', 1, 0, 'admin', '2023-10-24 07:07:51', '', '2023-10-24 07:07:51', 'd8133e73cc3840d99200adde618677dc', 'a7f25e1805a44ea5a546158da95ad726', 'node_id', 'node_id', NULL, '{\"type\": \"text\", \"length\": 0, \"is_primary_key\": 0, \"nullable\": 1, \"default\": \"\"}', 1);
INSERT INTO `datamodel_field` VALUES ('', 1, 0, 'admin', '2023-10-24 07:07:51', '', '2023-10-24 07:07:51', 'ddbc1713da704fb980e3bd8d32927b30', 'a7f25e1805a44ea5a546158da95ad726', 'worker', 'worker', NULL, '{\"type\": \"text\", \"length\": 0, \"is_primary_key\": 0, \"nullable\": 1, \"default\": \"\"}', 1);
INSERT INTO `datamodel_field` VALUES ('', 1, 0, 'admin', '2023-10-24 07:07:51', '', '2023-10-24 07:07:51', 'de573ae26cd24e13b850f5953330b18b', 'a7f25e1805a44ea5a546158da95ad726', 'closed', 'closed', NULL, '{\"type\": \"long\", \"length\": 0, \"is_primary_key\": 0, \"nullable\": 1, \"default\": \"\"}', 1);
INSERT INTO `datamodel_field` VALUES ('', 1, 0, 'admin', '2023-10-24 07:07:51', '', '2023-10-24 07:07:51', 'ee6bf0ac932146c6ace7d0be2e17c27d', 'a7f25e1805a44ea5a546158da95ad726', 'status', 'status', NULL, '{\"type\": \"text\", \"length\": 0, \"is_primary_key\": 0, \"nullable\": 1, \"default\": \"\"}', 1);
COMMIT;

-- ----------------------------
-- Table structure for datasource
-- ----------------------------
DROP TABLE IF EXISTS `datasource`;
CREATE TABLE `datasource` (
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '简介',
  `sort_no` float DEFAULT NULL COMMENT '排序',
  `del_flag` smallint DEFAULT NULL COMMENT '软删除标记',
  `create_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建者',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '修改者',
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'ID',
  `name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '名称',
  `type` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '类型',
  `conn_conf` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '连接配置',
  `status` int DEFAULT NULL COMMENT '状态',
  `ext_params` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '额外参数',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Records of datasource
-- ----------------------------
BEGIN;
INSERT INTO `datasource` VALUES ('', 1, 0, 'admin', '2023-09-13 05:33:32', 'admin', '2023-10-24 07:11:36', '0106d78d22a74df59c6f6b44f2caa843', '系统minio', 'minio', '{\n  \"username\": \"minio\",\n  \"password\": \"ezdata123\",\n  \"bucket\": \"ezdata\",\n  \"url\": \"10.233.31.5:9000\"\n}', 1, '{}');
INSERT INTO `datasource` VALUES ('', 1, 0, 'admin', '2023-09-16 07:12:38', 'admin', '2023-10-24 07:11:22', '10a0f8f11faa41968f5e75ee5afce4e7', '系统es', 'elasticsearch', '{\n  \"auth_type\": 1,\n  \"url\": \"10.233.31.6:9200\"\n}', 1, '{}');
INSERT INTO `datasource` VALUES ('', 1, 0, 'admin', '2023-10-22 06:38:51', 'admin', '2023-10-24 05:55:51', 'c4eccdd3fd294ac6b9d663519df485bb', 'akshare数据接口', 'akshare', '{}', 1, '{}');
INSERT INTO `datasource` VALUES ('', 10, 0, 'admin', '2023-08-10 07:31:27', 'admin', '2023-12-23 16:47:28', 'd018f252ef6740e89e387d32de4c412f', 'excel文件示例', 'file', '{\n  \"path\": \"examples/demo.xlsx\"\n}', 1, '{}');
INSERT INTO `datasource` VALUES ('', 1, 0, 'admin', '2023-08-10 07:38:11', 'admin', '2023-10-24 07:11:51', 'fdf0938c7d5a44eca94ba093cc8be6c8', '系统mysql', 'mysql', '{\n  \"host\": \"10.233.31.3\",\n  \"port\": 3306,\n  \"username\": \"root\",\n  \"password\": \"ezdata123\",\n  \"database_name\": \"ezdata\"\n}', 1, '{}');
COMMIT;

-- ----------------------------
-- Table structure for llm_chat_history
-- ----------------------------
DROP TABLE IF EXISTS `llm_chat_history`;
CREATE TABLE `llm_chat_history` (
  `description` text COLLATE utf8mb4_general_ci COMMENT '简介',
  `sort_no` float DEFAULT NULL COMMENT '排序',
  `del_flag` smallint DEFAULT NULL COMMENT '软删除标记',
  `create_by` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建者',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '修改者',
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `id` varchar(36) COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `user_id` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '用户id',
  `user_name` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '用户名',
  `content` text COLLATE utf8mb4_general_ci COMMENT '内容',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Records of llm_chat_history
-- ----------------------------
BEGIN;
COMMIT;

-- ----------------------------
-- Table structure for screen_project
-- ----------------------------
DROP TABLE IF EXISTS `screen_project`;
CREATE TABLE `screen_project` (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'id主键',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '简介',
  `sort_no` float DEFAULT NULL COMMENT '排序',
  `del_flag` smallint DEFAULT NULL COMMENT '软删除标记',
  `create_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建者',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '修改者',
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `project_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '项目名称',
  `index_image` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '首页图片',
  `remarks` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '项目介绍',
  `state` smallint DEFAULT NULL COMMENT '项目状态[-1未发布,1发布]',
  `content` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '项目介绍',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Records of screen_project
-- ----------------------------
BEGIN;
COMMIT;

-- ----------------------------
-- Table structure for sys_depart
-- ----------------------------
DROP TABLE IF EXISTS `sys_depart`;
CREATE TABLE `sys_depart` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'id主键',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '简介',
  `sort_no` float DEFAULT NULL COMMENT '排序',
  `del_flag` smallint DEFAULT NULL COMMENT '软删除标记',
  `create_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建者',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '修改者',
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `depart_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '机构/部门名称',
  `parent_id` int DEFAULT NULL COMMENT '父级ID',
  `depart_name_en` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '英文名',
  `depart_name_abbr` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '缩写',
  `org_category` smallint DEFAULT NULL COMMENT '机构类别 1公司，2组织机构，2岗位',
  `org_type` smallint DEFAULT NULL COMMENT '机构类型 1一级部门 2子部门',
  `org_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '机构编码',
  `mobile` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '手机号',
  `fax` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '传真',
  `address` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '地址',
  `memo` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  `status` smallint DEFAULT NULL COMMENT '状态（1启用，0不启用）',
  `qywx_identifier` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '对接企业微信的ID',
  `permissions` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '权限列表',
  `is_leaf` smallint DEFAULT NULL COMMENT '是否叶子节点: 1:是   0:不是',
  PRIMARY KEY (`id`),
  KEY `ix_sys_depart_depart_name` (`depart_name`),
  KEY `ix_sys_depart_depart_name_en` (`depart_name_en`),
  KEY `ix_sys_depart_depart_name_abbr` (`depart_name_abbr`),
  KEY `ix_sys_depart_org_code` (`org_code`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Records of sys_depart
-- ----------------------------
BEGIN;
INSERT INTO `sys_depart` VALUES (1, '', 1, 0, 'admin', '2022-11-06 17:01:20', 'admin', '2023-04-27 14:12:36', '默认机构', NULL, NULL, NULL, 1, 1, 'org_1', '18815593959', '1', '134234', '1', 1, NULL, '[\"42\", \"44\"]', 0);
INSERT INTO `sys_depart` VALUES (5, '', 3, 0, 'admin', '2022-11-12 14:19:08', 'admin', '2023-04-27 17:36:38', '管理员组', 1, NULL, NULL, 2, 1, 'org_5', NULL, NULL, NULL, NULL, 1, NULL, '[\"1\", \"3\", \"2\", \"25\", \"26\", \"98\", \"97\", \"96\", \"27\", \"102\", \"101\", \"100\", \"99\", \"37\", \"106\", \"105\", \"104\", \"103\", \"28\", \"110\", \"109\", \"108\", \"107\", \"31\", \"32\", \"83\", \"82\", \"81\", \"80\", \"33\", \"91\", \"87\", \"86\", \"85\", \"84\", \"35\", \"89\", \"88\", \"34\", \"95\", \"94\", \"93\", \"92\", \"90\", \"20\", \"21\", \"38\", \"41\", \"40\", \"78\", \"39\", \"79\", \"23\", \"24\", \"77\", \"76\", \"75\", \"74\", \"4\", \"18\", \"5\", \"73\", \"72\", \"71\", \"7\", \"6\", \"10\", \"70\", \"69\", \"68\", \"11\", \"67\", \"66\", \"65\", \"12\", \"64\", \"63\", \"62\", \"61\", \"13\", \"22\", \"19\", \"59\", \"58\", \"57\", \"14\", \"56\", \"55\", \"54\", \"15\", \"53\", \"52\", \"16\", \"49\", \"48\", \"47\", \"46\", \"45\", \"44\", \"43\", \"42\", \"17\", \"51\", \"50\"]', 1);
INSERT INTO `sys_depart` VALUES (6, '', 0, 0, 'admin', '2022-11-13 03:53:18', '', '2022-11-19 19:18:05', '普通用户组', 1, NULL, NULL, 2, 1, 'org_6', NULL, NULL, NULL, NULL, 1, NULL, '[\"1\", \"3\", \"2\", \"4\", \"18\", \"16\", \"17\", \"13\", \"20\", \"21\"]', 1);
INSERT INTO `sys_depart` VALUES (7, '', 0, 0, 'admin', '2023-04-27 17:40:57', 'admin', '2023-04-27 17:41:07', '开发组', 1, NULL, NULL, 2, 1, 'org_7', NULL, NULL, NULL, NULL, 1, NULL, '[]', 1);
COMMIT;

-- ----------------------------
-- Table structure for sys_dict
-- ----------------------------
DROP TABLE IF EXISTS `sys_dict`;
CREATE TABLE `sys_dict` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'id主键',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '简介',
  `sort_no` float DEFAULT NULL COMMENT '排序',
  `del_flag` smallint DEFAULT NULL COMMENT '软删除标记',
  `create_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建者',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '修改者',
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `dict_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '字典名称',
  `dict_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '字典编码',
  `type` smallint DEFAULT NULL COMMENT '字典值类型，0为string,1为number',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Records of sys_dict
-- ----------------------------
BEGIN;
INSERT INTO `sys_dict` VALUES (2, '', 1, 0, 'admin', '2022-11-02 07:57:21', 'admin', '2022-11-02 08:36:44', '性别', 'sex', 1);
INSERT INTO `sys_dict` VALUES (3, '', 1, 0, 'admin', '2022-11-02 08:35:23', 'admin', '2023-07-11 03:30:36', '字典项状态', 'dict_item_status', 1);
INSERT INTO `sys_dict` VALUES (4, '', 1, 0, 'admin', '2022-11-09 05:39:40', '', '2022-11-09 05:39:40', '职务职级', 'position_rank', 1);
INSERT INTO `sys_dict` VALUES (5, '', 1, 0, 'admin', '2022-11-09 09:47:18', '', '2022-11-09 09:47:18', '用户状态', 'user_status', 1);
INSERT INTO `sys_dict` VALUES (6, '', 1, 0, 'admin', '2022-11-09 14:24:13', '', '2022-11-09 14:24:13', '有效无效状态', 'valid_status', 1);
INSERT INTO `sys_dict` VALUES (7, '消息类型1:通知公告2:系统消息', 1, 0, 'admin', '2022-11-14 16:23:46', 'admin', '2022-11-14 16:27:36', '通告类型', 'msg_category', 1);
INSERT INTO `sys_dict` VALUES (8, '优先级', 1, 0, 'admin', '2022-11-14 16:28:19', '', '2022-11-14 16:28:19', '优先级', 'priority', 1);
INSERT INTO `sys_dict` VALUES (9, '发布状态', 1, 0, 'admin', '2022-11-14 16:29:36', 'admin', '2022-11-14 16:29:45', '发布状态', 'send_status', 1);
INSERT INTO `sys_dict` VALUES (10, '', 1, 0, 'admin', '2022-11-14 16:32:09', '', '2022-11-14 16:32:09', '推送类别', 'msg_type', 1);
INSERT INTO `sys_dict` VALUES (11, '', 1, 0, 'admin', '2022-11-24 13:09:32', '', '2022-11-24 13:09:32', '代码生成同步状态', 'code_gen_sync_status', 1);
INSERT INTO `sys_dict` VALUES (12, '', 1, 0, 'admin', '2022-11-24 13:14:02', '', '2022-11-24 13:14:02', '代码生成模型类型', 'code_gen_model_type', 1);
INSERT INTO `sys_dict` VALUES (13, '', 1, 0, 'admin', '2022-11-24 16:57:00', '', '2022-11-24 16:57:00', '代码生成前端类型', 'code_gen_frontend_type', 1);
INSERT INTO `sys_dict` VALUES (14, '', 1, 0, 'admin', '2022-11-24 16:58:52', '', '2022-11-24 16:58:52', '代码生成后端类型', 'code_gen_backend_type', 1);
INSERT INTO `sys_dict` VALUES (15, '', 1, 0, 'admin', '2022-11-29 17:00:48', 'admin', '2022-12-01 16:52:46', 'JVxeTable组件类型', 'jvex_component_types', 1);
INSERT INTO `sys_dict` VALUES (16, '', 1, 0, 'admin', '2022-11-30 17:14:46', '', '2022-11-30 17:14:46', '字段类型', 'field_types', 1);
INSERT INTO `sys_dict` VALUES (17, '', 1, 0, 'admin', '2022-12-17 16:22:10', '', '2022-12-17 16:22:10', '数据源类型', 'datasource_type', 1);
INSERT INTO `sys_dict` VALUES (18, '', 1, 0, 'admin', '2022-12-19 15:46:31', '', '2022-12-19 15:46:31', '数据模型类型', 'datamodel_type', 1);
INSERT INTO `sys_dict` VALUES (19, '', 1, 0, 'admin', '2023-03-07 17:19:44', '', '2023-03-07 17:19:44', '任务模版类型', 'task_template_type', 1);
INSERT INTO `sys_dict` VALUES (20, '', 1, 0, 'admin', '2023-03-07 17:21:33', 'admin', '2023-03-07 17:21:40', '任务组件', 'task_components', 1);
INSERT INTO `sys_dict` VALUES (21, '', 1, 0, 'admin', '2023-03-16 03:53:29', '', '2023-03-16 03:53:29', 'celery任务队列', 'celery_queue', 1);
INSERT INTO `sys_dict` VALUES (22, '', 1, 0, 'admin', '2023-04-03 13:48:42', '', '2023-04-03 13:48:42', '算法类型', 'alg_type', 1);
INSERT INTO `sys_dict` VALUES (23, '', 1, 0, 'admin', '2023-04-03 13:53:15', '', '2023-04-03 13:53:15', '算法表单类型', 'alg_form_type', 1);
INSERT INTO `sys_dict` VALUES (24, '', 1, 0, 'admin', '2023-04-03 13:54:15', '', '2023-04-03 13:54:15', '算法组件', 'alg_component', 1);
INSERT INTO `sys_dict` VALUES (29, '', 1, 0, 'admin', '2023-06-19 16:58:30', '', '2023-06-19 16:58:30', '告警策略模版', 'alert_strategy_template', 1);
INSERT INTO `sys_dict` VALUES (30, '', 1, 0, 'admin', '2023-06-20 06:10:39', '', '2023-06-20 06:10:39', '告警等级', 'alert_level', 1);
INSERT INTO `sys_dict` VALUES (31, '', 1, 0, 'admin', '2023-06-20 07:02:29', '', '2023-06-20 07:02:29', '告警状态', 'alert_status', 1);
INSERT INTO `sys_dict` VALUES (32, '', 1, 0, 'admin', '2023-10-22 06:39:57', '', '2023-10-22 06:39:57', 'akshare数据接口函数', 'akshare_method', 1);
COMMIT;

-- ----------------------------
-- Table structure for sys_dict_item
-- ----------------------------
DROP TABLE IF EXISTS `sys_dict_item`;
CREATE TABLE `sys_dict_item` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'id主键',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '简介',
  `sort_no` float DEFAULT NULL COMMENT '排序',
  `del_flag` smallint DEFAULT NULL COMMENT '软删除标记',
  `create_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建者',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '修改者',
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `dict_id` int DEFAULT NULL COMMENT '所属字典id',
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '字典项文本',
  `value` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '字典项值',
  `extend` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '额外参数',
  `status` smallint DEFAULT NULL COMMENT '状态（1启用 0禁用）',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=998 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Records of sys_dict_item
-- ----------------------------
BEGIN;
INSERT INTO `sys_dict_item` VALUES (2, '', 1, 0, 'admin', '2022-11-02 07:57:48', 'admin', '2022-11-02 08:40:36', 2, '男', '1', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (3, '', 1, 0, 'admin', '2022-11-02 07:57:55', 'admin', '2022-11-02 08:45:41', 2, '女', '2', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (4, '', 1, 0, 'admin', '2022-11-02 08:35:49', '', '2022-11-02 08:35:49', 3, '启用', '1', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (5, '', 1, 0, 'admin', '2022-11-02 08:35:59', 'admin', '2022-11-02 08:43:33', 3, '不启用', '0', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (6, '', 1, 0, 'admin', '2022-11-09 05:39:58', '', '2022-11-09 05:39:58', 4, '员级', '1', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (7, '', 1, 0, 'admin', '2022-11-09 05:40:09', '', '2022-11-09 05:40:09', 4, '中级', '3', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (8, '', 1, 0, 'admin', '2022-11-09 05:40:19', '', '2022-11-09 05:40:19', 4, '助级', '2', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (9, '', 1, 0, 'admin', '2022-11-09 05:40:31', '', '2022-11-09 05:40:31', 4, '高级', '4', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (10, '', 2, 0, 'admin', '2022-11-09 09:47:48', 'admin', '2022-11-09 09:48:53', 5, '正常', '1', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (11, '', 1, 0, 'admin', '2022-11-09 09:48:07', '', '2022-11-09 09:48:07', 5, '冻结', '2', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (12, '', 3, 0, 'admin', '2022-11-09 09:48:26', 'admin', '2022-11-09 09:49:01', 5, '禁用', '0', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (13, '', 1, 0, 'admin', '2022-11-09 14:24:26', '', '2022-11-09 14:24:26', 6, '有效', '1', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (14, '', 1, 0, 'admin', '2022-11-09 14:24:40', '', '2022-11-09 14:24:40', 6, '无效', '0', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (15, '', 1, 0, 'admin', '2022-11-14 16:24:10', '', '2022-11-14 16:24:10', 7, '通知公告', '1', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (16, '', 1, 0, 'admin', '2022-11-14 16:24:25', '', '2022-11-14 16:24:25', 7, '系统消息', '2', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (17, '', 1, 0, 'admin', '2022-11-14 16:28:39', '', '2022-11-14 16:28:39', 8, '高', 'H', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (18, '', 1, 0, 'admin', '2022-11-14 16:28:52', '', '2022-11-14 16:28:52', 8, '中', 'M', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (19, '', 1, 0, 'admin', '2022-11-14 16:29:03', '', '2022-11-14 16:29:03', 8, '低', 'L', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (20, '', 1, 0, 'admin', '2022-11-14 16:29:59', '', '2022-11-14 16:29:59', 9, '未发布', '0', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (21, '', 1, 0, 'admin', '2022-11-14 16:30:09', '', '2022-11-14 16:30:09', 9, '已发布', '1', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (22, '', 1, 0, 'admin', '2022-11-14 16:30:19', '', '2022-11-14 16:30:19', 9, '已撤销', '2', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (23, '', 1, 0, 'admin', '2022-11-14 16:32:26', 'admin', '2022-11-21 15:07:24', 10, '指定用户', 'USER', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (24, '', 1, 0, 'admin', '2022-11-14 16:32:39', 'admin', '2022-11-23 08:31:11', 10, '全体用户', 'ALL', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (25, '', 1, 0, 'admin', '2022-11-24 13:10:06', '', '2022-11-24 13:10:06', 11, '已同步', '1', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (26, '', 1, 0, 'admin', '2022-11-24 13:10:25', 'admin', '2022-11-24 13:10:32', 11, '未同步', '0', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (27, '', 1, 0, 'admin', '2022-11-24 13:14:18', '', '2022-11-24 13:14:18', 12, '单表模型', '1', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (28, '', 1, 0, 'admin', '2022-11-24 16:57:16', 'admin', '2022-11-24 16:58:16', 13, 'vue3-antd模版', '1', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (29, '', 1, 0, 'admin', '2022-11-24 16:57:29', 'admin', '2022-12-11 10:23:22', 13, 'vue3-antd原生', '2', '{}', 0);
INSERT INTO `sys_dict_item` VALUES (30, '', 1, 0, 'admin', '2022-11-24 16:57:45', 'admin', '2022-12-11 10:23:28', 13, 'vue2', '3', '{}', 0);
INSERT INTO `sys_dict_item` VALUES (31, '', 1, 0, 'admin', '2022-11-24 16:59:16', '', '2022-11-24 16:59:16', 14, 'flaREDACTEDsqlalchemy模版', '1', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (32, '', 100, 0, 'admin', '2022-11-29 17:02:13', 'admin', '2022-11-29 17:07:04', 15, '输入框', 'Input', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (33, '', 1, 0, 'admin', '2022-11-29 17:03:13', 'admin', '2022-11-29 17:04:38', 15, '字典选择器', 'JDictSelectTag', '{\"dictCode\": \"\", \"placeholder\": \"请选择\", \"stringToNumber\": true}', 1);
INSERT INTO `sys_dict_item` VALUES (34, '', 98, 0, 'admin', '2022-11-29 17:05:43', 'admin', '2022-11-29 17:07:24', 15, '下拉栏', 'JSelectInput', '{\"options\": []}', 1);
INSERT INTO `sys_dict_item` VALUES (35, '', 99, 0, 'admin', '2022-11-29 17:06:52', 'admin', '2022-11-29 17:07:17', 15, '数字输入框', 'InputNumber', '{\"placeholder\": \"请输入\"}', 1);
INSERT INTO `sys_dict_item` VALUES (36, '', 1, 0, 'admin', '2022-11-30 17:15:11', 'admin', '2022-11-30 17:20:21', 16, 'String有限长度字符串', 'String', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (37, '', 1, 0, 'admin', '2022-11-30 17:15:28', 'admin', '2022-11-30 17:19:58', 16, 'Text字符串', 'Text', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (38, '', 1, 0, 'admin', '2022-11-30 17:15:51', 'admin', '2022-11-30 17:19:00', 16, 'Integer整数', 'Integer', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (39, '', 1, 0, 'admin', '2022-11-30 17:16:24', 'admin', '2022-11-30 17:19:19', 16, 'Float浮点数', 'Float', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (40, '', 1, 0, 'admin', '2022-11-30 17:17:19', 'admin', '2022-11-30 17:18:42', 16, 'SmallInteger短整数', 'SmallInteger', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (41, '', 1, 0, 'admin', '2022-11-30 17:17:53', '', '2022-11-30 17:17:53', 16, 'TIMESTAMP时间戳', 'TIMESTAMP', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (42, '', 1, 0, 'admin', '2022-11-30 17:18:25', '', '2022-11-30 17:18:25', 16, 'DateTime时间', 'DateTime', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (43, '', 1, 0, 'admin', '2022-12-01 16:44:01', '', '2022-12-01 16:44:01', 15, '多行文本框', 'TextArea', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (44, '', 100, 0, 'admin', '2022-12-17 16:22:23', 'admin', '2022-12-17 19:25:48', 17, 'mysql', 'mysql', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (45, '', 1, 0, 'admin', '2022-12-17 19:10:21', '', '2022-12-17 19:10:21', 17, 'elasticsearch', 'elasticsearch', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (46, '', 1, 0, 'admin', '2022-12-19 12:28:39', '', '2022-12-19 12:28:39', 17, 'clickhouse', 'clickhouse', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (47, '', 99, 0, 'admin', '2022-12-19 15:46:55', 'admin', '2023-02-08 03:02:16', 18, 'mysql数据表', 'mysql_table', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (48, '', 100, 0, 'admin', '2022-12-19 15:47:44', 'admin', '2023-02-08 03:02:10', 18, 'sql', 'sql', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (49, '', 98, 0, 'admin', '2022-12-20 15:56:51', 'admin', '2023-02-08 03:02:23', 18, 'elasticsearch索引', 'elasticsearch_index', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (50, '', 97, 0, 'admin', '2023-02-08 02:56:41', 'admin', '2023-02-08 03:02:32', 18, 'clickhouse数据表', 'clickhouse_table', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (51, '', 1, 0, 'admin', '2023-02-08 02:57:14', '', '2023-02-08 02:57:14', 18, 'influxdb数据表', 'influxdb_table', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (52, '', 1, 0, 'admin', '2023-02-08 03:00:55', '', '2023-02-08 03:00:55', 18, 'neo4j graph', 'neo4j_graph', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (53, '', 1, 0, 'admin', '2023-02-08 03:01:44', '', '2023-02-08 03:01:44', 18, 'mongodb集合', 'mongodb_collection', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (54, '', 1, 0, 'admin', '2023-02-08 03:02:03', '', '2023-02-08 03:02:03', 18, 'kafka topic', 'kafka_topic', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (55, '', 2, 0, 'admin', '2023-03-07 17:20:23', 'admin', '2023-03-08 10:02:17', 19, '组件型', '1', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (56, '', 1, 0, 'admin', '2023-03-07 17:21:01', 'admin', '2023-03-08 10:02:11', 19, '配置型', '2', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (57, '', 1, 0, 'admin', '2023-03-07 17:22:17', 'admin', '2023-03-09 17:05:51', 20, 'python任务', 'PythonTask', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (58, '', 1, 0, 'admin', '2023-03-07 17:22:36', 'admin', '2023-03-09 17:05:41', 20, 'shell任务', 'ShellTask', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (59, '', 1, 0, 'admin', '2023-03-13 03:24:56', '', '2023-03-13 03:24:56', 20, 'spark任务', 'SparkTask', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (60, '', 99, 0, 'admin', '2023-03-16 03:53:46', 'admin', '2023-05-14 13:48:25', 21, '默认队列', 'default', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (61, '', 98, 0, 'admin', '2023-03-16 03:54:11', 'admin', '2023-05-14 13:48:32', 21, '计算型任务队列', 'compute', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (62, '', 96, 0, 'admin', '2023-03-16 03:54:33', 'admin', '2023-05-14 13:48:48', 21, 'eventlet协程队列', 'eventlet', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (63, '', 97, 0, 'admin', '2023-03-16 03:54:52', 'admin', '2023-05-14 13:48:40', 21, '实时任务处理队列', 'realtime', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (64, '', 1, 0, 'admin', '2023-03-24 16:57:00', 'admin', '2023-03-24 17:01:59', 20, '数据集成任务', 'EtlTask', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (65, '', 1, 0, 'admin', '2023-04-03 13:49:11', '', '2023-04-03 13:49:11', 22, '数据转换算法', 'etl_algorithm', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (66, '', 1, 0, 'admin', '2023-04-03 13:53:32', '', '2023-04-03 13:53:32', 23, '组件型', '1', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (67, '', 1, 0, 'admin', '2023-04-03 13:53:41', '', '2023-04-03 13:53:41', 23, '配置型', '2', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (68, '', 1, 0, 'admin', '2023-04-03 13:54:29', '', '2023-04-03 13:54:29', 24, '测试组件', 'test', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (69, '', 1, 0, 'admin', '2023-04-03 14:50:36', '', '2023-04-03 14:50:36', 22, '数据校验算法', 'verify_algorithm', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (70, '', 1, 0, 'admin', '2023-04-18 06:56:39', '', '2023-04-18 06:56:39', 17, 'influxdb', 'influxdb', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (71, '', 1, 0, 'admin', '2023-04-18 06:56:51', '', '2023-04-18 06:56:51', 17, 'neo4j', 'neo4j', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (72, '', 1, 0, 'admin', '2023-04-18 06:57:13', '', '2023-04-18 06:57:13', 17, 'mongodb', 'mongodb', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (73, '', 1, 0, 'admin', '2023-04-18 06:57:49', '', '2023-04-18 06:57:49', 17, 'kafka', 'kafka', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (74, '', 1, 0, 'admin', '2023-05-14 13:49:10', '', '2023-05-14 13:49:10', 21, '外网爬虫队列', 'haiwai_spider', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (75, '', 1, 0, 'admin', '2023-05-14 16:22:42', '', '2023-05-14 16:22:42', 18, 'mysql binlog数据流', 'mysql_binlog', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (84, '', 1, 0, 'admin', '2023-06-19 16:58:59', 'admin', '2023-06-25 07:03:45', 29, '任务失败告警', 'TaskFailStrategy', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (85, '', 1, 0, 'admin', '2023-06-20 06:16:08', '', '2023-06-20 06:16:08', 30, '紧急', '1', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (86, '', 1, 0, 'admin', '2023-06-20 06:16:30', 'admin', '2023-06-20 06:23:29', 30, '严重', '2', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (87, '', 1, 0, 'admin', '2023-06-20 06:16:52', 'admin', '2023-06-25 12:11:21', 30, '中等', '3', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (88, '', 1, 0, 'admin', '2023-06-20 06:17:18', '', '2023-06-20 06:17:18', 30, '提示', '4', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (89, '', 1, 0, 'admin', '2023-06-20 06:17:39', '', '2023-06-20 06:17:39', 30, '信息', '5', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (90, '', 1, 0, 'admin', '2023-06-20 07:02:46', '', '2023-06-20 07:02:46', 31, '未修复', '0', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (91, '', 1, 0, 'admin', '2023-06-20 07:02:56', '', '2023-06-20 07:02:56', 31, '已修复', '1', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (92, '', 1, 0, 'admin', '2023-07-08 07:23:51', '', '2023-07-08 07:23:51', 20, 'flink任务', 'FlinkTask', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (93, '', 1, 0, 'admin', '2023-07-17 10:49:21', '', '2023-07-17 10:49:21', 17, '文件', 'file', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (94, '', 1, 0, 'admin', '2023-07-17 10:54:32', '', '2023-07-17 10:54:32', 18, '表格文件(csv/excel)', 'file_table', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (95, '', 1, 0, 'admin', '2023-09-21 18:56:48', '', '2023-09-21 18:56:48', 17, 'minio对象存储', 'minio', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (96, '', 1, 0, 'admin', '2023-09-21 18:56:58', '', '2023-09-21 18:56:58', 17, 'redis', 'redis', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (97, '', 1, 0, 'admin', '2023-09-21 18:58:25', '', '2023-09-21 18:58:25', 18, 'minio表格文件(csv/excel)', 'minio_table', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (98, '', 1, 0, 'admin', '2023-09-21 18:58:46', '', '2023-09-21 18:58:46', 18, 'minio json文件', 'minio_json', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (99, '', 1, 0, 'admin', '2023-09-21 18:59:07', '', '2023-09-21 18:59:07', 18, 'minio h5文件', 'minio_h5', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (100, '', 1, 0, 'admin', '2023-09-21 18:59:31', '', '2023-09-21 18:59:31', 18, 'json文件', 'file_json', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (101, '', 1, 0, 'admin', '2023-09-21 18:59:46', '', '2023-09-21 18:59:46', 18, 'h5文件', 'file_h5', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (102, '', 1, 0, 'admin', '2023-09-21 19:00:11', '', '2023-09-21 19:00:11', 18, 'redis 字符串', 'redis_string', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (103, '', 1, 0, 'admin', '2023-09-21 19:00:23', '', '2023-09-21 19:00:23', 18, 'redis 列表', 'redis_list', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (104, '', 1, 0, 'admin', '2023-09-21 19:00:41', '', '2023-09-21 19:00:41', 18, 'redis 队列', 'redis_list_stream', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (105, '', 1, 0, 'admin', '2023-09-21 19:00:58', '', '2023-09-21 19:00:58', 18, 'redis 哈希', 'redis_map', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (106, '', 1, 0, 'admin', '2023-10-22 06:43:23', '', '2023-10-23 07:28:11', 32, '上海证券交易所-股票数据总貌', 'stock_sse_summary', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (107, '', 1, 0, 'admin', '2023-10-22 07:08:44', '', '2023-10-23 07:28:15', 32, 'A 股日频率数据-东方财富', 'stock_zh_a_hist', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (108, '', 1, 0, '', '2023-10-23 07:27:40', '', '2023-10-23 07:27:40', 32, '中国金融期货交易所每日交易数据', 'get_cffex_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (109, '', 1, 0, '', '2023-10-23 07:27:58', '', '2023-10-23 07:27:58', 32, '中国金融期货交易所前20会员持仓数据明细', 'get_cffex_rank_table', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (110, '', 1, 0, '', '2023-10-23 07:28:04', '', '2023-10-23 07:28:04', 32, '郑州商品交易所每日交易数据', 'get_czce_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (111, '', 1, 0, '', '2023-10-23 07:28:04', '', '2023-10-23 07:28:04', 32, '获取郑州商品交易所前20会员持仓数据明细', 'get_czce_rank_table', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (112, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取大连商品交易所每日交易数据', 'get_dce_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (113, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取广州期货交易所每日交易数据', 'get_gfex_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (114, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取上海国际能源交易中心每日交易数据', 'get_ine_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (115, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取新加坡交易所每日交易数据', 'futures_sgx_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (116, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取大连商品交易所前20会员持仓数据明细', 'get_dce_rank_table', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (117, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取中国金融期货交易所每日基差数据', 'get_futures_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (118, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取四个期货交易所前5, 10, 15, 20会员持仓排名数据', 'get_rank_sum', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (119, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取每日四个期货交易所前5, 10, 15, 20会员持仓排名数据', 'get_rank_sum_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (120, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '大连商品交易所前 20 会员持仓排名数据', 'futures_dce_position_rank', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (121, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取大宗商品注册仓单数据', 'get_receipt', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (122, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取某一天某品种(主力和次主力)或固定两个合约的展期收益率', 'get_roll_yield', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (123, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取展期收益率', 'get_roll_yield_bar', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (124, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取上海期货交易所每日交易数据', 'get_shfe_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (125, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取上海期货交易所前20会员持仓数据明细', 'get_shfe_rank_table', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (126, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取上海期货交易所日成交均价数据', 'get_shfe_v_wap', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (127, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取具体交易日大宗商品现货价格及相应基差数据', 'futures_spot_price', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (128, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取具体交易日大宗商品现货价格及相应基差数据-该接口补充历史数据', 'futures_spot_price_previous', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (129, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取一段交易日大宗商品现货价格及相应基差数据', 'futures_spot_price_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (130, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '郑州商品交易所-交易数据-仓单日报', 'futures_czce_warehouse_receipt', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (131, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '上海期货交易所-交易数据-仓单日报', 'futures_shfe_warehouse_receipt', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (132, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '大连商品交易所-交易数据-仓单日报', 'futures_dce_warehouse_receipt', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (133, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '国泰君安-交易日历', 'futures_rule', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (134, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取奇货可查-指数-数值数据', 'get_qhkc_index', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (135, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取奇货可查-指数-累计盈亏数据', 'get_qhkc_index_profit_loss', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (136, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取奇货可查-指数-大资金动向数据', 'get_qhkc_index_trend', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (137, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取奇货可查-资金-净持仓分布数据', 'get_qhkc_fund_bs', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (138, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取奇货可查-资金-总持仓分布数据', 'get_qhkc_fund_position', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (139, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取奇货可查-资金-净持仓变化分布数据', 'get_qhkc_fund_position_change', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (140, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取奇货可查-工具-外盘比价数据', 'get_qhkc_tool_foreign', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (141, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取奇货可查-工具-各地区经济数据', 'get_qhkc_tool_gdp', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (142, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取中国银行间市场交易商协会-债券数据', 'get_bond_bank', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (143, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '提供英为财情-股票指数-全球股指与期货指数数据', 'index_investing_global', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (144, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '提供英为财情-股票指数-全球股指与期货指数数据-URL版本', 'index_investing_global_from_url', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (145, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '提供英为财情-债券数据-全球政府债券行情与收益率数据', 'bond_investing_global', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (146, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '提供大连商品交易所商品期权数据', 'option_dce_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (147, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '提供郑州商品交易所商品期权数据', 'option_czce_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (148, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '提供上海期货交易所商品期权数据', 'option_shfe_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (149, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '提供广州期货交易所商品期权数据', 'option_gfex_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (150, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '提供广州期货交易所-合约隐含波动率数据', 'option_gfex_vol_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (151, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '债券市场行情-现券市场成交行情数据', 'get_bond_market_quote', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (152, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '债券市场行情-现券市场做市报价数据', 'get_bond_market_trade', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (153, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '人民币外汇即期报价数据', 'get_fx_spot_quote', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (154, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '人民币外汇远掉报价数据', 'get_fx_swap_quote', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (155, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '外币对即期报价数据', 'get_fx_pair_quote', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (156, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '全球大宗商品数据', 'futures_global_commodity_hist', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (157, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '欧洲央行决议报告', 'macro_euro_interest_rate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (158, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '全球最大黄金ETF—SPDR Gold Trust持仓报告', 'macro_cons_gold', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (159, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '全球最大白银ETF--iShares Silver Trust持仓报告', 'macro_cons_silver', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (160, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '欧佩克报告', 'macro_cons_opec_month', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (161, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '期货仓单有效期数据', 'get_receipt_date', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (162, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取新浪-国内期货实时行情数据', 'futures_zh_spot', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (163, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取新浪-国内期货实时行情数据(品种)', 'futures_zh_realtime', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (164, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取新浪-外盘期货实时行情数据', 'futures_foreign_commodity_realtime', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (165, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取新浪-外盘期货历史行情数据', 'futures_foreign_hist', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (166, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取新浪-外盘期货合约详情', 'futures_foreign_detail', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (167, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取新浪-内盘分时数据', 'futures_zh_minute_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (168, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '提供上海证券交易所期权数据', 'get_finance_option', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (169, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '提供主流加密货币行情数据接口', 'crypto_js_spot', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (170, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取港股的历史行情数据(包括前后复权因子)', 'stock_hk_spot', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (171, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取港股的实时行情数据(也可以用于获得所有港股代码)', 'stock_hk_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (172, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '港股实时行情', 'stock_hk_spot_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (173, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '港股主板实时行情', 'stock_hk_main_board_spot_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (174, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获得美股的所有股票代码', 'get_us_stock_name', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (175, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取美股行情报价', 'stock_us_spot', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (176, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取美股的历史数据(包括前复权因子)', 'stock_us_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (177, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取美股的基本面数据', 'stock_us_fundamental', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (178, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取 A+H 股实时行情数据(延迟15分钟)', 'stock_zh_ah_spot', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (179, '', 1, 0, '', '2023-10-23 07:28:05', '', '2023-10-23 07:28:05', 32, '获取 A+H 股历史行情数据(日频)', 'stock_zh_ah_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (180, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '获取 A+H 股所有股票代码', 'stock_zh_ah_name', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (181, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '新浪 A 股实时行情数据', 'stock_zh_a_spot', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (182, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '东财 A 股实时行情数据', 'stock_zh_a_spot_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (183, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '东财沪 A 股实时行情数据', 'stock_sh_a_spot_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (184, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '东财深 A 股实时行情数据', 'stock_sz_a_spot_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (185, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '东财京 A 股实时行情数据', 'stock_bj_a_spot_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (186, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '东财新股实时行情数据', 'stock_new_a_spot_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (187, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '东财科创板实时行情数据', 'stock_kc_a_spot_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (188, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '东财 B 股实时行情数据', 'stock_zh_b_spot_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (189, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '获取 A 股历史行情数据(日频)', 'stock_zh_a_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (190, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '获取 A 股分时历史行情数据(分钟)', 'stock_zh_a_minute', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (191, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '获取 A 股 CDR 历史行情数据(日频)', 'stock_zh_a_cdr_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (192, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '获取科创板实时行情数据', 'stock_zh_kcb_spot', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (193, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '获取科创板历史行情数据(日频)', 'stock_zh_kcb_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (194, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '获取银保监分局本级行政处罚-信息公开表', 'bank_fjcf_table_detail', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (195, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, 'O-MAN已实现波动率', 'article_oman_rv', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (196, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, 'RiREDACTEDLab已实现波动率', 'article_rlab_rv', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (197, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, 'FF当前因子', 'ff_crr', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (198, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '股票指数历史行情数据', 'stock_zh_index_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (199, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '股票指数历史行情数据-腾讯', 'stock_zh_index_daily_tx', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (200, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '股票指数历史行情数据-东方财富', 'stock_zh_index_daily_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (201, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '股票指数实时行情数据', 'stock_zh_index_spot', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (202, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, 'A 股票分笔行情数据(近2年)-腾讯', 'stock_zh_a_tick_tx', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (203, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, 'A 股票分笔行情数据(近2年)-腾讯-当日数据', 'stock_zh_a_tick_tx_js', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (204, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '每日日出和日落数据', 'weather_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (205, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '每月日出和日落数据', 'weather_monthly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (206, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '河北空气质量数据', 'air_quality_hebei', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (207, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '波动率指数', 'futures_volatility_index_nh', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (208, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '价格指数', 'futures_price_index_nh', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (209, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '收益率指数', 'futures_return_index_nh', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (210, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '主要国家和地区的经济政策不确定性(EPU)指数', 'article_epu_index', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (211, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '获取3个月内的微博指数', 'index_weibo_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (212, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '获取百度搜索指数', 'baidu_search_index', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (213, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '获取百度资讯指数', 'baidu_info_index', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (214, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '获取百度媒体指数', 'baidu_media_index', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (215, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '获取谷歌趋势指数', 'google_index', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (216, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '申万三级信息', 'sw_index_third_info', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (217, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '申万三级信息成份', 'sw_index_third_cons', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (218, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '空气质量历史数据', 'air_quality_hist', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (219, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '空气质量排行', 'air_quality_rank', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (220, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '空气质量观测点历史数据', 'air_quality_watch_point', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (221, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '所有城市列表', 'air_city_table', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (222, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '获取财富世界500强公司历年排名', 'fortune_rank', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (223, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '中国证券投资基金业协会-信息公示-会员信息-会员机构综合查询', 'amac_member_info', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (224, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '中国证券投资基金业协会-信息公示-从业人员信息-基金从业人员资格注册信息', 'amac_person_fund_org_list', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (225, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '中国证券投资基金业协会-信息公示-从业人员信息-债券投资交易相关人员公示', 'amac_person_bond_org_list', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (226, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '中国证券投资基金业协会-信息公示-私募基金管理人公示-私募基金管理人综合查询', 'amac_manager_info', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (227, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '中国证券投资基金业协会-信息公示-私募基金管理人公示-私募基金管理人分类公示', 'amac_manager_classify_info', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (228, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '中国证券投资基金业协会-信息公示-私募基金管理人公示-证券公司私募基金子公司管理人信息公示', 'amac_member_sub_info', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (229, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '中国证券投资基金业协会-信息公示-基金产品-私募基金管理人基金产品', 'amac_fund_info', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (230, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '中国证券投资基金业协会-信息公示-基金产品-证券公司集合资管产品公示', 'amac_securities_info', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (231, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '中国证券投资基金业协会-信息公示-基金产品-证券公司直投基金', 'amac_aoin_info', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (232, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '中国证券投资基金业协会-信息公示-基金产品公示-证券公司私募投资基金', 'amac_fund_sub_info', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (233, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '中国证券投资基金业协会-信息公示-基金产品公示-基金公司及子公司集合资管产品公示', 'amac_fund_account_info', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (234, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '中国证券投资基金业协会-信息公示-基金产品公示-资产支持专项计划', 'amac_fund_abs', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (235, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '中国证券投资基金业协会-信息公示-基金产品公示-期货公司集合资管产品公示', 'amac_futures_info', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (236, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '中国证券投资基金业协会-信息公示-诚信信息-已注销私募基金管理人名单', 'amac_manager_cancelled_info', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (237, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '市场行情-外汇市场行情-人民币外汇即期报价', 'fx_spot_quote', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (238, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '市场行情-债券市场行情-人民币外汇远掉报价', 'fx_swap_quote', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (239, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '市场行情-债券市场行情-外币对即期报价', 'fx_pair_quote', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (240, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '碳排放权-国内', 'energy_carbon_domestic', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (241, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '碳排放权-北京', 'energy_carbon_bj', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (242, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '碳排放权-深圳', 'energy_carbon_sz', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (243, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '碳排放权-国际', 'energy_carbon_eu', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (244, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '碳排放权-湖北', 'energy_carbon_hb', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (245, '', 1, 0, '', '2023-10-23 07:28:06', '', '2023-10-23 07:28:06', 32, '碳排放权-广州', 'energy_carbon_gz', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (246, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '获取世界各大城市生活成本数据', 'cost_living', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (247, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '获取商品现货价格指数', 'spot_goods', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (248, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '获取中国宏观杠杆率数据', 'macro_cnbs', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (249, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '获取金融期权数据', 'option_finance_board', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (250, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '获取新浪期货连续合约的历史数据', 'futures_main_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (251, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '获取2014至今倒闭公司名单', 'death_company', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (252, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '获取独角兽公司名单', 'nicorn_company', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (253, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '获取千里马公司名单', 'maxima_company', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (254, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '获取机构调研数据-统计', 'stock_jgdy_tj_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (255, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '获取机构调研数据-详细', 'stock_jgdy_detail_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (256, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '获取股权质押市场概况', 'stock_gpzy_profile_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (257, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '获取上市公司质押比例', 'stock_gpzy_pledge_ratio_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (258, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '获取重要股东股权质押明细', 'stock_gpzy_pledge_ratio_detail_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (259, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '获取质押机构分布统计-证券公司', 'stock_gpzy_distribute_statistics_company_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (260, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '获取质押机构分布统计-银行', 'stock_gpzy_distribute_statistics_bank_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (261, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '获取上市公司质押比例-行业数据', 'stock_gpzy_industry_data_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (262, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, 'A股商誉市场概况', 'stock_sy_profile_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (263, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '商誉减值预期明细', 'stock_sy_yq_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (264, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '个股商誉减值明细', 'stock_sy_jz_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (265, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '个股商誉明细', 'stock_sy_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (266, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '行业商誉', 'stock_sy_hy_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (267, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '获取股票账户统计数据', 'stock_account_statistics_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (268, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '股票指数-成份股-最新成份股获取', 'index_stock_cons', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (269, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '中证指数-成份股', 'index_stock_cons_csindex', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (270, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '中证指数成份股的权重', 'index_stock_cons_weight_csindex', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (271, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '股票指数-成份股-所有可以获取的指数表', 'index_stock_info', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (272, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '股票指数-成份股-所有可以获取的指数表-新浪新接口', 'index_stock_info_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (273, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '获取义乌小商品指数', 'index_yw', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (274, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '银行间拆借利率', 'rate_interbank', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (275, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '美联储利率决议报告', 'macro_bank_usa_interest_rate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (276, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '欧洲央行决议报告', 'macro_bank_euro_interest_rate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (277, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '新西兰联储决议报告', 'macro_bank_newzealand_interest_rate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (278, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '瑞士央行决议报告', 'macro_bank_switzerland_interest_rate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (279, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '英国央行决议报告', 'macro_bank_english_interest_rate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (280, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '澳洲联储决议报告', 'macro_bank_australia_interest_rate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (281, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '日本央行决议报告', 'macro_bank_japan_interest_rate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (282, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '俄罗斯央行决议报告', 'macro_bank_russia_interest_rate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (283, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '印度央行决议报告', 'macro_bank_india_interest_rate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (284, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '巴西央行决议报告', 'macro_bank_brazil_interest_rate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (285, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '城镇调查失业率', 'macro_china_urban_unemployment', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (286, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '社会融资规模增量统计', 'macro_china_shrzgm', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (287, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '金十数据中心-经济指标-中国-国民经济运行状况-经济状况-中国GDP年率报告', 'macro_china_gdp_yearly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (288, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '金十数据中心-经济指标-中国-国民经济运行状况-物价水平-中国CPI年率报告', 'macro_china_cpi_yearly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (289, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '金十数据中心-经济指标-中国-国民经济运行状况-物价水平-中国CPI月率报告', 'macro_china_cpi_monthly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (290, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '金十数据中心-经济指标-中国-国民经济运行状况-物价水平-中国PPI年率报告', 'macro_china_ppi_yearly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (291, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '金十数据中心-经济指标-中国-贸易状况-以美元计算出口年率报告', 'macro_china_exports_yoy', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (292, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '金十数据中心-经济指标-中国-贸易状况-以美元计算进口年率', 'macro_china_imports_yoy', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (293, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '金十数据中心-经济指标-中国-贸易状况-以美元计算贸易帐(亿美元)', 'macro_china_trade_balance', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (294, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '金十数据中心-经济指标-中国-产业指标-规模以上工业增加值年率', 'macro_china_industrial_production_yoy', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (295, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '金十数据中心-经济指标-中国-产业指标-官方制造业PMI', 'macro_china_pmi_yearly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (296, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '金十数据中心-经济指标-中国-产业指标-财新制造业PMI终值', 'macro_china_cx_pmi_yearly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (297, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '金十数据中心-经济指标-中国-产业指标-财新服务业PMI', 'macro_china_cx_services_pmi_yearly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (298, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '金十数据中心-经济指标-中国-产业指标-中国官方非制造业PMI', 'macro_china_non_man_pmi', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (299, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '金十数据中心-经济指标-中国-金融指标-外汇储备(亿美元)', 'macro_china_fx_reserves_yearly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (300, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '金十数据中心-经济指标-中国-金融指标-M2货币供应年率', 'macro_china_m2_yearly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (301, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '金十数据中心-经济指标-中国-金融指标-上海银行业同业拆借报告', 'macro_china_shibor_all', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (302, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '金十数据中心-经济指标-中国-金融指标-人民币香港银行同业拆息', 'macro_china_hk_market_info', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (303, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '金十数据中心-经济指标-中国-其他-中国日度沿海六大电库存数据', 'macro_china_daily_energy', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (304, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '金十数据中心-经济指标-中国-其他-中国人民币汇率中间价报告', 'macro_china_rmb', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (305, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '金十数据中心-经济指标-中国-其他-深圳融资融券报告', 'macro_china_market_margin_sz', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (306, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '金十数据中心-经济指标-中国-其他-上海融资融券报告', 'macro_china_market_margin_sh', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (307, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '金十数据中心-经济指标-中国-其他-上海黄金交易所报告', 'macro_china_au_report', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (308, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '中国-利率-贷款报价利率', 'macro_china_lpr', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (309, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '中国-新房价指数', 'macro_china_new_house_price', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (310, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '中国-企业景气及企业家信心指数', 'macro_china_enterprise_boom_index', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (311, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '中国-全国税收收入', 'macro_china_national_tax_receipts', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (312, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '中国-银行理财产品发行数量', 'macro_china_bank_financing', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (313, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '中国-新增信贷数据', 'macro_china_new_financial_credit', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (314, '', 1, 0, '', '2023-10-23 07:28:07', '', '2023-10-23 07:28:07', 32, '中国-外汇和黄金储备', 'macro_china_fx_gold', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (315, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '中国-全国股票交易统计表', 'macro_china_stock_market_cap', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (316, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '中国-居民消费价格指数', 'macro_china_cpi', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (317, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '中国-国内生产总值', 'macro_china_gdp', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (318, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '中国-工业品出厂价格指数', 'macro_china_ppi', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (319, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '中国-采购经理人指数', 'macro_china_pmi', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (320, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '中国-城镇固定资产投资', 'macro_china_gdzctz', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (321, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:12', 32, '海关进出口增减情况', 'macro_china_hgjck', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (322, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '中国-财政收入', 'macro_china_czsr', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (323, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '中国-外汇贷款数据', 'macro_china_whxd', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (324, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '中国-本外币存款', 'macro_china_wbck', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (325, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '中国-货币净投放与净回笼', 'macro_china_hb', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (326, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '中国-央行公开市场操作', 'macro_china_gksccz', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (327, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '中国-债券发行', 'macro_china_bond_public', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (328, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-经济状况-美国GDP', 'macro_usa_gdp_monthly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (329, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-物价水平-美国CPI月率报告', 'macro_usa_cpi_monthly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (330, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '东方财富-经济数据一览-美国-CPI年率', 'macro_usa_cpi_yoy', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (331, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-物价水平-美国核心CPI月率报告', 'macro_usa_core_cpi_monthly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (332, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-物价水平-美国个人支出月率报告', 'macro_usa_personal_spending', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (333, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-物价水平-美国零售销售月率报告', 'macro_usa_retail_sales', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (334, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-物价水平-美国进口物价指数报告', 'macro_usa_import_price', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (335, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-物价水平-美国出口价格指数报告', 'macro_usa_export_price', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (336, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-劳动力市场-LMCI', 'macro_usa_lmci', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (337, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-劳动力市场-失业率-美国失业率报告', 'macro_usa_unemployment_rate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (338, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-劳动力市场-失业率-美国挑战者企业裁员人数报告', 'macro_usa_job_cuts', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (339, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-劳动力市场-就业人口-美国非农就业人数报告', 'macro_usa_non_farm', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (340, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-劳动力市场-就业人口-美国ADP就业人数报告', 'macro_usa_adp_employment', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (341, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-劳动力市场-消费者收入与支出-美国核心PCE物价指数年率报告', 'macro_usa_core_pce_price', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (342, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-劳动力市场-消费者收入与支出-美国实际个人消费支出季率初值报告', 'macro_usa_real_consumer_spending', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (343, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-贸易状况-美国贸易帐报告', 'macro_usa_trade_balance', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (344, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-贸易状况-美国经常帐报告', 'macro_usa_current_account', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (345, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-产业指标-制造业-贝克休斯钻井报告', 'macro_usa_rig_count', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (346, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-产业指标-制造业-美国生产者物价指数(PPI)报告', 'macro_usa_ppi', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (347, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-产业指标-制造业-美国核心生产者物价指数(PPI)报告', 'macro_usa_core_ppi', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (348, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-产业指标-制造业-美国API原油库存报告', 'macro_usa_api_crude_stock', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (349, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-产业指标-制造业-美国Markit制造业PMI初值报告', 'macro_usa_pmi', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (350, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-产业指标-制造业-美国ISM制造业PMI报告', 'macro_usa_ism_pmi', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (351, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-产业指标-房地产-美国NAHB房产市场指数报告', 'macro_usa_nahb_house_market_index', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (352, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-产业指标-房地产-美国新屋开工总数年化报告', 'macro_usa_house_starts', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (353, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-产业指标-房地产-美国新屋销售总数年化报告', 'macro_usa_new_home_sales', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (354, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-产业指标-房地产-美国营建许可总数报告', 'macro_usa_building_permits', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (355, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-产业指标-房地产-美国成屋销售总数年化报告', 'macro_usa_exist_home_sales', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (356, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-产业指标-房地产-美国FHFA房价指数月率报告', 'macro_usa_house_price_index', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (357, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-产业指标-房地产-美国S&P/CS20座大城市房价指数年率报告', 'macro_usa_spcs20', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (358, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-产业指标-房地产-美国成屋签约销售指数月率报告', 'macro_usa_pending_home_sales', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (359, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-领先指标-美国谘商会消费者信心指数报告', 'macro_usa_cb_consumer_confidence', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (360, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-领先指标-美国NFIB小型企业信心指数报告', 'macro_usa_nfib_small_business', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (361, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-领先指标-美国密歇根大学消费者信心指数初值报告', 'macro_usa_michigan_consumer_sentiment', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (362, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-其他-美国EIA原油库存报告', 'macro_usa_eia_crude_rate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (363, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-其他-美国初请失业金人数报告', 'macro_usa_initial_jobless', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (364, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '金十数据中心-经济指标-美国-其他-美国原油产量报告', 'macro_usa_crude_inner', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (365, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '全球最大黄金ETF—SPDR Gold Trust持仓报告', 'macro_cons_gold_volume', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (366, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '全球最大黄金ETF—SPDR Gold Trust持仓报告', 'macro_cons_gold_change', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (367, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '全球最大黄金ETF—SPDR Gold Trust持仓报告', 'macro_cons_gold_amount', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (368, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '全球最大白银ETF--iShares Silver Trust持仓报告', 'macro_cons_silver_volume', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (369, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '全球最大白银ETF--iShares Silver Trust持仓报告', 'macro_cons_silver_change', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (370, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '全球最大白银ETF--iShares Silver Trust持仓报告', 'macro_cons_silver_amount', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (371, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '伦敦金属交易所(LME)-持仓报告', 'macro_euro_lme_holding', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (372, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '伦敦金属交易所(LME)-库存报告', 'macro_euro_lme_stock', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (373, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '外汇类非商业持仓报告', 'macro_usa_cftc_nc_holding', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (374, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '商品类非商业持仓报告', 'macro_usa_cftc_c_holding', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (375, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '外汇类商业持仓报告', 'macro_usa_cftc_merchant_currency_holding', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (376, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '商品类商业持仓报告', 'macro_usa_cftc_merchant_goods_holding', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (377, '', 1, 0, '', '2023-10-23 07:28:08', '', '2023-10-23 07:28:08', 32, '货币对-投机情绪报告', 'macro_fx_sentiment', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (378, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '百度迁徙地图-迁入/出地详情', 'migration_area_baidu', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (379, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '百度迁徙地图-迁徙规模', 'migration_scale_baidu', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (380, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '债券-沪深债券-历史行情数据', 'bond_zh_hs_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (381, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '债券-沪深债券-实时行情数据', 'bond_zh_hs_spot', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (382, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '债券-沪深可转债-历史行情数据', 'bond_zh_hs_cov_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (383, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '债券-沪深可转债-实时行情数据', 'bond_zh_hs_cov_spot', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (384, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '债券-可转债数据一览表', 'bond_zh_cov', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (385, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '债券-可转债数据比价', 'bond_cov_comparison', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (386, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '可转债实时数据-集思录', 'bond_cb_jsl', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (387, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '可转债转股价变动-集思录', 'bond_cb_adj_logs_jsl', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (388, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '可转债-集思录可转债等权指数', 'bond_cb_index_jsl', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (389, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '可转债-集思录可转债-强赎', 'bond_cb_redeem_jsl', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (390, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '上证50期权列表', 'option_cffex_sz50_list_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (391, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '沪深300期权历史行情-日频', 'option_cffex_sz50_daily_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (392, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '沪深300期权列表', 'option_cffex_hs300_list_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (393, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '沪深300期权实时行情', 'option_cffex_hs300_spot_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (394, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '沪深300期权历史行情-日频', 'option_cffex_hs300_daily_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (395, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '中证1000期权列表', 'option_cffex_zz1000_list_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (396, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '中证1000期权实时行情', 'option_cffex_zz1000_spot_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (397, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '中证1000期权历史行情-日频', 'option_cffex_zz1000_daily_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (398, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '上交所期权列表', 'option_sse_list_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (399, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '上交所期权剩余到期日', 'option_sse_expire_day_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (400, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '上交所期权代码', 'option_sse_codes_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (401, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '上交所期权实时行情', 'option_sse_spot_price_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (402, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '上交所期权标的物实时行情', 'option_sse_underlying_spot_price_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (403, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '上交所期权希腊字母', 'option_sse_greeks_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (404, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '上交所期权分钟数据', 'option_sse_minute_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (405, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '上交所期权日频数据', 'option_sse_daily_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (406, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '金融股票期权分时数据', 'option_finance_minute_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (407, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '股票期权分时数据', 'option_minute_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (408, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '商品期权合约字典查询', 'option_sina_option_commodity_dict', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (409, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '商品期权合约查询', 'option_sina_option_commodity_contract_list', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (410, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '商品期权行情历史数据', 'option_sina_option_commodity_hist', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (411, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '微博舆情报告', 'stock_js_weibo_report', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (412, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '知识图谱', 'nlp_ownthink', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (413, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '智能问答', 'nlp_answer', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (414, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '最新货币报价', 'currency_latest', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (415, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '指定历史日期的所有货币报价', 'currency_history', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (416, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '指定日期间的时间序列数据-需要权限', 'currency_time_series', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (417, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '查询所支持的货币信息', 'currency_currencies', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (418, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '货币换算', 'currency_convert', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (419, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '指定历史日期的货币对的历史报价', 'currency_hist', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (420, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '指定货币的所有可获取货币对的数据', 'currency_pair_map', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (421, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '当前所有可兑换货币对', 'currency_name_code', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (422, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '基金基本信息', 'fund_name_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (423, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '指数型基金-基本信息', 'fund_info_index_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (424, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '基金申购状态', 'fund_purchase_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (425, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '开放式基金-实时数据', 'fund_open_fund_daily_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (426, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '开放式基金-历史数据', 'fund_open_fund_info_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (427, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '场内交易基金-实时数据', 'fund_etf_fund_daily_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (428, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '场内交易基金-历史数据', 'fund_etf_fund_info_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (429, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '理财型基金-实时数据', 'fund_financial_fund_daily_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (430, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '理财型基金-历史数据', 'fund_financial_fund_info_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (431, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '分级基金-实时数据', 'fund_graded_fund_daily_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (432, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '分级基金-历史数据', 'fund_graded_fund_info_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (433, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '货币型基金-实时数据', 'fund_money_fund_daily_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (434, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '货币型基金-历史数据', 'fund_money_fund_info_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (435, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '基金估值', 'fund_value_estimation_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (436, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '分析师排名', 'stock_analyst_rank_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (437, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '分析师详情', 'stock_analyst_detail_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (438, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '股市关注度', 'stock_comment_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (439, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '机构参与度', 'stock_comment_detail_zlkp_jgcyd_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (440, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '综合评价-历史评分', 'stock_comment_detail_zhpj_lspf_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (441, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '市场热度-用户关注指数', 'stock_comment_detail_scrd_focus_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (442, '', 1, 0, '', '2023-10-23 07:28:09', '', '2023-10-23 07:28:09', 32, '市场热度-市场参与意愿', 'stock_comment_detail_scrd_desire_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (443, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '市场热度-日度市场参与意愿', 'stock_comment_detail_scrd_desire_daily_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (444, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '市场热度-市场成本', 'stock_comment_detail_scrd_cost_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (445, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '港股通成份股', 'stock_hk_ggt_components_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (446, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '沪深港通北向-净流入', 'stock_hsgt_north_net_flow_in_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (447, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '沪深港通北向-资金余额', 'stock_hsgt_north_cash_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (448, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '沪深港通北向-累计净流入', 'stock_hsgt_north_acc_flow_in_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (449, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '沪深港通南向-净流入', 'stock_hsgt_south_net_flow_in_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (450, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '沪深港通南向-资金余额', 'stock_hsgt_south_cash_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (451, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '沪深港通南向-累计净流入', 'stock_hsgt_south_acc_flow_in_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (452, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '沪深港通持股-个股排行', 'stock_hsgt_hold_stock_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (453, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '沪深港通持股-每日个股统计', 'stock_hsgt_stock_statistics_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (454, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '沪深港通持股-每日机构统计', 'stock_hsgt_institution_statistics_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (455, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '沪深港通历史数据', 'stock_hsgt_hist_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (456, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '板块排行', 'stock_hsgt_board_rank_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (457, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '沪深港通资金流向', 'stock_hsgt_fund_flow_summary_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (458, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '两市停复牌数据', 'stock_tfp_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (459, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '汽柴油历史调价信息', 'energy_oil_hist', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (460, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '地区油价', 'energy_oil_detail', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (461, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '现货与股票接口', 'futures_spot_stock', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (462, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '中证商品指数', 'futures_index_ccidx', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (463, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '中证商品指数-分时', 'futures_index_min_ccidx', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (464, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '打新收益率', 'stock_dxsyl_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (465, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '新股申购与中签查询', 'stock_xgsglb_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (466, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '上市公司业绩预告', 'stock_yjyg_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (467, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '上市公司预约披露时间', 'stock_yysj_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (468, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '获取标普500指数的分钟数据', 'hf_sp_500', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (469, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '库存数据-东方财富', 'futures_inventory_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (470, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '个股资金流', 'stock_individual_fund_flow', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (471, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '个股资金流排名', 'stock_individual_fund_flow_rank', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (472, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '大盘资金流', 'stock_market_fund_flow', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (473, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '板块资金流排名', 'stock_sector_fund_flow_rank', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (474, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, 'xx行业个股资金流', 'stock_sector_fund_flow_summary', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (475, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '行业历史资金流', 'stock_sector_fund_flow_hist', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (476, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '概念历史资金流', 'stock_concept_fund_flow_hist', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (477, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '财务摘要', 'stock_financial_abstract', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (478, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '三大财务报表', 'stock_financial_report_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (479, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '财务指标', 'stock_financial_analysis_indicator', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (480, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '股票增发', 'stock_add_stock', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (481, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '股票新股', 'stock_ipo_info', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (482, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '分红配股', 'stock_history_dividend_detail', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (483, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '历史分红', 'stock_history_dividend', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (484, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '个股历史分红', 'stock_dividend_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (485, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '限售解禁-新浪', 'stock_restricted_release_queue_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (486, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '东方财富网-数据中心-特色数据-限售股解禁', 'stock_restricted_release_summary_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (487, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '东方财富网-数据中心-限售股解禁-解禁详情一览', 'stock_restricted_release_detail_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (488, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '东方财富网-数据中心-个股限售解禁-解禁批次', 'stock_restricted_release_queue_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (489, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '东方财富网-数据中心-个股限售解禁-解禁股东', 'stock_restricted_release_stockholder_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (490, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '流动股东', 'stock_circulate_stock_holder', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (491, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '基金持股', 'stock_fund_stock_holder', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (492, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '主要股东', 'stock_main_stock_holder', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (493, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '板块行情', 'stock_sector_spot', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (494, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '板块详情(具体股票)', 'stock_sector_detail', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (495, '', 1, 0, '', '2023-10-23 07:28:10', '', '2023-10-23 07:28:10', 32, '深证证券交易所股票代码和简称', 'stock_info_sz_name_code', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (496, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '上海证券交易所股票代码和简称', 'stock_info_sh_name_code', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (497, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '北京证券交易所股票代码和简称', 'stock_info_bj_name_code', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (498, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '上海证券交易所暂停和终止上市', 'stock_info_sh_delist', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (499, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '深证证券交易所暂停和终止上市', 'stock_info_sz_delist', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (500, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '深证证券交易所名称变更', 'stock_info_sz_change_name', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (501, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, 'A 股股票曾用名列表', 'stock_info_change_name', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (502, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, 'A 股股票代码和简称', 'stock_info_a_code_name', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (503, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '机构持股一览表', 'stock_institute_hold', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (504, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '机构持股详情', 'stock_institute_hold_detail', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (505, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '机构推荐', 'stock_institute_recommend', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (506, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '股票评级记录', 'stock_institute_recommend_detail', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (507, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '深圳证券交易所-市场总貌-证券类别统计', 'stock_szse_summary', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (508, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '深圳证券交易所-市场总貌-地区交易排序', 'stock_szse_area_summary', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (509, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '上海证券交易所-每日股票情况', 'stock_sse_deal_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (510, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '美股港股目标价', 'stock_price_js', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (511, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '券商业绩月报', 'stock_qsjy_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (512, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '彭博亿万富豪指数', 'index_bloomberg_billionaires', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (513, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '彭博亿万富豪历史指数', 'index_bloomberg_billionaires_hist', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (514, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '乐咕乐股-主板市盈率', 'stock_market_pe_lg', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (515, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '乐咕乐股-指数市盈率', 'stock_index_pe_lg', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (516, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '乐咕乐股-主板市净率', 'stock_market_pb_lg', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (517, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '乐咕乐股-指数市净率', 'stock_index_pb_lg', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (518, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, 'A 股个股市盈率、市净率和股息率指标', 'stock_a_indicator_lg', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (519, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '港股股个股市盈率、市净率和股息率指标', 'stock_hk_indicator_eniu', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (520, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '创新高和新低的股票数量', 'stock_a_high_low_statistics', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (521, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '破净股统计', 'stock_a_below_net_asset_statistics', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (522, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '新浪财经-交易日历', 'tool_trade_date_hist', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (523, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '基金实时行情-新浪', 'fund_etf_category_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (524, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '基金行情-新浪', 'fund_etf_hist_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (525, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '基金历史行情-东财', 'fund_etf_hist_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (526, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '基金分时行情-东财', 'fund_etf_hist_min_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (527, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '基金实时行情-东财', 'fund_etf_spot_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (528, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '股票财务报告-预约披露时间', 'stock_report_disclosure', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (529, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '个股-基金持股', 'stock_report_fund_hold', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (530, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '个股-基金持股-明细', 'stock_report_fund_hold_detail', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (531, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '中证指数', 'stock_zh_index_hist_csindex', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (532, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '中证指数-指数估值', 'stock_zh_index_value_csindex', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (533, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '龙虎榜-每日详情', 'stock_sina_lhb_detail_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (534, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '龙虎榜-个股上榜统计', 'stock_sina_lhb_ggtj', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (535, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '龙虎榜-营业上榜统计', 'stock_sina_lhb_yytj', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (536, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '龙虎榜-机构席位追踪', 'stock_sina_lhb_jgzz', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (537, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '龙虎榜-机构席位成交明细', 'stock_sina_lhb_jgmx', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (538, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '注册制审核-科创板', 'stock_register_kcb', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (539, '', 1, 0, '', '2023-10-23 07:28:11', '', '2023-10-23 07:28:11', 32, '注册制审核-创业板', 'stock_register_cyb', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (540, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '注册制审核-达标企业', 'stock_register_db', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (541, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '股票数据-次新股', 'stock_zh_a_new', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (542, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '国债期货可交割券相关指标', 'bond_futures_deliverable_coupons', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (543, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, 'COMEX库存数据', 'futures_comex_inventory', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (544, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '消费者信心指数', 'macro_china_xfzxx', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (545, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '工业增加值增长', 'macro_china_gyzjz', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (546, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '存款准备金率', 'macro_china_reserve_requirement_ratio', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (547, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '社会消费品零售总额', 'macro_china_consumer_goods_retail', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (548, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '全社会用电分类情况表', 'macro_china_society_electricity', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (549, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '全社会客货运输量', 'macro_china_society_traffic_volume', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (550, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '邮电业务基本情况', 'macro_china_postal_telecommunicational', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (551, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '国际旅游外汇收入构成', 'macro_china_international_tourism_fx', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (552, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '民航客座率及载运率', 'macro_china_passenger_load_factor', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (553, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '航贸运价指数', 'macro_china_freight_index', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (554, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '央行货币当局资产负债', 'macro_china_central_bank_balance', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (555, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, 'FR007利率互换曲线历史数据', 'macro_china_swap_rate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (556, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '收盘收益率曲线历史数据', 'bond_china_close_return', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (557, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '保险业经营情况', 'macro_china_insurance', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (558, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '货币供应量', 'macro_china_supply_of_money', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (559, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '央行黄金和外汇储备', 'macro_china_foreign_exchange_gold', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (560, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '商品零售价格指数', 'macro_china_retail_price_index', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (561, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '新闻联播文字稿', 'news_cctv', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (562, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '电影实时票房', 'movie_boxoffice_realtime', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (563, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '电影单日票房', 'movie_boxoffice_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (564, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '电影单周票房', 'movie_boxoffice_weekly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (565, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '电影单月票房', 'movie_boxoffice_monthly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (566, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '电影年度票房', 'movie_boxoffice_yearly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (567, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '电影年度首周票房', 'movie_boxoffice_yearly_first_week', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (568, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '电影院单日票房', 'movie_boxoffice_cinema_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (569, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '电影院单周票房', 'movie_boxoffice_cinema_weekly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (570, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '国房景气指数', 'macro_china_real_estate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (571, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '加密货币历史数据', 'crypto_hist', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (572, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '加密货币货币名称', 'crypto_name_url_table', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (573, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '开放式基金排行', 'fund_open_fund_rank_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (574, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '场内交易基金排行', 'fund_em_exchange_rank', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (575, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '货币型基金排行', 'fund_em_money_rank', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (576, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '理财基金排行', 'fund_em_lcx_rank', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (577, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '香港基金排行', 'fund_em_hk_rank', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (578, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '回购定盘利率', 'repo_rate_hist', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (579, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '福布斯中国榜单', 'forbes_rank', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (580, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '新财富500富豪榜', 'xincaifu_rank', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (581, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '胡润排行榜', 'hurun_rank', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (582, '', 1, 0, '', '2023-10-23 07:28:12', '', '2023-10-23 07:28:12', 32, '期货合约详情', 'futures_contract_detail', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (583, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '科创板报告', 'stock_zh_kcb_report_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (584, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '东方财富-期权', 'option_current_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (585, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '国证指数-所有指数', 'index_all_cni', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (586, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '国证指数-指数行情', 'index_hist_cni', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (587, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '国证指数-样本详情', 'index_detail_cni', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (588, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '国证指数-历史样本', 'index_detail_hist_cni', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (589, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '国证指数-历史调样', 'index_detail_hist_adjust_cni', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (590, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '大宗交易-市场统计', 'stock_dzjy_sctj', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (591, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '大宗交易-每日明细', 'stock_dzjy_mrmx', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (592, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '大宗交易-每日统计', 'stock_dzjy_mrtj', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (593, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '大宗交易-活跃 A 股统计', 'stock_dzjy_hygtj', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (594, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '大宗交易-营业部排行', 'stock_dzjy_yybph', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (595, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '大宗交易-活跃营业部统计', 'stock_dzjy_hyyybtj', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (596, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '股票数据-一致行动人', 'stock_yzxdr_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (597, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '新闻-个股新闻', 'stock_news_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (598, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '上登债券信息网-债券现券市场概览', 'bond_cash_summary_sse', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (599, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '上登债券信息网-债券成交概览', 'bond_deal_summary_sse', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (600, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '中国货币供应量', 'macro_china_money_supply', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (601, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '郑商所期转现', 'futures_to_spot_czce', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (602, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '上期所期转现', 'futures_to_spot_shfe', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (603, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '大商所期转现', 'futures_to_spot_dce', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (604, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '大商所交割统计', 'futures_delivery_dce', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (605, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '郑商所交割统计', 'futures_delivery_czce', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (606, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '上期所交割统计', 'futures_delivery_shfe', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (607, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '大商所交割配对', 'futures_delivery_match_dce', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (608, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '郑商所交割配对', 'futures_delivery_match_czce', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (609, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '上海证券交易所-融资融券汇总', 'stock_margin_sse', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (610, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '上海证券交易所-融资融券详情', 'stock_margin_detail_sse', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (611, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '基金评级-基金评级总汇', 'fund_rating_all', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (612, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '基金评级-上海证券评级', 'fund_rating_sh', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (613, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '基金评级-招商证券评级', 'fund_rating_zs', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (614, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '基金评级-济安金信评级', 'fund_rating_ja', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (615, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '基金经理-基金经理大全', 'fund_manager', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (616, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '盈利预测-东财', 'stock_profit_forecast_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (617, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '盈利预测-同花顺', 'stock_profit_forecast_ths', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (618, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '中美国债收益率', 'bond_zh_us_rate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (619, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '分红配送', 'stock_fhps_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (620, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '业绩快报', 'stock_yjkb_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (621, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '同花顺-概念板块-成份股', 'stock_board_concept_cons_ths', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (622, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '同花顺-概念板块-指数日频数据', 'stock_board_concept_hist_ths', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (623, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '同花顺-成份股', 'stock_board_cons_ths', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (624, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '业绩报告', 'stock_yjbb_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (625, '', 1, 0, '', '2023-10-23 07:28:13', '', '2023-10-23 07:28:13', 32, '三大表报-资产负债表', 'stock_zcfz_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (626, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '三大表报-利润表', 'stock_lrb_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (627, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '三大表报-现金流量表', 'stock_xjll_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (628, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '首发企业申报', 'stock_ipo_declare', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (629, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '同花顺-行业板块-成份股', 'stock_board_industry_cons_ths', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (630, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '同花顺-行业板块-指数日频数据', 'stock_board_industry_index_ths', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (631, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '营业部排名-上榜次数最多', 'stock_lh_yyb_most', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (632, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '营业部排名-资金实力最强', 'stock_lh_yyb_capital', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (633, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '营业部排名-抱团操作实力', 'stock_lh_yyb_control', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (634, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '比特比持仓', 'crypto_bitcoin_hold_report', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (635, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '同花顺-数据中心-资金流向-个股资金流', 'stock_fund_flow_individual', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (636, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '同花顺-数据中心-资金流向-行业资金流', 'stock_fund_flow_industry', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (637, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '同花顺-数据中心-资金流向-概念资金流', 'stock_fund_flow_concept', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (638, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '同花顺-数据中心-资金流向-大单追踪', 'stock_fund_flow_big_deal', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (639, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '高管持股', 'stock_ggcg_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (640, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '新发基金', 'fund_new_found_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (641, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '柯桥纺织指数', 'index_kq_fz', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (642, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '柯桥时尚指数', 'index_kq_fashion', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (643, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '问财-热门股票', 'stock_hot_rank_wc', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (644, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, 'Drewry 集装箱指数', 'drewry_wci_index', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (645, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '浙江省排污权交易指数', 'index_eri', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (646, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '赚钱效应分析', 'stock_market_activity_legu', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (647, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '中国公路物流运价指数', 'index_cflp_price', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (648, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '中国公路物流运量指数', 'index_cflp_volume', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (649, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '盖世汽车-汽车行业制造企业数据库-销量数据', 'car_gasgoo_sale_rank', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (650, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '乘联会-新能源细分市场-整体市场', 'car_energy_sale_cpca', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (651, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '平均持仓', 'stock_average_position_legu', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (652, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '增发', 'stock_em_qbzf', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (653, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '配股', 'stock_em_pg', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (654, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '中国-香港-消费者物价指数', 'macro_china_hk_cpi', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (655, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '中国-香港-消费者物价指数年率', 'macro_china_hk_cpi_ratio', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (656, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '中国-香港-失业率', 'macro_china_hk_rate_of_unemployment', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (657, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '中国-香港-香港 GDP', 'macro_china_hk_gbp', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (658, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '中国-香港-香港 GDP 同比', 'macro_china_hk_gbp_ratio', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (659, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '中国-香港-香港楼宇买卖合约数量', 'macro_china_hk_building_volume', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (660, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '中国-香港-香港楼宇买卖合约成交金额', 'macro_china_hk_building_amount', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (661, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '中国-香港-香港商品贸易差额年率', 'macro_china_hk_trade_diff_ratio', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (662, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '中国-香港-香港制造业 PPI 年率', 'macro_china_hk_ppi', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (663, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '涨停板行情-涨停股池', 'stock_zt_pool_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (664, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '涨停板行情-昨日涨停股池', 'stock_zt_pool_previous_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (665, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '涨停板行情-强势股池', 'stock_zt_pool_strong_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (666, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '涨停板行情-次新股池', 'stock_zt_pool_sub_new_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (667, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '涨停板行情-炸板股池', 'stock_zt_pool_zbgc_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (668, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '涨停板行情-跌停股池', 'stock_zt_pool_dtgc_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (669, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '两网及退市', 'stock_staq_net_stop', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (670, '', 1, 0, '', '2023-10-23 07:28:14', '', '2023-10-23 07:28:14', 32, '股东户数', 'stock_zh_a_gdhs', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (671, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '股东户数详情', 'stock_zh_a_gdhs_detail_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (672, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '中行人民币牌价历史数据查询', 'currency_boc_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (673, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '盘口异动', 'stock_changes_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (674, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '板块异动', 'stock_board_change_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (675, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, 'CME 比特币成交量', 'crypto_bitcoin_cme', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (676, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '基金公司规模排名列表', 'fund_aum_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (677, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '基金市场管理规模走势图', 'fund_aum_trend_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (678, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '基金市场管理规模历史', 'fund_aum_hist_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (679, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '企业商品价格指数', 'macro_china_qyspjg', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (680, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '外商直接投资数据', 'macro_china_fdi', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (681, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '未决房屋销售月率', 'macro_usa_phs', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (682, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, 'ifo商业景气指数', 'macro_germany_ifo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (683, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '消费者物价指数月率终值', 'macro_germany_cpi_monthly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (684, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '消费者物价指数年率终值', 'macro_germany_cpi_yearly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (685, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '贸易帐(季调后)', 'macro_germany_trade_adjusted', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (686, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, 'GDP', 'macro_germany_gdp', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (687, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '实际零售销售月率', 'macro_germany_retail_sale_monthly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (688, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '实际零售销售年率', 'macro_germany_retail_sale_yearly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (689, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, 'ZEW经济景气指数', 'macro_germany_zew', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (690, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '概念板块-名称', 'stock_board_concept_name_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (691, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '概念板块-历史行情', 'stock_board_concept_hist_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (692, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '概念板块-分时历史行情', 'stock_board_concept_hist_min_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (693, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '概念板块-板块成份', 'stock_board_concept_cons_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (694, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '瑞士-宏观-SVME采购经理人指数', 'macro_swiss_svme', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (695, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '瑞士-宏观-贸易帐', 'macro_swiss_trade', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (696, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '瑞士-宏观-消费者物价指数年率', 'macro_swiss_cpi_yearly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (697, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '瑞士-宏观-GDP季率', 'macro_swiss_gdp_quarterly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (698, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '瑞士-宏观-GDP年率', 'macro_swiss_gbd_yearly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (699, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '瑞士-宏观-央行公布利率决议', 'macro_swiss_gbd_bank_rate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (700, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '日本-央行公布利率决议', 'macro_japan_bank_rate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (701, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '日本-全国消费者物价指数年率', 'macro_japan_cpi_yearly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (702, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '日本-全国核心消费者物价指数年率', 'macro_japan_core_cpi_yearly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (703, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '日本-失业率', 'macro_japan_unemployment_rate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (704, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '日本-领先指标终值', 'macro_japan_head_indicator', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (705, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '英国-Halifax 房价指数月率', 'macro_uk_halifax_monthly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (706, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '英国-Halifax 房价指数年率', 'macro_uk_halifax_yearly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (707, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '英国-贸易帐', 'macro_uk_trade', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (708, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '英国-央行公布利率决议', 'macro_uk_bank_rate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (709, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '英国-核心消费者物价指数年率', 'macro_uk_core_cpi_yearly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (710, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '英国-核心消费者物价指数月率', 'macro_uk_core_cpi_monthly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (711, '', 1, 0, '', '2023-10-23 07:28:15', '', '2023-10-23 07:28:15', 32, '英国-消费者物价指数年率', 'macro_uk_cpi_yearly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (712, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '英国-消费者物价指数月率', 'macro_uk_cpi_monthly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (713, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '英国-零售销售月率', 'macro_uk_retail_monthly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (714, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '英国-零售销售年率', 'macro_uk_retail_yearly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (715, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '英国-Rightmove 房价指数年率', 'macro_uk_rightmove_yearly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (716, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '英国-Rightmove 房价指数月率', 'macro_uk_rightmove_monthly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (717, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '英国-GDP 季率初值', 'macro_uk_gdp_quarterly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (718, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '英国-GDP 年率初值', 'macro_uk_gdp_yearly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (719, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '英国-失业率', 'macro_uk_unemployment_rate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (720, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '标的证券信息', 'stock_margin_underlying_info_szse', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (721, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '融资融券明细', 'stock_margin_detail_szse', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (722, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '融资融券汇总', 'stock_margin_szse', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (723, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '央行公布利率决议', 'macro_australia_bank_rate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (724, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '失业率', 'macro_australia_unemployment_rate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (725, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '贸易帐', 'macro_australia_trade', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (726, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '消费者物价指数季率', 'macro_australia_cpi_quarterly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (727, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '消费者物价指数年率', 'macro_australia_cpi_yearly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (728, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '生产者物价指数季率', 'macro_australia_ppi_quarterly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (729, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '零售销售月率', 'macro_australia_retail_rate_monthly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (730, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '生猪信息', 'futures_hog_info', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (731, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '生猪价格排行', 'futures_hog_rank', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (732, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '新屋开工', 'macro_canada_new_house_rate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (733, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '失业率', 'macro_canada_unemployment_rate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (734, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '贸易帐', 'macro_canada_trade', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (735, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '零售销售月率', 'macro_canada_retail_rate_monthly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (736, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '央行公布利率决议', 'macro_canada_bank_rate', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (737, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '核心消费者物价指数年率', 'macro_canada_core_cpi_yearly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (738, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '核心消费者物价指数月率', 'macro_canada_core_cpi_monthly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (739, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '消费者物价指数年率', 'macro_canada_cpi_yearly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (740, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '消费者物价指数月率', 'macro_canada_cpi_monthly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (741, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, 'GDP 月率', 'macro_canada_gdp_monthly', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (742, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '奥运奖牌', 'sport_olympic_hist', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (743, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '东方财富-港股-财务报表-三大报表', 'stock_financial_hk_report_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (744, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '东方财富-港股-财务分析-主要指标', 'stock_financial_hk_analysis_indicator_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (745, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '全部 A 股-等权重市盈率、中位数市盈率', 'stock_a_ttm_lyr', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (746, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '全部 A 股-等权重市净率、中位数市净率', 'stock_a_all_pb', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (747, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, 'REITs-行情', 'reits_realtime_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (748, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '东财-股票分时', 'stock_zh_a_hist_min_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (749, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '东财-股票盘前分时', 'stock_zh_a_hist_pre_min_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (750, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '东财-港股分时数据', 'stock_hk_hist_min_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (751, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '东财-美股分时数据', 'stock_us_hist_min_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (752, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '东财-可转债详情', 'bond_zh_cov_info', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (753, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '风险警示板', 'stock_zh_a_st_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (754, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '美股-粉单市场', 'stock_us_pink_spot_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (755, '', 1, 0, '', '2023-10-23 07:28:16', '', '2023-10-23 07:28:16', 32, '美股-知名美股', 'stock_us_famous_spot_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (756, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '股票-投资评级', 'stock_rank_forecast_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (757, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '股票-行业市盈率', 'stock_industry_pe_ratio_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (758, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '新股-新股过会', 'stock_new_gh_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (759, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '新股-IPO', 'stock_new_ipo_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (760, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '股东人数及持股集中度', 'stock_hold_num_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (761, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '实际控制人持股变动', 'stock_hold_control_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (762, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '高管持股变动明细', 'stock_hold_management_detail_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (763, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '期货手续费', 'futures_comm_info', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (764, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, 'B 股实时行情数据', 'stock_zh_b_spot', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (765, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, 'B 股历史行情数据(日频)', 'stock_zh_b_daily', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (766, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, 'B 股分时历史行情数据(分钟)', 'stock_zh_b_minute', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (767, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '公司治理-对外担保', 'stock_cg_guarantee_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (768, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '公司治理-公司诉讼', 'stock_cg_lawsuit_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (769, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '公司治理-股权质押', 'stock_cg_equity_mortgage_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (770, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '债券报表-债券发行-国债发行', 'bond_treasure_issue_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (771, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '债券报表-债券发行-地方债', 'bond_local_government_issue_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (772, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '债券报表-债券发行-企业债', 'bond_corporate_issue_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (773, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '债券报表-债券发行-可转债发行', 'bond_cov_issue_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (774, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '债券报表-债券发行-可转债转股', 'bond_cov_stock_issue_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (775, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '基金报表-基金重仓股', 'fund_report_stock_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (776, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '公告大全-沪深 A 股公告', 'stock_notice_report', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (777, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '基金报表-基金行业配置', 'fund_report_industry_allocation_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (778, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '基金报表-基金资产配置', 'fund_report_asset_allocation_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (779, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '基金规模-开放式基金', 'fund_scale_open_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (780, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '基金规模-封闭式基金', 'fund_scale_close_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (781, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '基金规模-分级子基金', 'fund_scale_structured_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (782, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '指数估值', 'index_value_hist_funddb', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (783, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '沪深港通持股-具体股票', 'stock_hsgt_individual_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (784, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '沪深港通持股-具体股票-详情', 'stock_hsgt_individual_detail_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (785, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, 'IPO 受益股', 'stock_ipo_benefit_ths', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (786, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '创新高', 'stock_rank_cxg_ths', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (787, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '创新低', 'stock_rank_cxd_ths', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (788, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '连续上涨', 'stock_rank_lxsz_ths', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (789, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '连续下跌', 'stock_rank_lxxd_ths', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (790, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '持续放量', 'stock_rank_cxfl_ths', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (791, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '持续缩量', 'stock_rank_cxsl_ths', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (792, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '向上突破', 'stock_rank_xstp_ths', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (793, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '向下突破', 'stock_rank_xxtp_ths', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (794, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '量价齐升', 'stock_rank_ljqs_ths', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (795, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '量价齐跌', 'stock_rank_ljqd_ths', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (796, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '险资举牌', 'stock_rank_xzjp_ths', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (797, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '可转债分时数据', 'bond_zh_hs_cov_min', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (798, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '可转债分时数据-分时行情-盘前', 'bond_zh_hs_cov_pre_min', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (799, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '艺人商业价值', 'business_value_artist', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (800, '', 1, 0, '', '2023-10-23 07:28:17', '', '2023-10-23 07:28:17', 32, '艺人流量价值', 'online_value_artist', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (801, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '电视剧集', 'video_tv', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (802, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '综艺节目', 'video_variety_show', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (803, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '基金拆分', 'fund_cf_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (804, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '基金分红排行', 'fund_fh_rank_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (805, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '基金分红', 'fund_fh_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (806, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '规模变动', 'fund_scale_change_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (807, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '持有人结构', 'fund_hold_structure_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (808, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '行业板块-板块成份', 'stock_board_industry_cons_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (809, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '行业板块-历史行情', 'stock_board_industry_hist_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (810, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '行业板块-分时历史行情', 'stock_board_industry_hist_min_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (811, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '行业板块-板块名称', 'stock_board_industry_name_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (812, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '股票回购数据', 'stock_repurchase_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (813, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '期货品种字典', 'futures_hq_subscribe_exchange_symbol', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (814, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '上海黄金交易所-历史行情走势', 'spot_hist_sge', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (815, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '上海金基准价', 'spot_golden_benchmark_sge', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (816, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '上海银基准价', 'spot_silver_benchmark_sge', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (817, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '个股信息查询', 'stock_individual_info_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (818, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '中国食糖指数', 'index_sugar_msweet', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (819, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '配额内进口糖估算指数', 'index_inner_quote_sugar_msweet', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (820, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '配额外进口糖估算指数', 'index_outer_quote_sugar_msweet', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (821, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '股东持股分析-十大流通股东', 'stock_gdfx_free_holding_analyse_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (822, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '股东持股分析-十大股东', 'stock_gdfx_holding_analyse_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (823, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '东方财富网-个股-十大流通股东', 'stock_gdfx_free_top_10_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (824, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '东方财富网-个股-十大股东', 'stock_gdfx_top_10_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (825, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '股东持股明细-十大流通股东', 'stock_gdfx_free_holding_detail_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (826, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '股东持股明细-十大股东', 'stock_gdfx_holding_detail_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (827, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '股东持股变动统计-十大流通股东', 'stock_gdfx_free_holding_change_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (828, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '股东持股变动统计-十大股东', 'stock_gdfx_holding_change_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (829, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '股东持股统计-十大流通股东', 'stock_gdfx_free_holding_statistics_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (830, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '股东持股统计-十大股东', 'stock_gdfx_holding_statistics_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (831, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '股东协同-十大流通股东', 'stock_gdfx_free_holding_teamwork_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (832, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '股东协同-十大股东', 'stock_gdfx_holding_teamwork_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (833, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '期权龙虎榜', 'option_lhb_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (834, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '期权价值分析', 'option_value_analysis_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (835, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '期权风险分析', 'option_risk_analysis_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (836, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '期权折溢价分析', 'option_premium_analysis_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (837, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '财新数据-指数报告-财新中国 PMI-综合 PMI', 'index_pmi_com_cx', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (838, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '财新数据-指数报告-财新中国 PMI-制造业 PMI', 'index_pmi_man_cx', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (839, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '财新数据-指数报告-财新中国 PMI-服务业 PMI', 'index_pmi_ser_cx', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (840, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '财新数据-指数报告-数字经济指数', 'index_dei_cx', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (841, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '财新数据-指数报告-产业指数', 'index_ii_cx', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (842, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '财新数据-指数报告-溢出指数', 'index_si_cx', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (843, '', 1, 0, '', '2023-10-23 07:28:18', '', '2023-10-23 07:28:18', 32, '财新数据-指数报告-融合指数', 'index_fi_cx', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (844, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '财新数据-指数报告-基础指数', 'index_bi_cx', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (845, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '财新数据-指数报告-中国新经济指数', 'index_nei_cx', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (846, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '财新数据-指数报告-劳动力投入指数', 'index_li_cx', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (847, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '财新数据-指数报告-资本投入指数', 'index_ci_cx', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (848, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '财新数据-指数报告-科技投入指数', 'index_ti_cx', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (849, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '财新数据-指数报告-新经济行业入职平均工资水平', 'index_neaw_cx', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (850, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '财新数据-指数报告-新经济入职工资溢价水平', 'index_awpr_cx', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (851, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '财新数据-指数报告-大宗商品指数', 'index_cci_cx', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (852, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '冬奥会-历届奖牌榜', 'sport_olympic_winter_hist', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (853, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '中国股票指数历史数据', 'index_zh_a_hist', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (854, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '中国股票指数-指数分时数据', 'index_zh_a_hist_min_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (855, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '东方财富-个股人气榜-人气榜', 'stock_hot_rank_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (856, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '东方财富-个股人气榜-飙升榜', 'stock_hot_up_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (857, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '东方财富-个股人气榜-历史趋势及粉丝特征', 'stock_hot_rank_detail_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (858, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '东方财富-个股人气榜-实时变动', 'stock_hot_rank_detail_realtime_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (859, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '东方财富-个股人气榜-关键词', 'stock_hot_keyword_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (860, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '东方财富-个股人气榜-最新排名', 'stock_hot_rank_latest_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (861, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '东方财富-个股人气榜-相关股票', 'stock_hot_rank_relate_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (862, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '东方财富-个股人气榜-人气榜-港股', 'stock_hk_hot_rank_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (863, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '东方财富-个股人气榜-历史趋势-港股', 'stock_hk_hot_rank_detail_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (864, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '东方财富-个股人气榜-实时变动-港股', 'stock_hk_hot_rank_detail_realtime_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (865, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '东方财富-个股人气榜-最新排名-港股', 'stock_hk_hot_rank_latest_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (866, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '东方财富网-数据中心-龙虎榜单-龙虎榜详情', 'stock_lhb_detail_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (867, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '东方财富网-数据中心-龙虎榜单-个股上榜统计', 'stock_lhb_stock_statistic_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (868, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '东方财富网-数据中心-龙虎榜单-个股龙虎榜详情', 'stock_lhb_stock_detail_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (869, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '东方财富网-数据中心-龙虎榜单-机构买卖每日统计', 'stock_lhb_jgmmtj_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (870, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '东方财富网-数据中心-龙虎榜单-每日活跃营业部', 'stock_lhb_hyyyb_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (871, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '东方财富网-数据中心-龙虎榜单-营业部排行', 'stock_lhb_yybph_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (872, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '东方财富网-数据中心-龙虎榜单-机构席位追踪', 'stock_lhb_jgstatistic_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (873, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '东方财富网-数据中心-龙虎榜单-营业部统计', 'stock_lhb_traderstatistic_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (874, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '天天基金网-基金档案-投资组合-基金持仓', 'fund_portfolio_hold_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (875, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '天天基金网-基金档案-投资组合-债券持仓', 'fund_portfolio_bond_hold_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (876, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '天天基金网-基金档案-投资组合-重大变动', 'fund_portfolio_change_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (877, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '天天基金网-基金档案-投资组合-行业配置', 'fund_portfolio_industry_allocation_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (878, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '原保险保费收入', 'macro_china_insurance_income', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (879, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '手机出货量', 'macro_china_mobile_number', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (880, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '菜篮子产品批发价格指数', 'macro_china_vegetable_basket', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (881, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '农产品批发价格总指数', 'macro_china_agricultural_product', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (882, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '农副指数', 'macro_china_agricultural_index', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (883, '', 1, 0, '', '2023-10-23 07:28:19', '', '2023-10-23 07:28:19', 32, '能源指数', 'macro_china_energy_index', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (884, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '大宗商品价格', 'macro_china_commodity_price_index', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (885, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '费城半导体指数', 'macro_global_sox_index', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (886, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '义乌小商品指数-电子元器件', 'macro_china_yw_electronic_index', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (887, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '建材指数', 'macro_china_construction_index', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (888, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '建材价格指数', 'macro_china_construction_price_index', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (889, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '物流景气指数', 'macro_china_lpi_index', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (890, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '原油运输指数', 'macro_china_bdti_index', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (891, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '超灵便型船运价指数', 'macro_china_bsi_index', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (892, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '可转债价值分析', 'bond_zh_cov_value_analysis', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (893, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '相关系数矩阵', 'futures_correlation_nh', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (894, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '板块指数涨跌', 'futures_board_index_nh', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (895, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '品种指数涨跌', 'futures_variety_index_nh', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (896, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '雪球-沪深股市-热度排行榜-关注排行榜', 'stock_hot_follow_xq', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (897, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '雪球-沪深股市-热度排行榜-讨论排行榜', 'stock_hot_tweet_xq', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (898, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '雪球-沪深股市-热度排行榜-分享交易排行榜', 'stock_hot_deal_xq', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (899, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '淘股吧-热门股票', 'stock_hot_tgb', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (900, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '内部交易', 'stock_inner_trade_xq', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (901, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '东方财富-股票-财务分析-资产负债表-按报告期', 'stock_balance_sheet_by_report_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (902, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '东方财富-股票-财务分析-资产负债表-按年度', 'stock_balance_sheet_by_yearly_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (903, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '东方财富-股票-财务分析-利润表-报告期', 'stock_profit_sheet_by_report_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (904, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '东方财富-股票-财务分析-利润表-按年度', 'stock_profit_sheet_by_yearly_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (905, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '东方财富-股票-财务分析-利润表-按单季度', 'stock_profit_sheet_by_quarterly_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (906, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '东方财富-股票-财务分析-现金流量表-按报告期', 'stock_cash_flow_sheet_by_report_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (907, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '东方财富-股票-财务分析-现金流量表-按年度', 'stock_cash_flow_sheet_by_yearly_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (908, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '东方财富-股票-财务分析-现金流量表-按单季度', 'stock_cash_flow_sheet_by_quarterly_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (909, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '宏观-全球事件', 'news_economic_baidu', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (910, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '停复牌', 'news_trade_notify_suspend_baidu', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (911, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '财报发行', 'news_report_time_baidu', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (912, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '上海证券交易所-产品-股票期权-期权风险指标', 'option_risk_indicator_sse', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (913, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '人民币汇率中间价', 'currency_boc_safe', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (914, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '主营构成-益盟', 'stock_zygc_ym', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (915, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '主营构成-东财', 'stock_zygc_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (916, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '管理层讨论与分析', 'stock_mda_ym', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (917, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '巨潮资讯-行业分类数据', 'stock_industry_category_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (918, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '巨潮资讯-上市公司行业归属的变动情况', 'stock_industry_change_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (919, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '巨潮资讯-公司股本变动', 'stock_share_change_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (920, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '咨询-财联社-今日快讯', 'stock_zh_a_alerts_cls', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (921, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '咨询-财联社-电报', 'stock_telegraph_cls', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (922, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '上海金属网-快讯', 'futures_news_shmet', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (923, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '分红配股', 'news_trade_notify_dividend_baidu', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (924, '', 1, 0, '', '2023-10-23 07:28:20', '', '2023-10-23 07:28:20', 32, '中债-新综合指数', 'bond_new_composite_index_cbond', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (925, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '中债-综合指数', 'bond_composite_index_cbond', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (926, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '深港通-港股通业务信息-结算汇率', 'stock_sgt_settlement_exchange_rate_szse', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (927, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '深港通-港股通业务信息-参考汇率', 'stock_sgt_reference_exchange_rate_szse', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (928, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '沪港通-港股通信息披露-参考汇率', 'stock_sgt_reference_exchange_rate_sse', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (929, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '沪港通-港股通信息披露-结算汇兑', 'stock_sgt_settlement_exchange_rate_sse', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (930, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '配股实施方案-巨潮资讯', 'stock_allotment_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (931, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '巨潮资讯-个股-公司概况', 'stock_profile_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (932, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '巨潮资讯-个股-上市相关', 'stock_ipo_summary_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (933, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '百度股市通-港股-财务报表-估值数据', 'stock_hk_valuation_baidu', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (934, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '百度股市通-A 股-财务报表-估值数据', 'stock_zh_valuation_baidu', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (935, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '百度股市通- A 股或指数-股评-投票', 'stock_zh_vote_baidu', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (936, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '百度股市通-期货-新闻', 'futures_news_baidu', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (937, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '百度股市通-热搜股票', 'stock_hot_search_baidu', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (938, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '乐估乐股-底部研究-巴菲特指标', 'stock_buffett_index_lg', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (939, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '百度股市通-外汇-行情榜单', 'fx_quote_baidu', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (940, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '50ETF 期权波动率指数', 'index_option_50etf_qvix', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (941, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '50ETF 期权波动率指数 QVIX-分时', 'index_option_50etf_min_qvix', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (942, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '300 ETF 期权波动率指数', 'index_option_300etf_qvix', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (943, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '300 ETF 期权波动率指数 QVIX-分时', 'index_option_300etf_min_qvix', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (944, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '申万指数实时行情', 'index_realtime_sw', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (945, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '申万指数历史行情', 'index_hist_sw', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (946, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '申万宏源研究-行业分类-全部行业分类', 'stock_industry_clf_hist_sw', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (947, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '申万指数分时行情', 'index_min_sw', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (948, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '申万指数成分股', 'index_component_sw', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (949, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '申万宏源研究-指数分析-日报表', 'index_analysis_daily_sw', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (950, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '申万宏源研究-指数分析-周报表', 'index_analysis_weekly_sw', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (951, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '申万宏源研究-指数分析-月报表', 'index_analysis_monthly_sw', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (952, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '申万宏源研究-指数分析-周/月-日期序列', 'index_analysis_week_month_sw', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (953, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '中国外汇交易中心暨全国银行间同业拆借中心-债券-信息查询结果', 'bond_info_cm', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (954, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '中国外汇交易中心暨全国银行间同业拆借中心-债券-债券详情', 'bond_info_detail_cm', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (955, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '生猪市场价格指数', 'index_hog_spot_price', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (956, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '乐咕乐股-股息率-A 股股息率', 'stock_a_gxl_lg', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (957, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '乐咕乐股-股息率-恒生指数股息率', 'stock_hk_gxl_lg', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (958, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '乐咕乐股-大盘拥挤度', 'stock_a_congestion_lg', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (959, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '乐咕乐股-基金仓位-股票型基金仓位', 'fund_stock_position_lg', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (960, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '乐咕乐股-基金仓位-平衡混合型基金仓位', 'fund_balance_position_lg', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (961, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '乐咕乐股-基金仓位-灵活配置型基金仓位', 'fund_linghuo_position_lg', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (962, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '主营介绍', 'stock_zyjs_ths', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (963, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '东方财富-行情报价', 'stock_bid_ask_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (964, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '同花顺-数据中心-可转债', 'bond_zh_cov_info_ths', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (965, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '新浪财经-行情中心-港股指数', 'stock_hk_index_spot_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (966, '', 1, 0, '', '2023-10-23 07:28:21', '', '2023-10-23 07:28:21', 32, '新浪财经-港股指数-历史行情数据', 'stock_hk_index_daily_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (967, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '东方财富网-行情中心-港股-指数实时行情', 'stock_hk_index_spot_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (968, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '东方财富网-港股-股票指数数据', 'stock_hk_index_daily_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (969, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '同花顺-财务指标-主要指标', 'stock_financial_abstract_ths', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (970, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '东方财富-LOF 行情', 'fund_lof_hist_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (971, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '东方财富-LOF 实时行情', 'fund_lof_spot_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (972, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '东方财富-LOF 分时行情', 'fund_lof_hist_min_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (973, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '新浪财经-ESG评级中心-ESG评级-ESG评级数据', 'stock_esg_rate_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (974, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '新浪财经-ESG评级中心-ESG评级-华证指数', 'stock_esg_hz_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (975, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '东方财富网站-天天基金网-基金档案-基金公告-人事调整', 'fund_announcement_personnel_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (976, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '互动易-提问', 'stock_irm_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (977, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '互动易-回答', 'stock_irm_ans_cninfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (978, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '上证e互动-提问与回答', 'stock_sns_sseinfo', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (979, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '新浪财经-债券-可转债-详情资料', 'bond_cb_profile_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (980, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '新浪财经-债券-可转债-债券概况', 'bond_cb_summary_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (981, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '东方财富网-数据中心-特色数据-高管持股-董监高及相关人员持股变动明细', 'stock_hold_management_detail_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (982, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '东方财富网-数据中心-特色数据-高管持股-人员增减持股变动明细', 'stock_hold_management_person_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (983, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '东方财富网-数据中心-股市日历-公司动态', 'stock_gsrl_gsdt_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (984, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '东方财富网-数据中心-股东大会', 'stock_gddh_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (985, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '重大合同明细', 'stock_zdhtmx_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (986, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '个股研报', 'stock_research_report_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (987, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '董监高及相关人员持股变动-上海证券交易所', 'stock_share_hold_change_sse', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (988, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '董监高及相关人员持股变动-深圳证券交易所', 'stock_share_hold_change_szse', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (989, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '董监高及相关人员持股变动-北京证券交易所', 'stock_share_hold_change_bse', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (990, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '国家统计局全国数据通用接口', 'macro_china_nbs_nation', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (991, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '国家统计局地区数据通用接口', 'macro_china_nbs_region', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (992, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '新浪财经-美股指数行情', 'index_us_stock_sina', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (993, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '融资融券-标的证券名单及保证金比例查询', 'stock_margin_ratio_pa', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (994, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '东财财富-日内分时数据', 'stock_intraday_em', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (995, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '同花顺-板块-概念板块-概念图谱', 'stock_board_concept_graph_ths', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (996, '', 1, 0, '', '2023-10-23 07:28:22', '', '2023-10-23 07:28:22', 32, '恐惧贪婪指数', 'index_fear_greed_funddb', '{}', 1);
INSERT INTO `sys_dict_item` VALUES (997, '', 1, 0, 'admin', '2023-10-24 01:29:03', '', '2023-10-24 01:29:03', 18, 'akshare数据接口', 'akshare_api', '{}', 1);
COMMIT;

-- ----------------------------
-- Table structure for sys_file
-- ----------------------------
DROP TABLE IF EXISTS `sys_file`;
CREATE TABLE `sys_file` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'id主键',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '简介',
  `sort_no` float DEFAULT NULL COMMENT '排序',
  `del_flag` smallint DEFAULT NULL COMMENT '软删除标记',
  `create_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建者',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '修改者',
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `file_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '文件名称',
  `url` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '文件地址',
  `file_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '文档类型（folder:文件夹 excel:excel doc:word ppt:ppt image:图片  archive:其他文档 video:视频 pdf:pdf）',
  `store_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '文件上传类型(temp/本地上传(临时文件) manage/知识库)',
  `parent_id` int DEFAULT NULL COMMENT '父级id',
  `tenant_id` int DEFAULT NULL COMMENT '租户id',
  `file_size` float DEFAULT NULL COMMENT '文件大小（kb）',
  `iz_folder` smallint DEFAULT NULL COMMENT '是否文件夹(1：是  0：否)',
  `iz_root_folder` smallint DEFAULT NULL COMMENT '是否为1级文件夹，允许为空 (1：是 )',
  `iz_star` smallint DEFAULT NULL COMMENT '是否标星(1：是  0：否)',
  `down_count` int DEFAULT NULL COMMENT '下载次数',
  `read_count` int DEFAULT NULL COMMENT '阅读次数',
  `share_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '分享链接',
  `share_perms` smallint DEFAULT NULL COMMENT '分享权限(1.关闭分享 2.允许所有联系人查看 3.允许任何人查看)',
  `enable_down` smallint DEFAULT NULL COMMENT '是否允许下载(1：是  0：否)',
  `enable_update` smallint DEFAULT NULL COMMENT '是否允许修改(1：是  0：否)',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Records of sys_file
-- ----------------------------
BEGIN;
INSERT INTO `sys_file` VALUES (1, '', 1, 0, 'admin', '2023-08-23 03:30:06', '', '2023-08-23 03:30:06', 'flink.png', 'http://110.40.157.36:9000/ezdata/1e8b13823bef5a22d695a17a8cae3268.png', 'png', NULL, NULL, NULL, NULL, 0, 0, 0, 0, 0, NULL, 0, 0, 0);
COMMIT;

-- ----------------------------
-- Table structure for sys_notice
-- ----------------------------
DROP TABLE IF EXISTS `sys_notice`;
CREATE TABLE `sys_notice` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'id主键',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '简介',
  `sort_no` float DEFAULT NULL COMMENT '排序',
  `del_flag` smallint DEFAULT NULL COMMENT '软删除标记',
  `create_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建者',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '修改者',
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `title` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '标题',
  `msg_content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '内容',
  `start_time` int DEFAULT NULL COMMENT '开始时间',
  `end_time` int DEFAULT NULL COMMENT '结束时间',
  `sender` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '发送人',
  `priority` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '优先级（L低，M中，H高）',
  `msg_category` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '消息类型1:通知公告2:系统消息',
  `msg_type` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '通告对象类型（USER:指定用户，ALL:全体用户）',
  `send_status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '发布状态（0未发布，1已发布，2已撤销）',
  `send_time` int DEFAULT NULL COMMENT '发送时间',
  `cancel_time` int DEFAULT NULL COMMENT '撤销时间',
  `bus_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '业务类型(email:邮件 bpm:流程)',
  `bus_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '业务id',
  `open_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '打开方式(组件：component 路由：url)',
  `open_page` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '组件/路由 地址',
  `user_ids` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '指定用户',
  `msg_abstract` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '摘要',
  `dt_task_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '钉钉task_id，用于撤回消息',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Records of sys_notice
-- ----------------------------
BEGIN;
INSERT INTO `sys_notice` VALUES (9, '', 1, 0, '', '2023-10-24 07:01:42', 'system', '2023-10-24 07:01:42', '任务失败告警策略', '普通任务失败告警:失败任务示例 在重试2次后仍失败。任务报错：/Users/xuwei/Desktop/code/ezdata/ezdata/tasks/normal_task.py:48:division by zero', 1698102102, NULL, 'system', 'M', '2', 'USER', '1', 1698130902, NULL, NULL, NULL, NULL, NULL, '[\"1\", \"8\", \"7\"]', '系统告警转通知', NULL);
INSERT INTO `sys_notice` VALUES (10, '', 1, 0, '', '2023-10-24 07:01:42', 'system', '2023-10-24 07:01:42', '任务失败告警策略', '普通任务失败告警:失败任务示例 在重试2次后仍失败。任务报错：/Users/xuwei/Desktop/code/ezdata/ezdata/tasks/normal_task.py:48:division by zero', 1698102102, NULL, 'system', 'M', '2', 'USER', '1', 1698130902, NULL, NULL, NULL, NULL, NULL, '[\"1\", \"8\", \"7\"]', '系统告警转通知', NULL);
COMMIT;

-- ----------------------------
-- Table structure for sys_notice_send
-- ----------------------------
DROP TABLE IF EXISTS `sys_notice_send`;
CREATE TABLE `sys_notice_send` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'id主键',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '简介',
  `sort_no` float DEFAULT NULL COMMENT '排序',
  `del_flag` smallint DEFAULT NULL COMMENT '软删除标记',
  `create_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建者',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '修改者',
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `notice_id` int DEFAULT NULL COMMENT '通知id',
  `user_id` int DEFAULT NULL COMMENT '用户id',
  `read_flag` smallint DEFAULT NULL COMMENT '阅读状态（0未读，1已读）',
  `star_flag` smallint DEFAULT NULL COMMENT '标星状态( 1为标星 空/0没有标星)',
  `read_time` int DEFAULT NULL COMMENT '阅读时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=42 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Records of sys_notice_send
-- ----------------------------
BEGIN;
INSERT INTO `sys_notice_send` VALUES (36, '', 1, 0, 'system', '2023-10-24 07:01:42', '', '2023-10-24 07:01:42', 9, 1, 0, 0, NULL);
INSERT INTO `sys_notice_send` VALUES (37, '', 1, 0, 'system', '2023-10-24 07:01:42', '', '2023-10-24 07:01:42', 10, 1, 0, 0, NULL);
INSERT INTO `sys_notice_send` VALUES (38, '', 1, 0, 'system', '2023-10-24 07:01:42', '', '2023-10-24 07:01:42', 9, 8, 0, 0, NULL);
INSERT INTO `sys_notice_send` VALUES (39, '', 1, 0, 'system', '2023-10-24 07:01:42', '', '2023-10-24 07:01:42', 10, 8, 0, 0, NULL);
INSERT INTO `sys_notice_send` VALUES (40, '', 1, 0, 'system', '2023-10-24 07:01:42', '', '2023-10-24 07:01:42', 9, 7, 0, 0, NULL);
INSERT INTO `sys_notice_send` VALUES (41, '', 1, 0, 'system', '2023-10-24 07:01:42', '', '2023-10-24 07:01:42', 10, 7, 0, 0, NULL);
COMMIT;

-- ----------------------------
-- Table structure for sys_permission
-- ----------------------------
DROP TABLE IF EXISTS `sys_permission`;
CREATE TABLE `sys_permission` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'id主键',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '简介',
  `sort_no` float DEFAULT NULL COMMENT '排序',
  `del_flag` smallint DEFAULT NULL COMMENT '软删除标记',
  `create_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建者',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '修改者',
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '名称',
  `parent_id` int DEFAULT NULL COMMENT '父级ID',
  `url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '路径',
  `component` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '组件',
  `component_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '组件名称',
  `redirect` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '一级菜单跳转地址',
  `menu_type` smallint DEFAULT NULL COMMENT '菜单类型(0:一级菜单 1:子菜单:2:按钮权限)',
  `perms` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '菜单权限编码',
  `perms_type` smallint DEFAULT NULL COMMENT '权限策略1显示2禁用',
  `always_show` smallint DEFAULT NULL COMMENT '聚合子路由: 1是0否',
  `icon` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '菜单图标',
  `is_route` smallint DEFAULT NULL COMMENT '是否路由菜单: 0:不是  1:是（默认值1）',
  `is_leaf` smallint DEFAULT NULL COMMENT '是否叶子节点: 1:是   0:不是',
  `keep_alive` smallint DEFAULT NULL COMMENT '是否缓存该页面:   1:是   0:不是',
  `hidden` smallint DEFAULT NULL COMMENT '是否隐藏路由: 0否,1是',
  `hide_tab` smallint DEFAULT NULL COMMENT '是否隐藏tab: 0否,1是',
  `rule_flag` smallint DEFAULT NULL COMMENT '是否添加数据权限1是0否',
  `status` smallint DEFAULT NULL COMMENT '按钮权限状态(0无效1有效)',
  `internal_or_external` smallint DEFAULT NULL COMMENT '外链菜单打开方式 0/内部打开 1/外部打开',
  PRIMARY KEY (`id`),
  KEY `ix_sys_permission_name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=120 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Records of sys_permission
-- ----------------------------
BEGIN;
INSERT INTO `sys_permission` VALUES (1, '', 10, 0, 'admin', '2022-11-01 07:39:03', 'admin', '2023-05-05 06:35:57', '概览', NULL, '/dashboard', 'layouts/default/index', '', '/dashboard/analysis', 0, NULL, 1, 0, 'ant-design:appstore-outlined', 1, 0, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (2, '', 1, 0, 'admin', '2022-11-01 07:39:59', 'admin', '2023-05-05 06:14:46', '工作台', 1, '/dashboard/workbench', 'dashboard/workbench/index', '', '', 1, NULL, 1, 0, 'ant-design:appstore-twotone', 1, 1, 0, 1, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (3, '', 1, 0, 'admin', '2022-11-01 07:41:16', 'admin', '2023-05-05 06:28:03', '首页', 1, '/dashboard/analysis', 'dashboard/Analysis', '', '', 1, NULL, 1, 0, 'ant-design:bank-filled', 1, 1, 1, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (4, '', 1, 0, 'admin', '2022-11-01 07:42:49', 'admin', '2023-04-19 17:28:17', '系统管理', NULL, '/system', 'layouts/default/index', '', '', 0, NULL, 1, 0, 'setting|svg', 1, 0, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (5, '', 2.99, 0, 'admin', '2022-11-01 07:45:52', 'admin', '2022-11-02 03:11:09', '用户管理', 4, '/system/user', 'system/user/index', '', '', 1, NULL, 1, 0, 'ant-design:user-outlined', 1, 1, 1, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (6, '', 1, 0, 'admin', '2022-11-01 07:46:23', 'admin', '2023-04-28 07:26:15', '用户编辑', 5, '', '', '', '', 2, 'user:edit', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (7, '', 1, 0, 'admin', '2022-11-01 07:46:53', '', '2022-11-02 03:11:09', '新增用户', 5, '', '', '', '', 2, 'user:add', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (10, '', 2.98, 0, 'admin', '2022-11-01 07:48:44', 'admin', '2022-11-02 03:11:09', '角色管理', 4, '/system/role', 'system/role/index', '', '', 1, NULL, 1, 0, 'ant-design:solution-outlined', 1, 1, 1, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (11, '', 2.97, 0, 'admin', '2022-11-01 08:27:04', 'admin', '2022-11-02 03:11:09', '菜单管理', 4, '/system/menu', 'system/menu/index', '', '', 1, NULL, 1, 0, 'ant-design:menu-fold-outlined', 1, 1, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (12, '', 2.96, 0, 'admin', '2022-11-01 08:31:42', 'admin', '2022-11-11 05:42:49', '部门管理', 4, '/system/depart', 'system/depart/index', '', '', 1, NULL, 1, 0, 'ant-design:team-outlined', 1, 1, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (13, '', 2.95, 0, 'admin', '2022-11-01 08:32:25', 'admin', '2022-11-02 03:11:09', '我的部门', 4, '/system/depart-user', 'system/departUser/index', '', '', 1, NULL, 1, 0, 'ant-design:home-outlined', 1, 1, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (14, '', 2.94, 0, 'admin', '2022-11-01 08:33:07', 'admin', '2023-07-11 08:39:31', '职务管理', 4, '/system/position', 'system/position/index', '', '', 1, NULL, 1, 0, 'ant-design:database-filled', 1, 0, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (15, '', 2.93, 0, 'admin', '2022-11-01 08:34:10', 'admin', '2022-11-02 03:11:10', '通知公告', 4, '/system/notice', 'system/notice/index', '', '', 1, NULL, 1, 0, 'ant-design:bell-outlined', 1, 1, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (16, '', 2.92, 0, 'admin', '2022-11-01 08:34:46', 'admin', '2022-11-02 03:11:10', '数据字典', 4, '/system/dict', 'system/dict/index', '', '', 1, NULL, 1, 0, 'ant-design:hdd-twotone', 1, 1, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (17, '', 2.91, 0, 'admin', '2022-11-01 08:35:30', 'admin', '2022-11-11 05:42:51', '对象存储', 4, '/system/ossfile', 'system/ossfile/index', '', '', 1, NULL, 1, 0, 'ant-design:file-add-outlined', 1, 1, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (18, '', 3, 0, 'admin', '2022-11-01 09:27:13', 'admin', '2022-11-09 01:40:15', '个人中心', 4, '/system/account/setting', 'system/account/setting/index', '', '', 1, NULL, 1, 0, 'ant-design:user-outlined', 1, 1, 0, 1, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (19, '', 2.945, 0, 'admin', '2022-11-10 06:10:27', 'admin', '2022-11-10 06:10:59', '租户管理', 4, '/system/tenant', 'system/tenant/index', '', '', 1, NULL, 1, 0, 'ant-design:appstore-twotone', 1, 1, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (20, '', 9.3, 0, 'admin', '2023-12-23 16:20:54', 'admin', '2023-12-23 16:24:45', '数据可视化', NULL, '/visualization', 'layouts/default/index', '', '', 0, NULL, 1, 0, 'chart|svg', 1, 0, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (21, '', 1, 0, 'admin', '2022-11-16 14:06:40', 'admin', '2023-04-15 08:12:43', '大屏设计器', 20, '/visualization/bigscreen', '{{ window._CONFIG[\'domianURL\'] }}/bigscreen/#/token_login?token=${token}', '', '', 1, NULL, 1, 0, 'ant-design:dot-chart-outlined', 1, 1, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (22, '', 1, 0, '2222', '2022-11-19 19:23:40', 'admin', '2023-05-04 09:33:18', '部门用户管理', 13, '', '', '', '', 2, 'user-depart:user', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (23, '', 8, 0, 'admin', '2022-11-21 16:11:58', 'admin', '2023-04-19 17:27:27', '开发工具', NULL, '/devtools', 'layouts/default/index', '', '', 0, NULL, 1, 0, 'dev|svg', 1, 0, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (24, '', 10, 0, 'admin', '2022-11-21 16:16:20', '', '2022-11-21 16:16:20', '代码生成器', 23, '/devtools/code-generator', 'devtools/codeGenerator/index', '', '', 1, NULL, 1, 0, 'ant-design:code-outlined', 1, 1, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (25, '', 9.5, 0, 'admin', '2022-12-16 02:33:48', 'admin', '2023-04-20 07:44:56', '数据管理', NULL, '/dataManage', 'layouts/default/index', '', '', 0, NULL, 1, 0, 'datamanage|svg', 1, 0, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (26, '', 9.9, 0, 'admin', '2022-12-16 02:34:43', 'admin', '2023-04-20 07:45:04', '数据源管理', 25, '/dataManage/dataSource/index', '/dataManage/dataSource/index', '', '', 1, NULL, 1, 0, 'datasource|svg', 1, 1, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (27, '', 9.8, 0, 'admin', '2022-12-19 15:32:22', 'admin', '2023-04-20 07:47:48', '数据模型管理', 25, '/dataManage/dataModel', '/dataManage/dataModel/index', '', '', 1, NULL, 1, 0, 'datamodel|svg', 1, 1, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (28, '', 1, 0, 'admin', '2023-01-28 09:05:13', 'admin', '2023-04-20 07:50:17', '数据查询', 25, '/dataManage/dataQuery', '/dataManage/dataQuery/index', '', '', 1, NULL, 1, 0, 'dataquery|svg', 1, 1, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (31, '', 9.4, 0, 'admin', '2023-03-05 17:12:27', 'admin', '2023-04-19 17:24:27', '任务调度', NULL, '/task', 'layouts/default/index', '', '', 0, NULL, 1, 0, 'task|svg', 1, 0, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (32, '', 9, 0, 'admin', '2023-03-06 02:28:58', 'admin', '2023-04-20 07:52:21', '任务模版管理', 31, '/task/task_template', '/task/task_template/index', '', '', 1, NULL, 1, 0, 'task_template|svg', 1, 1, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (33, '', 8, 0, 'admin', '2023-03-08 03:36:25', 'admin', '2023-04-20 07:56:27', '普通任务调度', 31, '/task/index', '/task/index', '', '', 1, NULL, 1, 0, 'task|svg', 1, 1, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (34, '', 1, 0, 'admin', '2023-03-11 04:32:24', 'admin', '2023-04-19 17:14:51', '任务工作流调度', 31, '/task/dag', '/task/dag_task/index', '', '', 1, NULL, 1, 0, 'dag_task|svg', 1, 1, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (35, '', 1, 0, 'admin', '2023-03-13 16:35:00', 'admin', '2023-03-14 09:49:30', '任务工作流详情', 31, '/task/dag/detail', '/task/dag_task/dag-editor/index', '', '', 1, NULL, 1, 0, NULL, 1, 1, 0, 1, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (37, '', 1, 0, 'admin', '2023-04-03 13:00:54', 'admin', '2023-04-20 07:49:24', '算法管理', 25, '/algorithm/index', '/algorithm/index', '', '', 1, NULL, 1, 0, 'algorithm|svg', 1, 1, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (38, '', 9.1, 0, 'admin', '2023-04-11 17:37:35', 'admin', '2023-06-19 16:54:57', '运维监控', NULL, '/ops', 'layouts/default/index', '', '', 0, NULL, 1, 0, 'ops|svg', 1, 0, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (39, '', 1, 0, 'admin', '2023-04-11 17:38:12', 'admin', '2023-04-20 08:02:26', 'worker管理', 38, '/ops/worker', '/ops/workerManage/index', '', '', 1, NULL, 1, 0, 'worker|svg', 1, 1, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (40, '', 1, 0, 'admin', '2023-04-12 06:24:56', 'admin', '2023-04-20 07:58:53', '定时job管理', 38, '/ops/job', '/ops/jobManage/index', '', '', 1, NULL, 1, 0, 'job|svg', 1, 1, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (41, '', 1, 0, 'admin', '2023-04-13 07:54:08', 'admin', '2023-04-20 07:58:00', '日志管理', 38, '/ops/log', '/ops/logManage/index', '', '', 1, NULL, 1, 0, 'log|svg', 1, 1, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (42, '', 1, 0, 'admin', '2023-04-25 07:14:39', '', '2023-04-25 07:14:39', '添加数据字典', 16, '', '', '', '', 2, 'system:dict:add', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (43, '', 1, 0, 'admin', '2023-04-25 07:15:09', '', '2023-04-25 07:15:09', '编辑数据字典', 16, '', '', '', '', 2, 'system:dict:edit', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (44, '', 1, 0, 'admin', '2023-04-25 07:16:04', '', '2023-04-25 07:16:04', '添加字典项', 16, '', '', '', '', 2, 'system:dict:item:add', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (45, '', 1, 0, 'admin', '2023-04-25 07:16:40', '', '2023-04-25 07:16:40', '编辑字典项', 16, '', '', '', '', 2, 'system:dict:item:edit', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (46, '', 1, 0, 'admin', '2023-04-25 07:17:03', '', '2023-04-25 07:17:03', '删除字典项', 16, '', '', '', '', 2, 'system:dict:item:delete', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (47, '', 1, 0, 'admin', '2023-04-25 07:17:42', '', '2023-04-25 07:17:42', '删除数据字典', 16, '', '', '', '', 2, 'system:dict:delete', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (48, '', 1, 0, 'admin', '2023-04-25 17:03:07', '', '2023-04-25 17:03:07', '数据字典回收站', 16, '', '', '', '', 2, 'system:dict:recycle', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (49, '', 1, 0, 'admin', '2023-04-25 17:04:41', '', '2023-04-25 17:04:41', '刷新字典缓存', 16, '', '', '', '', 2, 'system:dict:refresh', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (50, '', 1, 0, 'admin', '2023-04-25 17:16:25', '', '2023-04-25 17:16:25', '上传文件', 17, '', '', '', '', 2, 'system:oss:upload', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (51, '', 1, 0, 'admin', '2023-04-25 17:16:52', '', '2023-04-25 17:16:52', '删除文件', 17, '', '', '', '', 2, 'system:oss:delete', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (52, '', 1, 0, 'admin', '2023-04-25 17:17:58', '', '2023-04-25 17:17:58', '添加通知', 15, '', '', '', '', 2, 'system:notice:add', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (53, '', 1, 0, 'admin', '2023-04-25 17:18:32', '', '2023-04-25 17:18:32', '删除通知', 15, '', '', '', '', 2, 'system:notice:delete', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (54, '', 1, 0, 'admin', '2023-04-25 17:19:36', '', '2023-04-25 17:19:36', '添加职务', 14, '', '', '', '', 2, 'system:position:add', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (55, '', 1, 0, 'admin', '2023-04-25 17:20:07', '', '2023-04-25 17:20:07', '编辑职务', 14, '', '', '', '', 2, 'system:position:edit', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (56, '', 1, 0, 'admin', '2023-04-25 17:20:36', '', '2023-04-25 17:20:36', '删除职务', 14, '', '', '', '', 2, 'system:position:delete', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (57, '', 1, 0, 'admin', '2023-04-25 17:21:18', 'admin', '2023-04-25 17:21:56', '添加租户', 19, '', '', '', '', 2, 'system:tenant:add', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (58, '', 1, 0, 'admin', '2023-04-25 17:22:34', '', '2023-04-25 17:22:34', '编辑租户', 19, '', '', '', '', 2, 'system:tenant:edit', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (59, '', 1, 0, 'admin', '2023-04-25 17:23:07', '', '2023-04-25 17:23:07', '删除租户', 19, '', '', '', '', 2, 'system:tenant:delete', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (61, '', 1, 0, 'admin', '2023-04-26 12:17:26', '', '2023-04-26 12:17:26', '添加部门', 12, '', '', '', '', 2, 'sys:depart:add', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (62, '', 1, 0, 'admin', '2023-04-26 12:17:57', '', '2023-04-26 12:17:57', '编辑部门', 12, '', '', '', '', 2, 'sys:depart:edit', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (63, '', 1, 0, 'admin', '2023-04-26 12:18:24', '', '2023-04-26 12:18:24', '删除部门', 12, '', '', '', '', 2, 'sys:depart:delete', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (64, '', 1, 0, 'admin', '2023-04-26 12:20:06', '', '2023-04-26 12:20:06', '保存部门权限', 12, '', '', '', '', 2, 'sys:depart:save_role', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (65, '', 1, 0, 'admin', '2023-04-26 12:20:50', '', '2023-04-26 12:20:50', '添加菜单', 11, '', '', '', '', 2, 'sys:menu:add', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (66, '', 1, 0, 'admin', '2023-04-26 12:21:18', '', '2023-04-26 12:21:18', '编辑菜单', 11, '', '', '', '', 2, 'sys:menu:edit', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (67, '', 1, 0, 'admin', '2023-04-26 12:21:40', '', '2023-04-26 12:21:40', '删除菜单', 11, '', '', '', '', 2, 'sys:menu:delete', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (68, '', 1, 0, 'admin', '2023-04-26 12:49:18', '', '2023-04-26 12:49:18', '添加角色', 10, '', '', '', '', 2, 'sys:role:add', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (69, '', 1, 0, 'admin', '2023-04-26 12:49:52', '', '2023-04-26 12:49:52', '编辑角色', 10, '', '', '', '', 2, 'sys:role:edit', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (70, '', 1, 0, 'admin', '2023-04-26 12:50:17', '', '2023-04-26 12:50:17', '删除角色', 10, '', '', '', '', 2, 'sys:role:delete', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (71, '', 1, 0, 'admin', '2023-04-26 12:51:10', '', '2023-04-26 12:51:10', '删除用户', 5, '', '', '', '', 2, 'user:delete', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (72, '', 1, 0, 'admin', '2023-04-26 12:51:53', '', '2023-04-26 12:51:53', '用户回收站', 5, '', '', '', '', 2, 'user:recycle', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (73, '', 1, 0, 'admin', '2023-04-26 12:52:14', '', '2023-04-26 12:52:14', '修改用户密码', 5, '', '', '', '', 2, 'user:password', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (74, '', 1, 0, 'admin', '2023-04-26 17:06:55', '', '2023-04-26 17:06:55', '添加', 24, '', '', '', '', 2, 'codegen:add', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (75, '', 1, 0, 'admin', '2023-04-26 17:07:25', '', '2023-04-26 17:07:25', '编辑', 24, '', '', '', '', 2, 'codegen:edit', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (76, '', 1, 0, 'admin', '2023-04-26 17:07:48', '', '2023-04-26 17:07:48', '删除', 24, '', '', '', '', 2, 'codegen:delete', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (77, '', 1, 0, 'admin', '2023-04-26 17:09:05', '', '2023-04-26 17:09:05', '生成代码', 24, '', '', '', '', 2, 'codegen:generate', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (78, '', 1, 0, 'admin', '2023-04-26 17:09:33', '', '2023-04-26 17:09:33', '删除job', 40, '', '', '', '', 2, 'job:delete', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (79, '', 1, 0, 'admin', '2023-04-26 17:09:57', '', '2023-04-26 17:09:57', '查看详情', 39, '', '', '', '', 2, 'worker:detail', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (80, '', 1, 0, 'admin', '2023-04-26 17:17:02', '', '2023-04-26 17:17:02', '添加任务模版', 32, '', '', '', '', 2, 'task_template:add', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (81, '', 1, 0, 'admin', '2023-04-26 17:17:19', '', '2023-04-26 17:17:19', '编辑任务模版', 32, '', '', '', '', 2, 'task_template:edit', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (82, '', 1, 0, 'admin', '2023-04-26 17:17:34', '', '2023-04-26 17:17:34', '删除任务模版', 32, '', '', '', '', 2, 'task_template:delete', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (83, '', 1, 0, 'admin', '2023-04-26 17:17:49', '', '2023-04-26 17:17:49', '启用禁用', 32, '', '', '', '', 2, 'task_template:status', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (84, '', 1, 0, 'admin', '2023-04-26 17:18:13', '', '2023-04-26 17:18:13', '添加任务', 33, '', '', '', '', 2, 'task:add', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (85, '', 1, 0, 'admin', '2023-04-26 17:18:33', '', '2023-04-26 17:18:33', '编辑任务', 33, '', '', '', '', 2, 'task:edit', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (86, '', 1, 0, 'admin', '2023-04-26 17:18:48', '', '2023-04-26 17:18:48', '删除任务', 33, '', '', '', '', 2, 'task:delete', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (87, '', 1, 0, 'admin', '2023-04-26 17:19:08', '', '2023-04-26 17:19:08', '启用禁用', 33, '', '', '', '', 2, 'task:status', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (88, '', 1, 0, 'admin', '2023-04-26 17:19:49', '', '2023-04-26 17:19:49', '运行dag', 35, '', '', '', '', 2, 'dag_detail:run', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (89, '', 1, 0, 'admin', '2023-04-26 17:20:30', '', '2023-04-26 17:20:30', '删除选中节点', 35, '', '', '', '', 2, 'dag_detail:delete', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (90, '', 1, 0, 'admin', '2023-04-26 17:21:10', '', '2023-04-26 17:21:10', '添加', 34, '', '', '', '', 2, 'dag:add', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (91, '', 1, 0, 'admin', '2023-04-26 17:21:32', '', '2023-04-26 17:21:32', '复制任务', 33, '', '', '', '', 2, 'task:copy', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (92, '', 1, 0, 'admin', '2023-04-26 17:22:32', '', '2023-04-26 17:22:32', '编辑', 34, '', '', '', '', 2, 'dag:edit', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (93, '', 1, 0, 'admin', '2023-04-26 17:22:58', '', '2023-04-26 17:22:58', '删除', 34, '', '', '', '', 2, 'dag:delete', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (94, '', 1, 0, 'admin', '2023-04-26 17:23:15', '', '2023-04-26 17:23:15', '复制', 34, '', '', '', '', 2, 'dag:copy', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (95, '', 1, 0, 'admin', '2023-04-26 17:23:46', '', '2023-04-26 17:23:46', '启用禁用', 34, '', '', '', '', 2, 'dag:status', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (96, '', 1, 0, 'admin', '2023-04-26 17:24:10', '', '2023-04-26 17:24:10', '添加', 26, '', '', '', '', 2, 'datasource:add', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (97, '', 1, 0, 'admin', '2023-04-26 17:24:32', '', '2023-04-26 17:24:32', '编辑', 26, '', '', '', '', 2, 'datasource:edit', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (98, '', 1, 0, 'admin', '2023-04-26 17:24:51', '', '2023-04-26 17:24:51', '删除', 26, '', '', '', '', 2, 'datasource:delete', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (99, '', 1, 0, 'admin', '2023-04-26 17:25:47', '', '2023-04-26 17:25:47', '添加', 27, '', '', '', '', 2, 'datamodel:add', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (100, '', 1, 0, 'admin', '2023-04-26 17:26:08', '', '2023-04-26 17:26:08', '编辑', 27, '', '', '', '', 2, 'datamodel:edit', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (101, '', 1, 0, 'admin', '2023-04-26 17:26:28', '', '2023-04-26 17:26:28', '删除', 27, '', '', '', '', 2, 'datamodel:delete', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (102, '', 1, 0, 'admin', '2023-04-26 17:26:45', '', '2023-04-26 17:26:45', '复制', 27, '', '', '', '', 2, 'datamodel:copy', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (103, '', 1, 0, 'admin', '2023-04-26 17:27:03', '', '2023-04-26 17:27:03', '添加', 37, '', '', '', '', 2, 'algorithm:add', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (104, '', 1, 0, 'admin', '2023-04-26 17:27:25', '', '2023-04-26 17:27:25', '编辑', 37, '', '', '', '', 2, 'algorithm:edit', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (105, '', 1, 0, 'admin', '2023-04-26 17:27:39', '', '2023-04-26 17:27:39', '删除', 37, '', '', '', '', 2, 'algorithm:delete', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (106, '', 1, 0, 'admin', '2023-04-26 17:28:05', '', '2023-04-26 17:28:05', '启用禁用', 37, '', '', '', '', 2, 'algorithm:status', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (107, '', 1, 0, 'admin', '2023-04-26 17:29:07', '', '2023-04-26 17:29:07', '编辑数据接口', 28, '', '', '', '', 2, 'data_interface:edit', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (108, '', 1, 0, 'admin', '2023-04-26 17:29:29', '', '2023-04-26 17:29:29', '审核接口', 28, '', '', '', '', 2, 'data_interface:verify', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (109, '', 1, 0, 'admin', '2023-04-26 17:29:47', 'admin', '2023-04-26 17:30:22', '删除接口', 28, '', '', '', '', 2, 'data_interface:delete', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (110, '', 1, 0, 'admin', '2023-04-26 17:30:12', '', '2023-04-26 17:30:12', '数据接口启用禁用', 28, '', '', '', '', 2, 'data_interface:status', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (111, '', 1, 0, 'admin', '2023-04-28 07:31:18', 'admin', '2023-04-28 07:36:26', '管理角色用户', 10, '', '', '', '', 2, 'sys:role:user', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (112, '', 1, 0, 'admin', '2023-04-28 07:32:42', '', '2023-04-28 07:32:42', '授权', 10, '', '', '', '', 2, 'sys:role:auth', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (113, '', 1, 0, 'admin', '2023-05-04 09:29:15', '', '2023-05-04 09:29:15', '冻结用户', 5, '', '', '', '', 2, 'user:frozen', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (114, '', 9.2, 0, 'admin', '2023-06-19 12:04:35', 'admin', '2023-06-19 16:54:45', '告警管理', NULL, '/alert', 'layouts/default/index', '', '', 0, NULL, 1, 0, 'ant-design:alert-outlined', 1, 0, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (115, '', 1, 0, 'admin', '2023-06-19 16:51:20', 'admin', '2023-06-19 16:57:44', '告警查询', 114, '/alert/list', '/alert/index', '', '', 1, NULL, 1, 0, 'ant-design:alert-outlined', 1, 1, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (116, '', 99, 0, 'admin', '2023-06-19 16:54:21', 'admin', '2023-06-19 16:55:52', '告警策略', 114, '/alert/alert_strategy', '/alert/alert_strategy/index', '', '', 1, NULL, 1, 0, 'ant-design:exception-outlined', 1, 1, 0, 0, 0, 0, 1, 0);
INSERT INTO `sys_permission` VALUES (117, '', 1, 0, 'admin', '2023-07-28 08:17:22', '', '2023-07-28 08:17:22', '重启所有job', 40, '', '', '', '', 2, 'job:restart', 1, 1, NULL, 1, 1, 1, 1, 1, 0, 1, 1);
INSERT INTO `sys_permission` VALUES (119, '', 1, 0, 'admin', '2024-06-22 18:29:46', 'admin', '2024-06-22 18:30:01', 'ai助手', 1, '/ai', '/dashboard/ai', '', '', 1, NULL, 1, 0, NULL, 1, 1, 0, 1, 0, 0, 1, 0);
COMMIT;

-- ----------------------------
-- Table structure for sys_position
-- ----------------------------
DROP TABLE IF EXISTS `sys_position`;
CREATE TABLE `sys_position` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'id主键',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '简介',
  `sort_no` float DEFAULT NULL COMMENT '排序',
  `del_flag` smallint DEFAULT NULL COMMENT '软删除标记',
  `create_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建者',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '修改者',
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '名称',
  `code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '编码',
  `org_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属机构编码',
  `post_rank` int DEFAULT NULL COMMENT '职级',
  `company_id` int DEFAULT NULL COMMENT '公司id',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Records of sys_position
-- ----------------------------
BEGIN;
INSERT INTO `sys_position` VALUES (1, '', 1, 0, 'admin', '2022-11-09 05:41:20', 'admin', '2022-11-11 17:47:40', 'test13333', 'a1', '', 4, NULL);
COMMIT;

-- ----------------------------
-- Table structure for sys_role
-- ----------------------------
DROP TABLE IF EXISTS `sys_role`;
CREATE TABLE `sys_role` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'id主键',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '简介',
  `sort_no` float DEFAULT NULL COMMENT '排序',
  `del_flag` smallint DEFAULT NULL COMMENT '软删除标记',
  `create_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建者',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '修改者',
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `role_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '角色名称',
  `role_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '角色编码',
  `status` smallint DEFAULT NULL COMMENT '1-正常,0-禁用',
  `permissions` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '权限列表',
  PRIMARY KEY (`id`),
  KEY `ix_sys_role_role_name` (`role_name`),
  KEY `ix_sys_role_role_code` (`role_code`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Records of sys_role
-- ----------------------------
BEGIN;
INSERT INTO `sys_role` VALUES (12, '', 1, 0, 'admin', '2023-04-27 14:32:26', '', '2023-04-27 14:32:57', '管理员', 'admin', 1, '[\"1\", \"3\", \"2\", \"25\", \"26\", \"98\", \"97\", \"96\", \"27\", \"102\", \"101\", \"100\", \"99\", \"37\", \"106\", \"105\", \"104\", \"103\", \"28\", \"110\", \"109\", \"108\", \"107\", \"31\", \"32\", \"83\", \"82\", \"81\", \"80\", \"33\", \"91\", \"87\", \"86\", \"85\", \"84\", \"35\", \"89\", \"88\", \"34\", \"95\", \"94\", \"93\", \"92\", \"90\", \"20\", \"21\", \"38\", \"41\", \"40\", \"78\", \"39\", \"79\", \"23\", \"24\", \"77\", \"76\", \"75\", \"74\", \"4\", \"18\", \"5\", \"73\", \"72\", \"71\", \"7\", \"6\", \"10\", \"70\", \"69\", \"68\", \"11\", \"67\", \"66\", \"65\", \"12\", \"64\", \"63\", \"62\", \"61\", \"13\", \"22\", \"19\", \"59\", \"58\", \"57\", \"14\", \"56\", \"55\", \"54\", \"15\", \"53\", \"52\", \"16\", \"49\", \"48\", \"47\", \"46\", \"45\", \"44\", \"43\", \"42\", \"17\", \"51\", \"50\"]');
INSERT INTO `sys_role` VALUES (13, '', 1, 0, 'admin', '2023-04-27 14:32:45', '', '2023-04-27 14:48:17', '普通用户', 'user', 1, '[\"3\", \"1\", \"25\", \"28\", \"31\", \"33\", \"91\", \"87\", \"86\", \"85\", \"84\", \"35\", \"89\", \"88\", \"34\", \"95\", \"94\", \"93\", \"92\", \"90\", \"20\", \"21\", \"23\", \"24\", \"77\", \"4\", \"18\", \"13\", \"22\", \"15\", \"16\", \"17\", \"50\"]');
INSERT INTO `sys_role` VALUES (14, '', 1, 0, 'admin', '2023-04-27 17:38:31', '', '2023-04-27 17:43:35', '开发者', 'dev_user', 1, '[\"2\", \"1\", \"25\", \"26\", \"98\", \"97\", \"96\", \"27\", \"102\", \"101\", \"100\", \"99\", \"37\", \"106\", \"105\", \"104\", \"103\", \"28\", \"110\", \"109\", \"108\", \"107\", \"31\", \"32\", \"83\", \"82\", \"81\", \"80\", \"33\", \"91\", \"87\", \"86\", \"85\", \"84\", \"35\", \"89\", \"88\", \"34\", \"95\", \"94\", \"93\", \"92\", \"90\", \"20\", \"21\", \"38\", \"41\", \"40\", \"78\", \"39\", \"79\", \"23\", \"24\", \"77\", \"76\", \"75\", \"74\", \"4\", \"18\", \"13\", \"16\", \"17\", \"50\", \"3\"]');
COMMIT;

-- ----------------------------
-- Table structure for sys_tenant
-- ----------------------------
DROP TABLE IF EXISTS `sys_tenant`;
CREATE TABLE `sys_tenant` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'id主键',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '简介',
  `sort_no` float DEFAULT NULL COMMENT '排序',
  `del_flag` smallint DEFAULT NULL COMMENT '软删除标记',
  `create_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建者',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '修改者',
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '租户名称',
  `begin_date` int DEFAULT NULL COMMENT '开始时间',
  `end_date` int DEFAULT NULL COMMENT '结束时间',
  `status` smallint DEFAULT NULL COMMENT '状态 1正常 0冻结',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Records of sys_tenant
-- ----------------------------
BEGIN;
INSERT INTO `sys_tenant` VALUES (1, '', 1, 0, 'admin', '2022-11-10 06:13:24', 'admin', '2022-11-10 06:34:53', 'test', 1667911097, 1668159384, 1);
COMMIT;

-- ----------------------------
-- Table structure for sys_user
-- ----------------------------
DROP TABLE IF EXISTS `sys_user`;
CREATE TABLE `sys_user` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'id主键',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '简介',
  `sort_no` float DEFAULT NULL COMMENT '排序',
  `del_flag` smallint DEFAULT NULL COMMENT '软删除标记',
  `create_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建者',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '修改者',
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `username` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '登录的用户名',
  `password` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '密码',
  `nickname` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '昵称',
  `avatar` varchar(1024) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '头像',
  `birthday` datetime DEFAULT NULL COMMENT '生日',
  `sex` smallint DEFAULT NULL COMMENT '性别(0-默认未知,1-男,2-女)',
  `email` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '邮箱',
  `phone` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '手机号',
  `org_code` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '登录会话的机构编码',
  `status` smallint DEFAULT NULL COMMENT '1-正常,0-禁用',
  `user_identity` smallint DEFAULT NULL COMMENT '身份（1普通成员 2上级）',
  `third_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '第三方登陆的唯一标志',
  `third_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '第三方登陆的类型',
  `work_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '工号',
  `depart_id_list` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '部门列表',
  `post_id_list` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '职务列表',
  `role_id_list` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '角色列表',
  `verify_token` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '验证token',
  `login_times` int DEFAULT NULL COMMENT '登录次数',
  `login_time` int DEFAULT NULL COMMENT '上次登录时间',
  `login_ip` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '上次登录IP',
  `valid_start_time` int DEFAULT NULL COMMENT '有效期(开始)',
  `valid_end_time` int DEFAULT NULL COMMENT '有效期（结束）',
  `tenant_id_list` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '租户列表',
  `tenant_id` int DEFAULT NULL COMMENT '登录会话的租户id',
  PRIMARY KEY (`id`),
  KEY `ix_sys_user_email` (`email`),
  KEY `ix_sys_user_username` (`username`),
  KEY `ix_sys_user_phone` (`phone`),
  KEY `ix_sys_user_org_code` (`org_code`),
  KEY `ix_sys_user_password` (`password`),
  KEY `ix_sys_user_nickname` (`nickname`),
  KEY `ix_sys_user_third_id` (`third_id`),
  KEY `ix_sys_user_work_no` (`work_no`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Records of sys_user
-- ----------------------------
BEGIN;
INSERT INTO `sys_user` VALUES (1, '', 1, 0, 'system', '2022-10-31 09:41:34', 'admin', '2024-06-22 17:01:41', 'admin', 'pbkdf2:sha256:260000$uPkgXU614UEZVupq$f796a5bc254e02bfc78526a092ead4057073493f0115a9df56288f852cfb228a', 'admin', '', '2003-03-12 05:56:00', 1, '', '', 'org_5', 1, 2, NULL, NULL, '20213916', '[\"5\", \"7\"]', '[\"a1\"]', '[\"12\", \"14\"]', '', 746, 1719075701, '122.96.32.58', NULL, NULL, '[\"1\"]', 1);
INSERT INTO `sys_user` VALUES (6, '', 1, 0, 'admin', '2023-04-27 14:52:16', 'admin', '2023-09-14 01:38:33', 'preview', 'pbkdf2:sha256:260000$t4Gm48smy9rPudxM$5e65784bf7616ad5c09e9b85e0c3a0984e965c3aaad38e4ca3fa936011eb0f76', '预览用户', '', '2023-09-13 20:36:00', 0, NULL, NULL, 'org_5', 1, 2, NULL, NULL, '00002', '[\"5\"]', '[]', '[\"11\"]', '', 1, 1682617624, '172.18.0.1', NULL, NULL, '[]', NULL);
INSERT INTO `sys_user` VALUES (7, '', 1, 0, 'admin', '2023-04-27 14:54:05', 'admin', '2023-10-24 07:03:16', 'test1', 'pbkdf2:sha256:260000$VHkgoxdY1LJ4ml66$0dac1b13d19f2965d4e986ff0395aa43bf9766be2e3bd1b8fec7b5947dd65563', 'test1', NULL, '2023-09-13 20:36:00', 0, NULL, NULL, 'org_6', 1, 1, NULL, NULL, '202139160124', '[\"6\"]', '[]', '[\"13\"]', '', 3, 1694674855, '122.243.31.180', NULL, NULL, '[]', NULL);
INSERT INTO `sys_user` VALUES (8, '', 1, 0, 'admin', '2023-04-27 17:40:41', 'admin', '2023-09-13 12:36:33', 'dev1', 'pbkdf2:sha256:260000$3J8QC8NiR8TzyeN8$ff8228e7e8b41194e22a00282e08a2cf762667d3fd3e70a1681bcddc191ff9b4', '开发一', NULL, '2023-09-13 20:36:00', 1, NULL, NULL, 'org_7', 1, 2, NULL, NULL, '0000', '[\"7\"]', '[\"a1\"]', '[\"14\"]', '', 1, 1682617321, '172.18.0.1', NULL, NULL, '[\"1\"]', NULL);
COMMIT;

-- ----------------------------
-- Table structure for task
-- ----------------------------
DROP TABLE IF EXISTS `task`;
CREATE TABLE `task` (
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '简介',
  `sort_no` float DEFAULT NULL COMMENT '排序',
  `del_flag` smallint DEFAULT NULL COMMENT '软删除标记',
  `create_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建者',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '修改者',
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'id',
  `template_code` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '任务模版id',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '名称',
  `params` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '参数',
  `status` smallint DEFAULT NULL COMMENT '状态',
  `trigger_type` smallint DEFAULT NULL COMMENT '触发方式',
  `crontab` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '定时设置',
  `task_type` smallint DEFAULT NULL COMMENT '任务类型，1普通任务2dag工作流任务',
  `run_type` smallint DEFAULT NULL COMMENT 'dag运行类型，1分布式2，单进程',
  `trigger_date` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '触发始末时间',
  `priority` int DEFAULT NULL COMMENT '优先级',
  `retry` int DEFAULT NULL COMMENT '失败重试次数',
  `countdown` int DEFAULT NULL COMMENT '失败重试间隔',
  `running_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '运行中任务实例id',
  `run_queue` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '运行队列',
  `alert_strategy_ids` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '绑定告警策略列表',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Records of task
-- ----------------------------
BEGIN;
INSERT INTO `task` VALUES ('', 1, 0, 'admin', '2023-08-25 17:51:27', 'admin', '2023-08-26 09:20:28', '068324857ff6407895db34881c1c3f92', '', 'dag示例2', '{\n  \"cells\": [\n    {\n      \"shape\": \"edge\",\n      \"attrs\": {\n        \"line\": {\n          \"stroke\": \"#A2B1C3\",\n          \"strokeWidth\": 1,\n          \"targetMarker\": {\n            \"height\": 6,\n            \"name\": \"block\",\n            \"width\": 10\n          }\n        }\n      },\n      \"id\": \"eb8fc6c6-c3b5-4676-ae11-e84a90e77583\",\n      \"zIndex\": 0,\n      \"source\": {\n        \"cell\": \"c079b781-55ea-4c8e-bb6a-39d2a54ea18d\",\n        \"port\": \"9ce488b8-dc91-435d-8adf-646aea0dc35f\"\n      },\n      \"target\": {\n        \"cell\": \"41684aa0-2123-4988-a667-871bf3d23b05\",\n        \"port\": \"02d2fff0-f547-4247-aeee-056d7bb929aa\"\n      }\n    },\n    {\n      \"shape\": \"edge\",\n      \"attrs\": {\n        \"line\": {\n          \"stroke\": \"#A2B1C3\",\n          \"strokeWidth\": 1,\n          \"targetMarker\": {\n            \"height\": 6,\n            \"name\": \"block\",\n            \"width\": 10\n          }\n        }\n      },\n      \"id\": \"63e6cfe3-6c13-427f-8a42-4f17050113af\",\n      \"zIndex\": 0,\n      \"source\": {\n        \"cell\": \"41684aa0-2123-4988-a667-871bf3d23b05\",\n        \"port\": \"9ce488b8-dc91-435d-8adf-646aea0dc35f\"\n      },\n      \"target\": {\n        \"cell\": \"9302f8d4-2d18-4653-8ce2-8ca89da43500\",\n        \"port\": \"02d2fff0-f547-4247-aeee-056d7bb929aa\"\n      }\n    },\n    {\n      \"position\": {\n        \"x\": -110,\n        \"y\": -40\n      },\n      \"size\": {\n        \"width\": 180,\n        \"height\": 40\n      },\n      \"view\": \"vue-shape-view\",\n      \"shape\": \"container-node\",\n      \"img\": \"https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ\",\n      \"component\": {},\n      \"ports\": {\n        \"groups\": {\n          \"top\": {\n            \"position\": \"top\",\n            \"attrs\": {\n              \"circle\": {\n                \"r\": 4,\n                \"magnet\": true,\n                \"stroke\": \"#5F95FF\",\n                \"strokeWidth\": 1,\n                \"fill\": \"#fff\",\n                \"style\": {\n                  \"visibility\": \"hidden\"\n                }\n              }\n            }\n          },\n          \"bottom\": {\n            \"position\": \"bottom\",\n            \"attrs\": {\n              \"circle\": {\n                \"r\": 4,\n                \"magnet\": true,\n                \"stroke\": \"#5F95FF\",\n                \"strokeWidth\": 1,\n                \"fill\": \"#fff\",\n                \"style\": {\n                  \"visibility\": \"hidden\"\n                }\n              }\n            }\n          }\n        },\n        \"items\": [\n          {\n            \"group\": \"top\",\n            \"id\": \"02d2fff0-f547-4247-aeee-056d7bb929aa\"\n          },\n          {\n            \"group\": \"bottom\",\n            \"id\": \"9ce488b8-dc91-435d-8adf-646aea0dc35f\"\n          }\n        ]\n      },\n      \"id\": \"c079b781-55ea-4c8e-bb6a-39d2a54ea18d\",\n      \"data\": {\n        \"img\": \"https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ\",\n        \"label\": \"python任务\",\n        \"params\": {\n          \"countdown\": 0,\n          \"error_type\": \"throw\",\n          \"retry\": 0,\n          \"task_conf\": {\n            \"code\": \"import time\\nfor i in range(5):\\n    logger.info(i)\\n    time.sleep(1)\",\n            \"run_type\": \"code\"\n          },\n          \"template_code\": \"PythonTask\"\n        },\n        \"status\": \"\"\n      },\n      \"zIndex\": 1\n    },\n    {\n      \"position\": {\n        \"x\": -110,\n        \"y\": 250\n      },\n      \"size\": {\n        \"width\": 180,\n        \"height\": 40\n      },\n      \"view\": \"vue-shape-view\",\n      \"shape\": \"container-node\",\n      \"img\": \"https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ\",\n      \"component\": {},\n      \"ports\": {\n        \"groups\": {\n          \"top\": {\n            \"position\": \"top\",\n            \"attrs\": {\n              \"circle\": {\n                \"r\": 4,\n                \"magnet\": true,\n                \"stroke\": \"#5F95FF\",\n                \"strokeWidth\": 1,\n                \"fill\": \"#fff\",\n                \"style\": {\n                  \"visibility\": \"hidden\"\n                }\n              }\n            }\n          },\n          \"bottom\": {\n            \"position\": \"bottom\",\n            \"attrs\": {\n              \"circle\": {\n                \"r\": 4,\n                \"magnet\": true,\n                \"stroke\": \"#5F95FF\",\n                \"strokeWidth\": 1,\n                \"fill\": \"#fff\",\n                \"style\": {\n                  \"visibility\": \"hidden\"\n                }\n              }\n            }\n          }\n        },\n        \"items\": [\n          {\n            \"group\": \"top\",\n            \"id\": \"02d2fff0-f547-4247-aeee-056d7bb929aa\"\n          },\n          {\n            \"group\": \"bottom\",\n            \"id\": \"9ce488b8-dc91-435d-8adf-646aea0dc35f\"\n          }\n        ]\n      },\n      \"id\": \"9302f8d4-2d18-4653-8ce2-8ca89da43500\",\n      \"data\": {\n        \"img\": \"https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ\",\n        \"label\": \"python任务\",\n        \"params\": {\n          \"countdown\": 0,\n          \"error_type\": \"throw\",\n          \"retry\": 0,\n          \"task_conf\": {\n            \"code\": \"import time\\nfor i in range(5):\\n    logger.info(i)\\n    time.sleep(1)\",\n            \"run_type\": \"code\"\n          },\n          \"template_code\": \"PythonTask\"\n        },\n        \"status\": \"\"\n      },\n      \"zIndex\": 2\n    },\n    {\n      \"position\": {\n        \"x\": -110,\n        \"y\": 110\n      },\n      \"size\": {\n        \"width\": 180,\n        \"height\": 40\n      },\n      \"view\": \"vue-shape-view\",\n      \"shape\": \"container-node\",\n      \"img\": \"https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ\",\n      \"component\": {},\n      \"ports\": {\n        \"groups\": {\n          \"top\": {\n            \"position\": \"top\",\n            \"attrs\": {\n              \"circle\": {\n                \"r\": 4,\n                \"magnet\": true,\n                \"stroke\": \"#5F95FF\",\n                \"strokeWidth\": 1,\n                \"fill\": \"#fff\",\n                \"style\": {\n                  \"visibility\": \"hidden\"\n                }\n              }\n            }\n          },\n          \"bottom\": {\n            \"position\": \"bottom\",\n            \"attrs\": {\n              \"circle\": {\n                \"r\": 4,\n                \"magnet\": true,\n                \"stroke\": \"#5F95FF\",\n                \"strokeWidth\": 1,\n                \"fill\": \"#fff\",\n                \"style\": {\n                  \"visibility\": \"hidden\"\n                }\n              }\n            }\n          }\n        },\n        \"items\": [\n          {\n            \"group\": \"top\",\n            \"id\": \"02d2fff0-f547-4247-aeee-056d7bb929aa\"\n          },\n          {\n            \"group\": \"bottom\",\n            \"id\": \"9ce488b8-dc91-435d-8adf-646aea0dc35f\"\n          }\n        ]\n      },\n      \"id\": \"41684aa0-2123-4988-a667-871bf3d23b05\",\n      \"data\": {\n        \"img\": \"https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ\",\n        \"label\": \"python任务\",\n        \"params\": {\n          \"countdown\": 0,\n          \"error_type\": \"throw\",\n          \"retry\": 0,\n          \"task_conf\": {\n            \"code\": \"import time\\nfor i in range(5):\\n    logger.info(i)\\n    time.sleep(1)\",\n            \"run_type\": \"code\"\n          },\n          \"template_code\": \"PythonTask\"\n        },\n        \"status\": \"\"\n      },\n      \"zIndex\": 3\n    }\n  ]\n}', 1, 1, '', 2, 1, '[]', 1, 0, 0, NULL, 'default', '');
INSERT INTO `task` VALUES ('', 1, 0, 'admin', '2023-08-10 09:50:56', 'admin', '2023-08-14 05:53:51', '0e4392b2844a4951bd1c8434ea90dd9e', 'PythonTask', '周期任务示例', '{\n  \"run_type\": \"code\",\n  \"code\": \"import random\\nimport time\\nlogger.info(\\\"开始运行\\\")\\ntime.sleep(random.randint(3,5))\\nlogger.info(\\\"结束运行\\\")\"\n}', 0, 2, '0 * * * * ? *', 1, 1, '[]', 1, 0, 0, '577ba071-0d22-4c6b-826b-a7572668079e', 'default', '');
INSERT INTO `task` VALUES ('', 1, 0, 'admin', '2023-08-10 08:01:13', 'admin', '2023-08-14 04:12:37', '1b6aad025dc2405eb8248f28e75ec048', 'PythonTask', '单次任务示例', '{\n  \"run_type\": \"code\",\n  \"code\": \"import time\\n\\nfor i in range(10):\\n    logger.info(i)\\n    time.sleep(2)\"\n}', 1, 1, '', 1, 1, '[]', 1, 0, 0, '8a16f829-0b11-4fea-8290-208b49014d38', 'default', '');
INSERT INTO `task` VALUES ('', 1, 0, 'admin', '2023-08-10 11:39:19', 'admin', '2023-12-24 07:24:12', '691f4067b41a42099feef10c75fb56f8', 'EtlTask', '数据集成流处理示例-binlog2es', '{\n  \"extract\": {\n    \"model_id\": \"77b5008db89348348360893720a01b80\",\n    \"extract_type\": \"flow\",\n    \"extract_rules\": [],\n    \"search_type\": \"read_type\",\n    \"search_text\": \"latest\",\n    \"batch_size\": 1\n  },\n  \"process_rules\": [\n    {\n      \"code\": \"gen_records_list\",\n      \"component\": \"\",\n      \"form_type\": 2,\n      \"id\": \"4a6c1cdb93224f3f90502f64cf201538\",\n      \"name\": \"获取内容列表\",\n      \"params\": [\n        {\n          \"default\": \"\",\n          \"form_type\": \"select_fields\",\n          \"name\": \"字段列表\",\n          \"required\": false,\n          \"tips\": \"\",\n          \"value\": \"fields\"\n        }\n      ],\n      \"rule_dict\": {\n        \"fields\": \"\"\n      },\n      \"type\": \"etl_algorithm\"\n    },\n    {\n      \"code\": \"code_transform\",\n      \"component\": \"\",\n      \"form_type\": 2,\n      \"id\": \"880bc3108df249e499c7aff1da8cf2a3\",\n      \"name\": \"自定义代码转换数据\",\n      \"params\": [\n        {\n          \"default\": \"python\",\n          \"form_type\": \"select\",\n          \"name\": \"语言\",\n          \"options\": [\n            {\n              \"label\": \"python\",\n              \"value\": \"python\"\n            }\n          ],\n          \"required\": true,\n          \"tips\": \"\",\n          \"value\": \"language\"\n        },\n        {\n          \"default\": \"\",\n          \"form_type\": \"codeEditor\",\n          \"name\": \"代码\",\n          \"required\": true,\n          \"tips\": \"\",\n          \"value\": \"code\"\n        }\n      ],\n      \"rule_dict\": {\n        \"code\": \"def transform(source):\\n    result = []\\n    for i in source:\\n        dic = i[\'data\']\\n        result.append(dic)\\n    return result\",\n        \"language\": \"python\"\n      },\n      \"type\": \"etl_algorithm\"\n    },\n    {\n      \"code\": \"map_field_names\",\n      \"component\": \"\",\n      \"form_type\": 2,\n      \"id\": \"66fcaecbc68642359cf69824f27fb3a6\",\n      \"name\": \"字段映射\",\n      \"params\": [\n        {\n          \"default\": \"{}\",\n          \"form_type\": \"codeEditor\",\n          \"language\": \"json\",\n          \"name\": \"字段映射\",\n          \"required\": true,\n          \"tips\": \"\",\n          \"value\": \"field_map\"\n        }\n      ],\n      \"rule_dict\": {\n        \"field_map\": \"{\\n    \\\"id\\\": \\\"_id\\\"\\n}\"\n      },\n      \"type\": \"etl_algorithm\"\n    }\n  ],\n  \"load\": {\n    \"model_id\": \"a7f25e1805a44ea5a546158da95ad726\",\n    \"load_type\": \"upsert\",\n    \"only_fields\": [\n      \"_id\"\n    ]\n  }\n}', 1, 1, '', 1, 1, '[]', 1, 0, 0, 'c32da3d9-e01b-4b0c-b4da-dad44c68e2b8', 'default', '');
INSERT INTO `task` VALUES ('', 1, 0, 'admin', '2023-08-10 11:15:43', 'admin', '2023-12-24 07:27:45', '6c6395371bac4f8a8e5b4db23eaa010a', 'EtlTask', '数据集成批处理示例-akshare2es', '{\n  \"extract\": {\n    \"model_id\": \"d88b859297224ebcba7fe21efe118ebb\",\n    \"extract_type\": \"batch\",\n    \"extract_rules\": [],\n    \"search_type\": \"query_params\",\n    \"search_text\": \"{\\n  \\\"symbol\\\": \\\"000001\\\",\\n  \\\"period\\\": \\\"daily\\\",\\n  \\\"start_date\\\": \\\"19700101\\\",\\n  \\\"end_date\\\": \\\"20500101\\\",\\n  \\\"adjust\\\": \\\"\\\",\\n  \\\"timeout\\\": null\\n}\",\n    \"batch_size\": 100\n  },\n  \"process_rules\": [\n    {\n      \"code\": \"gen_records_list\",\n      \"component\": \"\",\n      \"form_type\": 2,\n      \"id\": \"4a6c1cdb93224f3f90502f64cf201538\",\n      \"name\": \"获取内容列表\",\n      \"params\": [\n        {\n          \"default\": \"\",\n          \"form_type\": \"select_fields\",\n          \"name\": \"字段列表\",\n          \"required\": false,\n          \"tips\": \"\",\n          \"value\": \"fields\"\n        }\n      ],\n      \"rule_dict\": {\n        \"fields\": \"收盘,开盘,日期,最低,最高,成交额\"\n      },\n      \"type\": \"etl_algorithm\"\n    },\n    {\n      \"code\": \"map_field_names\",\n      \"component\": \"\",\n      \"form_type\": 2,\n      \"id\": \"66fcaecbc68642359cf69824f27fb3a6\",\n      \"name\": \"字段映射\",\n      \"params\": [\n        {\n          \"default\": \"{}\",\n          \"form_type\": \"codeEditor\",\n          \"language\": \"json\",\n          \"name\": \"字段映射\",\n          \"required\": true,\n          \"tips\": \"\",\n          \"value\": \"field_map\"\n        }\n      ],\n      \"rule_dict\": {\n        \"field_map\": \"{\\n   \\\"日期\\\": \\\"time\\\",\\n   \\\"最高\\\": \\\"high\\\",\\n    \\\"最低\\\": \\\"low\\\",\\n    \\\"开盘\\\": \\\"open\\\",\\n    \\\"收盘\\\": \\\"close\\\",\\n    \\\"成交额\\\": \\\"volume\\\"\\n}\"\n      },\n      \"type\": \"etl_algorithm\"\n    },\n    {\n      \"code\": \"add_field\",\n      \"component\": \"\",\n      \"form_type\": 2,\n      \"id\": \"c9e0210186e14d50becd8653503f8620\",\n      \"name\": \"添加字段\",\n      \"params\": [\n        {\n          \"default\": \"\",\n          \"form_type\": \"input\",\n          \"name\": \"字段值\",\n          \"required\": true,\n          \"tips\": \"\",\n          \"value\": \"field\"\n        },\n        {\n          \"default\": \"\",\n          \"form_type\": \"input\",\n          \"name\": \"默认值\",\n          \"required\": true,\n          \"tips\": \"\",\n          \"value\": \"default\"\n        }\n      ],\n      \"rule_dict\": {\n        \"default\": \"000001\",\n        \"field\": \"symbol\"\n      },\n      \"type\": \"etl_algorithm\"\n    },\n    {\n      \"code\": \"gen_only_id\",\n      \"component\": \"\",\n      \"form_type\": 2,\n      \"id\": \"87c58ab9220d4532ab83f87fc817ce38\",\n      \"name\": \"生成唯一id\",\n      \"params\": [\n        {\n          \"default\": \"\",\n          \"form_type\": \"select_fields\",\n          \"name\": \"唯一字段列表\",\n          \"required\": true,\n          \"tips\": \"\",\n          \"value\": \"only_fields\"\n        },\n        {\n          \"default\": \"_id\",\n          \"form_type\": \"input\",\n          \"name\": \"唯一号字段\",\n          \"required\": true,\n          \"tips\": \"\",\n          \"value\": \"output_field\"\n        }\n      ],\n      \"rule_dict\": {\n        \"only_fields\": \"time,symbol\",\n        \"output_field\": \"_id\"\n      },\n      \"type\": \"etl_algorithm\"\n    }\n  ],\n  \"load\": {\n    \"model_id\": \"f4f58112235f4625a72f880a373ff697\",\n    \"load_type\": \"upsert\",\n    \"only_fields\": [\n      \"id\"\n    ]\n  }\n}', 1, 1, '', 1, 1, '[]', 1, 0, 0, 'e86aedff-215e-45d1-be10-90cfa2483dd5', 'default', '');
INSERT INTO `task` VALUES ('', 1, 0, 'admin', '2023-08-11 19:40:42', 'admin', '2023-10-24 07:01:39', '8ab8b4d482944ea59d1f7241b733907c', 'PythonTask', '失败任务示例', '{\n  \"run_type\": \"code\",\n  \"code\": \"import time\\n\\ntime.sleep(2)\\n1/0\"\n}', 1, 1, '', 1, 1, '[]', 1, 2, 5, 'c23e39de-6a73-4d29-bfc8-f42d682820f1', 'default', '0af64e7c24d44c19908ee0034ddd10ec');
INSERT INTO `task` VALUES ('', 1, 0, 'admin', '2023-08-09 07:32:59', '', '2023-12-24 09:01:17', 'e96a8e8a8ef140678873c1f3e548920a', 'PythonTask', '数据采集示例-股票历史数据采集', '{\n  \"run_type\": \"code\",\n  \"code\": \"import akshare as ak\\nfrom utils.etl_utils import get_writer_model\\nfrom utils.common_utils import md5, format_date\\n\\n\\ndef transform_stock_data(stock_data, stock_code, stock_name):\\n    \\\"\\\"\\\"\\n    转换数据\\n    :param stock_data:\\n    :return:\\n    \\\"\\\"\\\"\\n    field_map = {\\n        \\\"日期\\\": \\\"time\\\",\\n        \\\"最高\\\": \\\"high\\\",\\n        \\\"最低\\\": \\\"low\\\",\\n        \\\"开盘\\\": \\\"open\\\",\\n        \\\"收盘\\\": \\\"close\\\",\\n        \\\"成交量\\\": \\\"volume\\\",\\n        \\\"成交额\\\": \\\"amount\\\",\\n        \\\"换手率\\\": \\\"turnover\\\",\\n        \\\"振幅\\\": \\\"amplitude\\\",\\n        \\\"涨跌幅\\\": \\\"chg\\\",\\n        \\\"涨跌额\\\": \\\"change_amount\\\"\\n    }\\n    stock_data = stock_data.rename(columns=field_map)\\n    stock_data[\'symbol\'] = stock_code\\n    stock_data[\'name\'] = stock_name\\n    result_list = []\\n    for k, row in stock_data.iterrows():\\n        row = row.to_dict()\\n        row[\'time\'] = format_date(row[\'time\'], res_type=\'datetime\')\\n        hash_key = f\\\"{row[\'symbol\']}{row[\'time\']}\\\"\\n        row[\'_id\'] = md5(hash_key)\\n        result_list.append(row)\\n    return result_list\\n\\n\\nflag, writer = get_writer_model({\\n    \\\"model_id\\\": \\\"f4f58112235f4625a72f880a373ff697\\\",\\n    \\\"load_type\\\": \\\"upsert\\\",\\n    \\\"only_fields\\\": \\\"_id\\\"\\n})\\nif not flag:\\n    logger.exception(f\\\"获取写入模型失败\\\")\\n# 获取股票代码-名称 map\\ncode_id_dict = {}\\nstock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()\\nfor k, row in stock_zh_a_spot_em_df.iterrows():\\n    row = row.to_dict()\\n    code_id_dict[row[\'代码\']] = row[\'名称\']\\ni = 1\\nfor stock_code in code_id_dict:\\n    try:\\n        stock_name = code_id_dict[stock_code]\\n        if stock_name == 1:\\n            stock_name = \'unknow\'\\n        stock_data = ak.stock_zh_a_hist(symbol=stock_code, adjust=\\\"qfq\\\")\\n        stock_data = transform_stock_data(stock_data, stock_code, stock_name)\\n        writer.write(stock_data)\\n        logger.info(f\\\"{i}/{len(code_id_dict)}, 获取数据成功，股票代码：{stock_code}，数据量：{len(stock_data)}\\\")\\n    except Exception as e:\\n        logger.info(f\\\"获取数据失败，{e}\\\")\\n        logger.exception(e)\\n    i += 1\"\n}', 0, 1, '', 1, 1, '[]', 1, 0, 0, '015fcc8d-a133-4612-9a90-cd4bb94a179a', 'default', '');
INSERT INTO `task` VALUES ('', 1, 0, 'admin', '2023-08-11 06:11:05', 'admin', '2023-09-15 17:50:00', 'fdacfa5b336b47aeba93376d9e5a4621', '', '任务工作流示例', '{\n  \"cells\": [\n    {\n      \"shape\": \"edge\",\n      \"attrs\": {\n        \"line\": {\n          \"stroke\": \"#A2B1C3\",\n          \"strokeWidth\": 1,\n          \"targetMarker\": {\n            \"height\": 6,\n            \"name\": \"block\",\n            \"width\": 10\n          }\n        }\n      },\n      \"id\": \"856950e2-e7ac-4e83-a765-95476c35efbe\",\n      \"zIndex\": 0,\n      \"source\": {\n        \"cell\": \"8361303b-7893-4cb1-996d-aeadb3c13081\",\n        \"port\": \"f83f9e97-ff49-49d3-9aeb-a4663498684a\"\n      },\n      \"target\": {\n        \"cell\": \"2f427011-1c25-4559-b0eb-f11963191a32\",\n        \"port\": \"7869fd81-5cac-4724-93df-ca7ce317ac6e\"\n      }\n    },\n    {\n      \"shape\": \"edge\",\n      \"attrs\": {\n        \"line\": {\n          \"stroke\": \"#A2B1C3\",\n          \"strokeWidth\": 1,\n          \"targetMarker\": {\n            \"height\": 6,\n            \"name\": \"block\",\n            \"width\": 10\n          }\n        }\n      },\n      \"id\": \"369d10c2-679a-4245-8fd3-fdf798561c01\",\n      \"zIndex\": 0,\n      \"source\": {\n        \"cell\": \"8361303b-7893-4cb1-996d-aeadb3c13081\",\n        \"port\": \"f83f9e97-ff49-49d3-9aeb-a4663498684a\"\n      },\n      \"target\": {\n        \"cell\": \"b4f99075-5a79-4074-9dde-2cd282c1079e\",\n        \"port\": \"7869fd81-5cac-4724-93df-ca7ce317ac6e\"\n      }\n    },\n    {\n      \"shape\": \"edge\",\n      \"attrs\": {\n        \"line\": {\n          \"stroke\": \"#A2B1C3\",\n          \"strokeWidth\": 1,\n          \"targetMarker\": {\n            \"height\": 6,\n            \"name\": \"block\",\n            \"width\": 10\n          }\n        }\n      },\n      \"id\": \"b346428a-594b-44c4-93cd-eecee119fd79\",\n      \"zIndex\": 0,\n      \"source\": {\n        \"cell\": \"2f427011-1c25-4559-b0eb-f11963191a32\",\n        \"port\": \"f83f9e97-ff49-49d3-9aeb-a4663498684a\"\n      },\n      \"target\": {\n        \"cell\": \"234c1aa0-8fd3-4cee-b3be-74f501e8d635\",\n        \"port\": \"7869fd81-5cac-4724-93df-ca7ce317ac6e\"\n      }\n    },\n    {\n      \"shape\": \"edge\",\n      \"attrs\": {\n        \"line\": {\n          \"stroke\": \"#A2B1C3\",\n          \"strokeWidth\": 1,\n          \"targetMarker\": {\n            \"height\": 6,\n            \"name\": \"block\",\n            \"width\": 10\n          }\n        }\n      },\n      \"id\": \"1afd6efc-0eae-420b-85d5-1cdd6fece9fe\",\n      \"zIndex\": 0,\n      \"source\": {\n        \"cell\": \"234c1aa0-8fd3-4cee-b3be-74f501e8d635\",\n        \"port\": \"f83f9e97-ff49-49d3-9aeb-a4663498684a\"\n      },\n      \"target\": {\n        \"cell\": \"61f1c0f3-4fd7-4cdf-8a8e-34ce8cdc523c\",\n        \"port\": \"7869fd81-5cac-4724-93df-ca7ce317ac6e\"\n      }\n    },\n    {\n      \"shape\": \"edge\",\n      \"attrs\": {\n        \"line\": {\n          \"stroke\": \"#A2B1C3\",\n          \"strokeWidth\": 1,\n          \"targetMarker\": {\n            \"height\": 6,\n            \"name\": \"block\",\n            \"width\": 10\n          }\n        }\n      },\n      \"id\": \"1151c836-99d0-4997-85d4-be1927c0f8ad\",\n      \"zIndex\": 0,\n      \"source\": {\n        \"cell\": \"b4f99075-5a79-4074-9dde-2cd282c1079e\",\n        \"port\": \"f83f9e97-ff49-49d3-9aeb-a4663498684a\"\n      },\n      \"target\": {\n        \"cell\": \"61f1c0f3-4fd7-4cdf-8a8e-34ce8cdc523c\",\n        \"port\": \"7869fd81-5cac-4724-93df-ca7ce317ac6e\"\n      }\n    },\n    {\n      \"position\": {\n        \"x\": 150,\n        \"y\": -10\n      },\n      \"size\": {\n        \"width\": 180,\n        \"height\": 40\n      },\n      \"view\": \"vue-shape-view\",\n      \"shape\": \"container-node\",\n      \"img\": \"https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ\",\n      \"component\": {},\n      \"ports\": {\n        \"groups\": {\n          \"top\": {\n            \"position\": \"top\",\n            \"attrs\": {\n              \"circle\": {\n                \"r\": 4,\n                \"magnet\": true,\n                \"stroke\": \"#5F95FF\",\n                \"strokeWidth\": 1,\n                \"fill\": \"#fff\",\n                \"style\": {\n                  \"visibility\": \"hidden\"\n                }\n              }\n            }\n          },\n          \"bottom\": {\n            \"position\": \"bottom\",\n            \"attrs\": {\n              \"circle\": {\n                \"r\": 4,\n                \"magnet\": true,\n                \"stroke\": \"#5F95FF\",\n                \"strokeWidth\": 1,\n                \"fill\": \"#fff\",\n                \"style\": {\n                  \"visibility\": \"hidden\"\n                }\n              }\n            }\n          }\n        },\n        \"items\": [\n          {\n            \"group\": \"top\",\n            \"id\": \"7869fd81-5cac-4724-93df-ca7ce317ac6e\"\n          },\n          {\n            \"group\": \"bottom\",\n            \"id\": \"f83f9e97-ff49-49d3-9aeb-a4663498684a\"\n          }\n        ]\n      },\n      \"id\": \"8361303b-7893-4cb1-996d-aeadb3c13081\",\n      \"data\": {\n        \"img\": \"https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ\",\n        \"label\": \"python任务\",\n        \"params\": {\n          \"countdown\": 0,\n          \"error_type\": \"throw\",\n          \"retry\": 0,\n          \"task_conf\": {\n            \"code\": \"import time\\n\\nfor i in range(5):\\n    logger.info(i)\\n    time.sleep(2)\",\n            \"run_type\": \"code\"\n          },\n          \"template_code\": \"PythonTask\"\n        },\n        \"status\": \"\"\n      },\n      \"zIndex\": 1\n    },\n    {\n      \"position\": {\n        \"x\": -30,\n        \"y\": 180\n      },\n      \"size\": {\n        \"width\": 180,\n        \"height\": 40\n      },\n      \"view\": \"vue-shape-view\",\n      \"shape\": \"container-node\",\n      \"img\": \"https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ\",\n      \"component\": {},\n      \"ports\": {\n        \"groups\": {\n          \"top\": {\n            \"position\": \"top\",\n            \"attrs\": {\n              \"circle\": {\n                \"r\": 4,\n                \"magnet\": true,\n                \"stroke\": \"#5F95FF\",\n                \"strokeWidth\": 1,\n                \"fill\": \"#fff\",\n                \"style\": {\n                  \"visibility\": \"hidden\"\n                }\n              }\n            }\n          },\n          \"bottom\": {\n            \"position\": \"bottom\",\n            \"attrs\": {\n              \"circle\": {\n                \"r\": 4,\n                \"magnet\": true,\n                \"stroke\": \"#5F95FF\",\n                \"strokeWidth\": 1,\n                \"fill\": \"#fff\",\n                \"style\": {\n                  \"visibility\": \"hidden\"\n                }\n              }\n            }\n          }\n        },\n        \"items\": [\n          {\n            \"group\": \"top\",\n            \"id\": \"7869fd81-5cac-4724-93df-ca7ce317ac6e\"\n          },\n          {\n            \"group\": \"bottom\",\n            \"id\": \"f83f9e97-ff49-49d3-9aeb-a4663498684a\"\n          }\n        ]\n      },\n      \"id\": \"2f427011-1c25-4559-b0eb-f11963191a32\",\n      \"data\": {\n        \"img\": \"https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ\",\n        \"label\": \"python任务\",\n        \"params\": {\n          \"countdown\": 0,\n          \"error_type\": \"throw\",\n          \"retry\": 0,\n          \"task_conf\": {\n            \"code\": \"import time\\n\\nfor i in range(5):\\n    logger.info(i)\\n    time.sleep(2)\",\n            \"run_type\": \"code\"\n          },\n          \"template_code\": \"PythonTask\"\n        },\n        \"status\": \"\"\n      },\n      \"zIndex\": 2\n    },\n    {\n      \"position\": {\n        \"x\": 280,\n        \"y\": 210\n      },\n      \"size\": {\n        \"width\": 180,\n        \"height\": 40\n      },\n      \"view\": \"vue-shape-view\",\n      \"shape\": \"container-node\",\n      \"img\": \"https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ\",\n      \"component\": {},\n      \"ports\": {\n        \"groups\": {\n          \"top\": {\n            \"position\": \"top\",\n            \"attrs\": {\n              \"circle\": {\n                \"r\": 4,\n                \"magnet\": true,\n                \"stroke\": \"#5F95FF\",\n                \"strokeWidth\": 1,\n                \"fill\": \"#fff\",\n                \"style\": {\n                  \"visibility\": \"hidden\"\n                }\n              }\n            }\n          },\n          \"bottom\": {\n            \"position\": \"bottom\",\n            \"attrs\": {\n              \"circle\": {\n                \"r\": 4,\n                \"magnet\": true,\n                \"stroke\": \"#5F95FF\",\n                \"strokeWidth\": 1,\n                \"fill\": \"#fff\",\n                \"style\": {\n                  \"visibility\": \"hidden\"\n                }\n              }\n            }\n          }\n        },\n        \"items\": [\n          {\n            \"group\": \"top\",\n            \"id\": \"7869fd81-5cac-4724-93df-ca7ce317ac6e\"\n          },\n          {\n            \"group\": \"bottom\",\n            \"id\": \"f83f9e97-ff49-49d3-9aeb-a4663498684a\"\n          }\n        ]\n      },\n      \"id\": \"b4f99075-5a79-4074-9dde-2cd282c1079e\",\n      \"data\": {\n        \"img\": \"https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ\",\n        \"label\": \"python任务\",\n        \"params\": {\n          \"countdown\": 0,\n          \"error_type\": \"throw\",\n          \"retry\": 0,\n          \"task_conf\": {\n            \"code\": \"import time\\n\\nfor i in range(5):\\n    logger.info(i)\\n    time.sleep(2)\",\n            \"run_type\": \"code\"\n          },\n          \"template_code\": \"PythonTask\"\n        },\n        \"status\": \"\"\n      },\n      \"zIndex\": 3\n    },\n    {\n      \"position\": {\n        \"x\": -30,\n        \"y\": 300\n      },\n      \"size\": {\n        \"width\": 180,\n        \"height\": 40\n      },\n      \"view\": \"vue-shape-view\",\n      \"shape\": \"container-node\",\n      \"img\": \"https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ\",\n      \"component\": {},\n      \"ports\": {\n        \"groups\": {\n          \"top\": {\n            \"position\": \"top\",\n            \"attrs\": {\n              \"circle\": {\n                \"r\": 4,\n                \"magnet\": true,\n                \"stroke\": \"#5F95FF\",\n                \"strokeWidth\": 1,\n                \"fill\": \"#fff\",\n                \"style\": {\n                  \"visibility\": \"hidden\"\n                }\n              }\n            }\n          },\n          \"bottom\": {\n            \"position\": \"bottom\",\n            \"attrs\": {\n              \"circle\": {\n                \"r\": 4,\n                \"magnet\": true,\n                \"stroke\": \"#5F95FF\",\n                \"strokeWidth\": 1,\n                \"fill\": \"#fff\",\n                \"style\": {\n                  \"visibility\": \"hidden\"\n                }\n              }\n            }\n          }\n        },\n        \"items\": [\n          {\n            \"group\": \"top\",\n            \"id\": \"7869fd81-5cac-4724-93df-ca7ce317ac6e\"\n          },\n          {\n            \"group\": \"bottom\",\n            \"id\": \"f83f9e97-ff49-49d3-9aeb-a4663498684a\"\n          }\n        ]\n      },\n      \"id\": \"234c1aa0-8fd3-4cee-b3be-74f501e8d635\",\n      \"data\": {\n        \"img\": \"https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ\",\n        \"label\": \"python任务\",\n        \"params\": {\n          \"countdown\": 0,\n          \"error_type\": \"throw\",\n          \"retry\": 0,\n          \"task_conf\": {\n            \"code\": \"import time\\n\\nfor i in range(5):\\n    logger.info(i)\\n    time.sleep(2)\",\n            \"run_type\": \"code\"\n          },\n          \"template_code\": \"PythonTask\"\n        },\n        \"status\": \"\"\n      },\n      \"zIndex\": 4\n    },\n    {\n      \"position\": {\n        \"x\": 110,\n        \"y\": 480\n      },\n      \"size\": {\n        \"width\": 180,\n        \"height\": 40\n      },\n      \"view\": \"vue-shape-view\",\n      \"shape\": \"container-node\",\n      \"img\": \"https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ\",\n      \"component\": {},\n      \"ports\": {\n        \"groups\": {\n          \"top\": {\n            \"position\": \"top\",\n            \"attrs\": {\n              \"circle\": {\n                \"r\": 4,\n                \"magnet\": true,\n                \"stroke\": \"#5F95FF\",\n                \"strokeWidth\": 1,\n                \"fill\": \"#fff\",\n                \"style\": {\n                  \"visibility\": \"hidden\"\n                }\n              }\n            }\n          },\n          \"bottom\": {\n            \"position\": \"bottom\",\n            \"attrs\": {\n              \"circle\": {\n                \"r\": 4,\n                \"magnet\": true,\n                \"stroke\": \"#5F95FF\",\n                \"strokeWidth\": 1,\n                \"fill\": \"#fff\",\n                \"style\": {\n                  \"visibility\": \"hidden\"\n                }\n              }\n            }\n          }\n        },\n        \"items\": [\n          {\n            \"group\": \"top\",\n            \"id\": \"7869fd81-5cac-4724-93df-ca7ce317ac6e\"\n          },\n          {\n            \"group\": \"bottom\",\n            \"id\": \"f83f9e97-ff49-49d3-9aeb-a4663498684a\"\n          }\n        ]\n      },\n      \"id\": \"61f1c0f3-4fd7-4cdf-8a8e-34ce8cdc523c\",\n      \"data\": {\n        \"img\": \"https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ\",\n        \"label\": \"python任务\",\n        \"params\": {\n          \"countdown\": 0,\n          \"error_type\": \"throw\",\n          \"retry\": 0,\n          \"task_conf\": {\n            \"code\": \"import time\\n\\nfor i in range(5):\\n    logger.info(i)\\n    time.sleep(2)\",\n            \"run_type\": \"code\"\n          },\n          \"template_code\": \"PythonTask\"\n        },\n        \"status\": \"\"\n      },\n      \"zIndex\": 5\n    }\n  ]\n}', 1, 1, '', 2, 1, '[]', 1, 0, 0, NULL, 'default', '');
COMMIT;

-- ----------------------------
-- Table structure for task_instance
-- ----------------------------
DROP TABLE IF EXISTS `task_instance`;
CREATE TABLE `task_instance` (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'id',
  `task_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '任务id',
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '状态',
  `progress` float DEFAULT NULL COMMENT '任务进度',
  `start_time` timestamp NULL DEFAULT NULL COMMENT '开始时间',
  `end_time` timestamp NULL DEFAULT NULL COMMENT '结束时间',
  `result` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '执行结果',
  `parent_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '父任务id',
  `worker` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '运行节点',
  `retry_num` int DEFAULT NULL COMMENT '重试次数',
  `closed` smallint DEFAULT NULL COMMENT '是否已关闭',
  `node_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'dag任务节点id',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Records of task_instance
-- ----------------------------
BEGIN;
COMMIT;

-- ----------------------------
-- Table structure for task_template
-- ----------------------------
DROP TABLE IF EXISTS `task_template`;
CREATE TABLE `task_template` (
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '简介',
  `sort_no` float DEFAULT NULL COMMENT '排序',
  `del_flag` smallint DEFAULT NULL COMMENT '软删除标记',
  `create_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建者',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '修改者',
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '模版名称',
  `type` smallint DEFAULT NULL COMMENT '模版类型',
  `component` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '任务组件',
  `params` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '模版配置',
  `status` smallint DEFAULT NULL COMMENT '状态',
  `icon` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '任务图标',
  `code` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '模版编码',
  `runner_type` smallint DEFAULT NULL COMMENT '执行器类型',
  `runner_code` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '执行器代码',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Records of task_template
-- ----------------------------
BEGIN;
INSERT INTO `task_template` VALUES ('', 1, 0, 'admin', '2023-04-17 10:00:37', 'admin', '2023-08-13 10:25:02', '3bd8b6a5595d44f8b5a36b2e1e5f85f3', '动态任务测试模版', 2, '', '[\n  {\n    \"field\": \"code\",\n    \"component\": \"MonacoEditor\",\n    \"label\": \"代码\",\n    \"required\": true,\n    \"componentProps\": {\n      \"value\": \"print(111)\",\n      \"language\": \"python\"\n    }\n  },\n  {\n    \"field\": \"test\",\n    \"component\": \"Input\",\n    \"label\": \"测试字段1\",\n    \"required\": true\n  },\n  {\n    \"field\": \"test2\",\n    \"component\": \"InputNumber\",\n    \"label\": \"测试字段2\",\n    \"defualutValue\": 233,\n    \"required\": true\n  }\n]', 1, 'https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ', 'dynamicTask', 2, 'import time\ndef run(params, logger):\n    \'\'\'\n    任务执行函数\n    :param params: 任务参数\n    :param logger: 日志logger\n    :return:\n    \'\'\'\n    logger.info(str(params))\n    for i in range(5):\n        time.sleep(1)\n        logger.info(i)');
INSERT INTO `task_template` VALUES ('', 1, 0, 'admin', '2023-03-13 01:29:05', 'admin', '2023-08-13 10:25:08', '6f48c7155933452dbd706e88df4cb476', 'shell任务', 1, 'ShellTask', '{}', 1, 'https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ', 'ShellTask', 1, NULL);
INSERT INTO `task_template` VALUES ('', 1, 0, 'admin', '2023-07-08 07:23:21', 'admin', '2023-08-13 10:24:53', '825315ad5ef24462a33443a0d0bc0e6b', 'flink任务', 1, 'FlinkTask', '{}', 1, 'https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ', 'FlinkTask', 1, '');
INSERT INTO `task_template` VALUES ('', 1, 0, 'admin', '2023-03-13 03:24:27', 'admin', '2023-08-13 10:25:06', 'bab9faf461c24b9ca1ab3d9728683fca', 'spark任务', 1, 'SparkTask', '{}', 1, 'https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ', 'SparkTask', 1, NULL);
INSERT INTO `task_template` VALUES ('', 1, 0, 'admin', '2023-03-07 17:27:34', 'admin', '2023-08-13 10:25:10', 'd93d62d3b544420ba11caca64c86102f', 'python任务', 1, 'PythonTask', '\"{}\"', 1, 'https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ', 'PythonTask', 1, NULL);
INSERT INTO `task_template` VALUES ('', 1, 0, 'admin', '2023-03-24 16:56:20', 'admin', '2023-08-13 10:25:04', 'e177d70ffac7464fa72ff2da22a2f7fc', '数据集成任务', 1, 'EtlTask', '{}', 1, 'https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ', 'EtlTask', 1, NULL);
COMMIT;

SET FOREIGN_KEY_CHECKS = 1;
