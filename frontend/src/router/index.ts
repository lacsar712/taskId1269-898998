import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/drill/check-in/:token',
      name: 'DrillCheckInPublic',
      component: () => import('@/views/safety/DrillCheckIn.vue'),
      meta: { requiresAuth: false, hidden: true }
    },
    {
      path: '/',
      component: () => import('@/views/Layout.vue'),
      redirect: '/dashboard',
      children: [
        // 仪表盘
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/Dashboard.vue'),
          meta: { title: '首页', icon: 'icon-dashboard' }
        },
        // 统一工单中心
        {
          path: 'workorder-center',
          name: 'WorkOrderCenter',
          component: () => import('@/views/WorkOrderCenter.vue'),
          meta: { title: '统一工单中心', icon: 'icon-unordered-list' }
        },
        // 消息中心
        {
          path: 'message-center',
          name: 'MessageCenter',
          component: () => import('@/views/MessageCenter.vue'),
          meta: { title: '消息中心', icon: 'icon-notification', hidden: true }
        },
        // 生产管理
        {
          path: 'production',
          name: 'Production',
          redirect: '/production/monitor',
          meta: { title: '生产管理', icon: 'icon-settings' },
          children: [
            {
              path: 'monitor',
              name: 'ProcessMonitor',
              component: () => import('@/views/production/ProcessMonitor.vue'),
              meta: { title: '工艺运行监控' }
            },
            {
              path: 'plan',
              name: 'ProductionPlan',
              component: () => import('@/views/production/ProductionPlan.vue'),
              meta: { title: '生产计划调度' }
            },
            {
              path: 'log',
              name: 'ProductionLog',
              component: () => import('@/views/production/ProductionLog.vue'),
              meta: { title: '生产日志管理' }
            },
            {
              path: 'abnormal',
              name: 'AbnormalHandling',
              component: () => import('@/views/production/AbnormalHandling.vue'),
              meta: { title: '异常处理' }
            },
            {
              path: 'optimization',
              name: 'ProcessOptimization',
              component: () => import('@/views/production/ProcessOptimization.vue'),
              meta: { title: '工艺优化' }
            },
            {
              path: 'alarm',
              name: 'AlarmList',
              component: () => import('@/views/production/AlarmList.vue'),
              meta: { title: '异常告警列表' }
            },
            {
              path: 'schedule',
              name: 'TeamSchedule',
              component: () => import('@/views/production/TeamSchedule.vue'),
              meta: { title: '班组排班表' }
            }
          ]
        },
        // 安全管理
        {
          path: 'safety',
          name: 'Safety',
          redirect: '/safety/inspection',
          meta: { title: '安全管理', icon: 'icon-safe' },
          children: [
            {
              path: 'inspection',
              name: 'SafetyInspection',
              component: () => import('@/views/safety/SafetyInspection.vue'),
              meta: { title: '安全巡检' }
            },
            {
              path: 'risk',
              name: 'RiskControl',
              component: () => import('@/views/safety/RiskControl.vue'),
              meta: { title: '风险管控' }
            },
            {
              path: 'emergency',
              name: 'EmergencyManagement',
              component: () => import('@/views/safety/EmergencyManagement.vue'),
              meta: { title: '应急管理' }
            },
            {
              path: 'training',
              name: 'SafetyTraining',
              component: () => import('@/views/safety/SafetyTraining.vue'),
              meta: { title: '安全培训' }
            },
            {
              path: 'permit',
              name: 'WorkPermit',
              component: () => import('@/views/safety/WorkPermit.vue'),
              meta: { title: '作业许可' }
            },
            {
              path: 'drill',
              name: 'DrillManagement',
              component: () => import('@/views/safety/DrillManagement.vue'),
              meta: { title: '应急演练签到' }
            },
            {
              path: 'video-inspection',
              name: 'VideoInspectionPoints',
              component: () => import('@/views/safety/VideoInspectionPoints.vue'),
              meta: { title: '视频巡检点位' }
            },
            {
              path: 'video-abnormal',
              name: 'VideoInspectionAbnormal',
              component: () => import('@/views/safety/VideoInspectionAbnormal.vue'),
              meta: { title: '视频巡检异常汇总', hidden: true }
            }
          ]
        },
        // 设备管理
        {
          path: 'equipment',
          name: 'Equipment',
          redirect: '/equipment/ledger',
          meta: { title: '设备管理', icon: 'icon-computer' },
          children: [
            {
              path: 'ledger',
              name: 'EquipmentLedger',
              component: () => import('@/views/equipment/EquipmentLedger.vue'),
              meta: { title: '设备台账' }
            },
            {
              path: 'monitor',
              name: 'EquipmentMonitor',
              component: () => import('@/views/equipment/EquipmentMonitor.vue'),
              meta: { title: '运行监控' }
            },
            {
              path: 'maintenance',
              name: 'Maintenance',
              component: () => import('@/views/equipment/Maintenance.vue'),
              meta: { title: '维护保养' }
            },
            {
              path: 'fault',
              name: 'FaultManagement',
              component: () => import('@/views/equipment/FaultManagement.vue'),
              meta: { title: '故障管理' }
            },
            {
              path: 'spare',
              name: 'SparePartManagement',
              component: () => import('@/views/equipment/SparePartManagement.vue'),
              meta: { title: '备件管理' }
            },
            {
              path: 'fault-alarm',
              name: 'FaultAlarm',
              component: () => import('@/views/equipment/FaultAlarm.vue'),
              meta: { title: '故障告警' }
            },
            {
              path: 'analysis',
              name: 'EquipmentAnalysis',
              component: () => import('@/views/equipment/EquipmentAnalysis.vue'),
              meta: { title: '设备分析' }
            }
          ]
        },
        // 化验管理
        {
          path: 'laboratory',
          name: 'Laboratory',
          redirect: '/laboratory/sample',
          meta: { title: '化验管理', icon: 'icon-experiment' },
          children: [
            {
              path: 'sample',
              name: 'SampleManagement',
              component: () => import('@/views/laboratory/SampleManagement.vue'),
              meta: { title: '样品管理' }
            },
            {
              path: 'task',
              name: 'DetectionTask',
              component: () => import('@/views/laboratory/DetectionTask.vue'),
              meta: { title: '检测任务' }
            },
            {
              path: 'data',
              name: 'DataManagement',
              component: () => import('@/views/laboratory/DataManagement.vue'),
              meta: { title: '数据管理' }
            },
            {
              path: 'report',
              name: 'ReportManagement',
              component: () => import('@/views/laboratory/ReportManagement.vue'),
              meta: { title: '报告管理' }
            },
            {
              path: 'qc',
              name: 'QCManagement',
              component: () => import('@/views/laboratory/QCManagement.vue'),
              meta: { title: '质控管理' }
            },
            {
              path: 'standard',
              name: 'StandardLibrary',
              component: () => import('@/views/laboratory/StandardLibrary.vue'),
              meta: { title: '标准库' }
            }
          ]
        },
        // 生产报表
        {
          path: 'report',
          name: 'Report',
          redirect: '/report/regular',
          meta: { title: '生产报表', icon: 'icon-file' },
          children: [
            {
              path: 'regular',
              name: 'RegularReport',
              component: () => import('@/views/report/RegularReport.vue'),
              meta: { title: '常规报表' }
            },
            {
              path: 'weekly',
              name: 'WeeklyReportList',
              component: () => import('@/views/report/WeeklyReportList.vue'),
              meta: { title: '运行周报' }
            },
            {
              path: 'weekly/edit',
              name: 'WeeklyReportCreate',
              component: () => import('@/views/report/WeeklyReportEdit.vue'),
              meta: { title: '新建周报', hidden: true }
            },
            {
              path: 'weekly/edit/:id',
              name: 'WeeklyReportEdit',
              component: () => import('@/views/report/WeeklyReportEdit.vue'),
              meta: { title: '编辑周报', hidden: true }
            },
            {
              path: 'custom',
              name: 'CustomReport',
              component: () => import('@/views/report/CustomReport.vue'),
              meta: { title: '自定义报表' }
            },
            {
              path: 'visualization',
              name: 'DataVisualization',
              component: () => import('@/views/report/DataVisualization.vue'),
              meta: { title: '数据可视化' }
            },
            {
              path: 'trace',
              name: 'DataTrace',
              component: () => import('@/views/report/DataTrace.vue'),
              meta: { title: '数据溯源' }
            },
            {
              path: 'prediction',
              name: 'TrendPrediction',
              component: () => import('@/views/report/TrendPrediction.vue'),
              meta: { title: '趋势预测' }
            }
          ]
        },
        // 能耗管理
        {
          path: 'energy',
          name: 'Energy',
          redirect: '/energy/realtime',
          meta: { title: '能耗管理', icon: 'icon-thunderbolt' },
          children: [
            {
              path: 'realtime',
              name: 'EnergyRealtime',
              component: () => import('@/views/energy/EnergyRealtime.vue'),
              meta: { title: '能耗实时监测' }
            },
            {
              path: 'analysis',
              name: 'EnergyAnalysis',
              component: () => import('@/views/energy/EnergyAnalysis.vue'),
              meta: { title: '能耗多维度分析' }
            },
            {
              path: 'saving',
              name: 'EnergySaving',
              component: () => import('@/views/energy/EnergySaving.vue'),
              meta: { title: '节能策略管理' }
            },
            {
              path: 'cost',
              name: 'EnergyCost',
              component: () => import('@/views/energy/EnergyCost.vue'),
              meta: { title: '能耗成本核算' }
            },
            {
              path: 'report',
              name: 'EnergyReport',
              component: () => import('@/views/energy/EnergyReport.vue'),
              meta: { title: '能耗报表' }
            }
          ]
        },
        // 碳排放核算
        {
          path: 'carbon',
          name: 'Carbon',
          redirect: '/carbon/accounting',
          meta: { title: '碳排放核算', icon: 'icon-thunderbolt' },
          children: [
            {
              path: 'accounting',
              name: 'CarbonAccounting',
              component: () => import('@/views/carbon/CarbonAccounting.vue'),
              meta: { title: '碳排放总览' }
            },
            {
              path: 'factors',
              name: 'EmissionFactorManagement',
              component: () => import('@/views/carbon/EmissionFactorManagement.vue'),
              meta: { title: '排放因子管理' }
            }
          ]
        },
        // 成本管理
        {
          path: 'cost',
          name: 'Cost',
          redirect: '/cost/ledger',
          meta: { title: '成本管理', icon: 'icon-dollar' },
          children: [
            {
              path: 'ledger',
              name: 'CostCenterLedger',
              component: () => import('@/views/cost/CostCenterLedger.vue'),
              meta: { title: '成本中心台账' }
            }
          ]
        },
        // 资料管理
        {
          path: 'document',
          name: 'Document',
          redirect: '/document/category',
          meta: { title: '资料管理', icon: 'icon-folder' },
          children: [
            {
              path: 'category',
              name: 'DocumentCategory',
              component: () => import('@/views/document/DocumentCategory.vue'),
              meta: { title: '文档分类管理' }
            },
            {
              path: 'upload',
              name: 'DocumentUpload',
              component: () => import('@/views/document/DocumentUpload.vue'),
              meta: { title: '文档上传管理' }
            },
            {
              path: 'search',
              name: 'DocumentSearch',
              component: () => import('@/views/document/DocumentSearch.vue'),
              meta: { title: '文档检索下载' }
            },
            {
              path: 'archive',
              name: 'DocumentArchive',
              component: () => import('@/views/document/DocumentArchive.vue'),
              meta: { title: '归档备份' }
            },
            {
              path: 'recommend',
              name: 'DocumentRecommend',
              component: () => import('@/views/document/DocumentRecommend.vue'),
              meta: { title: '常用文档推荐' }
            }
          ]
        },
        // 运维知识库
        {
          path: 'knowledge',
          name: 'Knowledge',
          redirect: '/knowledge/list',
          meta: { title: '运维知识库', icon: 'icon-book' },
          children: [
            {
              path: 'list',
              name: 'KnowledgeList',
              component: () => import('@/views/knowledge/KnowledgeList.vue'),
              meta: { title: '知识库列表' }
            },
            {
              path: 'article/:id',
              name: 'KnowledgeDetail',
              component: () => import('@/views/knowledge/KnowledgeDetail.vue'),
              meta: { title: '文章详情', hidden: true }
            }
          ]
        },
        // 物资管理
        {
          path: 'material',
          name: 'Material',
          redirect: '/material/ledger',
          meta: { title: '物资管理', icon: 'icon-storage' },
          children: [
            {
              path: 'ledger',
              name: 'MaterialLedger',
              component: () => import('@/views/material/MaterialLedger.vue'),
              meta: { title: '物资台账' }
            },
            {
              path: 'inbound',
              name: 'InboundManagement',
              component: () => import('@/views/material/InboundManagement.vue'),
              meta: { title: '入库管理' }
            },
            {
              path: 'outbound',
              name: 'OutboundManagement',
              component: () => import('@/views/material/OutboundManagement.vue'),
              meta: { title: '出库管理' }
            },
            {
              path: 'inventory',
              name: 'InventoryManagement',
              component: () => import('@/views/material/InventoryManagement.vue'),
              meta: { title: '库存管理' }
            },
            {
              path: 'purchase',
              name: 'PurchaseManagement',
              component: () => import('@/views/material/PurchaseManagement.vue'),
              meta: { title: '采购管理' }
            },
            {
              path: 'supplier',
              name: 'SupplierManagement',
              component: () => import('@/views/material/SupplierManagement.vue'),
              meta: { title: '供应商管理' }
            }
          ]
        },
        // 绩效管理
        {
          path: 'performance',
          name: 'Performance',
          redirect: '/performance/indicator',
          meta: { title: '绩效管理', icon: 'icon-trophy' },
          children: [
            {
              path: 'indicator',
              name: 'PerformanceIndicator',
              component: () => import('@/views/performance/PerformanceIndicator.vue'),
              meta: { title: '考核指标体系' }
            },
            {
              path: 'data',
              name: 'PerformanceData',
              component: () => import('@/views/performance/PerformanceData.vue'),
              meta: { title: '绩效数据管理' }
            },
            {
              path: 'analysis',
              name: 'PerformanceAnalysis',
              component: () => import('@/views/performance/PerformanceAnalysis.vue'),
              meta: { title: '绩效统计分析' }
            },
            {
              path: 'application',
              name: 'PerformanceApplication',
              component: () => import('@/views/performance/PerformanceApplication.vue'),
              meta: { title: '绩效应用' }
            }
          ]
        },
        // 现场数据填报
        {
          path: 'field-data',
          name: 'FieldData',
          redirect: '/field-data/fill',
          meta: { title: '现场数据填报', icon: 'icon-edit' },
          children: [
            {
              path: 'fill',
              name: 'DataFill',
              component: () => import('@/views/field-data/DataFill.vue'),
              meta: { title: '数据填报' }
            },
            {
              path: 'record',
              name: 'RecordQuery',
              component: () => import('@/views/field-data/RecordQuery.vue'),
              meta: { title: '记录查询' }
            },
            {
              path: 'template',
              name: 'TemplateManagement',
              component: () => import('@/views/field-data/TemplateManagement.vue'),
              meta: { title: '模板管理' }
            }
          ]
        },
        // 系统设置
        {
          path: 'system',
          name: 'System',
          redirect: '/system/project',
          meta: { title: '系统设置', icon: 'icon-settings' },
          children: [
            {
              path: 'project',
              name: 'ProjectManagement',
              component: () => import('@/views/system/ProjectManagement.vue'),
              meta: { title: '项目管理' }
            },
            {
              path: 'user',
              name: 'UserManagement',
              component: () => import('@/views/system/UserManagement.vue'),
              meta: { title: '用户管理' }
            },
            {
              path: 'role',
              name: 'RoleManagement',
              component: () => import('@/views/system/RoleManagement.vue'),
              meta: { title: '角色权限管理' }
            },
            {
              path: 'basic',
              name: 'BasicDataManagement',
              component: () => import('@/views/system/BasicDataManagement.vue'),
              meta: { title: '基础数据管理' }
            },
            {
              path: 'params',
              name: 'SystemParams',
              component: () => import('@/views/system/SystemParams.vue'),
              meta: { title: '系统参数设置' }
            },
            {
              path: 'log',
              name: 'LogManagement',
              component: () => import('@/views/system/LogManagement.vue'),
              meta: { title: '日志管理' }
            },
            {
              path: 'interface',
              name: 'InterfaceConfig',
              component: () => import('@/views/system/InterfaceConfig.vue'),
              meta: { title: '接口配置' }
            },
            {
              path: 'maintenance',
              name: 'SystemMaintenance',
              component: () => import('@/views/system/SystemMaintenance.vue'),
              meta: { title: '系统维护' }
            }
          ]
        }
      ]
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth !== false && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router
