import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from rag.vector_store import VectorStoreService
from utils.logger_handler import logger
from utils.config_handler import chroma_conf

class KnowledgeBaseManager:
    """知识库管理类"""
    
    def __init__(self):
        self.vector_store_service = VectorStoreService()
        self.md5_store_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", chroma_conf.get("md5_hex_store", "md5.txt"))
        )
        # 文档元数据存储文件
        self.metadata_store_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "chroma_db", "documents_metadata.json")
        )
        self._init_metadata_store()
    
    def _init_metadata_store(self):
        """初始化文档元数据存储"""
        os.makedirs(os.path.dirname(self.metadata_store_path), exist_ok=True)
        if not os.path.exists(self.metadata_store_path):
            with open(self.metadata_store_path, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
    
    def get_all_documents(self) -> List[Dict]:
        """获取所有已上传的文档"""
        try:
            with open(self.metadata_store_path, "r", encoding="utf-8") as f:
                documents = json.load(f)
            logger.info(f"[知识库] 获取文档列表，共 {len(documents)} 个文档")
            return documents
        except Exception as e:
            logger.error(f"[知识库] 读取文档列表失败: {e}")
            return []
    
    def _save_documents_metadata(self, documents: List[Dict]) -> None:
        """保存文档元数据"""
        try:
            with open(self.metadata_store_path, "w", encoding="utf-8") as f:
                json.dump(documents, f, ensure_ascii=False, indent=2)
            logger.info(f"[知识库] 元数据已更新，共 {len(documents)} 个文档")
        except Exception as e:
            logger.error(f"[知识库] 保存元数据失败: {e}")
    
    def add_document_metadata(self, file_name: str, md5_hex: str, chunk_count: int) -> bool:
        """添加文档元数据记录"""
        try:
            documents = self.get_all_documents()
            
            # 检查是否已存在
            if any(doc["md5"] == md5_hex for doc in documents):
                logger.warning(f"[知识库] 文档 {file_name} (MD5: {md5_hex}) 已存在")
                return False
            
            # 添加新文档记录
            new_doc = {
                "id": len(documents) + 1,
                "file_name": file_name,
                "md5": md5_hex,
                "chunk_count": chunk_count,
                "upload_time": datetime.now().isoformat(),
                "status": "active"
            }
            documents.append(new_doc)
            self._save_documents_metadata(documents)
            logger.info(f"[知识库] 添加文档记录: {file_name}")
            return True
        
        except Exception as e:
            logger.error(f"[知识库] 添加文档元数据失败: {e}")
            return False
    
    def delete_document(self, file_name: str) -> Tuple[bool, str]:
        """
        删除指定文档及其所有相关数据
        
        Args:
            file_name: 文件名
        
        Returns:
            (success, message)
        """
        try:
            documents = self.get_all_documents()
            
            # 查找文档
            doc_index = None
            target_doc = None
            for idx, doc in enumerate(documents):
                if doc["file_name"] == file_name:
                    doc_index = idx
                    target_doc = doc
                    break
            
            if doc_index is None:
                msg = f"文档 '{file_name}' 不存在"
                logger.warning(f"[知识库] {msg}")
                return False, msg
            
            # 获取文档 MD5
            doc_md5 = target_doc.get("md5")
            
            # 步骤 1：从向量库中删除该文档对应的所有向量
            try:
                self.vector_store_service.vector_store.delete(
                    where={"source": file_name}
                )
                logger.info(f"[知识库] 已从向量库删除文档: {file_name}")
            except Exception as e:
                logger.warning(f"[知识库] 向量库删除可能失败: {e}")
                # 继续执行，不中断整个删除流程
            
            # 步骤 2：从 MD5 记录中删除
            if doc_md5:
                self._remove_md5_record(doc_md5)
            
            # 步骤 3：从元数据中标记为删除或移除
            # 方式 1：标记为删除（保留记录）
            documents[doc_index]["status"] = "deleted"
            documents[doc_index]["delete_time"] = datetime.now().isoformat()
            
            # 方式 2：直接删除（完全移除）
            # documents.pop(doc_index)
            
            self._save_documents_metadata(documents)
            
            msg = f"文档 '{file_name}' 已删除"
            logger.info(f"[知识库] {msg}")
            return True, msg
        
        except Exception as e:
            msg = f"删除文档失败: {str(e)}"
            logger.error(f"[知识库] {msg}", exc_info=True)
            return False, msg

    def _remove_md5_record(self, md5_hex: str) -> None:
        """从 MD5 记录中删除指定的 MD5"""
        try:
            if not os.path.exists(self.md5_store_path):
                return
            
            with open(self.md5_store_path, "r", encoding="utf-8") as f:
                md5_lines = f.readlines()
            
            # 移除匹配的 MD5
            md5_lines = [line for line in md5_lines if line.strip() != md5_hex]
            
            with open(self.md5_store_path, "w", encoding="utf-8") as f:
                f.writelines(md5_lines)
            
            logger.info(f"[知识库] 已从 MD5 记录中删除: {md5_hex}")
        
        except Exception as e:
            logger.error(f"[知识库] 删除 MD5 记录失败: {e}")
    def update_document(self, old_file_name: str, new_file_bytes: bytes, new_file_name: str, file_type: str) -> Tuple[bool, str, Dict]:
        """
        更新文档（删除旧版本 + 上传新版本）
        
        Args:
            old_file_name: 原文件名
            new_file_bytes: 新文件字节内容
            new_file_name: 新文件名
            file_type: 新文件 MIME 类型
        
        Returns:
            (success, message, stats)
        """
        try:
            # 步骤 1：删除旧文档
            delete_success, delete_msg = self.delete_document(old_file_name)
            if not delete_success:
                return False, f"删除旧文档失败: {delete_msg}", {}
            
            # 步骤 2：上传新文档
            # 需要调用文件上传服务
            from utils.file_uploader_service import FileUploadService
            upload_service = FileUploadService()
            
            success, upload_msg, upload_stats = upload_service.upload_file(
                file_bytes=new_file_bytes,
                file_name=new_file_name,
                file_type=file_type
            )
            
            if success:
                msg = f"文档已更新: '{old_file_name}' → '{new_file_name}'"
                logger.info(f"[知识库] {msg}")
                return True, msg, upload_stats
            else:
                return False, f"上传新文档失败: {upload_msg}", {}
        
        except Exception as e:
            msg = f"更新文档失败: {str(e)}"
            logger.error(f"[知识库] {msg}", exc_info=True)
            return False, msg, {}
    
    def get_document_stats(self) -> Dict:
        """获取知识库统计信息"""
        try:
            documents = self.get_all_documents()
            active_docs = [d for d in documents if d.get("status") == "active"]
            deleted_docs = [d for d in documents if d.get("status") == "deleted"]
            
            total_chunks = sum(doc.get("chunk_count", 0) for doc in active_docs)
            
            return {
                "total_documents": len(active_docs),
                "deleted_documents": len(deleted_docs),
                "total_chunks": total_chunks,
                "documents": active_docs
            }
        
        except Exception as e:
            logger.error(f"[知识库] 获取统计信息失败: {e}")
            return {}
 
        """从 MD5 记录中删除"""
        try:
            if not os.path.exists(self.md5_store_path):
                return
            
            with open(self.md5_store_path, "r", encoding="utf-8") as f:
                md5_lines = f.readlines()
            
            # 移除匹配的 MD5
            md5_lines = [line for line in md5_lines if line.strip() != md5_hex]
            
            with open(self.md5_store_path, "w", encoding="utf-8") as f:
                f.writelines(md5_lines)
            
            logger.info(f"[知识库] 已从 MD5 记录中删除: {md5_hex}")
        
        except Exception as e:
            logger.error(f"[知识库] 删除 MD5 记录失败: {e}")