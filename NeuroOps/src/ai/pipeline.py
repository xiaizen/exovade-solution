from PyQt6.QtCore import QThread, pyqtSignal
import numpy as np
import time

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

        # Lazy-loaded in run() — avoid importing heavy libs at startup
        self.db = None
        self.vector_store = None
        self.detector = None
        self.embedder = None
        self.decision_core = None
        self.vllm = None
        self.label_studio = None
        self.reid = None
        self.agent = None
        self.ocr = None

    def run(self):
        self.log_message.emit(f"Starting analysis for: {self.video_path}")
        
        try:
            # Deferred imports — only loaded when analysis actually starts
            import imageio.v3 as iio
            from .detector import ObjectDetector
            from .embedder import ClipEmbedder
            from src.data.db_manager import DatabaseManager
            from src.data.models import Detection, TextDetection
            from src.data.vector_store import VectorStore
            from src.decision_engine.core import DecisionCore
            from src.visual_cortex.vllm_client import VLLMClient
            from src.active_learning.sampler import EntropySampler
            from src.active_learning.label_studio import LabelStudioConnector
            from src.visual_cortex.reid import IdentityEncoder
            from src.agency.agent import AutonomousAgent
            from src.ai.ocr import OCRProcessor

            # Lazy-init services
            if not self.db:
                self.db = DatabaseManager()
            if not self.vector_store:
                self.vector_store = VectorStore(str(self.video_id))
            if not self.decision_core:
                self.decision_core = DecisionCore()
            if not self.label_studio:
                self.label_studio = LabelStudioConnector()
            if not self.agent:
                self.agent = AutonomousAgent()

            # Load only essential models upfront — others load on first use
            self.log_message.emit("Loading YOLO detector...")
            if not self.detector:
                self.detector = ObjectDetector("yolo26n.pt")
            
            self.log_message.emit("Loading CLIP embedder...")
            if not self.embedder:
                self.embedder = ClipEmbedder()
            
            self.log_message.emit("Models ready. Starting frame processing...")

            # Read video metadata
            props = iio.improps(self.video_path, plugin="pyav")
            total_frames = props.shape[0] if props.shape else 0
            fps = 30.0 # Default fallback

            # --- Performance tuning ---
            FRAME_SKIP = 15          # Process every 15th frame (~2 fps)
            CONF_THRESHOLD = 0.4     # Skip CLIP/Re-ID for low-confidence
            OCR_INTERVAL = 90        # OCR once per ~3 seconds
            COMMIT_INTERVAL = 90     # DB commit interval
            
            # Using basic imageio iterator
            reader = iio.imread(self.video_path, plugin="pyav", index=None)
            
            frame_idx = 0
            session = self.db.get_session()
            
            for frame in reader:
                if not self.is_running:
                    break
                
                # Process only every Nth frame
                if frame_idx % FRAME_SKIP == 0:
                    r = self.detector.detect(frame)
                    
                    # Collect batch items for Qdrant
                    embedding_batch = []
                    identity_batch = []
                    
                    # Store detections
                    for box in r.boxes:
                        coords = box.xyxy[0].cpu().tolist()
                        conf = float(box.conf[0].cpu())
                        cls_id = int(box.cls[0].cpu())
                        cls_name = self.detector.model.names[cls_id]

                        # Crop object for embedding
                        x1, y1, x2, y2 = map(int, coords)
                        h, w, _ = frame.shape
                        x1, y1 = max(0, x1), max(0, y1)
                        x2, y2 = min(w, x2), min(h, y2)
                        
                        point_id = None
                        # Only embed high-confidence detections
                        if x2 > x1 and y2 > y1 and conf >= CONF_THRESHOLD:
                            crop = frame[y1:y2, x1:x2]
                            vector = self.embedder.embed_image(crop)
                            
                            metadata = {
                                "video_id": self.video_id,
                                "frame_idx": frame_idx,
                                "class_name": cls_name,
                                "confidence": conf,
                                "timestamp": frame_idx / fps
                            }
                            embedding_batch.append((vector, metadata))
                            
                            # Identity Re-ID (Person Only — lazy load)
                            if cls_name == 'person':
                                if not self.reid:
                                    self.log_message.emit("Loading Re-ID model...")
                                    self.reid = IdentityEncoder()
                                id_vector = self.reid.extract_feature(crop)
                                identity_batch.append((id_vector, metadata))

                        # Decision Engine Evaluation
                        context = {
                            "class_name": cls_name,
                            "confidence": conf,
                            "timestamp": frame_idx / fps,
                            "zone": "default"
                        }
                        actions = self.decision_core.evaluate(context)
                        for action in actions:
                            if action['type'] == 'alert':
                                msg = action.get('message', 'Alert')
                                severity = action.get('severity', 'info')
                                self.log_message.emit(f"[ZEN]: {msg}")
                                self.alert_triggered.emit(severity, msg)
                            
                            if action['type'] == 'trigger_vllm':
                                if not self.vllm:
                                    self.vllm = VLLMClient()
                                prompt = action.get('prompt', 'Describe this.')
                                self.log_message.emit(f"[VLLM]: Analyzing frame for rule...")
                                desc = self.vllm.analyze_frame(frame, prompt)
                                self.log_message.emit(f"[VLLM RESULT]: {desc}")
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
                                frame,
                                {
                                    "class_name": cls_name,
                                    "confidence": conf,
                                    "uncertainty": uncertainty
                                }
                            )

                        det = Detection(
                            video_id=self.video_id,
                            frame_index=frame_idx,
                            timestamp=frame_idx / fps,
                            class_name=cls_name,
                            confidence=conf,
                            bbox_xyxy=coords,
                            embedding_id=point_id
                        )
                        session.add(det)
                    
                    # Batch upsert embeddings to Qdrant (much faster than one-by-one)
                    if embedding_batch:
                        batch_ids = self.vector_store.add_embeddings_batch(embedding_batch)
                    
                    # Batch upsert identities
                    for id_vec, id_meta in identity_batch:
                        self.vector_store.add_identity(id_vec, id_meta)
                    
                    # OCR Detection (reduced frequency, lazy load)
                    if frame_idx % OCR_INTERVAL == 0:
                        if not self.ocr:
                            self.log_message.emit("Loading OCR engine...")
                            self.ocr = OCRProcessor()
                        # Downscale for faster OCR
                        import cv2
                        h, w = frame.shape[:2]
                        if w > 1280:
                            scale = 1280 / w
                            small = cv2.resize(frame, (1280, int(h * scale)))
                        else:
                            small = frame
                        
                        text_results = self.ocr.detect_text(small)
                        for res in text_results:
                            if res['confidence'] > 0.4:
                                text_det = TextDetection(
                                    video_id=self.video_id,
                                    frame_index=frame_idx,
                                    timestamp=frame_idx / fps,
                                    text_content=res['text'],
                                    confidence=res['confidence'],
                                    bbox_xyxy=res['bbox']
                                )
                                session.add(text_det)
                                if res['confidence'] > 0.8:
                                     self.log_message.emit(f"[OCR] Detected: {res['text']}")

                    # Emit Stats
                    det_count = len(r.boxes)
                    details = []
                    for b in r.boxes:
                        cls_id = int(b.cls[0])
                        conf = float(b.conf[0])
                        cls_name = self.detector.model.names[cls_id]
                        details.append({
                            "class": cls_name,
                            "confidence": conf,
                            "box": b.xyxy[0].tolist()
                        })
                        
                    self.stats_update.emit({
                        "frame": frame_idx,
                        "timestamp": frame_idx / fps,
                        "detections": det_count,
                        "classes": [d['class'] for d in details],
                        "details": details
                    })

                    if frame_idx % COMMIT_INTERVAL == 0:
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
