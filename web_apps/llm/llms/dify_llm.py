from typing import List, Optional
import requests
import json
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM


class DifyLLM(LLM):
    url = 'https://api.dify.ai/v1'
    api_key = ''
    conversation_id = ''

    def _call(self, prompt: str, stop: Optional[List[str]] = None, run_manager: Optional[CallbackManagerForLLMRun] = None,):
        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json"
        }
        data = {
            "inputs": {},
            "query": str(prompt),
            "response_mode": "blocking",
            "conversation_id": self.conversation_id,
            "user": ""
        }
        res = requests.post(self.url + '/chat-messages', json=data, headers=headers)
        response_obj = json.loads(res.text)
        answer = response_obj['answer']
        if response_obj['conversation_id']:
            self.conversation_id = response_obj['conversation_id']
        return answer

    @property
    def _llm_type(self):
        return "dify_llm"


if __name__ == '__main__':
    api_key = ''
    llm = DifyLLM(api_key=api_key)
    res = llm('nihao')
    print(res)
    res = llm('我刚才说了啥')
    print(res)