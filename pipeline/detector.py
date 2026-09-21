import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import torch
from ultralytics import YOLO

try:
    from pipeline.schemas import BoundingBox, DetectionResult, ObjectItem
except ImportError:
    from .schemas import BoundingBox, DetectionResult, ObjectItem

# Ánh xạ từ điển 80 lớp COCO sang Tiếng Việt chuẩn hóa
COCO_VI_MAP: Dict[str, str] = {
    "person": "người", "bicycle": "xe đạp", "car": "ô tô", "motorcycle": "xe máy",
    "airplane": "máy bay", "bus": "xe buýt", "train": "tàu hỏa", "truck": "xe tải",
    "boat": "thuyền", "traffic light": "đèn giao thông", "fire hydrant": "trụ cứu hỏa",
    "stop sign": "biển dừng", "parking meter": "đồng hồ đỗ xe", "bench": "ghế dài",
    "bird": "chim", "cat": "mèo", "dog": "chó", "horse": "ngựa", "sheep": "cừu",
    "cow": "bò", "elephant": "voi", "bear": "gấu", "zebra": "ngựa vằn",
    "giraffe": "hươu cao cổ", "backpack": "ba lô", "umbrella": "cái ô",
    "handbag": "túi xách", "tie": "cà vạt", "suitcase": "va li", "frisbee": "đĩa bay",
    "skis": "ván trượt tuyết", "snowboard": "ván trượt tuyết", "sports ball": "bóng thể thao",
    "kite": "diều", "baseball bat": "gậy bóng chày", "baseball glove": "găng tay bóng chày",
    "skateboard": "ván trượt", "surfboard": "ván lướt sóng", "tennis racket": "vợt tennis",
    "bottle": "chai nước", "wine glass": "ly rượu", "cup": "cái cốc", "fork": "cái nĩa",
    "knife": "con dao", "spoon": "cái thìa", "bowl": "cái bát", "banana": "quả chuối",
    "apple": "quả táo", "sandwich": "bánh mì kẹp", "orange": "quả cam", "broccoli": "súp lơ",
    "carrot": "củ cà rốt", "hot dog": "bánh mì xúc xích", "pizza": "bánh pizza",
    "donut": "bánh donut", "cake": "bánh ngọt", "chair": "cái ghế", "couch": "ghế sofa",
    "potted plant": "chậu cây", "bed": "cái giường", "dining table": "bàn ăn",
    "toilet": "bồn cầu", "tv": "ti vi", "laptop": "máy tính xách tay",
    "mouse": "chuột máy tính", "remote": "điều khiển", "keyboard": "bàn phím",
    "cell phone": "điện thoại", "microwave": "lò vi sóng", "oven": "lò nướng",
    "toaster": "máy nướng bánh", "sink": "bồn rửa", "refrigerator": "tủ lạnh",
    "book": "cuốn sách", "clock": "đồng hồ", "vase": "bình hoa", "scissors": "cái kéo",
    "teddy bear": "gấu bông", "hair drier": "máy sấy tóc", "toothbrush": "bàn chải đánh răng"
}


def resolve_model_weights() -> str:
    """Xác định đường dẫn file trọng số cục bộ tại thư mục gốc."""
    pipeline_dir = Path(__file__).resolve().parent
    project_root = pipeline_dir.parent

    # Thứ tự ưu tiên nạp trọng số cục bộ: pipeline/ -> project_root -> current directory
    candidates = [
        pipeline_dir / "yolo11m.pt",
        pipeline_dir / "yolov8m.pt",
        project_root / "yolo11m.pt",
        project_root / "yolov8m.pt",
        Path("yolo11m.pt").resolve(),
        Path("yolov8m.pt").resolve(),
    ]
    for p in candidates:
        if p.exists() and p.is_file() and p.stat().st_size > 10_000_000:
            return str(p)

    # Fallback tên mô hình nếu môi trường cho phép tải động
    return os.getenv("YOLO_MODEL_NAME", "yolo11m.pt")


def load_unicode_font(font_size: int = 16) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Tự động duyệt font hệ thống hỗ trợ ký tự UTF-8 Tiếng Việt."""
    font_paths = [
        "arial.ttf",
        "tahoma.ttf",
        "segoeui.ttf",
        "DejaVuSans.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/tahoma.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, font_size)
        except OSError:
            continue
    return ImageFont.load_default()


class ObjectDetector:
    """Singleton ObjectDetector encapsulating YOLO inference, device routing, and Vietnamese annotation."""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ObjectDetector, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name: Optional[str] = None, conf_thresh: float = 0.35) -> None:
        if getattr(self, "_initialized", False):
            return
        self.conf_thresh = conf_thresh
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_path = resolve_model_weights() if model_name is None else model_name
        self.model = YOLO(self.model_path)
        self.model_name = Path(self.model_path).name
        self._initialized = True

    def detect_objects(
        self,
        image_path: str,
        output_destination: str,
        base_url_prefix: str = "/static/uploads"
    ) -> Tuple[DetectionResult, str]:
        """
        Synchronous, CPU/GPU-bound YOLO detection.
        Renders bounding boxes with UTF-8 Vietnamese diacritics via PIL and returns typed DetectionResult.
        """
        # Determine output file path and accessible web URL
        if os.path.isdir(output_destination) or not any(output_destination.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]):
            os.makedirs(output_destination, exist_ok=True)
            filename = Path(image_path).name
            annotated_filename = f"annotated_{filename}"
            annotated_path = os.path.join(output_destination, annotated_filename)
            annotated_url = f"{base_url_prefix}/{annotated_filename}"
        else:
            output_dir = os.path.dirname(output_destination)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            annotated_path = output_destination
            annotated_filename = Path(output_destination).name
            annotated_url = f"{base_url_prefix}/{annotated_filename}"

        results = self.model.predict(
            source=image_path,
            device=self.device,
            conf=self.conf_thresh,
            verbose=False
        )[0]

        image = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(image)
        font = load_unicode_font(font_size=max(14, int(image.height * 0.02)))

        detected_items: List[ObjectItem] = []
        names = results.names

        for box in results.boxes:
            cls_id = int(box.cls[0].item())
            raw_label = names.get(cls_id, f"class_{cls_id}")
            conf = float(box.conf[0].item())
            coords = [float(c) for c in box.xyxy[0].tolist()]
            xmin, ymin, xmax, ymax = coords

            label_vi = COCO_VI_MAP.get(raw_label, raw_label)
            detected_items.append(
                ObjectItem(
                    name=raw_label,
                    label_vi=label_vi,
                    confidence=round(conf, 3),
                    box=BoundingBox(
                        xmin=round(xmin, 1),
                        ymin=round(ymin, 1),
                        xmax=round(xmax, 1),
                        ymax=round(ymax, 1),
                    )
                )
            )

            # Draw bounding box and Vietnamese UTF-8 text label
            draw.rectangle([xmin, ymin, xmax, ymax], outline="#00FF00", width=3)
            display_text = f"{label_vi} {conf:.2f}"
            bbox_text = draw.textbbox((xmin, ymin), display_text, font=font)
            text_w = bbox_text[2] - bbox_text[0]
            text_h = bbox_text[3] - bbox_text[1]

            label_ymin = max(0, ymin - text_h - 6)
            draw.rectangle(
                [xmin, label_ymin, xmin + text_w + 8, label_ymin + text_h + 6],
                fill="#00FF00"
            )
            draw.text((xmin + 4, label_ymin + 1), display_text, fill="#000000", font=font)

        image.save(annotated_path, quality=95)

        if not detected_items:
            summary = "Không phát hiện đối tượng rõ ràng nào trong khung hình."
        else:
            counts = Counter([item.label_vi for item in detected_items])
            details = [f"{qty} {name}" for name, qty in counts.items()]
            summary = f"Phát hiện tổng cộng {len(detected_items)} đối tượng gồm: " + ", ".join(details) + "."

        detection_result = DetectionResult(
            timestamp=datetime.now(timezone.utc).isoformat(),
            total_objects=len(detected_items),
            objects=detected_items,
            summary=summary,
            image_url=annotated_url,
            annotated_image_url=annotated_url,
            audio_url=None
        )

        return detection_result, annotated_path


def get_detector() -> ObjectDetector:
    """Thread-safe singleton accessor for ObjectDetector."""
    return ObjectDetector()
