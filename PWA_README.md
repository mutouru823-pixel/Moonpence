# 📱 PWA 手机端部署指南

## 方案一：使用 Streamlit Community Cloud (推荐)

1. 把代码推送到 GitHub
2. 在 [Streamlit Community Cloud](https://share.streamlit.io/) 部署
3. 使用 HTTPS 访问应用
4. 在手机浏览器中打开并添加到主屏幕

## 方案二：本地测试

### 使用 `streamlit-static` 提供静态文件

首先安装依赖：
```bash
pip install streamlit
```

由于 Streamlit 不直接支持静态文件服务，我们需要一个简单的静态文件服务器。

### 方法 A：使用简单的启动脚本

创建 `serve.py`：

```python
import os
import threading
import http.server
import socketserver
from streamlit.web import cli as stcli

# 启动静态文件服务器
def start_static_server():
    PORT = 8502
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"静态文件服务器运行在 http://localhost:{PORT}")
        httpd.serve_forever()

# 启动 Streamlit 应用
def start_streamlit():
    import sys
    sys.argv = ["streamlit", "run", "app.py"]
    stcli.main()

if __name__ == "__main__":
    # 先启动静态服务器
    static_thread = threading.Thread(target=start_static_server)
    static_thread.daemon = True
    static_thread.start()
    
    # 再启动 Streamlit
    start_streamlit()
```

然后修改 `app.py` 中的 manifest 链接：
```python
<link rel="manifest" href="http://localhost:8502/manifest.json">
```

### 方法 B：使用 nginx 反向代理（生产环境）

使用 nginx 来同时提供静态文件和代理 Streamlit 应用。

## 方案三：使用 Heroku/Vercel/Railway 部署

这些平台支持同时提供静态文件和运行 Streamlit 应用。

---

## 📱 在手机上使用

### iOS (Safari)
1. 打开 Safari 访问应用
2. 点击分享按钮
3. 向下滚动，选择「添加到主屏幕」
4. 点击「添加」

### Android (Chrome)
1. 打开 Chrome 访问应用
2. 点击右上角菜单
3. 选择「安装应用」或「添加到主屏幕」
4. 点击「添加」

---

## 📦 进一步打包为原生 APP

如果需要真正的 `.apk` 或 `.ipa` 文件，可以使用：

- **Capacitor** - 把 PWA 打包成原生 app
- **Cordova** - 类似 Capacitor 的老牌工具
- **WebViewGold** - 在线工具，直接把网站打包成 app

### 使用 Capacitor 的步骤：

1. 安装 Capacitor：
```bash
npm install -g @capacitor/core @capacitor/cli @capacitor/android @capacitor/ios
```

2. 初始化：
```bash
npx cap init
```

3. 配置 `capacitor.config.json`：
```json
{
  "appId": "com.wenfengsuyuan.app",
  "appName": "文风溯源",
  "webDir": "www",
  "server": {
    "url": "你的部署地址"
  }
}
```

4. 添加平台：
```bash
npx cap add android
npx cap add ios
```

5. 构建：
```bash
npx cap build android
```

这样就可以生成可以安装到手机的原生 app 了！
