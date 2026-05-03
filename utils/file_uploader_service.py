import os
import hashlib
from datetime import datetime
from typing import Optional, Dict, Tuple
from langchain_core.documents import Document
from rag.vector_store import VectorStoreService
from utils.config_handler import chroma_conf
from utils.logger_handler import logger
from utils.file_handler import pdf_loader, txt_loader, doc_loader

class FileUploadService:
    """文件上传服务类"""
    
    def __init__(self):
        self.vector_store_service = VectorStoreService()
        self.md5_store_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", chroma_conf.get("md5_hex_store", "md5.txt"))
        )
        # 延迟导入以避免循环依赖
        self.kb_manager = None
        
        # 确保 md5 存储文件存在
        os.makedirs(os.path.dirname(self.md5_store_path), exist_ok=True)
        if not os.path.exists(self.md5_store_path):
            open(self.md5_store_path, "w", encoding="utf-8").close()
    
    def _get_kb_manager(self):
        """延迟获取知识库管理器（避免循环导入）"""
        if self.kb_manager is None:
            from utils.knowledge_base_manager import KnowledgeBaseManager
            self.kb_manager = KnowledgeBaseManager()
        return self.kb_manager
    
    def _calculate_md5(self, file_bytes: bytes) -> str:
        """计算文件的 MD5 哈希值"""
        return hashlib.md5(file_bytes).hexdigest()
    
    def _check_md5_exists(self, md5_hex: str) -> bool:
        """检查 MD5 是否已存在（文件是否已上传过）"""
        try:
            with open(self.md5_store_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return False
                existing_md5s = content.split("\n")
            return md5_hex in existing_md5s
        except Exception as e:
            logger.error(f"[MD5检查] 读取 MD5 文件失败: {e}")
            return False
    
    def _save_md5(self, md5_hex: str) -> None:
        """将 MD5 保存到文件"""
        try:
            with open(self.md5_store_path, "a", encoding="utf-8") as f:
                f.write(md5_hex + "\n")
            logger.info(f"[MD5保存] 成功保存 MD5: {md5_hex}")
        except Exception as e:
            logger.error(f"[MD5保存] 保存 MD5 失败: {e}")
    
    def upload_file(
        self, 
        file_bytes: bytes, 
        file_name: str, 
        file_type: str
    ) -> Tuple[bool, str, Dict]:
        """
        上传文件到向量库并记录元数据
        
        Args:
            file_bytes: 文件二进制内容
            file_name: 文件名
            file_type: 文件 MIME 类型
        
        Returns:
            (success, message, stats)
        """
        try:
            # 计算 MD5
            md5_hex = self._calculate_md5(file_bytes)
            logger.info(f"[上传] 文件 {file_name}, MD5: {md5_hex}")
            
            # 检查是否重复
            if self._check_md5_exists(md5_hex):
                msg = f"文件 '{file_name}' 已上传过，跳过。"
                logger.warning(f"[上传] {msg}")
                return False, msg, {"chunks": 0, "status": "skipped"}
            
            # 根据文件类型加载文档
            documents = self._load_documents(file_bytes, file_name, file_type)
            
            if not documents:
                msg = f"文件 '{file_name}' 无法解析或为空。"
                logger.error(f"[上传] {msg}")
                return False, msg, {"chunks": 0, "status": "failed"}
            
            # 分割文档
            split_docs = self.vector_store_service.spliter.split_documents(documents)
            
            if not split_docs:
                msg = f"文件 '{file_name}' 分片后无有效内容。"
                logger.warning(f"[上传] {msg}")
                return False, msg, {"chunks": 0, "status": "empty"}
            
            # 添加元数据
            for doc in split_docs:
                doc.metadata.update({
                    "source": file_name,
                    "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "md5": md5_hex,
                })
            
            # 添加到向量库
            self.vector_store_service.vector_store.add_documents(split_docs)
            
            # 保存 MD5
            self._save_md5(md5_hex)
            
            # ✅ 新增：保存文档元数据到知识库管理器
            kb_manager = self._get_kb_manager()
            metadata_saved = kb_manager.add_document_metadata(
                file_name=file_name,
                md5_hex=md5_hex,
                chunk_count=len(split_docs)
            )
            
            msg = f"文件 '{file_name}' 上传成功！"
            stats = {
                "file_name": file_name,
                "chunks": len(split_docs),
                "md5": md5_hex,
                "status": "success",
                "upload_time": datetime.now().isoformat(),
                "metadata_saved": metadata_saved
            }
            logger.info(f"[上传] {msg} 分片数: {len(split_docs)}")
            return True, msg, stats
            
        except Exception as e:
            msg = f"上传文件 '{file_name}' 时发生错误: {str(e)}"
            logger.error(f"[上传] {msg}", exc_info=True)
            return False, msg, {"chunks": 0, "status": "error", "error": str(e)}
    
    
    def _load_documents(self, file_bytes: bytes, file_name: str, file_type: str) -> list[Document]:
        """根据文件类型加载文档"""
        import io
        
        try:
            if file_type == "application/pdf":
                # 临时保存为文件（某些loader需要文件路径）
                temp_path = f"/tmp/{file_name}"
                os.makedirs(os.path.dirname(temp_path) or ".", exist_ok=True)
                with open(temp_path, "wb") as f:
                    f.write(file_bytes)
                docs = pdf_loader(temp_path)
                os.remove(temp_path)
                return docs
            
            elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                # DOCX 文件
                temp_path = f"/tmp/{file_name}"
                os.makedirs(os.path.dirname(temp_path) or ".", exist_ok=True)
                with open(temp_path, "wb") as f:
                    f.write(file_bytes)
                docs = doc_loader(temp_path)
                os.remove(temp_path)
                return docs
            
            elif file_type == "text/plain":
                # TXT 文件
                text_content = file_bytes.decode("utf-8", errors="ignore")
                return [Document(page_content=text_content, metadata={"source": file_name})]
            
            else:
                logger.error(f"[上传] 不支持的文件类型: {file_type}")
                return []
        
        except Exception as e:
            logger.error(f"[上传] 加载文档 {file_name} 失败: {e}", exc_info=True)
            return []