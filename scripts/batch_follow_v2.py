#!/usr/bin/env python3
"""
小红书批量关注工具 v2.0

改进：
- 实现断点续传（checkpoint机制）
- 添加关注成功验证
- 集成进度显示
- 改进选择器稳定性
- 智能延迟策略
- 重试机制
"""

import argparse
import csv
import json
import logging
import os
import random
import re
import sys
import time
from pathlib import Path
from typing import List, Dict, Set, Optional
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

# 配置日志
def setup_logging(log_file: Path) -> logging.Logger:
    """设置日志"""
    logger = logging.getLogger("follow")
    logger.setLevel(logging.INFO)
    
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        "%(asctime)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


class CheckpointManager:
    """断点续传管理器"""
    
    def __init__(self, checkpoint_file: Path):
        self.checkpoint_file = checkpoint_file
        self.processed_ids: Set[str] = set()
        self.failed_ids: Set[str] = set()
        self.skipped_ids: Set[str] = set()
        self.last_index: int = 0
        self.stats: Dict = {
            "total_processed": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "captcha": 0
        }
        self.load()
    
    def load(self) -> None:
        """加载checkpoint"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.processed_ids = set(data.get("processed_ids", []))
                self.failed_ids = set(data.get("failed_ids", []))
                self.skipped_ids = set(data.get("skipped_ids", []))
                self.last_index = data.get("last_index", 0)
                self.stats = data.get("stats", self.stats)
            except:
                pass
    
    def save(self) -> None:
        """保存checkpoint"""
        data = {
            "processed_ids": list(self.processed_ids),
            "failed_ids": list(self.failed_ids),
            "skipped_ids": list(self.skipped_ids),
            "last_index": self.last_index,
            "stats": self.stats,
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(self.checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def mark_processed(self, user_id: str, success: bool = True) -> None:
        """标记用户已处理"""
        self.processed_ids.add(user_id)
        self.stats["total_processed"] += 1
        if success:
            self.stats["success"] += 1
        else:
            self.failed_ids.add(user_id)
            self.stats["failed"] += 1
        self.save()
    
    def mark_skipped(self, user_id: str) -> None:
        """标记用户已跳过"""
        self.skipped_ids.add(user_id)
        self.stats["skipped"] += 1
        self.save()
    
    def mark_captcha(self) -> None:
        """记录验证码"""
        self.stats["captcha"] += 1
        self.save()
    
    def is_processed(self, user_id: str) -> bool:
        """检查用户是否已处理"""
        return user_id in self.processed_ids or user_id in self.skipped_ids
    
    def get_remaining_count(self, total: int) -> int:
        """获取剩余数量"""
        return total - len(self.processed_ids) - len(self.skipped_ids)


class XiaohongshuFollower:
    """小红书批量关注器"""
    
    # 选择器配置
    SELECTORS = {
        "follow_button": [
            "button:has-text('关注')",
            "[class*='followBtn']",
            "[class*='follow-btn']",
            ".follow-button",
            "button[class*='FollowBtn']"
        ],
        "following_button": [
            "button:has-text('已关注')",
            "button:has-text('互相关注')",
            "[class*='followingBtn']",
            "[class*='following-btn']"
        ],
        "captcha": [
            ".captcha-container",
            ".verify-container",
            "[class*='captcha']",
            "[class*='verify']",
            "text=请完成安全验证",
            "text=滑动验证",
            "iframe[src*='captcha']"
        ],
        "login_check": [
            ".user-info",
            "[class*='userInfo']",
            ".avatar",
            "[class*='avatar']"
        ]
    }
    
    def __init__(
        self,
        username: str,
        csv_file: Path,
        output_dir: Path,
        logger: logging.Logger,
        batch_size: int = 20,
        base_delay: float = 8.0
    ):
        self.username = username
        self.csv_file = csv_file
        self.output_dir = output_dir
        self.logger = logger
        self.batch_size = batch_size
        self.base_delay = base_delay
        
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # 断点续传
        checkpoint_file = output_dir / f"checkpoint_{username}.json"
        self.checkpoint = CheckpointManager(checkpoint_file)
        
        # 统计
        self.consecutive_failures = 0
    
    def find_element(self, selectors: List[str], timeout: int = 3000) -> Optional[any]:
        """尝试多个选择器"""
        for selector in selectors:
            try:
                element = self.page.locator(selector).first
                if element.count() > 0:
                    return element
            except:
                continue
        return None
    
    def check_captcha(self) -> bool:
        """检查验证码"""
        for selector in self.SELECTORS["captcha"]:
            try:
                if self.page.locator(selector).count() > 0:
                    return True
            except:
                continue
        return False
    
    def check_login(self) -> bool:
        """检查登录状态"""
        for selector in self.SELECTORS["login_check"]:
            try:
                if self.page.locator(selector).count() > 0:
                    return True
            except:
                continue
        return False
    
    def smart_delay(self, multiplier: float = 1.0) -> None:
        """智能延迟"""
        # 基础延迟 + 随机抖动
        base = self.base_delay * multiplier
        
        # 如果连续失败，增加延迟
        if self.consecutive_failures > 0:
            base *= (1.5 ** self.consecutive_failures)
        
        # 添加随机性
        delay = base * random.uniform(0.8, 1.2)
        delay = min(delay, 60)  # 最大60秒
        
        time.sleep(delay)
    
    def launch_browser(self, playwright) -> None:
        """启动浏览器"""
        self.logger.info("启动浏览器...")
        
        user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        self.browser = playwright.chromium.launch(headless=False)
        self.context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=random.choice(user_agents),
            locale="zh-CN",
            timezone_id="Asia/Shanghai"
        )
        self.page = self.context.new_page()
        self.logger.info("浏览器启动成功")
    
    def login(self) -> bool:
        """登录"""
        self.logger.info("访问小红书首页...")
        self.page.goto("https://www.xiaohongshu.com/explore", wait_until="networkidle")
        time.sleep(2)
        
        if self.check_login():
            self.logger.info("检测到已登录状态")
            return True
        
        self.logger.info("=" * 50)
        self.logger.info("请在浏览器中完成登录：")
        self.logger.info("  1. 点击右上角'登录'按钮")
        self.logger.info("  2. 使用手机小红书APP扫码登录")
        self.logger.info("  3. 登录成功后，回到此窗口按回车键")
        self.logger.info("=" * 50)
        
        input("\n按回车键继续...")
        
        return self.check_login()
    
    def check_already_following(self) -> bool:
        """检查是否已关注"""
        for selector in self.SELECTORS["following_button"]:
            try:
                if self.page.locator(selector).count() > 0:
                    return True
            except:
                continue
        return False
    
    def follow_user(self, user_id: str, username: str) -> str:
        """
        关注单个用户
        
        Returns:
            "success" - 关注成功
            "failed" - 关注失败
            "skipped" - 已关注，跳过
            "captcha" - 遇到验证码
        """
        try:
            # 访问用户主页
            user_url = f"https://www.xiaohongshu.com/user/profile/{user_id}"
            self.page.goto(user_url, wait_until="networkidle", timeout=15000)
            time.sleep(2)
            
            # 检查验证码
            if self.check_captcha():
                return "captcha"
            
            # 检查是否已关注
            if self.check_already_following():
                self.logger.info(f"  已关注 {username}，跳过")
                return "skipped"
            
            # 尝试点击关注按钮
            for selector in self.SELECTORS["follow_button"]:
                try:
                    button = self.page.locator(selector).first
                    if button.count() > 0:
                        # 记录点击前的状态
                        button_text_before = button.inner_text()
                        
                        # 点击
                        button.click()
                        time.sleep(1)
                        
                        # 验证是否成功
                        button_text_after = button.inner_text()
                        
                        if "已关注" in button_text_after or "互相关注" in button_text_after:
                            return "success"
                        
                        # 如果按钮文本变化了，可能成功
                        if button_text_after != button_text_before:
                            return "success"
                        
                except Exception as e:
                    continue
            
            # 所有选择器都失败
            return "failed"
            
        except Exception as e:
            self.logger.error(f"  关注异常: {username} - {e}")
            return "failed"
    
    def handle_captcha(self) -> None:
        """处理验证码"""
        self.logger.warning("⚠️ 检测到验证码，暂停操作")
        self.checkpoint.mark_captcha()
        
        self.logger.info("请在浏览器中手动完成验证码...")
        input("完成后按回车键继续...")
        
        # 重置连续失败计数
        self.consecutive_failures = 0
    
    def process_users(self, users: List[Dict]) -> None:
        """处理用户列表"""
        # 尝试导入进度模块
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
            from progress import ProgressTracker
            use_progress = True
        except:
            use_progress = False
        
        # 过滤已处理的用户
        remaining_users = [
            u for u in users 
            if not self.checkpoint.is_processed(u.get("user_id", ""))
        ]
        
        total = len(remaining_users)
        self.logger.info(f"剩余 {total} 个用户需要处理")
        
        if total == 0:
            self.logger.info("所有用户已处理完成")
            return
        
        # 使用进度显示
        if use_progress:
            with ProgressTracker(total=total, description="批量关注") as progress:
                self._process_users_loop(remaining_users, progress)
        else:
            self._process_users_loop(remaining_users, None)
    
    def _process_users_loop(self, users: List[Dict], progress) -> None:
        """处理用户循环"""
        for i, user in enumerate(users):
            user_id = user.get("user_id", "")
            username = user.get("username", "Unknown")
            
            # 跳过无效ID
            if not user_id or user_id.startswith("temp_"):
                self.logger.warning(f"  跳过无效ID: {username}")
                self.checkpoint.mark_skipped(user_id)
                if progress:
                    progress.update(1)
                continue
            
            # 检查是否已处理
            if self.checkpoint.is_processed(user_id):
                if progress:
                    progress.update(1)
                continue
            
            self.logger.info(f"[{i+1}/{len(users)}] 关注: {username} ({user_id})")
            
            # 关注用户
            result = self.follow_user(user_id, username)
            
            # 处理结果
            if result == "success":
                self.checkpoint.mark_processed(user_id, success=True)
                self.consecutive_failures = 0
                self.logger.info(f"  ✅ 关注成功")
                if progress:
                    progress.update(1)
                    progress.record_success()
                
            elif result == "skipped":
                self.checkpoint.mark_skipped(user_id)
                self.logger.info(f"  ⏭️ 已关注，跳过")
                if progress:
                    progress.update(1)
                
            elif result == "captcha":
                self.handle_captcha()
                # 重试当前用户
                result = self.follow_user(user_id, username)
                if result == "success":
                    self.checkpoint.mark_processed(user_id, success=True)
                else:
                    self.checkpoint.mark_processed(user_id, success=False)
                if progress:
                    progress.update(1)
                
            else:  # failed
                self.checkpoint.mark_processed(user_id, success=False)
                self.consecutive_failures += 1
                self.logger.warning(f"  ❌ 关注失败 (连续失败: {self.consecutive_failures})")
                if progress:
                    progress.update(1)
                    progress.record_failed()
            
            # 延迟
            self.smart_delay()
            
            # 如果连续失败太多，暂停
            if self.consecutive_failures >= 5:
                self.logger.warning("连续失败5次，暂停60秒...")
                time.sleep(60)
                self.consecutive_failures = 0
    
    def run(self) -> Dict:
        """运行批量关注"""
        # 读取CSV
        with open(self.csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            users = list(reader)
        
        self.logger.info(f"读取 {len(users)} 个用户")
        
        try:
            with sync_playwright() as p:
                # 1. 启动浏览器
                self.launch_browser(p)
                
                # 2. 登录
                if not self.login():
                    self.logger.error("登录失败")
                    return {"success": False, "error": "登录失败"}
                
                # 3. 处理用户
                self.process_users(users)
                
                # 4. 关闭浏览器
                self.browser.close()
                
                # 5. 返回统计
                return {
                    "success": True,
                    "stats": self.checkpoint.stats
                }
                
        except Exception as e:
            self.logger.error(f"批量关注失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="批量关注小红书用户 v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python batch_follow.py -a my_account -f data/following.csv
  python batch_follow.py -a my_account -f data/following.csv -b 20 -d 10

注意:
  - 支持断点续传，中断后重新运行即可继续
  - 建议每天关注不超过100人
  - 建议每批不超过20人
        """
    )
    parser.add_argument("--account", "-a", required=True, help="账号名称")
    parser.add_argument("--file", "-f", required=True, help="CSV文件路径")
    parser.add_argument("--batch-size", "-b", type=int, default=20, help="每批关注数量（默认20）")
    parser.add_argument("--delay", "-d", type=float, default=8.0, help="基础延迟秒数（默认8）")
    parser.add_argument("--output", "-o", default="data", help="输出目录")
    
    args = parser.parse_args()
    
    # 验证文件
    csv_file = Path(args.file)
    if not csv_file.exists():
        print(f"错误: CSV文件不存在: {args.file}")
        sys.exit(1)
    
    # 创建输出目录
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 设置日志
    log_file = output_dir / f"follow_{args.account}_{int(time.time())}.log"
    logger = setup_logging(log_file)
    
    # 运行
    follower = XiaohongshuFollower(
        username=args.account,
        csv_file=csv_file,
        output_dir=output_dir,
        logger=logger,
        batch_size=args.batch_size,
        base_delay=args.delay
    )
    
    result = follower.run()
    
    if result.get("success"):
        stats = result.get("stats", {})
        print(f"\n✅ 批量关注完成！")
        print(f"   成功: {stats.get('success', 0)}")
        print(f"   失败: {stats.get('failed', 0)}")
        print(f"   跳过: {stats.get('skipped', 0)}")
        print(f"   验证码: {stats.get('captcha', 0)}")
        print(f"   日志文件: {log_file}")
    else:
        print(f"\n❌ 批量关注失败: {result.get('error', '未知错误')}")
        print(f"   日志文件: {log_file}")
        sys.exit(1)


if __name__ == "__main__":
    main()
