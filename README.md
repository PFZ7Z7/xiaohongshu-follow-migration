# 小红书关注列表迁移工具

> 将一个小红书账号的关注列表，迁移到另一个账号

## 📖 目录

- [功能说明](#-功能说明)
- [适用场景](#-适用场景)
- [准备工作](#-准备工作)
- [安装步骤](#-安装步骤)
  - [Windows安装](#windows安装)
  - [Mac安装](#mac安装)
- [使用教程](#-使用教程)
  - [第一步：导出关注列表](#第一步导出关注列表)
  - [第二步：批量关注新账号](#第二步批量关注新账号)
- [常见问题](#-常见问题)
- [注意事项](#-注意事项)

---

## 📋 功能说明

**一句话描述：** 把账号A的关注列表，复制到账号B

**特点：**
- ✅ 自动导出关注列表
- ✅ 自动批量关注
- ✅ 进度实时显示
- ✅ 支持中断后继续
- ✅ 只在新账号关注，**不取消老账号的关注**

---

## 🎯 适用场景

| 场景 | 说明 |
|------|------|
| 换号 | 老账号不用了，想把关注的人转移到新账号 |
| 备份 | 导出关注列表，防止账号丢失 |
| 批量操作 | 不想手动一个个点关注 |

---

## 💻 准备工作

在开始之前，请确保你有：

1. **电脑** - Windows 10/11 或 macOS 10.15+
2. **Python** - 版本 3.8 或更高
3. **小红书账号** - 老账号（要导出）和新账号（要关注）
4. **手机** - 用于扫码登录小红书

---

## 📥 安装步骤

### Windows安装

#### 第1步：安装Python

1. 打开浏览器，访问 https://www.python.org/downloads/
2. 下载最新版Python（点击 "Download Python 3.x.x"）
3. 运行安装程序
4. **重要：** 勾选 "Add Python to PATH"
5. 点击 "Install Now"

#### 第2步：下载项目

**方法A：使用Git（推荐）**
```bash
# 打开命令提示符（按Win+R，输入cmd，回车）
git clone https://github.com/PFZ7Z7/xiaohongshu-follow-migration.git
cd xiaohongshu-follow-migration
```

**方法B：直接下载**
1. 访问 https://github.com/PFZ7Z7/xiaohongshu-follow-migration
2. 点击绿色按钮 "Code" → "Download ZIP"
3. 解压到任意文件夹
4. 打开命令提示符，进入该文件夹

#### 第3步：安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 安装依赖
pip install playwright tqdm

# 安装浏览器
playwright install chromium
```

---

### Mac安装

#### 第1步：安装Python

**方法A：使用Homebrew（推荐）**
```bash
# 打开终端（Command+空格，输入Terminal）
# 如果没有Homebrew，先安装：
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装Python
brew install python3
```

**方法B：官网下载**
1. 访问 https://www.python.org/downloads/
2. 下载macOS版本
3. 运行安装程序

#### 第2步：下载项目

**方法A：使用Git**
```bash
git clone https://github.com/PFZ7Z7/xiaohongshu-follow-migration.git
cd xiaohongshu-follow-migration
```

**方法B：直接下载**
1. 访问 https://github.com/PFZ7Z7/xiaohongshu-follow-migration
2. 点击 "Code" → "Download ZIP"
3. 解压到任意文件夹
4. 打开终端，进入该文件夹

#### 第3步：安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install playwright tqdm

# 安装浏览器
playwright install chromium
```

---

## 🚀 使用教程

### 第一步：导出关注列表

#### 1.1 运行导出命令

```bash
# 确保虚拟环境已激活
# Windows: venv\Scripts\activate
# Mac: source venv/bin/activate

python main.py export --account old_account
```

#### 1.2 扫码登录

1. 脚本会自动打开浏览器
2. 浏览器显示小红书登录页面
3. **用手机小红书APP扫码登录**
4. 登录成功后，回到命令行窗口
5. 按 **回车键** 继续

#### 1.3 等待导出完成

- 脚本会自动滚动页面，加载所有关注用户
- 进度条显示加载进度
- 完成后，CSV文件保存在 `data/` 文件夹

#### 1.4 查看导出结果

```bash
# 查看导出的文件
ls data/
# 输出示例：following_old_account_1234567890.csv
```

---

### 第二步：批量关注新账号

#### 2.1 运行关注命令

```bash
python main.py follow --account new_account --file data/following_old_account_*.csv
```

#### 2.2 扫码登录新账号

1. 浏览器再次打开
2. **用新账号扫码登录**
3. 登录成功后，按回车继续

#### 2.3 观察进度

脚本会显示实时进度：
```
关注用户: 45%|████▌     | 450/1000 [02:15<02:45]
  ✅ 成功: 440
  ❌ 失败: 10
  🔐 验证码: 0
```

#### 2.4 处理验证码

如果出现验证码：
1. 脚本会自动暂停
2. 在浏览器中手动完成验证
3. 完成后按回车继续

#### 2.5 完成后查看结果

```bash
# 查看日志
cat logs/migration.log
```

---

## ❓ 常见问题

### Q1: 提示"Python不是内部或外部命令"

**原因：** Python没有添加到系统路径

**解决：**
1. 重新安装Python，勾选 "Add Python to PATH"
2. 或手动添加Python到环境变量

---

### Q2: 提示"pip不是内部或外部命令"

**解决：**
```bash
# 使用完整路径
python -m pip install playwright tqdm
```

---

### Q3: 浏览器打开后闪退

**原因：** Chromium没有安装

**解决：**
```bash
playwright install chromium
```

---

### Q4: 登录后页面空白

**原因：** 网络问题或小红书更新

**解决：**
1. 检查网络连接
2. 刷新页面
3. 如果问题持续，提交Issue

---

### Q5: 关注过程中断了怎么办？

**解决：**
- 脚本会记录已处理的用户
- 重新运行命令即可从中断处继续
- 不会重复关注已关注的用户

---

### Q6: 为什么每天只能关注100人？

**原因：** 小红书风控限制

**建议：**
- 分多天完成
- 每天关注50-100人
- 避免触发风控

---

## ⚠️ 注意事项

### 风控建议

| 操作 | 建议 |
|------|------|
| 每天关注数量 | ≤ 100人 |
| 每次关注间隔 | 5-10秒 |
| 出现验证码 | 立即暂停，第二天继续 |

### 数据安全

- ✅ CSV文件保存在本地
- ✅ 不会上传到任何服务器
- ⚠️ 操作完成后建议删除CSV文件
- ⚠️ 不要将CSV文件分享给他人

### 账号安全

- ✅ 使用小号测试
- ⚠️ 不要频繁切换账号
- ⚠️ 避免在不同设备同时登录

---

## 📁 项目结构

```
xiaohongshu-follow-migration/
├── main.py              # 主入口
├── scripts/
│   ├── export_following.py   # 导出关注列表
│   ├── batch_follow.py       # 批量关注
│   └── unfollow.py           # 取消关注（可选）
├── src/
│   └── progress.py           # 进度显示
├── data/                     # 导出的CSV文件
├── logs/                     # 操作日志
├── test.py                   # 测试脚本
├── requirements.txt          # 依赖列表
├── README.md                 # 本文档
├── QUICKSTART.md             # 快速开始
└── USAGE.md                  # 详细用法
```

---

## 🔗 相关链接

- **GitHub仓库：** https://github.com/PFZ7Z7/xiaohongshu-follow-migration
- **问题反馈：** https://github.com/PFZ7Z7/xiaohongshu-follow-migration/issues

---

## 📜 更新日志

- 2026-04-20: v1.2.0 - 添加跨平台支持，优化文档
- 2026-04-19: v1.1.0 - 修改为只在新账号关注
- 2026-04-19: v1.0.0 - 初版发布

---

## 📄 许可证

MIT License - 可自由使用、修改和分发

---

## 💡 免责声明

本工具仅供学习交流使用，请遵守小红书用户协议。使用本工具产生的任何后果由用户自行承担。
