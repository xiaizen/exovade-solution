import os
import json
import uuid
import cv2

class LabelStudioConnector:
    def __init__(self, export_dir="collections/to_label"):
        self.export_dir = export_dir
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)

    def upload_task(self, frame, metadata):
        """
        Simulates uploading a task.
        Saves image to disk and metadata to json.
        """
        task_id = str(uuid.uuid4())
        image_name = f"task_{task_id}.jpg"
        image_path = os.path.join(self.export_dir, image_name)
        
        # Save image
        cv2.imwrite(image_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        
        # Save task definition
        task_data = {
            "data": {
                "image": image_path
            },
            "predictions": [{
                "model_version": "yolo26n",
                "score": metadata.get("confidence", 0),
                "result": [{
                    "from_name": "label",
                    "to_name": "image",
                    "type": "rectanglelabels",
                    "value": {
                        "x": 0, "y": 0, "width": 100, "height": 100, # Placeholder
                        "rectanglelabels": [metadata.get("class_name")]
                    }
                }]
            }]
        }
        
        json_path = os.path.join(self.export_dir, f"task_{task_id}.json")
        with open(json_path, 'w') as f:
            json.dump(task_data, f, indent=2)
            
        print(f"[ACTIVE LEARNING] Task uploaded: {task_id} (Uncertainty: {metadata.get('uncertainty', 0):.2f})")
