# 使用Python 3.8作为基础镜像
FROM python:3.8-slim

# 设置工作目录
WORKDIR /app

# 安装基础编辑器
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    nano && \
    rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . /app

# 安装项目依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建必要的目录
RUN mkdir -p /app/logs /app/configs /app/monitor_targets

# 设置环境变量
ENV FLASK_APP=webui.py
ENV FLASK_RUN_PORT=5000
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "webui.py"] 