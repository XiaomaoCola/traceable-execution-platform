import { createApp } from "vue";
import { createPinia } from "pinia";
import router from "./router";
import App from "./App.vue";
import setupElementPlus from "./plugins/element-plus";
import "./styles/index.css";
import { useUserStore } from "@/stores/user";

const app = createApp(App);
app.use(createPinia());
app.use(router);
setupElementPlus(app);

// 刷新页面时重新获取用户信息
const userStore = useUserStore();
if (userStore.token) {
  userStore.fetchUserInfo();
}

app.mount("#app");