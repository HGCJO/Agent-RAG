from langchain.agents.middleware import  wrap_tool_call,before_model,dynamic_prompt,ModelRequest
from langchain.tools.tool_node import ToolCallRequest
from typing import Callable
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langgraph.runtime import Runtime
from utils.logger_handler import logger
from langchain.agents import AgentState
from utils.prompt_loader import load_report_prompts,load_system_prompts

@wrap_tool_call
def monitor_tool(
        request: ToolCallRequest,#请求的数据格式
        handler :Callable[[ToolCallRequest],ToolMessage|Command] #执行的函数
)-> ToolMessage|Command:        #监控工具的执行

    logger.info(f"[tool monitor]执行工具: {request.tool_call['name']}")
    logger.info(f"[tool monitor]传入参数: {request.tool_call['args']}")
    try:
        result = handler(request)
        logger.info(f"[tool monitor]工具{request.tool_call['name']}执行成功")
            
        if request.tool_call['name'] == "file_context_for_report":
            request.runtime.context["report"] = True

        return result
    except Exception as e:
        logger.error(f"[tool monitor]工具执行异常,原因: {e}")
        raise



@before_model
def log_before_model(
    state: AgentState, #整个agent智能体的
    runtime: Runtime,   # 记录整个执行过程的上下文信息
):                      #在模型调用之前输出日志
    logger.info(f"[before model]即将调用模型，带有{len(state['messages'])}个消息")
    logger.debug(f"[before model]消息类型:{type(state['messages'][-1]).__name__}  |  {state['messages'][-1].content.strip()}")
    return None



@dynamic_prompt #每一次在生成提示词之前调用这个函数，可以根据当前的状态动态修改提示词
def report_prompt_switch(request :ModelRequest):#动态切换提示词
    is_report = request.runtime.context.get("report", False) #从上下文中获取是否是报告的标志，默认为False
    if is_report:   #如果是报告，就加载报告的提示词
        return load_report_prompts()
    else:           #否则加载系统的提示词
        return load_system_prompts()