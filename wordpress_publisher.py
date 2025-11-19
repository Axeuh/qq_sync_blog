"""
WordPress发布器模块
"""

import os
import time
import logging
import hashlib
import requests
from urllib.parse import urlparse
from typing import List, Optional
from datetime import datetime
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods import posts
from wordpress_xmlrpc.methods.media import UploadFile
from wordpress_xmlrpc.compat import xmlrpc_client

from config import WORDPRESS_CONFIG, WEB_CONFIG


class WordPressPublisher:
    def __init__(self, url: str = None, username: str = None, password: str = None):
        config = WORDPRESS_CONFIG
        self.wp = Client(
            url or config['url'],
            username or config['username'],
            password or config['password']
        )
        self.url = url or config['url']
        self.username = username or config['username']
    
    def publish_shuoshuo(self, content: str, images: List[str] = None) -> bool:
        """
        在WordPress发布说说，图片保存到网站根目录并引用
        """
        try:
            post = WordPressPost()
            post.post_type = 'shuoshuo'
            
            post.title = f"说说 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            post.content = f"<p>{content.replace(chr(10), '<br>')}</p>"  # 保留换行
            
            # 如果有图片，下载并保存到网站目录
            if images:
                for img_url in images[:3]:  # 限制图片数量
                    try:
                        web_filename = self._download_image_to_web(img_url)
                        if web_filename:
                            web_image_url = WEB_CONFIG['image_url'] + f"{web_filename}"
                            post.content += f'<div style="text-align: center; margin: 10px 0;">'
                            post.content += f'<img src="{web_image_url}" alt="说说图片" style="max-width: 100%; height: auto; display: inline-block;">'
                            post.content += f'</div>'
                            logging.info(f"图片已保存并引用: {web_image_url}")
                        else:
                            post.content += f'<div style="text-align: center; margin: 10px 0;">'
                            post.content += f'<img src="{img_url}" alt="说说图片" style="max-width: 100%; height: auto; display: inline-block;">'
                            post.content += f'</div>'
                            logging.warning(f"使用原始图片URL: {img_url}")
                        
                    except Exception as e:
                        logging.error(f"处理图片失败 {img_url}: {e}")
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
                        web_filename = self._download_image_to_web(img_url)
                        if web_filename:
                            web_image_url = WEB_CONFIG['image_url'] + f"{web_filename}"
                            post.content += f'<div style="text-align: center; margin: 20px 0;">'
                            post.content += f'<img src="{web_image_url}" alt="文章图片" style="max-width: 100%; height: auto; display: inline-block;">'
                            post.content += f'</div>'
                            logging.info(f"图片已保存并引用: {web_image_url}")
                        else:
                            post.content += f'<div style="text-align: center; margin: 20px 0;">'
                            post.content += f'<img src="{img_url}" alt="文章图片" style="max-width: 100%; height: auto; display: inline-block;">'
                            post.content += f'</div>'
                            logging.warning(f"使用原始图片URL: {img_url}")
                        
                    except Exception as e:
                        logging.error(f"处理图片失败 {img_url}: {e}")
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
        下载图片到网站根目录的qq_msg文件夹
        """
        try:
            qq_msg_path = os.path.join(WEB_CONFIG['root_path'], "qq_msg")
            os.makedirs(qq_msg_path, exist_ok=True)
            
            parsed_url = urlparse(img_url)
            original_filename = os.path.basename(parsed_url.path)
            
            if original_filename and '.' in original_filename:
                name, ext = os.path.splitext(original_filename)
                filename = f"{name}_{int(time.time())}{ext}"
            else:
                filename = f"qzone_{int(time.time())}_{hashlib.md5(img_url.encode()).hexdigest()[:8]}.jpg"
            
            local_path = os.path.join(qq_msg_path, filename)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://user.qzone.qq.com/'
            }
            
            response = requests.get(img_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            os.chmod(local_path, 0o644)
            
            logging.info(f"图片已保存到网站目录: {local_path}")
            return filename
            
        except Exception as e:
            logging.error(f"图片下载到网站目录失败 {img_url}: {e}")
            return None
