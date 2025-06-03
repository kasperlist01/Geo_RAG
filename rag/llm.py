import json
import requests
from typing import List, Optional, Any, Dict
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from config import OPENROUTER_API_KEY, MODEL_NAME


class OpenRouterLLM(LLM):
    """Класс для использования OpenRouter API для генерации текста"""

    model: str = MODEL_NAME
    temperature: float = 0
    api_key: str = OPENROUTER_API_KEY

    def _call(
            self,
            prompt: str,
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any
    ) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        messages = [{"role": "user", "content": prompt}]

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature
        }

        if stop:
            data["stop"] = stop

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(data)
        )

        if response.status_code != 200:
            raise Exception(f"Ошибка в OpenRouter API: {response.text}")

        result = response.json()
        return result["choices"][0]["message"]["content"]

    @property
    def _llm_type(self) -> str:
        return "openrouter"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model": self.model, "temperature": self.temperature}