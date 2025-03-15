import requests
import json
import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 替换为您的Railway应用URL
API_URL = os.environ.get("API_URL", "https://your-railway-app-url.railway.app")

def test_check_ffmpeg():
    """测试ffmpeg安装检查端点"""
    endpoint = f"{API_URL}/check-ffmpeg"
    
    print(f"正在检查ffmpeg安装状态: {endpoint}")
    
    try:
        response = requests.get(endpoint)
        
        if response.status_code == 200:
            print("ffmpeg检查成功!")
            print(f"响应数据: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
            return response.json()
        else:
            print(f"ffmpeg检查失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
    except Exception as e:
        print(f"请求发送失败: {str(e)}")
        return None

def test_process_video(object_key):
    """测试视频处理API"""
    endpoint = f"{API_URL}/process-video"
    
    # 准备请求数据
    payload = {
        "object_key": object_key
    }
    
    print(f"正在发送请求到 {endpoint}")
    print(f"请求数据: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
    # 发送POST请求
    try:
        response = requests.post(endpoint, json=payload)
        
        # 检查响应
        if response.status_code == 200:
            print("视频处理成功!")
            print(f"响应数据: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
            return response.json()
        else:
            print(f"视频处理失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
    except Exception as e:
        print(f"请求发送失败: {str(e)}")
        return None

if __name__ == "__main__":
    print("开始测试Railway部署的API...")
    
    # 首先检查ffmpeg是否正确安装
    print("\n===== 检查ffmpeg安装 =====")
    test_check_ffmpeg()
    
    # 如果提供了命令行参数，测试视频处理API
    if len(sys.argv) == 2:
        print("\n===== 测试视频处理 =====")
        object_key = sys.argv[1]
        test_process_video(object_key)
    else:
        print("\n要测试视频处理功能，请提供S3对象键参数:")
        print("python test_video_api.py <object_key>")
        print("示例: python test_video_api.py videos/sample.mp4") 