from pydantic import BaseModel
from typing import List

class ApdViolation(BaseModel):
    person_bbox: List[int] # [x1, y1, x2, y2]
    missing_apd: List[str] # e.g. ["helmet", "vest", "shoe"]

class ApdDetectionResult(BaseModel):
    camera_id: str
    timestamp: str
    violations: List[ApdViolation]

