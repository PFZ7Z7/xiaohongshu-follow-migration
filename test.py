#!/usr/bin/env python3
"""
测试脚本 - 模拟测试小红书关注列表迁移工具的核心功能

不实际登录小红书，只测试代码逻辑
"""

import sys
import os
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_imports():
    """测试所有必要的导入"""
    print("=" * 60)
    print("测试1: 检查导入")
    print("=" * 60)
    
    try:
        from playwright.sync_api import sync_playwright
        print("✅ playwright 导入成功")
    except ImportError as e:
        print(f"❌ playwright 导入失败: {e}")
        return False
    
    try:
        from tqdm import tqdm
        print("✅ tqdm 导入成功")
    except ImportError as e:
        print(f"❌ tqdm 导入失败: {e}")
        return False
    
    try:
        from progress import ProgressTracker, BatchProgressTracker
        print("✅ progress 模块导入成功")
    except ImportError as e:
        print(f"❌ progress 模块导入失败: {e}")
        return False
    
    print("\n✅ 所有导入测试通过！\n")
    return True


def test_progress_tracker():
    """测试进度跟踪器"""
    print("=" * 60)
    print("测试2: 进度跟踪器")
    print("=" * 60)
    
    from progress import ProgressTracker
    
    # 测试基本功能
    tracker = ProgressTracker(total=100, description="测试进度")
    print(f"初始状态: total={tracker.total}, success={tracker.success_count}, failed={tracker.failed_count}")
    
    # 模拟处理
    tracker.record_success()
    tracker.record_success()
    tracker.record_failed()
    tracker.record_skip()
    tracker.record_captcha()
    
    print(f"处理后: success={tracker.success_count}, failed={tracker.failed_count}, skipped={tracker.stats['skipped']}, captcha={tracker.stats['captcha']}")
    
    # 验证结果
    assert tracker.success_count == 2, "成功计数错误"
    assert tracker.failed_count == 1, "失败计数错误"
    assert tracker.stats['skipped'] == 1, "跳过计数错误"
    assert tracker.stats['captcha'] == 1, "验证码计数错误"
    
    print("\n✅ 进度跟踪器测试通过！\n")
    return True


def test_batch_progress_tracker():
    """测试批次进度跟踪器"""
    print("=" * 60)
    print("测试3: 批次进度跟踪器")
    print("=" * 60)
    
    from progress import BatchProgressTracker
    
    # 测试批次处理
    with BatchProgressTracker(total_batches=3, total_items=150, description="批次测试") as batch_tracker:
        print(f"总批次数: {batch_tracker.total_batches}")
        print(f"总用户数: {batch_tracker.total_items}")
        
        # 模拟批次处理
        for i in range(1, 4):
            batch_tracker.start_batch(i, 50)
            if batch_tracker.current_progress:
                for j in range(50):
                    batch_tracker.current_progress.update(1)
                    if j % 10 == 0:
                        batch_tracker.current_progress.record_success()
            batch_tracker.end_batch()
    
    print("\n✅ 批次进度跟踪器测试通过！\n")
    return True


def test_browser_launch():
    """测试浏览器启动（不访问小红书）"""
    print("=" * 60)
    print("测试4: 浏览器启动测试")
    print("=" * 60)
    
    from playwright.sync_api import sync_playwright
    
    try:
        with sync_playwright() as p:
            print("启动浏览器...")
            browser = p.chromium.launch(headless=True)
            print("✅ 浏览器启动成功")
            
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            print("✅ 浏览器上下文创建成功")
            
            page = context.new_page()
            print("✅ 页面创建成功")
            
            # 测试访问一个简单的页面
            page.goto("about:blank")
            print("✅ 页面导航成功")
            
            browser.close()
            print("✅ 浏览器关闭成功")
        
        print("\n✅ 浏览器启动测试通过！\n")
        return True
    except Exception as e:
        print(f"❌ 浏览器启动测试失败: {e}")
        return False


def test_csv_operations():
    """测试CSV文件操作"""
    print("=" * 60)
    print("测试5: CSV文件操作")
    print("=" * 60)
    
    import csv
    import tempfile
    
    # 创建临时CSV文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        csv_file = f.name
        writer = csv.DictWriter(f, fieldnames=['user_id', 'username', 'follow_time'])
        writer.writeheader()
        writer.writerow({'user_id': '123', 'username': '测试用户1', 'follow_time': '2026-04-20'})
        writer.writerow({'user_id': '456', 'username': '测试用户2', 'follow_time': '2026-04-20'})
    
    print(f"CSV文件创建: {csv_file}")
    
    # 读取CSV文件
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        users = list(reader)
    
    print(f"读取到 {len(users)} 个用户")
    for user in users:
        print(f"  - {user['username']} ({user['user_id']})")
    
    # 清理
    os.unlink(csv_file)
    print("✅ CSV文件清理成功")
    
    print("\n✅ CSV文件操作测试通过！\n")
    return True


def test_script_structure():
    """测试脚本结构"""
    print("=" * 60)
    print("测试6: 脚本结构检查")
    print("=" * 60)
    
    project_dir = Path(__file__).parent
    
    # 检查必要文件
    required_files = [
        'main.py',
        'scripts/export_following.py',
        'scripts/batch_follow.py',
        'scripts/unfollow.py',
        'src/progress.py',
        'requirements.txt',
        'README.md',
        'QUICKSTART.md',
        'USAGE.md'
    ]
    
    all_exist = True
    for file in required_files:
        file_path = project_dir / file
        if file_path.exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} 不存在")
            all_exist = False
    
    if all_exist:
        print("\n✅ 脚本结构测试通过！\n")
        return True
    else:
        print("\n❌ 脚本结构测试失败！\n")
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("小红书关注列表迁移工具 - 测试套件")
    print("=" * 60 + "\n")
    
    tests = [
        ("导入测试", test_imports),
        ("进度跟踪器测试", test_progress_tracker),
        ("批次进度跟踪器测试", test_batch_progress_tracker),
        ("浏览器启动测试", test_browser_launch),
        ("CSV文件操作测试", test_csv_operations),
        ("脚本结构测试", test_script_structure)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} 异常: {e}")
            results.append((name, False))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！脚本可以正常使用。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
