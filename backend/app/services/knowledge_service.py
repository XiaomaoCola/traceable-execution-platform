"""文档处理服务：文本提取 → 切片 → 向量化 → 存库。

【整体流程】

  1. 管理员通过 POST /knowledge/bases/{kb_id}/documents 上传文件
  2. API 层立刻把文件元信息写入 knowledge_documents（status=pending），然后返回
  3. FastAPI BackgroundTask 在后台异步调用 process_document()，执行：
       文件内容(bytes)
         → _extract_text()   提取纯文本
         → _chunk_text()     按段落切成若干小片（约 500 字/片）
         → OllamaEmbeddings  逐片调用 nomic-embed-text 生成 768 维向量
         → INSERT INTO knowledge_chunks（content + embedding）
         → UPDATE knowledge_documents SET status = 'ready'
  4. 用户提问时，_retrieve_knowledge() 在 knowledge_chunks 里做向量相似度检索，
     只返回 TOP_K 条最相关的片段，注入到 LLM 的 system prompt 里。

【关键设计决策：为什么要"切片"而不是整文件向量化？】

  LLM 的 embedding 模型（nomic-embed-text）输入有 token 上限（约 8192 token），
  整份 PDF 直接 embed 会截断，而且一个向量代表整篇文章，语义太模糊，
  检索时很难精确匹配用户的具体问题。

  切成小片后，每片只聚焦一个具体概念，向量语义更精准，
  检索时更容易命中真正相关的内容。

【已知问题：同一个 KB 文件越多，向量库越大，检索精度会下降】

  原因：
    TOP_K = 4 是从所有 chunk 里选最相似的 4 条。
    KB 里文件多 → chunk 总数多 → 相似度分布更分散 → top-4 可能混入不相关内容。

    举例：KB 里有 5 个文件共 60 个 chunk，检索"退货流程"，
    60 条里最相关的 4 条可能都来自同一个文件，没问题。
    但如果 KB 里有 50 个文件共 600 个 chunk，
    top-4 里可能混入语义上"沾边但不准确"的 chunk，
    导致 LLM 收到的上下文质量下降。

  现阶段可接受（文件数量有限），未来优化方向：
    1. 加 HNSW 向量索引（目前是全表扫描）
       ALTER TABLE knowledge_chunks ADD COLUMN ... ;
       CREATE INDEX ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);
       数据量上千条后搜索速度会从线性降为对数级。

    2. 检索前加一层"先过滤 document_id"的粗筛
       比如先让 LLM 判断问题属于哪个文件类别，再在该文件的 chunk 里检索，
       避免跨文件的语义干扰。（高考场景按省份先过滤就是这个思路）

    3. 调大 TOP_K 并在注入 LLM 前做二次重排（rerank）
       用更小的 rerank 模型对 top-20 结果打分，选出真正相关的 4 条再喂给 LLM。
"""

import io
import logging

from sqlalchemy import select

logger = logging.getLogger(__name__)

CHUNK_SIZE = 500     # 每个切片的目标字符数
CHUNK_OVERLAP = 50   # 相邻切片的重叠字符数，保证语义在切片边界不断裂


def _extract_text(filename: str, content: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            raise RuntimeError("pypdf 未安装，无法解析 PDF。请运行 poetry add pypdf。")
    # txt / md 等纯文本
    return content.decode("utf-8", errors="ignore")


def _chunk_text(text: str) -> list[str]:
    """按段落切片，超长段落按字符数截断，相邻块有少量重叠。

    策略：
      - 优先按 \\n\\n（段落边界）切，尽量保证每片是完整的语义单元。
      - 段落本身超过 CHUNK_SIZE，强制按字符截断，截断处有 CHUNK_OVERLAP 字符重叠。
      - 段落较短时，累积到接近 CHUNK_SIZE 再成片，减少碎片化。
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf = ""

    for para in paragraphs:
        # 单段就超长，强制按字符截断
        if len(para) > CHUNK_SIZE:
            for i in range(0, len(para), CHUNK_SIZE - CHUNK_OVERLAP):
                chunks.append(para[i: i + CHUNK_SIZE])
            continue

        if len(buf) + len(para) + 2 > CHUNK_SIZE:
            if buf:
                chunks.append(buf)
            # 把上一块末尾带过来一点，保证语义连贯
            buf = buf[-CHUNK_OVERLAP:] + "\n\n" + para if buf else para
        else:
            buf = (buf + "\n\n" + para).strip() if buf else para

    if buf:
        chunks.append(buf)

    return [c for c in chunks if c.strip()]


async def process_document(document_id: int, filename: str, content: bytes) -> None:
    """后台任务：提取文本 → 切片 → embed → 写库，最后更新 status。

    此函数由 FastAPI BackgroundTask 调用，在 HTTP 响应返回后异步执行。
    调用方（upload_document API）已将 status 设为 pending 并返回给前端，
    本函数执行完毕后将 status 改为 ready（或 failed）。

    每个 chunk 单独调用一次 Ollama embed，chunk 数量多时耗时较长，
    这是当前实现的性能瓶颈，未来可考虑批量 embed 接口优化。

    数据库相关 import 放在函数内部（延迟导入），避免模块加载时触发
    pydantic-settings 读取环境变量，使纯函数测试（_chunk_text 等）
    可以在没有数据库配置的环境（如 CI）中正常运行。
    """
    from langchain_ollama import OllamaEmbeddings
    from backend.app.db.session import AsyncSessionLocal
    from backend.app.models.knowledge import KnowledgeDocument, KnowledgeChunk, DocumentStatus

    embeddings = OllamaEmbeddings(
        model="nomic-embed-text",
        base_url="http://host.docker.internal:11434",
    )

    try:
        text = _extract_text(filename, content)
        chunks = _chunk_text(text)

        async with AsyncSessionLocal() as db:
            for idx, chunk_text in enumerate(chunks):
                vec = await embeddings.aembed_query(chunk_text)
                db.add(KnowledgeChunk(
                    document_id=document_id,
                    content=chunk_text,
                    chunk_index=idx,
                    embedding=vec,
                ))

            result = await db.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
            )
            doc = result.scalar_one()
            doc.status = DocumentStatus.ready
            await db.commit()

        logger.info("document %d processed: %d chunks", document_id, len(chunks))

    except Exception:
        logger.exception("failed to process document %d", document_id)
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
            )
            doc = result.scalar_one_or_none()
            if doc:
                doc.status = DocumentStatus.failed
                await db.commit()
