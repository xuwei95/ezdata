-- ----------------------------
-- 1、部门表
-- ----------------------------
drop table if exists sys_dept;
create table sys_dept (
  dept_id           bigint(20)      not null auto_increment    comment '部门id',
  parent_id         bigint(20)      default 0                  comment '父部门id',
  ancestors         varchar(50)     default ''                 comment '祖级列表',
  dept_name         varchar(30)     default ''                 comment '部门名称',
  order_num         int(4)          default 0                  comment '显示顺序',
  leader            varchar(20)     default null               comment '负责人',
  phone             varchar(11)     default null               comment '联系电话',
  email             varchar(50)     default null               comment '邮箱',
  status            char(1)         default '0'                comment '部门状态（0正常 1停用）',
  del_flag          char(1)         default '0'                comment '删除标志（0代表存在 2代表删除）',
  create_by         varchar(64)     default ''                 comment '创建者',
  create_time 	    datetime                                   comment '创建时间',
  update_by         varchar(64)     default ''                 comment '更新者',
  update_time       datetime                                   comment '更新时间',
  primary key (dept_id)
) engine=innodb auto_increment=200 comment = '部门表';

-- ----------------------------
-- 初始化-部门表数据
-- ----------------------------
insert into sys_dept values(100,  0,   '0',          '集团总公司',   0, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', sysdate(), '', null);
insert into sys_dept values(101,  100, '0,100',      '深圳分公司', 1, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', sysdate(), '', null);
insert into sys_dept values(102,  100, '0,100',      '长沙分公司', 2, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', sysdate(), '', null);
insert into sys_dept values(103,  101, '0,100,101',  '研发部门',   1, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', sysdate(), '', null);
insert into sys_dept values(104,  101, '0,100,101',  '市场部门',   2, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', sysdate(), '', null);
insert into sys_dept values(105,  101, '0,100,101',  '测试部门',   3, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', sysdate(), '', null);
insert into sys_dept values(106,  101, '0,100,101',  '财务部门',   4, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', sysdate(), '', null);
insert into sys_dept values(107,  101, '0,100,101',  '运维部门',   5, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', sysdate(), '', null);
insert into sys_dept values(108,  102, '0,100,102',  '市场部门',   1, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', sysdate(), '', null);
insert into sys_dept values(109,  102, '0,100,102',  '财务部门',   2, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', sysdate(), '', null);


-- ----------------------------
-- 2、用户信息表
-- ----------------------------
drop table if exists sys_user;
create table sys_user (
  user_id           bigint(20)      not null auto_increment    comment '用户ID',
  dept_id           bigint(20)      default null               comment '部门ID',
  user_name         varchar(30)     not null                   comment '用户账号',
  nick_name         varchar(30)     not null                   comment '用户昵称',
  user_type         varchar(2)      default '00'               comment '用户类型（00系统用户）',
  email             varchar(50)     default ''                 comment '用户邮箱',
  phonenumber       varchar(11)     default ''                 comment '手机号码',
  sex               char(1)         default '0'                comment '用户性别（0男 1女 2未知）',
  avatar            varchar(100)    default ''                 comment '头像地址',
  password          varchar(100)    default ''                 comment '密码',
  status            char(1)         default '0'                comment '帐号状态（0正常 1停用）',
  del_flag          char(1)         default '0'                comment '删除标志（0代表存在 2代表删除）',
  login_ip          varchar(128)    default ''                 comment '最后登录IP',
  login_date        datetime                                   comment '最后登录时间',
  pwd_update_date   datetime                                   comment '密码最后更新时间',
  create_by         varchar(64)     default ''                 comment '创建者',
  create_time       datetime                                   comment '创建时间',
  update_by         varchar(64)     default ''                 comment '更新者',
  update_time       datetime                                   comment '更新时间',
  remark            varchar(500)    default null               comment '备注',
  primary key (user_id)
) engine=innodb auto_increment=100 comment = '用户信息表';

-- ----------------------------
-- 初始化-用户信息表数据
-- ----------------------------
insert into sys_user values(1,  103, 'admin',   '超级管理员', '00', 'niangao@163.com', '15888888888', '1', '', '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2', '0', '0', '127.0.0.1', sysdate(), sysdate(), 'admin', sysdate(), '', null, '管理员');
insert into sys_user values(2,  105, 'test', '测试用户', 			'00', 'test@qq.com',  '15666666666', '1', '', '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2', '0', '0', '127.0.0.1', sysdate(), sysdate(), 'admin', sysdate(), '', null, '测试员');


-- ----------------------------
-- 3、岗位信息表
-- ----------------------------
drop table if exists sys_post;
create table sys_post
(
  post_id       bigint(20)      not null auto_increment    comment '岗位ID',
  post_code     varchar(64)     not null                   comment '岗位编码',
  post_name     varchar(50)     not null                   comment '岗位名称',
  post_sort     int(4)          not null                   comment '显示顺序',
  status        char(1)         not null                   comment '状态（0正常 1停用）',
  create_by     varchar(64)     default ''                 comment '创建者',
  create_time   datetime                                   comment '创建时间',
  update_by     varchar(64)     default ''			       comment '更新者',
  update_time   datetime                                   comment '更新时间',
  remark        varchar(500)    default null               comment '备注',
  primary key (post_id)
) engine=innodb comment = '岗位信息表';

-- ----------------------------
-- 初始化-岗位信息表数据
-- ----------------------------
insert into sys_post values(1, 'ceo',  '董事长',    1, '0', 'admin', sysdate(), '', null, '');
insert into sys_post values(2, 'se',   '项目经理',  2, '0', 'admin', sysdate(), '', null, '');
insert into sys_post values(3, 'hr',   '人力资源',  3, '0', 'admin', sysdate(), '', null, '');
insert into sys_post values(4, 'user', '普通员工',  4, '0', 'admin', sysdate(), '', null, '');


-- ----------------------------
-- 4、角色信息表
-- ----------------------------
drop table if exists sys_role;
create table sys_role (
  role_id              bigint(20)      not null auto_increment    comment '角色ID',
  role_name            varchar(30)     not null                   comment '角色名称',
  role_key             varchar(100)    not null                   comment '角色权限字符串',
  role_sort            int(4)          not null                   comment '显示顺序',
  data_scope           char(1)         default '1'                comment '数据范围（1：全部数据权限 2：自定数据权限 3：本部门数据权限 4：本部门及以下数据权限）',
  menu_check_strictly  tinyint(1)      default 1                  comment '菜单树选择项是否关联显示',
  dept_check_strictly  tinyint(1)      default 1                  comment '部门树选择项是否关联显示',
  status               char(1)         not null                   comment '角色状态（0正常 1停用）',
  del_flag             char(1)         default '0'                comment '删除标志（0代表存在 2代表删除）',
  create_by            varchar(64)     default ''                 comment '创建者',
  create_time          datetime                                   comment '创建时间',
  update_by            varchar(64)     default ''                 comment '更新者',
  update_time          datetime                                   comment '更新时间',
  remark               varchar(500)    default null               comment '备注',
  primary key (role_id)
) engine=innodb auto_increment=100 comment = '角色信息表';

-- ----------------------------
-- 初始化-角色信息表数据
-- ----------------------------
insert into sys_role values('1', '超级管理员',  'admin',  1, 1, 1, 1, '0', '0', 'admin', sysdate(), '', null, '超级管理员');
insert into sys_role values('2', '普通角色',    'common', 2, 2, 1, 1, '0', '0', 'admin', sysdate(), '', null, '普通角色');
insert into sys_role values('3', '数据管理员',  'data_admin', 3, 1, 1, 1, '0', '0', 'admin', sysdate(), '', null, '数据管理模块管理员:数据源/模型/查询/接口/集成/令牌');


-- ----------------------------
-- 5、菜单权限表
-- ----------------------------
drop table if exists sys_menu;
create table sys_menu (
  menu_id           bigint(20)      not null auto_increment    comment '菜单ID',
  menu_name         varchar(50)     not null                   comment '菜单名称',
  parent_id         bigint(20)      default 0                  comment '父菜单ID',
  order_num         int(4)          default 0                  comment '显示顺序',
  path              varchar(200)    default ''                 comment '路由地址',
  component         varchar(255)    default null               comment '组件路径',
  query             varchar(255)    default null               comment '路由参数',
  route_name        varchar(50)     default ''                 comment '路由名称',
  is_frame          int(1)          default 1                  comment '是否为外链（0是 1否）',
  is_cache          int(1)          default 0                  comment '是否缓存（0缓存 1不缓存）',
  menu_type         char(1)         default ''                 comment '菜单类型（M目录 C菜单 F按钮）',
  visible           char(1)         default 0                  comment '菜单状态（0显示 1隐藏）',
  status            char(1)         default 0                  comment '菜单状态（0正常 1停用）',
  perms             varchar(100)    default null               comment '权限标识',
  icon              varchar(100)    default '#'                comment '菜单图标',
  create_by         varchar(64)     default ''                 comment '创建者',
  create_time       datetime                                   comment '创建时间',
  update_by         varchar(64)     default ''                 comment '更新者',
  update_time       datetime                                   comment '更新时间',
  remark            varchar(500)    default ''                 comment '备注',
  primary key (menu_id)
) engine=innodb auto_increment=2000 comment = '菜单权限表';

-- ----------------------------
-- 初始化-菜单信息表数据
-- ----------------------------
-- 一级菜单
insert into sys_menu values('1',  '系统管理', '0', '4',  'system',           null, '', '', 1, 0, 'M', '0', '0', '', 'system',   'admin', sysdate(), '', null, '系统管理目录');
insert into sys_menu values('2',  '系统监控', '0', '5',  'monitor',          null, '', '', 1, 0, 'M', '0', '0', '', 'monitor',  'admin', sysdate(), '', null, '系统监控目录');
insert into sys_menu values('3',  '系统工具', '0', '6',  'tool',             null, '', '', 1, 0, 'M', '0', '0', '', 'tool',     'admin', sysdate(), '', null, '系统工具目录');
insert into sys_menu values('4',  'AI 管理', '0', '1',  'ai',               null, '', '', 1, 0, 'M', '0', '0', '', 'ai-manage', 'admin', sysdate(), '', null, 'AI 管理目录');
-- 二级菜单
insert into sys_menu values('100',  '用户管理', '1',   '1', 'user',                'system/user/index',                 '', '', 1, 0, 'C', '0', '0', 'system:user:list',                 'user',          'admin', sysdate(), '', null, '用户管理菜单');
insert into sys_menu values('101',  '角色管理', '1',   '2', 'role',                'system/role/index',                 '', '', 1, 0, 'C', '0', '0', 'system:role:list',                 'peoples',       'admin', sysdate(), '', null, '角色管理菜单');
insert into sys_menu values('102',  '菜单管理', '1',   '3', 'menu',                'system/menu/index',                 '', '', 1, 0, 'C', '0', '0', 'system:menu:list',                 'tree-table',    'admin', sysdate(), '', null, '菜单管理菜单');
insert into sys_menu values('103',  '部门管理', '1',   '4', 'dept',                'system/dept/index',                 '', '', 1, 0, 'C', '0', '0', 'system:dept:list',                 'tree',          'admin', sysdate(), '', null, '部门管理菜单');
insert into sys_menu values('104',  '岗位管理', '1',   '5', 'post',                'system/post/index',                 '', '', 1, 0, 'C', '0', '0', 'system:post:list',                 'post',          'admin', sysdate(), '', null, '岗位管理菜单');
insert into sys_menu values('105',  '字典管理', '1',   '6', 'dict',                'system/dict/index',                 '', '', 1, 0, 'C', '0', '0', 'system:dict:list',                 'dict',          'admin', sysdate(), '', null, '字典管理菜单');
insert into sys_menu values('106',  '参数设置', '1',   '7', 'config',              'system/config/index',               '', '', 1, 0, 'C', '0', '0', 'system:config:list',               'edit',          'admin', sysdate(), '', null, '参数设置菜单');
insert into sys_menu values('107',  '通知公告', '1',   '8', 'notice',              'system/notice/index',               '', '', 1, 0, 'C', '0', '0', 'system:notice:list',               'message',       'admin', sysdate(), '', null, '通知公告菜单');
insert into sys_menu values('108',  '日志管理', '1',   '9', 'log',                 '',                                  '', '', 1, 0, 'M', '0', '0', '',                                 'log',           'admin', sysdate(), '', null, '日志管理菜单');
insert into sys_menu values('109',  '在线用户', '2',   '1', 'online',              'monitor/online/index',              '', '', 1, 0, 'C', '0', '0', 'monitor:online:list',              'online',        'admin', sysdate(), '', null, '在线用户菜单');
insert into sys_menu values('110',  '定时任务', '2',   '2', 'job',                 'monitor/job/index',                 '', '', 1, 0, 'C', '0', '0', 'monitor:job:list',                 'job',           'admin', sysdate(), '', null, '定时任务菜单');
insert into sys_menu values('111',  '数据监控', '2',   '3', 'druid',               'monitor/druid/index',               '', '', 1, 0, 'C', '0', '0', 'monitor:druid:list',               'druid',         'admin', sysdate(), '', null, '数据监控菜单');
insert into sys_menu values('112',  '服务监控', '2',   '4', 'server',              'monitor/server/index',              '', '', 1, 0, 'C', '0', '0', 'monitor:server:list',              'server',        'admin', sysdate(), '', null, '服务监控菜单');
insert into sys_menu values('113',  '缓存监控', '2',   '5', 'cache',               'monitor/cache/index',               '', '', 1, 0, 'C', '0', '0', 'monitor:cache:list',               'redis',         'admin', sysdate(), '', null, '缓存监控菜单');
insert into sys_menu values('114',  '缓存列表', '2',   '6', 'cacheList',           'monitor/cache/list',                '', '', 1, 0, 'C', '0', '0', 'monitor:cache:list',               'redis-list',    'admin', sysdate(), '', null, '缓存列表菜单');
insert into sys_menu values('120',  '传输加密', '2',   '7', 'transportCrypto',     'monitor/transportCrypto/index',     '', '', 1, 0, 'C', '0', '0', 'monitor:transportCrypto:list',     'chart',         'admin', sysdate(), '', null, '传输加密监控菜单');
insert into sys_menu values('115',  '表单构建', '3',   '1', 'build',               'tool/build/index',                  '', '', 1, 0, 'C', '0', '0', 'tool:build:list',                  'build',         'admin', sysdate(), '', null, '表单构建菜单');
insert into sys_menu values('116',  '代码生成', '3',   '2', 'gen',                 'tool/gen/index',                    '', '', 1, 0, 'C', '0', '0', 'tool:gen:list',                    'code',          'admin', sysdate(), '', null, '代码生成菜单');
insert into sys_menu values('117',  '系统接口', '3',   '3', 'swagger',             'tool/swagger/index',                '', '', 1, 0, 'C', '0', '0', 'tool:swagger:list',                'swagger',       'admin', sysdate(), '', null, '系统接口菜单');
insert into sys_menu values('119',  'AI 对话', '4',   '1', 'chat',                'ai/chat/index',                     '', '', 1, 0, 'C', '0', '0', 'ai:chat:list',                     'ai-chat',       'admin', sysdate(), '', null, 'AI 对话菜单');
insert into sys_menu values('118',  '模型管理', '4',   '3', 'model',               'ai/model/index',                    '', '', 1, 0, 'C', '0', '0', 'ai:model:list',                    'ai-model',      'admin', sysdate(), '', null, '模型管理菜单');
insert into sys_menu values('121',  '工具管理', '4',   '4', 'tool',                'ai/tool/index',                     '', 'AiTool', 1, 0, 'C', '0', '0', 'ai:tool:list',                     'tool',          'admin', sysdate(), '', null, '工具管理菜单');
-- 三级菜单
insert into sys_menu values('500',  '操作日志', '108', '1', 'operlog',    'monitor/operlog/index',    '', '', 1, 0, 'C', '0', '0', 'monitor:operlog:list',    'form',          'admin', sysdate(), '', null, '操作日志菜单');
insert into sys_menu values('501',  '登录日志', '108', '2', 'logininfor', 'monitor/logininfor/index', '', '', 1, 0, 'C', '0', '0', 'monitor:logininfor:list', 'logininfor',    'admin', sysdate(), '', null, '登录日志菜单');
-- 用户管理按钮
insert into sys_menu values('1000', '用户查询', '100', '1',  '', '', '', '', 1, 0, 'F', '0', '0', 'system:user:query',          '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1001', '用户新增', '100', '2',  '', '', '', '', 1, 0, 'F', '0', '0', 'system:user:add',            '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1002', '用户修改', '100', '3',  '', '', '', '', 1, 0, 'F', '0', '0', 'system:user:edit',           '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1003', '用户删除', '100', '4',  '', '', '', '', 1, 0, 'F', '0', '0', 'system:user:remove',         '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1004', '用户导出', '100', '5',  '', '', '', '', 1, 0, 'F', '0', '0', 'system:user:export',         '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1005', '用户导入', '100', '6',  '', '', '', '', 1, 0, 'F', '0', '0', 'system:user:import',         '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1006', '重置密码', '100', '7',  '', '', '', '', 1, 0, 'F', '0', '0', 'system:user:resetPwd',       '#', 'admin', sysdate(), '', null, '');
-- 角色管理按钮
insert into sys_menu values('1007', '角色查询', '101', '1',  '', '', '', '', 1, 0, 'F', '0', '0', 'system:role:query',          '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1008', '角色新增', '101', '2',  '', '', '', '', 1, 0, 'F', '0', '0', 'system:role:add',            '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1009', '角色修改', '101', '3',  '', '', '', '', 1, 0, 'F', '0', '0', 'system:role:edit',           '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1010', '角色删除', '101', '4',  '', '', '', '', 1, 0, 'F', '0', '0', 'system:role:remove',         '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1011', '角色导出', '101', '5',  '', '', '', '', 1, 0, 'F', '0', '0', 'system:role:export',         '#', 'admin', sysdate(), '', null, '');
-- 菜单管理按钮
insert into sys_menu values('1012', '菜单查询', '102', '1',  '', '', '', '', 1, 0, 'F', '0', '0', 'system:menu:query',          '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1013', '菜单新增', '102', '2',  '', '', '', '', 1, 0, 'F', '0', '0', 'system:menu:add',            '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1014', '菜单修改', '102', '3',  '', '', '', '', 1, 0, 'F', '0', '0', 'system:menu:edit',           '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1015', '菜单删除', '102', '4',  '', '', '', '', 1, 0, 'F', '0', '0', 'system:menu:remove',         '#', 'admin', sysdate(), '', null, '');
-- 部门管理按钮
insert into sys_menu values('1016', '部门查询', '103', '1',  '', '', '', '', 1, 0, 'F', '0', '0', 'system:dept:query',          '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1017', '部门新增', '103', '2',  '', '', '', '', 1, 0, 'F', '0', '0', 'system:dept:add',            '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1018', '部门修改', '103', '3',  '', '', '', '', 1, 0, 'F', '0', '0', 'system:dept:edit',           '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1019', '部门删除', '103', '4',  '', '', '', '', 1, 0, 'F', '0', '0', 'system:dept:remove',         '#', 'admin', sysdate(), '', null, '');
-- 岗位管理按钮
insert into sys_menu values('1020', '岗位查询', '104', '1',  '', '', '', '', 1, 0, 'F', '0', '0', 'system:post:query',          '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1021', '岗位新增', '104', '2',  '', '', '', '', 1, 0, 'F', '0', '0', 'system:post:add',            '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1022', '岗位修改', '104', '3',  '', '', '', '', 1, 0, 'F', '0', '0', 'system:post:edit',           '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1023', '岗位删除', '104', '4',  '', '', '', '', 1, 0, 'F', '0', '0', 'system:post:remove',         '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1024', '岗位导出', '104', '5',  '', '', '', '', 1, 0, 'F', '0', '0', 'system:post:export',         '#', 'admin', sysdate(), '', null, '');
-- 字典管理按钮
insert into sys_menu values('1025', '字典查询', '105', '1', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:dict:query',          '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1026', '字典新增', '105', '2', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:dict:add',            '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1027', '字典修改', '105', '3', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:dict:edit',           '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1028', '字典删除', '105', '4', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:dict:remove',         '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1029', '字典导出', '105', '5', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:dict:export',         '#', 'admin', sysdate(), '', null, '');
-- 参数设置按钮
insert into sys_menu values('1030', '参数查询', '106', '1', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:config:query',        '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1031', '参数新增', '106', '2', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:config:add',          '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1032', '参数修改', '106', '3', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:config:edit',         '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1033', '参数删除', '106', '4', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:config:remove',       '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1034', '参数导出', '106', '5', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:config:export',       '#', 'admin', sysdate(), '', null, '');
-- 通知公告按钮
insert into sys_menu values('1035', '公告查询', '107', '1', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:notice:query',        '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1036', '公告新增', '107', '2', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:notice:add',          '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1037', '公告修改', '107', '3', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:notice:edit',         '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1038', '公告删除', '107', '4', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:notice:remove',       '#', 'admin', sysdate(), '', null, '');
-- 操作日志按钮
insert into sys_menu values('1039', '操作查询', '500', '1', '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:operlog:query',      '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1040', '操作删除', '500', '2', '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:operlog:remove',     '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1041', '日志导出', '500', '3', '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:operlog:export',     '#', 'admin', sysdate(), '', null, '');
-- 登录日志按钮
insert into sys_menu values('1042', '登录查询', '501', '1', '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:logininfor:query',   '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1043', '登录删除', '501', '2', '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:logininfor:remove',  '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1044', '日志导出', '501', '3', '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:logininfor:export',  '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1045', '账户解锁', '501', '4', '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:logininfor:unlock',  '#', 'admin', sysdate(), '', null, '');
-- 在线用户按钮
insert into sys_menu values('1046', '在线查询', '109', '1', '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:online:query',       '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1047', '批量强退', '109', '2', '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:online:batchLogout', '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1048', '单条强退', '109', '3', '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:online:forceLogout', '#', 'admin', sysdate(), '', null, '');
-- 定时任务按钮
insert into sys_menu values('1049', '任务查询', '110', '1', '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:job:query',          '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1050', '任务新增', '110', '2', '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:job:add',            '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1051', '任务修改', '110', '3', '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:job:edit',           '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1052', '任务删除', '110', '4', '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:job:remove',         '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1053', '状态修改', '110', '5', '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:job:changeStatus',   '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1054', '任务导出', '110', '6', '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:job:export',         '#', 'admin', sysdate(), '', null, '');
-- 代码生成按钮
insert into sys_menu values('1055', '生成查询', '116', '1', '#', '', '', '', 1, 0, 'F', '0', '0', 'tool:gen:query',             '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1056', '生成修改', '116', '2', '#', '', '', '', 1, 0, 'F', '0', '0', 'tool:gen:edit',              '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1057', '生成删除', '116', '3', '#', '', '', '', 1, 0, 'F', '0', '0', 'tool:gen:remove',            '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1058', '导入代码', '116', '4', '#', '', '', '', 1, 0, 'F', '0', '0', 'tool:gen:import',            '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1059', '预览代码', '116', '5', '#', '', '', '', 1, 0, 'F', '0', '0', 'tool:gen:preview',           '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1060', '生成代码', '116', '6', '#', '', '', '', 1, 0, 'F', '0', '0', 'tool:gen:code',              '#', 'admin', sysdate(), '', null, '');
-- 模型管理按钮
insert into sys_menu values('1061', '模型查询', '118', '1', '#', '', '', '', 1, 0, 'F', '0', '0', 'ai:model:query',             '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1062', '模型新增', '118', '2', '#', '', '', '', 1, 0, 'F', '0', '0', 'ai:model:add',               '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1063', '模型修改', '118', '3', '#', '', '', '', 1, 0, 'F', '0', '0', 'ai:model:edit',              '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1064', '模型删除', '118', '4', '#', '', '', '', 1, 0, 'F', '0', '0', 'ai:model:remove',            '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1065', '工具查询', '121', '1', '#', '', '', '', 1, 0, 'F', '0', '0', 'ai:tool:query',              '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1066', '工具新增', '121', '2', '#', '', '', '', 1, 0, 'F', '0', '0', 'ai:tool:add',                '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1067', '工具修改', '121', '3', '#', '', '', '', 1, 0, 'F', '0', '0', 'ai:tool:edit',               '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1068', '工具删除', '121', '4', '#', '', '', '', 1, 0, 'F', '0', '0', 'ai:tool:remove',             '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('122',  '应用管理', '4',   '2', 'app',                 'ai/app/index',                      '', 'AiApp', 1, 0, 'C', '0', '0', 'ai:app:list',                      'component',     'admin', sysdate(), '', null, 'AI应用管理菜单');
insert into sys_menu values('123',  '用量统计', '4',   '5', 'metrics',             'ai/metrics/index',                  '', 'AiMetrics', 1, 0, 'C', '0', '0', 'ai:metrics:list',              'chart',         'admin', sysdate(), '', null, 'AI用量可观测菜单');
insert into sys_menu values('1069', '应用查询', '122', '1', '#', '', '', '', 1, 0, 'F', '0', '0', 'ai:app:query',               '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1070', '应用新增', '122', '2', '#', '', '', '', 1, 0, 'F', '0', '0', 'ai:app:add',                 '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1071', '应用修改', '122', '3', '#', '', '', '', 1, 0, 'F', '0', '0', 'ai:app:edit',                '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('1072', '应用删除', '122', '4', '#', '', '', '', 1, 0, 'F', '0', '0', 'ai:app:remove',              '#', 'admin', sysdate(), '', null, '');


-- ----------------------------
-- 6、用户和角色关联表  用户N-1角色
-- ----------------------------
drop table if exists sys_user_role;
create table sys_user_role (
  user_id   bigint(20) not null comment '用户ID',
  role_id   bigint(20) not null comment '角色ID',
  primary key(user_id, role_id)
) engine=innodb comment = '用户和角色关联表';

-- ----------------------------
-- 初始化-用户和角色关联表数据
-- ----------------------------
insert into sys_user_role values ('1', '1');
insert into sys_user_role values ('2', '2');


-- ----------------------------
-- 7、角色和菜单关联表  角色1-N菜单
-- ----------------------------
drop table if exists sys_role_menu;
create table sys_role_menu (
  role_id   bigint(20) not null comment '角色ID',
  menu_id   bigint(20) not null comment '菜单ID',
  primary key(role_id, menu_id)
) engine=innodb comment = '角色和菜单关联表';

-- ----------------------------
-- 初始化-角色和菜单关联表数据
-- ----------------------------
insert into sys_role_menu values ('2', '4');
insert into sys_role_menu values ('2', '119');
insert into sys_role_menu values ('2', '122');
insert into sys_role_menu values ('2', '123');
insert into sys_role_menu values ('2', '1069');
insert into sys_role_menu values ('2', '1070');
insert into sys_role_menu values ('2', '1071');
insert into sys_role_menu values ('2', '1072');
insert into sys_role_menu values ('2', '2100');
insert into sys_role_menu values ('2', '2101');
insert into sys_role_menu values ('2', '2102');
insert into sys_role_menu values ('2', '2103');
insert into sys_role_menu values ('2', '2110');
insert into sys_role_menu values ('2', '2111');
insert into sys_role_menu values ('2', '2112');
insert into sys_role_menu values ('2', '2113');
insert into sys_role_menu values ('2', '2114');
insert into sys_role_menu values ('2', '2115');
insert into sys_role_menu values ('2', '2120');
insert into sys_role_menu values ('2', '2121');
insert into sys_role_menu values ('2', '2122');
insert into sys_role_menu values ('2', '2123');
insert into sys_role_menu values ('2', '2130');
insert into sys_role_menu values ('2', '2131');
insert into sys_role_menu values ('2', '2132');
insert into sys_role_menu values ('2', '2140');
insert into sys_role_menu values ('2', '2141');
insert into sys_role_menu values ('2', '2142');
insert into sys_role_menu values ('2', '2143');
insert into sys_role_menu values ('2', '2200');
insert into sys_role_menu values ('2', '2201');
insert into sys_role_menu values ('2', '2202');
insert into sys_role_menu values ('2', '2210');
insert into sys_role_menu values ('2', '2211');
insert into sys_role_menu values ('2', '2212');
insert into sys_role_menu values ('2', '2213');
insert into sys_role_menu values ('2', '2220');
insert into sys_role_menu values ('2', '2221');
insert into sys_role_menu values ('2', '2222');
insert into sys_role_menu values ('2', '2300');
insert into sys_role_menu values ('2', '2301');
insert into sys_role_menu values ('2', '2310');
insert into sys_role_menu values ('2', '2311');
insert into sys_role_menu values ('2', '2312');
insert into sys_role_menu values ('2', '2313');
insert into sys_role_menu values ('2', '2314');
insert into sys_role_menu values ('2', '2315');
insert into sys_role_menu values ('2', '2316');
insert into sys_role_menu values ('2', '2317');
insert into sys_role_menu values ('2', '2318');
insert into sys_role_menu values ('2', '2319');
insert into sys_role_menu values ('2', '2320');
insert into sys_role_menu values ('2', '2321');
insert into sys_role_menu values ('2', '2322');
insert into sys_role_menu values ('2', '2323');
insert into sys_role_menu values ('2', '2400');
insert into sys_role_menu values ('2', '2401');
insert into sys_role_menu values ('2', '2402');
insert into sys_role_menu values ('2', '2410');
insert into sys_role_menu values ('2', '2411');
insert into sys_role_menu values ('2', '2412');

-- ----------------------------
-- 8、角色和部门关联表  角色1-N部门
-- ----------------------------
drop table if exists sys_role_dept;
create table sys_role_dept (
  role_id   bigint(20) not null comment '角色ID',
  dept_id   bigint(20) not null comment '部门ID',
  primary key(role_id, dept_id)
) engine=innodb comment = '角色和部门关联表';

-- ----------------------------
-- 初始化-角色和部门关联表数据
-- ----------------------------
insert into sys_role_dept values ('2', '100');
insert into sys_role_dept values ('2', '101');
insert into sys_role_dept values ('2', '105');


-- ----------------------------
-- 9、用户与岗位关联表  用户1-N岗位
-- ----------------------------
drop table if exists sys_user_post;
create table sys_user_post
(
  user_id   bigint(20) not null comment '用户ID',
  post_id   bigint(20) not null comment '岗位ID',
  primary key (user_id, post_id)
) engine=innodb comment = '用户与岗位关联表';

-- ----------------------------
-- 初始化-用户与岗位关联表数据
-- ----------------------------
insert into sys_user_post values ('1', '1');
insert into sys_user_post values ('2', '2');


-- ----------------------------
-- 10、操作日志记录
-- ----------------------------
drop table if exists sys_oper_log;
create table sys_oper_log (
  oper_id           bigint(20)      not null auto_increment    comment '日志主键',
  title             varchar(50)     default ''                 comment '模块标题',
  business_type     int(2)          default 0                  comment '业务类型（0其它 1新增 2修改 3删除）',
  method            varchar(100)    default ''                 comment '方法名称',
  request_method    varchar(10)     default ''                 comment '请求方式',
  operator_type     int(1)          default 0                  comment '操作类别（0其它 1后台用户 2手机端用户）',
  oper_name         varchar(50)     default ''                 comment '操作人员',
  dept_name         varchar(50)     default ''                 comment '部门名称',
  oper_url          varchar(255)    default ''                 comment '请求URL',
  oper_ip           varchar(128)    default ''                 comment '主机地址',
  oper_location     varchar(255)    default ''                 comment '操作地点',
  oper_param        varchar(2000)   default ''                 comment '请求参数',
  json_result       varchar(2000)   default ''                 comment '返回参数',
  status            int(1)          default 0                  comment '操作状态（0正常 1异常）',
  error_msg         varchar(2000)   default ''                 comment '错误消息',
  oper_time         datetime                                   comment '操作时间',
  cost_time         bigint(20)      default 0                  comment '消耗时间',
  primary key (oper_id),
  key idx_sys_oper_log_bt (business_type),
  key idx_sys_oper_log_s  (status),
  key idx_sys_oper_log_ot (oper_time)
) engine=innodb auto_increment=100 comment = '操作日志记录';


-- ----------------------------
-- 11、字典类型表
-- ----------------------------
drop table if exists sys_dict_type;
create table sys_dict_type
(
  dict_id          bigint(20)      not null auto_increment    comment '字典主键',
  dict_name        varchar(100)    default ''                 comment '字典名称',
  dict_type        varchar(100)    default ''                 comment '字典类型',
  status           char(1)         default '0'                comment '状态（0正常 1停用）',
  create_by        varchar(64)     default ''                 comment '创建者',
  create_time      datetime                                   comment '创建时间',
  update_by        varchar(64)     default ''                 comment '更新者',
  update_time      datetime                                   comment '更新时间',
  remark           varchar(500)    default null               comment '备注',
  primary key (dict_id),
  unique (dict_type)
) engine=innodb auto_increment=100 comment = '字典类型表';

insert into sys_dict_type values(1,  '用户性别',     'sys_user_sex',        '0', 'admin', sysdate(), '', null, '用户性别列表');
insert into sys_dict_type values(2,  '菜单状态',     'sys_show_hide',       '0', 'admin', sysdate(), '', null, '菜单状态列表');
insert into sys_dict_type values(3,  '系统开关',     'sys_normal_disable',  '0', 'admin', sysdate(), '', null, '系统开关列表');
insert into sys_dict_type values(4,  '任务状态',     'sys_job_status',      '0', 'admin', sysdate(), '', null, '任务状态列表');
insert into sys_dict_type values(5,  '任务分组',     'sys_job_group',       '0', 'admin', sysdate(), '', null, '任务分组列表');
insert into sys_dict_type values(6,  '任务执行器',   'sys_job_executor',    '0', 'admin', sysdate(), '', null, '任务执行器列表');
insert into sys_dict_type values(7,  '系统是否',     'sys_yes_no',          '0', 'admin', sysdate(), '', null, '系统是否列表');
insert into sys_dict_type values(8,  '通知类型',     'sys_notice_type',     '0', 'admin', sysdate(), '', null, '通知类型列表');
insert into sys_dict_type values(9,  '通知状态', 	   'sys_notice_status',   '0', 'admin', sysdate(), '', null, '通知状态列表');
insert into sys_dict_type values(10, '操作类型', 	   'sys_oper_type',       '0', 'admin', sysdate(), '', null, '操作类型列表');
insert into sys_dict_type values(11, '系统状态',     'sys_common_status',   '0', 'admin', sysdate(), '', null, '登录状态列表');
insert into sys_dict_type values(12, 'AI模型提供商', 'ai_provider_type',    '0', 'admin', sysdate(), '', null, 'AI模型提供商列表');
insert into sys_dict_type values(13, '任务运行队列', 'task_run_queue',      '0', 'admin', sysdate(), '', null, '任务调度运行队列列表');


-- ----------------------------
-- 12、字典数据表
-- ----------------------------
drop table if exists sys_dict_data;
create table sys_dict_data
(
  dict_code        bigint(20)      not null auto_increment    comment '字典编码',
  dict_sort        int(4)          default 0                  comment '字典排序',
  dict_label       varchar(100)    default ''                 comment '字典标签',
  dict_value       varchar(100)    default ''                 comment '字典键值',
  dict_type        varchar(100)    default ''                 comment '字典类型',
  css_class        varchar(100)    default null               comment '样式属性（其他样式扩展）',
  list_class       varchar(100)    default null               comment '表格回显样式',
  is_default       char(1)         default 'N'                comment '是否默认（Y是 N否）',
  status           char(1)         default '0'                comment '状态（0正常 1停用）',
  create_by        varchar(64)     default ''                 comment '创建者',
  create_time      datetime                                   comment '创建时间',
  update_by        varchar(64)     default ''                 comment '更新者',
  update_time      datetime                                   comment '更新时间',
  remark           varchar(500)    default null               comment '备注',
  primary key (dict_code)
) engine=innodb auto_increment=100 comment = '字典数据表';

insert into sys_dict_data values(1,  1,  '男',             '0',                'sys_user_sex',        '',   '',        'Y', '0', 'admin', sysdate(), '', null, '性别男');
insert into sys_dict_data values(2,  2,  '女',             '1',                'sys_user_sex',        '',   '',        'N', '0', 'admin', sysdate(), '', null, '性别女');
insert into sys_dict_data values(3,  3,  '未知',            '2',                'sys_user_sex',        '',   '',        'N', '0', 'admin', sysdate(), '', null, '性别未知');
insert into sys_dict_data values(4,  1,  '显示',            '0',                'sys_show_hide',       '',   'primary', 'Y', '0', 'admin', sysdate(), '', null, '显示菜单');
insert into sys_dict_data values(5,  2,  '隐藏',            '1',                'sys_show_hide',       '',   'danger',  'N', '0', 'admin', sysdate(), '', null, '隐藏菜单');
insert into sys_dict_data values(6,  1,  '正常',            '0',                'sys_normal_disable',  '',   'primary', 'Y', '0', 'admin', sysdate(), '', null, '正常状态');
insert into sys_dict_data values(7,  2,  '停用',            '1',                'sys_normal_disable',  '',   'danger',  'N', '0', 'admin', sysdate(), '', null, '停用状态');
insert into sys_dict_data values(8,  1,  '正常',            '0',                'sys_job_status',      '',   'primary', 'Y', '0', 'admin', sysdate(), '', null, '正常状态');
insert into sys_dict_data values(9,  2,  '暂停',            '1',                'sys_job_status',      '',   'danger',  'N', '0', 'admin', sysdate(), '', null, '停用状态');
insert into sys_dict_data values(10, 1,  '默认',            'default',          'sys_job_group',       '',   '',        'Y', '0', 'admin', sysdate(), '', null, '默认分组');
insert into sys_dict_data values(11, 2,  '数据库',          'sqlalchemy',       'sys_job_group',       '',   '',        'N', '0', 'admin', sysdate(), '', null, '数据库分组');
insert into sys_dict_data values(12, 3,  'redis',          'redis',  			     'sys_job_group',       '',   '',        'N', '0', 'admin', sysdate(), '', null, 'reids分组');
insert into sys_dict_data values(13, 1,  '默认',            'default',  		    'sys_job_executor',    '',   '',        'N', '0', 'admin', sysdate(), '', null, '线程池');
insert into sys_dict_data values(14, 2,  '进程池',          'processpool',      'sys_job_executor',    '',   '',        'N', '0', 'admin', sysdate(), '', null, '进程池');
insert into sys_dict_data values(15, 1,  '是',              'Y',       		      'sys_yes_no',          '',   'primary', 'Y', '0', 'admin', sysdate(), '', null, '系统默认是');
insert into sys_dict_data values(16, 2,  '否',              'N',       		      'sys_yes_no',          '',   'danger',  'N', '0', 'admin', sysdate(), '', null, '系统默认否');
insert into sys_dict_data values(17, 1,  '通知',            '1',       		      'sys_notice_type',     '',   'warning', 'Y', '0', 'admin', sysdate(), '', null, '通知');
insert into sys_dict_data values(18, 2,  '公告',            '2',       		      'sys_notice_type',     '',   'success', 'N', '0', 'admin', sysdate(), '', null, '公告');
insert into sys_dict_data values(19, 1,  '正常',            '0',       		      'sys_notice_status',   '',   'primary', 'Y', '0', 'admin', sysdate(), '', null, '正常状态');
insert into sys_dict_data values(20, 2,  '关闭',            '1',       		      'sys_notice_status',   '',   'danger',  'N', '0', 'admin', sysdate(), '', null, '关闭状态');
insert into sys_dict_data values(21, 99, '其他',            '0',       		      'sys_oper_type',       '',   'info',    'N', '0', 'admin', sysdate(), '', null, '其他操作');
insert into sys_dict_data values(22, 1,  '新增',            '1',       		      'sys_oper_type',       '',   'info',    'N', '0', 'admin', sysdate(), '', null, '新增操作');
insert into sys_dict_data values(23, 2,  '修改',            '2',       		      'sys_oper_type',       '',   'info',    'N', '0', 'admin', sysdate(), '', null, '修改操作');
insert into sys_dict_data values(24, 3,  '删除',            '3',       		      'sys_oper_type',       '',   'danger',  'N', '0', 'admin', sysdate(), '', null, '删除操作');
insert into sys_dict_data values(25, 4,  '授权',            '4',       		      'sys_oper_type',       '',   'primary', 'N', '0', 'admin', sysdate(), '', null, '授权操作');
insert into sys_dict_data values(26, 5,  '导出',            '5',       		      'sys_oper_type',       '',   'warning', 'N', '0', 'admin', sysdate(), '', null, '导出操作');
insert into sys_dict_data values(27, 6,  '导入',            '6',       		      'sys_oper_type',       '',   'warning', 'N', '0', 'admin', sysdate(), '', null, '导入操作');
insert into sys_dict_data values(28, 7,  '强退',            '7',       		      'sys_oper_type',       '',   'danger',  'N', '0', 'admin', sysdate(), '', null, '强退操作');
insert into sys_dict_data values(29, 8,  '生成代码',         '8',       		     'sys_oper_type',       '',   'warning', 'N', '0', 'admin', sysdate(), '', null, '生成操作');
insert into sys_dict_data values(30, 9,  '清空数据',         '9',       		     'sys_oper_type',       '',   'danger',  'N', '0', 'admin', sysdate(), '', null, '清空操作');
insert into sys_dict_data values(31, 1,  '成功',            '0',       		       'sys_common_status',   '',   'primary', 'N', '0', 'admin', sysdate(), '', null, '正常状态');
insert into sys_dict_data values(32, 2,  '失败',            '1',       		       'sys_common_status',   '',   'danger',  'N', '0', 'admin', sysdate(), '', null, '停用状态');
insert into sys_dict_data values(33, 1,  'AIMLAPI',         'AIMLAPI',          'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'AIMLAPI');
insert into sys_dict_data values(34, 2,  'Anthropic',       'Anthropic',        'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'Anthropic');
insert into sys_dict_data values(35, 3,  'Cerebras',        'Cerebras',         'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'Cerebras');
insert into sys_dict_data values(36, 4,  'CerebrasOpenAI',  'CerebrasOpenAI',   'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'CerebrasOpenAI');
insert into sys_dict_data values(37, 5,  'Cohere',          'Cohere',           'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'Cohere');
insert into sys_dict_data values(38, 6,  'CometAPI',        'CometAPI',         'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'CometAPI');
insert into sys_dict_data values(39, 7,  'DashScope',       'DashScope',        'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'DashScope');
insert into sys_dict_data values(40, 8,  'DeepInfra',       'DeepInfra',        'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'DeepInfra');
insert into sys_dict_data values(41, 9,  'DeepSeek',        'DeepSeek',         'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'DeepSeek');
insert into sys_dict_data values(42, 10,  'Fireworks',       'Fireworks',        'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'Fireworks');
insert into sys_dict_data values(43, 11,  'Google',          'Google',           'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'Google');
insert into sys_dict_data values(44, 12,  'Groq',            'Groq',             'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'Groq');
insert into sys_dict_data values(45, 13,  'HuggingFace',     'HuggingFace',      'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'HuggingFace');
insert into sys_dict_data values(46, 14,  'LangDB',          'LangDB',           'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'LangDB');
insert into sys_dict_data values(47, 15,  'LiteLLM',         'LiteLLM',          'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'LiteLLM');
insert into sys_dict_data values(48, 16,  'LiteLLMOpenAI',   'LiteLLMOpenAI',    'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'LiteLLMOpenAI');
insert into sys_dict_data values(49, 17,  'LlamaCpp',        'LlamaCpp',         'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'LlamaCpp');
insert into sys_dict_data values(50, 18,  'LMStudio',        'LMStudio',         'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'LMStudio');
insert into sys_dict_data values(51, 19,  'Meta',            'Meta',             'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'Meta');
insert into sys_dict_data values(52, 20,  'Mistral',         'Mistral',          'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'Mistral');
insert into sys_dict_data values(53, 21,  'N1N',             'N1N',              'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'N1N');
insert into sys_dict_data values(54, 22,  'Nebius',          'Nebius',           'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'Nebius');
insert into sys_dict_data values(55, 23,  'Nexus',           'Nexus',            'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'Nexus');
insert into sys_dict_data values(56, 24,  'Nvidia',          'Nvidia',           'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'Nvidia');
insert into sys_dict_data values(57, 25,  'Ollama',          'Ollama',           'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'Ollama');
insert into sys_dict_data values(58, 26,  'OpenAI',          'OpenAI',           'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'OpenAI');
insert into sys_dict_data values(59, 27,  'OpenAIResponses', 'OpenAIResponses',  'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'OpenAIResponses');
insert into sys_dict_data values(60, 28,  'OpenRouter',      'OpenRouter',       'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'OpenRouter');
insert into sys_dict_data values(61, 29,  'Perplexity',      'Perplexity',       'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'Perplexity');
insert into sys_dict_data values(62, 30,  'Portkey',         'Portkey',          'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'Portkey');
insert into sys_dict_data values(63, 31,  'Requesty',        'Requesty',         'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'Requesty');
insert into sys_dict_data values(64, 32,  'Sambanova',       'Sambanova',        'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'Sambanova');
insert into sys_dict_data values(65, 33,  'SiliconFlow',     'SiliconFlow',      'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'SiliconFlow');
insert into sys_dict_data values(66, 34,  'Together',        'Together',         'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'Together');
insert into sys_dict_data values(67, 35,  'Vercel',          'Vercel',           'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'Vercel');
insert into sys_dict_data values(68, 36,  'VLLM',            'VLLM',             'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'VLLM');
insert into sys_dict_data values(69, 37,  'xAI',             'xAI',              'ai_provider_type',    '',   'info',    'N', '0', 'admin', sysdate(), '', null, 'xAI');
insert into sys_dict_data values(70, 1,   'default',         'default',          'task_run_queue',      '',   'primary', 'Y', '0', 'admin', sysdate(), '', null, '默认队列');


-- ----------------------------
-- 13、参数配置表
-- ----------------------------
drop table if exists sys_config;
create table sys_config (
  config_id         int(5)          not null auto_increment    comment '参数主键',
  config_name       varchar(100)    default ''                 comment '参数名称',
  config_key        varchar(100)    default ''                 comment '参数键名',
  config_value      varchar(500)    default ''                 comment '参数键值',
  config_type       char(1)         default 'N'                comment '系统内置（Y是 N否）',
  create_by         varchar(64)     default ''                 comment '创建者',
  create_time       datetime                                   comment '创建时间',
  update_by         varchar(64)     default ''                 comment '更新者',
  update_time       datetime                                   comment '更新时间',
  remark            varchar(500)    default null               comment '备注',
  primary key (config_id)
) engine=innodb auto_increment=100 comment = '参数配置表';

insert into sys_config values(1, '主框架页-默认皮肤样式名称',     'sys.index.skinName',            'skin-blue',     'Y', 'admin', sysdate(), '', null, '蓝色 skin-blue、绿色 skin-green、紫色 skin-purple、红色 skin-red、黄色 skin-yellow' );
insert into sys_config values(2, '用户管理-账号初始密码',         'sys.user.initPassword',         '123456',        'Y', 'admin', sysdate(), '', null, '初始化密码 123456' );
insert into sys_config values(3, '主框架页-侧边栏主题',           'sys.index.sideTheme',           'theme-dark',    'Y', 'admin', sysdate(), '', null, '深色主题theme-dark，浅色主题theme-light' );
insert into sys_config values(4, '账号自助-验证码开关',           'sys.account.captchaEnabled',    'true',          'Y', 'admin', sysdate(), '', null, '是否开启验证码功能（true开启，false关闭）');
insert into sys_config values(5, '账号自助-是否开启用户注册功能', 'sys.account.registerUser',      'false',         'Y', 'admin', sysdate(), '', null, '是否开启注册用户功能（true开启，false关闭）');
insert into sys_config values(6, '用户登录-黑名单列表',           'sys.login.blackIPList',         '',              'Y', 'admin', sysdate(), '', null, '设置登录IP黑名单限制，多个匹配项以;分隔，支持匹配（*通配、网段）');
insert into sys_config values(7, '用户管理-初始密码修改策略',     'sys.account.initPasswordModify',  '1',             'Y', 'admin', sysdate(), '', null, '0：初始密码修改策略关闭，没有任何提示，1：提醒用户，如果未修改初始密码，则在登录时就会提醒修改密码对话框');
insert into sys_config values(8, '用户管理-账号密码更新周期',     'sys.account.passwordValidateDays', '0',             'Y', 'admin', sysdate(), '', null, '密码更新周期（填写数字，数据初始化值为0不限制，若修改必须为大于0小于365的正整数），如果超过这个周期登录系统时，则在登录时就会提醒修改密码对话框');


-- ----------------------------
-- 14、系统访问记录
-- ----------------------------
drop table if exists sys_logininfor;
create table sys_logininfor (
  info_id        bigint(20)     not null auto_increment   comment '访问ID',
  user_name      varchar(50)    default ''                comment '用户账号',
  ipaddr         varchar(128)   default ''                comment '登录IP地址',
  login_location varchar(255)   default ''                comment '登录地点',
  browser        varchar(50)    default ''                comment '浏览器类型',
  os             varchar(50)    default ''                comment '操作系统',
  status         char(1)        default '0'               comment '登录状态（0成功 1失败）',
  msg            varchar(255)   default ''                comment '提示消息',
  login_time     datetime                                 comment '访问时间',
  primary key (info_id),
  key idx_sys_logininfor_s  (status),
  key idx_sys_logininfor_lt (login_time)
) engine=innodb auto_increment=100 comment = '系统访问记录';


-- ----------------------------
-- 15、定时任务调度表
-- ----------------------------
drop table if exists sys_job;
create table sys_job (
  job_id              bigint(20)    not null auto_increment    comment '任务ID',
  job_name            varchar(64)   default ''                 comment '任务名称',
  job_group           varchar(64)   default 'default'          comment '任务组名',
	job_executor 				varchar(64)   default 'default' 				 comment '任务执行器',
  invoke_target       varchar(500)  not null                   comment '调用目标字符串',
  job_args						varchar(255)	default ''								 comment '位置参数',
  job_kwargs					varchar(255)	default ''								 comment '关键字参数',
  cron_expression     varchar(255)  default ''                 comment 'cron执行表达式',
  misfire_policy      varchar(20)   default '3'                comment '计划执行错误策略（1立即执行 2执行一次 3放弃执行）',
  concurrent          char(1)       default '1'                comment '是否并发执行（0允许 1禁止）',
  status              char(1)       default '0'                comment '状态（0正常 1暂停）',
  create_by           varchar(64)   default ''                 comment '创建者',
  create_time         datetime                                 comment '创建时间',
  update_by           varchar(64)   default ''                 comment '更新者',
  update_time         datetime                                 comment '更新时间',
  remark              varchar(500)  default ''                 comment '备注信息',
  primary key (job_id, job_name, job_group)
) engine=innodb auto_increment=100 comment = '定时任务调度表';

insert into sys_job values(1, '系统默认（无参）', 'default', 'default', 'module_task.scheduler_test.job', NULL,   NULL, '0/10 * * * * ?', '3', '1', '1', 'admin', sysdate(), '', null, '');
insert into sys_job values(2, '系统默认（有参）', 'default', 'default', 'module_task.scheduler_test.job', 'test', NULL, '0/15 * * * * ?', '3', '1', '1', 'admin', sysdate(), '', null, '');
insert into sys_job values(3, '系统默认（多参）', 'default', 'default', 'module_task.scheduler_test.job', 'new',  '{\"test\": 111}', '0/20 * * * * ?', '3', '1', '1', 'admin', sysdate(), '', null, '');


-- ----------------------------
-- 16、定时任务调度日志表
-- ----------------------------
drop table if exists sys_job_log;
create table sys_job_log (
  job_log_id          bigint(20)     not null auto_increment    comment '任务日志ID',
  job_name            varchar(64)    not null                   comment '任务名称',
  job_group           varchar(64)    not null                   comment '任务组名',
  job_executor				varchar(64)		 not null										comment '任务执行器',
  invoke_target       varchar(500)   not null                   comment '调用目标字符串',
  job_args						varchar(255)	 default ''									comment '位置参数',
  job_kwargs					varchar(255)	 default ''									comment '关键字参数',
  job_trigger					varchar(255)	 default ''									comment '任务触发器',
  job_message         varchar(500)                              comment '日志信息',
  status              char(1)        default '0'                comment '执行状态（0正常 1失败）',
  exception_info      varchar(2000)  default ''                 comment '异常信息',
  create_time         datetime                                  comment '创建时间',
  primary key (job_log_id)
) engine=innodb comment = '定时任务调度日志表';


-- ----------------------------
-- 17、通知公告表
-- ----------------------------
drop table if exists sys_notice;
create table sys_notice (
  notice_id         int(4)          not null auto_increment    comment '公告ID',
  notice_title      varchar(50)     not null                   comment '公告标题',
  notice_type       char(1)         not null                   comment '公告类型（1通知 2公告）',
  notice_content    longblob        default null               comment '公告内容',
  status            char(1)         default '0'                comment '公告状态（0正常 1关闭）',
  create_by         varchar(64)     default ''                 comment '创建者',
  create_time       datetime                                   comment '创建时间',
  update_by         varchar(64)     default ''                 comment '更新者',
  update_time       datetime                                   comment '更新时间',
  remark            varchar(255)    default null               comment '备注',
  primary key (notice_id)
) engine=innodb auto_increment=10 comment = '通知公告表';

-- ----------------------------
-- 初始化-公告信息表数据
-- ----------------------------
insert into sys_notice values('1', '温馨提醒：2018-07-01 vfadmin新版本发布啦', '2', '新版本内容', '0', 'admin', sysdate(), '', null, '管理员');
insert into sys_notice values('2', '维护通知：2018-07-01 vfadmin系统凌晨维护', '1', '维护内容',   '0', 'admin', sysdate(), '', null, '管理员');


-- ----------------------------
-- 18、代码生成业务表
-- ----------------------------
drop table if exists gen_table;
create table gen_table (
  table_id          bigint(20)      not null auto_increment    comment '编号',
  table_name        varchar(200)    default ''                 comment '表名称',
  table_comment     varchar(500)    default ''                 comment '表描述',
  sub_table_name    varchar(64)     default null               comment '关联子表的表名',
  sub_table_fk_name varchar(64)     default null               comment '子表关联的外键名',
  class_name        varchar(100)    default ''                 comment '实体类名称',
  tpl_category      varchar(200)    default 'crud'             comment '使用的模板（crud单表操作 tree树表操作）',
  tpl_web_type      varchar(30)     default ''                 comment '前端模板类型（element-ui模版 element-plus模版）',
  package_name      varchar(100)                               comment '生成包路径',
  module_name       varchar(30)                                comment '生成模块名',
  business_name     varchar(30)                                comment '生成业务名',
  function_name     varchar(50)                                comment '生成功能名',
  function_author   varchar(50)                                comment '生成功能作者',
  gen_type          char(1)         default '0'                comment '生成代码方式（0zip压缩包 1自定义路径）',
  gen_path          varchar(200)    default '/'                comment '生成路径（不填默认项目路径）',
  options           varchar(1000)                              comment '其它生成选项',
  create_by         varchar(64)     default ''                 comment '创建者',
  create_time 	    datetime                                   comment '创建时间',
  update_by         varchar(64)     default ''                 comment '更新者',
  update_time       datetime                                   comment '更新时间',
  remark            varchar(500)    default null               comment '备注',
  primary key (table_id)
) engine=innodb auto_increment=1 comment = '代码生成业务表';


-- ----------------------------
-- 19、代码生成业务表字段
-- ----------------------------
drop table if exists gen_table_column;
create table gen_table_column (
  column_id         bigint(20)      not null auto_increment    comment '编号',
  table_id          bigint(20)                                 comment '归属表编号',
  column_name       varchar(200)                               comment '列名称',
  column_comment    varchar(500)                               comment '列描述',
  column_type       varchar(100)                               comment '列类型',
  python_type         varchar(500)                               comment 'PYTHON类型',
  python_field        varchar(200)                               comment 'PYTHON字段名',
  is_pk             char(1)                                    comment '是否主键（1是）',
  is_increment      char(1)                                    comment '是否自增（1是）',
  is_required       char(1)                                    comment '是否必填（1是）',
  is_unique         char(1)                                    comment '是否唯一（1是）',
  is_insert         char(1)                                    comment '是否为插入字段（1是）',
  is_edit           char(1)                                    comment '是否编辑字段（1是）',
  is_list           char(1)                                    comment '是否列表字段（1是）',
  is_query          char(1)                                    comment '是否查询字段（1是）',
  query_type        varchar(200)    default 'EQ'               comment '查询方式（等于、不等于、大于、小于、范围）',
  html_type         varchar(200)                               comment '显示类型（文本框、文本域、下拉框、复选框、单选框、日期控件）',
  dict_type         varchar(200)    default ''                 comment '字典类型',
  sort              int                                        comment '排序',
  create_by         varchar(64)     default ''                 comment '创建者',
  create_time 	    datetime                                   comment '创建时间',
  update_by         varchar(64)     default ''                 comment '更新者',
  update_time       datetime                                   comment '更新时间',
  primary key (column_id)
) engine=innodb auto_increment=1 comment = '代码生成业务表字段';


-- ----------------------------
-- 20、AI模型表
-- ----------------------------
drop table if exists ai_models;
create table ai_models (
  model_id          bigint(20)      not null auto_increment    comment '模型主键',
  model_code        varchar(100)    not null                   comment '模型编码',
  model_name        varchar(100)    default null               comment '模型名称',
  provider          varchar(50)     not null                   comment '提供商',
  model_sort        int(4)          not null                   comment '显示顺序',
  api_key           varchar(255)    default null               comment 'API Key',
  base_url          varchar(255)    default null               comment 'Base URL',
  model_type        varchar(50)     default null               comment '模型类型',
  max_tokens        int(11)         default null               comment '最大输出token',
  temperature       float           default null               comment '默认温度',
  support_reasoning char(1)         default 'N'                comment '是否支持推理',
  support_images    char(1)         default 'N'                comment '是否支持图片',
  status            char(1)         default '0'                comment '模型状态',
  user_id           bigint(20)                                 comment '用户ID',
  dept_id           bigint(20)                                 comment '部门ID',
  create_by         varchar(64)     default ''                 comment '创建者',
  create_time       datetime                                   comment '创建时间',
  update_by         varchar(64)     default ''                 comment '更新者',
  update_time       datetime                                   comment '更新时间',
  remark            varchar(500)    default null               comment '备注',
  primary key (model_id)
) engine=innodb auto_increment=1 comment = 'AI模型表';


-- ----------------------------
-- AI工具表(MCP 外部工具 + 内置工具)
-- ----------------------------
drop table if exists ai_tool;
create table ai_tool (
  tool_id           bigint(20)      not null auto_increment    comment '工具主键',
  name              varchar(100)    not null                   comment '工具名称',
  code              varchar(100)    not null                   comment '工具代码(唯一标识)',
  tool_type         varchar(50)     not null default 'mcp'     comment '工具类型: mcp/builtin',
  description       text                                       comment '工具描述',
  args              text                                       comment '工具配置JSON',
  status            char(1)         default '0'                comment '状态: 0启用 1停用',
  built_in          char(1)         default '0'                comment '是否内置: 1是(不可删/改code) 0否',
  user_id           bigint(20)                                 comment '用户ID',
  dept_id           bigint(20)                                 comment '部门ID',
  create_by         varchar(64)     default ''                 comment '创建者',
  create_time       datetime                                   comment '创建时间',
  update_by         varchar(64)     default ''                 comment '更新者',
  update_time       datetime                                   comment '更新时间',
  remark            varchar(500)    default null               comment '备注',
  tenant_id         bigint(20)                                 comment '租户ID(顶级部门)',
  primary key (tool_id),
  key ix_ai_tool_tenant_id (tenant_id)
) engine=innodb auto_increment=1 comment = 'AI工具表';

-- 内置工具种子(按工具集粒度,built_in=1 不可删/改code)
insert into ai_tool (name,code,tool_type,description,args,status,built_in,create_by,create_time,update_by,update_time) values
('数据探索','data_explore','builtin','发现数据源、查表结构、检索数据源知识库(含收藏的取数解法)','{}','0','1','admin',sysdate(),'admin',sysdate()),
('沙箱执行','sandbox_code','builtin','在隔离沙箱里跑 Python 计算 / 对数据源取数,产出结论/表格/图表','{}','0','1','admin',sysdate(),'admin',sysdate()),
('任务提议','task_propose','builtin','向用户弹出预填的任务确认表单(数据集成/Python/Shell)','{}','0','1','admin',sysdate(),'admin',sysdate());


-- ----------------------------
-- AI应用表(打包的助手配置)
-- ----------------------------
drop table if exists ai_app;
create table ai_app (
  app_id            bigint(20)      not null auto_increment    comment '应用主键',
  name              varchar(100)    not null                   comment '应用名称',
  icon              varchar(500)    default null               comment '应用图标',
  description       varchar(500)    default null               comment '应用描述',
  app_type          varchar(50)     default null               comment '应用类型/分类',
  status            char(1)         default '0'                comment '状态: 0发布 1草稿',
  config            text                                       comment '应用配置JSON(prompt/绑定工具知识库/参数等)',
  user_id           bigint(20)                                 comment '用户ID',
  dept_id           bigint(20)                                 comment '部门ID',
  create_by         varchar(64)     default ''                 comment '创建者',
  create_time       datetime                                   comment '创建时间',
  update_by         varchar(64)     default ''                 comment '更新者',
  update_time       datetime                                   comment '更新时间',
  remark            varchar(500)    default null               comment '备注',
  tenant_id         bigint(20)                                 comment '租户ID(顶级部门)',
  primary key (app_id),
  key ix_ai_app_tenant_id (tenant_id)
) engine=innodb auto_increment=1 comment = 'AI应用表';

-- (应用对外 APIKey 复用通用 api_token 表:token_type='ai_app', ref_id=应用ID)


-- ----------------------------
-- 21、AI对话配置表
-- ----------------------------
drop table if exists ai_chat_config;
create table ai_chat_config (
  chat_config_id          bigint(20)      not null auto_increment    comment '配置主键',
  user_id                 bigint(20)      not null unique            comment '用户ID',
  temperature             float           default null               comment '默认温度',
  add_history_to_context  char(1)         default '0'                comment '是否添加历史记录(0是, 1否)',
  num_history_runs        int(4)          default null               comment '历史记录条数',
  system_prompt           text            default null               comment '系统提示词',
  metrics_default_visible char(1)         default '0'                comment '默认显示指标(0是, 1否)',
  vision_enabled          char(1)         default '1'                comment '是否开启视觉(0是, 1否)',
  image_max_size_mb       int(4)          default null               comment '图片最大大小(MB)',
  mcp_tool_ids            varchar(500)    default null               comment '启用的MCP工具ID(逗号分隔)',
  agent_app_ids           varchar(500)    default null               comment '引用的应用agent ID(逗号分隔,多agent协作)',
  enable_memory           char(1)         default '1'                comment '是否开启长期记忆(0是, 1否)',
  create_time             datetime                                   comment '创建时间',
  update_time             datetime                                   comment '更新时间',
  primary key (chat_config_id)
) engine=innodb auto_increment=1 comment = 'AI对话配置表';

-- AI 长期记忆表(agno user-memory;按 user_id 跨会话沉淀,schema 须与 agno 一致)
drop table if exists ai_memories;
create table ai_memories (
  memory_id   varchar(128)    not null                   comment '记忆ID',
  memory      json            not null                   comment '记忆内容',
  input       text                                       comment '来源对话片段',
  agent_id    varchar(128)                               comment 'agent ID',
  team_id     varchar(128)                               comment 'team ID',
  user_id     varchar(128)                               comment '用户ID',
  topics      json                                       comment '主题标签',
  feedback    text                                       comment '反馈',
  created_at  bigint          not null                   comment '创建时间(epoch)',
  updated_at  bigint                                     comment '更新时间(epoch)',
  primary key (memory_id),
  key ix_ai_memories_user_id (user_id),
  key ix_ai_memories_created_at (created_at),
  key ix_ai_memories_updated_at (updated_at)
) engine=innodb comment = 'AI长期记忆表(agno)';

-- ----------------------------
-- 任务调度模块（module_task_schedule）
-- ----------------------------

-- 任务模板表
drop table if exists task_template;
create table task_template (
  id                  varchar(36)     not null                   comment '主键',
  name                varchar(200)    default ''                 comment '模板名称',
  code                varchar(200)    default ''                 comment '模板编码',
  icon                varchar(500)    default ''                 comment '模板图标',
  type                smallint        default 1                  comment '表单类型,1内置组件2动态配置',
  runner_type         smallint        default 1                  comment '执行器类型，1内置执行器2动态代码',
  runner_code         text                                       comment '动态执行器代码',
  component           varchar(500)    default ''                 comment '前端组件',
  params              text                                       comment '模板参数schema',
  built_in            smallint        default 0                  comment '是否内置 1是 0不是',
  status              smallint        default 1                  comment '状态 1启用 0禁用',
  create_by           varchar(64)     default ''                 comment '创建者',
  create_time         datetime                                   comment '创建时间',
  update_by           varchar(64)     default ''                 comment '更新者',
  update_time         datetime                                   comment '更新时间',
  remark              varchar(500)    default ''                 comment '备注',
  primary key (id),
  unique key uk_task_template_code (code)
) engine=innodb comment = '任务模板表';

-- 任务表
drop table if exists task;
create table task (
  id                  varchar(36)     not null                   comment '主键',
  template_code       varchar(200)    default ''                 comment '任务模板编码',
  task_type           smallint        default 1                  comment '任务类型，1普通任务2dag工作流任务',
  run_type            smallint        default 1                  comment 'DAG运行模式 1分布式2单机',
  name                varchar(100)    default ''                 comment '名称',
  params              text                                       comment '参数',
  status              smallint        default 0                  comment '状态 0停用 1启用',
  built_in            smallint        default 0                  comment '是否内置 1是 0不是',
  trigger_type        smallint        default 1                  comment '触发方式，1单次2定时',
  crontab             varchar(500)    default ''                 comment '定时设置',
  priority            int             default 1                  comment '优先级',
  retry               int             default 0                  comment '失败重试次数',
  countdown           int             default 0                  comment '失败重试间隔(秒)',
  run_queue           varchar(200)    default 'default'          comment '运行队列',
  running_id          varchar(36)     default null               comment '正在运行任务实例ID',
  job_id              int             default null               comment '关联的调度任务ID(sys_job)',
  published_version_id varchar(36)    default null               comment 'DAG当前发布版(dag_graph.id)',
  create_by           varchar(64)     default ''                 comment '创建者',
  create_time         datetime                                   comment '创建时间',
  update_by           varchar(64)     default ''                 comment '更新者',
  update_time         datetime                                   comment '更新时间',
  remark              varchar(500)    default ''                 comment '备注',
  primary key (id)
) engine=innodb comment = '任务表';

-- 任务实例(执行记录)表
drop table if exists task_instance;
create table task_instance (
  id                  varchar(36)     not null                   comment '主键(celery task uuid)',
  parent_id           varchar(36)     default ''                 comment '父任务id',
  task_id             varchar(36)     default ''                 comment '任务id',
  node_id             varchar(36)     default ''                 comment 'dag节点id',
  name                varchar(100)    default ''                 comment '任务名称',
  status              varchar(50)     default 'STARTED'          comment '状态',
  worker              varchar(200)    default ''                 comment 'worker',
  retry_num           int             default 0                  comment '重试次数',
  progress            float           default 0                  comment '任务进度',
  start_time          datetime                                   comment '开始时间',
  end_time            datetime                                   comment '结束时间',
  closed              smallint        default 0                  comment '是否已关闭',
  result              text                                       comment '执行结果',
  dag_version_id      varchar(36)     default null               comment 'DAG run 图版本(dag_graph.id)',
  primary key (id),
  key idx_task_instance_task (task_id),
  key idx_task_instance_status (status)
) engine=innodb comment = '任务实例表';

-- DAG 图版本文档表(Dify/n8n 范式:draft 可变 + published 不可变)
drop table if exists dag_graph;
create table dag_graph (
  id                  varchar(36)     not null                   comment '主键',
  dag_task_id         varchar(36)     default null               comment '所属 DAG 任务id',
  version             varchar(64)     default 'draft'            comment "版本:'draft' 或 发布版本号",
  status              varchar(20)     default 'draft'            comment 'draft/published/archived',
  graph               mediumtext                                 comment '整张图 JSON(nodes/edges/viewport)',
  remark              varchar(500)    default ''                 comment '发布说明',
  create_by           varchar(64)     default ''                 comment '创建者',
  create_time         datetime                                   comment '创建时间',
  tenant_id           bigint          default null               comment '租户ID',
  primary key (id),
  key ix_dag_graph_dag_task_id (dag_task_id)
) engine=innodb comment = 'DAG图版本文档表';

-- 任务执行明细日志表(仅 TASK_LOG_TYPE=db 时写入)
drop table if exists task_log;
create table task_log (
  id                  bigint(20)      not null auto_increment    comment '日志ID',
  task_uuid           varchar(36)     default ''                 comment '任务实例ID',
  level               varchar(20)     default 'INFO'             comment '日志级别',
  content             text                                       comment '日志内容',
  create_time         datetime                                   comment '创建时间',
  primary key (id),
  key idx_task_log_uuid (task_uuid)
) engine=innodb comment = '任务执行明细日志表';

-- 内置任务模板
insert into task_template values ('1', 'Python脚本任务', 'PythonTask', '', 1, 1, null, 'PythonTask', '', 1, 1, 'admin', sysdate(), '', null, '内置组件: Python 任务(代码/文件模式)');
insert into task_template values ('2', 'Shell脚本任务', 'ShellTask', '', 1, 1, null, 'ShellTask', '', 1, 1, 'admin', sysdate(), '', null, '内置组件: Shell 任务(代码/文件模式)');
insert into task_template values ('3', '动态代码任务', 'DynamicTask', '', 2, 2, 'def run(params, logger):
    logger.info("动态任务参数: " + str(params))
    return "执行成功"', '', '[{"field":"message","label":"消息内容","component":"text","required":false,"default":"hello dynamic"}]', 1, 1, 'admin', sysdate(), '', null, '动态代码模板：run(params, logger) 在模板上维护，任务只填参数');
insert into task_template values ('4', '数据集成任务', 'DataIntegrationTask', '', 1, 1, null, 'DataIntegrationTask', '', 1, 1, 'admin', sysdate(), '', null, '内置组件: 数据集成 ETL(抽取-转换-装载),支持抽取预览调试');

-- ----------------------------
-- 任务调度模块菜单/权限
-- ----------------------------
insert into sys_menu values('2100', '任务调度', '0',    '2', 'task',     null,                  '', '', 1, 0, 'M', '0', '0', '',                       'job',  'admin', sysdate(), '', null, '任务调度目录');
insert into sys_menu values('2101', '普通任务调度', '2100', '1', 'info',     'task/info/index',     '', '', 1, 0, 'C', '0', '0', 'task:info:list',         'list', 'admin', sysdate(), '', null, '任务管理菜单');
insert into sys_menu values('2102', '任务模板', '2100', '3', 'template', 'task/template/index', '', '', 1, 0, 'C', '0', '0', 'task:template:list',     'form', 'admin', sysdate(), '', null, '任务模板菜单');
insert into sys_menu values('2103', '任务工作流', '2100', '2', 'dag',     'task/dag/index',      '', '', 1, 0, 'C', '0', '0', 'task:dag:list',          'share', 'admin', sysdate(), '', null, 'DAG工作流菜单');
-- DAG 工作流 按钮
insert into sys_menu values('2140', 'DAG查询', '2103', '1', '#', '', '', '', 1, 0, 'F', '0', '0', 'task:dag:list',    '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2141', 'DAG编辑', '2103', '2', '#', '', '', '', 1, 0, 'F', '0', '0', 'task:dag:edit',    '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2142', 'DAG发布', '2103', '3', '#', '', '', '', 1, 0, 'F', '0', '0', 'task:dag:publish', '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2143', 'DAG运行', '2103', '4', '#', '', '', '', 1, 0, 'F', '0', '0', 'task:dag:run',     '#', 'admin', sysdate(), '', null, '');
-- 任务管理 按钮
insert into sys_menu values('2110', '任务查询', '2101', '1', '#', '', '', '', 1, 0, 'F', '0', '0', 'task:info:query',        '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2111', '任务新增', '2101', '2', '#', '', '', '', 1, 0, 'F', '0', '0', 'task:info:add',          '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2112', '任务修改', '2101', '3', '#', '', '', '', 1, 0, 'F', '0', '0', 'task:info:edit',         '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2113', '任务删除', '2101', '4', '#', '', '', '', 1, 0, 'F', '0', '0', 'task:info:remove',       '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2114', '状态修改', '2101', '5', '#', '', '', '', 1, 0, 'F', '0', '0', 'task:info:changeStatus', '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2115', '手动执行', '2101', '6', '#', '', '', '', 1, 0, 'F', '0', '0', 'task:info:run',          '#', 'admin', sysdate(), '', null, '');
-- 任务模板 按钮
insert into sys_menu values('2120', '模板查询', '2102', '1', '#', '', '', '', 1, 0, 'F', '0', '0', 'task:template:query',  '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2121', '模板新增', '2102', '2', '#', '', '', '', 1, 0, 'F', '0', '0', 'task:template:add',    '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2122', '模板修改', '2102', '3', '#', '', '', '', 1, 0, 'F', '0', '0', 'task:template:edit',   '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2123', '模板删除', '2102', '4', '#', '', '', '', 1, 0, 'F', '0', '0', 'task:template:remove', '#', 'admin', sysdate(), '', null, '');
-- 执行记录 按钮
insert into sys_menu values('2130', '记录查询', '2101', '1', '#', '', '', '', 1, 0, 'F', '0', '0', 'task:instance:query',  '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2131', '记录删除', '2101', '2', '#', '', '', '', 1, 0, 'F', '0', '0', 'task:instance:remove', '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2132', '终止任务', '2101', '3', '#', '', '', '', 1, 0, 'F', '0', '0', 'task:instance:stop',   '#', 'admin', sysdate(), '', null, '');
-- Worker 管理
insert into sys_menu values('2104', 'Worker管理', '2100', '4', 'worker', 'task/worker/index', '', '', 1, 0, 'C', '0', '0', 'task:worker:list', 'server', 'admin', sysdate(), '', null, 'Worker 管理菜单');
insert into sys_menu values('2150', 'Worker查询', '2104', '1', '#', '', '', '', 1, 0, 'F', '0', '0', 'task:worker:list',     '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2151', '队列管理',   '2104', '2', '#', '', '', '', 1, 0, 'F', '0', '0', 'task:worker:consumer', '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2152', '并发伸缩',   '2104', '3', '#', '', '', '', 1, 0, 'F', '0', '0', 'task:worker:scale',    '#', 'admin', sysdate(), '', null, '');

-- ----------------------------
-- 告警中心模块（module_alert）
-- ----------------------------

-- 告警策略表
drop table if exists alert_strategy;
create table alert_strategy (
  strategy_id         bigint(20)      not null auto_increment    comment '策略主键',
  strategy_name       varchar(200)    not null                   comment '策略名称',
  biz                 varchar(50)     default 'scheduler'        comment '业务类型(scheduler等)',
  trigger_conf        text                                       comment '触发条件(JSON,含告警等级level等)',
  forward_conf        text                                       comment '转发渠道配置(JSON数组)',
  status              smallint        default 1                  comment '状态(1启用 0停用)',
  create_by           varchar(64)     default ''                 comment '创建者',
  create_time         datetime                                   comment '创建时间',
  update_by           varchar(64)     default ''                 comment '更新者',
  update_time         datetime                                   comment '更新时间',
  remark              varchar(500)    default ''                 comment '备注信息',
  primary key (strategy_id)
) engine=innodb auto_increment=100 comment = '告警策略表';

-- 告警记录表
drop table if exists alert_record;
create table alert_record (
  alert_id            bigint(20)      not null auto_increment    comment '告警主键',
  strategy_id         bigint(20)                                 comment '告警策略id',
  title               varchar(500)                               comment '告警标题',
  content             text                                       comment '告警内容',
  level               int             default 0                  comment '告警等级',
  status              smallint        default 0                  comment '告警状态(0未处理 1已处理)',
  biz                 varchar(50)                                comment '告警业务(scheduler等)',
  source              varchar(200)                               comment '告警对象(任务名/实例等)',
  metric              varchar(100)                               comment '告警指标(task_fail/task_timeout等)',
  tags                text                                       comment '告警标签(JSON)',
  ext_params          text                                       comment '额外参数(JSON)',
  recover_time        datetime                                   comment '恢复时间',
  create_time         datetime                                   comment '创建时间',
  primary key (alert_id),
  key idx_alert_record_strategy (strategy_id),
  key idx_alert_record_status (status)
) engine=innodb comment = '告警记录表';

-- 内置示例告警策略(webhook 到本地占位地址；level=2 错误)
insert into alert_strategy (strategy_id, strategy_name, biz, trigger_conf, forward_conf, status, create_by, create_time, remark)
values (1, '默认任务失败告警', 'scheduler', '{"level":2}', '[{"type":"webhook","webhook_url":"http://ezdata-backend-dev:9099/dev-api/alert/test-sink"}]', 1, 'admin', sysdate(), '任务重试耗尽失败时通过 webhook 通知');

-- 任务表增加告警策略绑定字段
alter table task add column alert_strategy_ids varchar(500) default '' comment '绑定的告警策略ID(逗号分隔)';

-- ----------------------------
-- 告警中心菜单/权限
-- ----------------------------
insert into sys_menu values('2200', '告警中心', '0',    '3', 'alert',          null,                  '', '', 1, 0, 'M', '0', '0', '',                     'message', 'admin', sysdate(), '', null, '告警中心目录');
insert into sys_menu values('2201', '告警策略', '2200', '1', 'strategy',       'alert/strategy/index', '', '', 1, 0, 'C', '0', '0', 'alert:strategy:list',  'tool',    'admin', sysdate(), '', null, '告警策略菜单');
insert into sys_menu values('2202', '告警记录', '2200', '2', 'record',         'alert/record/index',   '', '', 1, 0, 'C', '0', '0', 'alert:record:list',    'log',     'admin', sysdate(), '', null, '告警记录菜单');
-- 告警策略 按钮
insert into sys_menu values('2210', '策略查询', '2201', '1', '#', '', '', '', 1, 0, 'F', '0', '0', 'alert:strategy:query',  '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2211', '策略新增', '2201', '2', '#', '', '', '', 1, 0, 'F', '0', '0', 'alert:strategy:add',    '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2212', '策略修改', '2201', '3', '#', '', '', '', 1, 0, 'F', '0', '0', 'alert:strategy:edit',   '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2213', '策略删除', '2201', '4', '#', '', '', '', 1, 0, 'F', '0', '0', 'alert:strategy:remove', '#', 'admin', sysdate(), '', null, '');
-- 告警记录 按钮
insert into sys_menu values('2220', '记录查询', '2202', '1', '#', '', '', '', 1, 0, 'F', '0', '0', 'alert:record:list',    '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2221', '记录处理', '2202', '2', '#', '', '', '', 1, 0, 'F', '0', '0', 'alert:record:edit',    '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2222', '记录删除', '2202', '3', '#', '', '', '', 1, 0, 'F', '0', '0', 'alert:record:remove',  '#', 'admin', sysdate(), '', null, '');

-- ----------------------------
-- 数据管理模块菜单/权限(module_data + module_apitoken)
-- ----------------------------
insert into sys_menu values('2300', '数据管理', '0',    '0', 'data',   null,               '', '', 1, 0, 'M', '0', '0', '',                  'database', 'admin', sysdate(), '', null, '数据管理目录(置顶)');
insert into sys_menu values('2301', '数据管理', '2300', '1', 'manage', 'dataManage/index', '', '', 1, 0, 'C', '0', '0', 'data:source:list',  'database', 'admin', sysdate(), '', null, '数据管理菜单');
insert into sys_menu values('2310', '数据源查询', '2301', '1',  '#', '', '', '', 1, 0, 'F', '0', '0', 'data:source:list',   '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2311', '数据源新增', '2301', '2',  '#', '', '', '', 1, 0, 'F', '0', '0', 'data:source:add',    '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2312', '数据源修改', '2301', '3',  '#', '', '', '', 1, 0, 'F', '0', '0', 'data:source:edit',   '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2313', '数据源删除', '2301', '4',  '#', '', '', '', 1, 0, 'F', '0', '0', 'data:source:remove', '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2314', '模型查询',   '2301', '5',  '#', '', '', '', 1, 0, 'F', '0', '0', 'data:model:list',    '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2315', '模型新增',   '2301', '6',  '#', '', '', '', 1, 0, 'F', '0', '0', 'data:model:add',     '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2316', '模型修改',   '2301', '7',  '#', '', '', '', 1, 0, 'F', '0', '0', 'data:model:edit',    '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2317', '模型删除',   '2301', '8',  '#', '', '', '', 1, 0, 'F', '0', '0', 'data:model:remove',  '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2318', '数据查询',   '2301', '9',  '#', '', '', '', 1, 0, 'F', '0', '0', 'data:query',         '#', 'admin', sysdate(), '', null, '原生/AI 取数');
insert into sys_menu values('2319', '数据接口',   '2301', '10', '#', '', '', '', 1, 0, 'F', '0', '0', 'data:api',           '#', 'admin', sysdate(), '', null, '分页接口预览');
insert into sys_menu values('2320', '数据集成',   '2301', '11', '#', '', '', '', 1, 0, 'F', '0', '0', 'data:etl',           '#', 'admin', sysdate(), '', null, 'ETL 预览/测试/AI生成');
insert into sys_menu values('2321', '令牌查询',   '2301', '12', '#', '', '', '', 1, 0, 'F', '0', '0', 'apitoken:list',      '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2322', '令牌生成',   '2301', '13', '#', '', '', '', 1, 0, 'F', '0', '0', 'apitoken:add',       '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2323', '令牌删除',   '2301', '14', '#', '', '', '', 1, 0, 'F', '0', '0', 'apitoken:remove',    '#', 'admin', sysdate(), '', null, '');

-- 数据管理员角色(role_id=3)分配数据管理全部菜单/权限
insert into sys_role_menu values('3', '2300');
insert into sys_role_menu values('3', '2301');
insert into sys_role_menu values('3', '2310');
insert into sys_role_menu values('3', '2311');
insert into sys_role_menu values('3', '2312');
insert into sys_role_menu values('3', '2313');
insert into sys_role_menu values('3', '2314');
insert into sys_role_menu values('3', '2315');
insert into sys_role_menu values('3', '2316');
insert into sys_role_menu values('3', '2317');
insert into sys_role_menu values('3', '2318');
insert into sys_role_menu values('3', '2319');
insert into sys_role_menu values('3', '2320');
insert into sys_role_menu values('3', '2321');
insert into sys_role_menu values('3', '2322');
insert into sys_role_menu values('3', '2323');

-- ----------------------------
-- 知识库模块菜单/权限(module_rag),一级菜单
-- ----------------------------
insert into sys_menu values('2400', '知识库',   '0',    '1', 'rag',       null,                 '', '', 1, 0, 'M', '0', '0', '',               'documentation', 'admin', sysdate(), '', null, '知识库目录');
insert into sys_menu values('2401', '知识库管理', '2400', '1', 'dataset',   'rag/dataset/index',  '', '', 1, 0, 'C', '0', '0', 'rag:dataset:list', 'documentation', 'admin', sysdate(), '', null, '知识库/文档/分段管理');
insert into sys_menu values('2402', '召回测试',   '2400', '2', 'retrieval', 'rag/retrieval/index','', '', 1, 0, 'C', '0', '0', 'rag:retrieval',    'search', 'admin', sysdate(), '', null, '知识库召回测试');
insert into sys_menu values('2410', '知识库查询', '2401', '1', '#', '', '', '', 1, 0, 'F', '0', '0', 'rag:dataset:list', '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2411', '知识库编辑', '2401', '2', '#', '', '', '', 1, 0, 'F', '0', '0', 'rag:dataset:edit', '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2412', '召回执行',   '2402', '1', '#', '', '', '', 1, 0, 'F', '0', '0', 'rag:retrieval',    '#', 'admin', sysdate(), '', null, '');

-- 数据管理员角色(role_id=3)分配知识库菜单/权限
insert into sys_role_menu values('3', '2400');
insert into sys_role_menu values('3', '2401');
insert into sys_role_menu values('3', '2402');
insert into sys_role_menu values('3', '2410');
insert into sys_role_menu values('3', '2411');
insert into sys_role_menu values('3', '2412');

-- ============================================================================
-- 知识库模块(module_rag):知识库 / 文档 / 分段 / embedding 缓存
-- ============================================================================
drop table if exists rag_dataset;
create table rag_dataset (
  id                 varchar(36)  not null comment '知识库ID',
  name               varchar(200) not null comment '名称',
  description        varchar(500) default null comment '描述',
  source_id          varchar(36)  default null comment '专属数据源ID(空=普通知识库)',
  embedding_provider varchar(50)  default null comment 'embedding 提供商',
  embedding_model    varchar(100) default null comment 'embedding 模型编码',
  embedding_dims     int          default null comment '向量维度',
  vector_backend     varchar(50)  default 'elasticsearch' comment '向量后端',
  vector_source_id   varchar(36)  default null comment '向量库 data_source(空=系统默认ES)',
  index_name         varchar(200) default null comment '向量索引/集合名',
  retrieval_config   text         default null comment '默认检索参数(JSON)',
  built_in           tinyint      default 0 comment '是否内置',
  status             tinyint      default 1 comment '状态 1启用0禁用',
  tenant_id          bigint       default null comment '租户ID',
  create_by          varchar(64)  default '' comment '创建者',
  create_time        datetime     default null comment '创建时间',
  update_by          varchar(64)  default '' comment '更新者',
  update_time        datetime     default null comment '更新时间',
  remark             varchar(500) default null comment '备注',
  primary key (id),
  key idx_rag_dataset_tenant (tenant_id)
) engine=innodb default charset=utf8mb4 comment='RAG 知识库';

drop table if exists rag_document;
create table rag_document (
  id             varchar(36)   not null comment '文档ID',
  dataset_id     varchar(36)   not null comment '所属知识库',
  name           varchar(300)  not null comment '文档名',
  document_type  varchar(30)   default 'upload_file' comment '来源类型',
  file_key       varchar(500)  default null comment '文件存储key',
  source         varchar(1000) default null comment '来源(URL/datamodel_id等)',
  meta_data      text          default null comment '元数据(JSON)',
  chunk_strategy text          default null comment '切分/清洗策略(JSON)',
  content_hash   varchar(64)   default null comment '原文hash(增量,未变跳过重训)',
  status         tinyint       default 1 comment '状态 1待训练2训练中3成功4失败',
  chunk_count    int           default 0 comment '分段数',
  error          varchar(1000) default null comment '失败原因',
  tenant_id      bigint        default null comment '租户ID',
  create_by      varchar(64)   default '' comment '创建者',
  create_time    datetime      default null comment '创建时间',
  update_by      varchar(64)   default '' comment '更新者',
  update_time    datetime      default null comment '更新时间',
  primary key (id),
  key idx_rag_document_dataset (dataset_id),
  key idx_rag_document_tenant (tenant_id)
) engine=innodb default charset=utf8mb4 comment='RAG 文档';

drop table if exists rag_chunk;
create table rag_chunk (
  id            varchar(36) not null comment '分段ID(=向量库_id)',
  dataset_id    varchar(36) not null comment '所属知识库',
  document_id   varchar(36) not null comment '所属文档',
  chunk_type    varchar(10) default 'chunk' comment '类型 chunk/qa',
  content       text        default null comment '正文',
  question      text        default null comment '问题(QA)',
  question_hash varchar(64) default null comment '问题hash',
  answer        text        default null comment '答案(QA)',
  hash          varchar(64) default null comment '正文hash',
  position      int         default 0 comment '序号',
  status        tinyint     default 1 comment '状态 1已索引0未索引',
  star_flag     tinyint     default 0 comment '标星',
  tenant_id     bigint      default null comment '租户ID',
  create_by     varchar(64) default '' comment '创建者',
  create_time   datetime    default null comment '创建时间',
  primary key (id),
  key idx_rag_chunk_dataset (dataset_id),
  key idx_rag_chunk_document (document_id),
  key idx_rag_chunk_qhash (question_hash),
  key idx_rag_chunk_tenant (tenant_id)
) engine=innodb default charset=utf8mb4 comment='RAG 分段';

drop table if exists rag_embedding;
create table rag_embedding (
  id          bigint      not null auto_increment comment '主键',
  hash        varchar(64) not null comment '文本hash(md5)',
  model_id    varchar(150) not null comment 'provider:model',
  dim         int         default null comment '维度',
  vector      mediumtext  default null comment '向量(JSON数组)',
  create_time datetime    default null comment '创建时间',
  primary key (id),
  unique key uk_rag_embedding (hash, model_id)
) engine=innodb default charset=utf8mb4 comment='RAG embedding 缓存';

-- ============================================================================
-- 数据管理模块(module_data)：数据源 / 数据模型
-- ============================================================================
drop table if exists data_source;
create table data_source (
  id           varchar(36)  not null comment '主键',
  name         varchar(200) default '' comment '名称',
  code         varchar(200) default '' comment '编码(稳定引用)',
  source_type  varchar(50)  default null comment '源类型,如 mysql/elasticsearch',
  family       varchar(50)  default null comment '源族,如 rdbms/search/vector',
  config       json         default null comment '非密钥连接参数(JSON)',
  secrets      text         default null comment '密钥(AES 加密)',
  status       varchar(20)  default 'untested' comment '状态 untested/ok/failed',
  last_test_at datetime     default null comment '最后测试时间',
  remark       varchar(500) default '' comment '备注',
  create_by    varchar(64)  default '' comment '创建者',
  create_time  datetime     default null comment '创建时间',
  update_by    varchar(64)  default '' comment '更新者',
  update_time  datetime     default null comment '更新时间',
  tenant_id    bigint       default null comment '租户ID(顶级部门)',
  primary key (id),
  key ix_data_source_tenant_id (tenant_id),
  key ix_data_source_code (code)
) engine=innodb default charset=utf8mb4 comment='数据源表';

drop table if exists data_model;
create table data_model (
  id              varchar(36)  not null comment '主键',
  name            varchar(200) default '' comment '名称',
  code            varchar(200) default '' comment '编码',
  datasource_code varchar(200) default null comment '引用的数据源编码',
  kind            varchar(50)  default 'table' comment 'table/collection/index/topic/custom_query',
  object_name     varchar(200) default null comment '表/索引/集合名',
  db_schema       varchar(200) default '' comment 'schema/库名',
  fields          json         default null comment '字段结构(introspect 缓存)',
  default_filters json         default null comment '默认过滤条件',
  auth            varchar(200) default 'query,extract' comment '授权位 query/extract/api/write(逗号)',
  status          smallint     default 1 comment '状态 1启用 0停用',
  remark          varchar(500) default '' comment '备注',
  create_by       varchar(64)  default '' comment '创建者',
  create_time     datetime     default null comment '创建时间',
  update_by       varchar(64)  default '' comment '更新者',
  update_time     datetime     default null comment '更新时间',
  tenant_id       bigint       default null comment '租户ID(顶级部门)',
  primary key (id),
  key ix_data_model_tenant_id (tenant_id),
  key ix_data_model_code (code)
) engine=innodb default charset=utf8mb4 comment='数据模型表';

-- ----------------------------
-- 通用 API Token 模块(module_apitoken)：apikey 校验,data_api/agent 等用途复用
-- ----------------------------
drop table if exists api_token;
create table api_token (
  id          varchar(36)  not null comment '主键',
  name        varchar(200) default '' comment '名称',
  token       varchar(80)  default null comment 'apikey',
  token_type  varchar(50)  default 'data_api' comment '用途 data_api/agent/...',
  ref_id      varchar(200) default null comment '绑定的资源(如数据模型 code);空=该 type 全部',
  status      smallint     default 1 comment '1启用 0停用',
  expire_time datetime     default null comment '过期时间(空=永不)',
  remark      varchar(500) default '' comment '备注',
  create_by   varchar(64)  default '' comment '创建者',
  create_time datetime     default null comment '创建时间',
  update_by   varchar(64)  default '' comment '更新者',
  update_time datetime     default null comment '更新时间',
  tenant_id   bigint       default null comment '租户ID(顶级部门)',
  primary key (id),
  key ix_api_token_token (token),
  key ix_api_token_tenant_id (tenant_id)
) engine=innodb default charset=utf8mb4 comment='通用 API Token 表(data_api/agent 复用)';

-- ============================================================================
-- 多租户(行级)：业务/组织表增加 tenant_id 列(值=顶级部门ID)，并回填已有种子到默认租户(集团总公司=100)
-- 租户=顶级部门(sys_dept parent_id=0)。平台超管(admin)绕过过滤可见全部。
-- 全局共享(不加 tenant_id)：sys_menu/sys_dict_*/sys_config/sys_role/sys_post/task_template/sys_job_log。
-- ============================================================================
alter table task           add column tenant_id bigint null comment '租户ID(顶级部门)', add index idx_task_tenant (tenant_id);
alter table task_instance  add column tenant_id bigint null comment '租户ID(顶级部门)', add index idx_task_instance_tenant (tenant_id);
alter table task_log       add column tenant_id bigint null comment '租户ID(顶级部门)', add index idx_task_log_tenant (tenant_id);
alter table alert_strategy add column tenant_id bigint null comment '租户ID(顶级部门)', add index idx_alert_strategy_tenant (tenant_id);
alter table alert_record   add column tenant_id bigint null comment '租户ID(顶级部门)', add index idx_alert_record_tenant (tenant_id);
alter table ai_models      add column tenant_id bigint null comment '租户ID(顶级部门)', add index idx_ai_models_tenant (tenant_id);
alter table ai_chat_config add column tenant_id bigint null comment '租户ID(顶级部门)', add index idx_ai_chat_config_tenant (tenant_id);
alter table sys_user       add column tenant_id bigint null comment '租户ID(顶级部门)', add index idx_sys_user_tenant (tenant_id);
alter table sys_dept       add column tenant_id bigint null comment '租户ID(顶级部门)', add index idx_sys_dept_tenant (tenant_id);
alter table sys_notice     add column tenant_id bigint null comment '租户ID(顶级部门)', add index idx_sys_notice_tenant (tenant_id);
alter table sys_job        add column tenant_id bigint null comment '租户ID(顶级部门)', add index idx_sys_job_tenant (tenant_id);
-- 回填默认租户(现有种子数据均归集团总公司=100)
update task set tenant_id=100;           update task_instance set tenant_id=100;  update task_log set tenant_id=100;
update alert_strategy set tenant_id=100; update alert_record set tenant_id=100;
update ai_models set tenant_id=100;      update ai_chat_config set tenant_id=100;
update sys_user set tenant_id=100;       update sys_dept set tenant_id=100;       update sys_notice set tenant_id=100;  update sys_job set tenant_id=100;

-- ----------------------------
-- 演示数据已抽离:默认空项目。需要财经 demo(数据源/任务/模型/AI应用 + 填充 ES)时,服务启动后手动跑:
--   docker exec -i ezdata-backend-my python - < api/demo_seed.py
-- ----------------------------

