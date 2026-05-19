#!/bin/bash
# D2 调研Agent 独立运行脚本
# 用法: ./run_d2.sh "调研主题" [领域偏好] [排除领域]

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 检查参数
if [ $# -lt 1 ]; then
    echo "用法: $0 <调研主题> [领域偏好] [排除领域]"
    echo ""
    echo "示例:"
    echo "  $0 \"AI写作工具对比\""
    echo "  $0 \"远程办公的未来\" \"商业 历史\""
    echo "  $0 \"短视频创作\" \"电影 喜剧\" \"自然科学\""
    echo ""
    echo "测试用例:"
    echo "  $0 --test"
    exit 1
fi

TOPIC="$1"
DOMAIN_PREF="${2:-}"
EXCLUDE_DOMAIN="${3:-}"

# 构建参数
ARGS="\"$TOPIC\""

if [ -n "$DOMAIN_PREF" ]; then
    ARGS="$ARGS --domain-preference $DOMAIN_PREF"
fi

if [ -n "$EXCLUDE_DOMAIN" ]; then
    ARGS="$ARGS --exclude-domain $EXCLUDE_DOMAIN"
fi

# 运行D2 Agent
echo "========================================"
echo "启动 D2 调研Agent"
echo "========================================"
echo "主题: $TOPIC"
[ -n "$DOMAIN_PREF" ] && echo "领域偏好: $DOMAIN_PREF"
[ -n "$EXCLUDE_DOMAIN" ] && echo "排除领域: $EXCLUDE_DOMAIN"
echo "========================================"
echo ""

python3 "$SCRIPT_DIR/D2_research_agent.py" $ARGS

echo ""
echo "========================================"
echo "调研完成!"
echo "========================================"
