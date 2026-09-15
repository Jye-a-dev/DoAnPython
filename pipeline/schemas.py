from typing import Any, List, Optional
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Normalized or absolute coordinate box for a detected object."""
    xmin: float = Field(..., description="Left pixel coordinate")
    ymin: float = Field(..., description="Top pixel coordinate")
    xmax: float = Field(..., description="Right pixel coordinate")
    ymax: float = Field(..., description="Bottom pixel coordinate")


class ObjectItem(BaseModel):
    """Metadata for a single detected entity."""
    name: str = Field(..., description="Original COCO class name (e.g., person, car)")
    label_vi: str = Field(..., description="Vietnamese translated label")
    confidence: float = Field(..., description="Model detection confidence score between 0 and 1")
    box: BoundingBox = Field(..., description="Object bounding box coordinates")


class DetectionResult(BaseModel):
    """Standardized JSON response payload for the detection pipeline."""
    timestamp: str = Field(..., description="ISO 8601 detection timestamp")
    total_objects: int = Field(..., description="Total count of detected entities")
    objects: List[ObjectItem] = Field(default_factory=list, description="Array of detected objects")
    summary: str = Field(..., description="Natural language Vietnamese summary")
    image_url: str = Field(..., description="Accessible URL for the annotated image")
    audio_url: Optional[str] = Field(default=None, description="Accessible stream URL for the synthesized TTS speech")

    def __iter__(self):
        return iter((self.objects, self.summary))

    def __getitem__(self, index: int) -> Any:
        return (self.objects, self.summary)[index]


class HistoryItem(BaseModel):
    """Single history record entry."""
    id: int
    created_at: str
    image_url: str
    summary: str
    json_data: Any
    audio_url: str


class HistoryResponse(BaseModel):
    """List response containing recent detection records."""
    total: int
    records: List[HistoryItem]

