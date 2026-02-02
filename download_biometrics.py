import os
import requests

WEIGHTS_DIR = "NeuroOps/weights"
os.makedirs(WEIGHTS_DIR, exist_ok=True)

# Updated URLs (Verified)
URLS = {
    # Source: yakhyo/face-anti-spoofing (GitHub Release 'weights')
    "MiniFASNetV2.pth": "https://github.com/yakhyo/face-anti-spoofing/releases/download/weights/MiniFASNetV2.pth",
    
    # Source: huggingface.co/VishalMishraTss/AdaFace (Public)
    "adaface_ir50_ms1mv2.ckpt": "https://huggingface.co/VishalMishraTss/AdaFace/resolve/main/adaface_ir50_ms1mv2.ckpt",
    
    # Source: huggingface.co/deepghs/yolo-face (Public)
    "yolov8n-face.pt": "https://huggingface.co/deepghs/yolo-face/resolve/main/yolov8n-face/model.pt"
}

def download_file(url, filename):
    path = os.path.join(WEIGHTS_DIR, filename)
    
    # Check if exists (and has size > 10KB to avoid empty fails)
    if os.path.exists(path) and os.path.getsize(path) > 10240:
        print(f"[SKIP] {filename} already exists.")
        return

    print(f"[DOWNLOAD] Downloading {filename}...")
    try:
        response = requests.get(url, stream=True, allow_redirects=True)
        response.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"[SUCCESS] Saved to {path}")
    except Exception as e:
        print(f"[ERROR] Failed to download {filename}: {e}")
        # Cleanup partial
        if os.path.exists(path):
            os.remove(path)

if __name__ == "__main__":
    print(f"Downloading biometric weights to {WEIGHTS_DIR}...")
    
    for name, url in URLS.items():
        download_file(url, name)
        
    print("\nDownload complete. Run 'python NeuroOps/src/main.py' to test.")
