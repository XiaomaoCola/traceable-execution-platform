<script setup lang="ts">
import { ref, nextTick } from "vue";
import { ElMessage } from "element-plus";
import { chatCompletions, type ChatMessage } from "@/api/chat";

const messages = ref<ChatMessage[]>([]);
const input = ref("");
const loading = ref(false);
const scrollRef = ref<HTMLElement>();

const scrollToBottom = async () => {
  await nextTick();
  if (scrollRef.value) {
    scrollRef.value.scrollTop = scrollRef.value.scrollHeight;
  }
};

const sendMessage = async () => {
  if (!input.value.trim() || loading.value) return;

  const userMsg: ChatMessage = { role: "user", content: input.value.trim() };
  messages.value.push(userMsg);
  input.value = "";
  loading.value = true;
  scrollToBottom();

  try {
    // TODO: 需要本地运行 Ollama + Mistral 模型才能正常响应
    const res = await chatCompletions(messages.value);
    const content = res.data.choices?.[0]?.message?.content || "无响应";
    messages.value.push({ role: "assistant", content });
  } catch (err: any) {
    const status = err?.response?.status;
    if (status === 503 || status === 502) {
      // TODO: AI 服务未启动时的提示，等 Ollama 配置好后这里会正常响应
      ElMessage.warning("AI 服务暂未启动，请先运行 Ollama");
      messages.value.push({
        role: "assistant",
        content: "⚠️ AI 服务暂未启动，请确认 Ollama 已运行并加载了 Mistral 模型。"
      });
    } else {
      ElMessage.error("请求失败");
      messages.value.push({ role: "assistant", content: "请求失败，请稍后重试。" });
    }
  } finally {
    loading.value = false;
    scrollToBottom();
  }
};

const clearMessages = () => {
  messages.value = [];
};
</script>

<template>
  <div class="chat-page">
    <div class="page-header">
      <h2>AI 对话</h2>
      <el-button @click="clearMessages" :disabled="messages.length === 0">清空对话</el-button>
    </div>

    <div class="chat-container">
      <!-- 消息列表 -->
      <div class="messages" ref="scrollRef">
        <div v-if="messages.length === 0" class="empty">
          <el-icon style="font-size: 40px; color: #ccc"><ChatDotRound /></el-icon>
          <p>发送消息开始对话</p>
          <!-- TODO: Ollama 启动后删掉这个提示 -->
          <p class="tip">⚠️ 需要本地运行 Ollama + Mistral 才能使用</p>
        </div>

        <div v-for="(msg, i) in messages" :key="i" class="message" :class="msg.role">
          <div class="avatar">{{ msg.role === "user" ? "我" : "AI" }}</div>
          <div class="bubble">{{ msg.content }}</div>
        </div>

        <div v-if="loading" class="message assistant">
          <div class="avatar">AI</div>
          <div class="bubble loading">
            <span class="dot">●</span>
            <span class="dot">●</span>
            <span class="dot">●</span>
          </div>
        </div>
      </div>

      <!-- 输入框 -->
      <div class="input-area">
        <el-input
          v-model="input"
          placeholder="输入消息，按 Enter 发送..."
          :disabled="loading"
          @keyup.enter="sendMessage"
          clearable
        />
        <el-button type="primary" :loading="loading" @click="sendMessage">发送</el-button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { ChatDotRound } from "@element-plus/icons-vue";
export default { components: { ChatDotRound } };
</script>

<style scoped>
.chat-page { height: 100%; display: flex; flex-direction: column; }

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
  overflow: hidden;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 400px;
  max-height: 600px;
}

.empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #999;
}

.tip { font-size: 12px; color: #f0a020; }

.message {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.message.user { flex-direction: row-reverse; }

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
  background: #409eff;
  color: white;
}

.message.assistant .avatar {
  background: #67c23a;
}

.bubble {
  max-width: 65%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.user .bubble {
  background: #409eff;
  color: white;
  border-radius: 12px 2px 12px 12px;
}

.assistant .bubble {
  background: #f0f2f5;
  color: #333;
  border-radius: 2px 12px 12px 12px;
}

.loading {
  display: flex;
  gap: 4px;
  align-items: center;
}

.dot {
  font-size: 8px;
  color: #999;
  animation: blink 1.2s infinite;
}

.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes blink {
  0%, 80%, 100% { opacity: 0.2; }
  40% { opacity: 1; }
}

.input-area {
  display: flex;
  gap: 8px;
  padding: 16px;
  border-top: 1px solid #f0f0f0;
}
</style>