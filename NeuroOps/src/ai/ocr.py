import easyocr
import numpy as np

class OCRProcessor:
    def __init__(self, languages=['en']):
        """
        Initializes the EasyOCR reader.
        Args:
            languages (list): List of language codes to detect.
        """
        # Initialize reader (will download model on first run if needed)
        # Using gpu=True if CUDA is available, usually handled automatically by easyocr but good to know.
        self.reader = easyocr.Reader(languages, gpu=True)

    def detect_text(self, frame):
        """
        Detects text in the given frame.
        Args:
            frame (numpy.ndarray): The video frame (RGB).
        
        Returns:
            list: List of detections. Each detection is a dict:
                  {
                      'bbox': [x1, y1, x2, y2],
                      'text': str,
                      'confidence': float
                  }
        """
        # EasyOCR expects RGB or Grayscale. `frame` from imageio/ffmpeg is usually RGB.
        # readtext returns a list of (bbox, text, prob).
        # bbox is a list of 4 points: [[x,y], [x,y], [x,y], [x,y]] (top-left, top-right, bottom-right, bottom-left)
        
        results = self.reader.readtext(frame)
        
        detections = []
        for (bbox, text, prob) in results:
            # Convert bbox to x1,y1,x2,y2
            # bbox is list of lists
            xs = [point[0] for point in bbox]
            ys = [point[1] for point in bbox]
            
            x1, x2 = min(xs), max(xs)
            y1, y2 = min(ys), max(ys)
            
            detections.append({
                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                'text': text,
                'confidence': float(prob)
            })
            
        return detections
