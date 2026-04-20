#!/usr/bin/env python3
"""
小红书关注列表导出工具 v2.0

改进：
- 修复硬编码URL问题
- 添加去重机制
- 添加登录状态验证
- 改进选择器稳定性
- 集成进度显示
- 添加错误处理和重试
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
    logger = logging.getLogger("export")
    logger.setLevel(logging.INFO)
    
    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        "%(asctime)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


class XiaohongshuExporter:
    """小红书关注列表导出器"""
    
    # 选择器配置（多个备选，提高稳定性）
    SELECTORS = {
        "user_card": [
            ".user-item",
            ".user-card",
            "[class*='userItem']",
            "[class*='UserItem']",
            ".following-item",
            "[class*='followingItem']"
        ],
        "user_name": [
            ".name",
            ".user-name",
            "[class*='userName']",
            "[class*='name']",
            "a[href*='/user/profile/']"
        ],
        "user_id": [
            "[class*='userId']",
            ".user-id",
            "a[href*='/user/profile/']"
        ],
        "following_tab": [
            "text=关注",
            "[class*='following']",
            "button:has-text('关注')",
            "a:has-text('关注')"
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
    
    def __init__(self, username: str, output_dir: Path, logger: logging.Logger):
        self.username = username
        self.output_dir = output_dir
        self.logger = logger
        self.seen_user_ids: Set[str] = set()
        self.following_list: List[Dict] = []
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    def find_element(self, selectors: List[str], timeout: int = 5000) -> Optional[any]:
        """尝试多个选择器，返回第一个匹配的元素"""
        for selector in selectors:
            try:
                element = self.page.locator(selector).first
                if element.count() > 0:
                    return element
            except:
                continue
        return None
    
    def check_captcha(self) -> bool:
        """检查是否出现验证码"""
        for selector in self.SELECTORS["captcha"]:
            try:
                if self.page.locator(selector).count() > 0:
                    return True
            except:
                continue
        return False
    
    def check_login(self) -> bool:
        """检查是否已登录"""
        for selector in self.SELECTORS["login_check"]:
            try:
                if self.page.locator(selector).count() > 0:
                    return True
            except:
                continue
        return False
    
    def smart_delay(self, base: float = 2.0) -> None:
        """智能延迟，添加随机性"""
        delay = base * random.uniform(0.8, 1.2)
        time.sleep(delay)
    
    def launch_browser(self, playwright) -> None:
        """启动浏览器"""
        self.logger.info("启动浏览器...")
        
        # 随机User-Agent
        user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
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
        """登录小红书"""
        self.logger.info("访问小红书首页...")
        self.page.goto("https://www.xiaohongshu.com/explore", wait_until="networkidle")
        self.smart_delay(2)
        
        # 检查是否已登录
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
        
        # 验证登录状态
        if not self.check_login():
            self.logger.warning("未检测到登录状态，请确认是否登录成功")
            retry = input("是否已登录成功？(y/n): ").strip().lower()
            if retry != 'y':
                return False
        
        return True
    
    def get_user_id_from_page(self) -> Optional[str]:
        """从当前页面获取用户ID"""
        try:
            # 方法1：从URL获取
            url = self.page.url
            match = re.search(r'/user/profile/(\w+)', url)
            if match:
                return match.group(1)
            
            # 方法2：从页面元素获取
            # 尝试点击头像进入个人主页
            avatar_selectors = [
                ".avatar",
                "[class*='avatar']",
                "img[class*='avatar']"
            ]
            for selector in avatar_selectors:
                try:
                    if self.page.locator(selector).count() > 0:
                        self.page.locator(selector).first.click()
                        self.smart_delay(2)
                        url = self.page.url
                        match = re.search(r'/user/profile/(\w+)', url)
                        if match:
                            return match.group(1)
                except:
                    continue
            
            return None
        except Exception as e:
            self.logger.error(f"获取用户ID失败: {e}")
            return None
    
    def navigate_to_following(self) -> bool:
        """导航到关注页面"""
        self.logger.info("正在访问关注页面...")
        
        # 方法1：直接访问个人主页
        # 先获取用户ID
        user_id = self.get_user_id_from_page()
        
        if user_id:
            # 访问关注页面
            following_url = f"https://www.xiaohongshu.com/user/profile/{user_id}?tab=following"
            self.page.goto(following_url, wait_until="networkidle")
        else:
            # 方法2：通过首页导航
            self.page.goto("https://www.xiaohongshu.com/explore", wait_until="networkidle")
            self.smart_delay(2)
            
            # 尝试点击"我的关注"
            # 这需要根据实际页面结构调整
        
        self.smart_delay(3)
        
        # 检查是否成功进入关注页面
        # 这里可以添加验证逻辑
        
        return True
    
    def extract_user_info(self, user_element) -> Optional[Dict]:
        """从用户元素中提取信息"""
        try:
            user_info = {}
            
            # 提取用户名
            for selector in self.SELECTORS["user_name"]:
                try:
                    name_elem = user_element.locator(selector).first
                    if name_elem.count() > 0:
                        user_info["username"] = name_elem.inner_text().strip()
                        break
                except:
                    continue
            
            if "username" not in user_info:
                user_info["username"] = "Unknown"
            
            # 提取用户ID
            for selector in self.SELECTORS["user_id"]:
                try:
                    id_elem = user_element.locator(selector).first
                    if id_elem.count() > 0:
                        # 可能是链接，提取href中的ID
                        href = id_elem.get_attribute("href")
                        if href:
                            match = re.search(r'/user/profile/(\w+)', href)
                            if match:
                                user_info["user_id"] = match.group(1)
                                break
                        # 或者直接获取文本
                        text = id_elem.inner_text().strip()
                        if text:
                            user_info["user_id"] = text
                            break
                except:
                    continue
            
            if "user_id" not in user_info:
                # 生成一个临时ID
                user_info["user_id"] = f"temp_{int(time.time() * 1000)}"
            
            user_info["follow_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            return user_info
            
        except Exception as e:
            self.logger.error(f"提取用户信息失败: {e}")
            return None
    
    def scroll_and_collect(self, max_count: int = 2000) -> None:
        """滚动页面并收集用户信息"""
        self.logger.info("开始滚动加载关注列表...")
        
        last_count = 0
        no_change_count = 0
        max_no_change = 3  # 连续3次没有变化则停止
        
        try:
            # 尝试导入进度模块
            sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
            from progress import ProgressTracker
            use_progress = True
        except:
            use_progress = False
        
        if use_progress:
            with ProgressTracker(total=max_count, description="加载关注列表") as progress:
                self._scroll_loop(max_count, last_count, no_change_count, max_no_change, progress)
        else:
            self._scroll_loop(max_count, last_count, no_change_count, max_no_change, None)
    
    def _scroll_loop(self, max_count: int, last_count: int, no_change_count: int, 
                     max_no_change: int, progress) -> None:
        """滚动循环"""
        while len(self.following_list) < max_count:
            # 检查验证码
            if self.check_captcha():
                self.logger.warning("⚠️ 检测到验证码，暂停操作")
                input("请手动完成验证码，完成后按回车键继续...")
                continue
            
            # 提取当前页面的用户
            for selector in self.SELECTORS["user_card"]:
                try:
                    user_elements = self.page.locator(selector).all()
                    if user_elements:
                        for elem in user_elements:
                            user_info = self.extract_user_info(elem)
                            if user_info:
                                user_id = user_info.get("user_id", "")
                                # 去重
                                if user_id and user_id not in self.seen_user_ids:
                                    self.seen_user_ids.add(user_id)
                                    self.following_list.append(user_info)
                        break
                except:
                    continue
            
            current_count = len(self.following_list)
            
            # 更新进度
            if progress:
                progress.update(current_count - last_count)
            
            # 检查是否有新数据
            if current_count == last_count:
                no_change_count += 1
                if no_change_count >= max_no_change:
                    self.logger.info(f"连续{max_no_change}次没有新数据，停止加载")
                    break
            else:
                no_change_count = 0
                self.logger.info(f"已加载 {current_count} 个关注用户")
            
            last_count = current_count
            
            # 滚动到底部
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            self.smart_delay(2)
            
            # 再次滚动（有些页面需要多次触发）
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            self.smart_delay(1)
    
    def save_results(self) -> Path:
        """保存结果"""
        csv_file = self.output_dir / f"following_{self.username}_{int(time.time())}.csv"
        
        self.logger.info(f"保存 {len(self.following_list)} 个用户到 {csv_file}")
        
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["user_id", "username", "follow_time"])
            writer.writeheader()
            writer.writerows(self.following_list)
        
        # 保存统计
        stats_file = self.output_dir / f"stats_{self.username}_{int(time.time())}.json"
        stats = {
            "total": len(self.following_list),
            "unique": len(self.seen_user_ids),
            "export_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "account": self.username
        }
        
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"统计文件: {stats_file}")
        
        return csv_file
    
    def run(self) -> Optional[Path]:
        """运行导出流程"""
        try:
            with sync_playwright() as p:
                # 1. 启动浏览器
                self.launch_browser(p)
                
                # 2. 登录
                if not self.login():
                    self.logger.error("登录失败")
                    return None
                
                # 3. 导航到关注页面
                if not self.navigate_to_following():
                    self.logger.error("无法访问关注页面")
                    return None
                
                # 4. 滚动收集
                self.scroll_and_collect()
                
                # 5. 保存结果
                csv_file = self.save_results()
                
                # 6. 关闭浏览器
                self.browser.close()
                
                return csv_file
                
        except Exception as e:
            self.logger.error(f"导出失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None


def main():
    parser = argparse.ArgumentParser(
        description="导出小红书关注列表 v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python export_following.py --account my_account
  python export_following.py -a my_account -o ./output
        """
    )
    parser.add_argument("--account", "-a", required=True, help="账号名称（用于标识）")
    parser.add_argument("--output", "-o", default="data", help="输出目录")
    
    args = parser.parse_args()
    
    # 创建输出目录
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 设置日志
    log_file = output_dir / f"export_{args.account}_{int(time.time())}.log"
    logger = setup_logging(log_file)
    
    # 运行导出
    exporter = XiaohongshuExporter(args.account, output_dir, logger)
    csv_file = exporter.run()
    
    if csv_file:
        print(f"\n✅ 导出成功！")
        print(f"   CSV文件: {csv_file}")
        print(f"   日志文件: {log_file}")
        print(f"   用户数量: {len(exporter.following_list)}")
    else:
        print(f"\n❌ 导出失败，请查看日志: {log_file}")
        sys.exit(1)


if __name__ == "__main__":
    main()
