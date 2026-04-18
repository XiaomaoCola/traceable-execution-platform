from sqlalchemy import Column, String, Text, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from backend.app.db.base import Base, IDMixin, TimestampMixin


class ChatSession(Base, IDMixin, TimestampMixin):
    """一段对话会话，与用户 1:1 绑定。

    【当前设计】一个用户只有一个永久会话，所有对话历史都在这里累积，
    实现长期记忆。user_id 加了 UNIQUE 约束来保证这一点。

    【如果以后要改成多会话（类似 ChatGPT 侧边栏）】：
      1. 去掉 UniqueConstraint('user_id')
      2. 加回 session_id 列（String，UUID，前端生成）作为对外标识
      3. 新增 POST /sessions 接口让用户主动创建新会话
      4. GET /sessions 接口返回该用户所有会话列表
      5. 聊天接口改为接收 session_id 参数，而不是直接用 user_id 查唯一会话
    """

    __tablename__ = "chat_sessions"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_chat_sessions_user_id"),
    )

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 会话标题，预留字段，多会话模式下可显示在侧边栏
    title = Column(String(200), nullable=True)

    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )

    def __repr__(self):
        return f"<ChatSession(id={self.id}, user_id={self.user_id})>"


class ChatMessage(Base, IDMixin, TimestampMixin):
    """单条消息记录，role 区分是用户还是 AI。"""

    __tablename__ = "chat_messages"

    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)

    # 'user' | 'assistant' | 'system'
    role = Column(String(20), nullable=False)

    content = Column(Text, nullable=False)

    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage(role='{self.role}', session_id={self.session_id})>"
