import logging
import asyncio
import os
import cv2
import numpy as np
from typing import List, Dict, Any

logger = logging.getLogger("ComputerVisionAgent")

class ComputerVisionAgent:
    """
    Real Computer Vision Agent using OpenCV.
    Performs frame extraction, metadata analysis, and simulated OCR/Detection (extensible).
    """

    async def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Extract basic metadata using OpenCV.
        """
        logger.info(f"Analyzing image: {image_path}")
        
        if not os.path.exists(image_path):
             return {"error": "Image not found"}

        img = cv2.imread(image_path)
        if img is None:
             return {"error": "Failed to load image"}

        height, width, channels = img.shape
        
        # Calculate dominant color (Simple average)
        avg_color_per_row = np.average(img, axis=0)
        avg_color = np.average(avg_color_per_row, axis=0)
        
        analysis = {
            "resolution": f"{width}x{height}",
            "channels": channels,
            "dominant_color_bgr": avg_color.tolist(),
            "file_size_kb": os.path.getsize(image_path) / 1024
        }
        
        markdown = f"""
## 🖼️ Image Analysis
- **Resolution**: {width}px x {height}px
- **Size**: {analysis['file_size_kb']:.2f} KB
- **Channels**: {channels}
"""
        return {"markdown": markdown, "metadata": analysis}

    async def video_processor(self, video_path: str, extract_every_n_frames: int = 30) -> Dict[str, Any]:
        """
        Extract frames and metadata from video using OpenCV.
        """
        logger.info(f"Processing video: {video_path}")
        
        if not os.path.exists(video_path):
             return {"error": "Video not found"}

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
             return {"error": "Could not open video"}

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        frames_extracted = 0
        output_dir = os.path.join(os.path.dirname(video_path), "frames")
        os.makedirs(output_dir, exist_ok=True)
        
        current_frame = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if current_frame % extract_every_n_frames == 0:
                frame_name = f"frame_{current_frame}.jpg"
                cv2.imwrite(os.path.join(output_dir, frame_name), frame)
                frames_extracted += 1
                
            current_frame += 1
            
        cap.release()
        
        return {
            "fps": fps,
            "total_frames": total_frames,
            "duration_sec": duration,
            "frames_extracted": frames_extracted,
            "output_dir": output_dir
        }

agent = ComputerVisionAgent()
