from fastapi import HTTPException
from typing import List, Dict
import io
import zipfile
import rarfile
import py7zr
import tarfile

def hw_file2text(file): #TODO: file to text with OCR, or process with AI directly
    pass #这个感觉需要lang graph就是需要一个ai对直接读取+OCR和AI直接识别的综合

def decode_text_bytes(text_bytes: bytes) -> str:
    """尝试以多种编码解码字节，失败则抛出HTTPException。"""
    try:
        return text_bytes.decode('utf-8')
    except UnicodeDecodeError:
        try:
            return text_bytes.decode('gbk')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="无法解码文件，请确保文件是 UTF-8 或 GBK 编码。")

# --- 主函数：处理上传的文件 ---
def extract_files_from_archive(file_bytes: bytes, filename: str) -> List[Dict[str, str]]:
    """
    处理一个以字节形式存在的上传文件（可能是压缩包或单个文本文件），
    提取其中所有文本文件的文件名和内容。

    Args:
        file_bytes: 文件内容的原始字节流。
        filename: 上传文件的原始名称，用于判断文件类型。

    Returns:
        一个字典列表，每个字典代表一个文件，格式为:
        [{"filename": "学号_姓名.txt", "content": "文件内容..."}, ...]
    
    Raises:
        ValueError: 如果 rarfile 或 py7zr 库未安装但尝试处理相应文件类型。
        Exception: 传递来自底层库的其他异常。
    """
    files_data: List[Dict[str, str]] = []
    file_in_memory = io.BytesIO(file_bytes)
    
    # 过滤掉常见的系统生成垃圾文件
    def is_valid_file(name: str) -> bool:
        return not (name.startswith('__MACOSX') or '.DS_Store' in name)

    # 1. 处理 .zip 文件
    if filename.lower().endswith('.zip'):
        with zipfile.ZipFile(file_in_memory, 'r') as zf:
            for info in zf.infolist():
                # 确保是文件而不是目录，并且是有效文件
                if not info.is_dir() and is_valid_file(info.filename):
                    # 从压缩文件名中提取纯文件名，避免路径问题
                    clean_filename = info.filename.split('/')[-1]
                    content_bytes = zf.read(info.filename)
                    files_data.append({
                        "filename": clean_filename,
                        "content": decode_text_bytes(content_bytes)
                    })

    # 2. 处理 .rar 文件
    elif filename.lower().endswith('.rar'):
        if not rarfile:
            raise ValueError("处理 .rar 文件需要 'rarfile' 库，请运行 'pip install rarfile'")
        # rarfile 可能会因缺少 unrar 工具而抛出异常
        try:
            with rarfile.RarFile(file_in_memory, 'r') as rf:
                for info in rf.infolist():
                    if not info.is_dir() and is_valid_file(info.filename):
                        clean_filename = info.filename.split('/')[-1]
                        content_bytes = rf.read(info.filename)
                        files_data.append({
                            "filename": clean_filename,
                            "content": decode_text_bytes(content_bytes)
                        })
        except rarfile.UNRARError as e:
            # 这是一个常见的服务器配置问题，提供明确的错误信息
            raise RuntimeError(f"处理RAR文件失败: {e}. 请确保服务器上已安装 'unrar' 命令行工具。")

    # 3. 处理 .7z 文件
    elif filename.lower().endswith('.7z'):
        if not py7zr:
            raise ValueError("处理 .7z 文件需要 'py7zr' 库，请运行 'pip install py7zr'")
        with py7zr.SevenZipFile(file_in_memory, 'r') as szf:
            # readall() 返回一个 {filename: BytesIO_object} 的字典
            all_files = szf.readall()
            for name, bio in all_files.items():
                if is_valid_file(name):
                    clean_filename = name.split('/')[-1]
                    content_bytes = bio.read()
                    files_data.append({
                        "filename": clean_filename,
                        "content": decode_text_bytes(content_bytes)
                    })

    # 4. 处理 .tar.* 系列文件
    elif filename.lower().endswith(('.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tbz2')):
        # 'r:*' 模式可以自动检测 tar 的压缩类型 (gz, bz2, etc.)
        with tarfile.open(fileobj=file_in_memory, mode='r:*') as tf:
            for member in tf.getmembers():
                # 确保是文件而不是目录
                if member.isfile() and is_valid_file(member.name):
                    clean_filename = member.name.split('/')[-1]
                    # 提取文件对象并读取内容
                    file_obj = tf.extractfile(member)
                    if file_obj:
                        content_bytes = file_obj.read()
                        files_data.append({
                            "filename": clean_filename,
                            "content": decode_text_bytes(content_bytes)
                        })

    # 5. 如果不是已知的压缩包，则作为单个文件处理
    else:
        # 假设上传的单个文件也是 txt 文件
        if filename.lower().endswith('.txt'): # TODO: 很重要的代码类文件，.doc, .docx, .pdf, .md
             files_data.append({
                "filename": filename,
                "content": decode_text_bytes(file_bytes)
            })
        else:
            # 对于非txt的单个文件，可以返回空或抛出异常，这里选择忽略
            print(f"忽略不支持的单个文件类型: {filename}")

    return files_data