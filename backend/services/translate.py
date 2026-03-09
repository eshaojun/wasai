from typing import List, Optional
import openai


class TranslateService:
    """翻译服务"""

    def __init__(
        self,
        provider: str = "openai",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4o-mini",
        deepl_key: Optional[str] = None
    ):
        self.provider = provider
        self.model = model
        self.deepl_key = deepl_key
        self.client = None

        if provider == "openai":
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

        if self.provider == "openai":
            return self._translate_openai(texts, source_lang, target_lang)
        else:
            raise NotImplementedError(f"不支持的翻译提供商: {self.provider}")

    def _translate_openai(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str
    ) -> List[str]:
        """使用 OpenAI 进行翻译"""
        # 构建提示
        lang_names = {
            "zh": "中文", "en": "英语", "ja": "日语", "ko": "韩语",
            "es": "西班牙语", "fr": "法语", "de": "德语",
            "ru": "俄语", "ar": "阿拉伯语", "pt": "葡萄牙语"
        }

        source_name = lang_names.get(source_lang, source_lang)
        target_name = lang_names.get(target_lang, target_lang)

        # 批量翻译（每次最多 50 条）
        batch_size = 50
        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_text = "\n---\n".join([f"[{idx}] {text}" for idx, text in enumerate(batch)])

            prompt = f"""请将以下 {source_name} 文本翻译成 {target_name}。
请保持原有的格式标记（如 [0], [1] 等），每条文本用 --- 分隔。
只输出翻译结果，不要添加解释。

{texts}
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的翻译助手，擅长将短剧对话翻译成自然流畅的目标语言。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )

            # 解析响应
            translated = response.choices[0].message.content
            translated_lines = translated.split("\n---\n")

            for line in translated_lines:
                line = line.strip()
                if line.startswith("[") and "]" in line:
                    idx = line.index("]")
                    results.append(line[idx + 1:].strip())
                else:
                    results.append(line)

        return results[:len(texts)]
