import requests
import json
import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 替换为您的Railway应用URL
API_URL = os.environ.get("API_URL", "https://your-railway-app-url.railway.app")

def test_create_proxy(object_key, add_text=True):
    """测试代理视频创建API"""
    endpoint = f"{API_URL}/create-proxy"
    
    # 准备请求数据
    payload = {
        "object_key": object_key,
        "add_text": add_text
    }
    
    print(f"正在发送请求到 {endpoint}")
    print(f"请求数据: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
    # 发送POST请求
    try:
        response = requests.post(endpoint, json=payload)
        
        # 检查响应
        if response.status_code == 200:
            result = response.json()
            print("\n代理视频创建成功!")
            print("\n处理时间统计:")
            times = result["data"]["processing_times"]
            print(f"下载时间: {times['download']}秒")
            print(f"处理时间: {times['process']}秒")
            print(f"上传时间: {times['upload']}秒")
            print(f"总时间: {times['total']}秒")
            print("\n文件信息:")
            print(f"原始文件: {result['data']['original']['bucket']}/{result['data']['original']['key']}")
            print(f"代理文件: {result['data']['proxy']['bucket']}/{result['data']['proxy']['key']}")
            return result
        else:
            print(f"代理视频创建失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
    except Exception as e:
        print(f"请求发送失败: {str(e)}")
        return None

def test_proxy_endpoint(object_key):
    """测试代理端点"""
    endpoint = f"{API_URL}/test-proxy/{object_key}"
    
    print(f"正在测试代理端点: {endpoint}")
    
    try:
        response = requests.get(endpoint)
        
        if response.status_code == 200:
            print("代理端点测试成功!")
            print(f"响应数据: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
            return response.json()
        else:
            print(f"代理端点测试失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
    except Exception as e:
        print(f"请求发送失败: {str(e)}")
        return None

if __name__ == "__main__":
    print("开始测试代理视频创建功能...")
    
    # 如果提供了命令行参数，测试代理视频创建
    if len(sys.argv) == 2:
        print("\n===== 测试代理视频创建 =====")
        object_key = sys.argv[1]
        add_text = sys.argv[2] if len(sys.argv) > 2 else False
        
        # 测试直接创建代理
        print("\n1. 测试直接创建代理")
        result = test_create_proxy(object_key, add_text=add_text)
        
        if result:
            # 测试代理端点
            print("\n2. 测试代理端点")
            test_proxy_endpoint(object_key)
    else:
        print("\n要测试代理视频创建功能，请提供S3对象键参数:")
        print("python test_proxy.py <object_key>")
        print("示例: python test_proxy.py videos/sample.mp4") 