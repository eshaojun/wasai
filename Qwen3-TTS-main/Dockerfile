# Qwen3-TTS FastAPI Docker 镜像
# 使用 CUDA 基础镜像
FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV HF_HOME=/app/models/.cache
ENV TRANSFORMERS_OFFLINE=0
ENV HF_HUB_ENABLE_HF_TRANSFER=0

# 构建参数 - 默认模型
ARG MODEL_NAME=Qwen3-TTS-12Hz-0.6B-CustomVoice
ENV MODEL_NAME=${MODEL_NAME}

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    wget \
    curl \
    libsndfile1 \
    libsox-fmt-all \
    sox \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 设置 Python3 为默认 python
RUN ln -s /usr/bin/python3 /usr/bin/python

# 升级 pip
RUN python -m pip install --upgrade pip setuptools wheel

# 创建工作目录
WORKDIR /app

# 安装 PyTorch (CUDA 12.1 版本)
RUN pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121

# 先复制 requirements.txt 并安装依赖（利用 Docker 缓存层）
COPY requirements-docker.txt /app/requirements-docker.txt
RUN pip install -r /app/requirements-docker.txt

# 复制项目代码
COPY qwen_tts /app/qwen_tts
COPY pyproject.toml /app/pyproject.toml
COPY README.md /app/README.md

# 安装 qwen-tts 包（本地安装）
RUN pip install -e .

# 尝试安装 flash-attn（可选，失败也不影响构建）
RUN pip install flash-attn --no-build-isolation || echo "FlashAttention installation failed, continuing without it"

# 创建模型目录
RUN mkdir -p /app/models

# 下载模型文件到镜像中
# 使用 huggingface_hub 下载模型，支持从镜像站点下载
COPY download_models.py /app/download_models.py
RUN python /app/download_models.py --model_name ${MODEL_NAME} --cache_dir /app/models

# 下载后设置为离线模式
ENV TRANSFORMERS_OFFLINE=1
ENV HF_HUB_OFFLINE=1

# 复制 FastAPI 应用代码
COPY api.py /app/api.py 


# 暴露端口
EXPOSE 8003

# 启动命令（临时注释掉，手动进入容器后运行）
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8003", "--workers", "1"]

# 保持容器运行，方便手动进入处理模型
# CMD ["tail", "-f", "/dev/null"]
