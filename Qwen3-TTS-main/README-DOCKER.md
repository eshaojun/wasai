# Qwen3-TTS Docker 部署指南

本项目提供完整的 Docker 部署方案，包含 FastAPI 接口服务，返回音频文件的 base64 编码。

## 项目结构

```
.
├── docker-compose.yml          # Docker Compose 配置
├── Dockerfile                  # Docker 镜像构建文件
├── requirements-docker.txt     # Python 依赖
├── download_models.py          # 模型下载脚本（使用 ModelScope）
├── api.py                      # FastAPI 服务主文件
├── test_api.py                 # API 测试脚本
├── .dockerignore               # Docker 构建忽略文件
└── qwen_tts/                   # Qwen3-TTS 源代码
```

## 支持模型

| 模型 | 功能 | 说明 |
|------|------|------|
| `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice` | 自定义语音 | 支持9种预设音色和风格控制 |
| `Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign` | 语音设计 | 通过自然语言描述设计声音 |
| `Qwen/Qwen3-TTS-12Hz-1.7B-Base` | 语音克隆 | 3秒快速声音克隆 |
| `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice` | 轻量自定义 | 0.6B 轻量版 |
| `Qwen/Qwen3-TTS-12Hz-0.6B-Base` | 轻量克隆 | 0.6B 轻量克隆版 |

默认使用 `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice` 模型。

## 快速开始

### 1. 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Docker Runtime (使用 GPU 时需要)

### 2. 安装 NVIDIA Docker Runtime

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# 验证安装
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### 3. 构建并启动服务

```bash
# 使用默认模型 (1.7B CustomVoice)
docker-compose up -d --build

# 使用其他模型，修改 docker-compose.yml 中的 MODEL_NAME 或通过环境变量指定
MODEL_NAME=Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign docker-compose up -d --build
```

### 4. 查看日志

```bash
# 查看构建和运行日志
docker-compose logs -f

# 等待模型加载完成（首次启动可能需要几分钟）
```

### 5. 测试 API

```bash
# 健康检查
curl http://localhost:8000/health

# 获取模型信息
curl http://localhost:8000/model/info

# 语音合成测试
curl -X POST http://localhost:8000/tts/custom-voice \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，这是Qwen3-TTS语音合成测试。",
    "speaker": "Vivian",
    "language": "Chinese"
  }'

# 或使用 Python 测试脚本
pip install requests
python test_api.py
```

## API 文档

启动服务后，访问 http://localhost:8000/docs 查看交互式 API 文档（Swagger UI）。

### 主要接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/model/info` | GET | 模型信息 |
| `/tts/custom-voice` | POST | 自定义语音合成 |
| `/tts/voice-design` | POST | 语音设计合成 |
| `/tts/voice-clone` | POST | 语音克隆合成 |
| `/tts/batch/custom-voice` | POST | 批量自定义语音合成 |

### 请求示例

#### 自定义语音合成

```json
POST /tts/custom-voice
{
  "text": "你好，这是测试语音。",
  "speaker": "Vivian",
  "language": "Chinese",
  "instruct": "用温柔的语气说"
}
```

**响应格式：**

```json
{
  "success": true,
  "audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA...",
  "sample_rate": 24000,
  "message": "语音合成成功",
  "duration_ms": 2345,
  "process_time_ms": 1250
}
```

#### 语音设计合成

```json
POST /tts/voice-design
{
  "text": "哥哥，你回来啦！",
  "instruct": "体现撒娇稚嫩的萝莉女声，音调偏高",
  "language": "Chinese"
}
```

#### 语音克隆合成

```json
POST /tts/voice-clone
{
  "text": "这是克隆后的语音。",
  "ref_audio_base64": "<base64编码的参考音频>",
  "ref_text": "这是参考音频的文本内容",
  "language": "Chinese",
  "x_vector_only_mode": false
}
```

## 支持的说话人

| 说话人 | 描述 | 母语 |
|--------|------|------|
| Vivian | 明亮、略带尖锐的年轻女声 | 中文 |
| Serena | 温暖、温柔的年轻女声 | 中文 |
| Uncle_Fu | 经验丰富、低沉醇厚的男声 | 中文 |
| Dylan | 年轻北京男声，音色清晰自然 | 中文（北京方言） |
| Eric | 活泼成都男声，略带沙哑的明亮感 | 中文（四川方言） |
| Ryan | 富有节奏感的动感男声 | 英文 |
| Aiden | 阳光美式男声，中音清晰 | 英文 |
| Ono_Anna | 俏皮日本女声，音色轻快灵动 | 日语 |
| Sohee | 温暖韩语女声，情感丰富 | 韩语 |

## 配置选项

### 修改模型

编辑 `docker-compose.yml`：

```yaml
services:
  qwen3-tts-api:
    build:
      args:
        MODEL_NAME: Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign  # 修改这里
```

或通过环境变量：

```yaml
environment:
  - MODEL_NAME=Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign
```

### 使用 CPU 运行

如果没有 GPU，需要修改 `Dockerfile`：

```dockerfile
# 注释掉 CUDA 基础镜像
FROM python:3.10-slim

# 移除 GPU 相关配置
# runtime: nvidia
```

### 持久化模型

模型已预下载到镜像中，如需挂载外部模型目录：

```yaml
volumes:
  - /path/to/local/models:/app/models
```

## 故障排查

### 1. 构建失败 - 内存不足

```bash
# 增加 Docker 构建内存限制
docker build --memory=16g --memory-swap=16g -t qwen3-tts-api .
```

### 2. GPU 不可用

```bash
# 检查 NVIDIA Docker Runtime
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# 如果失败，检查 nvidia-container-toolkit 安装
```

### 3. 模型下载失败

```bash
# 检查网络连接
# ModelScope 在国内访问更稳定，如需使用代理：
docker-compose build --build-arg HTTP_PROXY=http://proxy:port
```

### 4. 服务启动慢

首次启动需要加载模型到 GPU 内存，可能需要 1-3 分钟。查看日志确认状态：

```bash
docker-compose logs -f
```

## 性能优化

1. **使用 FlashAttention**（已默认启用）
2. **调整 batch size** 进行批量合成
3. **使用更快的 GPU**（推荐 A100/V100/RTX 3090 以上）

## 许可证

遵循原项目 Apache-2.0 许可证。
