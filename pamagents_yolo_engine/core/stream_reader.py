import cv2
import time
import os

class VideoStreamer:
    def __init__(self, source, target_fps=5, loop=True):
        self.source = source
        self.target_fps = target_fps
        self.loop = loop
        
        # Check if source is a local file
        self.is_file = isinstance(self.source, str) and os.path.isfile(self.source)
        
        try:
            self.source = int(source)
            self.is_file = False
        except ValueError:
            pass
            
        self.cap = cv2.VideoCapture(self.source)
        
        # Calculate time interval between frames
        self.frame_interval = 1.0 / target_fps if target_fps > 0 else 0
        self.last_frame_time = time.time()

    def get_next_frame(self):
        if not self.cap.isOpened():
            return None

        if self.is_file:
            # For local files, read sequentially and loop if requested
            ret, frame = self.cap.read()
            
            if not ret:
                if self.loop:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = self.cap.read()
                    if not ret:
                        return None
                else:
                    return None
                    
            # Enforce target FPS sleep for local files so it doesn't play too fast
            current_time = time.time()
            elapsed = current_time - self.last_frame_time
            if elapsed < self.frame_interval:
                time.sleep(self.frame_interval - elapsed)
                
            self.last_frame_time = time.time()
            return frame
        else:
            # For live streams (RTSP/Webcam), grab frames to clear buffer and keep real-time sync
            while True:
                ret = self.cap.grab()
                if not ret:
                    return None

                current_time = time.time()
                elapsed = current_time - self.last_frame_time

                if elapsed >= self.frame_interval:
                    ret, frame = self.cap.retrieve()
                    if ret:
                        self.last_frame_time = current_time
                        return frame
                    else:
                        return None
                
                time.sleep(0.001)

    def release(self):
        if self.cap.isOpened():
            self.cap.release()
