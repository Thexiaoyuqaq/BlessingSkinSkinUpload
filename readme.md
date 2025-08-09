# BlessingSkin皮肤上传 API

一个基于 PHP 的自实现内部皮肤批量上传API

## 功能特性

- **多文件支持**：同时支持单文件和多文件批量上传
- **重复检测**：防止上传相同哈希值的重复文件
- **完整验证**：MIME 类型验证确保文件真实性

## 环境要求

- PHP 7.4 或更高版本
- MySQL 5.7 或更高版本
- PHP 扩展：PDO、fileinfo、hash
- 服务器写入权限

## 项目结构

```
your-project/
├── public/                     # Web 根目录
│   └── skinapi.php         # 上传API脚本（必须放在此处）（脚本名没有要求）
└── storage/                   # 存储目录
    └── textures/              # 皮肤文件存储目录
```

**重要说明**：`skinapi.php` 必须放在 `public` 目录中，脚本使用相对路径 `../storage/textures/` 访问存储目录。

## 安装配置

### 1. 配置文件

修改脚本中的配置常量（必须根据实际环境修改）：

```php
// 上传者ID（根据实际情况修改）
const UPLOADER_ID = 1;

// 上传目录路径（相对于public目录）
const UPLOAD_DIR = '../storage/textures/';

// 文件大小限制（5MB）
const MAX_FILE_SIZE = 5 * 1024 * 1024;

// 数据库连接信息（请根据实际环境修改）
const DB_HOST = 'your-mysql-host';
const DB_USER = 'your-username';
const DB_PASS = 'your-password';
const DB_NAME = 'your-database';
```

## 使用方法

### API 端点

```
POST /skinapi.php
```

### 请求参数

- **字段名称**：`images`
- **文件格式**：`.png`
- **命名规范**：`{皮肤名}_{alex|steve}.png`

### 单文件上传

HTML 表单示例：

```html
<form action="skinapi.php" method="post" enctype="multipart/form-data">
    <input type="file" name="images" accept=".png" required>
    <button type="submit">上传皮肤</button>
</form>
```

### 多文件上传

HTML 表单示例：

```html
<form action="skinapi.php" method="post" enctype="multipart/form-data">
    <input type="file" name="images[]" accept=".png" multiple required>
    <button type="submit">批量上传</button>
</form>
```

### JavaScript 上传

```javascript
const formData = new FormData();
formData.append('images', file); // 单文件
// 或
formData.append('images[]', file1); // 多文件
formData.append('images[]', file2);

fetch('skinapi.php', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

## 文件命名规范

### 支持的格式

```
player123_steve.png     ✓ 正确
custom_skin_alex.png    ✓ 正确
my_skin_steve.png       ✓ 正确
invalid_name.png        ✗ 错误（缺少类型）
skin_john.png           ✗ 错误（类型不正确）
```

### 提取规则

- **皮肤名称**：下划线前的所有内容
- **皮肤类型**：`alex` 或 `steve`（不区分大小写）

示例：
- `custom_player_alex.png` → 名称：`custom_player`，类型：`alex`
- `zombie_steve.png` → 名称：`zombie`，类型：`steve`

## API 响应

### 成功响应

```json
{
    "success": true,
    "message": "处理完成：成功 2/2 个文件",
    "data": {
        "total": 2,
        "success": 2,
        "failed": 0,
        "results": [
            {
                "success": true,
                "filename": "player_steve.png",
                "tid": 123,
                "hash": "a1b2c3d4e5f6...",
                "name": "player",
                "type": "steve",
                "size": 2
            }
        ]
    }
}
```

### 错误响应

```json
{
    "success": false,
    "message": "处理完成：成功 0/1 个文件",
    "data": {
        "total": 1,
        "success": 0,
        "failed": 1,
        "results": [
            {
                "success": false,
                "filename": "invalid.png",
                "error": "文件名格式不正确，应为: name_alex.png 或 name_steve.png"
            }
        ]
    }
}
```

## 错误处理

### 常见错误类型

1. **文件格式错误**
   - 非 PNG 格式文件
   - MIME 类型验证失败

2. **文件名错误**
   - 命名格式不符合规范
   - 缺少皮肤类型标识

3. **文件大小错误**
   - 超过 5MB 限制
   - 空文件

4. **系统错误**
   - 数据库连接失败
   - 文件保存失败
   - 权限不足

### 错误代码对照

| HTTP状态码 | 错误信息 | 解决方案 |
|-----------|----------|----------|
| 400 | 只支持POST请求 | 使用 POST 方法 |
| 400 | 没有上传任何文件 | 检查表单字段名 |
| 500 | 数据库连接失败 | 检查数据库配置 |
| 413 | 文件大小超出限制 | 压缩文件或修改限制 |

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## 支持

如遇到问题或需要帮助：

- 提交 GitHub Issue
