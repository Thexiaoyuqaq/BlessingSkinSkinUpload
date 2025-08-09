<?php
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

const UPLOADER_ID = 1;
const UPLOAD_DIR = '../storage/textures/';
const MAX_FILE_SIZE = 5 * 1024 * 1024;

const DB_HOST = 'your-mysql-host';
const DB_USER = 'your-username';
const DB_PASS = 'your-password';
const DB_NAME = 'your-database';

function jsonResponse($success, $message, $data = null) {
    echo json_encode([
        'success' => $success,
        'message' => $message,
        'data' => $data
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

function connectDatabase() {
    try {
        $pdo = new PDO(
            "mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=utf8mb4",
            DB_USER,
            DB_PASS,
            [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
            ]
        );
        return $pdo;
    } catch (PDOException $e) {
        jsonResponse(false, '数据库连接失败: ' . $e->getMessage());
    }
}

function generateHash($filePath) {
    return hash('sha256', file_get_contents($filePath));
}

function parseFileName($fileName) {
    $nameWithoutExt = pathinfo($fileName, PATHINFO_FILENAME);
    if (preg_match('/^(.+)_(alex|steve)$/i', $nameWithoutExt, $matches)) {
        return [
            'name' => $matches[1],
            'type' => strtolower($matches[2])
        ];
    }
    return false;
}

function validateFile($file) {
    if ($file['error'] !== UPLOAD_ERR_OK) {
        return '文件上传失败，错误码: ' . $file['error'];
    }
    
    if ($file['size'] > MAX_FILE_SIZE) {
        return '文件大小超出限制(5MB)';
    }
    
    $fileExt = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
    if ($fileExt !== 'png') {
        return '只支持PNG格式的图片文件';
    }
    
    $finfo = finfo_open(FILEINFO_MIME_TYPE);
    $mimeType = finfo_file($finfo, $file['tmp_name']);
    finfo_close($finfo);
    
    if ($mimeType !== 'image/png') {
        return '文件不是有效的PNG图片';
    }
    
    $parsed = parseFileName($file['name']);
    if (!$parsed) {
        return '文件名格式不正确，应为: name_alex.png 或 name_steve.png';
    }
    
    return true;
}

function processFile($file, $pdo) {
    $validation = validateFile($file);
    if ($validation !== true) {
        return [
            'success' => false,
            'filename' => $file['name'],
            'error' => $validation
        ];
    }
    
    $parsed = parseFileName($file['name']);
    $skinName = $parsed['name'];
    $skinType = $parsed['type'];
    
    $hash = generateHash($file['tmp_name']);
    
    if (!is_dir(UPLOAD_DIR)) {
        $created = mkdir(UPLOAD_DIR, 0755, true);
        if (!$created) {
            $error = error_get_last();
            return [
                'success' => false,
                'filename' => $file['name'],
                'error' => '无法创建上传目录: ' . UPLOAD_DIR . ' - ' . ($error ? $error['message'] : '权限不足')
            ];
        }
    }
    
    if (!is_writable(UPLOAD_DIR)) {
        return [
            'success' => false,
            'filename' => $file['name'],
            'error' => '上传目录不可写: ' . UPLOAD_DIR . ' - 当前权限: ' . substr(sprintf('%o', fileperms(UPLOAD_DIR)), -4)
        ];
    }
    
    $targetPath = UPLOAD_DIR . $hash;
    if (!move_uploaded_file($file['tmp_name'], $targetPath)) {
        return [
            'success' => false,
            'filename' => $file['name'],
            'error' => '文件保存失败'
        ];
    }
    
    $sizeKB = intval($file['size'] / 1024);
    if ($sizeKB === 0) $sizeKB = 1;
    
    try {
        $checkStmt = $pdo->prepare("SELECT tid FROM textures WHERE hash = ?");
        $checkStmt->execute([$hash]);
        
        if ($checkStmt->rowCount() > 0) {
            unlink($targetPath);
            return [
                'success' => false,
                'filename' => $file['name'],
                'error' => '相同的文件已经存在'
            ];
        }
        
        $stmt = $pdo->prepare("
            INSERT INTO textures (name, type, hash, size, uploader, public, upload_at, likes) 
            VALUES (?, ?, ?, ?, ?, 1, NOW(), 0)
        ");
        
        $stmt->execute([
            $skinName,
            $skinType,
            $hash,
            $sizeKB,
            UPLOADER_ID
        ]);
        
        return [
            'success' => true,
            'filename' => $file['name'],
            'tid' => $pdo->lastInsertId(),
            'hash' => $hash,
            'name' => $skinName,
            'type' => $skinType,
            'size' => $sizeKB
        ];
        
    } catch (PDOException $e) {
        if (file_exists($targetPath)) {
            unlink($targetPath);
        }
        
        return [
            'success' => false,
            'filename' => $file['name'],
            'error' => '数据库错误: ' . $e->getMessage()
        ];
    }
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    jsonResponse(false, '只支持POST请求');
}

if (empty($_FILES) || !isset($_FILES['images'])) {
    jsonResponse(false, '没有上传任何文件，请使用字段名 "images"');
}

$pdo = connectDatabase();

$results = [];
$successCount = 0;

$files = $_FILES['images'];

if (is_array($files['name'])) {
    $fileCount = count($files['name']);
    
    for ($i = 0; $i < $fileCount; $i++) {
        $file = [
            'name' => $files['name'][$i],
            'type' => $files['type'][$i],
            'tmp_name' => $files['tmp_name'][$i],
            'error' => $files['error'][$i],
            'size' => $files['size'][$i]
        ];
        
        $result = processFile($file, $pdo);
        $results[] = $result;
        
        if ($result['success']) {
            $successCount++;
        }
    }
} else {
    $result = processFile($files, $pdo);
    $results[] = $result;
    
    if ($result['success']) {
        $successCount++;
    }
}

$totalFiles = count($results);
$message = "处理完成：成功 {$successCount}/{$totalFiles} 个文件";

jsonResponse(
    $successCount > 0,
    $message,
    [
        'total' => $totalFiles,
        'success' => $successCount,
        'failed' => $totalFiles - $successCount,
        'results' => $results
    ]
);
?>
