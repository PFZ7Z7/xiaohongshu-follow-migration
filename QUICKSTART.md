# 快速开始

> 5分钟上手小红书关注列表迁移工具

---

## 🚀 三步完成迁移

### 第一步：安装

#### Windows用户
```bash
# 1. 下载项目后，打开命令提示符，进入项目目录
cd xiaohongshu-follow-migration

# 2. 创建并激活虚拟环境
python -m venv venv
venv\Scripts\activate

# 3. 安装依赖
pip install playwright tqdm
playwright install chromium
```

#### Mac用户
```bash
# 1. 下载项目后，打开终端，进入项目目录
cd xiaohongshu-follow-migration

# 2. 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install playwright tqdm
playwright install chromium
```

---

### 第二步：导出关注列表

```bash
# 运行导出命令
python main.py export --account old_account
```

**接下来会发生什么：**
1. 浏览器自动打开
2. 显示小红书登录页面
3. **用手机扫码登录**
4. 登录成功后，按回车继续
5. 等待进度条走完

**导出结果：**
- 文件保存在 `data/` 文件夹
- 文件名类似 `following_old_account_1234567890.csv`

---

### 第三步：批量关注新账号

```bash
# 运行关注命令（替换文件名为你的实际文件名）
python main.py follow --account new_account --file data/following_old_account_*.csv
```

**接下来会发生什么：**
1. 浏览器再次打开
2. **用新账号扫码登录**
3. 登录成功后，按回车开始
4. 观察进度条

**进度显示：**
```
关注用户: 45%|████▌     | 450/1000 [02:15<02:45]
  ✅ 成功: 440
  ❌ 失败: 10
```

---

## ⚠️ 重要提醒

### 每天不要超过100人！

小红书有风控机制，一次性关注太多会：
- 触发验证码
- 账号被限制
- 严重时封号

### 建议做法

| 关注数量 | 建议时间 |
|---------|---------|
| 100人以内 | 1天完成 |
| 100-300人 | 分3天 |
| 300-500人 | 分5天 |
| 500人以上 | 分7-10天 |

---

## 🔧 遇到问题？

### 问题1：命令找不到

**Windows:**
```bash
# 使用完整路径
.\venv\Scripts\python main.py export --account old_account
```

**Mac:**
```bash
# 使用完整路径
./venv/bin/python main.py export --account old_account
```

### 问题2：浏览器没反应

```bash
# 重新安装浏览器
playwright install chromium
```

### 问题3：出现验证码

1. 脚本会自动暂停
2. 在浏览器中手动完成验证
3. 完成后按回车继续

---

## 📚 更多帮助

- 详细教程：[USAGE.md](USAGE.md)
- 问题反馈：[GitHub Issues](https://github.com/PFZ7Z7/xiaohongshu-follow-migration/issues)

---

## ✅ 检查清单

使用前请确认：

- [ ] Python 3.8+ 已安装
- [ ] 虚拟环境已激活
- [ ] 依赖已安装（playwright, tqdm）
- [ ] Chromium浏览器已安装
- [ ] 有两部手机（或能切换账号）
- [ ] 网络连接正常

---

**祝迁移顺利！** 🎉
