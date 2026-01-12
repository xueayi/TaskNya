# 使用 Python 3.8 作为基础镜像
FROM python:3.8-slim

# 设置工作目录
WORKDIR /app

# 安装基础工具
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    nano && \
    rm -rf /var/lib/apt/lists/*

# 复制依赖文件（利用缓存层）
COPY requirements.txt /app/

# 安装项目依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . /app

# 创建必要的目录
RUN mkdir -p /app/logs /app/configs /app/monitor_targets

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# TaskNya 配置环境变量
ENV TASKNYA_HOST=0.0.0.0
ENV TASKNYA_PORT=5000
ENV TASKNYA_DEBUG=0

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/')" || exit 1

# 启动命令
CMD ["python", "webui.py"]