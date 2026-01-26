from openai import OpenAI
import base64
import cv2
import io
from PIL import Image

class VLLMClient:
    def __init__(self, base_url="http://localhost:8000/v1", api_key="EMPTY"):
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        self.model = "llava-hf/llava-1.5-7b-hf" # Example model name

    def encode_image(self, image_array):
        """Encodes numpy array to base64 jpeg."""
        if isinstance(image_array, str):
            # If path
            with open(image_array, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        
        # If numpy
        img = Image.fromarray(image_array)
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    def analyze_frame(self, frames, prompt="Describe this image in detail."):
        """
        frames: Single numpy array or list of numpy arrays.
                If list, we tile them or send as multiple images (model dependent).
                For this prototype, we just use the last frame if a list is passed,
                conceptually treating it as 'contextual' but physically sending one 
                to avoid token limits on small local models.
        """
        target_frame = frames
        if isinstance(frames, list):
            # For prototype: Just take the last frame (most recent)
            # Future: Stitch frames horizontally to show temporal progression
            target_frame = frames[-1]
            
        try:
            base64_image = self.encode_image(target_frame)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=300,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"VLLM Error: {e}")
            return "VLLM Unreachable or Error."
