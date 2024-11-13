from web_apps.llm.llm_utils import extract_code
import traceback
import pandas as pd


class DataExtractAgent:
    def __init__(self, llm, reader, retry=1):
        self.llm = llm
        self.reader = reader
        self.question = ''
        self.last_code_executed = ''
        self.code_exception = ''
        self.max_retry = retry
        self.info_prompt = ''
        self.question = ''

    def gen_info_prompt(self):
        '''
        生成信息提示
        :return:
        '''
        if self.info_prompt == '':
            self.info_prompt = self.reader.get_info_prompt(self.question)
        # if len(info_prompt) > self.max_tokens:
        #     # 提示过长，使用llm判断需要取哪些模型提示信息
        #     prompt = f"""你是一个数据读取器，
        #     """
        return self.info_prompt

    def generate_code(self, prompt):
        result_example_prompt = '{ "type": "dataframe", "value": pd.DataFrame({...}) }'
        prompt = f"""
I have a data reader object called reader, and the object information is：
{self.gen_info_prompt()}

Update this initial code:
```python
# TODO: import the required dependencies

# Write code here

# Declare result var: 
type (must be "dataframe"), value must be a pd.DataFrame. Example: result = {result_example_prompt}

```

### QUERY

{prompt}

Variable `reader` is already declared.

At the end, declare "result" variable as a dictionary of type and value.


Generate python code and return full updated code:
请在代码中使用中文添加必要注释
"""
        self.llm_result = self.llm.invoke(prompt).content
        code = extract_code(self.llm_result)
        return code

    def fix_code(self):
        '''
        使用llm修正错误代码
        :return:
        '''
        fix_code_prompt = f"""
I have a data reader object called reader, and the object information is：
{self.gen_info_prompt()}
The user asked the following question:
{self.question}
You generated this python code:
{self.last_code_executed}
the code running throws an exception:
{self.code_exception}
Fix the python code above and return the new python code
请在代码中使用中文添加必要注释
        """
        self.llm_result = self.llm.invoke(fix_code_prompt).content
        new_code = extract_code(self.llm_result)
        return new_code

    def execute_code(self, code: str):
        """
        Execute the python code generated by LLMs to answer the question
        about the input dataframe. Run the code in the current context and return the
        result.
        Args:
            code (str): Python code to execute.
            context (CodeExecutionContext): Code Execution Context
                    with prompt id and skills.
        Returns:
            Any: The result of the code execution. The type of the result depends
                on the generated code.
        """
        try:
            environment = {'reader': self.reader}
            exec(code, environment)
            self.last_code_executed = code
            if "result" not in environment:
                raise ValueError("No result returned")
            else:
                result = environment['result']
                if not isinstance(result['value'], pd.DataFrame):
                    raise ValueError(f'Value type {type(result["value"])} must match with type {result["type"]}')
                return environment['result']
        except Exception as e:
            self.last_code_executed = code
            raise e

    def run(self, prompt):
        self.question = prompt
        code = self.generate_code(prompt)
        retry_count = 0
        result = None
        while retry_count <= self.max_retry:
            try:
                print(code)
                result = self.execute_code(code)
                break
            except Exception as e:
                traceback_errors = traceback.format_exc()
                self.code_exception = traceback_errors
                retry_count += 1
                code = self.fix_code()
        return result

