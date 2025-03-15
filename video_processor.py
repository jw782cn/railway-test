import os
import boto3
import tempfile
import uuid
from botocore.exceptions import ClientError
import ffmpeg
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None, region_name=None):
        """
        初始化S3客户端
        如果不提供凭证，将使用环境变量或IAM角色
        """
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        self.temp_dir = tempfile.gettempdir()
    
    def download_video(self, bucket_name, object_key):
        """
        从S3下载视频文件到临时目录
        
        Args:
            bucket_name (str): S3存储桶名称
            object_key (str): S3对象键（路径）
            
        Returns:
            str: 临时文件的路径
        """
        # 生成唯一的临时文件名
        file_extension = os.path.splitext(object_key)[1]
        temp_file_path = os.path.join(self.temp_dir, f"{uuid.uuid4()}{file_extension}")
        
        try:
            logger.info(f"开始从S3下载: {bucket_name}/{object_key}")
            self.s3_client.download_file(bucket_name, object_key, temp_file_path)
            logger.info(f"下载完成，临时文件: {temp_file_path}")
            return temp_file_path
        except ClientError as e:
            logger.error(f"下载S3文件失败: {e}")
            raise Exception(f"无法从S3下载文件: {e}")
    
    def get_video_metadata(self, file_path):
        """
        使用ffmpeg获取视频元数据
        
        Args:
            file_path (str): 视频文件路径
            
        Returns:
            dict: 视频元数据
        """
        try:
            logger.info(f"开始获取视频元数据: {file_path}")
            probe = ffmpeg.probe(file_path)
            
            # 提取关键元数据
            metadata = {
                "format": probe["format"]["format_name"],
                "duration": float(probe["format"]["duration"]),
                "size": int(probe["format"]["size"]),
                "bit_rate": int(probe["format"]["bit_rate"]) if "bit_rate" in probe["format"] else None,
            }
            
            # 提取视频流信息
            video_streams = [stream for stream in probe["streams"] if stream["codec_type"] == "video"]
            if video_streams:
                video_stream = video_streams[0]
                metadata["video"] = {
                    "codec": video_stream["codec_name"],
                    "width": video_stream["width"],
                    "height": video_stream["height"],
                    "fps": eval(video_stream["avg_frame_rate"]) if "avg_frame_rate" in video_stream else None,
                }
            
            # 提取音频流信息
            audio_streams = [stream for stream in probe["streams"] if stream["codec_type"] == "audio"]
            if audio_streams:
                audio_stream = audio_streams[0]
                metadata["audio"] = {
                    "codec": audio_stream["codec_name"],
                    "channels": audio_stream["channels"],
                    "sample_rate": int(audio_stream["sample_rate"]) if "sample_rate" in audio_stream else None,
                }
            
            logger.info("元数据获取成功")
            return metadata
        except Exception as e:
            logger.error(f"获取视频元数据失败: {e}")
            raise Exception(f"无法获取视频元数据: {e}")
    
    def cleanup_temp_file(self, file_path):
        """
        删除临时文件
        
        Args:
            file_path (str): 要删除的文件路径
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"临时文件已删除: {file_path}")
        except Exception as e:
            logger.error(f"删除临时文件失败: {e}")
    
    def process_video(self, bucket_name, object_key):
        """
        处理视频的主函数：下载、获取元数据、清理
        
        Args:
            bucket_name (str): S3存储桶名称
            object_key (str): S3对象键（路径）
            
        Returns:
            dict: 视频元数据
        """
        temp_file_path = None
        try:
            # 下载视频
            temp_file_path = self.download_video(bucket_name, object_key)
            
            # 获取元数据
            metadata = self.get_video_metadata(temp_file_path)
            
            # 添加源信息
            metadata["source"] = {
                "bucket": bucket_name,
                "key": object_key
            }
            
            return metadata
        finally:
            # 无论成功与否，都清理临时文件
            if temp_file_path:
                self.cleanup_temp_file(temp_file_path) 