import request from "@/utils/request";
import type { User } from "@/types/user";

// 登录接口的返回值类型
interface LoginResponse {
  access_token: string; // 登录成功后返回的 JWT token，后续请求需携带它
  token_type: string;   // token 类型，通常是 "bearer"
}

// 登录：传入用户名和密码，返回 token
export const login = (username: string, password: string) =>
  request.post<LoginResponse>("/auth/login", { username, password });

// 获取当前已登录的用户信息（依赖请求头中携带的 token）
export const getMe = () =>
  request.get<User>("/auth/me");