"""
QQ空间监控器模块
"""

import asyncio
import json
import time
import re
import logging
from typing import List, Dict
from datetime import datetime

from qzone_crawler import QZoneCrawler
from wordpress_publisher import WordPressPublisher
from config import MONITOR_CONFIG


class QZoneMonitor:
    def __init__(self, wordpress_publisher: WordPressPublisher):
        self.qzone_crawler = QZoneCrawler()
        self.wp_publisher = wordpress_publisher
        self.processed_shuoshuo_ids = set()
        self.last_check_time = int(time.time())
        self.is_running = False
        
        self._load_processed_ids()
    
    def _load_processed_ids(self):
        """加载已处理的说说ID"""
        try:
            with open(MONITOR_CONFIG['processed_ids_file'], 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.processed_shuoshuo_ids = set(data.get('processed_ids', []))
                self.last_check_time = data.get('last_check_time', int(time.time()))
            logging.info(f"已加载 {len(self.processed_shuoshuo_ids)} 个已处理说说ID")
        except FileNotFoundError:
            logging.info("未找到已处理说说记录文件，将创建新文件")
    
    def _save_processed_ids(self):
        """保存已处理的说说ID"""
        try:
            data = {
                'processed_ids': list(self.processed_shuoshuo_ids),
                'last_check_time': self.last_check_time,
                'update_time': datetime.now().isoformat()
            }
            with open(MONITOR_CONFIG['processed_ids_file'], 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"保存已处理说说ID失败: {e}")
    
    async def initialize(self) -> bool:
        """初始化监控器"""
        logging.info("正在初始化QQ空间监控器...")
        return await self.qzone_crawler.login()
    
    def should_sync(self, content: str) -> Dict[str, bool]:
        """
        检查内容是否包含同步指令
        返回: {'article': 是否同步文章, 'shuoshuo': 是否同步说说}
        """
        sync_article = bool(re.search(r'#同步文章', content))
        sync_shuoshuo = bool(re.search(r'#同步说说', content))
        
        return {
            'article': sync_article,
            'shuoshuo': sync_shuoshuo
        }
    
    def clean_content(self, content: str) -> str:
        """
        清理内容，移除同步指令
        """
        content = re.sub(r'#同步文章\s*', '', content)
        content = re.sub(r'#同步说说\s*', '', content)
        content = re.sub(r'\[em\]e\d+\[\/em\]', '', content)
        content = re.sub(r'\n\s*\n', '\n\n', content)
        
        return content.strip()
    
    def extract_images(self, shuoshuo: Dict) -> List[str]:
        """提取图片URL"""
        images_urls = []
        
        raw_data = shuoshuo.get('raw_data', {})
        
        if 'pic' in raw_data and isinstance(raw_data['pic'], list):
            for pic_info in raw_data['pic']:
                if isinstance(pic_info, dict):
                    possible_url_fields = ['pic_id', 'url1', 'url2', 'url3', 'smallurl']
                    for field in possible_url_fields:
                        url = pic_info.get(field)
                        if url and isinstance(url, str) and url.startswith('http'):
                            images_urls.append(url)
                            break
        
        if not images_urls:
            images_data = shuoshuo.get('media', {}).get('images', [])
            for img in images_data:
                url = img.get('url', '')
                if url and isinstance(url, str) and url.startswith('http'):
                    images_urls.append(url)
        
        return list(set(images_urls))    
    
    async def check_new_shuoshuo(self) -> List[Dict]:
        """检查新说说"""
        try:
            messages = await self.qzone_crawler.get_shuoshuo_list(count=20)
            new_messages = []
            
            for msg in messages:
                msg_id = msg.get('id')
                
                if not msg_id:
                    logging.warning(f"说说缺少ID字段: {msg.get('content', {}).get('raw', '')[:50]}...")
                    continue
                
                if msg_id not in self.processed_shuoshuo_ids:
                    new_messages.append(msg)
                    self.processed_shuoshuo_ids.add(msg_id)
                    
                    raw_content = msg.get('content', {}).get('raw', '')
                    logging.info(f"发现新说说: {msg_id}, 内容: {repr(raw_content[:100])}...")
            
            self.last_check_time = int(time.time())
            return new_messages
            
        except Exception as e:
            logging.error(f"检查新说说时出错: {e}")
            return []
    
    async def process_shuoshuo(self, shuoshuo: Dict):
        """处理单条说说"""
        content_data = shuoshuo.get('content', {})
        raw_content = content_data.get('raw', '')
        parsed_content = content_data.get('parsed', '')
        
        images = self.extract_images(shuoshuo)
        
        sync_commands = self.should_sync(raw_content)
        
        if not any(sync_commands.values()):
            logging.info(f"说说不包含同步指令，跳过。内容: {repr(raw_content[:50])}...")
            return
        
        clean_content = self.clean_content(parsed_content)
        
        if not clean_content and not images:
            logging.info("说说内容为空且无图片，跳过")
            return
        
        logging.info(f"开始处理说说同步，指令: {sync_commands}")
        logging.info(f"清理后内容: {repr(clean_content)}")
        
        success_count = 0
        
        if sync_commands['article']:
            title = None
            lines = clean_content.split('\n')
            if len(lines) > 1:
                title = lines[0].strip()
                content_body = '\n'.join(lines[1:]).strip()
            else:
                content_body = clean_content
            
            success = self.wp_publisher.publish_article(title, content_body, images)
            if success:
                logging.info("文章同步成功")
                success_count += 1
            else:
                logging.error("文章同步失败")
        
        if sync_commands['shuoshuo']:
            success = self.wp_publisher.publish_shuoshuo(clean_content, images)
            if success:
                logging.info("说说同步成功")
                success_count += 1
            else:
                logging.error("说说同步失败")
        
        if success_count > 0:
            self._save_processed_ids()
    
    async def start_monitoring(self, interval: int = None):
        """开始监控"""
        if not await self.initialize():
            logging.error("QQ空间登录失败，无法启动监控")
            return
        
        check_interval = interval or MONITOR_CONFIG['delay_time']
        logging.info(f"开始监控QQ空间动态，检查间隔: {check_interval}秒")
        logging.info("同步指令说明:")
        logging.info("  - 使用 '#同步文章' 将内容发布为WordPress文章")
        logging.info("  - 使用 '#同步说说' 将内容发布为WordPress说说")
        
        self.is_running = True
        
        try:
            while self.is_running:
                try:
                    new_shuoshuos = await self.check_new_shuoshuo()
                    
                    if new_shuoshuos:
                        logging.info(f"发现 {len(new_shuoshuos)} 条新说说")
                        
                        for shuoshuo in new_shuoshuos:
                            await self.process_shuoshuo(shuoshuo)
                    else:
                        logging.info("未发现新说说")
                    
                    await asyncio.sleep(check_interval)
                    
                except Exception as e:
                    logging.error(f"监控循环出错: {e}")
                    await asyncio.sleep(check_interval)
                    
        except KeyboardInterrupt:
            logging.info("监控被用户中断")
        finally:
            self.is_running = False
            self._save_processed_ids()
