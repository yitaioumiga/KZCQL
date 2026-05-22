# KZCQL 编排指南改造计划

> **版本**: v1.0 | **日期**: 2026-05-22
> **目标**: 解决"主Agent决策负担过重"和"子Agent输入不明确"问题
> **范围**: 主Agent编排指南 + 子Agent规范输入定义

---

## 一、问题诊断

### 1.1 当前痛点

| 痛点 | 具体表现 | 影响 |
|------|----------|------|
| **主Agent决策负担** | 每次调用子Agent时，需要决定：读取哪些文件、传递什么内容、如何处理返回 | 易遗漏关键文件，调用质量不稳定 |
| **子Agent输入模糊** | 编排指南只说"构造A1输入包"，但没有具体定义输入包的内容和格式 | 子Agent执行不一致，输出质量波动 |
| **错误处理缺失** | 当子Agent失败或输出不符时，主Agent不知道应该查看哪个文件来解决 | 问题排查困难，修复周期长 |
| **规范与执行脱节** | 规则文件定义了要求，但没有明确映射到Agent的执行步骤 | 规则悬空，执行无保障 |

### 1.2 核心矛盾

```
用户期望                          当前现实
─────────────────────────────────────────────────────────
编排指南告诉主Agent：             编排指南只说：
"调用A1时，必须读取以下文件..."    "构造A1输入包，调用A1"
"传递以下内容给子Agent..."         "执行九维度审查"
"如果失败，查看这个文件..."        "验证输出"
"这个步骤可选，那个必须..."        "按流程执行"
```

---

## 二、开源方案研究总结

### 2.1 研究范围

| 项目 | Stars | 核心特点 | 可借鉴点 |
|------|-------|----------|----------|
| **LangGraph** | 11k+ | 图结构状态机、Node/Edge/Condition、持久化状态 | 输入输出Schema定义、状态流转图 |
| **AutoGen (Microsoft)** | 37k+ | 对话式多Agent、AgentTool、GroupChat | Agent能力描述模板、工具调用规范 |
| **CrewAI** | 25k+ | 角色化团队、Task/Agent/Crew三层 | 任务输入模板、角色职责定义 |
| **LlamaIndex Workflows** | 8k+ | 事件驱动、@step装饰器、上下文传递 | 步骤输入输出类型检查 |
| **Agent-Squad** | 3k+ | Classifier-based路由、SupervisorAgent | 输入包分类、路由决策树 |

### 2.2 关键发现

#### 发现1: 输入Schema是行业标准

所有主流框架都明确定义Agent的输入Schema：

```python
# LangGraph 风格
class AgentInput(TypedDict):
    messages: List[BaseMessage]
    context: Dict[str, Any]
    files: List[FileReference]

# CrewAI 风格
class TaskInput(BaseModel):
    description: str
    expected_output: str
    context: Dict[str, Any]
    tools: List[Tool]
```

**启示**: KZCQL需要为每个子Agent定义明确的输入模板。

#### 发现2: 状态机模式解决编排复杂性

LangGraph使用StateGraph管理复杂流程：

```python
# 状态定义
class WorkflowState(TypedDict):
    current_step: str
    inputs: Dict[str, AgentInput]
    outputs: Dict[str, AgentOutput]
    errors: List[ErrorRecord]

# 节点定义
def agent_node(state: WorkflowState) -> WorkflowState:
    agent_input = construct_input(state)
    result = call_agent(agent_input)
    return update_state(state, result)
```

**启示**: KZCQL可以用"输入包构造函数"替代复杂的运行时状态机。

#### 发现3: 错误处理必须内嵌在流程中

AutoGen的阻断机制：

```python
class AutoGenOrchestrator:
    def handle_failure(self, agent: str, error: Exception):
        if agent in MANDATORY_AGENTS:
            raise BlockingError(f"强制Agent {agent} 失败，必须修复")
        else:
            decision = self.ask_user(f"{agent} 失败，是否跳过？")
            return decision
```

**启示**: 编排指南需要包含"错误处理决策树"。

---

## 三、改造方案设计

### 3.1 设计原则

| 原则 | 说明 | 避免 |
|------|------|------|
| **轻量级** | 不引入运行时依赖，仅增强规范文档 | 不创建新的Python运行时 |
| **声明式** | 用模板描述"应该做什么"，而非"怎么做" | 不写执行代码，只写规范 |
| **可验证** | 每个输入项都有明确的验证标准 | 模糊的"根据需要"描述 |
| **渐进式** | 从高频Agent开始，逐步覆盖全部 | 一次性改造所有文件 |

### 3.2 核心概念：输入包模板 (Input Package Template)

```yaml
# 输入包模板结构
agent: "A1-主"                    # Agent代号
trigger: "架构评估触发"           # 触发条件

input_package:                    # 输入包定义
  required_files:                 # [MUST] 必须读取的文件
    - path: "/workspace/KZCQL/00_架构文档/"
      description: "所有架构文档"
      validation: "目录存在且非空"
    - path: "/workspace/KZCQL/02_子Agent规范/"
      description: "所有子Agent规范"
      validation: "目录存在且非空"
  
  optional_files:                 # [SHOULD] 建议读取的文件
    - path: "/workspace/KZCQL/04_工作区/架构归档/"
      description: "上次审查报告"
      validation: "如有则读取"
      default: "跳过"
  
  context_data:                   # 上下文数据
    trigger_reason:               # 触发原因
      source: "user_input"        # 来源：用户输入/系统自动
      format: "字符串描述"
    review_scope:                 # 审查范围
      options: ["全面审查", "针对性审查"]
      default: "全面审查"
  
  validation_rules:               # 输入验证规则
    pre_call:                     # 调用前验证
      - "所有required_files存在"
      - "trigger_reason已明确"
    post_call:                    # 调用后验证
      - "输出包含九维度评分"
      - "输出包含P0/P1/P2建议"

error_handling:                   # 错误处理
  file_not_found:                 # 文件不存在
    fallback: "使用默认路径"
    reference_doc: "00_架构文档/文件路径规范.md"
  agent_timeout:                  # Agent超时
    fallback: "重试3次后询问用户"
    reference_doc: "00_架构文档/错误处理指南.md"
  output_invalid:                 # 输出格式不符
    fallback: "要求子Agent重新生成"
    validation_doc: "02_子Agent规范/架构专家组/架构审查报告模板.md"
```

### 3.3 改造内容清单

#### 阶段1: 高频Agent输入包模板（优先级P0）

| Agent | 当前问题 | 改造内容 | 工作量 |
|-------|----------|----------|--------|
| **W1** | 输入定义模糊 | 创建W1输入包模板，明确：用户档案、主题、角度、风格偏好 | 2h |
| **R1** | 输入文件不明确 | 创建R1输入包模板，明确：待审稿件路径、一票否决项清单、事实核查要点 | 2h |
| **R2** | 评分维度输入不完整 | 创建R2输入包模板，明确：评分体系文件、九维度检查清单、配图质量检查流程 | 2h |
| **R4** | 路由决策输入缺失 | 创建R4输入包模板，明确：R1/R2评分、路由规则文件、历史迭代数据 | 1.5h |
| **A1-主** | 输入范围不清晰 | 创建A1输入包模板，明确：架构文档清单、子Agent规范清单、规则文件清单 | 2h |

#### 阶段2: 并行Agent组输入包模板（优先级P1）

| Agent组 | 改造内容 | 工作量 |
|---------|----------|--------|
| **D5-1/2/3/4** | 创建统一的D5输入包基础模板 + 各子Agent差异化字段 | 3h |
| **D2/D3** | 创建调研Agent输入包模板，明确：信息地图格式、角度选项格式 | 2h |

#### 阶段3: 编排指南增强（优先级P1）

| 章节 | 改造内容 | 工作量 |
|------|----------|--------|
| **§1.1b Orchestrator使用规范** | 增加输入包构造示例、验证检查清单 | 2h |
| **§2 任务类型判定** | 增加各任务类型的输入包选择决策树 | 2h |
| **§4 状态管理** | 增加输入包状态追踪字段 | 1h |
| **§5 检查执行验证** | 增加输入包验证失败的处理流程 | 1h |

#### 阶段4: 错误处理指南（优先级P2）

| 内容 | 说明 | 工作量 |
|------|------|--------|
| **错误类型分类** | 文件不存在、Agent超时、输出无效、验证失败 | 1h |
| **处理决策树** | 每种错误类型的处理流程图 | 2h |
| **参考文档映射** | 每种错误应该查看的文档清单 | 1h |

---

## 四、具体实施计划

### 4.1 文件创建清单

```
/workspace/KZCQL/00_架构文档/
├── 输入包模板/                          # 新增目录
│   ├── W1_初稿撰写_输入包模板.md         # 新增
│   ├── R1_事实核查_输入包模板.md         # 新增
│   ├── R2_全量评审_输入包模板.md         # 新增
│   ├── R4_评级判定_输入包模板.md         # 新增
│   ├── A1-主_架构审查_输入包模板.md      # 新增
│   ├── D5_基础输入包模板.md              # 新增
│   ├── D5-1_规则执行映射_输入包模板.md   # 新增
│   ├── D5-2_执行验证映射_输入包模板.md   # 新增
│   ├── D5-3_悬空规则检测_输入包模板.md   # 新增
│   ├── D5-4_盲评风险检测_输入包模板.md   # 新增
│   └── 输入包模板使用指南.md             # 新增
├── 错误处理指南.md                       # 新增
└── 主Agent编排指南.md                    # 修改（增加输入包引用）
```

### 4.2 实施步骤

#### Step 1: 创建输入包模板基础设施（Day 1）

1. 创建 `/workspace/KZCQL/00_架构文档/输入包模板/` 目录
2. 创建 `输入包模板使用指南.md`，定义：
   - 输入包模板语法规范（YAML frontmatter + Markdown）
   - [MUST]/[SHOULD]/[MAY] 标记语义
   - 验证规则编写规范
3. 创建第一个完整示例：`W1_初稿撰写_输入包模板.md`

#### Step 2: 高频Agent输入包模板（Day 2-3）

按优先级创建：
- R1_事实核查_输入包模板.md
- R2_全量评审_输入包模板.md
- R4_评级判定_输入包模板.md
- A1-主_架构审查_输入包模板.md

#### Step 3: D5并行组输入包模板（Day 4）

创建D5基础模板 + 4个子Agent差异化模板

#### Step 4: 编排指南更新（Day 5）

修改 `主Agent编排指南.md`：
- 在§1.1b中增加"输入包构造"小节
- 在各Agent调用步骤中引用对应的输入包模板
- 增加"输入验证检查清单"

#### Step 5: 错误处理指南（Day 6）

创建 `错误处理指南.md`：
- 错误类型分类表
- 处理决策树
- 参考文档映射表

#### Step 6: 验证与测试（Day 7）

1. 使用A1架构审查验证新规范的完整性
2. 选择一篇文章，按新规范执行完整流程
3. 记录问题并修复

---

## 五、关键设计决策

### 5.1 为什么不用JSON Schema？

| 方案 | 优点 | 缺点 | 决策 |
|------|------|------|------|
| **JSON Schema** | 机器可验证、类型安全 | 对人类不友好、SOLO环境不支持运行时验证 | ❌ 不采用 |
| **YAML模板** | 人类可读、易于维护、可直接嵌入Markdown | 无自动验证 | ✅ 采用 |
| **Python TypedDict** | 类型安全、IDE支持 | 需要运行时环境、增加复杂度 | ❌ 不采用 |

**结论**: 使用YAML frontmatter + Markdown的混合格式，平衡可读性和结构化。

### 5.2 为什么不创建运行时编排器？

| 方案 | 优点 | 缺点 | 决策 |
|------|------|------|------|
| **运行时编排器** | 强制执行、自动验证 | 增加系统复杂度、需要维护代码 | ❌ 不采用 |
| **规范增强** | 轻量级、易于理解、不增加运行时依赖 | 依赖主Agent自觉遵守 | ✅ 采用 |

**结论**: 采用"规范即代码"思路，通过清晰的模板和检查清单降低主Agent决策负担，而非增加运行时约束。

### 5.3 如何处理可选vs强制内容？

使用明确的标记语法：

```yaml
input_package:
  required_files:              # [MUST] 强制
    - path: "..."
      
  optional_files:              # [SHOULD] 建议
    - path: "..."
      
  conditional_files:           # [MAY] 可选（条件触发）
    - path: "..."
      condition: "当xxx时"
```

---

## 六、预期效果

### 6.1 主Agent决策负担减轻

| 改造前 | 改造后 |
|--------|--------|
| "调用R2，我需要传递什么？" | "查看R2输入包模板，按清单准备文件" |
| "R2需要哪些输入文件？" | "required_files列表已明确列出" |
| "R2输出格式不符怎么办？" | "查看error_handling.output_invalid处理流程" |

### 6.2 子Agent执行一致性提升

| 维度 | 改造前 | 改造后 |
|------|--------|--------|
| 输入完整性 | 依赖主Agent经验 | 模板强制要求 |
| 验证标准 | 口头描述 | 明确的validation_rules |
| 错误处理 | 临时决定 | 预定义的处理流程 |

### 6.3 系统可维护性提升

- 新增Agent时，只需创建对应的输入包模板
- 修改输入要求时，只需更新模板文件
- 排查问题时，参考错误处理指南的决策树

---

## 七、风险与缓解

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 模板过于复杂，主Agent不愿使用 | 中 | 高 | 保持模板简洁，提供使用示例 |
| 模板与实际执行脱节 | 中 | 高 | 每次规范修改同步更新模板 |
| 模板覆盖不全 | 低 | 中 | 从高频Agent开始，逐步完善 |
| 主Agent跳过模板直接使用 | 中 | 高 | 在编排指南中强制引用模板 |

---

## 八、附录

### 8.1 输入包模板示例（W1）

```yaml
---
agent: "W1"
name: "初稿撰写Agent输入包模板"
version: "1.0"
trigger: "阶段一写作任务"
---

## 输入包定义

### [MUST] 必须输入

| 字段 | 来源 | 格式 | 验证 |
|------|------|------|------|
| user_profile | 01_共享知识库/作者事实档案.md | Markdown | 文件存在 |
| topic | 用户输入 | 字符串 | 非空 |
| writing_rules | 01_共享知识库/前置撰写规则/ | 目录 | 目录存在 |

### [SHOULD] 建议输入

| 字段 | 来源 | 格式 | 默认值 |
|------|------|------|--------|
| angle | D3角度挖掘输出 | 角度选项JSON | 如未执行D3，使用默认角度 |
| research_data | D2调研输出 | 信息地图 | 如未执行D2，跳过 |

### [MAY] 可选输入

| 字段 | 来源 | 条件 |
|------|------|------|
| reference_articles | 04_工作区/产出归档/ | 当用户要求参考历史文章时 |

## 错误处理

### 文件不存在

- **user_profile不存在**: 使用默认作者档案（卡兹克）
- **writing_rules不存在**: 终止任务，报告错误

### 输出验证失败

- **缺少必备章节**: 要求W1补充
- **配图数量不足**: 返回W1重新生成

## 参考文档

- W1 Agent规范: 02_子Agent规范/写作组/初稿撰写Agent.md
- 前置撰写规则: 01_共享知识库/前置撰写规则/前置撰写规则.md
```

### 8.2 改造后编排流程对比

#### 改造前

```markdown
Step 3: 构造A1输入包
    ├── 架构文档路径列表
    ├── 子Agent规范路径列表
    ├── 规则文件路径列表
    ├── 上次审查报告（如有）
    └── 触发原因和审查范围
```

#### 改造后

```markdown
Step 3: 构造A1输入包
    └── 参考: 输入包模板/A1-主_架构审查_输入包模板.md
        ├── [MUST] 读取 00_架构文档/ 所有.md文件
        ├── [MUST] 读取 02_子Agent规范/ 所有.md文件
        ├── [MUST] 读取 01_共享知识库/ 所有规则文件
        ├── [SHOULD] 读取 04_工作区/架构归档/ 上次报告（如有）
        └── [MUST] 确认触发原因（用户输入）
    
    验证检查清单:
    - [ ] 所有required_files已读取
    - [ ] trigger_reason已明确
    - [ ] 输入包格式符合模板要求
```

---

## 九、下一步行动

1. **立即执行**: 创建 `/workspace/KZCQL/00_架构文档/输入包模板/` 目录
2. **本周完成**: W1、R1、R2输入包模板
3. **下周完成**: R4、A1-主、D5组输入包模板
4. **持续优化**: 根据实际使用情况迭代模板

---

*本计划基于对LangGraph、AutoGen、CrewAI等开源框架的深入研究，结合KZCQL实际架构设计而成。*
