import sys
import os
import cv2
import numpy as np

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.ai.ocr import OCRProcessor
from src.data.db_manager import DatabaseManager
from src.data.models import TextDetection, init_db, Base
from src.core.search_engine import SearchEngine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def log(msg):
    print(msg)
    with open("test_results.log", "a", encoding='utf-8') as f:
        f.write(msg + "\n")

def test_ocr_and_search():
    if os.path.exists("test_results.log"):
        os.remove("test_results.log")
        
    log("--- Testing OCR and Search ---")
    
    # 1. Test OCR Processor
    log("\n1. Testing OCRProcessor...")
    ocr = OCRProcessor()
    
    # Create a dummy image with text
    img = np.zeros((200, 600, 3), dtype=np.uint8)
    cv2.putText(img, 'HELLO WORLD', (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 4)
    # Save for manual inspection if needed
    # cv2.imwrite('test_ocr.png', img)
    
    detections = ocr.detect_text(img)
    log(f"Detections: {detections}")
    
    if not detections:
        log("FAILED: No text detected.")
        return
        
    found_text = False
    for d in detections:
        if "HELLO" in d['text'] or "WORLD" in d['text']:
            found_text = True
            break
            
    if found_text:
        log("SUCCESS: Text detected correctly.")
    else:
        log(f"FAILED: Expected 'HELLO WORLD', got {[d['text'] for d in detections]}")

    # 2. Test Database Insertion
    log("\n2. Testing Database Insertion...")
    # Use a temporary test DB
    test_db_path = os.path.join(os.path.dirname(__file__), 'test_neuroops.db')
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        
    engine = create_engine(f'sqlite:///{test_db_path}')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Mock DatabaseManager to return our session
    # (Since SearchEngine initializes its own DBManager, we need to monkeypatch or just rely on models)
    # Actually SearchEngine connects to the REAL DB defined in models.py logic usually.
    # To test logic cleanly without messing up proper DB, let's just insert into the REAL DB but with a dummy video ID.
    
    # Let's use the real DB path logic but a specific ID
    db = DatabaseManager()
    session = db.get_session()
    
    VIDEO_ID = 99999
    
    # Clean up first
    session.query(TextDetection).filter_by(video_id=VIDEO_ID).delete()
    session.commit()
    
    try:
        det = TextDetection(
            video_id=VIDEO_ID,
            frame_index=10,
            timestamp=0.5,
            text_content="SECRET_CODE_123",
            confidence=0.99,
            bbox_xyxy=[10, 10, 100, 50]
        )
        session.add(det)
        session.commit()
        log("SUCCESS: Inserted text detection.")
    except Exception as e:
        log(f"FAILED to insert: {e}")
        return

    # 3. Test Search
    log("\n3. Testing SearchEngine...")
    
    # Initialize engine for that video
    engine = SearchEngine(collection_suffix=str(VIDEO_ID))
    # We mock looking for "SECRET"
    
    results = engine.search("SECRET")
    log(f"Search Results: {results}")
    
    found = False
    for res in results:
        if "SECRET_CODE_123" in res['class_name']:
            found = True
            break
            
    if found:
        log("SUCCESS: Search found the text.")
    else:
        log("FAILED: Search did not find the text.")
        
    # Cleanup
    session.query(TextDetection).filter_by(video_id=VIDEO_ID).delete()
    session.commit()
    session.close()

if __name__ == "__main__":
    test_ocr_and_search()
