# QQ空间到WordPress同步工具

一个自动监控QQ空间动态并将其同步到WordPress网站的工具。支持通过特定标签指令控制同步内容到WordPress文章或说说。

## 效果预览

<table> <tr> <td align="center"><strong>发送说说</strong></td> <td align="center"><strong>同步效果</strong></td> </tr> <tr> <td><img src="https://github.com/Axeuh/qq_sync_blog/blob/main/6f23def5a74a92958111f672c0c42a5c.png?raw=true" alt="登录界面" width="100%"></td> <td><img src="https://github.com/Axeuh/qq_sync_blog/blob/main/0de57e8dc6d6ed7ed9702f84fa1f4488.png?raw=true" alt="同步效果" width="100%"></td> </tr> </table>

## 功能特点

- 🔄 **自动监控**：定时检查QQ空间新动态
- 🏷️ **智能同步**：通过`#同步文章`和`#同步说说`标签控制同步
- 🖼️ **图片处理**：自动下载QQ空间图片到网站目录并引用
- 💾 **状态持久化**：保存登录状态和已处理记录
- 🚀 **服务化部署**：支持系统服务部署和开机自启动

## 文件结构

```
.
├── install.sh          # 依赖安装脚本
├── main.py            # 主程序文件
├── requirements.txt   # Python依赖包
├── setup.sh          # 系统服务配置脚本
└── processed_shuoshuo.json # 运行状态记录（自动生成）
```

## 安装步骤

### 1. 配置参数

在 `main.py` 文件中修改以下配置：

```python
# WordPress配置
WORDPRESS_CONFIG = {
    'url': "https://您的网站.com/xmlrpc.php",
    'username': "您的用户名",
    'password': "您的密码"
}

# 网站配置
my_web_image_url = "https://您的网站.com/qq_img/"
web_root_path = "/www/wwwroot/您的网站.com"
delay_time = 30  # 检查间隔（秒）
```

### 2. 安装依赖

```bash
# 给安装脚本执行权限
chmod +x install.sh

# 运行安装脚本
./install.sh
```

### 3. 配置系统服务

```bash
# 给设置脚本执行权限
chmod +x setup.sh

# 运行设置脚本
./setup.sh
```

## 使用方法

### 指令说明

在QQ空间动态中使用以下标签来控制同步：

- **`#同步文章`** - 将内容发布为WordPress文章
- **`#同步说说`** - 将内容发布为WordPress说说

### 手动运行

```bash
# 直接运行主程序
python3 main.py

# 或使用系统服务管理
sudo systemctl start qq_blog    # 启动
sudo systemctl stop qq_blog     # 停止
sudo systemctl restart qq_blog  # 重启
```

### 服务管理命令

```bash
# 查看服务状态
sudo systemctl status qq_blog

# 查看实时日志
sudo journalctl -u qq_blog -f

# 查看最近日志
sudo journalctl -u qq_blog --lines=50
```

## 配置说明

### WordPress分类

所有同步内容会自动归类到"QQ空间"分类，确保WordPress中已创建此分类。

### 图片存储

- 图片自动保存到网站根目录的 `qq_img` 文件夹
- 支持自动重命名避免冲突
- 保持原始图片质量

### 登录状态

- 登录状态自动保存到 `qzone_login_state.json`
- 24小时内有效，过期自动重新登录
- 支持扫码登录和账号密码登录

## 注意事项

1. **首次运行**：首次运行会要求QQ空间登录，支持扫码登录
2. **权限要求**：确保有权限在网站根目录创建 `qq_img` 文件夹
3. **网络要求**：服务器需要能访问QQ空间和您的WordPress网站
4. **安全考虑**：建议使用专门的WordPress账户，权限设置为作者即可
5. 更换账号：删除 `qzone_login_state.json` 文件重启服务再扫描登录即可

## 故障排除

### 常见问题

1. **登录失败**
   
   - 检查网络连接
   - 确认QQ账号密码正确
   - 尝试重新运行程序重新登录
2. **图片同步失败**
   
   - 检查网站目录权限
   - 确认 `web_root_path` 配置正确
   - 检查磁盘空间
3. **WordPress发布失败**
   
   - 检查XML-RPC是否启用
   - 确认用户名密码正确
   - 检查用户发布权限

### 查看日志

```bash
# 查看详细日志
tail -f qzone_monitor.log

# 查看系统服务日志
sudo journalctl -u qq_blog -f
```

## 更新维护

如需更新程序，只需替换文件后重启服务：

```bash
sudo systemctl restart qq_blog
```
