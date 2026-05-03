import logging
import os
from .path_tool import get_abs_path
from datetime import datetime
#日志保存的根目录
LOG_ROOT = get_abs_path("logs")

os.makedirs(name=LOG_ROOT, exist_ok=True)

#日志的格式配置 error info debug
DEFAULT_LOG_FORMAT = logging.Formatter(
    fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def get_logger(
    name: str = "agent",
    console_log_level: int = logging.INFO,
    file_log_level: int = logging.DEBUG,
    log_file: str = None #日志文件路径，如果为None则不保存日志到文件
) ->logging.Logger:#继承logging.Logger类，返回一个日志对象
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG) #设置根日志级别为DEBUG，确保所有日志都能被处理

    #如果日志记录器已经有处理器了，就直接返回，避免重复添加处理器
    if logger.handlers:
        return logger
    
    #控制台日志处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_log_level)
    console_handler.setFormatter(DEFAULT_LOG_FORMAT)
    logger.addHandler(console_handler)
    #文件日志处理器
    if not log_file:
        log_file = os.path.join(LOG_ROOT, f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    file_handler = logging.FileHandler(log_file,encoding="utf-8")
    file_handler.setLevel(file_log_level)
    file_handler.setFormatter(DEFAULT_LOG_FORMAT)
    logger.addHandler(file_handler)

    return logger


#快捷获取日志记录器
logger = get_logger()


