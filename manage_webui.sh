#!/bin/bash

# --- 配置区 ---
APP_NAME="webui.py"
LOG_FILE="output.log"
PYTHON_BIN="python3"

# --- 逻辑处理 ---

# 获取进程 ID (PID)
get_pid() {
    echo $(ps -ef | grep "$APP_NAME" | grep -v grep | awk '{print $2}')
}

start() {
    pid=$(get_pid)
    if [ -n "$pid" ]; then
        echo "警告: $APP_NAME 已经在运行中 (PID: $pid)"
    else
        echo "正在启动 $APP_NAME..."
        # 核心启动命令
        nohup $PYTHON_BIN $APP_NAME > $LOG_FILE 2>&1 &
        sleep 1
        new_pid=$(get_pid)
        if [ -n "$new_pid" ]; then
            echo "启动成功！PID: $new_pid"
            echo "日志输出位置: $LOG_FILE"
        else
            echo "启动失败，请检查日志。"
        fi
    fi
}

stop() {
    pid=$(get_pid)
    if [ -z "$pid" ]; then
        echo "提示: $APP_NAME 当前未运行。"
    else
        echo "正在停止 PID: $pid ..."
        kill $pid
        sleep 2
        # 再次确认是否停止成功
        pid=$(get_pid)
        if [ -z "$pid" ]; then
            echo "服务已停止。"
        else
            echo "强制停止中..."
            kill -9 $pid
            echo "服务已强制结束。"
        fi
    fi
}

status() {
    pid=$(get_pid)
    if [ -n "$pid" ]; then
        echo "状态: $APP_NAME 正在运行 (PID: $pid)"
        echo "最近 5 行日志:"
        tail -n 5 $LOG_FILE
    else
        echo "状态: $APP_NAME 未运行"
    fi
}

# 根据参数执行
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    status)
        status
        ;;
    restart)
        stop
        start
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status}"
        exit 1
esac