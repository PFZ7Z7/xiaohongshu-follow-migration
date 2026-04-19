"""
进度显示模块 - 使用tqdm实现美观的进度条

参考了tqdm库的最佳实践，支持实时进度更新和统计信息显示
"""
from tqdm import tqdm
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import sys


class ProgressTracker:
    """进度跟踪器
    
    支持：
    - 实时进度条显示
    - 成功/失败/跳过统计
    - 预估剩余时间
    - 动态更新附加信息
    """
    
    def __init__(
        self,
        total: int,
        description: str = "处理中",
        unit: str = "用户",
        show_stats: bool = True
    ):
        self.total = total
        self.description = description
        self.unit = unit
        self.show_stats = show_stats
        self.start_time = datetime.now()
        self.stats = {
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "captcha": 0
        }
        self.pbar: Optional[tqdm] = None
        self.current_user = ""
    
    def __enter__(self):
        """进入上下文管理器"""
        self.pbar = tqdm(
            total=self.total,
            desc=self.description,
            unit=self.unit,
            ncols=120,
            bar_format=[
                '{l_bar}{bar}|',
                ' {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
                ' {rate_fmt}'
            ],
            file=sys.stdout,
            leave=True,
            dynamic_ncols=True
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器"""
        if self.pbar:
            self.pbar.close()
        # 打印最终统计
        if self.show_stats:
            self._print_final_stats()
    
    def _print_final_stats(self):
        """打印最终统计信息"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        print(f"\n{'='*60}")
        print(f"处理完成！总耗时: {elapsed:.1f}秒")
        print(f"  ✅ 成功: {self.stats['success']}")
        print(f"  ❌ 失败: {self.stats['failed']}")
        print(f"  ⏭️  跳过: {self.stats['skipped']}")
        print(f"  🔐 验证码: {self.stats['captcha']}")
        if self.stats['success'] > 0:
            avg_time = elapsed / (self.stats['success'] + self.stats['failed'])
            print(f"  ⏱️  平均耗时: {avg_time:.2f}秒/用户")
        print(f"{'='*60}")
    
    def update(self, n: int = 1, **kwargs):
        """更新进度
        
        Args:
            n: 更新的步数
            **kwargs: 附加的统计信息（如 success=1, failed=0）
        """
        if self.pbar:
            self.pbar.update(n)
            
            # 更新统计
            for key, value in kwargs.items():
                if key in self.stats:
                    self.stats[key] += value
            
            # 更新进度条右侧的附加信息
            if self.show_stats:
                postfix = {
                    "成功": self.stats["success"],
                    "失败": self.stats["failed"]
                }
                if self.stats["captcha"] > 0:
                    postfix["验证码"] = self.stats["captcha"]
                self.pbar.set_postfix(**postfix)
    
    def set_postfix(self, **kwargs):
        """设置进度条右侧的附加信息"""
        if self.pbar:
            self.pbar.set_postfix(**kwargs)
    
    def set_description(self, description: str):
        """设置进度条描述"""
        if self.pbar:
            self.pbar.set_description(description)
    
    def record_success(self, user_name: str = ""):
        """记录成功"""
        self.stats["success"] += 1
        self.current_user = user_name
        self.set_postfix(
            成功=self.stats["success"],
            失败=self.stats["failed"],
            当前=user_name[:10] if user_name else ""
        )
    
    def record_failed(self, user_name: str = ""):
        """记录失败"""
        self.stats["failed"] += 1
        self.current_user = user_name
        self.set_postfix(
            成功=self.stats["success"],
            失败=self.stats["failed"],
            当前=user_name[:10] if user_name else ""
        )
    
    def record_captcha(self):
        """记录验证码触发"""
        self.stats["captcha"] += 1
        self.set_postfix(
            成功=self.stats["success"],
            失败=self.stats["failed"],
            验证码=self.stats["captcha"]
        )
    
    def record_skip(self):
        """记录跳过"""
        self.stats["skipped"] += 1
    
    @property
    def success_count(self) -> int:
        return self.stats["success"]
    
    @property
    def failed_count(self) -> int:
        return self.stats["failed"]
    
    @property
    def elapsed_seconds(self) -> float:
        return (datetime.now() - self.start_time).total_seconds()
    
    def get_elapsed_str(self) -> str:
        """获取已用时间字符串"""
        elapsed = self.elapsed_seconds
        if elapsed < 60:
            return f"{elapsed:.1f}秒"
        elif elapsed < 3600:
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            return f"{minutes}分{seconds}秒"
        else:
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            return f"{hours}小时{minutes}分"


class BatchProgressTracker:
    """批次进度跟踪器
    
    用于跟踪多批次任务的整体进度
    """
    
    def __init__(
        self,
        total_batches: int,
        total_items: int,
        description: str = "批次处理"
    ):
        self.total_batches = total_batches
        self.total_items = total_items
        self.description = description
        self.current_batch = 0
        self.batch_progress: Optional[ProgressTracker] = None
        self.start_time = datetime.now()
    
    def __enter__(self):
        """进入批次处理"""
        print(f"\n{'='*60}")
        print(f"{self.description}")
        print(f"总批次数: {self.total_batches}, 总用户数: {self.total_items}")
        print(f"{'='*60}\n")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出批次处理"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        print(f"\n{'='*60}")
        print(f"全部批次处理完成！总耗时: {elapsed:.1f}秒 ({elapsed/60:.1f}分钟)")
        print(f"{'='*60}\n")
    
    def start_batch(self, batch_num: int, batch_size: int):
        """开始一个新批次"""
        self.current_batch = batch_num
        print(f"\n--- 批次 {batch_num}/{self.total_batches} (共{batch_size}人) ---")
        if self.batch_progress:
            self.batch_progress.__exit__(None, None, None)
        self.batch_progress = ProgressTracker(
            total=batch_size,
            description=f"批次{batch_num}",
            unit="用户"
        )
        self.batch_progress.__enter__()
    
    def end_batch(self):
        """结束当前批次"""
        if self.batch_progress:
            self.batch_progress.__exit__(None, None, None)
    
    @property
    def current_progress(self) -> Optional[ProgressTracker]:
        return self.batch_progress
