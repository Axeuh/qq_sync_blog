"""
配置文件
"""

# WordPress配置
WORDPRESS_CONFIG = {
    'url': "https://www.axeuh.com/xmlrpc.php",
    'username': "2176284372@qq.com",
    'password': "hc18052741602"
}

# 网站配置
WEB_CONFIG = {
    'image_url': "https://www.axeuh.com/qq_msg/",
    'root_path': "/www/wwwroot/www.axeuh.com"
}

# 监控配置
MONITOR_CONFIG = {
    'delay_time': 600,  # 检查间隔（秒）
    'login_state_file': 'qzone_login_state.json',
    'processed_ids_file': 'processed_shuoshuo.json'
}

# 日志配置
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(levelname)s - %(message)s',
    'filename': 'qzone_monitor.log'
}
