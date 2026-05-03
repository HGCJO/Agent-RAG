# 整个工程的路径
import os

# 获取项目根目录的绝对路径
def get_project_root():
    # 当前文件的绝对路径
    current_file_path = os.path.abspath(__file__)
    
    # 当前文件所在目录的父目录（即项目根目录）
    project_root = os.path.dirname(os.path.dirname(current_file_path))
    
    return project_root

# 根据相对路径获取绝对路径
def get_abs_path(relative_path):#传递相对路径，返回绝对路径
    project_root = get_project_root()

    abs_path = os.path.join(project_root, relative_path)

    return abs_path
