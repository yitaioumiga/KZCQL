#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KZCQL 子智能体系统提示词注入器
强制为主智能体调用子智能体时注入系统提示词，确保子智能体行为符合规范
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

class AgentPromptInjector:
    """
    子智能体系统提示词注入器
    
    核心原则：
    1. 强制注入：每次调用子智能体必须注入系统提示词
    2. 规范对齐：提示词必须与子智能体规范文件一致
    3. 上下文完整：提示词必须包含所有必要的上下文信息
    4. 版本控制：提示词必须标注版本，确保可追溯
    """
    
    # 子智能体规范文件映射
    AGENT_SPEC_FILES = {
        "W1": "02_子Agent规范/写作组/初稿撰写Agent.md",
        "W2": "02_子Agent规范/写作组/迭代修改Agent.md",
        "R1": "02_子Agent规范/评审专家组/事实核查Agent.md",
        "R2": "02_子Agent规范/评审专家组/全量评审Agent.md",
        "R3": "02_子Agent规范/评审专家组/差异评审Agent.md",
        "R4": "02_子Agent规范/评审专家组/评级判定Agent.md",
        "I1": "02_子Agent规范/督察组/督察智能体.md",
        "E1": "02_子Agent规范/规则修改Agent/规则修改Agent.md",
        "A1": "02_子Agent规范/架构专家组/架构专家Agent.md",
        "D1": "02_子Agent规范/配图设计组/配图设计Agent.md",
        "D2": "02_子Agent规范/调研专家组/D2_调研Agent.md",
        "D3": "02_子Agent规范/调研专家组/D3_角度挖掘Agent.md",
    }
    
    # 共享知识库文件
    SHARED_KNOWLEDGE_FILES = {
        "前置撰写规则": "01_共享知识库/前置撰写规则/前置撰写规则.md",
        "后置评审规则": "01_共享知识库/后置评审规则/后置评审规范.md",
        "评分体系": "01_共享知识库/后置评审规则/评分体系.md",
        "一票否决项": "01_共享知识库/后置评审规则/一票否决项.md",
        "去AI感检测清单": "01_共享知识库/前置撰写规则/去AI感检测清单.md",
        "系列文章评审检查项": "01_共享知识库/后置评审规则/系列文章评审检查项.md",
    }
    
    def __init__(self, kzcql_root: str = "/workspace/KZCQL"):
        self.kzcql_root = kzcql_root
        self.prompt_cache: Dict[str, str] = {}  # 缓存已加载的提示词
        
    def load_spec(self, agent_name: str) -> str:
        """加载子智能体规范文件"""
        if agent_name in self.prompt_cache:
            return self.prompt_cache[agent_name]
            
        spec_file = self.AGENT_SPEC_FILES.get(agent_name)
        if not spec_file:
            raise ValueError(f"未知的Agent: {agent_name}")
            
        spec_path = os.path.join(self.kzcql_root, spec_file)
        if not os.path.exists(spec_path):
            raise FileNotFoundError(f"规范文件不存在: {spec_path}")
            
        with open(spec_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        self.prompt_cache[agent_name] = content
        return content
        
    def load_shared_knowledge(self, knowledge_name: str) -> str:
        """加载共享知识库文件"""
        knowledge_file = self.SHARED_KNOWLEDGE_FILES.get(knowledge_name)
        if not knowledge_file:
            raise ValueError(f"未知的知识库: {knowledge_name}")
            
        knowledge_path = os.path.join(self.kzcql_root, knowledge_file)
        if not os.path.exists(knowledge_path):
            raise FileNotFoundError(f"知识库文件不存在: {knowledge_path}")
            
        with open(knowledge_path, 'r', encoding='utf-8') as f:
            return f.read()
            
    def build_system_prompt(self, agent_name: str, context: Dict) -> str:
        """
        构建系统提示词

        结构：
        1. 角色定义（来自规范文件）
        2. 【强制】自身规范读取要求
        3. 核心职责（来自规范文件）
        4. 输入规范（来自规范文件）
        5. 输出规范（来自规范文件）
        6. 禁止事项（来自规范文件）
        7. 当前任务上下文（动态生成）
        8. 历史记录（如有）
        """
        # 加载规范
        spec_content = self.load_spec(agent_name)
        spec_file_path = self.AGENT_SPEC_FILES.get(agent_name, '未知')

        # 提取关键部分（简化版，实际应该解析Markdown）
        prompt_parts = [
            f"# 系统提示词 - {agent_name}",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 角色定义",
            f"你是KZCQL系统的{agent_name}子智能体。",
            "",
            "## 【强制】自身规范读取要求",
            f"**在开始执行任何任务之前，你必须：**",
            f"1. **读取你的规范文件**：`/workspace/KZCQL/{spec_file_path}`",
            f"2. **确认核心职责**：理解你在系统中的角色定位",
            f"3. **确认输入规范**：了解所有必需和可选输入",
            f"4. **确认输出规范**：了解输出格式和质量要求",
            f"5. **确认禁止事项**：明确哪些行为是禁止的",
            f"6. **确认工作流程**：按照规范中的步骤逐步执行",
            "",
            f"**为什么必须读取自身规范？**",
            f"- 你的规范文件定义了你的行为准则和工作标准",
            f"- 规范文件可能随时间更新，每次执行前读取确保使用最新版本",
            f"- 主Agent只传递任务描述，具体的执行细节在你的规范中定义",
            "",
            "## 规范文件",
            f"你的完整规范定义在: {spec_file_path}",
            "",
            "## 核心职责",
            self._extract_section(spec_content, "核心职责"),
            "",
            "## 输入规范",
            self._extract_section(spec_content, "输入"),
            "",
            "## 输出规范",
            self._extract_section(spec_content, "输出"),
            "",
            "## 禁止事项",
            self._extract_section(spec_content, "禁止"),
            "",
            "## 当前任务上下文",
            self._build_context_section(context),
            "",
            "## 强制检查清单（执行前必须确认）",
            self._build_checklist(agent_name),
        ]

        return "\n".join(prompt_parts)
        
    def _extract_section(self, content: str, section_name: str) -> str:
        """
        从规范文件中提取特定章节
        
        支持提取的章节：
        - 核心职责：匹配"核心职责"、"主要职责"等
        - 输入：匹配"输入规范"、"必需输入"等
        - 输出：匹配"输出规范"、"输出格式"等
        - 禁止：匹配"禁止事项"、"禁止行为"等
        
        Args:
            content: 规范文件内容
            section_name: 要提取的章节名称
            
        Returns:
            提取的章节内容，如果未找到则返回提示信息
        """
        import re
        
        # 定义章节匹配模式
        section_patterns = {
            "核心职责": [
                r"##?\s*核心职责\s*\n(.*?)(?=##?\s|$)",
                r"##?\s*主要职责\s*\n(.*?)(?=##?\s|$)",
                r"\*\*核心职责\*\*[:：]\s*\n?(.*?)(?=\n\n|\n##|\Z)",
            ],
            "输入": [
                r"##?\s*输入规范\s*\n(.*?)(?=##?\s|$)",
                r"##?\s*必需输入\s*\n(.*?)(?=##?\s|$)",
                r"##?\s*2\.1\s*必需输入\s*\n(.*?)(?=##?\s*2\.2|$)",
            ],
            "输出": [
                r"##?\s*输出规范\s*\n(.*?)(?=##?\s|$)",
                r"##?\s*输出格式\s*\n(.*?)(?=##?\s|$)",
                r"\*\*输出格式\*\*[:：]\s*\n?(.*?)(?=\n\n|\n##|\Z)",
            ],
            "禁止": [
                r"##?\s*禁止事项\s*\n(.*?)(?=##?\s|$)",
                r"##?\s*禁止行为\s*\n(.*?)(?=##?\s|$)",
                r"\*\*禁止事项\*\*[:：]\s*\n?(.*?)(?=\n\n|\n##|\Z)",
            ],
        }
        
        # 获取匹配模式
        patterns = section_patterns.get(section_name, [])
        if not patterns:
            return f"[请查阅完整规范文件获取{section_name}的详细定义]"
        
        # 尝试匹配
        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            if matches:
                # 取第一个匹配，清理空白
                section_content = matches[0].strip()
                # 限制长度，避免过长
                if len(section_content) > 800:
                    section_content = section_content[:800] + "\n... [内容已截断，请查阅完整规范文件]"
                return section_content
        
        # 未找到匹配
        return f"[请查阅完整规范文件获取{section_name}的详细定义]"
        
    def _build_context_section(self, context: Dict) -> str:
        """构建当前任务上下文"""
        context_parts = []
        
        if "task_id" in context:
            context_parts.append(f"- 任务ID: {context['task_id']}")
        if "topic" in context:
            context_parts.append(f"- 主题: {context['topic']}")
        if "previous_agents" in context:
            context_parts.append(f"- 前置Agent: {', '.join(context['previous_agents'])}")
        if "user_decisions" in context:
            context_parts.append(f"- 用户决策: {json.dumps(context['user_decisions'], ensure_ascii=False)}")
            
        return "\n".join(context_parts) if context_parts else "- 无特定上下文"
        
    def _build_checklist(self, agent_name: str) -> str:
        """构建强制检查清单"""
        # 获取规范文件路径
        spec_file_path = self.AGENT_SPEC_FILES.get(agent_name, '未知')

        checklists = {
            "W1": f"""
- [ ] **【强制】是否已读取自身规范文件** (`/workspace/KZCQL/{spec_file_path}`)？
- [ ] 是否已读取前置撰写规则？
- [ ] 是否已确认用户论点方向约束？
- [ ] 是否已检查D2/D3输入（如有）？
- [ ] 是否已准备Skill调用上下文？
- [ ] 是否已执行四层自检（L1-L4）？""",
            "W2": f"""
- [ ] **【强制】是否已读取自身规范文件** (`/workspace/KZCQL/{spec_file_path}`)？
- [ ] 是否已理解评分报告中的问题？
- [ ] 是否已定位需要修改的具体位置？
- [ ] 是否已执行最小化修改？
- [ ] 是否已执行修改后自检？""",
            "R1": f"""
- [ ] **【强制】是否已读取自身规范文件** (`/workspace/KZCQL/{spec_file_path}`)？
- [ ] 是否已读取一票否决项清单？
- [ ] 是否已逐项检查19项否决项？
- [ ] 是否已标注所有存疑内容？
- [ ] 是否已生成复检清单？""",
            "R2": f"""
- [ ] **【强制】是否已读取自身规范文件** (`/workspace/KZCQL/{spec_file_path}`)？
- [ ] 是否已读取评分体系？
- [ ] 是否已按12维度逐项评分？
- [ ] 是否已检查去AI感？
- [ ] 是否已生成改进建议？""",
            "R3": f"""
- [ ] **【强制】是否已读取自身规范文件** (`/workspace/KZCQL/{spec_file_path}`)？
- [ ] 是否已对比修改前后差异？
- [ ] 是否已评估修改影响范围？
- [ ] 是否已检查是否引入新问题？
- [ ] 是否已决定是否回退到R2？""",
            "R4": f"""
- [ ] **【强制】是否已读取自身规范文件** (`/workspace/KZCQL/{spec_file_path}`)？
- [ ] 是否已读取R1事实核查报告？
- [ ] 是否已读取R2/R3评分报告？
- [ ] 是否已执行S/A级发布前检查？
- [ ] 是否已确定最终评级和下一步行动？""",
            "D1": f"""
- [ ] **【强制】是否已读取自身规范文件** (`/workspace/KZCQL/{spec_file_path}`)？
- [ ] 是否已读取前置撰写规则和配图设计规则？
- [ ] 是否已分析文章配图需求？
- [ ] 是否已生成所有配图？
- [ ] 是否已执行配图质检？""",
            "D2": f"""
- [ ] **【强制】是否已读取自身规范文件** (`/workspace/KZCQL/{spec_file_path}`)？
- [ ] 是否已确认搜索预算？
- [ ] 是否已执行4个必选维度调研？
- [ ] 是否已标注所有信息来源？
- [ ] 是否已执行质量检查？""",
            "D3": f"""
- [ ] **【强制】是否已读取自身规范文件** (`/workspace/KZCQL/{spec_file_path}`)？
- [ ] 是否已读取D2信息地图（如有）？
- [ ] 是否已执行第一直觉排除法？
- [ ] 是否已使用4种方法生成角度？
- [ ] 是否已评估并推荐最佳角度？""",
            "I1": f"""
- [ ] **【强制】是否已读取自身规范文件** (`/workspace/KZCQL/{spec_file_path}`)？
- [ ] 是否已明确审查范围？
- [ ] 是否已读取相关Agent规范？
- [ ] 是否已对比规范与实际执行？
- [ ] 是否已输出审查报告？""",
            "E1": f"""
- [ ] **【强制】是否已读取自身规范文件** (`/workspace/KZCQL/{spec_file_path}`)？
- [ ] 是否已解析人类反馈？
- [ ] 是否已分析规则缺口？
- [ ] 是否已设计规则变更方案？
- [ ] 是否已评估影响范围？""",
            "A1": f"""
- [ ] **【强制】是否已读取自身规范文件** (`/workspace/KZCQL/{spec_file_path}`)？
- [ ] 是否已读取所有架构文档？
- [ ] 是否已读取所有子Agent规范？
- [ ] 是否已执行十维度审查（D1-D10）？
- [ ] 是否已执行D10审查框架自省（文件-维度覆盖矩阵）？
- [ ] 是否已使用D5并行拆解策略？
- [ ] 是否已使用120分制评分体系？
- [ ] 是否已输出架构审查报告？""",
        }

        return checklists.get(agent_name, f"""
- [ ] **【强制】是否已读取自身规范文件** (`/workspace/KZCQL/{spec_file_path}`)？
- [ ] 是否已查阅相关规则文件？
- [ ] 是否已理解任务要求？
- [ ] 是否已按照规范执行？""")
        
    def inject_prompt(self, agent_name: str, user_input: str, context: Dict) -> Dict:
        """
        注入系统提示词
        
        返回格式：
        {
            "system_prompt": "系统提示词",
            "user_input": "用户输入",
            "metadata": {
                "agent_name": "Agent名称",
                "spec_version": "规范版本",
                "injection_time": "注入时间"
            }
        }
        """
        system_prompt = self.build_system_prompt(agent_name, context)
        
        return {
            "system_prompt": system_prompt,
            "user_input": user_input,
            "metadata": {
                "agent_name": agent_name,
                "spec_file": self.AGENT_SPEC_FILES.get(agent_name),
                "injection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "context_keys": list(context.keys())
            }
        }
        
    def validate_injection(self, injection_result: Dict) -> bool:
        """验证提示词注入是否完整"""
        required_keys = ["system_prompt", "user_input", "metadata"]
        
        for key in required_keys:
            if key not in injection_result:
                return False
                
        if not injection_result["system_prompt"]:
            return False
            
        return True


class PromptInjectionError(Exception):
    """提示词注入错误"""
    pass


# 使用示例
USAGE_EXAMPLE = """
# 在主智能体中使用提示词注入器

from agent_prompt_injector import AgentPromptInjector

# 初始化注入器
injector = AgentPromptInjector()

# 准备上下文
context = {
    "task_id": "TASK-20260519-001",
    "topic": "AI写作工具对比",
    "previous_agents": ["D2", "D3"],
    "user_decisions": {"D2": "enable", "D3": "enable"}
}

# 注入W1的系统提示词
injection = injector.inject_prompt("W1", "请撰写初稿", context)

# 验证注入
if injector.validate_injection(injection):
    # 调用子智能体
    result = call_agent_with_prompt(
        agent_name="W1",
        system_prompt=injection["system_prompt"],
        user_input=injection["user_input"]
    )
else:
    raise PromptInjectionError("提示词注入验证失败")
"""


if __name__ == "__main__":
    print("KZCQL 子智能体系统提示词注入器")
    print("=" * 60)
    print("支持的Agent:")
    for agent, spec_file in AgentPromptInjector.AGENT_SPEC_FILES.items():
        print(f"  - {agent}: {spec_file}")
    print()
    print("=" * 60)
    print("使用示例：")
    print(USAGE_EXAMPLE)
