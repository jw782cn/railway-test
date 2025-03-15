import os
import boto3
import tempfile
import uuid
from botocore.exceptions import ClientError
import ffmpeg
import logging
import time
import requests
import subprocess

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoProcessor:
    def __init__(
        self, aws_access_key_id=None, aws_secret_access_key=None, region_name=None
    ):
        """
        初始化S3客户端
        如果不提供凭证，将使用环境变量或IAM角色
        """
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )
        self.temp_dir = tempfile.gettempdir()
        self.font_path = self._ensure_font()

    def _ensure_font(self):
        """
        确保字体文件存在，如果不存在则下载
        """
        # 字体文件路径
        font_path = os.path.join(self.temp_dir, "NotoSans-Regular.ttf")

        # 如果字体文件不存在，则下载
        if not os.path.exists(font_path):
            try:
                logger.info("正在下载字体文件...")
                # Noto Sans Regular 字体的 Google Fonts 下载链接
                font_url = "https://fonts.google.com/download?family=Noto%20Sans"
                response = requests.get(font_url)
                with open(font_path, "wb") as f:
                    f.write(response.content)
                logger.info(f"字体文件已下载到: {font_path}")
            except Exception as e:
                logger.error(f"下载字体文件失败: {e}")
                # 如果下载失败，使用系统默认字体
                font_path = None

        return font_path

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
                "bit_rate": int(probe["format"]["bit_rate"])
                if "bit_rate" in probe["format"]
                else None,
            }

            # 提取视频流信息
            video_streams = [
                stream for stream in probe["streams"] if stream["codec_type"] == "video"
            ]
            if video_streams:
                video_stream = video_streams[0]
                metadata["video"] = {
                    "codec": video_stream["codec_name"],
                    "width": video_stream["width"],
                    "height": video_stream["height"],
                    "fps": eval(video_stream["avg_frame_rate"])
                    if "avg_frame_rate" in video_stream
                    else None,
                }

            # 提取音频流信息
            audio_streams = [
                stream for stream in probe["streams"] if stream["codec_type"] == "audio"
            ]
            if audio_streams:
                audio_stream = audio_streams[0]
                metadata["audio"] = {
                    "codec": audio_stream["codec_name"],
                    "channels": audio_stream["channels"],
                    "sample_rate": int(audio_stream["sample_rate"])
                    if "sample_rate" in audio_stream
                    else None,
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
            metadata["source"] = {"bucket": bucket_name, "key": object_key}

            return metadata
        finally:
            # 无论成功与否，都清理临时文件
            if temp_file_path:
                self.cleanup_temp_file(temp_file_path)

    def create_proxy_with_counter(self, input_file, output_file=None):
        """
        将视频压制为720p 30fps并添加帧数计数器

        Args:
            input_file (str): 输入视频文件路径
            output_file (str, optional): 输出视频文件路径，如果不指定则自动生成

        Returns:
            str: 输出视频文件路径
        """
        try:
            if output_file is None:
                # 生成输出文件路径
                file_dir = os.path.dirname(input_file)
                file_name = os.path.splitext(os.path.basename(input_file))[0]
                output_file = os.path.join(file_dir, f"{file_name}_proxy.mp4")

            # 确保输出目录存在
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            font_path = self.font_path

            logger.info(f"开始处理视频: {input_file}")

            # 使用subprocess直接调用ffmpeg命令
            # 构建ffmpeg命令
            cmd = [
                "ffmpeg",
                "-i",
                input_file,
                "-vf",
                f"scale=-1:540,fps=fps=30,drawtext=text='%{{frame_num}}':x=10:y=h-th-10:fontfile={font_path}:fontsize=60:fontcolor=yellow:box=1:boxcolor=black@0.5",
                "-c:v",
                "libx264",  # 视频编码使用h264
                "-preset",
                "medium",  # 编码速度和质量的平衡
                "-crf",
                "23",  # 视频质量参数
                "-c:a",
                "aac",  # 音频编码使用aac
                "-y",  # 覆盖输出文件
                output_file,
            ]

            # 记录完整命令
            logger.info(f"执行命令: {' '.join(cmd)}")

            # 执行命令并捕获输出
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            # 获取命令输出
            stdout, stderr = process.communicate()

            # 检查命令是否成功执行
            if process.returncode != 0:
                logger.error(f"FFmpeg命令执行失败，错误码: {process.returncode}")
                logger.error(f"错误输出: {stderr}")
                raise Exception(f"FFmpeg处理失败，错误码: {process.returncode}")

            logger.info(f"视频处理完成: {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"视频处理失败: {str(e)}")
            # 如果输出文件已经创建但处理失败，删除它
            if output_file and os.path.exists(output_file):
                try:
                    os.remove(output_file)
                    logger.info(f"删除不完整的输出文件: {output_file}")
                except Exception as cleanup_error:
                    logger.error(f"删除不完整的输出文件失败: {output_file} {cleanup_error}")
            raise Exception(f"视频处理失败: {str(e)}")

    def process_and_upload_proxy(self, bucket_name, object_key):
        """
        下载视频，创建代理文件（720p 30fps带帧数计数器），并上传到S3

        Args:
            bucket_name (str): S3存储桶名称
            object_key (str): S3对象键（路径）

        Returns:
            dict: 包含原始视频和代理视频信息的字典
        """
        start_time = time.time()
        temp_input_file = None
        temp_output_file = None
        try:
            # 下载原始视频
            download_start = time.time()
            temp_input_file = self.download_video(bucket_name, object_key)
            download_time = time.time() - download_start

            # 创建代理文件
            process_start = time.time()
            temp_output_file = self.create_proxy_with_counter(temp_input_file)
            process_time = time.time() - process_start

            # 构建代理文件的S3路径
            proxy_key = f"proxy/{os.path.splitext(object_key)[0]}_proxy.mp4"

            # 上传代理文件到S3
            upload_start = time.time()
            logger.info(f"开始上传代理文件到S3: {bucket_name}/{proxy_key}")
            self.s3_client.upload_file(temp_output_file, bucket_name, proxy_key)
            upload_time = time.time() - upload_start

            total_time = time.time() - start_time

            return {
                "original": {"bucket": bucket_name, "key": object_key},
                "proxy": {"bucket": bucket_name, "key": proxy_key},
                "processing_times": {
                    "download": round(download_time, 2),
                    "process": round(process_time, 2),
                    "upload": round(upload_time, 2),
                    "total": round(total_time, 2),
                },
            }

        finally:
            # 清理临时文件
            if temp_input_file:
                self.cleanup_temp_file(temp_input_file)
            if temp_output_file:
                self.cleanup_temp_file(temp_output_file)
