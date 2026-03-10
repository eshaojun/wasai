from typing import List, Optional, Dict
import openai
import time
import logging

logger = logging.getLogger(__name__)


class TranslateService:
    """翻译服务"""

    # 语言代码映射
    LANG_NAMES = {
        "zh": "中文", "en": "英语", "ja": "日语", "ko": "韩语",
        "es": "西班牙语", "fr": "法语", "de": "德语",
        "ru": "俄语", "ar": "阿拉伯语", "pt": "葡萄牙语",
        "it": "意大利语", "nl": "荷兰语", "pl": "波兰语",
        "tr": "土耳其语", "vi": "越南语", "th": "泰语",
        "id": "印尼语", "ms": "马来语", "hi": "印地语"
    }

    def __init__(
        self,
        provider: str = "custom",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4o-mini",
        prompt: str = "你是一个专业的翻译助手，擅长将短剧对话翻译成自然流畅的目标语言。",
        batch_size: int = 50,
        max_retries: int = 3
    ):
        """
        初始化翻译服务

        Args:
            provider: 提供商类型 (openai, custom)
            api_key: API密钥
            base_url: API基础URL
            model: 模型名称
            prompt: 翻译提示词
            batch_size: 每批翻译的条数
            max_retries: 最大重试次数
        """
        self.provider = provider
        self.model = model
        self.prompt = prompt
        self.batch_size = batch_size
        self.max_retries = max_retries

        # 初始化OpenAI客户端
        if provider == "openai":
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.openai.com/v1"
            )
        else:
            # custom - 使用用户配置的base_url
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url=base_url or "https://api.openai.com/v1"
            )

    def translate(
        self,
        texts: List[str],
        source_lang: str = "zh",
        target_lang: str = "en"
    ) -> List[str]:
        """
        批量翻译文本

        Args:
            texts: 要翻译的文本列表
            source_lang: 源语言代码
            target_lang: 目标语言代码

        Returns:
            翻译后的文本列表
        """
        if not texts:
            return []

        return self._translate_with_retry(texts, source_lang, target_lang)

    def _translate_with_retry(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str
    ) -> List[str]:
        """带重试机制的翻译"""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                return self._translate_batch(texts, source_lang, target_lang)
            except Exception as e:
                last_error = e
                logger.warning(f"翻译失败 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}")

                if attempt < self.max_retries - 1:
                    # 指数退避
                    wait_time = 2 ** attempt
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)

        raise Exception(f"翻译失败，已重试 {self.max_retries} 次: {str(last_error)}")

    def _translate_batch(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str
    ) -> List[str]:
        """执行批量翻译"""
        source_name = self.LANG_NAMES.get(source_lang, source_lang)
        target_name = self.LANG_NAMES.get(target_lang, target_lang)

        results = []

        # 分批翻译
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_results = self._translate_single_batch(
                batch, source_name, target_name
            )
            results.extend(batch_results)

        # 质量检查
        results = self._quality_check(texts, results)

        return results

    def _translate_single_batch(
        self,
        batch: List[str],
        source_name: str,
        target_name: str
    ) -> List[str]:
        """翻译单个批次"""
        # 构建批次文本
        batch_text = "\n---\n".join([f"[{idx}] {text}" for idx, text in enumerate(batch)])

        user_prompt = f"""请将以下 {source_name} 文本翻译成 {target_name}。
请保持原有的格式标记（如 [0], [1] 等），每条文本用 --- 分隔。
只输出翻译结果，不要添加解释。

{batch_text}
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )

        # 解析响应
        translated = response.choices[0].message.content
        translated_lines = translated.split("\n---\n")

        results = []
        for line in translated_lines:
            line = line.strip()
            if line.startswith("[") and "]" in line:
                idx = line.index("]")
                results.append(line[idx + 1:].strip())
            else:
                results.append(line)

        # 确保结果数量与输入一致
        while len(results) < len(batch):
            results.append("")

        return results[:len(batch)]

    def _quality_check(
        self,
        original: List[str],
        translated: List[str]
    ) -> List[str]:
        """
        翻译质量检查

        检测并修复常见问题：
        - 翻译结果为空
        - 翻译结果过长/过短
        - 与原文完全相同（可能是语言相同或未翻译）
        """
        results = []

        for orig, trans in zip(original, translated):
            # 跳过空翻译
            if not trans or not trans.strip():
                logger.warning(f"检测到空翻译: 原文={orig}")
                results.append(orig)
                continue

            # 检查是否与原文完全相同（可能是同一语言）
            if orig.strip() == trans.strip():
                logger.warning(f"翻译结果与原文相同，可能语言设置错误: {orig}")
                results.append(trans)
                continue

            # 检查长度异常（翻译结果长度是原文的10倍以上，可能是误翻译）
            if len(trans) > len(orig) * 10:
                logger.warning(f"翻译结果异常长: 原文={orig}, 译文={trans}")
                results.append(trans)
                continue

            results.append(trans)

        return results

    def translate_single(
        self,
        text: str,
        source_lang: str = "zh",
        target_lang: str = "en"
    ) -> str:
        """
        翻译单条文本

        Args:
            text: 要翻译的文本
            source_lang: 源语言代码
            target_lang: 目标语言代码

        Returns:
            翻译后的文本
        """
        if not text:
            return ""

        results = self.translate([text], source_lang, target_lang)
        return results[0] if results else ""
