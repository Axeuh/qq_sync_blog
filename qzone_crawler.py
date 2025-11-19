"""
QQ空间爬虫模块
"""

import asyncio
import json
import time
import re
import logging
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from qzone_api import QzoneApi
from qzone_api.login import QzoneLogin

from config import MONITOR_CONFIG


class QZoneCrawler:
    def __init__(self):
        self.qzone = None
        self.cookies_str = None
        self.g_tk = None
        self.qq_number = None
        self.login_state_file = MONITOR_CONFIG['login_state_file']
    
    def _save_login_state(self):
        """保存登录状态到文件"""
        if not self.cookies_str or not self.g_tk or not self.qq_number:
            return
        
        state = {
            'cookies_str': self.cookies_str,
            'g_tk': self.g_tk,
            'qq_number': self.qq_number,
            'save_time': int(time.time())
        }
        
        try:
            with open(self.login_state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            logging.info("登录状态已保存")
        except Exception as e:
            logging.error(f"保存登录状态失败: {e}")
    
    def _load_login_state(self) -> bool:
        """从文件加载登录状态"""
        try:
            if not os.path.exists(self.login_state_file):
                return False
            
            with open(self.login_state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # 检查状态是否过期（24小时内有效）
            save_time = state.get('save_time', 0)
            if time.time() - save_time > 24 * 60 * 60:
                logging.info("登录状态已过期，需要重新登录")
                return False
            
            self.cookies_str = state['cookies_str']
            self.g_tk = state['g_tk']
            self.qq_number = state['qq_number']
            self.qzone = QzoneApi()
            
            logging.info(f"从文件加载登录状态成功，QQ: {self.qq_number}")
            return True
            
        except Exception as e:
            logging.error(f"加载登录状态失败: {e}")
            return False
    
    def _extract_qq_number(self, qq_str: str) -> str:
        """从可能包含前缀的QQ号字符串中提取纯数字QQ号"""
        match = re.search(r'\d+', qq_str)
        if match:
            return match.group()
        return qq_str
    
    async def login(self, qq: Optional[str] = None, password: Optional[str] = None) -> bool:
        """登录QQ空间"""
        if self._load_login_state():
            if await self._verify_login_state():
                logging.info("使用保存的登录状态成功")
                return True
            else:
                logging.info("保存的登录状态已失效，需要重新登录")
        
        # 需要重新登录
        try:
            qzone_login = QzoneLogin()
            
            if qq and password:
                login_result = await qzone_login.login(qq, password)
            else:
                login_result = await qzone_login.login()
            
            if login_result["code"] == 0:
                raw_qq = login_result["qq"]
                clean_qq = self._extract_qq_number(raw_qq)
                logging.info(f"登录成功! 原始QQ: {raw_qq}, 提取后QQ: {clean_qq}")
                
                cookies = login_result["cookies"]
                self.cookies_str = '; '.join([f"{k}={v}" for k, v in cookies.items()])
                self.g_tk = login_result["bkn"]
                self.qq_number = clean_qq
                
                self.qzone = QzoneApi()
                
                # 保存登录状态
                self._save_login_state()
                return True
            else:
                logging.error(f"登录失败: {login_result.get('message', '未知错误')}")
                return False
                
        except Exception as e:
            logging.error(f"登录过程中出现错误: {e}")
            return False
    
    async def _verify_login_state(self) -> bool:
        """验证登录状态是否仍然有效"""
        try:
            messages = await self.get_shuoshuo_list(count=1)
            return messages is not None and len(messages) >= 0
        except Exception as e:
            logging.error(f"验证登录状态失败: {e}")
            return False
    
    def _parse_jsonp_response(self, response: str) -> Any:
        """解析JSONP响应"""
        if not response:
            return None
        
        try:
            if response.strip().startswith('{') or response.strip().startswith('['):
                return json.loads(response)
            
            match = re.search(r'_preloadCallback\((\{.*\})\)', response)
            if match:
                return json.loads(match.group(1))
            
            match = re.search(r'[\w_]*\((\{.*\})\)', response)
            if match:
                return json.loads(match.group(1))
            
            return json.loads(response)
        except json.JSONDecodeError as e:
            logging.error(f"JSON解析失败: {e}, 响应内容: {response[:200]}...")
            return None
    
    def _extract_messages_from_raw_response(self, response: Any) -> List[Dict]:
        """
        从原始API响应中提取说说列表
        """
        messages = []
        
        if not response:
            return messages
        
        if isinstance(response, dict):
            if 'msglist' in response and isinstance(response['msglist'], list):
                messages = response['msglist']
            elif 'data' in response and isinstance(response['data'], list):
                messages = response['data']
            elif 'message' in response and isinstance(response['message'], list):
                messages = response['message']
            elif 'feeds' in response and isinstance(response['feeds'], list):
                messages = response['feeds']
        
        messages = [msg for msg in messages if msg]
        logging.info(f"从原始响应中提取到 {len(messages)} 条消息")
        return messages

    def _parse_timestamp(self, timestamp: int) -> Dict[str, Any]:
        """解析时间戳"""
        try:
            if timestamp > 10**12:  # 13位时间戳
                timestamp = timestamp / 1000
            
            dt = datetime.fromtimestamp(timestamp)
            return {
                'timestamp': timestamp,
                'formatted': dt.strftime('%Y-%m-%d %H:%M:%S'),
                'date': dt.strftime('%Y-%m-%d'),
                'time': dt.strftime('%H:%M:%S'),
                'iso': dt.isoformat()
            }
        except:
            return {
                'timestamp': timestamp,
                'formatted': str(timestamp),
                'date': '未知',
                'time': '未知',
                'iso': '未知'
            }

    def _extract_images_from_raw_msg(self, raw_msg: Dict) -> List[Dict]:
        """从原始消息中提取图片信息"""
        images = []
        
        if 'pic' in raw_msg and isinstance(raw_msg['pic'], list):
            for pic_info in raw_msg['pic']:
                if isinstance(pic_info, dict):
                    possible_url_fields = ['pic_id', 'url1', 'url2', 'url3', 'smallurl']
                    url = None
                    for field in possible_url_fields:
                        url_candidate = pic_info.get(field)
                        if url_candidate and isinstance(url_candidate, str) and url_candidate.startswith('http'):
                            url = url_candidate
                            break
                    
                    if url:
                        images.append({
                            'url': url,
                            'width': pic_info.get('width', 0),
                            'height': pic_info.get('height', 0),
                            'pic_id': pic_info.get('pic_id', ''),
                            'pictype': pic_info.get('pictype', 0)
                        })
        
        if 'images' in raw_msg and isinstance(raw_msg['images'], list):
            for img in raw_msg['images']:
                if isinstance(img, dict) and img.get('url'):
                    images.append({
                        'url': img['url'],
                        'width': img.get('width', 0),
                        'height': img.get('height', 0)
                    })
        
        pic_ids = raw_msg.get('pic_ids', [])
        if pic_ids and isinstance(pic_ids, list):
            for pic_id in pic_ids:
                if pic_id:
                    images.append({
                        'url': f"pic_id_{pic_id}",
                        'id': pic_id
                    })
        
        return images

    def _clean_content_preserve_newlines(self, content: str) -> str:
        """
        清理内容但保留换行符
        """
        if not content:
            return ""
        
        content = re.sub(r'\[em\]e(\d+)\[\/em\]', lambda m: f'[表情{eval(m.group(1))}]', content)
        content = re.sub(r'@\{uin:(\d+),nick:([^,]+),who:(\d+)\}', r'@\2', content)
        content = content.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        content = content.replace('&quot;', '"').replace('&#39;', "'")
        
        return content.strip()

    def _parse_raw_shuoshuo(self, raw_msg: Dict) -> Optional[Dict]:
        """
        解析原始说说数据，保留所有原始格式
        """
        try:
            if not isinstance(raw_msg, dict):
                return None
            
            msg_id = raw_msg.get('tid') or raw_msg.get('cur_key', '')
            uin = raw_msg.get('uin', '')
            timestamp = raw_msg.get('created_time', 0)
            
            raw_content = raw_msg.get('content', '')
            
            conlist = raw_msg.get('conlist', [])
            if conlist and isinstance(conlist, list):
                for con_item in conlist:
                    if isinstance(con_item, dict) and con_item.get('type') == 2:
                        con_content = con_item.get('con', '')
                        if con_content:
                            raw_content = con_content
                            break
            
            time_info = self._parse_timestamp(timestamp)
            images = self._extract_images_from_raw_msg(raw_msg)
            
            detailed_msg = {
                'id': msg_id,
                'uin': uin,
                'content': {
                    'raw': raw_content,
                    'parsed': self._clean_content_preserve_newlines(raw_content),
                    'has_media': len(images) > 0
                },
                'time': time_info,
                'media': {
                    'images': images,
                    'image_count': len(images)
                },
                'raw_data': raw_msg
            }
            
            return detailed_msg
            
        except Exception as e:
            logging.error(f"解析原始说说数据失败: {e}")
            logging.debug(f"问题消息内容: {raw_msg}")
            return None

    async def get_shuoshuo_list(self, target_qq: str = None, count: int = 20) -> List[Dict]:
        """
        获取说说列表 - 使用原始API响应保留回车符
        """
        if not self.qzone or not self.cookies_str or not self.g_tk:
            logging.error("请先登录!")
            return []
        
        try:
            target_qq = target_qq or self.qq_number
            if isinstance(target_qq, str):
                target_qq = self._extract_qq_number(target_qq)
            
            raw_response = await self.qzone._get_messages_list(
                target_qq=int(target_qq),
                g_tk=self.g_tk,
                cookies=self.cookies_str,
                num=count
            )
            
            # 打印原始响应（调试用）
            logging.debug(f"原始响应内容: {raw_response}")
            
            parsed_response = self._parse_jsonp_response(raw_response)
            
            # 详细的API响应信息检查
            if isinstance(parsed_response, dict):
                api_message = parsed_response.get('message')
                api_code = parsed_response.get('code')
                api_subcode = parsed_response.get('subcode')
                api_total = parsed_response.get('total')
                
                # 记录API返回的主要信息
                log_parts = []
                if api_code is not None:
                    log_parts.append(f"code={api_code}")
                if api_subcode is not None:
                    log_parts.append(f"subcode={api_subcode}")
                if api_total is not None:
                    log_parts.append(f"total={api_total}")
                if api_message and api_message.strip():
                    log_parts.append(f"message='{api_message}'")
                
                if log_parts:
                    logging.info(f"API响应: {', '.join(log_parts)}")
                
                # 检查错误情况
                if api_code != 0:
                    logging.warning(f"API返回非零代码: {api_code}, 消息: {api_message}")
                
            elif parsed_response is None:
                logging.warning("API响应解析为None")
            else:
                logging.info(f"API响应类型: {type(parsed_response)}")
            
            messages = self._extract_messages_from_raw_response(parsed_response)
            
            detailed_messages = []
            for msg in messages:
                detailed_msg = self._parse_raw_shuoshuo(msg)
                if detailed_msg:
                    detailed_messages.append(detailed_msg)
            
            logging.info(f"成功解析 {len(detailed_messages)} 条说说")
            return detailed_messages
            
        except Exception as e:
            logging.error(f"获取说说列表失败: {e}")
            import traceback
            logging.error(f"详细错误: {traceback.format_exc()}")
            return []
