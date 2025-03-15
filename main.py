from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import os
import subprocess
from video_processor import VideoProcessor
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/")
async def root():
    return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!"}

@app.get("/calculate/{num1}/{num2}")
async def calculate(num1: float, num2: float):
    """
    计算两个数字的加减乘除结果
    """
    return {
        "addition": num1 + num2,
        "subtraction": num1 - num2,
        "multiplication": num1 * num2,
        "division": num1 / num2 if num2 != 0 else "除数不能为零"
    }

@app.get("/check-ffmpeg")
async def check_ffmpeg():
    """
    检查ffmpeg是否正确安装
    """
    try:
        # 运行ffmpeg -version命令
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            # 提取版本信息
            version_info = result.stdout.split('\n')[0]
            return {
                "status": "success",
                "message": "ffmpeg已正确安装",
                "version": version_info
            }
        else:
            return {
                "status": "error",
                "message": "ffmpeg安装检查失败",
                "error": result.stderr
            }
    except Exception as e:
        logger.error(f"检查ffmpeg失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"检查ffmpeg失败: {str(e)}")

# 定义请求模型
class VideoRequest(BaseModel):
    object_key: str = Field(..., description="S3对象键（路径）")
    add_text: bool = Field(True, description="是否添加帧数计数器")

@app.post("/process-video")
async def process_video(request: VideoRequest):
    """
    处理S3中的视频文件
    
    1. 从S3下载视频
    2. 获取视频元数据
    3. 删除临时文件
    4. 返回元数据
    """
    try:
        # 从环境变量获取存储桶名称
        bucket_name = os.environ.get("AWS_BUCKET_NAME")
        if not bucket_name:
            raise HTTPException(status_code=500, detail="环境变量AWS_BUCKET_NAME未设置")
            
        # 获取AWS凭证（优先从环境变量获取）
        aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        region_name = os.environ.get("AWS_REGION", "us-east-1")
        
        # 初始化视频处理器
        processor = VideoProcessor(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        
        # 处理视频
        logger.info(f"开始处理视频: {bucket_name}/{request.object_key}")
        metadata = processor.process_video(bucket_name, request.object_key)
        
        return {
            "status": "success",
            "message": "视频处理成功",
            "metadata": metadata
        }
    except Exception as e:
        logger.error(f"视频处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"视频处理失败: {str(e)}")

@app.post("/create-proxy")
async def create_proxy(request: VideoRequest):
    """
    为S3中的视频创建代理文件（720p 30fps带帧数计数器）
    
    1. 从S3下载视频
    2. 创建720p 30fps的代理文件，并添加帧数计数器
    3. 上传代理文件到S3
    4. 返回原始文件和代理文件的信息
    """
    try:
        # 从环境变量获取存储桶名称
        bucket_name = os.environ.get("AWS_BUCKET_NAME")
        if not bucket_name:
            raise HTTPException(status_code=500, detail="环境变量AWS_BUCKET_NAME未设置")
            
        # 获取AWS凭证
        aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        region_name = os.environ.get("AWS_REGION", "us-east-1")
        
        # 初始化视频处理器
        processor = VideoProcessor(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        
        # 处理视频并创建代理文件
        logger.info(f"开始创建代理文件: {bucket_name}/{request.object_key}")
        result = processor.process_and_upload_proxy(bucket_name, request.object_key, add_text=request.add_text)
        
        return {
            "status": "success",
            "message": "代理文件创建成功",
            "data": result
        }
    except Exception as e:
        logger.error(f"创建代理文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建代理文件失败: {str(e)}")
