# 快速开始

## 1. 安装依赖

```bash
cd xiaohongshu-follow-migration
pip install -r requirements.txt
playwright install chromium
```

## 2. 导出关注列表

```bash
python main.py export --account old_account
```

按提示操作：
1. 浏览器会自动打开小红书登录页面
2. 手动登录旧账号
3. 按回车键继续
4. 等待脚本自动滚动加载所有关注用户

## 3. 批量关注新账号

```bash
python main.py follow --account new_account --file data/following_old_account_*.csv --batch-size 50 --delay 10
```

---

## 注意事项

- **每天关注不超过100人**
- **出现验证码时暂停操作**
- **操作完成后删除CSV文件**
- **老账号不会取消关注，仅在新账号上关注**

详细说明请查看 [USAGE.md](USAGE.md)
