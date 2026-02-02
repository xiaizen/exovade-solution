from ultralytics import YOLO
import torch

class ObjectDetector:
    def __init__(self, model_name="yolo26n.pt"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading YOLO on {self.device}...")
        self.model = YOLO(model_name)
    
    def detect(self, frame):
        # Frame is numpy array (RGB)
        results = self.model(frame, verbose=False)
        return results[0]  # Return first result (single frame)
