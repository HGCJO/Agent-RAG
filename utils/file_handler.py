import os,hashlib
from utils.logger_handler import logger
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredWordDocumentLoader

def get_file_md5_hex(filepath:str):             #获取文件的md5的十六进制字符串
    if not os.path.isfile(filepath):
        logger.error(f"[md5计算]文件不存在: {filepath}")
        return
    if not os.path.isfile(filepath):
        logger.error(f"[md5计算]路径不是文件: {filepath}")
        return
    md5_obj = hashlib.md5()

    chunk_size = 4096 #每次读取4KB的文件内容，避免一次性加载大文件导致内存占用过高
    try:
        with open(filepath,'rb') as f:
            while chunk := f.read(chunk_size):
                md5_obj.update(chunk)
        md5_hex = md5_obj.hexdigest()
        return md5_hex
    
    except Exception as e:
        logger.error(f"[md5计算]读取文件{filepath}时发生错误: {str(e)}")
        return None


def listdir_with_allowed_type(path:str, allowed_type:tuple[str]):  #返回文件夹内的文件列表
    files = []

    if not os.path.isdir(path):
        logger.error(f"[文件列表]路径不是文件夹: {path}")
        return allowed_type
    for f in os.listdir(path):
        if f.endswith(allowed_type):#检查文件是否以允许的类型结尾，如果是则添加到文件列表中
            files.append(os.path.join(path,f))

    return tuple(files)




def pdf_loader(filepath:str,password = None)->list[Document]:                   #加载pdf文件，返回文本内容
    return PyPDFLoader(filepath,password).load()

def txt_loader(filepath:str)->list[Document]:                   #加载txt文件，返回文本内容
    return TextLoader(filepath,encoding='utf-8').load()

def doc_loader(filepath:str)->list[Document]:                   #加载doc文件，返回文本内容
    return UnstructuredWordDocumentLoader(filepath).load()