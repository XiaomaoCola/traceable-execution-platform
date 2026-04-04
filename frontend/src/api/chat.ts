import request from "@/utils/request";

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ChatRequest {
  model: string;
  messages: ChatMessage[];
  stream?: boolean;
  temperature?: number;
  max_tokens?: number;
}

export interface ChatResponse {
  choices: {
    message: ChatMessage;
    finish_reason: string;
  }[];
}

// TODO: 确认后端支持的模型名称（现在是 local-mistral，需要 Ollama 运行）
export const MODEL = "local-mistral";

export const chatCompletions = (messages: ChatMessage[]) =>
  request.post<ChatResponse>("/chat/completions", {
    model: MODEL,
    messages,
    stream: false,       // TODO: 如果后端支持流式输出，改成 true 并用 EventSource 处理
    temperature: 0.7,
    max_tokens: 1000
  });