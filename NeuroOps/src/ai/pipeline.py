from PyQt6.QtCore import QThread, pyqtSignal
import imageio.v3 as iio
import numpy as np
import time
from .detector import ObjectDetector
from .embedder import ClipEmbedder
from src.data.db_manager import DatabaseManager
from src.data.models import Detection
from src.data.vector_store import VectorStore
from src.decision_engine.core import DecisionCore
from src.visual_cortex.vllm_client import VLLMClient
from src.active_learning.sampler import EntropySampler
from src.active_learning.label_studio import LabelStudioConnector
from src.visual_cortex.reid import IdentityEncoder
from src.agency.agent import AutonomousAgent

class VideoAnalysisWorker(QThread):
    progress_update = pyqtSignal(int)
    log_message = pyqtSignal(str)
    finished_processing = pyqtSignal(bool)
    alert_triggered = pyqtSignal(str, str) # severity, message
    stats_update = pyqtSignal(dict) # dynamic stats for dashboard

    def __init__(self, video_path, video_id):
        super().__init__()
        self.video_path = video_path
        self.video_id = video_id
        self.is_running = True
        self.db = DatabaseManager()
        # Ensure collection name is a string
        self.vector_store = VectorStore(str(self.video_id)) 
        self.detector = None
        self.embedder = None
        self.decision_core = DecisionCore()
        self.vllm = None
        self.label_studio = LabelStudioConnector()
        self.reid = None
        self.agent = AutonomousAgent()

    def run(self):
        self.log_message.emit(f"Starting analysis for: {self.video_path}")
        
        try:
            # Lazy load models
            if not self.detector:
                self.detector = ObjectDetector("yolov8n.pt")
                
            if not self.embedder:
                self.embedder = ClipEmbedder()
                
            if not self.vllm:
                # Lazy load VLLM client (connection only)
                self.vllm = VLLMClient()
                
            if not self.reid:
                self.reid = IdentityEncoder()

            # Read video metadata
            props = iio.improps(self.video_path, plugin="pyav")
            total_frames = props.shape[0] if props.shape else 0
            fps = 30.0 # Default fallback, as ImageIO props might vary
            
            # Using basic imageio iterator
            reader = iio.imread(self.video_path, plugin="pyav", index=None)
            
            frame_idx = 0
            session = self.db.get_session()
            
            for frame in reader:
                if not self.is_running:
                    break
                
                # Detect every 5th frame for performance (Sampling)
                if frame_idx % 5 == 0:
                    r = self.detector.detect(frame)
                    
                    # Store detections
                    for box in r.boxes:
                        # box.xyxy is tensor
                        coords = box.xyxy[0].cpu().tolist()
                        conf = float(box.conf[0].cpu())
                        cls_id = int(box.cls[0].cpu())
                        cls_name = self.detector.model.names[cls_id]

                        # Crop object for embedding
                        x1, y1, x2, y2 = map(int, coords)
                        # Ensure within bounds
                        h, w, _ = frame.shape
                        x1, y1 = max(0, x1), max(0, y1)
                        x2, y2 = min(w, x2), min(h, y2)
                        
                        point_id = None
                        if x2 > x1 and y2 > y1:
                            crop = frame[y1:y2, x1:x2]
                            vector = self.embedder.embed_image(crop)
                            
                            # Store in Qdrant
                            metadata = {
                                "video_id": self.video_id,
                                "frame_idx": frame_idx,
                                "class_name": cls_name,
                                "confidence": conf,
                                "timestamp": frame_idx / fps
                            }
                            point_id = self.vector_store.add_embedding(vector, metadata)
                            
                            # Identity Re-ID (Person Only)
                            if cls_name == 'person':
                                id_vector = self.reid.extract_feature(crop)
                                self.vector_store.add_identity(id_vector, metadata)

                        # Decision Engine Evaluation
                        context = {
                            "class_name": cls_name,
                            "confidence": conf,
                            "timestamp": frame_idx / fps,
                            "zone": "default" # Placeholder
                        }
                        actions = self.decision_core.evaluate(context)
                        for action in actions:
                            if action['type'] == 'alert':
                                msg = action.get('message', 'Alert')
                                severity = action.get('severity', 'info')
                                self.log_message.emit(f"[ZEN]: {msg}")
                                self.alert_triggered.emit(severity, msg)
                            
                            if action['type'] == 'trigger_vllm':
                                prompt = action.get('prompt', 'Describe this.')
                                self.log_message.emit(f"[VLLM]: Analyzing frame for rule...")
                                # In a real app, offload this to another thread to avoid blocking detection
                                desc = self.vllm.analyze_frame(frame, prompt)
                                self.log_message.emit(f"[VLLM RESULT]: {desc}")
                                
                                # Store in DB
                                self.db.add_summary(
                                    video_id=self.video_id,
                                    timestamp=frame_idx / fps,
                                    content=desc,
                                    prompt=prompt
                                )

                            if action['type'] == 'perform_action':
                                tool_name = action.get('tool')
                                params = action.get('params', {})
                                result = self.agent.execute_action(tool_name, params)
                                self.log_message.emit(f"[AGENT]: {result}")

                        # Active Learning Check
                        if EntropySampler.is_uncertain(conf):
                            uncertainty = EntropySampler.calculate_entropy(conf)
                            self.log_message.emit(f"[ACTIVE LEARNING] Uncertain detection ({conf:.2f}). Queueing for review...")
                            self.label_studio.upload_task(
                                frame, # Ideally crop object
                                {
                                    "class_name": cls_name,
                                    "confidence": conf,
                                    "uncertainty": uncertainty
                                }
                            )

                        det = Detection(
                            video_id=self.video_id,
                            frame_index=frame_idx,
                            timestamp=frame_idx / fps, # Approximation
                            class_name=cls_name,
                            confidence=conf,
                            bbox_xyxy=coords,
                            embedding_id=point_id
                        )
                        session.add(det)
                    
                    if frame_idx % 5 == 0:
                        # ... (existing detection logic) ...
                        
                        # Emit Stats (Moved here to capture detection count)
                        det_count = len(r.boxes)
                        self.stats_update.emit({
                            "frame": frame_idx,
                            "timestamp": frame_idx / fps,
                            "detections": det_count,
                            "classes": [self.detector.model.names[int(b.cls[0])] for b in r.boxes]
                        })

                    if frame_idx % 30 == 0:
                        session.commit()
                        progress = int((frame_idx / total_frames) * 100) if total_frames > 0 else 0
                        self.progress_update.emit(progress)

                frame_idx += 1

            session.commit()
            session.close()
            self.log_message.emit("Analysis Complete.")
            self.finished_processing.emit(True)

        except Exception as e:
            self.log_message.emit(f"Error: {str(e)}")
            self.finished_processing.emit(False)

    def stop(self):
        self.is_running = False
