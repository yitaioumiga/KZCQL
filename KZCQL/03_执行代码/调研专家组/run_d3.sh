#!/bin/bash
# D3 角度挖掘Agent 独立运行脚本
# 用法: ./run_d3.sh "主题" [--d2-info 路径]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ $# -lt 1 ]; then
    echo "用法: $0 <主题> [--d2-info D2信息地图JSON路径]"
    echo ""
    echo "示例:"
    echo "  $0 \"AI写作工具对比\""
    echo "  $0 \"远程办公的未来\" --d2-info /path/to/info_map.json"
    echo ""
    echo "注意: 如果不指定--d2-info，脚本会自动查找最新的D2输出"
    exit 1
fi

TOPIC="$1"
shift

# P0修复：自动查找D2输出
default_d2_dir="/workspace/KZCQL/04_工作区/产出归档"
auto_d2_info=""

# 解析可选参数
D2_INFO=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --d2-info)
            D2_INFO="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# P0修复：如果没有指定D2_INFO，自动查找
if [ -z "$D2_INFO" ]; then
    # 查找最新的D2输出
    topic_key="${TOPIC:0:20}"
    # 查找匹配主题的目录
    latest_dir=$(find "$default_d2_dir" -maxdepth 1 -type d -name "*${topic_key}*" 2>/dev/null | sort -r | head -1)
    
    if [ -n "$latest_dir" ]; then
        potential_d2_info="${latest_dir}/调研/${topic_key}_信息地图.json"
        if [ -f "$potential_d2_info" ]; then
            auto_d2_info="$potential_d2_info"
            echo "✓ 自动找到D2信息地图: $auto_d2_info"
        fi
    fi
fi

# 使用指定的或自动找到的D2_INFO
D2_INFO_TO_USE="${D2_INFO:-$auto_d2_info}"

echo "========================================"
echo "启动 D3 角度挖掘Agent"
echo "========================================"
echo "主题: $TOPIC"
if [ -n "$D2_INFO_TO_USE" ]; then
    echo "D2信息地图: $D2_INFO_TO_USE"
else
    echo "D2信息地图: 未提供（将基于主题直接生成角度）"
fi
echo "========================================"
echo ""

ARGS="\"$TOPIC\""
[ -n "$D2_INFO_TO_USE" ] && ARGS="$ARGS --d2-info $D2_INFO_TO_USE"

python3 "$SCRIPT_DIR/D3_angle_agent.py" $ARGS

echo ""
echo "========================================"
echo "角度挖掘完成!"
echo "========================================"
