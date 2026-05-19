# Orchestrator 编排器规范

> **代号**: Orchestrator  
> **全名**: 主智能体编排器  
> **版本**: v1.0  
> **最后更新**: 2026-05-19  
> **关联文件**: [智能体注册表](../../00_架构文档/智能体注册表与路由规则.md) | [主Agent编排指南](../../00_架构文档/主Agent编排指南.md)

---

## 一、角色定位

**编排指挥官**，强制主智能体按照规范正确调用子智能体，禁止跳过任何步骤。

### 1.1 核心职责

| 职责 | 说明 |
|------|------|
| **强制顺序** | 必须按照AGENT_SEQUENCE顺序调用Agent |
| **禁止跳过** | MANDATORY_AGENTS中的Agent绝对禁止跳过 |
| **显式决策** | OPTIONAL_AGENTS必须显式决策（启用/跳过） |
| **记录完整** | 每个调用必须有记录，禁止"隐形"调用 |
| **异常阻断** | 失败时必须进入阻断流程，禁止自动继续 |

### 1.2 与主Agent的关系

```
用户任务
    ↓
主Agent（理解任务、决策）
    ↓
Orchestrator（编排执行）
    ↓
子智能体（W1/R1/R2等）
    ↓
返回结果
```

**主Agent职责**：理解用户意图、做出高层决策、调用Orchestrator
**Orchestrator职责**：执行编排逻辑、验证调用顺序、记录调用日志

---

## 二、输入输出

### 2.1 输入格式

```python
{
    "task_id": "任务唯一标识",
    "topic": "任务主题",
    "execution_plan": {
        "agents": ["W1", "R1", "R2", "R4"],
        "optional_decisions": {
            "D2": "skip",
            "D3": "enable"
        }
    }
}
```

### 2.2 输出格式

**Agent调用记录**（agent_call_records.json）：
```json
{
    "task_id": "任务ID",
    "call_records": [
        {
            "agent_name": "W1",
            "call_time": "2026-05-19 10:00:00",
            "status": "success",
            "output_path": ".../W1_输出.md"
        }
    ]
}
```

**执行日志**（orchestrator.log）：
```
[2026-05-19 10:00:00] [INFO] 调用W1
[2026-05-19 10:05:00] [INFO] W1执行成功
```

---

## 三、编排逻辑

### 3.1 Agent调用顺序

```python
AGENT_SEQUENCE = [
    "D2",           # 调研Agent（可选）
    "D3",           # 角度挖掘Agent（可选）
    "W1",           # 初稿撰写Agent（强制）
    "ImageCheck",   # 配图检查（可选）
    "R1",           # 事实核查（强制）
    "R2",           # 全量评审（强制）
    "R3",           # 差异评审（可选）
    "R4",           # 评级判定（强制）
    "D1",           # 配图设计（可选）
]
```

### 3.2 强制Agent列表

```python
MANDATORY_AGENTS = ["W1", "R1", "R2", "R4"]
```

**禁止跳过**，必须调用。

### 3.3 可选Agent列表

```python
OPTIONAL_AGENTS = ["D2", "D3", "ImageCheck", "R3", "D1"]
```

**必须显式决策**，不能自动启用或跳过。

---

## 四、核心方法

### 4.1 validate_sequence(agent_name)

验证调用顺序是否正确。

**输入**: agent_name（Agent代号）
**输出**: True/False
**逻辑**:
1. 获取当前步骤期望的Agent
2. 检查传入的agent_name是否匹配
3. 不匹配则记录错误并返回False

### 4.2 check_mandatory(agent_name)

检查是否为强制Agent。

**输入**: agent_name
**输出**: True/False

### 4.3 make_decision(agent_name, context)

对可选Agent进行显式决策。

**输入**: agent_name, context（决策上下文）
**输出**: "enable" / "skip"
**禁止**: 自动决策、默认启用、默认跳过

### 4.4 call_agent(agent_name, input_data, agent_func)

调用子智能体（强约束）。

**流程**:
1. 验证顺序（validate_sequence）
2. 检查是否强制（check_mandatory）
3. 如果是可选，进行显式决策（make_decision）
4. 执行调用（带重试机制）
5. 记录结果
6. 更新步骤

---

## 五、阻断机制

### 5.1 强制Agent失败

**处理流程**:
1. 记录失败
2. 重试（最多3次）
3. 重试失败 → 抛出异常，停止执行
4. **禁止**: 自动跳过或继续

### 5.2 可选Agent失败

**处理流程**:
1. 记录失败
2. 询问用户"是否跳过？"
3. 用户选择"跳过" → 记录跳过，继续下一步
4. 用户选择"重试" → 重新调用
5. **禁止**: 自动决策

---

## 六、使用示例

### 6.1 基础使用

```python
from orchestrator import Orchestrator

# 创建编排器
orch = Orchestrator(
    task_id="写作任务_001",
    topic="AI写作工具对比"
)

# 调用Agent（必须按照顺序）
result = orch.call_agent(
    agent_name="W1",
    input_data={"topic": "AI写作工具对比"},
    agent_func=w1_agent_function
)
```

### 6.2 SOLO环境使用

```python
from orchestrator_solo_adapter import SoloOrchestrator

# 创建SOLO适配编排器
orch = SoloOrchestrator(
    task_id="架构评估_001",
    topic="Phase 0-4架构升级后评估",
    review_type="全面审查"
)

# 生成执行计划
plan = orch.generate_execution_plan()

# 生成SOLO配置
solo_config = orch.generate_solo_task_config()

# SOLO主Agent读取配置并执行
```

### 6.3 不同场景的编排模式

#### 6.3.1 写作流程编排（串行）

```python
# 标准写作流程：W1 → R1 → R2 → R4
WRITING_SEQUENCE = ["W1", "R1", "R2", "R4"]

orch = Orchestrator(task_id="写作任务", topic="主题")

# 逐个串行调用（禁止并行）
for agent in WRITING_SEQUENCE:
    result = orch.call_agent(agent, input_data, agent_func)
    if agent == "R1" and result.status == "FAIL":
        # R1失败时跳过R2，直接进入R4
        continue
```

#### 6.3.2 架构评估编排（混合）

```python
# 架构评估：A1主审（串行）→ D5四个维度（并行）→ A1整合（串行）
ARCHITECTURE_SEQUENCE = {
    "phase1_serial": ["A1-主"],           # 第一阶段：主审
    "phase2_parallel": ["D5-1", "D5-2", "D5-3", "D5-4"],  # 第二阶段：并行
    "phase3_serial": ["A1-整合"]         # 第三阶段：整合
}

orch = Orchestrator(task_id="架构评估", topic="主题")

# Phase 1: 串行
a1_main = orch.call_agent("A1-主", input_data, agent_func)

# Phase 2: 并行（D5维度相互独立）
d5_results = []
for d5_agent in ARCHITECTURE_SEQUENCE["phase2_parallel"]:
    # 使用SOLO Task工具并行调用
    result = parallel_call(d5_agent, a1_main.output)
    d5_results.append(result)

# Phase 3: 串行
a1_final = orch.call_agent("A1-整合", d5_results, agent_func)
```

#### 6.3.3 联合督查编排（并行）

```python
# 联合督查：主Agent和I1必须独立调查（并行）
INSPECTION_SEQUENCE = {
    "parallel": ["主Agent调查", "I1调查"],
    "serial": ["交叉验证"]
}

orch = Orchestrator(task_id="联合督查", topic="主题")

# Step 1: 并行独立调查
main_report = parallel_call("主Agent调查", context)
i1_report = parallel_call("I1调查", context)

# Step 2: 串行交叉验证
cross_validation = orch.call_agent(
    "交叉验证", 
    {"main": main_report, "i1": i1_report}, 
    agent_func
)
```

#### 6.3.4 异常处理编排

```python
# 异常处理流程
EXCEPTION_HANDLING = {
    "mandatory_fail": ["记录", "重试3次", "阻断"],
    "optional_fail": ["记录", "询问用户", "决策"],
    "timeout": ["记录", "通知用户", "保存状态"]
}

orch = Orchestrator(task_id="任务", topic="主题")

try:
    result = orch.call_agent(agent_name, input_data, agent_func)
except OrchestratorError as e:
    if orch.check_mandatory(agent_name):
        # 强制Agent失败：重试3次后阻断
        orch.handle_mandatory_failure(agent_name, e)
    else:
        # 可选Agent失败：询问用户
        orch.handle_optional_failure(agent_name, e)
```

#### 6.3.5 人类反馈后编排

```python
# 人类反馈后的路由决策
HUMAN_FEEDBACK_ROUTING = {
    "满意": ["A1架构审查", "E1规则修改"],
    "要求修改": ["W2迭代", "R3差异评审", "R4评级"],
    "要求重写": ["W1重写", "完整评审链路"]
}

orch = Orchestrator(task_id="规则演进", topic="主题")

# 根据人类反馈选择路由
feedback = get_human_feedback()
if feedback == "满意":
    # 进入规则演进流程
    orch.call_agent("A1", data, agent_func)
    orch.call_agent("E1", a1_output, agent_func)
elif feedback == "要求修改":
    # 进入迭代流程
    for agent in ["W2", "R3", "R4"]:
        orch.call_agent(agent, data, agent_func)
else:
    # 返回阶段一重写
    reset_to_phase1()
```

---

## 七、禁止事项

| 编号 | 禁止事项 | 违规后果 |
|------|----------|----------|
| 1 | 跳过MANDATORY_AGENTS | 抛出OrchestratorError |
| 2 | 自动决策OPTIONAL_AGENTS | 抛出OrchestratorError |
| 3 | 不记录调用 | 无法追溯，审计失败 |
| 4 | 异常时自动继续 | 可能导致质量问题 |
| 5 | 逆序或重复调用Agent | 抛出OrchestratorError |

---

## 八、关联文件

- **可执行代码**: `03_执行代码/主智能体编排/orchestrator.py`
- **SOLO适配**: `03_执行代码/主智能体编排/orchestrator_solo_adapter.py`
- **注册信息**: `00_架构文档/智能体注册表与路由规则.md` 1.14节
- **审核维度**: `02_子Agent规范/架构专家组/A1_D9_脚本与工具审核.md`

---

## 九、版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-05-19 | 初始版本，P30补丁新增 |
