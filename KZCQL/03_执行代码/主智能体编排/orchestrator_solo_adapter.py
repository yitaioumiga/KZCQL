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
