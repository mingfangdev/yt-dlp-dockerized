# 1. 使用官方的轻量级 Python 3.11 镜像作为基础
FROM python:3.11-slim

# 2. 设置容器内的工作目录为 /app
WORKDIR /app

# 3. 更新系统包并安装 ffmpeg (yt-dlp 合并音视频需要它)
# 添加重试机制和清理缓存
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 4. 复制依赖文件到容器中
COPY requirements.txt .

# 5. 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 6. 复制项目中的所有文件到容器的 /app 目录
COPY . .

# 7. 暴露 8000 端口，以便外部可以访问我们的 API
EXPOSE 8000

# 8. 容器启动时运行的命令：使用 python -m uvicorn 启动 main.py 中的 app
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]