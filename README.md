# NeuroOps: Advanced Neural Operations Platform

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)
![YOLO](https://img.shields.io/badge/AI-YOLOv8%2Fv11-orange.svg)
![Qdrant](https://img.shields.io/badge/Vector_DB-Qdrant-red.svg)
![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)

## 📋 Overview

**NeuroOps** is a cutting-edge computer vision and operations command center designed for high-performance surveillance, real-time analytics, and intelligent decision-making. By integrating state-of-the-art object detection, biometric analysis, and vector-based semantic search, NeuroOps provides a unified interface for monitoring complex environments.

The platform relies on a robust active learning loop, ensuring that the AI models continuously evolve and adapt to new scenarios by interacting with labeling backends like Label Studio.

## ✨ Key Features

- **🚀 Real-Time Object Detection**: High-speed inference using advanced YOLO models (e.g., `yolo26n`) for detecting diverse objects in live video feeds.
- **👤 Biometric Recognition**: Integrated engine for face detection, recognition, and analysis, enabling secure access control and identity tracking.
- **🧠 Semantic Search Engine**: Utilizes **Qdrant** and **Sentence Transformers** to index visual data, allowing users to search for objects, events, or specific attributes using natural language (e.g., "red car in the parking lot").
- **💻 Modern Command Dashboard**: A responsive, dark-themed GUI built with **PyQt6**, featuring:
  - Live multi-camera grid views.
  - Interactive rule editors for setting up alerts.
  - Real-time event logs and analytics charts.
- **🔄 Active Learning Pipeline**: Automated uncertainty sampling and data export to **Label Studio**, creating a closed-loop system for continuous model improvement.
- **📄 Optical Character Recognition (OCR)**: Seamless pipeline for extracting text from scenes, useful for license plate reading or document logging.
- **📹 Universal Stream Support**: Compatible with RTSP, HTTP, and local video files, powered by `imageio` and `FFmpeg`.

## 🛠️ Technology Stack

- **Core**: Python 3.10+
- **Interface**: PyQt6, PyQt6-WebEngine
- **Computer Vision**: Ultralytics YOLO, OpenCV, Pillow, Av
- **AI & NLP**: LangChain, SentenceTransformers
- **Database**: SQLAlchemy (Relational), Qdrant (Vector)
- **OCR**: EasyOCR

## ⚙️ Installation

### Prerequisites

Ensure you have **Python 3.10+** installed. It is recommended to use a virtual environment.

### Steps

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-username/NeuroOps.git
    cd NeuroOps
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Setup Database**
    Ensure your database configurations are set. The system initializes necessary tables on first run.

## 🚀 Usage

To launch the NeuroOps dashboard:

```bash
python src/main.py
```

### Dashboard Navigation
- **Dashboard**: Main view with analytics and system health.
- **Cameras**: Manage and view live streams.
- **Search**: Perform semantic searches across recorded footage.
- **Rules**: Define logic for automated alerts (e.g., "If Person detected in Zone A, trigger Alarm").

## 📂 Project Structure

```
NeuroOps/
├── src/
│   ├── ai/                 # Core AI logic (Detector, Pipeline, Biometrics)
│   ├── ui/                 # PyQt6 Widgets and Windows
│   ├── data/               # Database Models and Schemas
│   ├── active_learning/    # Loop for Label Studio integration
│   ├── decision_engine/    # Logic for rules and alerts
│   └── main.py             # Application Entry Point
├── configs/                # Configuration files
├── weights/                # Model weights (YOLO, etc.)
├── database/               # SQL and Vector DB storage
├── tests/                  # Unit and Integration tests
└── requirements.txt        # Project dependencies
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---
*Built for the Future of Neural Operations.*
