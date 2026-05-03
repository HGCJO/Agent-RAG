from langchain.agents import create_agent
from model.factory import chat_model 
from utils.prompt_loader import load_system_prompts
from agent.tools.agent_tools import (rag_summarize,get_weather,get_user_location,
get_current_month,get_user_id,fetch_external_data,file_context_for_report)

from agent.tools.middleware import monitor_tool, log_before_model, report_prompt_switch
from typing import List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from utils.logger_handler import logger

class ReactAgent:
    def __init__(self, user_id: str = "default_user"):
        self.user_id = user_id
        self.system_prompts = load_system_prompts()
        self.message_history: List[BaseMessage] = []
        
        self.agent = create_agent(
            model = chat_model,
            # system_prompt = self.system_prompts,
            tools=[
                rag_summarize,
                get_weather,
                get_user_location,
                get_current_month,
                get_user_id,
                fetch_external_data,
                file_context_for_report
            ],
            middleware=[
                monitor_tool,
                log_before_model,
                report_prompt_switch
            ],
        )
    # def execute_stream(self, query:str):
    #     input_dict = {
    #         "messages": [
    #             {"role": "user", "content": query}
    #         ]
    #     }
    #     #第三个参数是上下文runtime的信息，可以在middleware中使用这个上下文来动态切换提示词
    #     res=self.agent.stream(input_dict, stream_mode="values", context={"report": False})
    #     for chunk  in res:
    #         latest_message = chunk["messages"][-1]
    #         if latest_message.content:
    #             yield latest_message.content.strip() + "\n"

    def execute_stream(self, query: str, use_history: bool = True):
        """
        执行流式查询
        
        Args:
            query: 用户查询文本
            use_history: 是否使用历史消息
        """

        # 构建输入消息列表
        messages = []

        messages.append({"role": "system", "content": self.system_prompts}) 

        # 添加历史消息
        if use_history:
            for msg in self.message_history[-10:]:  # 保留最近 10 条消息
                if isinstance(msg, HumanMessage): # 只添加用户消息到输入中
                    messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):  # 只添加模型消息到输入中
                    messages.append({"role": "assistant", "content": msg.content})

        # 添加当前用户消息
        messages.append({"role": "user", "content": query})

         # 保存用户消息到历史
        self.message_history.append(HumanMessage(content=query))

        # 执行 agent
        input_dict = {"messages": messages}

        res = self.agent.stream(input_dict, stream_mode="values", context={"report": False})
        # 收集完整的 AI 响应
        full_response = ""
        for chunk in res:
            if not isinstance(chunk, dict): # 确保 chunk 是一个字典
                continue

            # 获取最新的消息内容
            msg_list = chunk.get("messages") or chunk.get("message")
            if msg_list:
                try:
                    latest = msg_list[-1] # 获取最新的消息
                    content = getattr(latest, "content", None) or (
                        latest.get("content") if isinstance(latest, dict) else None
                    ) # 兼容不同消息格式
                    if isinstance(content, str) and content.strip():  # 确保 content 是非空字符串
                        yield content.strip() + "\n"
                        full_response += content.strip()
                        continue
                except Exception:
                    pass

            # # 处理其他字段
            # text = chunk.get("text") or chunk.get("content") or chunk.get("delta")
            # if isinstance(text, dict):
            #     text = text.get("content") or text.get("text")
            # if isinstance(text, str) and text.strip():
            #     yield text.strip() + "\n"
            #     full_response += text.strip()

    # 保存 AI 响应到历史
        if full_response:
            self.message_history.append(AIMessage(content=full_response))
            logger.info(f"[对话记录] 用户: {query[:50]}... | AI: {full_response[:50]}...")

    def get_history(self) -> List[dict]:
        """获取对话历史"""
        history = []
        for msg in self.message_history:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": msg.content})
        return history
    
    def clear_history(self):
        """清空对话历史"""
        self.message_history = []
        logger.info(f"[对话记录] 用户 {self.user_id} 的历史已清空")        





if __name__ == "__main__":
    agent = ReactAgent()
    query = "生成使用报告"
    for chunk in agent.execute_stream(query):
        print(chunk,end="",flush=True)