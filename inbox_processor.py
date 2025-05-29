#!/usr/bin/env python3
"""
智能文件整理助手 - 文件夹批处理版本

监控或批量处理文件夹中的文件，自动整理归档到知识库中。
"""

import sys
import time
import logging
from pathlib import Path
from typing import List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import click
from colorama import init, Fore, Style

# 初始化colorama
init()

# 添加src目录到路径
sys.path.append(str(Path(__file__).parent / 'src'))

from src.config_manager import ConfigManager
from src.file_processor import FileProcessor
from src.llm_client import LLMClient
from src.utils import setup_logging, print_banner


class InboxHandler(FileSystemEventHandler):
    """文件夹监控处理器"""
    
    def __init__(self, processor_instance):
        self.processor = processor_instance
        self.logger = logging.getLogger(__name__)
        # 防止重复处理的文件集合
        self.processing_files = set()
    
    def on_created(self, event):
        """文件创建时的处理"""
        if not event.is_directory:
            file_path = Path(event.src_path)
            # 延迟一秒确保文件完全写入
            time.sleep(1)
            self.process_file_safe(file_path)
    
    def on_moved(self, event):
        """文件移动时的处理"""
        if not event.is_directory:
            file_path = Path(event.dest_path)
            self.process_file_safe(file_path)
    
    def process_file_safe(self, file_path: Path):
        """安全处理文件（避免重复处理）"""
        if str(file_path) in self.processing_files:
            return
        
        try:
            self.processing_files.add(str(file_path))
            if file_path.exists():
                self.processor.process_single_file(file_path)
        finally:
            self.processing_files.discard(str(file_path))


class InboxProcessor:
    """文件夹批处理器"""
    
    def __init__(self, config_path: str = None):
        """初始化处理器"""
        # 加载配置
        self.config_manager = ConfigManager(config_path=config_path)
        self.config = self.config_manager.config
        
        # 设置日志
        setup_logging(self.config, verbose=True)
        self.logger = logging.getLogger(__name__)
        
        # 初始化核心组件
        self.llm_client = LLMClient(self.config)
        self.file_processor = FileProcessor(self.config, self.llm_client)
        
        # 设置默认文件夹路径
        self.inbox_folder = Path("./inbox")
        self.processed_folder = Path("./processed")
        
        # 创建必要的文件夹
        self.setup_folders()
    
    def setup_folders(self):
        """设置必要的文件夹"""
        self.inbox_folder.mkdir(exist_ok=True)
        self.processed_folder.mkdir(exist_ok=True)
        
        # 创建说明文件
        readme_path = self.inbox_folder / "README.md"
        if not readme_path.exists():
            readme_path.write_text("""# 📥 待处理文件夹

## 使用说明

1. **直接拖放文件**：将需要整理的文件直接拖放到此文件夹中
2. **支持的格式**：
   - Word文档 (.docx)
   - Excel表格 (.xlsx) 
   - PDF文档 (.pdf)
   - 文本文件 (.txt)
   - Markdown文件 (.md)

3. **自动处理**：
   - 程序会自动检测新文件
   - 使用AI分析文档内容
   - 自动重命名并归档到知识库

4. **处理完成后**：
   - 原文件会移动到 `../processed/` 文件夹
   - 整理后的文件保存在 `../knowledge_base/` 中

## 批量处理命令

```bash
# 处理当前文件夹中的所有文件
python inbox_processor.py --process-all

# 开启文件夹监控模式
python inbox_processor.py --watch

# 处理指定文件夹
python inbox_processor.py --folder "你的文件夹路径"
```

---
*将文件拖放到此文件夹即可开始整理！*
""", encoding='utf-8')
    
    def process_all_files(self, auto_confirm: bool = False) -> dict:
        """处理文件夹中的所有文件"""
        print_banner()
        
        # 获取所有支持的文件
        files = self.get_supported_files()
        
        if not files:
            click.echo(f"{Fore.YELLOW}📂 待处理文件夹为空{Style.RESET_ALL}")
            return {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}
        
        click.echo(f"{Fore.CYAN}📁 发现 {len(files)} 个待处理文件{Style.RESET_ALL}")
        
        if not auto_confirm:
            if not click.confirm(f"\n🤖 是否开始智能整理这些文件？"):
                click.echo(f"{Fore.YELLOW}❌ 用户取消操作{Style.RESET_ALL}")
                return {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}
        
        # 处理所有文件
        results = {'total': len(files), 'success': 0, 'failed': 0, 'skipped': 0}
        
        for i, file_path in enumerate(files, 1):
            click.echo(f"\n{Fore.BLUE}[{i}/{len(files)}] 🔄 处理: {file_path.name}{Style.RESET_ALL}")
            
            try:
                success = self.process_single_file(file_path)
                if success:
                    results['success'] += 1
                else:
                    results['skipped'] += 1
            except Exception as e:
                self.logger.error(f"处理文件失败 {file_path}: {e}")
                click.echo(f"  {Fore.RED}❌ 处理失败: {str(e)}{Style.RESET_ALL}")
                results['failed'] += 1
        
        # 显示处理结果
        self.display_summary(results)
        return results
    
    def process_single_file(self, file_path: Path) -> bool:
        """处理单个文件"""
        try:
            # 使用文件处理器处理文件
            result = self.file_processor.process_file(file_path, dry_run=False)
            
            if result['status'] == 'error':
                click.echo(f"  {Fore.RED}❌ 分析失败: {result['error']}{Style.RESET_ALL}")
                return False
            
            # 显示处理信息
            click.echo(f"  {Fore.CYAN}🎯 主体: {result['subject']}{Style.RESET_ALL}")
            click.echo(f"  {Fore.CYAN}📅 日期: {result['date']}{Style.RESET_ALL}")
            click.echo(f"  {Fore.YELLOW}📝 新名称: {result['new_name']}{Style.RESET_ALL}")
            click.echo(f"  {Fore.MAGENTA}📁 存储路径: {Path(result['target_path']).parent}{Style.RESET_ALL}")
            
            # 执行文件操作
            final_result = self.file_processor.execute_operation(result)
            
            if final_result['status'] == 'success':
                click.echo(f"  {Fore.GREEN}✅ 整理完成{Style.RESET_ALL}")
                
                # 移动原文件到已处理文件夹
                processed_path = self.processed_folder / file_path.name
                if file_path.exists():
                    file_path.rename(processed_path)
                    click.echo(f"  {Fore.BLUE}📦 原文件已移至: {processed_path}{Style.RESET_ALL}")
                
                return True
            else:
                click.echo(f"  {Fore.RED}❌ 操作失败: {final_result.get('error', '未知错误')}{Style.RESET_ALL}")
                return False
                
        except Exception as e:
            self.logger.error(f"处理文件异常 {file_path}: {e}")
            click.echo(f"  {Fore.RED}💥 处理异常: {str(e)}{Style.RESET_ALL}")
            return False
    
    def get_supported_files(self) -> List[Path]:
        """获取文件夹中所有支持的文件"""
        supported_extensions = self.config['file_processing']['supported_extensions']
        files = []
        
        for file_path in self.inbox_folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                # 跳过README文件
                if file_path.name.lower() != 'readme.md':
                    files.append(file_path)
        
        return sorted(files)
    
    def watch_folder(self):
        """监控文件夹变化"""
        click.echo(f"{Fore.GREEN}👀 开始监控文件夹: {self.inbox_folder.absolute()}{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}💡 请将待处理文件拖放到上述文件夹中{Style.RESET_ALL}")
        click.echo(f"{Fore.YELLOW}⏹️  按 Ctrl+C 停止监控{Style.RESET_ALL}\n")
        
        # 设置文件夹监控
        event_handler = InboxHandler(self)
        observer = Observer()
        observer.schedule(event_handler, str(self.inbox_folder), recursive=False)
        
        try:
            observer.start()
            
            # 首先处理现有文件
            existing_files = self.get_supported_files()
            if existing_files:
                click.echo(f"{Fore.CYAN}📁 发现 {len(existing_files)} 个现有文件，开始处理...{Style.RESET_ALL}")
                for file_path in existing_files:
                    self.process_single_file(file_path)
            
            # 持续监控
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            click.echo(f"\n{Fore.YELLOW}🛑 监控已停止{Style.RESET_ALL}")
        finally:
            observer.stop()
            observer.join()
    
    def display_summary(self, results: dict):
        """显示处理结果摘要"""
        click.echo(f"\n{Fore.CYAN}{'='*50}")
        click.echo(f"📊 批量处理完成统计:")
        click.echo(f"  📁 总文件数: {results['total']}")
        click.echo(f"  {Fore.GREEN}✅ 成功: {results['success']}{Style.RESET_ALL}")
        click.echo(f"  {Fore.RED}❌ 失败: {results['failed']}{Style.RESET_ALL}")
        if results['skipped'] > 0:
            click.echo(f"  {Fore.YELLOW}⏭️ 跳过: {results['skipped']}{Style.RESET_ALL}")
        click.echo(f"{'='*50}{Style.RESET_ALL}")


@click.command()
@click.option('--folder', '-f', type=click.Path(exists=True), 
              help='指定待处理文件夹路径（默认: ./inbox）')
@click.option('--config', '-c', type=click.Path(exists=True), 
              help='配置文件路径（默认: config.yaml）')
@click.option('--process-all', '-a', is_flag=True, 
              help='处理文件夹中的所有文件')
@click.option('--watch', '-w', is_flag=True, 
              help='开启文件夹监控模式')
@click.option('--auto-confirm', '-y', is_flag=True, 
              help='自动确认，跳过用户确认')
def main(folder, config, process_all, watch, auto_confirm):
    """
    智能文件整理助手 - 文件夹批处理版本
    
    将文件放入待处理文件夹，程序自动整理归档。
    
    使用方法：
    1. 将文件拖放到 ./inbox/ 文件夹
    2. 运行命令进行批量处理
    
    示例：
        # 处理所有待处理文件
        python inbox_processor.py --process-all
        
        # 开启监控模式
        python inbox_processor.py --watch
        
        # 处理指定文件夹
        python inbox_processor.py --folder "/path/to/files" --process-all
    """
    
    try:
        # 创建处理器实例
        processor = InboxProcessor(config_path=config)
        
        # 如果指定了自定义文件夹
        if folder:
            processor.inbox_folder = Path(folder)
        
        if watch:
            # 监控模式
            processor.watch_folder()
        elif process_all:
            # 批量处理模式
            processor.process_all_files(auto_confirm=auto_confirm)
        else:
            # 显示帮助信息
            click.echo(f"{Fore.CYAN}🤖 智能文件整理助手 - 文件夹批处理版本{Style.RESET_ALL}")
            click.echo(f"\n📁 待处理文件夹: {processor.inbox_folder.absolute()}")
            click.echo(f"📚 知识库路径: {processor.file_processor.knowledge_base_path.absolute()}")
            
            files = processor.get_supported_files()
            if files:
                click.echo(f"\n{Fore.YELLOW}📋 发现 {len(files)} 个待处理文件：{Style.RESET_ALL}")
                for file in files:
                    click.echo(f"  📄 {file.name}")
                    
                click.echo(f"\n💡 使用以下命令开始处理：")
                click.echo(f"  {Fore.GREEN}python inbox_processor.py --process-all{Style.RESET_ALL}")
                click.echo(f"  {Fore.GREEN}python inbox_processor.py --watch{Style.RESET_ALL}")
            else:
                click.echo(f"\n{Fore.YELLOW}📂 待处理文件夹为空{Style.RESET_ALL}")
                click.echo(f"💡 请将文件拖放到 {processor.inbox_folder} 文件夹中")
            
    except Exception as e:
        click.echo(f"{Fore.RED}❌ 程序运行出错: {str(e)}{Style.RESET_ALL}")
        logging.error(f"程序运行出错: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main() 