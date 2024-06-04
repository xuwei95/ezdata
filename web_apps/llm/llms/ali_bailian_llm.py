import random
from http import HTTPStatus
from dashscope import Generation
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
from typing import List, Optional


class AliBailianLLM(LLM):
    api_key = ''
    model_name = 'qwen-max'
    messages = []

    def _call(self, prompt: str, stop: Optional[List[str]] = None, run_manager: Optional[CallbackManagerForLLMRun] = None,):
        message = {'role': 'user', 'content': prompt}
        self.messages.append(message)
        response = Generation.call(model=self.model_name,
                                   api_key=self.api_key,
                                   messages=self.messages,
                                   # 设置随机数种子seed，如果没有设置，则随机数种子默认为1234
                                   seed=random.randint(1, 10000),
                                   # 将输出设置为"message"格式
                                   result_format='message')
        if response.status_code == HTTPStatus.OK:
            print(response)
            answer = response['output']['choices'][0]['message']['content']
            return answer
        else:
            return 'Request id: %s, Status code: %s, error code: %s, error message: %s' % (
                response.request_id, response.status_code,
                response.code, response.message
            )

    @property
    def _llm_type(self):
        return "ali_llm"


if __name__ == '__main__':
    api_key = ''
    model = 'qwen-max'
    llm = AliBailianLLM(api_key=api_key, model=model)
    res = llm('你好')
    print(res)
    res = llm('我刚才说了啥')
    print(res)