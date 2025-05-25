import pandas as pd

from pandasai import SmartDatalake
from pandasai.llm import OpenAI
from pandasai.prompts import AbstractPrompt


class MyCustomPrompt(AbstractPrompt):
    @property
    def template(self):
        return """你必须用中文回答所有问题"""

employees_df = pd.DataFrame(
    {
        "EmployeeID": [1, 2, 3, 4, 5],
        "Name": ["John", "Emma", "Liam", "Olivia", "William"],
        "Department": ["HR", "Sales", "IT", "Marketing", "Finance"],
    }
)

salaries_df = pd.DataFrame(
    {
        "EmployeeID": [1, 2, 3, 4, 5],
        "Salary": [5000, 6000, 4500, 7000, 5500],
    }
)

llm = OpenAI(api_token='REDACTEDmZ1uAMcKPRGva1H3VsLNT3BlbkFJKLxOo1DAyHtF3FeuJU69')
dl = SmartDatalake(
    [employees_df, salaries_df],
    config={
        "llm": llm,
        "verbose": True,
        "custom_prompts": {
                "generate_python_code": MyCustomPrompt()
            }
    },
)

dl.chat("Plot salaries against name")
