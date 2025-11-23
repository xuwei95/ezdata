from typing import List, Optional, Any
import requests
import json
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage

from langchain_core.outputs import (
    ChatGeneration,
    ChatResult,
)


class DifyChatModel(BaseChatModel):
    url: str = 'https://api.dify.ai/v1'
    api_key: str = ''
    conversation_id: str = ''

    def _generate(
            self,
            messages: List[BaseMessage],
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
    ) -> ChatResult:
        generations = []
        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json"
        }
        data = {
            "inputs": {},
            "query": str(messages[-1].content),
            "response_mode": "blocking",
            "conversation_id": self.conversation_id,
            "user": ""
        }
        res = requests.post(self.url + '/chat-messages', json=data, headers=headers)
        response_obj = json.loads(res.text)
        if response_obj['conversation_id']:
            self.conversation_id = response_obj['conversation_id']
        answer = response_obj['answer']
        gen = ChatGeneration(
            message=AIMessage(content=answer, id=self.conversation_id)
        )
        generations.append(gen)
        return ChatResult(
            generations=generations,
            llm_output=response_obj,
        )

    @property
    def _llm_type(self):
        return "dify_llm"


if __name__ == '__main__':
    api_key = ''
    llm = DifyChatModel(api_key=api_key)
    res = llm.stream('nihao')
    print(res)
    for i in res:
        print(i)
    res = llm.stream('我刚才说了啥')
    print(res)
    for i in res:
        print(i)