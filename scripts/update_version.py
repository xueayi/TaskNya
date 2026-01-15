import re
import sys
import os

def update_version(file_path, new_version):
    """
    更新文件中符合 'vX.Y.Z' 格式的版本号。
    符合 TaskNya 开发指南：轻量级、职责单一、错误处理明确。
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found - {file_path}")
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 匹配 '通用任务监控工具 vX.Y.Z' 中的版本号部分
        pattern = r'(通用任务监控工具 v)\d+\.\d+\.\d+'
        replacement = rf'\g<1>{new_version}'
        
        new_content, count = re.subn(pattern, replacement, content)

        if count > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Successfully updated {file_path} to version {new_version} ({count} replacements)")
            return True
        else:
            print(f"Warning: No version string found in {file_path} matching the pattern.")
            return False

    except Exception as e:
        print(f"Error updating file: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_version.py <version>")
        sys.exit(1)

    # 规范化版本号：去除可能存在的 'v' 前缀
    target_version = sys.argv[1]
    if target_version.startswith('v'):
        target_version = target_version[1:]

    # 定义需要更新的文件列表（目前仅 index.html）
    # 路径使用相对于项目根目录的相对路径
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files_to_update = [
        os.path.join(base_dir, 'app', 'templates', 'index.html'),
    ]

    success = True
    for file in files_to_update:
        if not update_version(file, target_version):
            success = False
    
    if not success:
        sys.exit(1)
