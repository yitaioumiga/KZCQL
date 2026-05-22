#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KZCQL 主智能体编排器 - 强约束脚本
强制主智能体按照规范正确调用子智能体，禁止跳过任何步骤
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

# 强制配置：禁止修改
class OrchestratorConfig:
    """编排器强制配置"""

    # ========== 串行Agent序列（写作流程）==========
    # 子智能体调用顺序（严格顺序，禁止跳过）
    AGENT_SEQUENCE = [
        "D2",  # 调研Agent（可选但不可跳过，必须显式决策）
        "D3",  # 角度挖掘Agent（可选但不可跳过，必须显式决策）
        "W1",  # 初稿撰写Agent（强制）
        "ImageCheck",  # 配图检查（强制，如需要配图）
        "R1",  # 事实核查（强制）
        "R2",  # 全量评审（强制）
        "R3",  # 差异评审（强制，如需要）
        "R4",  # 评级判定（强制）
        "D1",  # 配图设计（强制，如需要配图）
    ]

    # 强制调用的智能体（不可跳过）
    MANDATORY_AGENTS = ["W1", "R1", "R2", "R4"]

    # 可选但必须决策的智能体
    OPTIONAL_AGENTS = ["D2", "D3", "ImageCheck", "R3", "D1"]

    # ========== 并行Agent组（架构评估流程）==========
    # 架构评估并行组（可以同时并行调用）
    ARCHITECTURE_PARALLEL_GROUPS = {
        # 串行调用组（按顺序执行）
        "A1-主组": ["A1-主"],  # 执行D1-D4, D6-D10

        # 并行调用组（同时执行）
        "D5-并行组": [
            "D5-1",  # 规则执行映射
            "D5-2",  # 执行验证映射
            "D5-3",  # 悬空规则检测
            "D5-4",  # 盲评风险检测
        ],

        # 串行调用组（按顺序执行）
        "A1-整合组": ["A1-整合"],  # 整合所有结果
    }

    # 架构评估流程（完整序列）
    ARCHITECTURE_SEQUENCE = [
        "A1-主组",   # Step 4.1：串行
        "D5-并行组", # Step 4.2：并行
        "A1-整合组", # Step 4.3：串行
    ]

    # ========== 其他并行组（按需扩展）==========
    # 联合督查并行组
    INSPECTION_PARALLEL_GROUPS = {
        "主Agent调查": ["主Agent调查"],
        "I1调查": ["I1调查"],
        "交叉验证": ["交叉验证"],
    }

    # 最大重试次数
    MAX_RETRIES = 3

    # 超时时间（秒）
    TIMEOUT_SECONDS = 300

class AgentCallRecord:
    """智能体调用记录"""
    def __init__(self, agent_name: str, call_time: str, status: str, output_path: str = None):
        self.agent_name = agent_name
        self.call_time = call_time
        self.status = status  # success, failed, skipped
        self.output_path = output_path
        
    def to_dict(self) -> Dict:
        return {
            "agent_name": self.agent_name,
            "call_time": self.call_time,
            "status": self.status,
            "output_path": self.output_path
        }

class Orchestrator:
    """
    KZCQL主智能体编排器
    
    核心原则：
    1. 强制顺序：必须按照AGENT_SEQUENCE顺序调用
    2. 禁止跳过：MANDATORY_AGENTS中的智能体绝对禁止跳过
    3. 显式决策：OPTIONAL_AGENTS中的智能体必须显式决策（启用/跳过）
    4. 记录完整：每个调用必须有记录，禁止"隐形"调用
    5. 异常阻断：失败时必须进入阻断流程，禁止自动继续
    """
    
    def __init__(self, task_id: str, topic: str):
        self.task_id = task_id
        self.topic = topic
        self.call_records: List[AgentCallRecord] = []
        self.current_step = 0
        self.decisions: Dict[str, str] = {}  # 记录每个可选Agent的决策
        self.errors: List[str] = []
        
        # 创建任务目录
        self.task_dir = f"/workspace/KZCQL/04_工作区/产出归档/{datetime.now().strftime('%Y%m%d')}_{task_id}"
        os.makedirs(self.task_dir, exist_ok=True)
        
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"
        print(log_line)
        
        # 写入日志文件
        with open(f"{self.task_dir}/orchestrator.log", "a", encoding="utf-8") as f:
            f.write(log_line + "\n")
            
    def validate_sequence(self, agent_name: str) -> bool:
        """
        验证调用顺序是否正确
        禁止：跳过前置Agent、重复调用、逆序调用
        """
        expected_agent = OrchestratorConfig.AGENT_SEQUENCE[self.current_step]
        
        if agent_name != expected_agent:
            self.log(f"顺序错误：期望调用 {expected_agent}，实际调用 {agent_name}", "ERROR")
            self.errors.append(f"Sequence violation: expected {expected_agent}, got {agent_name}")
            return False
            
        return True
        
    def check_mandatory(self, agent_name: str) -> bool:
        """检查是否为强制调用Agent"""
        return agent_name in OrchestratorConfig.MANDATORY_AGENTS
        
    def make_decision(self, agent_name: str, context: Dict) -> str:
        """
        对可选Agent进行显式决策
        禁止：自动决策、默认启用、默认跳过
        必须：询问用户或基于明确规则决策
        """
        if agent_name not in OrchestratorConfig.OPTIONAL_AGENTS:
            return "not_optional"
            
        # 检查是否已经决策
        if agent_name in self.decisions:
            return self.decisions[agent_name]
            
        # 决策逻辑（必须显式）
        decision = self._explicit_decision(agent_name, context)
        self.decisions[agent_name] = decision
        
        self.log(f"决策 [{agent_name}]: {decision}")
        return decision
        
    def _explicit_decision(self, agent_name: str, context: Dict) -> str:
        """
        显式决策逻辑
        子类必须覆盖此方法，实现具体的决策逻辑
        """
        raise NotImplementedError("子类必须实现 _explicit_decision 方法")
        
    def call_agent(self, agent_name: str, input_data: Dict, 
                   agent_func: Callable) -> Dict:
        """
        调用子智能体（强约束）
        
        流程：
        1. 验证顺序
        2. 检查是否强制
        3. 如果是可选，进行显式决策
        4. 执行调用
        5. 记录结果
        6. 更新步骤
        """
        self.log(f"准备调用 [{agent_name}]...")
        
        # 1. 验证顺序
        if not self.validate_sequence(agent_name):
            raise OrchestratorError(f"调用顺序错误: {agent_name}")
            
        # 2. 检查是否强制
        is_mandatory = self.check_mandatory(agent_name)
        
        # 3. 可选Agent进行显式决策
        if not is_mandatory:
            decision = self.make_decision(agent_name, input_data)
            if decision == "skip":
                self._record_skip(agent_name)
                self.current_step += 1
                return {"status": "skipped", "reason": "explicit_decision"}
                
        # 4. 执行调用（带重试）
        result = self._execute_with_retry(agent_name, input_data, agent_func)
        
        # 5. 记录结果
        self._record_call(agent_name, result)
        
        # 6. 更新步骤
        self.current_step += 1
        
        return result
        
    def _execute_with_retry(self, agent_name: str, input_data: Dict,
                           agent_func: Callable) -> Dict:
        """带重试的执行"""
        for attempt in range(OrchestratorConfig.MAX_RETRIES):
            try:
                self.log(f"执行 [{agent_name}] 第 {attempt + 1} 次尝试...")
                result = agent_func(input_data)
                
                if result.get("status") == "success":
                    self.log(f"[{agent_name}] 执行成功")
                    return result
                else:
                    raise AgentExecutionError(f"Agent returned non-success: {result}")
                    
            except Exception as e:
                self.log(f"[{agent_name}] 执行失败: {str(e)}", "ERROR")
                
                if attempt < OrchestratorConfig.MAX_RETRIES - 1:
                    self.log(f"[{agent_name}] 准备重试...")
                else:
                    # 达到最大重试次数，进入阻断流程
                    return self._blocking_handler(agent_name, input_data, e)
                    
        return {"status": "failed", "error": "Max retries exceeded"}
        
    def _blocking_handler(self, agent_name: str, input_data: Dict, 
                         error: Exception) -> Dict:
        """
        阻断处理流程
        禁止：自动继续、跳过强制Agent
        必须：显式决策如何处理
        """
        self.log(f"[{agent_name}] 进入阻断流程", "ERROR")
        
        is_mandatory = self.check_mandatory(agent_name)
        
        if is_mandatory:
            # 强制Agent失败，必须修复后才能继续
            self.log(f"[{agent_name}] 是强制Agent，必须修复后才能继续", "ERROR")
            raise OrchestratorError(f"Mandatory agent {agent_name} failed: {error}")
        else:
            # 可选Agent失败，询问用户
            decision = self._ask_user_blocking(agent_name, error)
            if decision == "skip":
                return {"status": "skipped", "reason": "user_decision_after_failure"}
            elif decision == "retry":
                # 重新调用
                return self.call_agent(agent_name, input_data, 
                                      lambda x: self._get_agent_func(agent_name)(x))
            else:
                raise OrchestratorError(f"Unknown blocking decision: {decision}")
                
    def _ask_user_blocking(self, agent_name: str, error: Exception) -> str:
        """
        阻断时询问用户
        子类必须覆盖此方法
        """
        raise NotImplementedError("子类必须实现 _ask_user_blocking 方法")
        
    def _record_call(self, agent_name: str, result: Dict):
        """记录调用"""
        record = AgentCallRecord(
            agent_name=agent_name,
            call_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            status=result.get("status", "unknown"),
            output_path=result.get("output_path")
        )
        self.call_records.append(record)
        
        # 保存到文件
        self._save_records()
        
    def _record_skip(self, agent_name: str):
        """记录跳过"""
        record = AgentCallRecord(
            agent_name=agent_name,
            call_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            status="skipped",
            output_path=None
        )
        self.call_records.append(record)
        self._save_records()
        
    def _save_records(self):
        """保存调用记录"""
        records_file = f"{self.task_dir}/agent_call_records.json"
        with open(records_file, "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in self.call_records], f, 
                     ensure_ascii=False, indent=2)
            
    def get_execution_report(self) -> Dict:
        """生成执行报告"""
        return {
            "task_id": self.task_id,
            "topic": self.topic,
            "start_time": self.call_records[0].call_time if self.call_records else None,
            "end_time": self.call_records[-1].call_time if self.call_records else None,
            "total_steps": len(self.call_records),
            "completed_steps": sum(1 for r in self.call_records if r.status == "success"),
            "skipped_steps": sum(1 for r in self.call_records if r.status == "skipped"),
            "failed_steps": sum(1 for r in self.call_records if r.status == "failed"),
            "decisions": self.decisions,
            "errors": self.errors,
            "call_records": [r.to_dict() for r in self.call_records]
        }
        
    def validate_completion(self) -> bool:
        """
        验证流程是否完整完成
        禁止：未完成所有强制Agent就结束
        """
        called_agents = {r.agent_name for r in self.call_records}

        for mandatory in OrchestratorConfig.MANDATORY_AGENTS:
            if mandatory not in called_agents:
                self.log(f"验证失败：强制Agent [{mandatory}] 未被调用", "ERROR")
                return False

        self.log("流程验证通过：所有强制Agent已调用")
        return True

    # ========== 并行调用支持（P33补丁新增）==========
    def call_parallel_group(self, group_name: str, agents_data: Dict[str, Dict],
                              agent_funcs: Dict[str, Callable]) -> Dict[str, Dict]:
        """
        调用并行Agent组（P33补丁新增）

        用于架构评估等需要并行执行的场景：
        - A1-主组（串行）：执行D1-D4, D6-D10
        - D5-并行组（并行）：D5-1/2/3/4同时执行
        - A1-整合组（串行）：整合所有结果

        注意：SOLO环境使用Task工具并行调用多个子代理

        Args:
            group_name: 并行组名称
            agents_data: {agent_name: input_data} 格式的字典
            agent_funcs: {agent_name: callable} 格式的字典

        Returns:
            {agent_name: result} 格式的结果字典

        Example:
            # 调用D5并行组
            results = orch.call_parallel_group(
                "D5-并行组",
                {
                    "D5-1": {"task": "规则执行映射"},
                    "D5-2": {"task": "执行验证映射"},
                    "D5-3": {"task": "悬空规则检测"},
                    "D5-4": {"task": "盲评风险检测"},
                },
                {
                    "D5-1": d5_1_agent_func,
                    "D5-2": d5_2_agent_func,
                    "D5-3": d5_3_agent_func,
                    "D5-4": d5_4_agent_func,
                }
            )
        """
        self.log(f"准备调用并行组 [{group_name}]...")

        # 获取组内的Agent列表
        if group_name not in OrchestratorConfig.ARCHITECTURE_PARALLEL_GROUPS:
            raise OrchestratorError(f"未知并行组: {group_name}")

        agents = OrchestratorConfig.ARCHITECTURE_PARALLEL_GROUPS[group_name]
        self.log(f"并行组 [{group_name}] 包含 {len(agents)} 个Agent: {agents}")

        # ========== P34补丁：配置完整性检查（P0-01修复）==========
        missing_agents = []
        for agent_name in agents:
            if agent_name not in agents_data:
                missing_agents.append(agent_name)
                self.log(f"错误：Agent [{agent_name}] 缺少输入数据", "ERROR")

        if missing_agents:
            error_msg = f"配置完整性检查失败：并行组 [{group_name}] 缺少 {len(missing_agents)} 个Agent的输入数据: {missing_agents}"
            self.log(error_msg, "ERROR")
            self.errors.append(f"Config integrity check failed: {error_msg}")
            raise OrchestratorError(error_msg)

        self.log(f"配置完整性检查通过：所有 {len(agents)} 个Agent都有输入数据", "INFO")
        # ========== P34补丁结束 ==========

        results = {}

        # 记录并行调用开始
        self.log(f"开始并行调用 {len(agents)} 个Agent...", "INFO")

        # 在SOLO环境中，这里应该返回任务配置
        # 主Agent需要使用Task工具并行调用这些子代理
        for agent_name in agents:
            # 记录为待执行
            record = AgentCallRecord(
                agent_name=agent_name,
                call_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                status="pending_parallel",
                output_path=None
            )
            self.call_records.append(record)

        # 返回并行调用配置（供SOLO Task工具使用）
        parallel_config = {
            "group_name": group_name,
            "agents": agents,
            "agents_data": agents_data,
            "call_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        self.log(f"并行组 [{group_name}] 配置已生成，等待SOLO Task工具执行", "INFO")

        return parallel_config

    def validate_parallel_execution(self, group_name: str, results: Dict[str, Dict]) -> bool:
        """
        验证并行执行结果（P33补丁新增）

        Args:
            group_name: 并行组名称
            results: {agent_name: result} 格式的结果字典

        Returns:
            True if all agents succeeded, False otherwise
        """
        agents = OrchestratorConfig.ARCHITECTURE_PARALLEL_GROUPS.get(group_name, [])

        all_success = True
        for agent_name in agents:
            if agent_name not in results:
                self.log(f"并行Agent [{agent_name}] 结果缺失", "ERROR")
                all_success = False
            elif results[agent_name].get("status") != "success":
                self.log(f"并行Agent [{agent_name}] 执行失败", "ERROR")
                all_success = False
            else:
                self.log(f"并行Agent [{agent_name}] 执行成功", "INFO")
                # 更新记录状态
                for record in reversed(self.call_records):
                    if record.agent_name == agent_name and record.status == "pending_parallel":
                        record.status = "success"
                        record.output_path = results[agent_name].get("output_path")
                        break

        if all_success:
            self.log(f"并行组 [{group_name}] 所有Agent执行成功", "INFO")
        else:
            self.log(f"并行组 [{group_name}] 存在失败Agent", "ERROR")

        return all_success

    def execute_architecture_flow(self) -> Dict:
        """
        执行架构评估完整流程（P33补丁新增）

        按照Step 4的并行+串行混合方式执行：
        1. 调用A1-主（串行）
        2. 并行调用D5-1/2/3/4
        3. 调用A1-整合（串行）
        """
        self.log("开始执行架构评估完整流程（并行+串行混合）", "INFO")

        flow_results = {
            "A1-主": None,
            "D5-并行": None,
            "A1-整合": None,
        }

        # Step 4.1: 调用A1-主（串行）
        self.log("Step 4.1: 调用A1-主（串行）", "INFO")
        # 这里需要主Agent自行调用A1-主

        # Step 4.2: 并行调用D5子代理
        self.log("Step 4.2: 并行调用D5子代理", "INFO")
        d5_config = self.call_parallel_group(
            "D5-并行组",
            {
                "D5-1": {"task": "规则执行映射"},
                "D5-2": {"task": "执行验证映射"},
                "D5-3": {"task": "悬空规则检测"},
                "D5-4": {"task": "盲评风险检测"},
            },
            {}
        )
        flow_results["D5-并行"] = d5_config

        # Step 4.3: 调用A1-整合（串行）
        self.log("Step 4.3: 调用A1-整合（串行）", "INFO")
        # 这里需要主Agent自行调用A1-整合

        self.log("架构评估完整流程配置已生成", "INFO")

        return flow_results

class OrchestratorError(Exception):
    """编排器错误"""
    pass

class AgentExecutionError(Exception):
    """智能体执行错误"""
    pass


# 使用示例和强制检查清单
USAGE_EXAMPLE = """
# 主智能体必须使用编排器的示例

class MyOrchestrator(Orchestrator):
    def _explicit_decision(self, agent_name: str, context: Dict) -> str:
        # 必须显式决策，禁止自动决策
        if agent_name == "D2":
            # 询问用户是否启用D2
            return ask_user("是否启用D2调研？")
        return "skip"
        
    def _ask_user_blocking(self, agent_name: str, error: Exception) -> str:
        # 阻断时询问用户
        return ask_user(f"{agent_name}失败，是否跳过？")

# 强制检查清单（主智能体必须执行）
CHECKLIST = [
    "[ ] 是否按照AGENT_SEQUENCE顺序调用？",
    "[ ] MANDATORY_AGENTS是否全部调用？",
    "[ ] OPTIONAL_AGENTS是否显式决策？",
    "[ ] 每个调用是否有记录？",
    "[ ] 失败时是否进入阻断流程？",
    "[ ] 结束前是否调用validate_completion()？",
]
"""

if __name__ == "__main__":
    print("KZCQL 主智能体编排器 - 强约束脚本")
    print("=" * 60)
    print("此脚本定义了主智能体必须遵守的编排规则：")
    print()
    print("1. 强制顺序：", " → ".join(OrchestratorConfig.AGENT_SEQUENCE))
    print()
    print("2. 强制Agent（禁止跳过）：", ", ".join(OrchestratorConfig.MANDATORY_AGENTS))
    print()
    print("3. 可选Agent（必须显式决策）：", ", ".join(OrchestratorConfig.OPTIONAL_AGENTS))
    print()
    print("4. 最大重试次数：", OrchestratorConfig.MAX_RETRIES)
    print()
    print("=" * 60)
    print("主智能体必须继承Orchestrator类并实现抽象方法")
