from pandasai.prompts import AbstractPrompt
from pandasai import Agent
from pandasai.responses.response_parser import ResponseParser


class MyResponseParser(ResponseParser):

    def __init__(self, context) -> None:
        super().__init__(context)

    def format_plot(self, result: dict):
        # 直接返回内容
        return result["value"]


class MyCorrectErrorPrompt(AbstractPrompt):

    @property
    def template(self) -> str:
        prompt = '''
{dataframes}

The user asked the following question:
{conversation}

You generated this python code:
{code}

It fails with the following error:
{error_returned}

Fix the python code above and return the new python code:
如果错误中有File name too long: '<!DOCTYPE html>这种错误，帮我将result的type改为string
如果错误中有Can only use .dt accessor 请在逻辑之前对处理列先进行转换为datetime类型
如果错误中有snapshot_selenium 请纠正代码中禁止使用此库并直接使用render_embed()函数返回对应html文本
        '''
        return prompt

    def set_var(self, var, value):
        if self._args is None:
            self._args = {}
        if var == "dfs":
            self._args["dataframes"] = self._generate_dataframes(value)
        if var == "error_returned":
            # 将报错截取前1000字符防止prompt过长
            print('error', value)
            self._args["error_returned"] = str(value)[:1000]
        else:
            self._args[var] = value


class MyReasoningPrompt(AbstractPrompt):
    """The simple reasoning instructions"""

    @property
    def template(self) -> str:
        prompt = '''
At the end, declare "result" var dict: {output_type_hint}
{viz_library_type}
{instructions}

Generate python code and return full updated code:        
        '''
        return prompt


class MyGeneratePythonCodePrompt(AbstractPrompt):
    """Prompt to generate Python code"""

    @property
    def template(self) -> str:
        prompt = '''
{dataframes}
{skills}

{prev_conversation}

{code_description}
```python
{current_code}
```

{last_message}
Variable `dfs: list[pd.DataFrame]` is already declared.
{reasoning}
            '''
        return prompt

    def setup(self, **kwargs) -> None:
        if "custom_instructions" in kwargs:
            self.set_var("instructions", kwargs["custom_instructions"])
        else:
            self.set_var("instructions", "")

        if "current_code" in kwargs:
            self.set_var("current_code", kwargs["current_code"])
        else:
            self.set_var("current_code", MyCorrectErrorPrompt(dfs_declared=True))

        if "code_description" in kwargs:
            self.set_var("code_description", kwargs["code_description"])
        else:
            self.set_var("code_description", "Update this initial code:")

        if "last_message" in kwargs:
            self.set_var("last_message", kwargs["last_message"])
        else:
            self.set_var("last_message", "")

        if "prev_conversation" in kwargs:
            self.set_var("prev_conversation", kwargs["prev_conversation"])
        else:
            self.set_var("prev_conversation", "")

    def on_prompt_generation(self) -> None:
        default_import = "import pandas as pd"
        engine_df_name = "pd.DataFrame"

        self.set_var("default_import", default_import)
        self.set_var("engine_df_name", engine_df_name)
        self.set_var("reasoning", MyReasoningPrompt())


class MyExplainPrompt(AbstractPrompt):
    """Prompt to explain code generation by the LLM"""

    @property
    def template(self) -> str:
        prompt = '''
        The previous conversation we had

        <Conversation>
        {conversation}
        </Conversation>

        Based on the last conversation you generated the following code:

        <Code>
        {code}
        </Code>

        Explain how you came up with code for non-technical people without 
        mentioning technical details or mentioning the libraries used?
        使用中文解释
        '''
        return prompt

    def setup(self, conversation: str, code: str) -> None:
        self.set_var("conversation", conversation)
        self.set_var("code", code)


class MyPandasAgent(Agent):

    def explain(self) -> str:
        """
        Returns the explanation of the code how it reached to the solution
        """
        try:
            prompt = MyExplainPrompt(
                conversation=self._lake._memory.get_conversation(),
                code=self._lake.last_code_executed,
            )
            response = self._call_llm_with_prompt(prompt)
            self._logger.log(
                f"""Explanation:  {response}
                """
            )
            return response
        except Exception as exception:
            return (
                "Unfortunately, I was not able to explain, "
                "because of the following error:\n"
                f"\n{exception}\n"
            )
