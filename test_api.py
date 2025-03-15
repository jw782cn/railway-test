import requests
import sys

# 替换为您的Railway应用URL
# 部署后，您可以通过 railway domain 命令获取
API_URL = "https://sophisticated-galley-production.up.railway.app"  # 请替换为实际URL

def test_root_endpoint():
    """测试根路径端点"""
    response = requests.get(f"{API_URL}/")
    if response.status_code == 200:
        print("根路径测试成功!")
        print(f"响应数据: {response.json()}")
    else:
        print(f"根路径测试失败，状态码: {response.status_code}")
        print(f"错误信息: {response.text}")

def test_calculate_endpoint(num1, num2):
    """测试计算端点"""
    response = requests.get(f"{API_URL}/calculate/{num1}/{num2}")
    if response.status_code == 200:
        print(f"计算测试成功! 参数: {num1}, {num2}")
        print(f"响应数据: {response.json()}")
    else:
        print(f"计算测试失败，状态码: {response.status_code}")
        print(f"错误信息: {response.text}")

if __name__ == "__main__":
    print("开始测试Railway部署的API...")
    
    # 测试根路径
    test_root_endpoint()
    
    # 测试计算功能
    test_calculate_endpoint(10, 5)
    test_calculate_endpoint(3.5, 2.5)
    test_calculate_endpoint(7, 0)  # 测试除以零的情况
    
    # 如果命令行提供了参数，也用它们测试
    if len(sys.argv) == 3:
        try:
            num1 = float(sys.argv[1])
            num2 = float(sys.argv[2])
            test_calculate_endpoint(num1, num2)
        except ValueError:
            print("命令行参数必须是数字") 