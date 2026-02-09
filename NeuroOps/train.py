import sys
import os
import argparse

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.active_learning.prepare_data import DataPreparer
from src.ai.trainer import ModelTrainer

def main():
    parser = argparse.ArgumentParser(description="NeuroOps Training Pipeline")
    parser.add_argument('--epochs', type=int, default=10, help='Number of epochs')
    parser.add_argument('--prepare-only', action='store_true', help='Only prepare data, do not train')
    parser.add_argument('--source', type=str, default='collections/labeled', help='Source directory for labeled data')
    
    args = parser.parse_args()
    
    print("--- NeuroOps Training Pipeline ---")
    
    # 1. Prepare Data
    print("\n[1/2] Preparing Dataset...")
    preparer = DataPreparer(source_dir=args.source)
    success = preparer.prepare()
    
    if not success:
        print("Data preparation failed or no data found.")
        return
        
    if args.prepare_only:
        print("Preparation complete. Exiting.")
        return

    # 2. Train Model
    print("\n[2/2] Training Model...")
    dataset_yaml = os.path.abspath("dataset/data.yaml")
    
    trainer = ModelTrainer()
    best_model = trainer.train(data_path=dataset_yaml, epochs=args.epochs)
    
    if best_model:
        print(f"\nSUCCESS: New model accessible at {best_model}")
        print("Update your config or pipeline to use this new model.")

if __name__ == "__main__":
    main()
