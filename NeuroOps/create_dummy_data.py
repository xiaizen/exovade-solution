import cv2
import numpy as np
import json
import os

os.makedirs("collections/labeled", exist_ok=True)

# Create dummy image
img = np.zeros((480, 640, 3), dtype=np.uint8)
cv2.rectangle(img, (100, 100), (200, 200), (0, 255, 0), -1) # Green box
cv2.imwrite("collections/labeled/dummy_task_01.jpg", img)

# Create dummy label
data = {
    "data": {
        "image": "dummy_task_01.jpg"
    },
    "predictions": [{
        "result": [{
            "value": {
                "x": 100, "y": 100, "width": 100, "height": 100,
                "rectanglelabels": ["green_box"]
            }
        }]
    }]
}

with open("collections/labeled/dummy_task_01.json", "w") as f:
    json.dump(data, f)

print("Created dummy data in collections/labeled")
