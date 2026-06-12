from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.models.knowledge import KnowledgeCategory, KnowledgeArticle, KnowledgeFeedback
from app.schemas.common import PaginatedResponse, MessageResponse
from app.services.auth import get_current_active_user
import json

router = APIRouter(prefix="/api/knowledge", tags=["运维知识库"])


class KnowledgeCategoryResponse(BaseModel):
    id: int
    name: str
    code: str
    parent_id: int
    sort_order: int
    description: Optional[str]
    icon: Optional[str]

    class Config:
        from_attributes = True


class KnowledgeArticleListResponse(BaseModel):
    id: int
    title: str
    summary: Optional[str]
    category_id: Optional[int]
    category_name: Optional[str] = ""
    tags: Optional[str]
    author_name: Optional[str]
    view_count: int
    helpful_count: int
    unhelpful_count: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class KnowledgeArticleDetailResponse(BaseModel):
    id: int
    title: str
    summary: Optional[str]
    content: str
    category_id: Optional[int]
    category_name: Optional[str] = ""
    tags: Optional[str]
    author_name: Optional[str]
    view_count: int
    helpful_count: int
    unhelpful_count: int
    attachment_names: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    user_feedback: Optional[int] = 0

    class Config:
        from_attributes = True


class KnowledgeArticleCreate(BaseModel):
    title: str
    summary: Optional[str] = None
    content: str
    category_id: Optional[int] = None
    tags: Optional[str] = None
    attachment_names: Optional[str] = None


class KnowledgeFeedbackCreate(BaseModel):
    is_helpful: int
    comment: Optional[str] = None


def get_category_name_map(db: Session):
    categories = db.query(KnowledgeCategory).all()
    return {cat.id: cat.name for cat in categories}


@router.get("/categories", response_model=List[KnowledgeCategoryResponse])
def get_knowledge_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return db.query(KnowledgeCategory).order_by(KnowledgeCategory.sort_order).all()


@router.post("/categories", response_model=KnowledgeCategoryResponse)
def create_knowledge_category(
    name: str,
    parent_id: int = 0,
    description: Optional[str] = None,
    icon: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    code = f"KC{datetime.now().strftime('%Y%m%d%H%M%S')}"
    category = KnowledgeCategory(
        name=name,
        code=code,
        parent_id=parent_id,
        description=description,
        icon=icon
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("/articles", response_model=PaginatedResponse[KnowledgeArticleListResponse])
def get_knowledge_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category_id: Optional[int] = None,
    keyword: Optional[str] = None,
    tag: Optional[str] = None,
    sort_by: Optional[str] = "latest",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(KnowledgeArticle).filter(KnowledgeArticle.status == "published")

    if category_id:
        query = query.filter(KnowledgeArticle.category_id == category_id)

    if keyword:
        query = query.filter(
            or_(
                KnowledgeArticle.title.contains(keyword),
                KnowledgeArticle.summary.contains(keyword),
                KnowledgeArticle.content.contains(keyword)
            )
        )

    if tag:
        query = query.filter(KnowledgeArticle.tags.contains(tag))

    if sort_by == "hot":
        query = query.order_by(desc(KnowledgeArticle.view_count))
    elif sort_by == "helpful":
        query = query.order_by(desc(KnowledgeArticle.helpful_count))
    else:
        query = query.order_by(desc(KnowledgeArticle.created_at))

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    category_map = get_category_name_map(db)
    result_items = []
    for item in items:
        item_dict = KnowledgeArticleListResponse.from_orm(item)
        item_dict.category_name = category_map.get(item.category_id, "")
        result_items.append(item_dict)

    return PaginatedResponse(
        items=result_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/articles/{article_id}", response_model=KnowledgeArticleDetailResponse)
def get_knowledge_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    article = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    article.view_count += 1
    db.commit()
    db.refresh(article)

    category_map = get_category_name_map(db)

    feedback = db.query(KnowledgeFeedback).filter(
        KnowledgeFeedback.article_id == article_id,
        KnowledgeFeedback.user_id == current_user.id
    ).first()

    result = KnowledgeArticleDetailResponse.from_orm(article)
    result.category_name = category_map.get(article.category_id, "")
    result.user_feedback = feedback.is_helpful if feedback else 0

    return result


@router.post("/articles", response_model=KnowledgeArticleDetailResponse)
def create_knowledge_article(
    data: KnowledgeArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    article = KnowledgeArticle(
        title=data.title,
        summary=data.summary,
        content=data.content,
        category_id=data.category_id,
        tags=data.tags,
        attachment_names=data.attachment_names,
        author_id=current_user.id,
        author_name=current_user.real_name or current_user.username
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.post("/articles/{article_id}/feedback", response_model=MessageResponse)
def submit_feedback(
    article_id: int,
    data: KnowledgeFeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    article = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    existing = db.query(KnowledgeFeedback).filter(
        KnowledgeFeedback.article_id == article_id,
        KnowledgeFeedback.user_id == current_user.id
    ).first()

    if existing:
        old_value = existing.is_helpful
        existing.is_helpful = data.is_helpful
        existing.comment = data.comment
        db.commit()

        if old_value == 1 and data.is_helpful != 1:
            article.helpful_count = max(0, article.helpful_count - 1)
        if old_value == -1 and data.is_helpful != -1:
            article.unhelpful_count = max(0, article.unhelpful_count - 1)
        if data.is_helpful == 1 and old_value != 1:
            article.helpful_count += 1
        if data.is_helpful == -1 and old_value != -1:
            article.unhelpful_count += 1
        db.commit()
    else:
        feedback = KnowledgeFeedback(
            article_id=article_id,
            user_id=current_user.id,
            user_name=current_user.real_name or current_user.username,
            is_helpful=data.is_helpful,
            comment=data.comment
        )
        db.add(feedback)
        db.commit()

        if data.is_helpful == 1:
            article.helpful_count += 1
        elif data.is_helpful == -1:
            article.unhelpful_count += 1
        db.commit()

    return MessageResponse(message="评价成功")


@router.get("/hot/articles", response_model=List[KnowledgeArticleListResponse])
def get_hot_articles(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    articles = db.query(KnowledgeArticle).filter(
        KnowledgeArticle.status == "published"
    ).order_by(desc(KnowledgeArticle.view_count)).limit(limit).all()

    category_map = get_category_name_map(db)
    result = []
    for item in articles:
        item_dict = KnowledgeArticleListResponse.from_orm(item)
        item_dict.category_name = category_map.get(item.category_id, "")
        result.append(item_dict)

    return result


@router.get("/tags", response_model=List[str])
def get_all_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    articles = db.query(KnowledgeArticle).all()
    tag_set = set()
    for article in articles:
        if article.tags:
            try:
                tags = json.loads(article.tags)
                if isinstance(tags, list):
                    tag_set.update(tags)
                else:
                    tag_set.add(article.tags)
            except (json.JSONDecodeError, TypeError):
                tag_set.add(article.tags)
    return list(tag_set)


def init_default_categories(db: Session):
    categories = [
        {"name": "工艺调控", "code": "PROCESS", "icon": "icon-settings", "description": "污水处理工艺运行调控经验"},
        {"name": "设备操作", "code": "EQUIPMENT", "icon": "icon-computer", "description": "各类设备操作维护指南"},
        {"name": "故障排查", "code": "FAULT", "icon": "icon-exclamation-circle", "description": "常见故障诊断与排除方法"},
        {"name": "应急预案", "code": "EMERGENCY", "icon": "icon-safe", "description": "突发情况应急处置方案"},
        {"name": "安全规范", "code": "SAFETY", "icon": "icon-lock", "description": "安全生产操作规程"},
        {"name": "化验检测", "code": "LAB", "icon": "icon-experiment", "description": "水质化验检测方法"},
    ]

    for cat_data in categories:
        existing = db.query(KnowledgeCategory).filter(KnowledgeCategory.code == cat_data["code"]).first()
        if not existing:
            category = KnowledgeCategory(
                name=cat_data["name"],
                code=cat_data["code"],
                icon=cat_data["icon"],
                description=cat_data["description"],
                sort_order=categories.index(cat_data)
            )
            db.add(category)

    sample_articles = [
        {
            "title": "曝气池DO浓度异常升高排查与处理",
            "summary": "本文详细介绍了曝气池溶解氧浓度异常升高的常见原因、排查步骤和处理方法，帮助运维人员快速定位并解决问题。",
            "content": """
## 一、现象描述

曝气池溶解氧(DO)浓度在正常运行情况下突然升高，超出工艺控制范围，可能影响生化处理效果。

## 二、常见原因

### 1. 进水负荷降低
- 进水量减少
- 进水COD/BOD浓度下降
- 工业废水比例变化

### 2. 曝气系统异常
- 曝气头堵塞或损坏
- 曝气量过大
- 曝气均匀性变差

### 3. 活性污泥性状变化
- 污泥浓度降低
- 污泥活性下降
- 微生物种群变化

## 三、排查步骤

1. **检查进水参数**
   - 核实进水量、进水COD、BOD等数据
   - 对比历史数据，确认负荷变化情况

2. **检查曝气系统**
   - 检查各曝气支管阀门开度
   - 检测曝气头曝气状态
   - 校核风机运行参数

3. **检查污泥性状**
   - 测定MLSS、MLVSS
   - 观察污泥沉降比(SV30)
   - 镜检微生物相

## 四、处理方法

### 负荷降低导致的DO升高
1. 适当减少曝气量，维持DO在2-4mg/L
2. 调整污泥回流比，保持污泥浓度稳定
3. 必要时可补充碳源

### 曝气系统问题
1. 清洗或更换堵塞的曝气头
2. 调整风机频率或阀门开度
3. 优化曝气支管配气均匀性

## 五、预防措施

1. 定期巡检曝气系统运行状态
2. 建立进水水质预警机制
3. 制定曝气量自动控制策略
4. 定期清理维护曝气头
            """,
            "category_code": "PROCESS",
            "tags": ["曝气池", "DO", "溶解氧", "工艺调控"],
            "author": "系统管理员"
        },
        {
            "title": "离心泵常见故障诊断与维修指南",
            "summary": "总结了污水处理厂离心泵在运行中常见的故障类型、产生原因及对应的维修处理方法，适用于各类水泵的日常维护。",
            "content": """
## 一、概述

离心泵是污水处理厂最常用的设备之一，掌握其常见故障的诊断与维修方法对保障生产连续运行至关重要。

## 二、常见故障及处理

### 1. 泵不出水

**可能原因：**
- 泵内未充满水或存在空气
- 吸水管路漏气
- 叶轮堵塞
- 电机转向错误
- 吸水扬程过高

**处理方法：**
1. 检查并排除泵内空气
2. 检查吸水管路密封
3. 清理叶轮堵塞物
4. 调整电机转向
5. 降低安装高度或设置引水装置

### 2. 流量不足

**可能原因：**
- 叶轮磨损
- 转速不足
- 出口阀门开度不够
- 管路阻力增大
- 汽蚀现象

**处理方法：**
1. 检查更换磨损叶轮
2. 检查电机及电源
3. 全开出口阀门
4. 检查清理管路
5. 降低吸水高度

### 3. 异常振动与噪音

**可能原因：**
- 轴承损坏
- 叶轮不平衡
- 联轴器不对中
- 基础松动
- 泵内进入异物

**处理方法：**
1. 检查更换轴承
2. 叶轮做动平衡
3. 校正联轴器同轴度
4. 紧固基础螺栓
5. 清理泵内异物

### 4. 轴承过热

**可能原因：**
- 润滑油不足或变质
- 轴承装配不良
- 轴承损坏
- 泵轴弯曲

**处理方法：**
1. 检查补充润滑油
2. 重新装配调整轴承
3. 更换轴承
4. 校正或更换泵轴

## 三、日常维护要点

1. **每日巡检**：检查运行电流、振动、温度、泄漏
2. **每周维护**：检查油位、清理泵体及周边
3. **每月保养**：检查联轴器、紧固各连接螺栓
4. **每年大修**：全面拆解检查，更换易损件

## 四、安全注意事项

1. 维修前必须断电、挂牌
2. 关闭进出口阀门，放空泵内液体
3. 高空作业必须系安全带
4. 使用合格的专用工具
            """,
            "category_code": "EQUIPMENT",
            "tags": ["离心泵", "设备维护", "故障维修"],
            "author": "系统管理员"
        },
        {
            "title": "污泥膨胀应急处置预案",
            "summary": "针对活性污泥法运行中可能出现的污泥膨胀问题，制定详细的应急响应流程和处置措施，确保工艺安全稳定运行。",
            "content": """
## 一、适用范围

本预案适用于采用活性污泥法工艺的污水处理系统发生污泥膨胀时的应急处置。

## 二、定义与判定

### 污泥膨胀的判定标准
- SVI > 150 mL/g
- 污泥沉降性能变差，出水浑浊
- 二沉池液面出现大量泡沫或浮渣
- 镜检发现丝状菌大量增殖

## 三、组织机构与职责

### 应急领导小组
- **组长**：厂长/运行主管
- **成员**：工艺工程师、设备主管、班组长

### 主要职责
1. 负责应急响应的启动与终止
2. 组织制定应急处置方案
3. 协调各部门应急资源
4. 负责对外报告与信息发布

## 四、应急响应流程

### 第一步：发现与报告
1. 运行人员发现污泥膨胀迹象
2. 立即报告班组长及工艺工程师
3. 工艺工程师核实情况，报告应急领导小组

### 第二步：应急启动
1. 领导小组决定启动应急响应
2. 成立现场处置小组
3. 明确各岗位人员职责

### 第三步：原因排查
1. 进水水质检测（COD、BOD、氮磷、pH、有毒物质等）
2. 运行参数核查（DO、MLSS、F/M、污泥龄等）
3. 工艺系统检查（曝气、回流、排泥等）
4. 镜检分析丝状菌类型

### 第四步：应急处置
根据排查结果采取针对性措施：

**水质冲击型膨胀：**
1. 降低进水量或进行水质调节
2. 增加DO浓度
3. 适量投加混凝剂
4. 加大剩余污泥排放

**丝状菌膨胀：**
1. 调整曝气强度，控制DO
2. 调整营养配比，补充氮磷
3. 投加杀菌剂（需谨慎控制剂量）
4. 考虑投加载体或采用生物选择器

**污泥老化型膨胀：**
1. 加大剩余污泥排放量
2. 缩短污泥龄
3. 适当提高有机负荷

## 五、恢复与善后

1. **系统恢复**：污泥沉降性能改善后，逐步恢复正常运行参数
2. **效果评估**：对处置效果进行总结评估
3. **原因分析**：深入分析事故根本原因
4. **完善措施**：修订工艺规程，加强预防措施
5. **培训教育**：组织全员培训，提高应急能力

## 六、应急物资储备

- 应急药品：聚合氯化铝、聚丙烯酰胺、次氯酸钠等
- 检测设备：便携式DO仪、MLSS仪、显微镜等
- 防护用品：防护服、防毒面具、手套等

## 七、联系电话

- 厂长：XXX-XXXXXXX
- 工艺工程师：XXX-XXXXXXX
- 设备主管：XXX-XXXXXXX
- 环保部门：XXX-XXXXXXX
            """,
            "category_code": "EMERGENCY",
            "tags": ["污泥膨胀", "应急预案", "活性污泥"],
            "author": "系统管理员"
        },
        {
            "title": "有限空间作业安全操作规程",
            "summary": "规范污水处理厂有限空间作业的安全管理，明确作业程序、防护要求和应急措施，防止中毒、窒息等安全事故发生。",
            "content": """
## 一、适用范围

本规程适用于污水处理厂内各类有限空间作业，包括但不限于：
- 各类水池、沉淀池、曝气池内部
- 检查井、阀门井、集水井
- 污泥消化池、储泥池
- 管道、箱涵、隧道等

## 二、术语定义

**有限空间**：封闭或部分封闭，进出口较为狭窄有限，未被设计为固定工作场所，自然通风不良，易造成有毒有害、易燃易爆物质积聚或氧含量不足的空间。

## 三、作业审批

### 作业申请
1. 作业单位填写《有限空间作业审批表》
2. 明确作业内容、时间、地点、人员
3. 制定作业方案和应急救援预案
4. 安全管理部门审核批准

### 审批要求
- 必须进行危险有害因素辨识
- 必须制定专项作业方案
- 必须配备应急救援装备
- 必须明确现场监护人员

## 四、安全作业程序

### 第一步：作业前准备

1. **安全交底**
   - 对作业人员进行安全技术交底
   - 明确作业风险和安全注意事项
   - 确认作业人员身体状况良好

2. **设备检查**
   - 检查通风设备、检测仪器
   - 检查个人防护用品
   - 检查通讯设备、应急救援器材
   - 确保所有设备完好有效

3. **现场警戒**
   - 设置警示标志和围栏
   - 清理作业通道
   - 禁止无关人员进入

### 第二步：通风与检测

1. **强制通风**
   - 打开所有出入口
   - 采用机械通风，通风时间不少于30分钟
   - 通风设备应放置在上风向

2. **气体检测**
   - 检测项目：氧含量、有毒有害气体、可燃气体
   - 检测点：上、中、下三个部位
   - 合格标准：
     - 氧含量：19.5% ~ 23.5%
     - 有毒气体：低于职业接触限值
     - 可燃气体：低于爆炸下限的10%

3. **检测要求**
   - 作业前30分钟内检测
   - 作业中每2小时复测一次
   - 作业中断后重新检测
   - 检测人员必须在有限空间外检测

### 第三步：作业实施

1. **人员防护**
   - 正确佩戴个人防护用品
   - 系好安全带和安全绳
   - 携带通讯设备

2. **监护要求**
   - 必须有专人监护，监护人员不得离开
   - 保持与作业人员的持续联系
   - 发现异常立即通知作业人员撤离

3. **作业规范**
   - 严格按照作业方案实施
   - 禁止使用明火
   - 工具、材料系绳传递
   - 发现异常立即停止作业并撤离

### 第四步：作业结束

1. 清点作业人员和工具
2. 关闭出入口，恢复现场
3. 整理作业记录
4. 清理现场卫生

## 五、应急救援

### 救援原则
- 先防护后救援
- 先通风后进入
- 禁止盲目施救

### 救援措施
1. 立即发出救援信号
2. 启动应急救援预案
3. 救援人员必须佩戴防护装备
4. 必要时拨打120急救电话

## 六、处罚规定

违反本规程的行为，按照厂安全管理规定进行处罚；造成事故的，依法追究相关人员责任。
            """,
            "category_code": "SAFETY",
            "tags": ["有限空间", "安全作业", "操作规程"],
            "author": "系统管理员"
        },
        {
            "title": "COD测定方法及注意事项",
            "summary": "详细介绍化学需氧量(COD)的测定原理、操作步骤、试剂配制和质量控制要求，帮助化验人员准确开展水质检测工作。",
            "content": """
## 一、方法原理

在强酸性溶液中，用一定量的重铬酸钾氧化水样中还原性物质，过量的重铬酸钾以试亚铁灵作指示剂，用硫酸亚铁铵溶液回滴。根据硫酸亚铁铵的用量计算水样中还原性物质消耗氧的量。

## 二、试剂与仪器

### 主要试剂
1. 重铬酸钾标准溶液（1/6 K₂Cr₂O₇ = 0.2500 mol/L）
2. 试亚铁灵指示剂
3. 硫酸亚铁铵标准溶液
4. 硫酸-硫酸银溶液
5. 硫酸汞（结晶或粉末）
6. 邻苯二甲酸氢钾标准溶液

### 主要仪器
1. COD消解装置或回流装置
2. 酸式滴定管（50mL）
3. 锥形瓶（500mL）
4. 移液管
5. 分析天平
6. 加热装置

## 三、操作步骤

### 1. 水样采集与保存
- 采集具有代表性的水样
- 如不能及时测定，应加硫酸至pH < 2，4℃以下冷藏
- 最长保存时间不超过7天

### 2. 样品预处理
- 水样浑浊时应摇匀后取样
- 对于高氯废水，需加入硫酸汞掩蔽氯离子
- 氯离子含量超过1000mg/L时需稀释后测定

### 3. 加热消解

**步骤：**
1. 取20.00mL混匀水样于锥形瓶中
2. 加入0.4g硫酸汞，摇匀
3. 准确加入10.00mL重铬酸钾标准溶液
4. 加入数粒玻璃珠，摇匀
5. 连接回流装置，从冷凝管上端缓慢加入30mL硫酸-硫酸银溶液
6. 轻轻摇动锥形瓶使溶液混匀
7. 加热回流2小时（自开始沸腾计时）

### 4. 滴定

**步骤：**
1. 冷却后，用90mL水从冷凝管上端冲洗
2. 取下锥形瓶，冷却至室温
3. 加入3滴试亚铁灵指示剂
4. 用硫酸亚铁铵标准溶液滴定
5. 溶液由黄色经蓝绿色变为红褐色即为终点
6. 记录硫酸亚铁铵标准溶液的用量

### 5. 空白试验
用20.00mL蒸馏水代替水样，按相同步骤进行测定。

## 四、结果计算

COD(mg/L) = (V₀ - V₁) × C × 8 × 1000 / V

式中：
- V₀：空白消耗硫酸亚铁铵体积，mL
- V₁：水样消耗硫酸亚铁铵体积，mL
- C：硫酸亚铁铵标准溶液浓度，mol/L
- 8：1/2氧的摩尔质量，g/mol
- V：水样体积，mL

## 五、质量控制

1. **空白值控制**：每批样品做2个空白，空白值应稳定
2. **平行样测定**：每10个样品做1个平行样，相对偏差≤10%
3. **加标回收**：定期做加标回收试验，回收率应在90%~110%
4. **标准样核查**：每批样品带一个标准样品，结果应在允许范围内

## 六、注意事项

1. **安全防护**
   - 操作时佩戴防护眼镜、手套和白大褂
   - 浓硫酸操作要小心，防止溅出
   - 消解时注意防止爆沸

2. **试剂质量**
   - 重铬酸钾需在105℃烘干2小时
   - 硫酸亚铁铵溶液需每日标定
   - 试亚铁灵指示剂应避光保存

3. **操作要点**
   - 水样取样要均匀有代表性
   - 加热回流时间要准确
   - 滴定终点判断要准确
   - 冷凝水要保持通畅，防止挥发损失

4. **干扰消除**
   - 氯离子干扰用硫酸汞掩蔽
   - 亚硝酸盐干扰可加入氨基磺酸
   - 亚铁离子干扰可在酸性条件下曝气去除

## 七、废液处理

COD测定废液含有重金属和强酸，应统一收集，交由有资质的单位处理，不得直接排放。
            """,
            "category_code": "LAB",
            "tags": ["COD", "化验检测", "水质分析"],
            "author": "系统管理员"
        },
        {
            "title": "鼓风机日常巡检与维护要点",
            "summary": "介绍污水处理厂鼓风机的日常巡检内容、维护保养周期和常见问题处理，确保曝气系统稳定可靠运行。",
            "content": """
## 一、设备概述

鼓风机是污水处理厂曝气系统的核心设备，其运行状态直接影响生化处理效果。常见类型有罗茨鼓风机、离心鼓风机和磁悬浮鼓风机。

## 二、日常巡检内容

### 每日巡检（运行中检查）

**1. 运行参数监测**
- 电流/功率：与额定值对比，不应超过额定值
- 风压/风量：在正常范围内波动
- 进风温度：一般不超过40℃
- 出风温度：一般不超过80~100℃
- 润滑油温度：不超过65℃
- 振动值：符合设备技术要求

**2. 外观与声音检查**
- 设备有无异常振动或异响
- 各连接部位有无松动
- 有无泄漏（油、气）
- 皮带张力是否合适（皮带传动型）

**3. 辅助系统检查**
- 冷却水系统运行正常
- 润滑油油位在正常范围
- 空气过滤器压差正常
- 消音器、隔声罩完好

### 每周巡检

1. 清洁设备及周边卫生
2. 检查并紧固各连接螺栓
3. 检查皮带张紧度及磨损情况
4. 检查安全阀及放空阀动作是否正常
5. 检查仪表显示是否准确

## 三、定期维护保养

### 月度保养

1. **空气过滤器**
   - 检查滤芯清洁情况
   - 必要时清洗或更换滤芯
   - 检查过滤器密封

2. **润滑系统**
   - 检查油位，不足时补充
   - 检查油质，观察是否变质
   - 检查有无泄漏

3. **传动系统**
   - 检查联轴器/皮带状态
   - 润滑轴承（脂润滑型）
   - 检查各转动部位灵活性

### 季度保养

1. 更换润滑油（首次运行500小时后更换，以后每2000小时或3个月更换）
2. 检查皮带磨损情况，必要时更换
3. 检查并清洁冷却器
4. 检查电气接线及接地
5. 校验压力表、温度计等仪表

### 年度大修

1. **主机部分**
   - 拆卸检查叶轮、轴承、齿轮等
   - 测量各部件间隙
   - 更换磨损的密封件
   - 叶轮做动平衡校验

2. **电机部分**
   - 电机绝缘检测
   - 轴承检查及润滑
   - 清洁电机内部

3. **控制系统**
   - 检查PLC程序及参数
   - 检查传感器及执行器
   - 校验保护定值

## 四、常见故障与处理

| 故障现象 | 可能原因 | 处理方法 |
|---------|---------|---------|
| 风量不足 | 过滤器堵塞<br>转速降低<br>管道泄漏<br>叶轮磨损 | 清洗或更换滤芯<br>检查电机及电源<br>检查并修复漏点<br>更换或修复叶轮 |
| 风压过高 | 曝气系统阻力增大<br>出气管道堵塞<br>压力表故障 | 检查曝气头及管路<br>疏通管道<br>检修或更换压力表 |
| 异常噪音 | 轴承损坏<br>齿轮磨损<br>叶轮碰壳<br>地脚螺栓松动 | 更换轴承<br>更换齿轮<br>调整叶轮间隙<br>紧固螺栓 |
| 温度过高 | 润滑不良<br>冷却不足<br>负荷过大<br>环境温度高 | 检查更换润滑油<br>检查冷却系统<br>降低运行负荷<br>改善通风条件 |
| 振动过大 | 叶轮不平衡<br>轴承损坏<br>基础松动<br>联轴器不对中 | 叶轮做动平衡<br>更换轴承<br>紧固基础<br>校正联轴器 |

## 五、安全注意事项

1. **运行中禁止**
   - 拆除安全防护罩
   - 触摸转动部件
   - 打开检修门
   - 调整安全阀压力

2. **停机检修**
   - 必须断电并挂牌
   - 泄压后再拆卸
   - 做好设备隔离措施
   - 配备专人监护

3. **启动前检查**
   - 确认各阀门开关状态
   - 盘车检查有无卡阻
   - 检查油位和冷却系统
   - 确认无人在设备附近

## 六、记录与档案

1. 每日运行记录：电流、风压、风量、温度、振动
2. 维护保养记录：保养内容、更换备件、保养人员
3. 故障维修记录：故障现象、原因分析、处理措施
4. 设备台账：设备编号、型号、投运时间、大修记录
            """,
            "category_code": "EQUIPMENT",
            "tags": ["鼓风机", "设备巡检", "维护保养"],
            "author": "系统管理员"
        },
        {
            "title": "生物池硝化反应异常处理",
            "summary": "分析生物池硝化效果下降的常见原因，提供系统性的排查思路和处理措施，保障出水氨氮达标排放。",
            "content": """
## 一、现象说明

硝化反应异常表现为：
- 出水氨氮浓度升高
- 硝化速率下降
- 亚硝酸盐积累
- 总氮去除率下降

## 二、影响因素分析

### 1. 温度影响
- 硝化菌适宜温度：20~30℃
- 温度低于15℃时硝化速率明显下降
- 温度低于5℃时硝化作用几乎停止

### 2. pH值影响
- 最佳pH范围：7.5~8.5
- pH < 6.5时硝化菌活性受抑制
- pH < 6.0时硝化反应基本停止

### 3. 溶解氧(DO)影响
- 硝化需氧量：约4.57g O₂/g NH₃-N
- 建议DO浓度：2~4mg/L
- DO < 0.5mg/L时硝化严重受抑制

### 4. 有毒物质影响
- 重金属：镉、铬、铜、镍等
- 有机物：酚类、氰化物、醛类等
- 高浓度盐类

### 5. 污泥龄影响
- 硝化菌世代时间长
- 需保证足够的污泥龄
- 一般冬季污泥龄应大于10~15天

## 三、排查步骤

### 第一步：核实数据
1. 确认氨氮检测数据准确
2. 对比进水氨氮浓度变化
3. 检查历史数据趋势

### 第二步：工艺参数检查
1. **DO检查**
   - 各段DO分布是否正常
   - 曝气强度是否足够
   - 曝气均匀性

2. **pH与碱度检查**
   - 进出水pH值
   - 系统碱度是否足够
   - 是否需要补充碱度

3. **污泥检查**
   - MLSS、MLVSS浓度
   - 污泥沉降性能
   - 污泥龄计算
   - 镜检微生物相

4. **负荷检查**
   - 进水氨氮负荷
   - 容积负荷
   - 污泥负荷

### 第三步：进水水质排查
1. 排查进水工业废水
2. 检测有毒有害物质
3. 核实水量水质变化

## 四、处理措施

### 1. 温度降低导致
- 适当提高MLSS浓度
- 延长污泥龄
- 增加曝气，提高DO浓度
- 条件允许时可考虑进水加热

### 2. pH偏低导致
- 投加碱度（如碳酸氢钠、石灰）
- 调整pH至7.5~8.0
- 检查进水酸性废水来源

### 3. DO不足导致
- 增加曝气强度
- 提高好氧段DO至3~4mg/L
- 检查曝气系统是否堵塞
- 优化曝气配置

### 4. 毒性冲击导致
- 降低或切断有毒废水
- 加大回流水量稀释
- 增加污泥浓度
- 投加粉末活性炭吸附
- 必要时可投加外来污泥接种

### 5. 污泥龄不足导致
- 减少剩余污泥排放量
- 延长污泥龄
- 提高MLSS浓度

## 五、恢复策略

1. **短期应急**
   - 加大曝气，提高DO
   - 投加碱度调节pH
   - 降低处理负荷

2. **中期调整**
   - 逐步恢复污泥浓度
   - 优化工艺参数
   - 培养硝化菌群

3. **长期预防**
   - 建立水质预警机制
   - 加强源头管控
   - 制定应急预案
   - 保留应急菌种

## 六、预防措施

1. 定期分析硝化效果，建立趋势曲线
2. 加强进水水质监控，特别是工业废水
3. 保持运行参数稳定，避免大幅波动
4. 储备应急物资（碱、碳源、菌种等）
5. 定期开展应急演练
            """,
            "category_code": "PROCESS",
            "tags": ["硝化反应", "氨氮", "生物处理", "工艺调控"],
            "author": "系统管理员"
        },
    ]

    for article_data in sample_articles:
        category = db.query(KnowledgeCategory).filter(KnowledgeCategory.code == article_data["category_code"]).first()
        if category:
            existing_article = db.query(KnowledgeArticle).filter(KnowledgeArticle.title == article_data["title"]).first()
            if not existing_article:
                import json as json_lib
                article = KnowledgeArticle(
                    title=article_data["title"],
                    summary=article_data["summary"],
                    content=article_data["content"].strip(),
                    category_id=category.id,
                    tags=json_lib.dumps(article_data["tags"], ensure_ascii=False),
                    author_name=article_data["author"],
                    view_count=0,
                    helpful_count=0,
                    unhelpful_count=0,
                    status="published"
                )
                db.add(article)

    db.commit()
