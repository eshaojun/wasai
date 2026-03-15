#!/usr/bin/env python3
"""
模型下载脚本 - 在 Docker 构建时运行，使用 ModelScope 下载模型到镜像中
"""
import argparse
import os
import sys
from pathlib import Path


def download_model(model_name: str, cache_dir: str):
    """
    从 ModelScope 下载模型到指定目录
    
    Args:
        model_name: Hugging Face 模型名称，如 "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
        cache_dir: 模型缓存目录
    """
    print(f"开始下载模型: {model_name}")
    print(f"缓存目录: {cache_dir}")
    
    os.makedirs(cache_dir, exist_ok=True)
    
    try:
        from modelscope import snapshot_download
        from transformers import AutoConfig, AutoModel, AutoProcessor
        
        # 注册自定义模型类
        import sys
        sys.path.insert(0, '/app')
        from qwen_tts.core.models import Qwen3TTSConfig, Qwen3TTSForConditionalGeneration, Qwen3TTSProcessor
        
        AutoConfig.register("qwen3_tts", Qwen3TTSConfig)
        AutoModel.register(Qwen3TTSConfig, Qwen3TTSForConditionalGeneration)
        AutoProcessor.register(Qwen3TTSConfig, Qwen3TTSProcessor)
        
        # 转换模型名称为 ModelScope 格式
        # HuggingFace: Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice
        # ModelScope: Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice (相同)
        
        # 下载主模型
        print(f"\n[1/3] 下载 TTS 模型: {model_name}")
        model_local_name = model_name.split('/')[-1]
        model_local_path = os.path.join(cache_dir, model_local_name)
        
        model_path = snapshot_download(
            model_id=model_name,
            cache_dir=cache_dir,
            local_dir=model_local_path,
        )
        print(f"模型下载完成: {model_path}")
        
        # 下载 Tokenizer
        print(f"\n[2/3] 下载 Tokenizer: Qwen/Qwen3-TTS-Tokenizer-12Hz")
        tokenizer_local_path = os.path.join(cache_dir, "Qwen3-TTS-Tokenizer-12Hz")
        
        tokenizer_path = snapshot_download(
            model_id="Qwen/Qwen3-TTS-Tokenizer-12Hz",
            cache_dir=cache_dir,
            local_dir=tokenizer_local_path,
        )
        print(f"Tokenizer 下载完成: {tokenizer_path}")
        
        # 预加载模型以验证
        print(f"\n[3/3] 验证模型加载...")
        import torch
        
        model = AutoModel.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="cpu",  # 构建时不使用 GPU
            trust_remote_code=True
        )
        processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)
        
        print(f"模型验证成功！")
        print(f"模型类型: {model.config.tts_model_type}")
        print(f"模型大小: {model.config.tts_model_size}")
        
        # 清理内存
        del model
        del processor
        import gc
        gc.collect()
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        
        print(f"\n✅ 所有模型下载并验证成功！")
        return True
        
    except Exception as e:
        print(f"\n❌ 模型下载失败: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description='下载 Qwen3-TTS 模型')
    parser.add_argument('--model_name', type=str, 
                        default='Qwen/Qwen3-TTS-12Hz-0.6B-Base',
                        help='ModelScope 模型名称')
    parser.add_argument('--cache_dir', type=str, 
                        default='/app/models',
                        help='模型缓存目录')
    
    args = parser.parse_args()
    
    success = download_model(args.model_name, args.cache_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
