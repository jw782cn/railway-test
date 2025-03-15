import unittest
import os
import shutil
from video_processor import VideoProcessor

class TestVideoProcessor(unittest.TestCase):
    def setUp(self):
        """在每个测试用例前运行，设置测试环境"""
        self.processor = VideoProcessor()
        # 创建临时目录用于测试
        self.test_dir = 'test/tmp'
        
    def tearDown(self):
        """在每个测试用例后运行，清理测试环境"""
        # 删除测试过程中创建的临时目录
        shutil.rmtree(self.test_dir)

    def test_create_proxy_with_counter(self):
        """测试代理视频创建功能"""
        # 这里需要提供一个测试用的视频文件路径
        # 你需要替换为实际的测试视频文件路径
        test_video_path = "test/video.mp4"
        
        # 确保测试视频文件存在
        self.assertTrue(os.path.exists(test_video_path), "测试视频文件不存在")
        
        # 设置输出文件路径
        output_path = os.path.join(self.test_dir, "test_output_proxy.mp4")
        
        try:
            # 调用代理视频创建方法
            result_path = self.processor.create_proxy_with_counter(
                test_video_path,
                output_path
            )
            
            # 验证输出文件是否存在
            self.assertTrue(os.path.exists(result_path), "代理视频文件未创建成功")
            
            # 验证输出文件大小是否大于0
            self.assertGreater(os.path.getsize(result_path), 0, "代理视频文件是空的")
            
        except Exception as e:
            self.fail(f"代理视频创建失败: {str(e)}")

if __name__ == '__main__':
    unittest.main() 