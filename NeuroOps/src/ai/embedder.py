from sentence_transformers import SentenceTransformer
from PIL import Image
import numpy as np
import torch

class ClipEmbedder:
    def __init__(self, model_name="clip-ViT-B-32"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading CLIP ({model_name}) on {self.device}...")
        self.model = SentenceTransformer(model_name, device=self.device)

    def embed_image(self, image_array):
        """
        Embeds a numpy image array (RGB).
        Returns a list of floats (vector).
        """
        # Convert numpy array to PIL Image
        if isinstance(image_array, np.ndarray):
            image = Image.fromarray(image_array)
        else:
            image = image_array
            
        vector = self.model.encode(image)
        return vector.tolist()

    def embed_text(self, text):
        """
        Embeds text query.
        Returns a list of floats.
        """
        vector = self.model.encode(text)
        return vector.tolist()
