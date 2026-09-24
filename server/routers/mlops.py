import json
from datetime import datetime, timezone
from flask import request, Response
from flask_restx import Namespace, Resource, fields
from sqlalchemy import func
from sqlmodel import select

from server.core.security import admin_required
from server.database import get_db_session
from server.models.ocr_record import OCRRecord
from server.models.ocr_review import OCRReview

ns_mlops = Namespace("MLOps & Engine Telemetry", path="/api/v1/mlops", description="Model drift monitoring, OOV vocabulary alerts, and error clustering")

# 80 COCO Standard Classes
COCO_CLASSES = {
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
    "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
    "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
    "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
    "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
    "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
}

COCO_VI_CLASSES = {
    "người", "xe đạp", "ô tô", "xe máy", "máy bay", "xe buýt", "tàu hỏa", "xe tải",
    "thuyền", "đèn giao thông", "trụ cứu hỏa", "biển dừng", "đồng hồ đỗ xe", "ghế dài",
    "chim", "mèo", "chó", "ngựa", "cừu", "bò", "voi", "gấu", "ngựa vằn",
    "hươu cao cổ", "ba lô", "cái ô", "túi xách", "cà vạt", "va li", "đĩa bay",
    "ván trượt tuyết", "bóng thể thao", "diều", "gậy bóng chày", "găng tay bóng chày",
    "ván trượt", "ván lướt sóng", "vợt tennis", "chai nước", "ly rượu", "cái cốc",
    "cái nĩa", "con dao", "cái thìa", "cái bát", "quả chuối", "quả táo", "bánh mì kẹp",
    "quả cam", "súp lơ", "củ cà rốt", "bánh mì xúc xích", "bánh pizza", "bánh donut",
    "bánh ngọt", "cái ghế", "ghế sofa", "chậu cây", "cái giường", "bàn ăn", "bồn cầu",
    "ti vi", "máy tính xách tay", "chuột máy tính", "điều khiển", "bàn phím", "điện thoại",
    "lò vi sóng", "lò nướng", "máy nướng bánh", "bồn rửa", "tủ lạnh", "cuốn sách",
    "đồng hồ", "bình hoa", "cái kéo", "gấu bông", "máy sấy tóc", "bàn chải đánh răng"
}

oov_term_model = ns_mlops.model("OOVTermItem", {
    "term": fields.String,
    "occurrences": fields.Integer,
    "last_seen": fields.String,
    "suggested_category": fields.String
})

retrain_queue_item_model = ns_mlops.model("RetrainQueueItem", {
    "record_id": fields.String,
    "image_url": fields.String,
    "raw_detected_text": fields.String,
    "corrected_text": fields.String,
    "confidence": fields.Float,
    "reason": fields.String,
    "reviewed_at": fields.String
})

drift_alert_response_model = ns_mlops.model("ModelDriftResponse", {
    "drift_score": fields.Float,
    "total_analyzed": fields.Integer,
    "low_confidence_count": fields.Integer,
    "corrected_count": fields.Integer,
    "oov_terms": fields.List(fields.Nested(oov_term_model)),
    "retrain_queue": fields.List(fields.Nested(retrain_queue_item_model))
})

error_cluster_item_model = ns_mlops.model("ErrorClusterItem", {
    "cluster_id": fields.String,
    "cluster_name": fields.String,
    "description": fields.String,
    "count": fields.Integer,
    "record_ids": fields.List(fields.String)
})

error_clusters_response_model = ns_mlops.model("ErrorClustersResponse", {
    "clusters": fields.List(fields.Nested(error_cluster_item_model)),
    "total_flagged": fields.Integer
})


@ns_mlops.route("/drift-alert")
class ModelDriftAlert(Resource):
    @ns_mlops.doc("get_drift_alerts", description="Identify low-confidence records, OOV terms, and retrain queue")
    @ns_mlops.response(200, "Success", drift_alert_response_model)
    def get(self):
        with get_db_session() as session:
            records = session.exec(select(OCRRecord).order_by(OCRRecord.created_at.desc()).limit(200)).all()
            reviews = session.exec(select(OCRReview)).all()
            review_map = {r.record_id: r for r in reviews}

            total_analyzed = len(records)
            low_conf_count = 0
            corrected_count = 0
            oov_counter = {}
            retrain_candidates = []

            for rec in records:
                objs = []
                try:
                    objs = json.loads(rec.ocr_json_data) if isinstance(rec.ocr_json_data, str) else rec.ocr_json_data
                except Exception:
                    objs = []

                min_conf = 1.0
                if objs and isinstance(objs, list):
                    confs = [float(o.get("confidence", 1.0)) for o in objs if isinstance(o, dict)]
                    if confs:
                        min_conf = min(confs)

                is_low_conf = min_conf < 0.40
                if is_low_conf:
                    low_conf_count += 1

                rev = review_map.get(rec.id)
                is_corrected = False
                if rev and rev.corrected_text and rev.corrected_text.strip().lower() != rec.raw_detected_text.strip().lower():
                    is_corrected = True
                    corrected_count += 1

                    # Check for Out-of-Vocabulary words
                    words = rev.corrected_text.strip().lower().split()
                    for w in words:
                        w_clean = w.strip(",.!?\"'#")
                        if len(w_clean) >= 3 and w_clean not in COCO_CLASSES and w_clean not in COCO_VI_CLASSES:
                            oov_counter[w_clean] = oov_counter.get(w_clean, 0) + 1

                if is_low_conf or is_corrected:
                    reason = "Admin đã sửa nhãn (Misclassification)" if is_corrected else f"Độ tin cậy thấp ({round(min_conf * 100, 1)}%)"
                    retrain_candidates.append({
                        "record_id": rec.id,
                        "image_url": f"/api/v1/media/records/{rec.id}/image",
                        "raw_detected_text": rec.raw_detected_text,
                        "corrected_text": rev.corrected_text if rev else rec.raw_detected_text,
                        "confidence": round(min_conf, 2),
                        "reason": reason,
                        "reviewed_at": rev.reviewed_at.isoformat() if rev else rec.created_at.isoformat()
                    })

            drift_score = round(((low_conf_count + corrected_count) / max(1, total_analyzed)) * 100, 1)

            sorted_oov = [
                {
                    "term": term,
                    "occurrences": count,
                    "last_seen": datetime.now(timezone.utc).isoformat(),
                    "suggested_category": "Phụ kiện mới" if "sạc" in term or "tai" in term else "Vật dụng mở rộng"
                }
                for term, count in sorted(oov_counter.items(), key=lambda x: x[1], reverse=True)[:15]
            ]

            return {
                "drift_score": drift_score,
                "total_analyzed": total_analyzed,
                "low_confidence_count": low_conf_count,
                "corrected_count": corrected_count,
                "oov_terms": sorted_oov,
                "retrain_queue": retrain_candidates[:20]
            }, 200


@ns_mlops.route("/error-clusters")
class ErrorClusters(Resource):
    @ns_mlops.doc("get_error_clusters", description="Categorize inference errors into distinct clusters")
    @ns_mlops.response(200, "Success", error_clusters_response_model)
    def get(self):
        with get_db_session() as session:
            records = session.exec(select(OCRRecord).order_by(OCRRecord.created_at.desc()).limit(150)).all()
            reviews = session.exec(select(OCRReview)).all()
            review_map = {r.record_id: r for r in reviews}

            clusters = {
                "low_light": {
                    "cluster_id": "low_light",
                    "cluster_name": "Ảnh thiếu sáng / Tương phản kém",
                    "description": "Ảnh có độ phơi sáng thấp hoặc bóng tối bao phủ dẫn đến giảm độ tin cậy nhận diện.",
                    "record_ids": []
                },
                "occlusion": {
                    "cluster_id": "occlusion",
                    "cluster_name": "Vật thể bị che khuất / Bbox nhỏ",
                    "description": "Vật thể bị khuất một phần bởi đồ vật khác hoặc diện tích bounding box < 5% khung hình.",
                    "record_ids": []
                },
                "overlap": {
                    "cluster_id": "overlap",
                    "cluster_name": "Đa vật thể chồng chéo",
                    "description": "Mật độ vật thể cao, các khung viền đè lên nhau gây khó khăn cho việc phân loại riêng rẽ.",
                    "record_ids": []
                },
                "misclassification": {
                    "cluster_id": "misclassification",
                    "cluster_name": "Nhầm lẫn phân loại (Admin đã sửa)",
                    "description": "Mô hình nhận diện sai tên đối tượng và đã được quản trị viên hiệu chỉnh nhãn đúng.",
                    "record_ids": []
                }
            }

            for rec in records:
                objs = []
                try:
                    objs = json.loads(rec.ocr_json_data) if isinstance(rec.ocr_json_data, str) else rec.ocr_json_data
                except Exception:
                    objs = []

                rev = review_map.get(rec.id)
                if rev and rev.corrected_text and rev.corrected_text.strip().lower() != rec.raw_detected_text.strip().lower():
                    clusters["misclassification"]["record_ids"].append(rec.id)
                    continue

                if len(objs) >= 4:
                    clusters["overlap"]["record_ids"].append(rec.id)
                elif any(float(o.get("confidence", 1.0)) < 0.40 for o in objs if isinstance(o, dict)):
                    clusters["low_light"]["record_ids"].append(rec.id)
                elif any(isinstance(o, dict) and o.get("box") and ((o["box"].get("xmax", 100) - o["box"].get("xmin", 0)) < 40) for o in objs):
                    clusters["occlusion"]["record_ids"].append(rec.id)

            cluster_list = [
                {
                    "cluster_id": c["cluster_id"],
                    "cluster_name": c["cluster_name"],
                    "description": c["description"],
                    "count": len(c["record_ids"]),
                    "record_ids": c["record_ids"]
                }
                for c in clusters.values()
            ]

            total_flagged = sum(c["count"] for c in cluster_list)
            return {
                "clusters": cluster_list,
                "total_flagged": total_flagged
            }, 200


@ns_mlops.route("/export-dataset")
class ExportDataset(Resource):
    @ns_mlops.doc("export_dataset", description="Export training manifest for fine-tuning YOLO11")
    @ns_mlops.param("cluster_id", "Filter by specific error cluster", type=str)
    def get(self):
        cluster_id = request.args.get("cluster_id")
        with get_db_session() as session:
            records = session.exec(select(OCRRecord).order_by(OCRRecord.created_at.desc()).limit(100)).all()
            reviews = session.exec(select(OCRReview)).all()
            review_map = {r.record_id: r for r in reviews}

            dataset = []
            for rec in records:
                rev = review_map.get(rec.id)
                objs = []
                try:
                    objs = json.loads(rec.ocr_json_data) if isinstance(rec.ocr_json_data, str) else rec.ocr_json_data
                except Exception:
                    objs = []

                target_label = rev.corrected_text if rev else rec.raw_detected_text

                dataset.append({
                    "record_id": rec.id,
                    "target_annotation": target_label,
                    "raw_detected_text": rec.raw_detected_text,
                    "accuracy_score": rev.accuracy_score if rev else 0.8,
                    "status": rec.status,
                    "created_at": rec.created_at.isoformat(),
                    "objects": objs,
                    "image_url": f"/api/v1/media/records/{rec.id}/image"
                })

            manifest = {
                "version": "1.0.0",
                "format": "yolo11-custom-retrain",
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "total_samples": len(dataset),
                "cluster_filter": cluster_id or "all",
                "samples": dataset
            }

            json_bytes = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
            return Response(
                json_bytes,
                mimetype="application/json",
                headers={"Content-Disposition": "attachment; filename=yolo11_retrain_dataset.json"}
            )

