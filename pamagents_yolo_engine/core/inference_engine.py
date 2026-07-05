import torch
from ultralytics import YOLOE

class YoloDetector:
    def __init__(self, model_path="yoloe-26s-seg-pf.pt"):
        # Load the YOLOE model
        self.model = YOLOE(model_path)
        
        # Explicitly move to GPU and enable FP16 if CUDA is available
        if torch.cuda.is_available():
            self.model.to('cuda')
            
            # Use Half-Precision (FP16) to save VRAM and speed up inference
            # We don't apply half() to TensorRT engines as their precision is pre-compiled
            if not str(model_path).endswith('.engine'):
                self.model.half()
            print("Model initialized on CUDA with FP16 enabled (if applicable).")
        else:
            print("Warning: CUDA is not available. Running on CPU.")

    def detect(self, frame, confidence_threshold=0.5):
        # Run inference using Ultralytics
        results = self.model(frame, conf=confidence_threshold, verbose=False)
        
        detections = []
        for result in results:
            for box in result.boxes:
                # Extract coordinates and cast to int
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = box.conf[0].item()
                cls_id = int(box.cls[0].item())
                label = self.model.names[cls_id]
                
                detections.append({
                    "label": label,
                    "confidence": conf,
                    "bbox_xyxy": [int(x1), int(y1), int(x2), int(y2)]
                })
                
        return detections
