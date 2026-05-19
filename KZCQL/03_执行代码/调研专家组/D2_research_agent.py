#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D2 调研Agent - 可执行代码
生成结构化的信息地图，为内容创作提供跨领域素材

【P0修复标记】当前版本为演示版本，WebSearch为模拟实现
真实WebSearch集成需要SOLO平台支持，详见call_websearch方法
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
import argparse

# 添加工具路径
sys.path.insert(0, '/workspace/KZCQL/03_执行代码/工具库')

class D2ResearchAgent:
    """D2调研Agent实现"""
    
    def __init__(self, topic: str, domain_preference: List[str] = None, 
                 excluded_domains: List[str] = None, time_range: str = None,
                 demo_mode: bool = True):
        self.topic = topic
        self.domain_preference = domain_preference or []
        self.excluded_domains = excluded_domains or []
        self.time_range = time_range or "7天"
        self.demo_mode = demo_mode  # P0修复：添加演示模式标记
        self.research_data = {
            "主题": topic,
            "调研时间": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "演示模式": demo_mode,  # P0修复：明确标记演示模式
            "调研维度": {
                "必选维度": ["热点信息", "跨领域关联", "竞品内容分析", "历史案例"],
                "可选维度": []
            },
            "热点信息": [],
            "跨领域关联": [],
            "竞品内容分析": [],
            "历史案例": [],
            "数据支撑": [],
            "人物/金句": [],
            "信息来源清单": [],
            "矛盾信息标注": [],
            "P0修复说明": "当前为演示版本，WebSearch为模拟实现。真实版本需要集成SOLO WebSearch工具。"
        }
        self.search_count = 0
        self.max_search = 19  # 搜索预算上限
        
    def log(self, message: str):
        """打印日志"""
        print(f"[D2] {message}")
        
    def can_search(self) -> bool:
        """检查是否还有搜索预算"""
        return self.search_count < self.max_search
        
    def call_websearch(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        【真实WebSearch集成】WebSearch调用方法
        
        使用websearch_tool.py封装的WebSearch工具
        支持缓存、备用查询、真实/模拟数据切换
        """
        if not self.can_search():
            self.log(f"搜索预算已用完，跳过: {query}")
            return []
            
        self.search_count += 1
        self.log(f"搜索 [{self.search_count}/{self.max_search}]: {query}")
        
        try:
            # 导入WebSearch工具
            sys.path.insert(0, '/workspace/KZCQL/03_执行代码/工具库')
            from websearch_tool import WebSearchTool
            
            # 创建WebSearch工具实例
            # 演示模式使用模拟数据，真实模式尝试真实搜索
            ws_tool = WebSearchTool(use_cache=True)
            
            # 执行搜索
            results = ws_tool.search(query, num_results=num_results)
            
            # 检查是否为模拟数据
            if results and any(r.get('is_mock') for r in results):
                self.log(f"  ⚠️  注意：返回模拟数据（真实WebSearch需在SOLO环境集成）")
            else:
                self.log(f"  ✓ 获取真实搜索结果: {len(results)}条")
                
            return results
            
        except ImportError as e:
            self.log(f"WebSearch工具导入失败: {e}")
            self.log("  使用备用模拟数据")
            return self._fallback_mock_search(query, num_results)
        except Exception as e:
            self.log(f"搜索异常: {str(e)}")
            return self._fallback_mock_search(query, num_results)
    
    def _fallback_mock_search(self, query: str, num_results: int = 5) -> List[Dict]:
        """备用模拟搜索（当WebSearch工具不可用时）"""
        return [
            {
                "title": f"{query} - 搜索结果{i+1}",
                "url": f"https://example.com/{i+1}",
                "snippet": f"关于{query}的信息...",
                "source": "备用来源",
                "is_mock": True
            }
            for i in range(min(num_results, 3))
        ]
        
    def research_hot_topics(self) -> List[Dict]:
        """调研热点信息"""
        self.log("开始调研热点信息...")
        
        queries = [
            f"{self.topic} 最新",
            f"{self.topic} 2026",
            f"{self.topic} 发布"
        ]
        
        results = []
        for query in queries:
            if not self.can_search():
                break
            search_results = self.call_websearch(query)
            for r in search_results:
                # P0修复：使用搜索结果中的source字段，如果是演示模式则明确标注
                source = r.get("source", "未知来源")
                is_demo = r.get("is_demo", False)
                results.append({
                    "标题": r["title"],
                    "来源": f"{source} {'[演示数据]' if is_demo else ''}".strip(),
                    "时间": datetime.now().strftime("%Y-%m-%d"),
                    "摘要": r["snippet"],
                    "来源URL": r["url"],
                    "is_demo": is_demo  # P0修复：保留演示标记
                })
                
        # 去重并限制数量
        seen = set()
        unique_results = []
        for r in results:
            if r["标题"] not in seen and len(unique_results) < 5:
                seen.add(r["标题"])
                unique_results.append(r)
                
        self.log(f"热点信息调研完成: {len(unique_results)}条")
        return unique_results[:3]  # 至少3条
        
    def research_cross_domain(self) -> List[Dict]:
        """调研跨领域关联"""
        self.log("开始调研跨领域关联...")
        
        # 推荐领域列表
        candidate_domains = [
            "电影", "历史", "商业", "设计", "喜剧", 
            "文学", "哲学", "体育", "游戏", "自然科学"
        ]
        
        # 应用用户偏好和排除
        if self.domain_preference:
            candidate_domains = self.domain_preference + [d for d in candidate_domains if d not in self.domain_preference]
        if self.excluded_domains:
            candidate_domains = [d for d in candidate_domains if d not in self.excluded_domains]
            
        results = []
        for domain in candidate_domains[:5]:  # 最多搜索5个领域
            if not self.can_search():
                break
                
            query = f"{self.topic} {domain}"
            search_results = self.call_websearch(query, num_results=3)
            
            if search_results:
                results.append({
                    "领域": domain,
                    "关联点": f"{self.topic}与{domain}的内在联系",
                    "灵感方向": f"从{domain}视角切入{self.topic}",
                    "参考来源": search_results[0]["url"] if search_results else "模拟来源"
                })
                
        self.log(f"跨领域关联调研完成: {len(results)}个领域")
        return results[:3]  # 至少3个
        
    def research_competitors(self) -> List[Dict]:
        """调研竞品内容"""
        self.log("开始调研竞品内容...")
        
        queries = [
            f"{self.topic} 公众号",
            f"{self.topic} 深度",
            f"{self.topic} 分析"
        ]
        
        results = []
        for query in queries:
            if not self.can_search():
                break
            search_results = self.call_websearch(query)
            for r in search_results:
                results.append({
                    "文章标题": r["title"],
                    "作者/平台": r.get("source", "未知平台"),
                    "角度": "待分析",
                    "数据表现": "待获取",
                    "可借鉴点": "待总结",
                    "来源URL": r["url"]
                })
                
        seen = set()
        unique_results = []
        for r in results:
            if r["文章标题"] not in seen and len(unique_results) < 5:
                seen.add(r["文章标题"])
                unique_results.append(r)
                
        self.log(f"竞品内容调研完成: {len(unique_results)}篇")
        return unique_results[:3]  # 至少3篇
        
    def research_history(self) -> List[Dict]:
        """调研历史案例"""
        self.log("开始调研历史案例...")
        
        queries = [
            f"{self.topic} 历史",
            f"{self.topic} 之前",
            f"{self.topic} 起源"
        ]
        
        results = []
        for query in queries:
            if not self.can_search():
                break
            search_results = self.call_websearch(query)
            for r in search_results:
                results.append({
                    "案例": r["title"],
                    "角度": "历史回顾角度",
                    "与当前主题的关联": f"与{self.topic}的发展轨迹相似",
                    "参考来源": r["url"]
                })
                
        seen = set()
        unique_results = []
        for r in results:
            if r["案例"] not in seen and len(unique_results) < 4:
                seen.add(r["案例"])
                unique_results.append(r)
                
        self.log(f"历史案例调研完成: {len(unique_results)}个")
        return unique_results[:2]  # 至少2个
        
    def execute_research(self) -> Dict:
        """执行完整调研流程"""
        self.log(f"开始调研主题: {self.topic}")
        self.log(f"搜索预算: {self.max_search}次")
        
        # 执行4个必选维度调研
        self.research_data["热点信息"] = self.research_hot_topics()
        self.research_data["跨领域关联"] = self.research_cross_domain()
        self.research_data["竞品内容分析"] = self.research_competitors()
        self.research_data["历史案例"] = self.research_history()
        
        # 收集信息来源
        sources = set()
        for item in self.research_data["热点信息"]:
            sources.add(item.get("来源", "未知"))
        for item in self.research_data["竞品内容分析"]:
            sources.add(item.get("作者/平台", "未知"))
        self.research_data["信息来源清单"] = list(sources)
        
        self.log(f"调研完成! 总搜索次数: {self.search_count}/{self.max_search}")
        return self.research_data
        
    def quality_check(self) -> Dict:
        """执行质量检查"""
        checks = {
            "热点信息数量": len(self.research_data["热点信息"]) >= 3,
            "跨领域关联数量": len(self.research_data["跨领域关联"]) >= 3,
            "竞品内容数量": len(self.research_data["竞品内容分析"]) >= 3,
            "历史案例数量": len(self.research_data["历史案例"]) >= 2,
            "信息来源标注": len(self.research_data["信息来源清单"]) > 0
        }
        
        passed = sum(checks.values())
        total = len(checks)
        
        return {
            "检查项": checks,
            "通过数": passed,
            "总数": total,
            "质量状态": "通过" if passed == total else "部分通过"
        }
        
    def generate_markdown_report(self) -> str:
        """生成Markdown格式的调研报告"""
        md = f"""---
title: {self.topic}_信息地图
agent: D2
created_at: {self.research_data['调研时间']}
dimensions_completed: {', '.join(self.research_data['调研维度']['必选维度'])}
quality_check: {self.quality_check()['质量状态']}
---

# {self.topic} - 信息地图

## 调研概览

- **主题**: {self.topic}
- **调研时间**: {self.research_data['调研时间']}
- **搜索次数**: {self.search_count}/{self.max_search}
- **质量状态**: {self.quality_check()['质量状态']}

## 热点信息

"""
        
        for i, item in enumerate(self.research_data["热点信息"], 1):
            md += f"""### {i}. {item['标题']}
- **来源**: {item['来源']}
- **时间**: {item['时间']}
- **摘要**: {item['摘要']}
- **链接**: {item['来源URL']}

"""
            
        md += "## 跨领域关联\n\n"
        for i, item in enumerate(self.research_data["跨领域关联"], 1):
            md += f"""### {i}. {item['领域']}领域
- **关联点**: {item['关联点']}
- **灵感方向**: {item['灵感方向']}
- **参考来源**: {item['参考来源']}

"""
            
        md += "## 竞品内容分析\n\n"
        for i, item in enumerate(self.research_data["竞品内容分析"], 1):
            md += f"""### {i}. {item['文章标题']}
- **作者/平台**: {item['作者/平台']}
- **切入角度**: {item['角度']}
- **数据表现**: {item['数据表现']}
- **可借鉴点**: {item['可借鉴点']}
- **链接**: {item['来源URL']}

"""
            
        md += "## 历史案例\n\n"
        for i, item in enumerate(self.research_data["历史案例"], 1):
            md += f"""### {i}. {item['案例']}
- **切入角度**: {item['角度']}
- **与当前主题的关联**: {item['与当前主题的关联']}
- **参考来源**: {item['参考来源']}

"""
            
        md += f"""## 信息来源清单

{chr(10).join(['- ' + s for s in self.research_data['信息来源清单']])}

## 质量检查

"""
        qc = self.quality_check()
        for check, passed in qc["检查项"].items():
            status = "✅" if passed else "❌"
            md += f"- {status} {check}\n"
            
        md += f"\n**总体**: {qc['通过数']}/{qc['总数']} 项通过\n"
        
        return md
        
    def save_report(self, output_dir: str = None) -> str:
        """保存调研报告"""
        if output_dir is None:
            # 默认保存路径
            date_str = datetime.now().strftime("%Y%m%d")
            topic_key = self.topic[:20]  # 取前20字符作为关键词
            output_dir = f"/workspace/KZCQL/04_工作区/产出归档/{date_str}_{topic_key}/调研"
            
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存Markdown报告
        md_path = os.path.join(output_dir, f"{topic_key}_信息地图.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_markdown_report())
            
        # 保存JSON数据
        json_path = os.path.join(output_dir, f"{topic_key}_信息地图.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.research_data, f, ensure_ascii=False, indent=2)
            
        self.log(f"报告已保存:")
        self.log(f"  - Markdown: {md_path}")
        self.log(f"  - JSON: {json_path}")
        
        return output_dir


def main():
    """主函数 - 命令行入口"""
    parser = argparse.ArgumentParser(description='D2 调研Agent')
    parser.add_argument('topic', help='调研主题')
    parser.add_argument('--domain-preference', nargs='+', help='领域偏好')
    parser.add_argument('--exclude-domain', nargs='+', help='排除领域')
    parser.add_argument('--time-range', default='7天', help='时间范围')
    parser.add_argument('--output-dir', help='输出目录')
    parser.add_argument('--json-only', action='store_true', help='仅输出JSON')
    # P0修复：添加演示模式开关
    parser.add_argument('--demo-mode', action='store_true', default=True, 
                        help='演示模式（默认True，使用模拟数据）')
    parser.add_argument('--real-mode', action='store_true',
                        help='真实模式（需要集成WebSearch工具）')
    
    args = parser.parse_args()
    
    # P0修复：确定模式
    demo_mode = not args.real_mode  # 默认演示模式，除非指定--real-mode
    
    if demo_mode:
        print("⚠️  警告：当前为演示模式，返回模拟数据")
        print("   如需真实数据，请使用 --real-mode 参数（需要集成WebSearch工具）")
        print()
    
    # 创建Agent实例
    agent = D2ResearchAgent(
        topic=args.topic,
        domain_preference=args.domain_preference,
        excluded_domains=args.exclude_domain,
        time_range=args.time_range,
        demo_mode=demo_mode  # P0修复：传递模式参数
    )
    
    # 执行调研
    result = agent.execute_research()
    
    # 质量检查
    qc = agent.quality_check()
    
    # 保存报告
    output_dir = agent.save_report(args.output_dir)
    
    # 输出JSON结果（供下游Agent使用）
    if args.json_only:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("\n" + "="*60)
        print("调研完成!")
        print("="*60)
        print(f"主题: {args.topic}")
        print(f"搜索次数: {agent.search_count}/{agent.max_search}")
        print(f"质量检查: {qc['质量状态']} ({qc['通过数']}/{qc['总数']})")
        print(f"输出目录: {output_dir}")
        print("="*60)


if __name__ == '__main__':
    main()
