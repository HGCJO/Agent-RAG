from .config_handler import prompts_conf
from .path_tool import get_abs_path
from .logger_handler import logger

def load_system_prompts():
    try:
        system_prompt_path = get_abs_path(prompts_conf["main_prompt_path"])

    except KeyError as e:
        logger.error(f"[load_system_prompts]配置中缺少main_prompt_path")
        raise e
    
    try:
        return open(system_prompt_path, 'r', encoding='utf-8').read()
    except Exception as e:
        logger.error(f"[load_system_prompts]加载系统提示词失败: {str(e)}")
        raise e

def load_rag_prompts():
    try:
        system_prompt_path = get_abs_path(prompts_conf["rag_summarize_prompt_path"])

    except KeyError as e:
        logger.error(f"[load_rag_summarize_prompts]配置中缺少rag_summarize_prompt_path")
        raise e
    
    try:
        return open(system_prompt_path, 'r', encoding='utf-8').read()
    except Exception as e:
        logger.error(f"[load_rag_summarize_prompts]加载RAG提示词失败: {str(e)}")
        raise e
    


def load_report_prompts():
    try:
        system_prompt_path = get_abs_path(prompts_conf["report_prompt_path"])

    except KeyError as e:
        logger.error(f"[load_report_prompts]配置中缺少report_prompt_path")
        raise e
    
    try:
        return open(system_prompt_path, 'r', encoding='utf-8').read()
    except Exception as e:
        logger.error(f"[load_report_prompts]加载报告提示词失败: {str(e)}")
        raise e
    

if __name__ == "__main__":
    print(load_system_prompts())
