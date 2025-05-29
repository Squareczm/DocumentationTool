#!/usr/bin/env python3
"""
智能文件整理助手 - 主程序
自动处理inbox中的文件，基于AI分析进行智能重命名和分类归档
"""

import os
import sys
import click
from pathlib import Path
from colorama import init, Fore, Style

# 初始化colorama
init()

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from inbox_processor import InboxProcessor


@click.command()
@click.option('--folder', '-f', type=click.Path(exists=True), 
              help='指定待处理文件夹路径（默认: ./inbox）')
@click.option('--config', '-c', type=click.Path(exists=True), 
              help='配置文件路径（默认: config.yaml）')
@click.option('--watch', '-w', is_flag=True, 
              help='开启文件夹监控模式，自动处理新文件')
@click.option('--auto-confirm', '-y', is_flag=True, 
              help='自动确认，跳过用户确认')
@click.option('--verbose', '-v', is_flag=True, 
              help='显示详细处理信息')
@click.option('--check', is_flag=True, 
              help='检查环境和配置')
def main(folder, config, watch, auto_confirm, verbose, check):
    """
    🤖 智能文件整理助手
    
    主要功能：
    - 自动分析文档内容，提取核心主体信息
    - 智能重命名文件为标准格式
    - 按业务类型自动分类归档到知识库
    - 支持DOCX、PDF、TXT、MD等多种格式
    
    使用方法：
    
    1. 基本用法（处理inbox中的所有文件）：
       python main.py
    
    2. 指定文件夹：
       python main.py -f "你的文件夹路径"
    
    3. 开启监控模式：
       python main.py --watch
    
    4. 自动确认处理：
       python main.py -y
    """
    
    if check:
        check_environment()
        return
    
    try:
        # 初始化处理器
        processor = InboxProcessor(config_path=config)
        
        # 设置文件夹路径
        if folder:
            processor.inbox_folder = Path(folder)
        
        if watch:
            # 监控模式
            click.echo(f"{Fore.CYAN}🔍 开启文件夹监控模式...{Style.RESET_ALL}")
            click.echo(f"{Fore.YELLOW}监控文件夹: {processor.inbox_folder}{Style.RESET_ALL}")
            click.echo(f"{Fore.YELLOW}按 Ctrl+C 停止监控{Style.RESET_ALL}")
            processor.watch_folder()
        else:
            # 批量处理模式
            results = processor.process_all_files(auto_confirm=auto_confirm)
            
            # 提示用户可以开启监控模式
            if results['total'] > 0:
                click.echo(f"\n{Fore.CYAN}💡 提示: 可以使用 'python main.py --watch' 开启自动监控模式{Style.RESET_ALL}")
    
    except KeyboardInterrupt:
        click.echo(f"\n{Fore.YELLOW}⚠️ 用户中断操作{Style.RESET_ALL}")
    except Exception as e:
        click.echo(f"{Fore.RED}❌ 程序运行出错: {e}{Style.RESET_ALL}")
        sys.exit(1)


def check_environment():
    """检查运行环境"""
    click.echo(f"{Fore.CYAN}🔧 检查运行环境...{Style.RESET_ALL}")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        click.echo(f"{Fore.RED}❌ Python版本过低，需要3.8+{Style.RESET_ALL}")
        return False
    else:
        click.echo(f"{Fore.GREEN}✅ Python版本: {sys.version}{Style.RESET_ALL}")
    
    # 检查依赖包
    required_packages = ['yaml', 'docx', 'openpyxl', 'PyPDF2', 'requests', 'click', 'colorama', 'watchdog']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            click.echo(f"{Fore.GREEN}✅ {package}{Style.RESET_ALL}")
        except ImportError:
            click.echo(f"{Fore.RED}❌ {package}{Style.RESET_ALL}")
            missing_packages.append(package)
    
    if missing_packages:
        click.echo(f"\n{Fore.YELLOW}缺少依赖包，请运行:{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}pip install {' '.join(missing_packages)}{Style.RESET_ALL}")
        return False
    
    # 检查配置文件
    config_file = Path("config.yaml")
    if config_file.exists():
        click.echo(f"{Fore.GREEN}✅ 配置文件存在{Style.RESET_ALL}")
        
        # 检查API密钥
        try:
            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            api_key = config.get('llm', {}).get('api_key', '')
            env_api_key = os.getenv('SMARTFILEORG_LLM_API_KEY')
            
            # 检查API密钥是否已正确配置
            if env_api_key and env_api_key.strip():
                click.echo(f"{Fore.GREEN}✅ API密钥已配置（环境变量）{Style.RESET_ALL}")
            elif api_key and api_key.strip() and not api_key.startswith('sk-your') and not api_key.startswith('your_'):
                click.echo(f"{Fore.GREEN}✅ API密钥已配置（配置文件）{Style.RESET_ALL}")
            else:
                click.echo(f"{Fore.YELLOW}⚠️ API密钥未配置，请按以下任一方式配置：{Style.RESET_ALL}")
                click.echo(f"{Fore.CYAN}   方式1: 编辑 config.yaml 文件第12行，将 api_key: \"\" 改为 api_key: \"你的API密钥\"{Style.RESET_ALL}")
                click.echo(f"{Fore.CYAN}   方式2: 设置环境变量 SMARTFILEORG_LLM_API_KEY=你的API密钥{Style.RESET_ALL}")
                click.echo(f"{Fore.MAGENTA}   💡 获取密钥: OpenAI https://platform.openai.com/api-keys{Style.RESET_ALL}")
                click.echo(f"{Fore.MAGENTA}   💡 获取密钥: DeepSeek https://platform.deepseek.com/api_keys{Style.RESET_ALL}")
        except Exception as e:
            click.echo(f"{Fore.RED}❌ 配置文件格式错误: {e}{Style.RESET_ALL}")
            return False
    else:
        click.echo(f"{Fore.YELLOW}⚠️ 配置文件不存在，请复制config.example.yaml为config.yaml{Style.RESET_ALL}")
        return False
    
    # 检查文件夹
    inbox_dir = Path("inbox")
    kb_dir = Path("knowledge_base")
    
    inbox_dir.mkdir(exist_ok=True)
    kb_dir.mkdir(exist_ok=True)
    
    click.echo(f"{Fore.GREEN}✅ 文件夹结构正常{Style.RESET_ALL}")
    
    click.echo(f"\n{Fore.GREEN}🎉 环境检查完成，可以开始使用！{Style.RESET_ALL}")
    click.echo(f"\n{Fore.CYAN}使用方法:{Style.RESET_ALL}")
    click.echo(f"  1. 将文件拖放到 inbox/ 文件夹中")
    click.echo(f"  2. 运行: python main.py")
    click.echo(f"  3. 或者开启监控: python main.py --watch")
    
    return True


if __name__ == '__main__':
    main() 