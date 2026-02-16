from ultralytics import YOLO
import torch

class ObjectDetector:
    def __init__(self, model_name="yolo26n.pt"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.use_half = self.device == "cuda"
        print(f"Loading YOLO on {self.device} (half={self.use_half})...")
        self.model = YOLO(model_name)
        # Fuse model layers for faster inference
        self.model.fuse()
    
    def detect(self, frame):
        # Frame is numpy array (RGB)
        results = self.model(frame, verbose=False, half=self.use_half, imgsz=640)
        return results[0]  # Return first result (single frame)
