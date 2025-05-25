import pandas as pd
from pandasai import Agent

from pandasai.llm.openai import OpenAI
from pandasai.prompts import AbstractPrompt
from pandasai.prompts.explain_prompt import ExplainPrompt

employees_data = {
    "EmployeeID": [1, 2, 3, 4, 5],
    "Name": ["John", "Emma", "Liam", "Olivia", "William"],
    "Department": ["HR", "Sales", "IT", "Marketing", "Finance"],
}

salaries_data = {
    "EmployeeID": [1, 2, 3, 4, 5],
    "Salary": [5000, 6000, 4500, 7000, 5500],
}

employees_df = pd.DataFrame(employees_data)
salaries_df = pd.DataFrame(salaries_data)


llm = OpenAI("REDACTEDmZ1uAMcKPRGva1H3VsLNT3BlbkFJKLxOo1DAyHtF3FeuJU69")


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


class MyAgent(Agent):

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


agent = MyAgent([employees_df, salaries_df], config={
    "llm": llm,
    # "custom_prompts": {
    #     "generate_python_code": MyCustomPrompt()
    # }
}, memory_size=10)
# Chat with the agent
response = agent.chat("谁的工资最高? 用中文回答")
print(response)

# Explain how the chat response is generated
res = agent.last_code_executed
print(res)
response = agent.explain()
print(response)