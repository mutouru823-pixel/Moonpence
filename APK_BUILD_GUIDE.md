# 📦 文风溯源 APK 打包指南

## 方案一：使用 WebViewGold（最简单，推荐 ⭐）

不需要安装 Android Studio，直接使用在线工具打包，5分钟搞定！

### 步骤：

1. **部署你的 Streamlit 应用到公网**
   - 推荐使用 [Streamlit Community Cloud](https://share.streamlit.io/)（免费）
   - 或使用 [Railway](https://railway.app/)、[Vercel](https://vercel.com/) 等平台

2. **打开 WebViewGold**
   - 访问：https://www.webviewgold.com/
   - 输入你的应用网址
   - 选择 "Android"

3. **配置应用信息**
   - App Name: `文风溯源`
   - Package Name: `com.wenfengsuyuan.app`
   - 上传 icon（使用你的应用图标）

4. **下载 APK**
   - 免费版会有水印，付费版可以去除水印

---

## 方案二：使用 Capacitor（技术流，免费）

需要安装 Android Studio，但完全免费，没有水印。

### 前置准备：
1. 安装 [Android Studio](https://developer.android.com/studio)
2. 安装 JDK 17+
3. 部署你的 Streamlit 应用到公网

### 步骤：

1. **初始化项目**
```bash
cd /workspace
npm init -y
npm install @capacitor/core @capacitor/cli @capacitor/android
npx cap init
```

2. **配置 capacitor.config.json**
```json
{
  "appId": "com.wenfengsuyuan.app",
  "appName": "文风溯源",
  "webDir": ".",
  "server": {
    "url": "你的应用部署地址",
    "cleartext": true
  }
}
```

3. **添加 Android 平台**
```bash
npx cap add android
npx cap sync
```

4. **打开 Android Studio**
```bash
npx cap open android
```

5. **在 Android Studio 中构建 APK**
   - 点击 `Build` → `Build Bundle(s) / APK(s)` → `Build APK(s)`
   - APK 位置：`android/app/build/outputs/apk/debug/`

---

## 方案三：使用 Hermit（极简方案）

如果只是想在手机上快速使用，可以使用 Hermit：
- 下载 Hermit：https://hermit.chromium.auroraoss.com/
- 输入你的应用网址，它会把你的应用变成一个轻量级的 app

---

## 📱 推荐方案对比

| 方案 | 难度 | 成本 | 水印 | 推荐度 |
|------|------|------|------|--------|
| WebViewGold | ⭐ 简单 | 低 | 有水印 | ⭐⭐⭐⭐ |
| Capacitor | ⭐⭐⭐ 复杂 | 免费 | 无 | ⭐⭐⭐ |
| Hermit | ⭐ 最简单 | 免费 | 无 | ⭐⭐⭐⭐⭐ |

---

## 💡 最佳实践

对于「文风溯源」这个应用，**我强烈推荐**：

1. **先部署到 Streamlit Community Cloud**
2. **让用户用手机浏览器访问**
3. **添加到主屏幕**（PWA 方式）

这样用户体验最好，不需要下载安装，而且能保持最新版本！
