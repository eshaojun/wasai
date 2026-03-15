#!/usr/bin/env python3
"""
Qwen3-TTS API 测试脚本
用于测试 FastAPI 接口是否正常工作
"""
import base64
import json
import sys

import requests


API_BASE = "http://localhost:8003"


def test_health():
    """测试健康检查"""
    print("测试健康检查...")
    resp = requests.get(f"{API_BASE}/health")
    print(f"状态码: {resp.status_code}")
    print(f"响应: {resp.json()}")
    return resp.status_code == 200


def test_model_info():
    """测试模型信息"""
    print("\n测试模型信息...")
    resp = requests.get(f"{API_BASE}/model/info")
    print(f"状态码: {resp.status_code}")
    data = resp.json()
    print(f"模型名称: {data.get('model_name')}")
    print(f"模型类型: {data.get('model_type')}")
    print(f"支持说话人: {data.get('supported_speakers')}")
    return data


def test_custom_voice():
    """测试自定义语音合成"""
    print("\n测试自定义语音合成...")
    
    payload = {
        "text": "你好，这是一个测试语音。我是 Qwen3-TTS 语音合成系统。",
        "speaker": "Vivian",
        "language": "Chinese",
        # "language": "English",
        "instruct": ""
    }
    
    resp = requests.post(
        f"{API_BASE}/tts/custom-voice",
        json=payload,
        timeout=120
    )
    
    print(f"状态码: {resp.status_code}")
    data = resp.json()
    
    if data.get('success'):
        print(f"✅ 合成成功！")
        print(f"采样率: {data.get('sample_rate')}")
        print(f"音频时长: {data.get('duration_ms')} ms")
        print(f"处理耗时: {data.get('process_time_ms')} ms")
        print(f"音频大小: {len(data.get('audio_base64', ''))} bytes (base64)")
        
        # 保存音频文件
        audio_data = base64.b64decode(data['audio_base64'])
        output_file = "test_output.wav"
        with open(output_file, "wb") as f:
            f.write(audio_data)
        print(f"音频已保存到: {output_file}")
        return True
    else:
        print(f"❌ 合成失败: {data.get('message')}")
        return False


def test_voice_design():
    """测试语音设计合成"""
    print("\n测试语音设计合成...")
    
    payload = {
        "text": "哥哥，你回来啦，人家等了你好久好久了！",
        "instruct": "体现撒娇稚嫩的萝莉女声，音调偏高且起伏明显，营造出黏人、卖萌的听觉效果。",
        "language": "Chinese"
    }
    
    resp = requests.post(
        f"{API_BASE}/tts/voice-design",
        json=payload,
        timeout=120
    )
    
    print(f"状态码: {resp.status_code}")
    data = resp.json()
    
    if data.get('success'):
        print(f"✅ 语音设计合成成功！")
        print(f"采样率: {data.get('sample_rate')}")
        print(f"处理耗时: {data.get('process_time_ms')} ms")
        
        # 保存音频文件
        audio_data = base64.b64decode(data['audio_base64'])
        output_file = "test_voice_design.wav"
        with open(output_file, "wb") as f:
            f.write(audio_data)
        print(f"音频已保存到: {output_file}")
        return True
    else:
        print(f"❌ 合成失败: {data.get('message')}")
        return False


def test_batch_custom_voice():
    """测试批量自定义语音合成"""
    print("\n测试批量自定义语音合成...")
    
    payload = {
        "items": [
            {"text": "第一句中文测试", "speaker": "Vivian", "language": "Chinese"},
            {"text": "第二句中文测试", "speaker": "Serena", "language": "Chinese"},
            {"text": "This is an English test.", "speaker": "Ryan", "language": "English"}
        ]
    }
    
    resp = requests.post(
        f"{API_BASE}/tts/batch/custom-voice",
        json=payload,
        timeout=180
    )
    
    print(f"状态码: {resp.status_code}")
    data = resp.json()
    
    if data.get('success'):
        print(f"✅ 批量合成成功！")
        print(f"总处理耗时: {data.get('total_process_time_ms')} ms")
        print(f"合成结果数量: {len(data.get('results', []))}")
        
        # 保存音频文件
        for i, result in enumerate(data.get('results', [])):
            if result.get('success'):
                audio_data = base64.b64decode(result['audio_base64'])
                output_file = f"test_batch_{i}.wav"
                with open(output_file, "wb") as f:
                    f.write(audio_data)
                print(f"  - 音频 {i+1} 已保存到: {output_file}")
        return True
    else:
        print(f"❌ 批量合成失败")
        return False


def main():
    """主函数"""
    print("=" * 50)
    print("Qwen3-TTS API 测试脚本")
    print("=" * 50)
    
    # 测试健康检查
    if not test_health():
        print("❌ 服务未启动，请检查 API 是否运行")
        sys.exit(1)
    
    # 获取模型信息
    model_info = test_model_info()
    model_type = model_info.get('model_type', 'unknown')
    
    # 根据模型类型选择测试用例
    if model_type == 'custom_voice':
        print("\n检测到 CustomVoice 模型，测试自定义语音功能...")
        test_custom_voice()
        test_batch_custom_voice()
    elif model_type == 'voice_design':
        print("\n检测到 VoiceDesign 模型，测试语音设计功能...")
        test_voice_design()
    elif model_type == 'base':
        print("\n检测到 Base 模型（语音克隆），请参考 API 文档测试 /tts/voice-clone 端点")
        print("需要使用参考音频的 base64 编码")
    else:
        print(f"\n未知模型类型: {model_type}")
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
