# WasAI (哇塞！)

面向个人创作者的短剧出海助手，帮助你实现创意灵感的海外变现。

## 功能特性

- **视频上传**: 支持 MP4、AVI、MOV、MKV、WebM 等格式
- **语音识别 (ASR)**: 集成 OpenAI Whisper API，自动识别视频语音
- **字幕翻译**: 支持多语种翻译，支持 OpenAI 等翻译服务
- **AI 配音 (TTS)**: 使用 OpenAI TTS 等服务生成自然语音
- **视频导出**: 合成配音音频，支持字幕烧录

## 技术栈

- **前端**: Vue 3 + Vite + Element Plus
- **后端**: FastAPI + SQLAlchemy + SQLite
- **AI 服务**: OpenAI (Whisper, GPT, TTS)

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 16+
- ffmpeg

### 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
```

### 启动服务

```bash
# 方式一：使用启动脚本
./start.sh

# 方式二：手动启动
# 1. 启动后端
cd backend
uvicorn main:app --reload

# 2. 启动前端（新终端）
cd frontend
npm run dev
```

访问 http://localhost:5173 开始使用。

## 项目结构

```
wasai/
├── backend/              # 后端代码
│   ├── api/             # API 路由
│   ├── models/          # 数据模型
│   ├── schemas/         # Pydantic 模型
│   ├── services/        # 业务逻辑
│   ├── utils/           # 工具函数
│   ├── data/            # 数据库文件
│   ├── uploads/         # 上传的视频文件
│   └── main.py          # FastAPI 入口
├── frontend/            # 前端代码
│   ├── src/
│   │   ├── api/        # API 调用
│   │   ├── components/ # Vue 组件
│   │   ├── stores/     # Pinia Store
│   │   ├── views/      # 页面视图
│   │   └── router/     # 路由配置
│   └── package.json
├── requirements.txt     # Python 依赖
└── start.sh            # 启动脚本
```

## 配置说明

在设置页面配置以下 API 密钥：

1. **OpenAI API Key**: 用于语音识别、翻译和语音合成
2. 可选配置 Base URL: 如果使用第三方 API 代理

## 使用流程

1. **创建项目**: 输入项目名称，选择源语言和目标语言
2. **上传视频**: 拖拽或点击上传视频文件
3. **语音识别**: 点击"开始识别"，系统自动提取字幕
4. **翻译字幕**: 在字幕编辑器中编辑或自动翻译
5. **生成配音**: 点击"生成配音"，AI 合成目标语音
6. **导出视频**: 合成最终视频，可选择烧录字幕

## License

Apache License 2.0
