#!/usr/bin/env python3
"""
小红书关注列表迁移工具 - 主脚本

功能：整合导出、批量关注、取消关注功能
使用：python main.py <command> [options]

命令：
  export    导出关注列表
  follow    批量关注
  unfollow  取消关注
  help      显示帮助
"""

import argparse
import os
import sys
from pathlib import Path


def run_export(args):
    """运行导出命令"""
    script_path = Path(__file__).parent / "scripts" / "export_following.py"
    cmd = f"python {script_path} --account {args.account}"
    if args.output:
        cmd += f" --output {args.output}"
    os.system(cmd)


def run_follow(args):
    """运行批量关注命令"""
    script_path = Path(__file__).parent / "scripts" / "batch_follow.py"
    cmd = f"python {script_path} --account {args.account} --file {args.file}"
    if args.batch_size:
        cmd += f" --batch-size {args.batch_size}"
    if args.delay:
        cmd += f" --delay {args.delay}"
    if args.output:
        cmd += f" --output {args.output}"
    os.system(cmd)


def run_unfollow(args):
    """运行取消关注命令"""
    script_path = Path(__file__).parent / "scripts" / "unfollow.py"
    cmd = f"python {script_path} --account {args.account} --file {args.file}"
    if args.batch_size:
        cmd += f" --batch-size {args.batch_size}"
    if args.delay:
        cmd += f" --delay {args.delay}"
    if args.output:
        cmd += f" --output {args.output}"
    os.system(cmd)


def main():
    parser = argparse.ArgumentParser(
        description="小红书关注列表迁移工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  python main.py export --account old_account
  python main.py follow --account new_account --file data/following_old_account_*.csv
  python main.py unfollow --account old_account --file data/following_old_account_*.csv
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # export命令
    export_parser = subparsers.add_parser("export", help="导出关注列表")
    export_parser.add_argument("--account", "-a", required=True, help="账号名称")
    export_parser.add_argument("--output", "-o", default="data", help="输出目录")
    
    # follow命令
    follow_parser = subparsers.add_parser("follow", help="批量关注")
    follow_parser.add_argument("--account", "-a", required=True, help="账号名称")
    follow_parser.add_argument("--file", "-f", required=True, help="CSV文件路径")
    follow_parser.add_argument("--batch-size", "-b", type=int, default=50, help="每批关注数量")
    follow_parser.add_argument("--delay", "-d", type=int, default=10, help="批次间延迟（秒）")
    follow_parser.add_argument("--output", "-o", default="data", help="输出目录")
    
    # unfollow命令
    unfollow_parser = subparsers.add_parser("unfollow", help="取消关注")
    unfollow_parser.add_argument("--account", "-a", required=True, help="账号名称")
    unfollow_parser.add_argument("--file", "-f", required=True, help="CSV文件路径")
    unfollow_parser.add_argument("--batch-size", "-b", type=int, default=50, help="每批取消数量")
    unfollow_parser.add_argument("--delay", "-d", type=int, default=10, help="批次间延迟（秒）")
    unfollow_parser.add_argument("--output", "-o", default="data", help="输出目录")
    
    args = parser.parse_args()
    
    if args.command == "export":
        run_export(args)
    elif args.command == "follow":
        run_follow(args)
    elif args.command == "unfollow":
        run_unfollow(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
