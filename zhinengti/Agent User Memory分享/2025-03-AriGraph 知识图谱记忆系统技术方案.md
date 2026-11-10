> 原文：https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/KeF15lNOtH/-UXFkEkRyR/QddQ6AjU2unXQ4

2025-03-AriGraph 知识图谱记忆系统技术方案

[https://arxiv.org/abs/2407.04363](https://arxiv.org/abs/2407.04363)

# AriGraph 知识图谱记忆系统技术方案
## 1. 核心概念与架构
### 1.1 记忆系统设计理念
AriGraph采用认知科学中的语义记忆（结构化知识）和情景记忆（时序经验）融合设计：

* ∙**语义记忆**：以三元组形式存储的结构化知识，如（"钥匙"，"位于"，"桌子"）
* ∙**情景记忆**：保存完整的时序观察文本，记录发生的具体事件
* ∙**关联机制**：通过情景边将某一时刻的所有语义三元组连接到对应的情景节点

**关键创新点**：情景边作为"超边"，连接同一观察中提取的所有三元组，保留共现关系。

### 1.2 数据结构定义
记忆图谱结构定义为：

```
G = (Vs, Es, Ve, Ee)
```
其中：

* ∙**Vs**：语义顶点集合 - 实体对象
* ∙**Es**：语义边集合 - 实体关系（三元组）
* ∙**Ve**：情景顶点集合 - 完整观察文本
* ∙**Ee**：情景边集合 - 连接情景与语义的关联

具体定义如下：

```
# 记忆图谱结构
G = (Vs, Es, Ve, Ee)

# Vs: 语义顶点集合 - 实体对象
Vs = {"钥匙", "门", "厨房", "桌子", ...}

# Es: 语义边集合 - 实体关系（三元组）
Es = {
    ("钥匙", "位于", "桌子"),
    ("厨房", "连接", "餐厅"),
    ("钥匙", "可以打开", "门")
}

# Ve: 情景顶点集合 - 完整观察文本
Ve = {
    v_e^t = "你在厨房看到一把金色钥匙在桌子上",
    ...
}

# Ee: 情景边集合 - 连接情景与语义的关联
Ee = {
    e_e^t = (v_e^t, {所有从该观察提取的三元组})
}
```
## 2. 记忆存储机制
### 2.1 存储架构
采用双数据库架构实现混合存储：

**图数据库（Neo4j）**：

* ∙存储语义顶点和边的图结构
* ∙存储情景顶点
* ∙维护语义关系和情景关联

**向量数据库（Chroma/Faiss）**：

* ∙存储三元组的向量表示（768维）
* ∙支持快速相似性检索

### 2.2 语义三元组存储示例
**Neo4j节点结构**：

```
// 语义顶点
CREATE (key:Entity {
    name: "金色钥匙",
    entity_type: "object",
    first_seen: timestamp()
})

// 语义边（三元组）
CREATE (key)-[:LOCATED_AT {
    relation: "位于",
    confidence: 0.95,
    last_updated: timestamp()
}]->(table)
```
**向量数据库条目**：

```
{
    "id": "triplet_001",
    "vector": [0.23, -0.45, 0.67, ...],  // 768维
    "metadata": {
        "subject": "金色钥匙",
        "relation": "位于",
        "object": "厨房桌子",
        "triplet_text": "金色钥匙 位于 厨房桌子",
        "timestamp": 1698765432,
        "confidence": 0.92,
        "source_observation_id": "episode_042"
    }
}
```
### 2.3 情景记忆存储示例
**情景顶点结构**：

```
CREATE (ep:EpisodicVertex {
    vertex_id: "episode_042",
    timestamp: 1698765432,
    observation_text: "你在厨房看到一把金色钥匙在桌子上",
    embedding: [0.12, 0.34, ...]  // 文本嵌入
})
```
**情景边（超边）结构**：

```
// 情景边连接该观察的所有三元组
CREATE (ep:EpisodicVertex)-[:CONTAINS_TRIPLETS {
    edge_id: "episodic_edge_042",
    triplet_count: 3,
    triplet_ids: ["triplet_001", "triplet_002", "triplet_003"]
}]->(triplets:TripletGroup)
```
## 3. 记忆检索机制
### 3.1 两阶段检索流程
检索流程分为三个阶段：

```
查询文本 → 向量编码 → [阶段1：语义搜索] → 相关三元组
                              ↓
                    [阶段2：图结构扩展] → 关联实体
                              ↓
                    [阶段3：情景检索] → 历史观察
```
### 3.2 阶段1：基于向量的语义搜索
**实现步骤**：

```
def semantic_search(query_text, top_k=5):
    # 1. 查询向量化
    query_vector = contriever_model.encode(query_text)
    # 输出: [0.23, -0.45, ..., 0.89] (768维)
    
    # 2. 向量相似性搜索（余弦距离）
    results = vector_db.similarity_search(
        query_vector,
        top_k=top_k,
        threshold=0.7  # 相似度阈值
    )
    
    # 3. 返回相关三元组
    return results
```
**具体示例**：

* ∙**查询**："钥匙在哪里"
* ∙**向量化结果**：[0.15, 0.32, -0.21, ...]
* ∙**相似性计算结果**： 1.("金色钥匙", "位于", "厨房桌子") - 相似度: 0.89 2.("钥匙", "打开", "门") - 相似度: 0.82 3.("桌子", "在", "厨房") - 相似度: 0.78

### 3.3 阶段2：图结构扩展搜索
**广度优先遍历算法**：

```
def graph_traversal(initial_entities, max_depth=3):
    """
    从初始实体出发，进行多层图遍历
    """
    visited = set()
    results = set(initial_entities)
    current_level = set(initial_entities)
    
    for depth in range(1, max_depth + 1):
        next_level = set()
        
        for entity in current_level:
            if entity in visited:
                continue
            
            visited.add(entity)
            
            # 查询Neo4j获取邻居节点
            neighbors = neo4j_query(f"""
                MATCH (n:Entity {{name: '{entity}'}})-[r]-(neighbor)
                RETURN neighbor.name, type(r)
            """)
            
            for neighbor, relation in neighbors:
                if neighbor not in visited:
                    next_level.add(neighbor)
                    results.add((entity, relation, neighbor))
        
        current_level = next_level
    
    return results
```
**遍历示例**：

* ∙**初始查询**："如何找到宝藏"
* ∙**初始节点**：["宝藏"]
* ∙**深度1扩展**：宝藏 -[需要]-> 钥匙
* ∙**深度2扩展**：钥匙 -[位于]-> 厨房，钥匙 -[打开]-> 门
* ∙**深度3扩展**：厨房 -[连接]-> 餐厅，门 -[通向]-> 藏宝室
* ∙**最终关联路径**：宝藏 → 需要钥匙 → 钥匙在厨房 → 厨房连接餐厅

### 3.4 阶段3：情景记忆检索
**相关性计算公式**：

```
rel(v_e^i) = (n_i / max(N_i, 1)) × log(max(N_i, 1))
```
其中：

* ∙**n_i**：查询三元组与情景边匹配的数量
* ∙**N_i**：情景边包含的总三元组数
* ∙**log项**：信息量权重因子

**计算示例**：

```
def calculate_episodic_relevance(episode, query_triplets):
    """
    计算情景节点的相关性得分
    """
    # 情景包含的三元组
    episode_triplets = episode.get_triplets()
    N_i = len(episode_triplets)
    
    # 与查询匹配的三元组数量
    n_i = len(set(query_triplets) & set(episode_triplets))
    
    # 计算相关性得分
    if N_i == 0:
        return 0
    
    relevance = (n_i / N_i) * math.log(max(N_i, 1))
    return relevance
```
**实际案例**：

* ∙**查询相关三元组**：("钥匙", "位于", "厨房")，("厨房", "连接", "餐厅")
* ∙**候选情景1**： ∙观察文本："你在厨房看到钥匙和桌子" ∙包含三元组：("钥匙", "位于", "厨房") ✓，("桌子", "在", "厨房") ∙N_i = 2，n_i = 1 ∙relevance = (1/2) × log(2) = 0.5 × 0.69 = 0.35
* ∙**候选情景2**： ∙观察文本："你看到很多房间和物品" ∙包含三元组：50个（大量无关信息） ∙N_i = 50，n_i = 1 ∙relevance = (1/50) × log(50) = 0.02 × 3.91 = 0.08
* ∙**结果**：情景1得分更高，被优先选择

**过滤策略**：

```
def filter_episodic_memories(candidates, threshold=0.3):
    """
    多层次过滤策略
    """
    filtered = []
    
    for episode in candidates:
        score = episode.relevance_score
        
        # 1. 基础阈值过滤
        if score < threshold:
            continue
        
        # 2. 时间衰减调整
        time_decay = calculate_time_decay(episode.timestamp)
        adjusted_score = score * time_decay
        
        # 3. 置信度加权
        confidence_weight = episode.confidence
        final_score = adjusted_score * confidence_weight
        
        if final_score >= threshold:
            filtered.append((episode, final_score))
    
    # 按得分排序，返回top-k
    return sorted(filtered, key=lambda x: x[1], reverse=True)[:k]
```
## 4. 记忆更新机制
### 4.1 增量更新流程
更新流程如下：

```
新观察 → 三元组提取 → 检测冲突 → 过滤过时信息 → 更新图谱 → 添加情景节点
```
### 4.2 三元组提取
**使用LLM提取关系**：

```
def extract_triplets(observation_text):
    """
    从观察文本中提取结构化三元组
    """
    prompt = f"""
从以下观察中提取所有关系三元组：
观察：{observation_text}

请以JSON格式返回：
[
    {{"subject": "实体1", "relation": "关系", "object": "实体2", "confidence": 0.95}},
    ...
]
"""
    
    response = llm.generate(prompt)
    triplets = parse_json(response)
    
    # 实体链接和消歧
    triplets = entity_linking(triplets)
    
    return triplets
```
**提取示例**：

* ∙**观察**："你在厨房看到一把金色钥匙在桌子上"
* ∙
* **提取的三元组**：

```
[
    {"subject": "金色钥匙", "relation": "位于", "object": "桌子", "confidence": 0.95},
    {"subject": "桌子", "relation": "在", "object": "厨房", "confidence": 0.90},
    {"subject": "玩家", "relation": "在", "object": "厨房", "confidence": 0.92}
]
```
### 4.3 冲突检测与过时信息过滤
**检测逻辑**：

```
def detect_and_update_conflicts(new_triplets, graph):
    """
    检测并更新冲突的知识
    """
    for new_triplet in new_triplets:
        subject = new_triplet['subject']
        relation = new_triplet['relation']
        new_object = new_triplet['object']
        
        # 查找现有的相关三元组
        existing_triplets = graph.query(f"""
            MATCH (s:Entity {{name: '{subject}'}})-[r:{relation}]->(o)
            RETURN o.name as object, r.timestamp as timestamp
        """)
        
        for old_triplet in existing_triplets:
            # 检测冲突（同一关系类型指向不同对象）
            if old_triplet['object'] != new_object:
                # 判断是否为可变关系（如位置）
                if is_mutable_relation(relation):
                    # 删除旧边
                    graph.delete_edge(subject, relation, old_triplet['object'])
                    print(f"删除过时信息: ({subject}, {relation}, {old_triplet['object']})")
        
        # 添加新边
        graph.add_edge(new_triplet)
```
**更新示例**：

* ∙**时刻 t=1**： ∙观察："红色储物柜是关闭的" ∙三元组：("红色储物柜", "状态", "关闭")
* ∙**时刻 t=5**： ∙观察："红色储物柜是打开的" ∙新三元组：("红色储物柜", "状态", "打开")
* ∙**更新流程**： 1.检测冲突：发现旧状态"关闭" 2.判断可变性："状态"是可变关系 3.删除旧边：("红色储物柜", "状态", "关闭") 4.添加新边：("红色储物柜", "状态", "打开")

### 4.4 情景节点添加
```
def add_episodic_memory(observation_text, extracted_triplets, graph):
    """
    添加新的情景记忆节点
    """
    # 1. 创建情景顶点
    episode_id = generate_episode_id()
    episode_embedding = encode_text(observation_text)
    
    graph.create_node({
        'id': episode_id,
        'type': 'EpisodicVertex',
        'text': observation_text,
        'embedding': episode_embedding,
        'timestamp': current_timestamp()
    })
    
    # 2. 创建情景边（连接所有相关三元组）
    triplet_ids = [t['id'] for t in extracted_triplets]
    graph.create_episodic_edge(
        episode_id,
        triplet_ids,
        triplet_count=len(triplet_ids)
    )
    
    return episode_id
```
## 5. 实际使用流程
### 5.1 完整的任务执行周期
任务周期如下：

```
环境观察(t) → 更新记忆 → 检索相关知识 → 构建工作记忆 → 生成计划 → 选择动作 → 执行
      ↑                                                                        ↓
      └────────────────────────────环境反馈────────────────────────────────────┘
```
### 5.2 工作记忆组装
**数据结构**：

```
working_memory = {
    # 基础上下文
    "current_observation": "...",
    "goal": "找到宝藏",
    "recent_actions": ["进入厨房", "拾取钥匙"],
    
    # 检索的语义知识
    "semantic_knowledge": [
        "厨房连接餐厅",
        "钥匙可以打开宝箱",
        "宝箱位于藏宝室"
    ],
    
    # 检索的情景经验
    "episodic_memories": [
        "上次在类似房间找到钥匙在抽屉里",
        "宝箱需要特定的金色钥匙"
    ],
    
    # 当前计划
    "plan": [
        "✓ 进入厨房",
        "→ 找到金色钥匙",
        "  寻找藏宝室",
        "  打开宝箱"
    ]
}
```
### 5.3 Prompt组装示例
```
def assemble_prompt(working_memory):
    """
    将工作记忆组装成LLM的输入Prompt
    """
    prompt = f"""
你是一个探索智能体，正在文本冒险游戏中寻找宝藏。

【当前环境】
{working_memory['current_observation']}

【最终目标】
{working_memory['goal']}

【近期动作】
{' → '.join(working_memory['recent_actions'])}

【环境知识】（从记忆图谱检索）
{format_knowledge_list(working_memory['semantic_knowledge'])}

【历史经验】（相关的过往观察）
{format_episodic_list(working_memory['episodic_memories'])}

【当前计划】
{format_plan(working_memory['plan'])}

请基于以上信息：
1. 分析当前情况与目标的关联
2. 评估计划的可行性
3. 决定下一步动作
4. 说明你的推理过程

请按ReAct格式回答：
思考：<你的推理>
动作：<具体动作>
"""
    return prompt
```
**实际组装结果**：

```
你是一个探索智能体，正在文本冒险游戏中寻找宝藏。

【当前环境】
你在厨房看到一把金色钥匙在桌子上。

【最终目标】
找到隐藏的宝藏并安全返回

【近期动作】
开始 → 进入厨房 → 查看桌子

【环境知识】（从记忆图谱检索）
- 厨房通过门连接餐厅
- 金色钥匙可以打开宝箱
- 宝箱通常位于隐蔽位置
- 藏宝室在地下层

【历史经验】（相关的过往观察）
- 上次在类似环境中，钥匙需要用来打开特定的门
- 成功经验：先获取钥匙再寻找宝箱效率更高
- 注意：某些门可能需要特定颜色的钥匙

【当前计划】
1. ✓ 进入厨房
2. → 找到钥匙（进行中）
3. ⏳ 寻找藏宝室
4. ⏳ 打开宝箱

请基于以上信息：
1. 分析当前情况与目标的关联
2. 评估计划的可行性
3. 决定下一步动作
4. 说明你的推理过程

请按ReAct格式回答：
思考：<你的推理>
动作：<具体动作>
```
## 6. 关键技术细节
### 6.1 向量编码的一致性
**重要原则**：查询和存储必须使用同一编码模型

```
# 初始化时统一编码器
encoder = ContrieverModel()  # 或 BGE-M3

# 存储时编码
triplet_text = f"{subject} {relation} {object}"
triplet_vector = encoder.encode(triplet_text)

# 查询时编码（使用同一编码器）
query_vector = encoder.encode(query_text)

# 确保向量空间一致性
similarity = cosine_similarity(query_vector, triplet_vector)
```
### 6.2 图谱索引优化
**Neo4j索引策略**：

```
-- 实体名称索引（加速节点查找）
CREATE INDEX entity_name_idx FOR (n:Entity) ON (n.name);

-- 时间戳索引（支持时序查询）
CREATE INDEX episodic_time_idx FOR (e:EpisodicVertex) ON (e.timestamp);

-- 向量索引（加速相似性搜索）
CREATE VECTOR INDEX episodic_embedding_idx 
FOR (e:EpisodicVertex) 
ON (e.embedding) 
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 768,
        `vector.similarity_function`: 'cosine'
    }
};
```
### 6.3 缓存策略
```
# 多级缓存设计
class MemoryCache:
    def __init__(self):
        self.l1_cache = {}  # 热点查询结果
        self.l2_cache = {}  # 常用子图结构
        
    def get_or_compute(self, query_key, compute_fn):
        # L1缓存命中
        if query_key in self.l1_cache:
            return self.l1_cache[query_key]
        
        # L2缓存命中
        if query_key in self.l2_cache:
            result = self.l2_cache[query_key]
            self.promote_to_l1(query_key, result)
            return result
        
        # 计算并缓存
        result = compute_fn()
        self.l2_cache[query_key] = result
        return result
```
## 7. 与其他方法的对比
### 7.1 vs RAG（检索增强生成）
|特性|AriGraph|传统RAG|
|-|-|-|
|知识表示|结构化图谱 + 情景记忆|非结构化文本块|
|检索方式|语义搜索 + 图遍历|纯向量相似性|
|关联能力|多跳推理，发现间接关系|仅检索直接相似文本|
|动态更新|支持冲突检测和知识更新|简单追加，无更新机制|
|推理能力|强（基于图结构）|弱（依赖LLM理解）|

### 7.2 vs 完整历史记忆
|特性|AriGraph|完整历史|
|-|-|-|
|存储效率|高（结构化压缩）|低（存储所有文本）|
|检索效率|快（索引+图遍历）|慢（线性扫描）|
|信息密度|高（过滤冗余）|低（包含大量噪音）|
|Token消耗|低（仅检索相关）|高（所有历史）|
|扩展性|好（适合长期交互）|差（受上下文窗口限制）|

## 8. 总结
AriGraph通过以下技术创新实现了高效的记忆管理：

1. 1.**混合记忆架构**：语义图谱提供结构化推理基础，情景节点保留详细上下文
2. 2.**情景边设计**：超边连接同时发生的三元组，保留时序共现关系
3. 3.**智能检索**：向量搜索定位相关知识，图遍历扩展关联信息，相关性公式过滤噪音
4. 4.**动态更新**：主动检测和删除过时知识，保持图谱准确性
5. 5.**高效组装**：将检索结果整合到工作记忆，为LLM提供结构化上下文

这种设计使智能体能够在复杂的交互环境中有效学习和推理，显著优于传统的记忆方法。