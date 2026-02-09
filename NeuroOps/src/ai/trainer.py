from ultralytics import YOLO
import os

class ModelTrainer:
    def __init__(self, model_name="yolo26n.pt"):
        self.model_name = model_name
        self.model = YOLO(model_name)

    def train(self, data_path, epochs=10, imgsz=640, batch=16):
        """
        Runs the training loop.
        """
        print(f"Starting training for {epochs} epochs on {data_path}...")
        
        results = self.model.train(
            data=data_path,
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            device='0', # Use first GPU
            project='runs/train',
            name='neuroops_finetune',
            exist_ok=True
        )
        
        # Save best model to weights dir
        best_weight = os.path.join(results.save_dir, 'weights', 'best.pt')
        target_weight = 'weights/yolo26n_v2.pt'
        
        if os.path.exists(best_weight):
            import shutil
            os.makedirs('weights', exist_ok=True)
            shutil.copy2(best_weight, target_weight)
            print(f"Training complete. Best model saved to: {target_weight}")
            return target_weight
        else:
            print("Training finished but best.pt not found.")
            return None
