"""
主程序入口
"""

import asyncio
import logging
from datetime import datetime  # 添加这行

from config import LOGGING_CONFIG, WORDPRESS_CONFIG, MONITOR_CONFIG
from wordpress_publisher import WordPressPublisher
from qzone_crawler import QZoneCrawler
from qzone_monitor import QZoneMonitor


# 配置日志
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['level']),
    format=LOGGING_CONFIG['format'],
    handlers=[
        logging.FileHandler(LOGGING_CONFIG['filename'], encoding='utf-8'),
        logging.StreamHandler()
    ]
)


async def test_new_shuoshuo_detection():
    """测试新说说检测功能"""
    crawler = QZoneCrawler()
    
    if await crawler.login():
        logging.info("测试新说说检测...")
        
        messages = await crawler.get_shuoshuo_list(count=10)
        if messages:
            logging.info(f"当前有 {len(messages)} 条说说")
            
            for i, msg in enumerate(messages[:3]):
                msg_id = msg.get('id')
                raw_content = msg.get('content', {}).get('raw', '')[:50]
                timestamp = msg.get('time', {}).get('timestamp', 0)
                time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') if timestamp else '未知'
                
                logging.info(f"说说 {i+1}: ID={msg_id}, 时间={time_str}, 内容={repr(raw_content)}...")
        
        monitor = QZoneMonitor(None)
        monitor.qzone_crawler = crawler
        new_messages = await monitor.check_new_shuoshuo()
        
        if new_messages:
            logging.info(f"检测到 {len(new_messages)} 条新说说")
        else:
            logging.info("未检测到新说说")


async def main():
    """主函数"""
    await test_new_shuoshuo_detection()
    
    try:
        wp_publisher = WordPressPublisher(
            WORDPRESS_CONFIG['url'],
            WORDPRESS_CONFIG['username'],
            WORDPRESS_CONFIG['password']
        )
        logging.info("WordPress发布器初始化成功")
    except Exception as e:
        logging.error(f"WordPress发布器初始化失败: {e}")
        return
    
    monitor = QZoneMonitor(wp_publisher)
    
    await monitor.start_monitoring(interval=MONITOR_CONFIG['delay_time'])


if __name__ == "__main__":
    asyncio.run(main())
