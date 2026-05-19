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
    exit 1
fi

TOPIC="$1"
shift

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

echo "========================================"
echo "启动 D3 角度挖掘Agent"
echo "========================================"
echo "主题: $TOPIC"
[ -n "$D2_INFO" ] && echo "D2信息地图: $D2_INFO"
echo "========================================"
echo ""

ARGS="\"$TOPIC\""
[ -n "$D2_INFO" ] && ARGS="$ARGS --d2-info $D2_INFO"

python3 "$SCRIPT_DIR/D3_angle_agent.py" $ARGS

echo ""
echo "========================================"
echo "角度挖掘完成!"
echo "========================================"
