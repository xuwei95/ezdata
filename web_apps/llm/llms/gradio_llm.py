from typing import List, Optional
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
from gradio_client import Client

gradio_url = "https://s5k.cn/api/v1/studio/ZhipuAI/glm-4-9b-chat-vllm/gradio/"


class GradioLLM(LLM):
    url = gradio_url
    messages = []

    def _call(self, prompt: str, stop: Optional[List[str]] = None, run_manager: Optional[CallbackManagerForLLMRun] = None,):
        client = Client(self.url)
        result = client.predict(
            prompt,
            self.messages,
            api_name="/predict_1"
        )
        self.messages = result[1]
        return self.messages[-1][-1]

    @property
    def _llm_type(self):
        return "gradio_llm"


if __name__ == '__main__':
    llm = GradioLLM(url=gradio_url)
    res = llm('nihao')
    print(res)
    res = llm('我刚才说了啥')
    print(res)