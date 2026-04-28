#!/bin/bash
# TaskNya 快捷监控启动脚本

PYTHON_BIN="${PYTHON_BIN:-python3}"
CONFIG_DIR="configs"
DEFAULT_CONFIG="$CONFIG_DIR/default.yaml"

usage() {
    echo "用法: $0 [--config <配置文件>] [--trigger [--message <消息>]]"
    echo ""
    echo "选项:"
    echo "  --config <path>    指定配置文件路径"
    echo "  --trigger          跳过检测，直接触发通知"
    echo "  --message <text>   触发时附带的自定义消息"
    echo ""
    echo "无参数运行时将列出已保存的配置供选择。"
}

select_config() {
    configs=($(ls "$CONFIG_DIR"/*.yaml 2>/dev/null))
    
    if [ ${#configs[@]} -eq 0 ]; then
        echo "未找到配置文件，使用默认配置。"
        echo "$DEFAULT_CONFIG"
        return
    fi
    
    echo "可用配置文件："
    for i in "${!configs[@]}"; do
        echo "  [$((i+1))] ${configs[$i]}"
    done
    echo ""
    read -p "选择配置 [1-${#configs[@]}] (默认 1): " choice
    choice=${choice:-1}
    
    idx=$((choice - 1))
    if [ $idx -ge 0 ] && [ $idx -lt ${#configs[@]} ]; then
        echo "${configs[$idx]}"
    else
        echo "无效选择，使用默认配置。"
        echo "$DEFAULT_CONFIG"
    fi
}

print_summary() {
    local config_file="$1"
    echo "========================================"
    echo "  TaskNya 监控启动"
    echo "========================================"
    echo "  配置文件: $config_file"
    echo "========================================"
}

# 解析参数
CONFIG=""
TRIGGER=""
MESSAGE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --config)
            CONFIG="$2"
            shift 2
            ;;
        --trigger)
            TRIGGER="--trigger"
            shift
            ;;
        --message)
            MESSAGE="--message $2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            usage
            exit 1
            ;;
    esac
done

# 如果没有指定配置且不是触发模式，交互选择
if [ -z "$CONFIG" ] && [ -z "$TRIGGER" ]; then
    CONFIG=$(select_config)
fi

# 构建命令
CMD="$PYTHON_BIN main.py"
if [ -n "$CONFIG" ]; then
    CMD="$CMD --config $CONFIG"
fi
if [ -n "$TRIGGER" ]; then
    CMD="$CMD $TRIGGER"
fi
if [ -n "$MESSAGE" ]; then
    CMD="$CMD $MESSAGE"
fi

# 打印摘要并启动
if [ -n "$CONFIG" ]; then
    print_summary "$CONFIG"
fi

echo "执行: $CMD"
echo ""
exec $CMD
