import json
from abc import ABC
from langchain.agents import AgentExecutor
from langchain_core.agents import AgentAction, AgentStep, AgentFinish
from langchain_core.callbacks import CallbackManagerForChainRun
from langchain_core.tools import BaseTool
from langchain.agents.tools import InvalidTool
from typing import (
    Dict,
    Optional,
    Tuple,
)
from utils.common_utils import gen_uuid


class ToolsAgentExecutor(AgentExecutor, ABC):
    object_map = {}

    def serialize_value(self, value):
        """
        Serialize the input data for non-serializable or too-long strings.
        """
        if isinstance(value, dict):
            return {k: self.serialize_value(v) for k, v in value.items()}
        else:
            try:
                # Try to JSON serialize the value
                json.dumps(value)
                if len(str(value)) > 2000:
                    # Replace with a reference string
                    ref_key = f"object({type(value)}):{str(value)[:200]}"
                    self.object_map[ref_key] = value
                    return ref_key
                return value
            except Exception as e:  # Value is not serializable
                # Replace with a reference string
                ref_key = f"object({type(value)}):{gen_uuid('base')[:16]}"
                self.object_map[ref_key] = value
                return ref_key

    def de_serialize_value(self, value):
        """
        DeSerialize the input data for non-serializable or too-long strings.
        """
        if isinstance(value, dict):
            output = {k: self.de_serialize_value(v) for k, v in value.items()}
        else:
            output = self.object_map.get(f"{value}", value)
        return output

    def _perform_agent_action(
            self,
            name_to_tool_map: Dict[str, BaseTool],
            color_mapping: Dict[str, str],
            agent_action: AgentAction,
            run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> AgentStep:
        if run_manager:
            run_manager.on_agent_action(agent_action, color="green")
        # Otherwise we lookup the tool
        if agent_action.tool in name_to_tool_map:
            tool = name_to_tool_map[agent_action.tool]
            return_direct = tool.return_direct
            color = color_mapping[agent_action.tool]
            tool_run_kwargs = self.agent.tool_run_logging_kwargs()
            if return_direct:
                tool_run_kwargs["llm_prefix"] = ""
            # 反序列化无法json序列化或超长的值和对象传入工具执行
            agent_action.tool_input = self.de_serialize_value(agent_action.tool_input)
            observation = tool.run(
                agent_action.tool_input,
                verbose=self.verbose,
                color=color,
                callbacks=run_manager.get_child() if run_manager else None,
                **tool_run_kwargs,
            )
            # 序列化无法json序列化或超长的值和对象
            observation = self.serialize_value(observation)
            print(observation)
        else:
            tool_run_kwargs = self.agent.tool_run_logging_kwargs()
            observation = InvalidTool().run(
                {
                    "requested_tool_name": agent_action.tool,
                    "available_tool_names": list(name_to_tool_map.keys()),
                },
                verbose=self.verbose,
                color=None,
                callbacks=run_manager.get_child() if run_manager else None,
                **tool_run_kwargs,
            )
        return AgentStep(action=agent_action, observation=observation)

    def _get_tool_return(
            self, next_step_output: Tuple[AgentAction, str]
    ) -> Optional[AgentFinish]:
        """Check if the tool is a returning tool."""
        agent_action, observation = next_step_output
        name_to_tool_map = {tool.name: tool for tool in self.tools}
        return_value_key = "output"
        if len(self.agent.return_values) > 0:
            return_value_key = self.agent.return_values[0]
        # Invalid tools won't be in the map, so we return False.
        if agent_action.tool in name_to_tool_map:
            # 如果工具指定了是结果工具，或工具返回的是一个字典，并且字典中包含'type'键，且键的值为'agent_output'，则返回该字典中的'output作为最终结果
            break_flag = name_to_tool_map[agent_action.tool].return_direct
            # 反序列化无法json序列化或超长的值和对象
            output = self.de_serialize_value(observation)
            if isinstance(output, dict) and 'type' in output and output['type'] == 'agent_output':
                output = output['output']
                break_flag = True
            if name_to_tool_map[agent_action.tool].return_direct or break_flag:
                return AgentFinish(
                    {return_value_key: output},
                    "",
                )
        return None
