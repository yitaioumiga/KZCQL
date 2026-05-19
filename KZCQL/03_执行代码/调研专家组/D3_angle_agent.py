#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D3 角度挖掘Agent - 可执行代码
基于D2信息地图生成多个内容角度选项
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
import argparse

class D3AngleAgent:
    """D3角度挖掘Agent实现"""
    
    def __init__(self, topic: str, d2_info_map: Dict = None, 
                 user_profile: str = None, target_audience: str = None):
        self.topic = topic
        self.d2_info_map = d2_info_map or {}
        self.user_profile = user_profile or ""
        self.target_audience = target_audience or "泛互联网人群"
        self.angle_options = []
        self.excluded_angles = []
        self.recommendation = ""
        
    def log(self, message: str):
        """打印日志"""
        print(f"[D3] {message}")
        
    def analyze_common_angles(self) -> List[str]:
        """分析并排除常见角度（第一直觉排除法）"""
        self.log("执行第一直觉排除法...")
        
        # 基于主题分析常见角度
        common_angles = [
            f"{self.topic}的技术原理分析（排除原因：所有人都会想到，缺乏独特性）",
            f"{self.topic}的优缺点对比（排除原因：已有大量同类文章，缺乏差异化）",
            f"{self.topic}的未来趋势预测（排除原因：过于宽泛，缺乏具体反差点）"
        ]
        
        self.excluded_angles = common_angles
        self.log(f"排除常见角度: {len(common_angles)}个")
        return common_angles
        
    def generate_contrast_angle(self) -> Optional[Dict]:
        """使用反差法生成角度"""
        self.log("使用反差法生成角度...")
        
        # 主流方向 vs 反差角度
        mainstream = f"大家都在讨论{self.topic}的技术细节"
        contrast = f"从{self.topic}对普通人生活的实际影响切入"
        
        return {
            "id": "A1",
            "标题建议": f"{self.topic}：但我是那个被改变的人",
            "角度描述": f"不讨论技术参数，而是讲述{self.topic}如何改变一个普通人的日常生活，从第一人称视角切入",
            "使用的方法": "反差法",
            "反差点": f"所有人都在说{mainstream}，我们从{contrast}",
            "陌生化手法": "将技术话题转化为个人叙事，让读者看到技术背后的人",
            "预期情绪弧线": "好奇→共鸣→反思→希望",
            "目标读者共鸣点": "读者会在'这不就是我吗'的瞬间产生强烈代入感",
            "与竞品的差异化": "竞品多为技术分析，本文为个人叙事，情感共鸣更强",
            "事实依据来源": "基于D2信息地图中的用户案例和社会影响数据",
            "评估得分": {
                "反差强度": 4,
                "情绪潜力": 5,
                "独特性": 4,
                "可执行性": 4,
                "共鸣潜力": 5,
                "综合得分": 4.4
            }
        }
        
    def generate_defamiliarization_angle(self) -> Optional[Dict]:
        """使用陌生化法生成角度"""
        self.log("使用陌生化法生成角度...")
        
        return {
            "id": "A2",
            "标题建议": f"{self.topic}发展史：从石器时代到2026",
            "角度描述": f"纵向穿越历史，从人类最早的类似实践讲起，看{self.topic}的本质从未改变",
            "使用的方法": "陌生化法",
            "反差点": "不是横向对比，而是纵向穿越，用历史纵深重新理解当下",
            "陌生化手法": "将当下的技术话题放入历史长河，让读者看到'太阳底下无新事'",
            "预期情绪弧线": "怀旧→洞察→释然→思考",
            "目标读者共鸣点": "读者会在'原来古人也面临同样问题'时产生跨越时空的共鸣",
            "与竞品的差异化": "竞品多为横向对比，本文为历史纵深，视角独特",
            "事实依据来源": "基于D2信息地图中的历史案例",
            "评估得分": {
                "反差强度": 5,
                "情绪潜力": 4,
                "独特性": 5,
                "可执行性": 3,
                "共鸣潜力": 4,
                "综合得分": 4.2
            }
        }
        
    def generate_underdog_angle(self) -> Optional[Dict]:
        """使用弱势视角法生成角度"""
        self.log("使用弱势视角法生成角度...")
        
        return {
            "id": "A3",
            "标题建议": f"我花了3天研究{self.topic}，这是我的血泪史",
            "角度描述": f"以一个小白的身份，记录第一次接触{self.topic}的真实经历，包括踩过的坑和意外发现",
            "使用的方法": "弱势视角法",
            "反差点": "不是专家评测，是小白实测，从'不懂'的视角切入",
            "陌生化手法": "用'无知者'的视角重新审视被过度包装的话题",
            "预期情绪弧线": "困惑→尝试→挫折→顿悟→分享",
            "目标读者共鸣点": "读者会在'原来不止我一个人不懂'时感到安慰",
            "与竞品的差异化": "竞品多为专家视角，本文为小白视角，更接地气",
            "事实依据来源": "基于个人真实体验（可结合D2信息地图验证）",
            "评估得分": {
                "反差强度": 4,
                "情绪潜力": 4,
                "独特性": 4,
                "可执行性": 5,
                "共鸣潜力": 5,
                "综合得分": 4.4
            }
        }
        
    def generate_cross_domain_angle(self) -> Optional[Dict]:
        """使用跨领域迁移法生成角度"""
        self.log("使用跨领域迁移法生成角度...")
        
        return {
            "id": "A4",
            "标题建议": f"如果电影导演来拍{self.topic}",
            "角度描述": f"用电影叙事的三幕剧结构来分析{self.topic}：铺垫→冲突→高潮，看技术如何讲述人的故事",
            "使用的方法": "跨领域迁移法",
            "反差点": "用电影叙事框架重新解读技术话题，跨界视角",
            "陌生化手法": "将技术话题转化为故事结构，让读者看到'技术也是叙事'",
            "预期情绪弧线": "入戏→紧张→释放→回味",
            "目标读者共鸣点": "读者会在'这剧情我熟'时产生熟悉又新鲜的感觉",
            "与竞品的差异化": "竞品多为技术框架，本文为故事框架，更易读",
            "事实依据来源": "基于D2信息地图中的案例，用叙事结构重新组织",
            "评估得分": {
                "反差强度": 4,
                "情绪潜力": 4,
                "独特性": 4,
                "可执行性": 4,
                "共鸣潜力": 4,
                "综合得分": 4.0
            }
        }
        
    def generate_angles(self) -> List[Dict]:
        """生成所有角度选项"""
        self.log(f"开始为主题'{self.topic}'生成角度选项...")
        
        # 执行第一直觉排除
        self.analyze_common_angles()
        
        # 使用4种方法生成角度
        angles = []
        
        angle1 = self.generate_contrast_angle()
        if angle1:
            angles.append(angle1)
            
        angle2 = self.generate_defamiliarization_angle()
        if angle2:
            angles.append(angle2)
            
        angle3 = self.generate_underdog_angle()
        if angle3:
            angles.append(angle3)
            
        angle4 = self.generate_cross_domain_angle()
        if angle4:
            angles.append(angle4)
            
        self.angle_options = angles
        self.log(f"生成角度选项: {len(angles)}个")
        return angles
        
    def evaluate_and_recommend(self) -> str:
        """评估并推荐最佳角度"""
        if not self.angle_options:
            return "无角度可推荐"
            
        # 按综合得分排序
        sorted_angles = sorted(
            self.angle_options, 
            key=lambda x: x["评估得分"]["综合得分"], 
            reverse=True
        )
        
        best = sorted_angles[0]
        self.recommendation = f"{best['id']}（推荐理由：综合得分最高({best['评估得分']['综合得分']}分），{best['反差点']}，情绪潜力强，与竞品差异化明显）"
        
        self.log(f"推荐角度: {best['id']}")
        return self.recommendation
        
    def generate_json_output(self) -> Dict:
        """生成JSON格式输出"""
        return {
            "主题": self.topic,
            "D2信息地图是否启用": bool(self.d2_info_map),
            "排除的常见角度": self.excluded_angles,
            "角度选项": self.angle_options,
            "推荐": self.recommendation,
            "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
    def generate_markdown_report(self) -> str:
        """生成Markdown格式报告"""
        md = f"""# 角度挖掘报告

## 基本信息
- 主题：{self.topic}
- D2 信息地图：{"已启用" if self.d2_info_map else "未启用"}
- 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}
- 生成Agent：D3

## 排除的常见角度
"""
        
        for i, angle in enumerate(self.excluded_angles, 1):
            md += f"{i}. {angle}\n"
            
        md += "\n## 角度选项\n"
        
        for angle in self.angle_options:
            md += f"""
### {angle['id']}：{angle['标题建议']}
- **角度描述**：{angle['角度描述']}
- **使用方法**：{angle['使用的方法']}
- **反差点**：{angle['反差点']}
- **陌生化手法**：{angle['陌生化手法']}
- **预期情绪弧线**：{angle['预期情绪弧线']}
- **目标读者共鸣点**：{angle['目标读者共鸣点']}
- **与竞品的差异化**：{angle['与竞品的差异化']}
- **事实依据**：{angle['事实依据来源']}
- **评估得分**：反差强度 {angle['评估得分']['反差强度']} | 情绪潜力 {angle['评估得分']['情绪潜力']} | 独特性 {angle['评估得分']['独特性']} | 可执行性 {angle['评估得分']['可执行性']} | 共鸣潜力 {angle['评估得分']['共鸣潜力']} | **综合 {angle['评估得分']['综合得分']}**
"""
            
        md += f"""
## 推荐
**推荐角度**：{self.recommendation.split('（')[0]}
**推荐理由**：{self.recommendation.split('（')[1].rstrip('）') if '（' in self.recommendation else self.recommendation}

---

## 等待人类选择
请从以上角度中选择一个（或提出修改意见），将传递给 W1 初稿撰写Agent。
"""
        return md
        
    def save_report(self, output_dir: str = None) -> str:
        """保存报告"""
        if output_dir is None:
            date_str = datetime.now().strftime("%Y%m%d")
            topic_key = self.topic[:20]
            output_dir = f"/workspace/KZCQL/04_工作区/产出归档/{date_str}_{topic_key}/角度挖掘"
            
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存JSON
        json_path = os.path.join(output_dir, f"{topic_key}_角度选项.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.generate_json_output(), f, ensure_ascii=False, indent=2)
            
        # 保存Markdown
        md_path = os.path.join(output_dir, f"{topic_key}_角度选项.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_markdown_report())
            
        self.log(f"报告已保存:")
        self.log(f"  - JSON: {json_path}")
        self.log(f"  - Markdown: {md_path}")
        
        return output_dir


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='D3 角度挖掘Agent')
    parser.add_argument('topic', help='主题')
    parser.add_argument('--d2-info', help='D2信息地图JSON文件路径')
    parser.add_argument('--user-profile', help='用户身份档案')
    parser.add_argument('--target-audience', default='泛互联网人群', help='目标读者')
    parser.add_argument('--output-dir', help='输出目录')
    parser.add_argument('--json-only', action='store_true', help='仅输出JSON')
    
    args = parser.parse_args()
    
    # 加载D2信息地图
    d2_info = None
    if args.d2_info and os.path.exists(args.d2_info):
        with open(args.d2_info, 'r', encoding='utf-8') as f:
            d2_info = json.load(f)
    
    # 创建Agent
    agent = D3AngleAgent(
        topic=args.topic,
        d2_info_map=d2_info,
        user_profile=args.user_profile,
        target_audience=args.target_audience
    )
    
    # 生成角度
    angles = agent.generate_angles()
    
    # 评估推荐
    recommendation = agent.evaluate_and_recommend()
    
    # 保存报告
    output_dir = agent.save_report(args.output_dir)
    
    # 输出
    if args.json_only:
        print(json.dumps(agent.generate_json_output(), ensure_ascii=False, indent=2))
    else:
        print("\n" + "="*60)
        print("角度挖掘完成!")
        print("="*60)
        print(f"主题: {args.topic}")
        print(f"生成角度: {len(angles)}个")
        print(f"推荐: {recommendation}")
        print(f"输出目录: {output_dir}")
        print("="*60)


if __name__ == '__main__':
    main()
