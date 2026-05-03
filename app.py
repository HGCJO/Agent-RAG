import streamlit as st
from agent.react_agent import ReactAgent
import time
import streamlit as st
from streamlit_option_menu import option_menu
from utils.knowledge_base_manager import KnowledgeBaseManager
from utils.message_store import MessageStore
# 配置页面
st.set_page_config(
    page_title="🤖 Agent-RAG 智能助手",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 自定义 CSS 样式
custom_css = """
<style>
    /* 美化主容器 */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
    }
    
    /* 美化标题 */
    h1 {
        color: #ffffff;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        font-size: 3rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    /* 美化输入框 */
    .stTextInput input {
        border-radius: 10px;
        border: 2px solid #667eea;
        padding: 12px;
    }
    
    /* 美化按钮 */
    .stButton button {
        border-radius: 8px;
        background: linear-gradient(90deg, #667eea, #764ba2);
        color: white;
        font-weight: bold;
        border: none;
        padding: 10px 20px;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* 美化对话框 */
    .chat-message {
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .chat-message.user {
        background: linear-gradient(90deg, #667eea, #764ba2);
        color: white;
        margin-left: 2rem;
    }
    
    .chat-message.assistant {
        background: #f0f2f6;
        color: #333;
        margin-right: 2rem;
    }
    
    /* 侧边栏美化 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9ff 0%, #f0f2f6 100%);
    }
    
    /* 上传区域美化 */
    .upload-area {
        border: 2px dashed #667eea;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        background: rgba(102, 126, 234, 0.05);
    }
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)
with st.sidebar:
    st.markdown("### 👤 用户设置")
    user_id = st.text_input(
        "请输入用户 ID：",
        value=st.session_state.get("user_id", "default_user"),
        placeholder="例如：user_001"
    )
    st.session_state["user_id"] = user_id
    
    st.divider()
    
    st.markdown("### 📚 导航菜单")
    page = option_menu(
        menu_title=None,
        options=["💬 对话", "📤 文件上传", "📊 知识库管理", "⚙️ 设置"],
        icons=["chat-dots", "file-arrow-up", "collection", "gear"],
        menu_icon="cast",
        default_index=0,
    )
# # 侧边栏导航菜单
# with st.sidebar:
#     st.markdown("### 📚 导航菜单")
#     page = option_menu(
#         menu_title=None,
#         options=["💬 对话", "📤 文件上传", "📊 知识库管理", "⚙️ 设置"],
#         icons=["chat-dots", "file-arrow-up", "collection", "gear"],
#         menu_icon="cast",
#         default_index=0,
#     )

# 主页面标题
st.markdown("""
    <div style='text-align: center; margin: 2rem 0;'>
        <h1>🤖 Agent-RAG 智能助手</h1>
        <p style='font-size: 1.1rem; color: #666;'>
            基于智能检索的个性化知识助手
        </p>
    </div>
""", unsafe_allow_html=True)

#===========================================
from utils.file_uploader_service import FileUploadService

# 初始化上传服务
upload_service = FileUploadService()

def upload_file_to_rag(uploaded_file):
    """上传文件到 RAG 向量库"""
    with st.spinner(f"正在上传 '{uploaded_file.name}'..."):
        file_bytes = uploaded_file.getvalue()
        success, message, stats = upload_service.upload_file(
            file_bytes=file_bytes,
            file_name=uploaded_file.name,
            file_type=uploaded_file.type
        )
        
        if success:
            st.success(f"✅ {message}")
            st.json(stats)
        else:
            st.error(f"❌ {message}")
            if "error" in stats:
                st.write(f"错误详情: {stats['error']}")


if page == "📤 文件上传":
    with st.sidebar:
        st.markdown("### 📤 知识库上传")
        
        # 文件上传组件
        uploaded_file = st.file_uploader(
            "选择要上传的文件",
            type=["pdf", "txt", "docx"],
            accept_multiple_files=False,
            help="支持 PDF、TXT、DOCX 格式"
        )
        
        if uploaded_file is not None:
            # 文件信息展示
            col1, col2 = st.columns(2)
            with col1:
                st.metric("文件名", uploaded_file.name)
            with col2:
                st.metric("文件大小", f"{uploaded_file.size / 1024:.2f} KB")
            
            # 预览功能（根据文件类型）
            file_type = uploaded_file.type
            st.markdown("#### 📋 文件预览")
            
            if file_type == "application/pdf":
                # PDF 预览逻辑（参考之前提供的代码）
                st.info("PDF 文件预览功能")
                # 调用 pdf_preview 函数
                
            elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                # DOCX 预览逻辑
                st.info("Word 文件预览功能")
                # 调用 docx_preview 函数
                
            elif file_type == "text/plain":
                # TXT 预览逻辑
                content = uploaded_file.getvalue().decode("utf-8", errors="ignore")
                st.text_area("文本内容预览", value=content[:500], height=200, disabled=True)
            
            # 上传按钮
            if st.button("✅ 上传到知识库", use_container_width=True):
                upload_file_to_rag(uploaded_file)
#===========================================
# # 初始化知识库管理
# if "kb_manager" not in st.session_state:
#     st.session_state["kb_manager"] = KnowledgeBaseManager()

# # ============ 知识库管理页面 ============
# if page == "📊 知识库管理":
#     st.markdown("### 📊 知识库管理")
#     st.write("管理已上传的文档，支持删除和更新操作")
    
#     # 创建三个选项卡
#     tab1, tab2, tab3 = st.tabs(["📋 文档列表", "🗑️ 删除文档", "🔄 更新文档"])
    
#     # 选项卡 1：文档列表
#     with tab1:
#         st.subheader("已上传的文档")
        
#         kb_manager = st.session_state["kb_manager"]
#         stats = kb_manager.get_document_stats()
        
#         # 显示统计信息
#         col1, col2, col3 = st.columns(3)
#         with col1:
#             st.metric("📚 文档总数", stats.get("total_documents", 0))
#         with col2:
#             st.metric("📦 分片总数", stats.get("total_chunks", 0))
#         with col3:
#             st.metric("🗑️ 已删除", stats.get("deleted_documents", 0))
        
#         st.divider()
        
#         # 显示文档列表
#         documents = stats.get("documents", [])
#         if documents:
#             for doc in documents:
#                 col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
#                 with col1:
#                     st.write(f"📄 {doc['file_name']}")
#                 with col2:
#                     st.write(f"分片: {doc['chunk_count']}")
#                 with col3:
#                     st.write(f"MD5: {doc['md5'][:8]}...")
#                 with col4:
#                     st.write(f"上传时间: {doc['upload_time'][:10]}")
#         else:
#             st.info("📭 暂无文档")
    
#     # 选项卡 2：删除文档
#     with tab2:
#         st.subheader("删除文档")
#         st.warning("⚠️ 删除后将无法恢复，请谨慎操作")
        
#         kb_manager = st.session_state["kb_manager"]
#         documents = kb_manager.get_all_documents()
#         active_docs = [d for d in documents if d.get("status") == "active"]
        
#         if active_docs:
#             doc_names = [doc["file_name"] for doc in active_docs]
#             selected_doc = st.selectbox("选择要删除的文档", doc_names)
            
#             if st.button("🗑️ 删除选中文档", use_container_width=True, type="secondary"):
#                 with st.spinner(f"正在删除 '{selected_doc}'..."):
#                     success, message = kb_manager.delete_document(selected_doc)
#                     if success:
#                         st.success(f"✅ {message}")
#                         st.rerun()
#                     else:
#                         st.error(f"❌ {message}")
#         else:
#             st.info("📭 没有可删除的文档")
#================================================

st.divider()

if "agent" not in st.session_state:
    st.session_state["agent"] = ReactAgent()
if "message" not in st.session_state:
    st.session_state["message"] = []

for message in st.session_state["message"]:
    st.chat_message(message["role"]).write(message["content"])

# # 用户输入框
# prompt = st.chat_input()

# if prompt:
#     st.chat_message("user").write(prompt)
#     st.session_state["message"].append({"role": "user", "content": prompt})

#     response_messages = []
#     with st.spinner("智能客服正在思考..."):
#         res_stream = st.session_state["agent"].execute_stream(prompt)

#         def capture(generate, cache_list):
#             for chunk in generate:
#                 cache_list.append(chunk)
#                 for char in chunk:
#                     time.sleep(0.01)  # 模拟打字效果
#                     yield char

#         st.chat_message("assistant").write_stream(capture(res_stream, response_messages))
#         st.session_state["message"].append({"role": "assistant", "content": response_messages[-1]})
#         st.rerun()


# 初始化消息存储
if "message_store" not in st.session_state:
    st.session_state["message_store"] = MessageStore(storage_dir="history")

if "user_id" not in st.session_state:
    st.session_state["user_id"] = "default_user"

# 用户输入框
prompt = st.chat_input()

if prompt:
    user_id = st.session_state["user_id"]
    message_store = st.session_state["message_store"]
    
    # 显示用户消息
    st.chat_message("user").write(prompt)
    st.session_state["message"].append({"role": "user", "content": prompt})
    
    # ✅ 保存用户消息到本地
    message_store.save_message(user_id, "user", prompt)
    
    response_messages = []
    with st.spinner("智能客服正在思考..."):
        res_stream = st.session_state["agent"].execute_stream(prompt)

        def capture(generate, cache_list):
            for chunk in generate:
                cache_list.append(chunk)
                for char in chunk:
                    time.sleep(0.01)
                    yield char


        st.chat_message("assistant").write_stream(capture(res_stream, response_messages))

        st.chat_message("assistant").write_stream(capture(res_stream, response_messages))
        
        # 合并响应（处理流式消息）
        full_response = "".join(response_messages)
        st.session_state["message"].append({"role": "assistant", "content": response_messages[-1]})
        
        # ✅ 保存 AI 响应到本地
        message_store.save_message(user_id, "assistant", full_response)
        
        st.rerun()