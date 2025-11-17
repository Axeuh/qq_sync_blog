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
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods import posts
from wordpress_xmlrpc.methods.media import UploadFile
from wordpress_xmlrpc.compat import xmlrpc_client
import requests
import os
from urllib.parse import urlparse
import hashlib

# 网站根目录的qq_img文件夹路径
# 这里实际情需要您根据况修改为网站根目录的路径
my_web_image_url="https://www.your.com/qq_img/"

# qq动态图片保存位置
web_root_path = "/www/wwwroot/www.your.com"  

# wordpress地址及账号密码
WORDPRESS_CONFIG = {
        'url': "https://www.your.com/xmlrpc.php",
        'username': "your@your.com",
        'password': "yourpassword"
    }
delay_time=30
    
    
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('qzone_monitor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class WordPressPublisher:
    def __init__(self, url: str, username: str, password: str):
        self.wp = Client(url, username, password)
        self.url = url
        self.username = username
    
    def publish_shuoshuo(self, content: str, images: List[str] = None) -> bool:
        """
        在WordPress发布说说，图片保存到网站根目录并引用
        """
        try:
            post = WordPressPost()
            post.post_type = 'post'
            
            # 设置分类为"QQ空间"
            post.terms_names = {
                'category': ['QQ空间']
            }
            
            post.title = f"说说 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            post.content = f"<p>{content.replace(chr(10), '<br>')}</p>"  # 保留换行
            
            # 如果有图片，下载并保存到网站目录
            if images:
                for img_url in images[:3]:  # 限制图片数量
                    try:
                        # 下载图片并保存到网站目录
                        web_filename = self._download_image_to_web(img_url)
                        if web_filename:
                            # 使用网站URL引用图片
                            web_image_url = my_web_image_url+f"{web_filename}"
                            # 添加居中显示的图片
                            post.content += f'<div style="text-align: center; margin: 10px 0;">'
                            post.content += f'<img src="{web_image_url}" alt="说说图片" style="max-width: 100%; height: auto; display: inline-block;">'
                            post.content += f'</div>'
                            logging.info(f"图片已保存并引用: {web_image_url}")
                        else:
                            # 如果图片处理失败，直接使用原始URL
                            post.content += f'<div style="text-align: center; margin: 10px 0;">'
                            post.content += f'<img src="{img_url}" alt="说说图片" style="max-width: 100%; height: auto; display: inline-block;">'
                            post.content += f'</div>'
                            logging.warning(f"使用原始图片URL: {img_url}")
                        
                    except Exception as e:
                        logging.error(f"处理图片失败 {img_url}: {e}")
                        # 如果图片处理失败，直接使用原始URL
                        post.content += f'<div style="text-align: center; margin: 10px 0;">'
                        post.content += f'<img src="{img_url}" alt="说说图片" style="max-width: 100%; height: auto; display: inline-block;">'
                        post.content += f'</div>'
            
            post.post_status = 'publish'
            post.comment_status = 'open'
            
            post_id = self.wp.call(posts.NewPost(post))
            logging.info(f"WordPress说说发布成功! ID: {post_id}")
            return True
            
        except Exception as e:
            logging.error(f"WordPress说说发布失败: {e}")
            return False
    

    def publish_article(self, title: str, content: str, images: List[str] = None) -> bool:
        """
        在WordPress发布文章，图片保存到网站根目录并引用
        """
        try:
            post = WordPressPost()
            post.post_type = 'post'
            
            # 设置分类为"QQ空间"
            post.terms_names = {
                'category': ['QQ空间']
            }
            
            # 从内容中提取标题（如果没有提供标题）
            if not title:
                # 取内容的第一行作为标题
                first_line = content.split('\n')[0].strip()
                title = first_line[:50] + "..." if len(first_line) > 50 else first_line
                if not title:
                    title = f"QQ空间同步 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            post.title = title
            post.content = f"<p>{content.replace(chr(10), '<br>')}</p>"  # 保留换行
            
            # 如果有图片，下载并保存到网站目录
            if images:
                post.content += "<h3>图片</h3>"
                
                for img_url in images:
                    try:
                        # 下载图片并保存到网站目录
                        web_filename = self._download_image_to_web(img_url)
                        if web_filename:
                            # 使用网站URL引用图片
                            web_image_url = my_web_image_url+f"{web_filename}"
                            # 添加居中显示的图片
                            post.content += f'<div style="text-align: center; margin: 20px 0;">'
                            post.content += f'<img src="{web_image_url}" alt="文章图片" style="max-width: 100%; height: auto; display: inline-block;">'
                            post.content += f'</div>'
                            logging.info(f"图片已保存并引用: {web_image_url}")
                        else:
                            # 如果图片处理失败，直接使用原始URL
                            post.content += f'<div style="text-align: center; margin: 20px 0;">'
                            post.content += f'<img src="{img_url}" alt="文章图片" style="max-width: 100%; height: auto; display: inline-block;">'
                            post.content += f'</div>'
                            logging.warning(f"使用原始图片URL: {img_url}")
                        
                    except Exception as e:
                        logging.error(f"处理图片失败 {img_url}: {e}")
                        # 如果图片处理失败，直接使用原始URL
                        post.content += f'<div style="text-align: center; margin: 20px 0;">'
                        post.content += f'<img src="{img_url}" alt="文章图片" style="max-width: 100%; height: auto; display: inline-block;">'
                        post.content += f'</div>'
            
            post.post_status = 'publish'
            post.comment_status = 'open'
            
            post_id = self.wp.call(posts.NewPost(post))
            logging.info(f"WordPress文章发布成功! 标题: {title}, ID: {post_id}")
            return True
            
        except Exception as e:
            logging.error(f"WordPress文章发布失败: {e}")
            return False

    def _download_image_to_web(self, img_url: str) -> Optional[str]:
        """
        下载图片到网站根目录的qq_img文件夹
        """
        try:
            # 网站根目录的qq_img文件夹路径
            # 这里实际情需要您根据况修改为网站根目录的路径
            
            qq_img_path = os.path.join(web_root_path, "qq_img")
            
            # 创建qq_img目录（如果不存在）
            os.makedirs(qq_img_path, exist_ok=True)
            
            # 从URL提取文件名或生成唯一文件名
            parsed_url = urlparse(img_url)
            original_filename = os.path.basename(parsed_url.path)
            
            if original_filename and '.' in original_filename:
                # 使用原始文件名，但添加时间戳避免重复
                name, ext = os.path.splitext(original_filename)
                filename = f"{name}_{int(time.time())}{ext}"
            else:
                # 生成唯一文件名
                filename = f"qzone_{int(time.time())}_{hashlib.md5(img_url.encode()).hexdigest()[:8]}.jpg"
            
            local_path = os.path.join(qq_img_path, filename)
            
            # 设置请求头，模拟浏览器
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://user.qzone.qq.com/'
            }
            
            # 下载图片
            response = requests.get(img_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # 保存图片到网站目录
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            # 设置适当的文件权限（如果需要）
            os.chmod(local_path, 0o644)
            
            logging.info(f"图片已保存到网站目录: {local_path}")
            return filename
            
        except Exception as e:
            logging.error(f"图片下载到网站目录失败 {img_url}: {e}")
            return None

class QZoneCrawler:
    def __init__(self):
        self.qzone = None
        self.cookies_str = None
        self.g_tk = None
        self.qq_number = None
        self.login_state_file = 'qzone_login_state.json'
    
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
        # 先尝试从文件加载登录状态
        if self._load_login_state():
            # 验证登录状态是否仍然有效
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
            # 尝试获取一条说说来验证登录状态
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
            # 尝试直接解析JSON
            if response.strip().startswith('{') or response.strip().startswith('['):
                return json.loads(response)
            
            # 尝试解析JSONP格式 _preloadCallback({...})
            match = re.search(r'_preloadCallback\((\{.*\})\)', response)
            if match:
                return json.loads(match.group(1))
            
            # 尝试其他可能的JSONP格式
            match = re.search(r'[\w_]*\((\{.*\})\)', response)
            if match:
                return json.loads(match.group(1))
            
            # 如果都不匹配，尝试直接解析整个响应
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
        
        # 如果响应是字典，尝试提取msglist
        if isinstance(response, dict):
            # 优先尝试msglist字段
            if 'msglist' in response and isinstance(response['msglist'], list):
                messages = response['msglist']
            # 尝试其他可能的字段
            elif 'data' in response and isinstance(response['data'], list):
                messages = response['data']
            elif 'message' in response and isinstance(response['message'], list):
                messages = response['message']
            elif 'feeds' in response and isinstance(response['feeds'], list):
                messages = response['feeds']
        
        # 过滤掉空消息
        messages = [msg for msg in messages if msg]
        
        logging.info(f"从原始响应中提取到 {len(messages)} 条消息")
        return messages

    def _parse_timestamp(self, timestamp: int) -> Dict[str, Any]:
        """解析时间戳"""
        try:
            # QQ空间时间戳可能是10位或13位
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
        
        # 检查是否有pic字段
        if 'pic' in raw_msg and isinstance(raw_msg['pic'], list):
            for pic_info in raw_msg['pic']:
                if isinstance(pic_info, dict):
                    # 尝试从多个可能的URL字段中提取
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
        
        # 检查是否有images字段
        if 'images' in raw_msg and isinstance(raw_msg['images'], list):
            for img in raw_msg['images']:
                if isinstance(img, dict) and img.get('url'):
                    images.append({
                        'url': img['url'],
                        'width': img.get('width', 0),
                        'height': img.get('height', 0)
                    })
        
        # 尝试从pic_ids构建URL
        pic_ids = raw_msg.get('pic_ids', [])
        if pic_ids and isinstance(pic_ids, list):
            for pic_id in pic_ids:
                if pic_id:
                    images.append({
                        'url': f"pic_id_{pic_id}",  # 占位符
                        'id': pic_id
                    })
        
        return images

    def _clean_content_preserve_newlines(self, content: str) -> str:
        """
        清理内容但保留换行符
        """
        if not content:
            return ""
        
        # 处理QQ表情 [em]eXXX[/em]
        content = re.sub(r'\[em\]e(\d+)\[\/em\]', lambda m: f'[表情{eval(m.group(1))}]', content)
        
        # 处理@用户格式 @{uin:XXX,nick:XXX,who:1}
        content = re.sub(r'@\{uin:(\d+),nick:([^,]+),who:(\d+)\}', r'@\2', content)
        
        # 处理可能的HTML转义字符，但保留换行
        content = content.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        content = content.replace('&quot;', '"').replace('&#39;', "'")
        
        # 保留原始的换行符，不进行任何替换
        
        return content.strip()

    def _parse_raw_shuoshuo(self, raw_msg: Dict) -> Optional[Dict]:
        """
        解析原始说说数据，保留所有原始格式
        """
        try:
            if not isinstance(raw_msg, dict):
                return None
            
            # 提取基本信息
            msg_id = raw_msg.get('tid') or raw_msg.get('cur_key', '')
            uin = raw_msg.get('uin', '')
            timestamp = raw_msg.get('created_time', 0)
            
            # 获取原始内容 - 保留所有格式
            raw_content = raw_msg.get('content', '')
            
            # 从conlist中获取更详细的内容（如果有）
            conlist = raw_msg.get('conlist', [])
            if conlist and isinstance(conlist, list):
                for con_item in conlist:
                    if isinstance(con_item, dict) and con_item.get('type') == 2:  # 文本类型
                        con_content = con_item.get('con', '')
                        if con_content:
                            raw_content = con_content  # 使用conlist中的内容，通常更完整
                            break
            
            # 解析时间
            time_info = self._parse_timestamp(timestamp)
            
            # 提取图片信息
            images = self._extract_images_from_raw_msg(raw_msg)
            
            # 构建详细的说说信息，保留原始内容
            detailed_msg = {
                'id': msg_id,
                'uin': uin,
                'content': {
                    'raw': raw_content,  # 保留原始内容，包含回车
                    'parsed': self._clean_content_preserve_newlines(raw_content),  # 清理但保留换行
                    'has_media': len(images) > 0
                },
                'time': time_info,
                'media': {
                    'images': images,
                    'image_count': len(images)
                },
                'raw_data': raw_msg  # 保留完整的原始数据
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
            
            # 使用原始API方法获取未经处理的响应
            raw_response = await self.qzone._get_messages_list(
                target_qq=int(target_qq),
                g_tk=self.g_tk,
                cookies=self.cookies_str,
                num=count
            )
            
            # 解析原始响应
            parsed_response = self._parse_jsonp_response(raw_response)
            
            # 从解析后的响应中提取说说列表
            messages = self._extract_messages_from_raw_response(parsed_response)
            
            # 对每条消息进行详细解析，保留原始格式
            detailed_messages = []
            for msg in messages:
                detailed_msg = self._parse_raw_shuoshuo(msg)
                if detailed_msg:
                    detailed_messages.append(detailed_msg)
            
            return detailed_messages
            
        except Exception as e:
            logging.error(f"获取说说列表失败: {e}")
            import traceback
            logging.error(f"详细错误: {traceback.format_exc()}")
            return []

class QZoneMonitor:
    def __init__(self, wordpress_publisher: WordPressPublisher):
        self.qzone_crawler = QZoneCrawler()
        self.wp_publisher = wordpress_publisher
        self.processed_shuoshuo_ids = set()
        self.last_check_time = int(time.time())
        self.is_running = False
        
        # 加载已处理的说说ID（从文件）
        self._load_processed_ids()
    
    def _load_processed_ids(self):
        """加载已处理的说说ID"""
        try:
            with open('processed_shuoshuo.json', 'r', encoding='utf-8') as f:
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
            with open('processed_shuoshuo.json', 'w', encoding='utf-8') as f:
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
        # 只使用 #同步文章 和 #同步说说 格式
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
        # 移除同步指令
        content = re.sub(r'#同步文章\s*', '', content)
        content = re.sub(r'#同步说说\s*', '', content)
        
        # 清理QQ表情代码
        content = re.sub(r'\[em\]e\d+\[\/em\]', '', content)
        
        # 移除多余的空行
        content = re.sub(r'\n\s*\n', '\n\n', content)
        
        return content.strip()
    
    def extract_images(self, shuoshuo: Dict) -> List[str]:
        """提取图片URL"""
        images_urls = []
        
        # 从原始数据中提取图片信息
        raw_data = shuoshuo.get('raw_data', {})
        
        # 检查是否有pic字段
        if 'pic' in raw_data and isinstance(raw_data['pic'], list):
            for pic_info in raw_data['pic']:
                if isinstance(pic_info, dict):
                    # 尝试从多个可能的URL字段中提取
                    possible_url_fields = ['pic_id', 'url1', 'url2', 'url3', 'smallurl']
                    for field in possible_url_fields:
                        url = pic_info.get(field)
                        if url and isinstance(url, str) and url.startswith('http'):
                            images_urls.append(url)
                            break  # 找到一个有效的URL就跳出循环
        
        # 如果没有在pic字段中找到，尝试从media字段中提取
        if not images_urls:
            images_data = shuoshuo.get('media', {}).get('images', [])
            for img in images_data:
                url = img.get('url', '')
                if url and isinstance(url, str) and url.startswith('http'):
                    images_urls.append(url)
        
        # 去重
        return list(set(images_urls))    
    async def check_new_shuoshuo(self) -> List[Dict]:
        """检查新说说"""
        try:
            messages = await self.qzone_crawler.get_shuoshuo_list(count=20)
            new_messages = []
            
            for msg in messages:
                # 使用消息ID作为唯一标识
                msg_id = msg.get('id')
                
                if not msg_id:
                    logging.warning(f"说说缺少ID字段: {msg.get('content', {}).get('raw', '')[:50]}...")
                    continue
                
                # 检查是否是新说说且未处理过
                if msg_id not in self.processed_shuoshuo_ids:
                    new_messages.append(msg)
                    self.processed_shuoshuo_ids.add(msg_id)
                    
                    raw_content = msg.get('content', {}).get('raw', '')
                    logging.info(f"发现新说说: {msg_id}, 内容: {repr(raw_content[:100])}...")
            
            # 更新最后检查时间
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
        
        # 检查同步指令 - 使用原始内容检查
        sync_commands = self.should_sync(raw_content)
        
        if not any(sync_commands.values()):
            logging.info(f"说说不包含同步指令，跳过。内容: {repr(raw_content[:50])}...")
            return
        
        # 清理内容 - 使用解析后的内容（已保留换行）
        clean_content = self.clean_content(parsed_content)
        
        if not clean_content and not images:
            logging.info("说说内容为空且无图片，跳过")
            return
        
        logging.info(f"开始处理说说同步，指令: {sync_commands}")
        logging.info(f"清理后内容: {repr(clean_content)}")
        
        # 根据指令类型发布到WordPress
        success_count = 0
        
        if sync_commands['article']:
            # 从内容中提取标题
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
        
        # 如果同步成功，保存状态
        if success_count > 0:
            self._save_processed_ids()
    
    async def start_monitoring(self, interval: int = 60):
        """开始监控"""
        if not await self.initialize():
            logging.error("QQ空间登录失败，无法启动监控")
            return
        
        logging.info(f"开始监控QQ空间动态，检查间隔: {interval}秒")
        logging.info("同步指令说明:")
        logging.info("  - 使用 '#同步文章' 将内容发布为WordPress文章")
        logging.info("  - 使用 '#同步说说' 将内容发布为WordPress说说")
        
        self.is_running = True
        
        try:
            while self.is_running:
                try:
                    # 检查新说说
                    new_shuoshuos = await self.check_new_shuoshuo()
                    
                    if new_shuoshuos:
                        logging.info(f"发现 {len(new_shuoshuos)} 条新说说")
                        
                        # 处理每条新说说
                        for shuoshuo in new_shuoshuos:
                            await self.process_shuoshuo(shuoshuo)
                    else:
                        logging.info("未发现新说说")
                    
                    # 等待下一次检查
                    await asyncio.sleep(interval)
                    
                except Exception as e:
                    logging.error(f"监控循环出错: {e}")
                    await asyncio.sleep(interval)
                    
        except KeyboardInterrupt:
            logging.info("监控被用户中断")
        finally:
            self.is_running = False
            self._save_processed_ids()

async def test_new_shuoshuo_detection():
    """测试新说说检测功能"""
    crawler = QZoneCrawler()
    
    if await crawler.login():
        logging.info("测试新说说检测...")
        
        # 获取当前说说列表
        messages = await crawler.get_shuoshuo_list(count=10)
        if messages:
            logging.info(f"当前有 {len(messages)} 条说说")
            
            # 显示最新几条说说
            for i, msg in enumerate(messages[:3]):
                msg_id = msg.get('id')
                raw_content = msg.get('content', {}).get('raw', '')[:50]
                timestamp = msg.get('time', {}).get('timestamp', 0)
                time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') if timestamp else '未知'
                
                logging.info(f"说说 {i+1}: ID={msg_id}, 时间={time_str}, 内容={repr(raw_content)}...")
        
        # 模拟新说说检测
        monitor = QZoneMonitor(None)  # 不初始化WordPress发布器
        monitor.qzone_crawler = crawler
        new_messages = await monitor.check_new_shuoshuo()
        
        if new_messages:
            logging.info(f"检测到 {len(new_messages)} 条新说说")
        else:
            logging.info("未检测到新说说")

async def main():
    """主函数"""
    # WordPress配置
    
    
    # 先测试新说说检测
    await test_new_shuoshuo_detection()
    
    try:
        # 初始化WordPress发布器
        wp_publisher = WordPressPublisher(
            WORDPRESS_CONFIG['url'],
            WORDPRESS_CONFIG['username'],
            WORDPRESS_CONFIG['password']
        )
        logging.info("WordPress发布器初始化成功")
    except Exception as e:
        logging.error(f"WordPress发布器初始化失败: {e}")
        return
    
    # 初始化监控器
    monitor = QZoneMonitor(wp_publisher)
    
    # 开始监控（每30秒检查一次）
    await monitor.start_monitoring(interval=delay_time)

if __name__ == "__main__":
    # 运行监控
    asyncio.run(main())
