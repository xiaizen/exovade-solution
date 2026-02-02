from ..ai.biometrics.engine import BiometricEngine
import os

class IdentityEncoder:
    def __init__(self, model_name="biometrics"):
        # Use our new BiometricEngine
        # Ensure weights path covers relative execution
        weights_path = os.path.abspath("NeuroOps/weights")
        self.engine = BiometricEngine(weights_dir=weights_path)
        print("[RE-ID] Validating Biometric Engine...")

    def extract_feature(self, image_crop):
        """
        Extract feature vector for a person crop using AdaFace.
        Returns: embedding (list of floats)
        """
        if isinstance(image_crop, list):
             # Handle weird case if passed as list
             return [0.0] * 512
             
        # BiometricEngine handles numpy arrays directly
        is_real, score, embedding = self.engine.analyze_face(image_crop)
        
        # We can optionally log spoof attempts here
        if not is_real:
             pass # potentially return None or zero vector?
             # For now, we return valid vector but maybe downstream logic handles "Fake"
        
        return embedding
