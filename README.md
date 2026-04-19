# 小红书关注列表迁移工具

## 功能说明

将一个小红书账号的关注列表迁移到另一个账号。

## 使用场景

- 账号A有900+关注，准备停用
- 希望将这些关注迁移到账号B
- 避免手动逐个关注的繁琐操作

## 实现方案

### 方案1：Playwright自动化（推荐）

**优点：** 快速实现，完全自动化
**缺点：** 需要处理验证码、风控

**操作步骤：**
1. 登录账号A，导出关注列表为CSV
2. 登录账号B，批量关注这些用户
3. 账号A取消关注

**风控处理：**
- 每次关注间隔5-10秒
- 每天关注不超过100人
- 出现验证码时暂停并提示用户

---

### 方案2：小红书MCP扩展

**优点：** 可复用，更稳定
**缺点：** 需要修改MCP服务器代码

**需要扩展的功能：**
1. `get_following_list` - 获取关注列表
2. `batch_follow` - 批量关注
3. `unfollow` - 取消关注

---

## 使用方法

### 方法1：Playwright自动化

```bash
# 1. 导出关注列表
python scripts/export_following.py --account old_account

# 2. 批量关注
python scripts/batch_follow.py --account new_account --file following.csv

# 3. 取消关注
python scripts/unfollow.py --account old_account --file following.csv
```

### 方法2：半自动导出+手动关注

```bash
# 1. 导出关注列表
python scripts/export_following.py --account old_account

# 2. 手动在新账号关注CSV中的用户
# 3. 确认关注完成后，取消旧账号关注
python scripts/unfollow.py --account old_account --file following.csv
```

---

## 风控注意事项

1. **操作频率：**
   - 每次关注间隔5-10秒
   - 每天关注不超过100人
   - 出现验证码立即暂停

2. **账号安全：**
   - 使用小号测试
   - 不要频繁切换账号
   - 避免在不同设备同时登录

3. **失败处理：**
   - 自动重试3次
   - 记录失败用户，后续手动处理
   - 生成详细的操作日志

---

## 文件结构

```
xiaohongshu-follow-migration/
├── README.md
├── scripts/
│   ├── export_following.py    # 导出关注列表
│   ├── batch_follow.py        # 批量关注
│   └── unfollow.py            # 取消关注
├── data/
│   └── following.csv          # 导出的关注列表
└── logs/
    └── migration.log          # 操作日志
```

---

## CSV格式

```csv
user_id,username,avatar_url,follow_time
123456,用户A,https://example.com/avatar.jpg,2024-01-01
789012,用户B,https://example.com/avatar2.jpg,2024-01-02
```

---

## 运行环境

- Python 3.8+
- playwright
- pandas (用于CSV处理)

---

## 注意事项

1. **小红书API限制：**
   - 每日关注上限：100-200人
   - 需要手动验证（可能触发短信验证）
   - 频繁操作可能触发风控

2. **数据安全：**
   - CSV文件包含用户信息，请妥善保管
   - 不要将CSV文件上传到公开仓库
   - 操作完成后及时删除CSV文件

3. **法律合规：**
   - 遵守小红书用户协议
   - 不要用于商业用途
   - 尊重用户隐私

---

## 常见问题

### Q1: 为什么不能一次性关注900+人？
A: 小红书有严格的风控机制，一次性关注大量用户会触发验证码甚至封号。

### Q2: 出现验证码怎么办？
A: 脚本会自动暂停并提示用户手动完成验证，完成后继续执行。

### Q3: 如何确保数据安全？
A: CSV文件只保存在本地，操作完成后建议手动删除。

---

## 更新日志

- 2026-04-19: 初版创建
