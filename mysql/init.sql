-- 污水处理厂智能管理系统数据库初始化脚本
-- Water Treatment Plant Intelligent Management System Database Init Script

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- 角色表
-- ----------------------------
DROP TABLE IF EXISTS `roles`;
CREATE TABLE `roles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL COMMENT '角色名称',
  `code` varchar(50) NOT NULL COMMENT '角色编码',
  `description` varchar(200) DEFAULT NULL COMMENT '描述',
  `permissions` text COMMENT '权限列表JSON',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色表';

-- 初始化角色数据
INSERT INTO `roles` (`name`, `code`, `description`, `permissions`) VALUES
('系统管理员', 'admin', '拥有系统全部权限', '["*"]'),
('运行主管', 'supervisor', '负责生产运行管理', '["production:*","equipment:*","report:*"]'),
('操作员', 'operator', '负责日常操作', '["production:view","production:log","equipment:view"]'),
('化验员', 'lab_operator', '负责化验检测', '["laboratory:*"]'),
('安全员', 'safety_officer', '负责安全管理', '["safety:*"]');

-- ----------------------------
-- 用户表
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL COMMENT '用户名',
  `password_hash` varchar(128) NOT NULL COMMENT '密码哈希',
  `real_name` varchar(50) DEFAULT NULL COMMENT '真实姓名',
  `email` varchar(100) DEFAULT NULL COMMENT '邮箱',
  `phone` varchar(20) DEFAULT NULL COMMENT '手机号',
  `department` varchar(50) DEFAULT NULL COMMENT '部门',
  `position` varchar(50) DEFAULT NULL COMMENT '职位',
  `role_id` int DEFAULT NULL COMMENT '角色ID',
  `is_active` tinyint(1) DEFAULT '1' COMMENT '是否启用',
  `last_login` datetime DEFAULT NULL COMMENT '最后登录时间',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`),
  KEY `idx_role_id` (`role_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 初始化用户数据 (密码都是 123456)
INSERT INTO `users` (`username`, `password_hash`, `real_name`, `email`, `phone`, `department`, `position`, `role_id`, `is_active`) VALUES
('admin', '$2b$12$5HJdvS5gkw/ZdXlVBjmIk.CgIanVB.YhXR12o.ZC0h8/jmsjq6ss6', '系统管理员', 'admin@example.com', '13800138000', '信息部', '系统管理员', 1, 1),
('user', '$2b$12$5HJdvS5gkw/ZdXlVBjmIk.CgIanVB.YhXR12o.ZC0h8/jmsjq6ss6', '张三', 'zhangsan@example.com', '13800138001', '运行部', '运行主管', 2, 1),
('operator1', '$2b$12$5HJdvS5gkw/ZdXlVBjmIk.CgIanVB.YhXR12o.ZC0h8/jmsjq6ss6', '李四', 'lisi@example.com', '13800138002', '运行部', '操作员', 3, 1),
('lab1', '$2b$12$5HJdvS5gkw/ZdXlVBjmIk.CgIanVB.YhXR12o.ZC0h8/jmsjq6ss6', '王五', 'wangwu@example.com', '13800138003', '化验室', '化验员', 4, 1),
('safety1', '$2b$12$5HJdvS5gkw/ZdXlVBjmIk.CgIanVB.YhXR12o.ZC0h8/jmsjq6ss6', '赵六', 'zhaoliu@example.com', '13800138004', '安全环保部', '安全员', 5, 1);

-- ----------------------------
-- 工艺参数表
-- ----------------------------
DROP TABLE IF EXISTS `process_parameters`;
CREATE TABLE `process_parameters` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL COMMENT '参数名称',
  `code` varchar(50) NOT NULL COMMENT '参数编码',
  `unit` varchar(20) DEFAULT NULL COMMENT '单位',
  `current_value` float DEFAULT NULL COMMENT '当前值',
  `min_value` float DEFAULT NULL COMMENT '最小值',
  `max_value` float DEFAULT NULL COMMENT '最大值',
  `standard_value` float DEFAULT NULL COMMENT '标准值',
  `process_section` varchar(50) DEFAULT NULL COMMENT '工艺段',
  `equipment_id` int DEFAULT NULL COMMENT '关联设备ID',
  `status` varchar(20) DEFAULT 'normal' COMMENT '状态',
  `recorded_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工艺参数表';

-- 初始化工艺参数
INSERT INTO `process_parameters` (`name`, `code`, `unit`, `current_value`, `min_value`, `max_value`, `standard_value`, `process_section`, `status`) VALUES
('溶解氧', 'DO', 'mg/L', 2.5, 1.0, 4.0, 2.0, '生化处理', 'normal'),
('pH值', 'PH', '', 7.2, 6.0, 9.0, 7.0, '生化处理', 'normal'),
('水温', 'TEMP', '℃', 22.5, 10.0, 35.0, 20.0, '生化处理', 'normal'),
('MLSS', 'MLSS', 'mg/L', 4200, 3000, 5000, 4000, '生化处理', 'normal'),
('污泥沉降比', 'SV30', '%', 32, 20, 40, 30, '生化处理', 'normal'),
('进水流量', 'FLOW_IN', 'm³/h', 650, 400, 800, 600, '预处理', 'normal'),
('出水COD', 'COD_OUT', 'mg/L', 28, 0, 50, 30, '出水', 'normal'),
('出水氨氮', 'NH3N_OUT', 'mg/L', 3.5, 0, 8, 5, '出水', 'normal'),
('进水COD', 'COD_IN', 'mg/L', 185, 100, 300, 200, '进水', 'normal'),
('进水氨氮', 'NH3N_IN', 'mg/L', 38, 20, 50, 35, '进水', 'normal');

-- ----------------------------
-- 设备分类表
-- ----------------------------
DROP TABLE IF EXISTS `equipment_categories`;
CREATE TABLE `equipment_categories` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL COMMENT '分类名称',
  `code` varchar(30) NOT NULL COMMENT '分类编码',
  `parent_id` int DEFAULT '0' COMMENT '父级ID',
  `description` varchar(200) DEFAULT NULL COMMENT '描述',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备分类表';

INSERT INTO `equipment_categories` (`name`, `code`, `parent_id`, `description`) VALUES
('风机', 'FAN', 0, '各类风机设备'),
('水泵', 'PUMP', 0, '各类水泵设备'),
('阀门', 'VALVE', 0, '各类阀门'),
('仪表', 'METER', 0, '各类仪表'),
('电气设备', 'ELEC', 0, '电气控制设备');

-- ----------------------------
-- 设备台账表
-- ----------------------------
DROP TABLE IF EXISTS `equipments`;
CREATE TABLE `equipments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL COMMENT '设备名称',
  `code` varchar(50) NOT NULL COMMENT '设备编码',
  `category_id` int DEFAULT NULL COMMENT '分类ID',
  `model` varchar(100) DEFAULT NULL COMMENT '型号规格',
  `manufacturer` varchar(100) DEFAULT NULL COMMENT '生产厂家',
  `purchase_date` date DEFAULT NULL COMMENT '采购日期',
  `install_date` date DEFAULT NULL COMMENT '安装日期',
  `location` varchar(200) DEFAULT NULL COMMENT '安装位置',
  `process_section` varchar(50) DEFAULT NULL COMMENT '所属工艺段',
  `rated_power` float DEFAULT NULL COMMENT '额定功率kW',
  `status` varchar(20) DEFAULT 'running' COMMENT '状态',
  `running_hours` float DEFAULT '0' COMMENT '累计运行时长',
  `last_maintenance_date` date DEFAULT NULL COMMENT '上次维护日期',
  `next_maintenance_date` date DEFAULT NULL COMMENT '下次维护日期',
  `responsible_person` varchar(50) DEFAULT NULL COMMENT '责任人',
  `qr_code` varchar(200) DEFAULT NULL COMMENT '二维码',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备台账表';

INSERT INTO `equipments` (`name`, `code`, `category_id`, `model`, `manufacturer`, `location`, `process_section`, `rated_power`, `status`, `running_hours`, `responsible_person`) VALUES
('曝气风机#1', 'EQ001', 1, 'DL-200', '上海鼓风机厂', '风机房', '生化处理', 200, 'running', 12500, '张三'),
('曝气风机#2', 'EQ002', 1, 'DL-200', '上海鼓风机厂', '风机房', '生化处理', 200, 'running', 11800, '张三'),
('曝气风机#3', 'EQ003', 1, 'DL-200', '上海鼓风机厂', '风机房', '生化处理', 200, 'stopped', 10200, '张三'),
('提升泵#1', 'EQ004', 2, 'QW-150', '南方泵业', '进水泵房', '预处理', 55, 'running', 8500, '李四'),
('提升泵#2', 'EQ005', 2, 'QW-150', '南方泵业', '进水泵房', '预处理', 55, 'running', 7800, '李四'),
('回流泵#1', 'EQ006', 2, 'QW-100', '南方泵业', '回流泵房', '生化处理', 37, 'running', 6500, '李四'),
('刮泥机', 'EQ007', 5, 'ZGN-30', '无锡环保', '二沉池', '生化处理', 5.5, 'maintenance', 6200, '王五');

-- ----------------------------
-- 异常告警表
-- ----------------------------
DROP TABLE IF EXISTS `abnormal_alarms`;
CREATE TABLE `abnormal_alarms` (
  `id` int NOT NULL AUTO_INCREMENT,
  `alarm_no` varchar(50) NOT NULL COMMENT '告警编号',
  `alarm_type` varchar(50) NOT NULL COMMENT '告警类型',
  `alarm_level` enum('normal','warning','urgent') DEFAULT 'normal' COMMENT '告警级别',
  `title` varchar(200) NOT NULL COMMENT '告警标题',
  `description` text COMMENT '告警描述',
  `source` varchar(100) DEFAULT NULL COMMENT '告警来源',
  `related_param` varchar(50) DEFAULT NULL COMMENT '关联参数',
  `current_value` float DEFAULT NULL COMMENT '当前值',
  `threshold_value` float DEFAULT NULL COMMENT '阈值',
  `status` enum('pending','processing','resolved') DEFAULT 'pending' COMMENT '状态',
  `handler_id` int DEFAULT NULL COMMENT '处理人ID',
  `handler_name` varchar(50) DEFAULT NULL COMMENT '处理人姓名',
  `handle_time` datetime DEFAULT NULL COMMENT '处理时间',
  `handle_result` text COMMENT '处理结果',
  `alarm_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '告警时间',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_alarm_no` (`alarm_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='异常告警表';

INSERT INTO `abnormal_alarms` (`alarm_no`, `alarm_type`, `alarm_level`, `title`, `description`, `current_value`, `threshold_value`, `status`, `alarm_time`) VALUES
('ALM20240115001', '水质超标', 'urgent', '出水COD超标', '出水COD超过排放标准', 35, 30, 'pending', '2024-01-15 10:30:00'),
('ALM20240115002', '工艺参数异常', 'warning', '生化池DO偏低', '溶解氧浓度低于设定值', 1.2, 1.5, 'processing', '2024-01-15 11:15:00'),
('ALM20240115003', '工况异常', 'normal', '进水流量波动', '进水流量超出正常范围', 750, 700, 'resolved', '2024-01-15 12:00:00');

-- ----------------------------
-- 系统配置表
-- ----------------------------
DROP TABLE IF EXISTS `system_configs`;
CREATE TABLE `system_configs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `config_key` varchar(100) NOT NULL COMMENT '配置键',
  `config_value` text COMMENT '配置值',
  `config_type` varchar(30) DEFAULT NULL COMMENT '配置类型',
  `description` varchar(200) DEFAULT NULL COMMENT '描述',
  `is_editable` tinyint(1) DEFAULT '1' COMMENT '是否可编辑',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_config_key` (`config_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置表';

INSERT INTO `system_configs` (`config_key`, `config_value`, `config_type`, `description`, `is_editable`) VALUES
('system.name', '污水处理厂智能管理系统', 'other', '系统名称', 1),
('alarm.cod_threshold', '30', 'alarm', 'COD告警阈值(mg/L)', 1),
('alarm.nh3n_threshold', '5', 'alarm', '氨氮告警阈值(mg/L)', 1),
('alarm.do_min', '1.5', 'alarm', 'DO最小值告警阈值(mg/L)', 1),
('report.auto_generate', 'true', 'report', '是否自动生成日报', 1),
('report.generate_time', '08:00', 'report', '日报生成时间', 1);

-- ----------------------------
-- 消息表
-- ----------------------------
DROP TABLE IF EXISTS `messages`;
CREATE TABLE `messages` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(200) NOT NULL COMMENT '消息标题',
  `content` text COMMENT '消息内容',
  `summary` varchar(500) COMMENT '消息摘要',
  `message_type` enum('alarm','approval','workorder','announcement') NOT NULL COMMENT '消息类型',
  `priority` enum('low','medium','high','urgent') NOT NULL DEFAULT 'medium' COMMENT '优先级',
  `sender_id` int DEFAULT NULL COMMENT '发送人ID',
  `sender_name` varchar(50) DEFAULT NULL COMMENT '发送人姓名',
  `related_type` varchar(50) DEFAULT NULL COMMENT '关联业务类型',
  `related_id` int DEFAULT NULL COMMENT '关联业务ID',
  `related_url` varchar(500) DEFAULT NULL COMMENT '关联跳转URL',
  `is_global` tinyint(1) DEFAULT '0' COMMENT '是否全局消息',
  `target_user_ids` text COMMENT '目标用户ID列表(逗号分隔)',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_message_type` (`message_type`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息表';

-- 初始化示例消息数据
INSERT INTO `messages` (`title`, `content`, `summary`, `message_type`, `priority`, `sender_name`, `related_type`, `related_id`, `related_url`, `is_global`, `target_user_ids`, `created_at`) VALUES
('出水COD超标告警', '检测到出水COD浓度为35mg/L，超过排放标准30mg/L，请及时处理。', '出水COD浓度超标，需要立即处理', 'alarm', 'urgent', '系统监测', 'alarm', 1, '/production/alarm', 1, NULL, '2024-01-15 10:30:00'),
('作业许可审批待处理', '您有一条新的作业许可申请等待审批，申请人：张三，作业类型：高处作业。', '作业许可审批待处理', 'approval', 'high', '张三', 'permit', 1, '/safety/permit', 0, '1,2', '2024-01-15 09:15:00'),
('新工单指派', '您被指派处理新的工单：曝气风机#1异常振动检查，工单编号：WO20240115001。', '新工单：曝气风机#1异常振动检查', 'workorder', 'high', '李四', 'workorder', 1, '/workorder-center', 0, '2,3', '2024-01-15 08:45:00'),
('系统维护公告', '系统将于2024年01月20日22:00-24:00进行例行维护，期间可能影响部分功能使用，请提前做好相关工作安排。', '系统将于1月20日晚进行例行维护', 'announcement', 'medium', '系统管理员', NULL, NULL, NULL, 1, NULL, '2024-01-15 08:00:00'),
('生化池DO偏低告警', '生化池溶解氧浓度为1.2mg/L，低于设定阈值1.5mg/L，请检查曝气系统运行状态。', '生化池DO浓度偏低，需要检查曝气系统', 'alarm', 'high', '系统监测', 'alarm', 2, '/production/alarm', 1, NULL, '2024-01-14 16:20:00'),
('设备维护提醒', '刮泥机设备维护时间已到，请安排维护人员进行定期维护保养。', '刮泥机需要进行定期维护', 'workorder', 'medium', '系统提醒', 'equipment', 7, '/equipment/maintenance', 0, '2,5', '2024-01-14 14:00:00'),
('月度绩效考核通知', '2024年1月绩效考核已开始，请各部门于1月25日前完成绩效数据填报工作。', '1月绩效考核已开始，请按时填报', 'announcement', 'medium', '人力资源部', NULL, NULL, NULL, 1, NULL, '2024-01-14 10:00:00'),
('安全培训审批通过', '您提交的安全培训申请已通过审批，培训时间：2024年01月18日14:00-16:00。', '安全培训申请已通过审批', 'approval', 'medium', '赵六', 'training', 1, '/safety/training', 0, '3,4', '2024-01-13 15:30:00');

-- ----------------------------
-- 用户消息已读状态表
-- ----------------------------
DROP TABLE IF EXISTS `user_message_reads`;
CREATE TABLE `user_message_reads` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL COMMENT '用户ID',
  `message_id` int NOT NULL COMMENT '消息ID',
  `is_read` tinyint(1) DEFAULT '0' COMMENT '是否已读',
  `read_at` datetime DEFAULT NULL COMMENT '阅读时间',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_message` (`user_id`, `message_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_message_id` (`message_id`),
  KEY `idx_is_read` (`is_read`),
  CONSTRAINT `fk_user_message_reads_message` FOREIGN KEY (`message_id`) REFERENCES `messages` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户消息已读状态表';

-- ----------------------------
-- 现场数据采集模板表
-- ----------------------------
DROP TABLE IF EXISTS `field_data_templates`;
CREATE TABLE `field_data_templates` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL COMMENT '模板名称',
  `code` varchar(50) NOT NULL COMMENT '模板编码',
  `description` varchar(500) DEFAULT NULL COMMENT '模板描述',
  `template_type` varchar(20) DEFAULT 'daily' COMMENT '模板类型：daily日报/shift班报/weekly周报/monthly月报',
  `is_active` tinyint(1) DEFAULT '1' COMMENT '是否启用',
  `created_by` int DEFAULT NULL COMMENT '创建人ID',
  `created_by_name` varchar(50) DEFAULT NULL COMMENT '创建人姓名',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='现场数据采集模板表';

-- 初始化示例模板
INSERT INTO `field_data_templates` (`name`, `code`, `description`, `template_type`, `is_active`, `created_by`, `created_by_name`) VALUES
('运行日报', 'DAILY_RUN', '每日运行数据填报，包含水质、工艺参数等核心数据', 'daily', 1, 1, '系统管理员'),
('班报-早班', 'SHIFT_MORNING', '早班现场数据采集，8:00-16:00运行记录', 'shift', 1, 1, '系统管理员'),
('班报-中班', 'SHIFT_AFTERNOON', '中班现场数据采集，16:00-24:00运行记录', 'shift', 1, 1, '系统管理员'),
('班报-晚班', 'SHIFT_NIGHT', '晚班现场数据采集，0:00-8:00运行记录', 'shift', 1, 1, '系统管理员'),
('水质周报', 'WEEKLY_WATER', '每周水质分析汇总报表', 'weekly', 0, 1, '系统管理员');

-- ----------------------------
-- 模板字段表
-- ----------------------------
DROP TABLE IF EXISTS `field_data_template_fields`;
CREATE TABLE `field_data_template_fields` (
  `id` int NOT NULL AUTO_INCREMENT,
  `template_id` int NOT NULL COMMENT '模板ID',
  `field_name` varchar(100) NOT NULL COMMENT '字段名称',
  `field_code` varchar(50) NOT NULL COMMENT '字段编码',
  `field_type` varchar(20) DEFAULT 'text' COMMENT '字段类型：number数字/text文本/select单选下拉',
  `is_required` tinyint(1) DEFAULT '0' COMMENT '是否必填',
  `default_value` varchar(500) DEFAULT NULL COMMENT '默认值',
  `options` text COMMENT '下拉选项(JSON数组格式)',
  `unit` varchar(20) DEFAULT NULL COMMENT '单位(数字类型使用)',
  `sort_order` int DEFAULT '0' COMMENT '排序',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_template_id` (`template_id`),
  CONSTRAINT `fk_template_fields` FOREIGN KEY (`template_id`) REFERENCES `field_data_templates` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='模板字段表';

-- 初始化运行日报字段
INSERT INTO `field_data_template_fields` (`template_id`, `field_name`, `field_code`, `field_type`, `is_required`, `default_value`, `unit`, `sort_order`) VALUES
(1, '进水COD', 'COD_IN', 'number', 1, NULL, 'mg/L', 1),
(1, '出水COD', 'COD_OUT', 'number', 1, NULL, 'mg/L', 2),
(1, '进水氨氮', 'NH3N_IN', 'number', 1, NULL, 'mg/L', 3),
(1, '出水氨氮', 'NH3N_OUT', 'number', 1, NULL, 'mg/L', 4),
(1, '进水流量', 'FLOW_IN', 'number', 1, NULL, 'm³/h', 5),
(1, '出水流量', 'FLOW_OUT', 'number', 1, NULL, 'm³/h', 6),
(1, '溶解氧', 'DO', 'number', 0, '2.0', 'mg/L', 7),
(1, 'MLSS', 'MLSS', 'number', 0, '4000', 'mg/L', 8),
(1, 'pH值', 'PH', 'number', 0, '7.0', '', 9),
(1, '运行状态', 'STATUS', 'select', 1, '正常', NULL, 10),
(1, '值班人员', 'DUTY', 'text', 0, NULL, NULL, 11),
(1, '设备巡检情况', 'INSPECTION', 'text', 0, NULL, NULL, 12);

-- 初始化运行状态选项
UPDATE `field_data_template_fields` SET `options` = '["正常","异常","停机"]' WHERE `field_code` = 'STATUS';

-- 初始化早班班报字段
INSERT INTO `field_data_template_fields` (`template_id`, `field_name`, `field_code`, `field_type`, `is_required`, `default_value`, `unit`, `sort_order`) VALUES
(2, '进水COD', 'COD_IN', 'number', 1, NULL, 'mg/L', 1),
(2, '出水COD', 'COD_OUT', 'number', 1, NULL, 'mg/L', 2),
(2, '溶解氧', 'DO', 'number', 1, NULL, 'mg/L', 3),
(2, '曝气风机运行台数', 'FAN_COUNT', 'number', 1, '4', '台', 4),
(2, '设备运行情况', 'EQUIPMENT', 'select', 1, '正常', NULL, 5),
(2, '异常情况记录', 'ABNORMAL', 'text', 0, NULL, NULL, 6),
(2, '交接班说明', 'HANDOVER', 'text', 0, NULL, NULL, 7);

-- 初始化设备运行情况选项
UPDATE `field_data_template_fields` SET `options` = '["正常","轻微异常","严重异常"]' WHERE `template_id` = 2 AND `field_code` = 'EQUIPMENT';

-- 复制早班字段到中班和晚班
INSERT INTO `field_data_template_fields` (`template_id`, `field_name`, `field_code`, `field_type`, `is_required`, `default_value`, `options`, `unit`, `sort_order`)
SELECT 3, `field_name`, `field_code`, `field_type`, `is_required`, `default_value`, `options`, `unit`, `sort_order`
FROM `field_data_template_fields` WHERE `template_id` = 2;

INSERT INTO `field_data_template_fields` (`template_id`, `field_name`, `field_code`, `field_type`, `is_required`, `default_value`, `options`, `unit`, `sort_order`)
SELECT 4, `field_name`, `field_code`, `field_type`, `is_required`, `default_value`, `options`, `unit`, `sort_order`
FROM `field_data_template_fields` WHERE `template_id` = 2;

-- ----------------------------
-- 填报记录表
-- ----------------------------
DROP TABLE IF EXISTS `field_data_records`;
CREATE TABLE `field_data_records` (
  `id` int NOT NULL AUTO_INCREMENT,
  `template_id` int NOT NULL COMMENT '模板ID',
  `record_date` datetime NOT NULL COMMENT '填报日期',
  `shift` varchar(20) DEFAULT NULL COMMENT '班次：morning早班/afternoon中班/night晚班',
  `operator_id` int DEFAULT NULL COMMENT '填报人ID',
  `operator_name` varchar(50) DEFAULT NULL COMMENT '填报人姓名',
  `remark` text COMMENT '备注',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_template_id` (`template_id`),
  KEY `idx_record_date` (`record_date`),
  CONSTRAINT `fk_record_template` FOREIGN KEY (`template_id`) REFERENCES `field_data_templates` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='填报记录表';

-- ----------------------------
-- 填报记录数据值表
-- ----------------------------
DROP TABLE IF EXISTS `field_data_record_values`;
CREATE TABLE `field_data_record_values` (
  `id` int NOT NULL AUTO_INCREMENT,
  `record_id` int NOT NULL COMMENT '记录ID',
  `field_id` int NOT NULL COMMENT '字段ID',
  `field_name` varchar(100) NOT NULL COMMENT '字段名称(快照)',
  `field_value` text COMMENT '字段值',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_record_id` (`record_id`),
  KEY `idx_field_id` (`field_id`),
  CONSTRAINT `fk_value_record` FOREIGN KEY (`record_id`) REFERENCES `field_data_records` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_value_field` FOREIGN KEY (`field_id`) REFERENCES `field_data_template_fields` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='填报记录数据值表';

SET FOREIGN_KEY_CHECKS = 1;
