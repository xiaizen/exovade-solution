import torch
import numpy as np
import cv2
import os
from .models.minifasnet import MiniFASNetV2SE, MiniFASNetV2
from .models.adaface import build_model
from PIL import Image

class BiometricEngine:
    def __init__(self, weights_dir="./weights"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.weights_dir = weights_dir
        
        # Paths
        self.spoof_path = os.path.join(weights_dir, "MiniFASNetV2.pth")
        self.adaface_path = os.path.join(weights_dir, "adaface_ir50_ms1mv2.ckpt")
        
        self.use_biometrics = False
        self._load_models()
        
    def _load_models(self):
        try:
            # 1. Load Anti-Spoofing (MiniFASNetV2)
            if os.path.exists(self.spoof_path):
                # MiniFASNetV2: 80x80, conv6_kernel=(7,7), num_classes=3
                self.spoof_model = MiniFASNetV2(conv6_kernel=(7, 7)).to(self.device)
                state_dict = torch.load(self.spoof_path, map_location=self.device)
                # Handle DataParallel wrap if present
                if 'state_dict' in state_dict:
                    state_dict = state_dict['state_dict']
                # Remove module. prefix if present
                new_state_dict = {}
                for k, v in state_dict.items():
                    name = k.replace("module.", "")
                    new_state_dict[name] = v
                self.spoof_model.load_state_dict(new_state_dict, strict=False)
                self.spoof_model.eval()
                print("[BIOMETRICS] Loaded MiniFASNetV2 (Anti-Spoofing)")
            else:
                print(f"[BIOMETRICS] Warning: {self.spoof_path} not found. Anti-spoofing disabled.")
                self.spoof_model = None

            # 2. Load Recognition (AdaFace IR-50)
            if os.path.exists(self.adaface_path):
                self.adaface_model = build_model('ir_50').to(self.device)
                # Load checkpoint
                checkpoint = torch.load(self.adaface_path, map_location=self.device)
                if 'state_dict' in checkpoint:
                     state_dict = checkpoint['state_dict']
                else:
                     state_dict = checkpoint
                
                # Cleaning keys
                new_state_dict = {}
                for k, v in state_dict.items():
                    name = k.replace("module.", "")
                    new_state_dict[name] = v
                    
                self.adaface_model.load_state_dict(new_state_dict, strict=False)
                self.adaface_model.eval()
                print("[BIOMETRICS] Loaded AdaFace (Face Recognition)")
                self.use_biometrics = True
            else:
                print(f"[BIOMETRICS] Warning: {self.adaface_path} not found. Recognition disabled.")
                self.adaface_model = None
                
        except Exception as e:
            print(f"[BIOMETRICS] Error loading models: {e}")
            self.use_biometrics = False

    def preprocess_spoof(self, image_crop):
        # Resize to 80x80
        img = cv2.resize(image_crop, (80, 80))
        img = img.astype(np.float32)
        img = img.transpose((2, 0, 1)) # C, H, W
        img = torch.from_numpy(img).unsqueeze(0).to(self.device)
        return img

    def preprocess_adaface(self, image_crop):
        # Resize to 112x112, Normalize -1 to 1
        img = cv2.resize(image_crop, (112, 112))
        img = img[:, :, ::-1] # BGR to RGB
        img = ((img / 255.0) - 0.5) / 0.5
        img = img.transpose((2, 0, 1)).astype(np.float32)
        img = torch.from_numpy(img).unsqueeze(0).to(self.device)
        return img

    def analyze_face(self, image_crop):
        """
        Returns:
            is_real (bool): True if real face
            spoof_score (float): Probability of being real (class 1)
            embedding (list): 512-dim vector for identity
        """
        if not self.use_biometrics or image_crop is None or image_crop.size == 0:
            return True, 0.0, np.zeros(512).tolist()

        is_real = True
        spoof_score = 1.0
        embedding = np.zeros(512).tolist()

        with torch.no_grad():
            # 1. Anti-Spoofing Check
            if self.spoof_model:
                spoof_input = self.preprocess_spoof(image_crop)
                prediction = self.spoof_model(spoof_input)
                probs = F.softmax(prediction, dim=1)
                # Class 1 is usually 'Live' in MiniFASNet protocols (check specific model)
                # Assuming index 1 is live/real. 
                # Note: MiniFASNet output classes depend on training. 
                # Common: 0=Spoof, 1=Real OR 0=Real, 1=Print, 2=Replay.
                # Let's assume standard 3 class: 0=Spoof, 1=Real. 
                # Actually commonly: 1=Live. Let's use index 1 prob.
                spoof_score = probs[0][1].item()
                if spoof_score < 0.4: # Threshold
                    is_real = False
            
            # 2. Identify (only if real or forced)
            # We extract embedding regardless for now, but tag as spoof
            if self.adaface_model:
                ada_input = self.preprocess_adaface(image_crop)
                feat, _ = self.adaface_model(ada_input)
                embedding = feat.cpu().numpy()[0].tolist()

        return is_real, spoof_score, embedding
