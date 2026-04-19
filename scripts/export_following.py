#!/usr/bin/env python3
"""
小红书关注列表导出工具

功能：导出小红书账号的关注列表为CSV文件
使用：python export_following.py --account <account_name>
"""

import argparse
import csv
import json
import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright


def export_following_list(username: str, output_dir: str = "data"):
    """
    导出小红书账号的关注列表
    
    Args:
        username: 账号名称（用于标识）
        output_dir: 输出目录
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    csv_file = output_dir / f"following_{username}_{int(time.time())}.csv"
    log_file = output_dir / f"export_{username}_{int(time.time())}.log"
    
    print(f"开始导出账号 '{username}' 的关注列表...")
    print(f"CSV输出: {csv_file}")
    print(f"日志文件: {log_file}")
    
    # 记录日志
    def log(message: str):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
        print(f"[{timestamp}] {message}")
    
    log("开始导出关注列表")
    
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
        
        # 访问关注页面
        log("正在访问关注页面...")
        page.goto("https://www.xiaohongshu.com/user/profile/500000000", wait_until="networkidle")
        
        # 点击关注标签
        try:
            page.click("text=关注", timeout=5000)
        except:
            log("关注标签已选中或无法点击")
        
        time.sleep(2)
        
        # 滚动加载所有关注用户
        following_list = []
        last_height = page.evaluate("document.body.scrollHeight")
        
        log("开始滚动加载关注列表...")
        
        while True:
            # 提取当前页面的关注用户
            users = page.locator(".user-card").all()
            
            for user in users:
                try:
                    # 提取用户信息
                    username_elem = user.locator(".name").first
                    username_text = username_elem.inner_text() if username_elem else "Unknown"
                    
                    user_id_elem = user.locator(".user-id")
                    user_id = user_id_elem.inner_text() if user_id_elem else "Unknown"
                    
                    # 提取关注时间（如果有）
                    follow_time = time.strftime("%Y-%m-%d %H:%M:%S")
                    
                    following_list.append({
                        "user_id": user_id,
                        "username": username_text,
                        "follow_time": follow_time
                    })
                except Exception as e:
                    log(f"提取用户信息失败: {e}")
                    continue
            
            log(f"已加载 {len(following_list)} 个关注用户...")
            
            # 滚动到底部
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            
            # 检查是否加载完成
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                # 尝试再次滚动
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    break
            
            last_height = new_height
            
            # 限制最大数量（防止无限滚动）
            if len(following_list) >= 1000:
                log("达到最大数量限制（1000），停止加载")
                break
        
        # 保存CSV
        log(f"共找到 {len(following_list)} 个关注用户")
        log(f"正在保存到CSV文件...")
        
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["user_id", "username", "follow_time"])
            writer.writeheader()
            writer.writerows(following_list)
        
        log(f"保存完成: {csv_file}")
        
        # 关闭浏览器
        browser.close()
    
    print(f"\n导出完成！")
    print(f"CSV文件: {csv_file}")
    print(f"日志文件: {log_file}")
    
    return csv_file


def main():
    parser = argparse.ArgumentParser(description="导出小红书关注列表")
    parser.add_argument("--account", "-a", required=True, help="账号名称（用于标识）")
    parser.add_argument("--output", "-o", default="data", help="输出目录")
    
    args = parser.parse_args()
    
    export_following_list(args.account, args.output)


if __name__ == "__main__":
    main()
