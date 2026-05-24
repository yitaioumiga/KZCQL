#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KZCQL Orchestrator SOLO Adapter
适配SOLO环境的编排器，将Python编排逻辑与SOLO Task工具集成
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# SOLO环境检测
def is_solo_environment():
    """检测是否在SOLO环境中"""
    return 'SOLO_ENV' in os.environ or os.path.exists('/.solo')

@dataclass
class AgentCallRecord:
    """智能体调用记录"""
    agent_name: str
    call_time: str
    status: str
    output_path: Optional[str] = None
    task_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class OrchestratorConfig:
    """编排器配置"""
    AGENT_SEQUENCE = [
        "A1-主",      # 串行执行D1-D4,D6-D10
        "A1-D5-1",    # 规则→执行映射（并行）
        "A1-D5-2",    # 执行→验证映射（并行）
        "A1-D5-3",    # 悬空规则检测（并行）
        "A1-D5-4",    # 盲评风险检测（并行）
    ]
    
    # D5子Agent权重
    D5_WEIGHTS = {
        "A1-D5-1": 0.30,
        "A1-D5-2": 0.25,
        "A1-D5-3": 0.25,
        "A1-D5-4": 0.20,
    }
    
    MAX_RETRIES = 3
    TIMEOUT_SECONDS = 300

    # 写作创作流程Agent序列
    WRITING_AGENT_SEQUENCE = [
        "D2",         # 调研Agent（长文必须，短文可跳过）
        "D3",         # 角度挖掘Agent（长文必须，短文可跳过）
        "W1",         # 初稿撰写Agent（强制）
        "ImageCheck", # 配图检查
        "R1",         # 事实核查（强制）
        "R2",         # 全量评审（强制）
        "R3",         # 差异评审（如需要）
        "R4",         # 评级判定（强制）
        "D1",         # 配图设计（如需要）
    ]

    # 写作流程强制Agent
    WRITING_MANDATORY_AGENTS = ["W1", "R1", "R2", "R4"]

    # 写作流程可选Agent
    WRITING_OPTIONAL_AGENTS = ["D2", "D3", "ImageCheck", "R3", "D1"]

class SoloOrchestrator:
    """
    SOLO适配的KZCQL编排器
    
    核心功能：
    1. 按照KZCQL规范编排Agent调用
    2. 生成SOLO可执行的Task调用计划
    3. 记录调用日志和结果
    4. 验证调用顺序和完整性
    
    SOLO集成方式：
    - 生成Task调用配置（JSON）
    - SOLO主Agent读取配置并执行Task调用
    - 接收Task返回结果并整合
    """
    
    def __init__(self, task_id: str, topic: str, review_type: str = "全面审查"):
        self.task_id = task_id
        self.topic = topic
        self.review_type = review_type
        self.config = OrchestratorConfig()
        self.call_records: List[AgentCallRecord] = []
        self.current_step = 0
        self.execution_plan: List[Dict] = []
        
        # 创建任务目录
        self.task_dir = f"/workspace/KZCQL/04_工作区/产出归档/{datetime.now().strftime('%Y%m%d')}_{task_id}"
        os.makedirs(self.task_dir, exist_ok=True)
        
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"
        print(log_line)
        
        log_file = f"{self.task_dir}/orchestrator.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")
            
    def generate_execution_plan(self) -> List[Dict]:
        """
        生成执行计划（SOLO可执行）
        
        按照KZCQL架构专家Agent规范：
        Step 1: A1-主（串行D1-D4,D6-D10）
        Step 2: A1-D5-1到A1-D5-4（并行）
        Step 3: 整合评分
        """
        self.log("生成KZCQL架构评估执行计划...")
        
        plan = []
        
        # Step 1: A1-主（串行执行D1-D4,D6-D10）
        plan.append({
            "step": 1,
            "agent": "A1-主",
            "type": "serial",
            "description": "串行执行D1-D4,D6-D10维度审查",
            "input": {
                "review_type": self.review_type,
                "topic": self.topic,
                "dimensions": ["D1", "D2", "D3", "D4", "D6", "D7", "D8", "D9", "D10"]
            },
            "output_format": "A1_主_审查报告.md",
            "timeout": 600,
        })
        
        # Step 2: D5并行拆解（4个子Agent并行）
        d5_agents = ["A1-D5-1", "A1-D5-2", "A1-D5-3", "A1-D5-4"]
        d5_specs = {
            "A1-D5-1": "规则→执行映射",
            "A1-D5-2": "执行→验证映射",
            "A1-D5-3": "悬空规则检测",
            "A1-D5-4": "盲评风险检测",
        }
        
        for agent in d5_agents:
            plan.append({
                "step": 2,
                "agent": agent,
                "type": "parallel",
                "description": f"D5维度：{d5_specs[agent]}",
                "input": {
                    "review_type": self.review_type,
                    "topic": self.topic,
                    "spec_file": f"/workspace/KZCQL/02_子Agent规范/架构专家组/{agent.replace('-', '_')}.md"
                },
                "output_format": f"{agent}_报告.md",
                "timeout": 300,
                "weight": self.config.D5_WEIGHTS[agent],
            })
            
        # Step 3: 整合评分
        plan.append({
            "step": 3,
            "agent": "A1-整合",
            "type": "integration",
            "description": "整合所有子Agent评分，生成最终报告",
            "input": {
                "depends_on": ["A1-主", "A1-D5-1", "A1-D5-2", "A1-D5-3", "A1-D5-4"],
                "d5_weights": self.config.D5_WEIGHTS,
            },
            "output_format": "A1_架构审查报告_最终.md",
            "timeout": 120,
        })
        
        self.execution_plan = plan
        self.log(f"执行计划生成完成：{len(plan)}个步骤")
        
        # 保存执行计划
        plan_file = f"{self.task_dir}/execution_plan.json"
        with open(plan_file, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        self.log(f"执行计划已保存：{plan_file}")
        
        return plan
    
    def validate_plan(self) -> bool:
        """验证执行计划是否符合KZCQL规范"""
        self.log("验证执行计划...")
        
        checks = {
            "A1-主存在": any(p["agent"] == "A1-主" for p in self.execution_plan),
            "D5并行完整": sum(1 for p in self.execution_plan if p["agent"].startswith("A1-D5-")) == 4,
            "权重总和为1": abs(sum(self.config.D5_WEIGHTS.values()) - 1.0) < 0.001,
            "整合步骤存在": any(p["agent"] == "A1-整合" for p in self.execution_plan),
        }
        
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            self.log(f"  {status} {check}")
            
        all_passed = all(checks.values())
        self.log(f"验证结果：{'通过' if all_passed else '失败'}")
        return all_passed
    
    def record_call(self, agent_name: str, status: str, output_path: str = None, task_id: str = None):
        """记录Agent调用"""
        record = AgentCallRecord(
            agent_name=agent_name,
            call_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            status=status,
            output_path=output_path,
            task_id=task_id
        )
        self.call_records.append(record)
        
        # 保存调用记录
        records_file = f"{self.task_dir}/agent_call_records.json"
        with open(records_file, "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in self.call_records], f, ensure_ascii=False, indent=2)
            
    def calculate_d5_score(self, sub_scores: Dict[str, float]) -> float:
        """计算D5维度加权得分"""
        total = 0.0
        for agent, score in sub_scores.items():
            weight = self.config.D5_WEIGHTS.get(agent, 0)
            total += score * weight
        return total
    
    def generate_solo_task_config(self) -> Dict:
        """
        生成SOLO Task调用配置
        
        SOLO主Agent可以读取此配置，使用Task工具执行每个步骤
        """
        config = {
            "orchestrator_version": "1.0",
            "task_id": self.task_id,
            "topic": self.topic,
            "review_type": self.review_type,
            "execution_mode": "solo_compatible",
            "steps": []
        }
        
        for step in self.execution_plan:
            config["steps"].append({
                "step_number": step["step"],
                "agent": step["agent"],
                "type": step["type"],
                "description": step["description"],
                "solo_task": {
                    "subagent_type": "general_purpose_task",
                    "query": f"执行{step['agent']}：{step['description']}",
                    "response_language": "zh",
                    "input_data": step["input"],
                    "expected_output": step["output_format"],
                    "timeout": step["timeout"],
                }
            })
            
        return config
    
    def generate_writing_execution_plan(self, is_long_form: bool = False) -> List[Dict]:
        """
        生成写作创作流程执行计划（SOLO可执行）

        按照KZCQL写作创作流程规范：
        Step 1: D2调研 + D3角度挖掘（长文必须，短文可跳过）
        Step 2: W1初稿撰写（强制）
        Step 3: ImageCheck配图验证
        Step 4: R1事实核查（强制）
        Step 5: R2全量评审（强制）
        Step 6: R3差异评审（如需要）
        Step 7: R4评级判定（强制）
        Step 8: D1配图设计（如需要）

        Args:
            is_long_form: 是否为长文创作（>3000字），影响D2/D3是否强制
        """
        self.log(f"生成KZCQL写作创作流程执行计划（长文={is_long_form}）...")

        plan = []
        step_num = 0

        # Step 1: D2调研（长文必须，短文可跳过）
        step_num += 1
        plan.append({
            "step": step_num,
            "agent": "D2",
            "type": "conditional_mandatory" if is_long_form else "optional",
            "description": "调研Agent：生成跨领域信息地图",
            "mandatory": is_long_form,
            "input": {
                "topic": self.topic,
                "spec_file": "/workspace/KZCQL/02_子Agent规范/调研专家组/D2_调研Agent.md",
                "input_package": "/workspace/KZCQL/00_架构文档/输入包模板/D2_调研_输入包模板.md",
            },
            "output_format": "D2_调研报告.md",
            "timeout": 600,
        })

        # Step 2: D3角度挖掘（长文必须，短文可跳过）
        step_num += 1
        plan.append({
            "step": step_num,
            "agent": "D3",
            "type": "conditional_mandatory" if is_long_form else "optional",
            "description": "角度挖掘Agent：生成3-5个内容角度选项",
            "mandatory": is_long_form,
            "depends_on": ["D2"],
            "input": {
                "topic": self.topic,
                "d2_output": "D2_调研报告.md",
                "spec_file": "/workspace/KZCQL/02_子Agent规范/调研专家组/D3_角度挖掘Agent.md",
                "input_package": "/workspace/KZCQL/00_架构文档/输入包模板/D3_角度挖掘_输入包模板.md",
            },
            "output_format": "D3_角度选项.md",
            "timeout": 300,
        })

        # Step 3: W1初稿撰写（强制）
        step_num += 1
        plan.append({
            "step": step_num,
            "agent": "W1",
            "type": "mandatory",
            "description": "初稿撰写Agent：调用khazix-writer Skill撰写初稿",
            "mandatory": True,
            "depends_on": ["D2", "D3"] if is_long_form else [],
            "input": {
                "topic": self.topic,
                "spec_file": "/workspace/KZCQL/02_子Agent规范/写作组/初稿撰写Agent.md",
                "input_package": "/workspace/KZCQL/00_架构文档/输入包模板/W1_初稿撰写_输入包模板.md",
                "pre_writing_rules": "/workspace/KZCQL/01_共享知识库/前置撰写规则/前置撰写规则.md",
                "author_profile": "/workspace/KZCQL/01_共享知识库/作者事实档案.md",
            },
            "output_format": "初稿_v0.1.md",
            "timeout": 600,
        })

        # Step 4: ImageCheck配图验证
        step_num += 1
        plan.append({
            "step": step_num,
            "agent": "ImageCheck",
            "type": "mandatory",
            "description": "配图验证：确认图片引用数量>=4张，逐张检查质量",
            "mandatory": True,
            "depends_on": ["W1"],
            "input": {
                "article_file": "初稿_v0.1.md",
            },
            "output_format": "ImageCheck_报告.md",
            "timeout": 120,
        })

        # Step 5: R1事实核查（强制）
        step_num += 1
        plan.append({
            "step": step_num,
            "agent": "R1",
            "type": "mandatory",
            "description": "事实核查Agent：19项否决规则检查",
            "mandatory": True,
            "depends_on": ["ImageCheck"],
            "input": {
                "article_file": "初稿_v0.1.md",
                "spec_file": "/workspace/KZCQL/02_子Agent规范/评审专家组/事实核查Agent.md",
                "input_package": "/workspace/KZCQL/00_架构文档/输入包模板/R1_事实核查_输入包模板.md",
            },
            "output_format": "R1_事实核查报告.md",
            "timeout": 300,
        })

        # Step 6: R2全量评审（强制）
        step_num += 1
        plan.append({
            "step": step_num,
            "agent": "R2",
            "type": "mandatory",
            "description": "全量评审Agent：12维度100分制全量评审",
            "mandatory": True,
            "depends_on": ["R1"],
            "input": {
                "article_file": "初稿_v0.1.md",
                "r1_report": "R1_事实核查报告.md",
                "spec_file": "/workspace/KZCQL/02_子Agent规范/评审专家组/全量评审Agent.md",
                "input_package": "/workspace/KZCQL/00_架构文档/输入包模板/R2_全量评审_输入包模板.md",
            },
            "output_format": "R2_全量评审报告.md",
            "timeout": 300,
        })

        # Step 7: R3差异评审（如需要，迭代轮次>=2时启用）
        step_num += 1
        plan.append({
            "step": step_num,
            "agent": "R3",
            "type": "optional",
            "description": "差异评审Agent：对比前后版本差异",
            "mandatory": False,
            "depends_on": ["R2"],
            "input": {
                "article_before": "初稿_v0.1.md",
                "article_after": "初稿_v0.2.md",
                "r1_report": "R1_事实核查报告.md",
                "r2_report": "R2_全量评审报告.md",
                "spec_file": "/workspace/KZCQL/02_子Agent规范/评审专家组/差异评审Agent.md",
                "input_package": "/workspace/KZCQL/00_架构文档/输入包模板/R3_差异评审_输入包模板.md",
            },
            "output_format": "R3_差异评审报告.md",
            "timeout": 300,
        })

        # Step 8: R4评级判定（强制）
        step_num += 1
        plan.append({
            "step": step_num,
            "agent": "R4",
            "type": "mandatory",
            "description": "评级判定Agent：综合评级和路由建议",
            "mandatory": True,
            "depends_on": ["R1", "R2", "R3"],
            "input": {
                "r1_report": "R1_事实核查报告.md",
                "r2_report": "R2_全量评审报告.md",
                "r3_report": "R3_差异评审报告.md",
                "spec_file": "/workspace/KZCQL/02_子Agent规范/评审专家组/评级判定Agent.md",
                "input_package": "/workspace/KZCQL/00_架构文档/输入包模板/R4_评级判定_输入包模板.md",
            },
            "output_format": "R4_评级报告.md",
            "timeout": 120,
        })

        # Step 9: D1配图设计（如需要）
        step_num += 1
        plan.append({
            "step": step_num,
            "agent": "D1",
            "type": "optional",
            "description": "配图设计Agent：生成、质检、嵌入配图",
            "mandatory": False,
            "depends_on": ["R4"],
            "input": {
                "article_file": "初稿_v0.1.md",
                "r2_report": "R2_全量评审报告.md",
                "spec_file": "/workspace/KZCQL/02_子Agent规范/配图设计组/配图设计Agent.md",
                "input_package": "/workspace/KZCQL/00_架构文档/输入包模板/D1_配图设计_输入包模板.md",
                "pre_writing_rules": "/workspace/KZCQL/01_共享知识库/前置撰写规则/前置撰写规则.md",
            },
            "output_format": "D1_配图质检报告.md",
            "timeout": 600,
        })

        self.writing_execution_plan = plan
        self.log(f"写作创作流程执行计划生成完成：{len(plan)}个步骤")

        # 保存执行计划
        plan_file = f"{self.task_dir}/writing_execution_plan.json"
        with open(plan_file, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        self.log(f"写作执行计划已保存：{plan_file}")

        return plan

    def generate_solo_writing_config(self, is_long_form: bool = False) -> Dict:
        """
        生成写作创作流程的SOLO Task调用配置

        SOLO主Agent可以读取此配置，使用Task工具执行写作流程的每个步骤。

        Args:
            is_long_form: 是否为长文创作（>3000字），影响D2/D3是否强制
        """
        # 确保已生成写作执行计划
        if not hasattr(self, 'writing_execution_plan') or not self.writing_execution_plan:
            self.generate_writing_execution_plan(is_long_form)

        config = {
            "orchestrator_version": "1.0",
            "task_id": self.task_id,
            "topic": self.topic,
            "execution_mode": "writing_flow",
            "is_long_form": is_long_form,
            "writing_agent_sequence": self.config.WRITING_AGENT_SEQUENCE,
            "writing_mandatory_agents": self.config.WRITING_MANDATORY_AGENTS,
            "writing_optional_agents": self.config.WRITING_OPTIONAL_AGENTS,
            "steps": []
        }

        for step in self.writing_execution_plan:
            step_config = {
                "step_number": step["step"],
                "agent": step["agent"],
                "type": step["type"],
                "description": step["description"],
                "mandatory": step.get("mandatory", False),
                "depends_on": step.get("depends_on", []),
                "solo_task": {
                    "subagent_type": "general_purpose_task",
                    "query": f"执行{step['agent']}：{step['description']}",
                    "response_language": "zh",
                    "input_data": step["input"],
                    "expected_output": step["output_format"],
                    "timeout": step["timeout"],
                }
            }
            config["steps"].append(step_config)

        return config

    def get_execution_summary(self) -> Dict:
        """获取执行摘要"""
        return {
            "task_id": self.task_id,
            "topic": self.topic,
            "total_steps": len(self.execution_plan),
            "completed_calls": len(self.call_records),
            "task_dir": self.task_dir,
            "execution_plan_file": f"{self.task_dir}/execution_plan.json",
            "call_records_file": f"{self.task_dir}/agent_call_records.json",
        }


def demo_solo_integration():
    """
    演示SOLO集成方式
    
    展示orchestrator如何生成SOLO可执行的配置
    """
    print("=" * 70)
    print("KZCQL Orchestrator SOLO Integration Demo")
    print("=" * 70)
    
    # 创建编排器
    orch = SoloOrchestrator(
        task_id="架构评估_20260519",
        topic="Phase 0-4架构升级后评估",
        review_type="全面审查"
    )
    
    # 生成执行计划
    plan = orch.generate_execution_plan()
    
    # 验证计划
    is_valid = orch.validate_plan()
    
    # 生成SOLO配置
    solo_config = orch.generate_solo_task_config()
    
    # 保存SOLO配置
    config_file = f"{orch.task_dir}/solo_task_config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(solo_config, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 70)
    print("SOLO Task Configuration Generated")
    print("=" * 70)
    print(f"\n配置文件：{config_file}")
    print(f"\n配置内容：")
    print(json.dumps(solo_config, ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 70)
    print("SOLO Integration Evidence")
    print("=" * 70)
    print(f"""
证据1：执行计划符合KZCQL规范
  - A1-主串行步骤：{any(p['agent'] == 'A1-主' for p in plan)}
  - D5并行步骤数：{sum(1 for p in plan if p['agent'].startswith('A1-D5-'))}/4
  - 权重总和：{sum(OrchestratorConfig.D5_WEIGHTS.values())}
  
证据2：生成SOLO可执行配置
  - 配置包含{len(solo_config['steps'])}个步骤
  - 每个步骤都有solo_task字段
  - 可直接被SOLO Task工具使用
  
证据3：调用记录机制
  - 支持记录每次Agent调用
  - 保存到agent_call_records.json
  - 符合KZCQL可追溯性要求
    """)
    
    return orch, solo_config


if __name__ == "__main__":
    orch, config = demo_solo_integration()
