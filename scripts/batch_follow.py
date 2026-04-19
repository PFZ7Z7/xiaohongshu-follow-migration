#!/usr/bin/env python3
"""
小红书批量关注工具

功能：批量关注CSV文件中的用户
使用：python batch_follow.py --account <account_name> --file <csv_file> [--batch-size 50] [--delay 10]
"""

import argparse
import csv
import os
import random
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright


def batch_follow_users(username: str, csv_file: str, batch_size: int = 50, delay: int = 10, output_dir: str = "data"):
    """
    批量关注CSV文件中的用户
    
    Args:
        username: 账号名称
        csv_file: CSV文件路径
        batch_size: 每批关注数量
        delay: 批次间延迟（秒）
        output_dir: 输出目录
    """
    csv_path = Path(csv_file)
    if not csv_path.exists():
        print(f"错误: CSV文件不存在: {csv_file}")
        sys.exit(1)
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = output_dir / f"follow_{username}_{int(time.time())}.log"
    
    print(f"开始批量关注账号 '{username}'...")
    print(f"CSV文件: {csv_file}")
    print(f"每批关注: {batch_size} 人")
    print(f"批次延迟: {delay} 秒")
    
    # 记录日志
    def log(message: str):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
        print(f"[{timestamp}] {message}")
    
    log("开始批量关注")
    
    # 读取CSV文件
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        users = list(reader)
    
    log(f"共读取 {len(users)} 个用户")
    
    if len(users) == 0:
        log("没有用户需要关注")
        return
    
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = context.new_page()
        
        # 访问小红书登录页面
        log("正在访问小红书登录页面...")
        page.goto("https://www.xiaohongshu.com/explore", wait_until="networkidle")
        
        # 等待用户手动登录
        log("请在浏览器中手动登录小红书账号...")
        input("登录完成后按回车键继续...")
        
        # 统计
        success_count = 0
        fail_count = 0
        skip_count = 0
        captcha_count = 0
        
        # 分批处理
        for i in range(0, len(users), batch_size):
            batch = users[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(users) + batch_size - 1) // batch_size
            
            log(f"处理批次 {batch_num}/{total_batches} ({len(batch)} 人)...")
            
            for user in batch:
                user_id = user.get("user_id", "")
                username_text = user.get("username", "Unknown")
                
                log(f"关注用户: {username_text} ({user_id})")
                
                try:
                    # 构造用户主页URL
                    # 尝试多种URL格式
                    user_urls = [
                        f"https://www.xiaohongshu.com/user/profile/{user_id}",
                        f"https://www.xiaohongshu.com/user/profile/{username_text}"
                    ]
                    
                    success = False
                    for url in user_urls:
                        try:
                            page.goto(url, wait_until="networkidle", timeout=10000)
                            time.sleep(2)
                            
                            # 尝试点击关注按钮
                            follow_buttons = [
                                "text=关注",
                                "button:text('关注')",
                                ".follow-btn",
                                ".follow-button"
                            ]
                            
                            for selector in follow_buttons:
                                try:
                                    page.click(selector, timeout=2000)
                                    success = True
                                    break
                                except:
                                    continue
                            
                            if success:
                                break
                        except:
                            continue
                    
                    if success:
                        success_count += 1
                        log(f"✓ 关注成功: {username_text}")
                    else:
                        fail_count += 1
                        log(f"✗ 关注失败: {username_text}")
                    
                except Exception as e:
                    fail_count += 1
                    log(f"✗ 关注异常: {username_text} - {e}")
                
                # 随机延迟，避免风控
                time.sleep(random.uniform(delay * 0.8, delay * 1.2))
                
                # 检查是否出现验证码
                if page.url.find("captcha") > 0 or page.url.find("security") > 0:
                    log("⚠️ 检测到验证码，暂停操作")
                    captcha_count += 1
                    input("请手动完成验证码，完成后按回车键继续...")
            
            # 批次间延迟
            if batch_num < total_batches:
                log(f"批次完成，等待 {delay} 秒...")
                time.sleep(delay)
        
        # 保存统计
        stats_file = output_dir / f"stats_{username}_{int(time.time())}.json"
        stats = {
            "total": len(users),
            "success": success_count,
            "fail": fail_count,
            "skip": skip_count,
            "captcha": captcha_count
        }
        
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        log(f"关注完成！统计: {stats}")
        log(f"统计文件: {stats_file}")
        
        # 关闭浏览器
        browser.close()
    
    print(f"\n关注完成！")
    print(f"成功: {success_count} 人")
    print(f"失败: {fail_count} 人")
    print(f"跳过: {skip_count} 人")
    print(f"验证码: {captcha_count} 次")
    print(f"日志文件: {log_file}")
    print(f"统计文件: {stats_file}")


def main():
    parser = argparse.ArgumentParser(description="批量关注小红书用户")
    parser.add_argument("--account", "-a", required=True, help="账号名称")
    parser.add_argument("--file", "-f", required=True, help="CSV文件路径")
    parser.add_argument("--batch-size", "-b", type=int, default=50, help="每批关注数量")
    parser.add_argument("--delay", "-d", type=int, default=10, help="批次间延迟（秒）")
    parser.add_argument("--output", "-o", default="data", help="输出目录")
    
    args = parser.parse_args()
    
    batch_follow_users(args.account, args.file, args.batch_size, args.delay, args.output)


if __name__ == "__main__":
    main()
