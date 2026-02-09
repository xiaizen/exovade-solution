import os
import shutil
import json
import random
import yaml
import cv2
from pathlib import Path

class DataPreparer:
    def __init__(self, source_dir="collections/labeled", dataset_dir="dataset"):
        self.source_dir = Path(source_dir)
        self.dataset_dir = Path(dataset_dir)
        self.images_dir = self.dataset_dir / "images"
        self.labels_dir = self.dataset_dir / "labels"
        self.classes = set()
        self.temp_data = [] # Store (split, image_path, [(class_name, x, y, w, h)])

    def prepare(self, split_ratio=0.8):
        print(f"Preparing data from {self.source_dir}...")
        
        if not self.source_dir.exists():
            print(f"Error: Source directory {self.source_dir} does not exist.")
            return False

        # 1. Scan and parse headers to build class list
        json_files = list(self.source_dir.glob("*.json"))
        if not json_files:
            print("No JSON files found.")
            return False
            
        print(f"Found {len(json_files)} tasks. Parsing...")
        
        split_idx = int(len(json_files) * split_ratio)
        if split_idx == 0 and len(json_files) > 0:
             split_idx = 1 # Force at least 1 for train if we have data
        
        for i, json_file in enumerate(json_files):
            split = 'train' if i < split_idx else 'val'
            self._parse_file(json_file, split)
            
        # 2. Setup Directories
        for split in ['train', 'val']:
            (self.images_dir / split).mkdir(parents=True, exist_ok=True)
            (self.labels_dir / split).mkdir(parents=True, exist_ok=True)
            
        # 3. Create YAML
        class_list = sorted(list(self.classes))
        print(f"Classes found: {class_list}")
        
        yaml_data = {
            'train': str((self.images_dir / 'train').absolute()).replace('\\', '/'),
            'val': str((self.images_dir / 'val').absolute()).replace('\\', '/'),
            'nc': len(class_list),
            'names': class_list
        }
        
        with open(self.dataset_dir / "data.yaml", 'w') as f:
            yaml.dump(yaml_data, f)
            
        # 4. Write Data
        for item in self.temp_data:
            split, src_img, labels = item
            
            # Copy Image
            dst_img = self.images_dir / split / src_img.name
            shutil.copy2(src_img, dst_img)
            
            # Write Label
            txt_name = src_img.name.rsplit('.', 1)[0] + ".txt"
            dst_txt = self.labels_dir / split / txt_name
            
            with open(dst_txt, 'w') as f:
                for lbl in labels:
                    cls_name, x, y, w, h = lbl
                    if cls_name in class_list:
                        cls_id = class_list.index(cls_name)
                        f.write(f"{cls_id} {x:.6f} {y:.6f} {w:.6f} {h:.6f}\n")
                        
        print(f"Success! Dataset created at {self.dataset_dir}")
        return True

    def _parse_file(self, json_file, split):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                
            # Locate Image
            image_rel = data.get('data', {}).get('image')
            if not image_rel: return
            
            # Assume image is in same dir as json for "labeled" collection
            image_name = os.path.basename(image_rel)
            src_image_path = self.source_dir / image_name
            
            if not src_image_path.exists():
                return

            # Read Image for Dimensions (needed for normalization if raw pixels used)
            img = cv2.imread(str(src_image_path))
            if img is None: return
            img_h, img_w = img.shape[:2]

            labels = []
            for pred in data.get('predictions', []):
                for res in pred.get('result', []):
                    val = res.get('value', {})
                    rect_labels = val.get('rectanglelabels', [])
                    if not rect_labels: continue
                    
                    cls_name = rect_labels[0]
                    self.classes.add(cls_name)
                    
                    # Coordinate Handling
                    # We accept 'x', 'y', 'width', 'height' assuming they are PIXELS 
                    # based on our previous placeholder logic.
                    x = val.get('x', 0)
                    y = val.get('y', 0)
                    w = val.get('width', 0)
                    h = val.get('height', 0)
                    
                    # Convert to Center-XYWH Normalized
                    cx = (x + w/2) / img_w
                    cy = (y + h/2) / img_h
                    nw = w / img_w
                    nh = h / img_h
                    
                    labels.append((cls_name, cx, cy, nw, nh))
            
            if labels:
                self.temp_data.append((split, src_image_path, labels))
                
        except Exception as e:
            print(f"Error parsing {json_file}: {e}")

if __name__ == "__main__":
    preparer = DataPreparer()
    preparer.prepare()
