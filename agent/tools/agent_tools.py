from langchain_core.tools import tool
from rag.rag_service import RagSummarizeService
rag = RagSummarizeService()
import random
from utils.config_handler import agent_conf
from utils.path_tool import get_abs_path
import os
from utils.logger_handler import logger
user_ids = ["1001", "1002", "1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010"]
month_arr = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06", "2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12"]
external_data = {}

@tool(description="使用RAG方法总结回答用户的问题")
def rag_summarize(query:str)->str:
    """
    使用RAG方法总结回答用户的问题
    """
    return rag.rag_summarize(query)

@tool(description="获取天气信息的工具函数，输入城市名称，返回天气信息")
def get_weather(city:str)->str:
    """
    获取天气信息的工具函数，输入城市名称，返回天气信息
    """
    # 这里可以调用第三方天气API获取天气信息，或者使用模拟数据
    return f"{city}的天气是晴天，温度25度。"

@tool(description="获取用户所在城市的名称，以纯字符串形式返回")
def get_user_location() -> str:
    """
    获取用户所在城市的名称，以纯字符串形式返回
    """
    return random.choice(["北京", "上海", "广州", "深圳", "杭州"])


@tool(description="获取用户的ID，以纯字符串形式返回")
def get_user_id() -> str:
    """
    获取用户ID，以纯字符串形式返回
    """
    return random.choice(user_ids)

@tool(description="获取当前月份，返回格式为字符串")
def get_current_month() -> str:
    """
    获取当前月份，返回格式为字符串
    """
    return random.choice(month_arr)

def generate_external_data():
    """
    {
    "1001": {
        "2025-01": {
            "特征": "功能A,功能B",
            "效率": "高",
            "耗材": "耗材X,耗材Y",
            "对比": "与上月相比，功能A使用增加，功能B使用减少，效率提高，耗材X使用增加，耗材Y使用减少"
        },
    }

    """
    if not external_data:
        external_data_path = agent_conf["external_data_path"] = get_abs_path(agent_conf["external_data_path"])
        if not os.path.isfile(external_data_path):
            raise FileNotFoundError(f"外部数据文件不存在: {external_data_path}")
        with open(external_data_path, 'r', encoding='utf-8') as f:
            for line in f.readlines()[1:]: #跳过第一行表头
                arr: list[str] = line.strip().split(",")

                user_id : str = arr[0].replace('"', "") #去掉可能存在的引号
                feature : str = arr[1].replace('"', "")
                efficiency : str = arr[2].replace('"', "")
                consumeables : str = arr[3].replace('"', "")
                comparsion: str = arr[4].replace('"', "")
                time:str = arr[5].replace('"', "")

                if user_id not in external_data:
                    external_data[user_id] = {}

                external_data[user_id][time] = {
                    "特征": feature,
                    "效率": efficiency,
                    "耗材": consumeables,
                    "对比": comparsion
                }
  
@tool(description="从外部系统中获取用户在指定月份的使用记录，以纯字符串形式返回，没有检索到记录时返回空字符串")
def fetch_external_data(user_id:str, month:str) -> str:
    """
    从外部系统中获取用户的使用记录，以纯字符串形式返回，没有检索到记录时返回空字符串
    """ 
    generate_external_data()
    try:
        return external_data[user_id][month]
    except KeyError:
        logger.warning(f"未找到用户{user_id}在{month}的使用记录")
        return ""
    


@tool(description="无入参，无返回值，调用之后触发中间件为报告生成的场景动态注入上下文信息，为后续提示词切换提供上下文")
def file_context_for_report():
    return "file_context_for_report已调用"


