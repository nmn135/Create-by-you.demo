# 封印之殿 · 像素叙事 Demo

一个 2D 像素叙事游戏原型：玩家在像素村庄中与 NPC「老罗」自由对话，AI 实时生成回复，你的发言会改变世界状态（关系、场景色调），甚至触发一次「世界规则重编译」的元模式演出。

## 运行

需要 **Node.js 18+**。

方式一：双击 `启动demo.bat`（Windows）。
方式二：命令行 `node server.js`。

然后浏览器打开 <http://localhost:8890>。

## 操作

- `←` / `→` 移动
- `E` 与 NPC 对话
- 对话框输入文字后回车或点发送

## AI 对话配置（可选）

不配置也能玩，NPC 会走离线兜底回复。要体验实时 AI 对话，需要一把 **Doubao（豆包）Ark API Key**：

1. 在本目录（`game-prototypes/2d-narrative-demo/`）新建一个文件，名为 `.env`
2. 文件内容一行：
   ```
   DOUBAO_API_KEY=你的ark密钥
   ```
3. 保存后重启 `server.js`

`.env` 已被 gitignore 排除，密钥不会进仓库；也可以改用环境变量 `DOUBAO_API_KEY`。

## 彩蛋

试试对老罗说「这些都是程序吧？」或「你在骗我」。
