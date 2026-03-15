#!/usr/bin/env python3
"""
Qwen3-TTS FastAPI 接口服务
提供语音合成服务，返回音频文件的 base64 编码
"""
import base64
import io
import os
import time
from contextlib import asynccontextmanager
from typing import List, Optional, Union

import numpy as np
import soundfile as sf
import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 全局模型实例
model = None
model_config = {}


def numpy_to_base64(wav: np.ndarray, sample_rate: int) -> str:
    """
    将 numpy 音频数组转换为 base64 编码的 WAV 格式
    
    Args:
        wav: 音频波形数据
        sample_rate: 采样率
        
    Returns:
        base64 编码的音频字符串
    """
    buffer = io.BytesIO()
    sf.write(buffer, wav, sample_rate, format='WAV')
    buffer.seek(0)
    audio_bytes = buffer.read()
    return base64.b64encode(audio_bytes).decode('utf-8')


def load_model():
    """
    加载 Qwen3-TTS 模型
    从环境变量 MODEL_NAME 读取模型名称，默认使用 0.6B Base 模型
    """
    global model, model_config
    
    from qwen_tts import Qwen3TTSModel
    
    # 从环境变量获取模型配置
    model_name = os.getenv('MODEL_NAME', 'Qwen/Qwen3-TTS-12Hz-0.6B-Base')
    cache_dir = '/app/models'
    
    # 转换模型名称为本地路径
    model_local_name = model_name.split('/')[-1]
    local_model_path = os.path.join(cache_dir, model_local_name)
    
    # 如果本地路径存在则使用本地路径，否则使用原始名称（会自动下载）
    model_path = local_model_path if os.path.exists(local_model_path) else model_name
    
    print(f"正在加载模型: {model_path}")
    print(f"模型名称: {model_name}")
    
    # 检测 GPU 可用性
    if torch.cuda.is_available():
        device = "cuda:0"
        dtype = torch.bfloat16
        print(f"使用 GPU: {torch.cuda.get_device_name(0)}")
    else:
        device = "cpu"
        dtype = torch.float32
        print("GPU 不可用，使用 CPU 模式")
    
    # 加载模型
    try:
        model = Qwen3TTSModel.from_pretrained(
            model_path,
            device_map=device,
            dtype=dtype,
            attn_implementation="flash_attention_2" if torch.cuda.is_available() else "eager",
        )
        print("模型加载成功！")
        
        # 获取模型信息
        model_config = {
            "model_name": model_name,
            "model_path": model_path,
            "model_type": model.model.tts_model_type if hasattr(model.model, 'tts_model_type') else "unknown",
            "model_size": model.model.tts_model_size if hasattr(model.model, 'tts_model_size') else "unknown",
            "device": device,
            "dtype": str(dtype),
            "supported_speakers": model.get_supported_speakers(),
            "supported_languages": model.get_supported_languages(),
        }
        print(f"模型配置: {model_config}")
        
    except Exception as e:
        print(f"模型加载失败: {str(e)}")
        raise e


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时加载模型
    print("=" * 50)
    print("启动 Qwen3-TTS API 服务...")
    print("=" * 50)
    load_model()
    yield
    # 关闭时清理资源
    print("关闭 Qwen3-TTS API 服务...")


app = FastAPI(
    title="Qwen3-TTS API",
    description="Qwen3-TTS 语音合成服务 - 返回 base64 编码的音频",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS - 允许所有来源访问（生产环境建议限制具体域名）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境建议改为具体域名如 ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有请求头
)


# ============== Pydantic 模型定义 ==============

class CustomVoiceRequest(BaseModel):
    """自定义语音合成请求"""
    text: str = Field(..., description="要合成的文本", example="你好，这是测试语音。")
    speaker: str = Field(default="Vivian", description="说话人名称", example="Vivian")
    language: Optional[str] = Field(default="Chinese", description="语言 (Chinese/English/Auto)", example="Chinese")
    instruct: Optional[str] = Field(default="", description="语音风格指令（可选）", example="用温柔的语气说")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "你好，这是测试语音。",
                "speaker": "Vivian",
                "language": "Chinese",
                "instruct": ""
            }
        }


class VoiceDesignRequest(BaseModel):
    """语音设计合成请求"""
    text: str = Field(..., description="要合成的文本", example="哥哥，你回来啦！")
    instruct: str = Field(..., description="语音风格描述", example="体现撒娇稚嫩的萝莉女声，音调偏高")
    language: Optional[str] = Field(default="Chinese", description="语言", example="Chinese")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "哥哥，你回来啦！",
                "instruct": "体现撒娇稚嫩的萝莉女声，音调偏高",
                "language": "Chinese"
            }
        }


class VoiceCloneRequest(BaseModel):
    """语音克隆合成请求"""
    text: str = Field(..., description="要合成的文本", example="这是一段克隆语音测试。")
    ref_audio_base64: str = Field(..., description="参考音频的 base64 编码", example="UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=")
    ref_text: Optional[str] = Field(default=None, description="参考音频对应的文本（用于 ICL 模式）")
    language: Optional[str] = Field(default="Chinese", description="语言", example="Chinese")
    x_vector_only_mode: bool = Field(default=False, description="仅使用声纹特征（无需 ref_text）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "这是一段克隆语音测试。",
                "ref_audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=",
                "ref_text": "",
                "language": "Chinese",
                "x_vector_only_mode": False
            }
        }


class TTSResponse(BaseModel):
    """语音合成响应"""
    success: bool = Field(..., description="是否成功")
    audio_base64: Optional[str] = Field(default=None, description="base64 编码的 WAV 音频")
    sample_rate: int = Field(default=24000, description="音频采样率")
    message: str = Field(default="", description="提示信息")
    duration_ms: Optional[int] = Field(default=None, description="音频时长（毫秒）")
    process_time_ms: Optional[int] = Field(default=None, description="处理耗时（毫秒）")


class ModelInfoResponse(BaseModel):
    """模型信息响应"""
    model_name: str = Field(..., description="模型名称")
    model_type: str = Field(..., description="模型类型 (custom_voice/voice_design/base)")
    model_size: str = Field(..., description="模型大小 (0.6B/1.7B)")
    supported_speakers: Optional[List[str]] = Field(default=None, description="支持的说话人列表")
    supported_languages: Optional[List[str]] = Field(default=None, description="支持的语言列表")
    device: str = Field(..., description="运行设备")


# ============== API 端点 ==============

@app.get("/", tags=["Root"])
async def root():
    """根路径 - 服务信息"""
    return {
        "service": "Qwen3-TTS API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Health"])
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "model_type": model_config.get("model_type") if model_config else None
    }


@app.get("/model/info", response_model=ModelInfoResponse, tags=["Model"])
async def model_info():
    """获取模型信息"""
    if model is None or not model_config:
        raise HTTPException(status_code=503, detail="模型尚未加载")
    
    return ModelInfoResponse(
        model_name=model_config.get("model_name", ""),
        model_type=model_config.get("model_type", "unknown"),
        model_size=model_config.get("model_size", "unknown"),
        supported_speakers=model_config.get("supported_speakers"),
        supported_languages=model_config.get("supported_languages"),
        device=model_config.get("device", "cpu")
    )


@app.post("/tts/custom-voice", response_model=TTSResponse, tags=["TTS"])
async def tts_custom_voice(request: CustomVoiceRequest):
    """
    自定义语音合成 (CustomVoice 模型)
    
    使用预设的说话人合成语音，支持风格指令控制。
    
    支持的说话人:
    - Vivian: 明亮、略带尖锐的年轻女声（中文）
    - Serena: 温暖、温柔的年轻女声（中文）
    - Uncle_Fu: 经验丰富、低沉醇厚的男声（中文）
    - Dylan: 年轻北京男声，音色清晰自然（中文北京方言）
    - Eric: 活泼成都男声，略带沙哑的明亮感（中文四川方言）
    - Ryan: 富有节奏感的动感男声（英文）
    - Aiden: 阳光美式男声，中音清晰（英文）
    - Ono_Anna: 俏皮日本女声，音色轻快灵动（日语）
    - Sohee: 温暖韩语女声，情感丰富（韩语）
    """
    if model is None:
        raise HTTPException(status_code=503, detail="模型尚未加载")
    
    # 检查模型类型
    if model.model.tts_model_type != "custom_voice":
        raise HTTPException(
            status_code=400, 
            detail=f"当前模型不支持 custom_voice 功能。模型类型: {model.model.tts_model_type}"
        )
    
    start_time = time.time()
    
    try:
        # 调用模型生成语音
        wavs, sr = model.generate_custom_voice(
            text=request.text,
            speaker=request.speaker,
            language=request.language,
            instruct=request.instruct if request.instruct else None,
        )
        
        # 转换为 base64
        audio_base64 = numpy_to_base64(wavs[0], sr)
        
        # 计算音频时长
        duration_ms = int(len(wavs[0]) / sr * 1000)
        process_time_ms = int((time.time() - start_time) * 1000)
        
        return TTSResponse(
            success=True,
            audio_base64=audio_base64,
            sample_rate=sr,
            message="语音合成成功",
            duration_ms=duration_ms,
            process_time_ms=process_time_ms
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音合成失败: {str(e)}")


@app.post("/tts/voice-design", response_model=TTSResponse, tags=["TTS"])
async def tts_voice_design(request: VoiceDesignRequest):
    """
    语音设计合成 (VoiceDesign 模型)
    
    根据自然语言描述设计语音风格并合成。
    
    示例 instruct:
    - "体现撒娇稚嫩的萝莉女声，音调偏高且起伏明显"
    - "成熟稳重的男性播音员声音，语速适中"
    - "活泼可爱的少女声，带有一点俏皮"
    """
    if model is None:
        raise HTTPException(status_code=503, detail="模型尚未加载")
    
    # 检查模型类型
    if model.model.tts_model_type != "voice_design":
        raise HTTPException(
            status_code=400, 
            detail=f"当前模型不支持 voice_design 功能。模型类型: {model.model.tts_model_type}"
        )
    
    start_time = time.time()
    
    try:
        # 调用模型生成语音
        wavs, sr = model.generate_voice_design(
            text=request.text,
            instruct=request.instruct,
            language=request.language,
        )
        
        # 转换为 base64
        audio_base64 = numpy_to_base64(wavs[0], sr)
        
        # 计算音频时长
        duration_ms = int(len(wavs[0]) / sr * 1000)
        process_time_ms = int((time.time() - start_time) * 1000)
        
        return TTSResponse(
            success=True,
            audio_base64=audio_base64,
            sample_rate=sr,
            message="语音设计合成成功",
            duration_ms=duration_ms,
            process_time_ms=process_time_ms
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音合成失败: {str(e)}")


@app.post("/tts/voice-clone", response_model=TTSResponse, tags=["TTS"])
async def tts_voice_clone(request: VoiceCloneRequest):
    """
    语音克隆合成 (Base 模型)
    
    根据参考音频克隆说话人声音并合成新文本。
    
    模式说明:
    - ICL 模式 (x_vector_only_mode=false): 需要提供 ref_text，效果更好
    - X-Vector 模式 (x_vector_only_mode=true): 无需 ref_text，仅使用声纹特征
    """
    if model is None:
        raise HTTPException(status_code=503, detail="模型尚未加载")
    
    # 检查模型类型
    if model.model.tts_model_type != "base":
        raise HTTPException(
            status_code=400, 
            detail=f"当前模型不支持 voice_clone 功能。模型类型: {model.model.tts_model_type}"
        )
    
    # ICL 模式需要 ref_text
    if not request.x_vector_only_mode and not request.ref_text:
        raise HTTPException(
            status_code=400, 
            detail="ICL 模式需要提供 ref_text 参数，或设置 x_vector_only_mode=true"
        )
    
    start_time = time.time()
    
    try:
        # 解码 base64 音频
        ref_audio_data = base64.b64decode(request.ref_audio_base64)
        
        # 调用模型生成语音
        wavs, sr = model.generate_voice_clone(
            text=request.text,
            ref_audio=ref_audio_data,
            ref_text=request.ref_text if request.ref_text else None,
            language=request.language,
            x_vector_only_mode=request.x_vector_only_mode,
        )
        
        # 转换为 base64
        audio_base64 = numpy_to_base64(wavs[0], sr)
        
        # 计算音频时长
        duration_ms = int(len(wavs[0]) / sr * 1000)
        process_time_ms = int((time.time() - start_time) * 1000)
        
        return TTSResponse(
            success=True,
            audio_base64=audio_base64,
            sample_rate=sr,
            message="语音克隆合成成功",
            duration_ms=duration_ms,
            process_time_ms=process_time_ms
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音合成失败: {str(e)}")


# ============== 批量处理端点 ==============

class BatchCustomVoiceRequest(BaseModel):
    """批量自定义语音合成请求"""
    items: List[CustomVoiceRequest]
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {"text": "第一句", "speaker": "Vivian", "language": "Chinese"},
                    {"text": "Second sentence", "speaker": "Ryan", "language": "English"}
                ]
            }
        }


class BatchTTSResponse(BaseModel):
    """批量语音合成响应"""
    success: bool
    results: List[TTSResponse]
    total_process_time_ms: int


@app.post("/tts/batch/custom-voice", response_model=BatchTTSResponse, tags=["Batch TTS"])
async def batch_tts_custom_voice(request: BatchCustomVoiceRequest):
    """批量自定义语音合成"""
    if model is None:
        raise HTTPException(status_code=503, detail="模型尚未加载")
    
    if model.model.tts_model_type != "custom_voice":
        raise HTTPException(
            status_code=400, 
            detail=f"当前模型不支持 custom_voice 功能。模型类型: {model.model.tts_model_type}"
        )
    
    start_time = time.time()
    results = []
    
    try:
        # 准备批量数据
        texts = [item.text for item in request.items]
        speakers = [item.speaker for item in request.items]
        languages = [item.language for item in request.items]
        instructs = [item.instruct if item.instruct else "" for item in request.items]
        
        # 批量生成
        wavs, sr = model.generate_custom_voice(
            text=texts,
            speaker=speakers,
            language=languages,
            instruct=instructs,
        )
        
        # 转换结果
        for wav in wavs:
            audio_base64 = numpy_to_base64(wav, sr)
            duration_ms = int(len(wav) / sr * 1000)
            results.append(TTSResponse(
                success=True,
                audio_base64=audio_base64,
                sample_rate=sr,
                message="合成成功",
                duration_ms=duration_ms
            ))
        
        total_process_time_ms = int((time.time() - start_time) * 1000)
        
        return BatchTTSResponse(
            success=True,
            results=results,
            total_process_time_ms=total_process_time_ms
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量合成失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
