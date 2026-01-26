import numpy as np

class EntropySampler:
    @staticmethod
    def calculate_entropy(probs):
        """
        Calculate Shannon entropy for a probability distribution.
        probs: list or numpy array of probabilities (must sum to 1 ideally, 
               but strictly for YOLO classification score, we treat conf as p(class)
               and 1-conf as p(other)).
        """
        # For single-class confidence score p: entropy = -p*log(p) - (1-p)*log(1-p)
        p = np.clip(probs, 1e-6, 1 - 1e-6) # Avoid log(0)
        entropy = -p * np.log2(p) - (1 - p) * np.log2(1 - p)
        return entropy

    @staticmethod
    def is_uncertain(confidence, min_thresh=0.3, max_thresh=0.6):
        """
        Simple uncertainty sampling based on confidence thresholds.
        If confidence is "middle of the road", it's uncertain.
        """
        return min_thresh <= confidence <= max_thresh
