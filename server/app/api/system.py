"""
system.py — System Health & Status API endpoints (Tag: System).
GET /api/health: Healthcheck trạng thái Server, SQLite DB và ping Pipeline (/api/pi/health).
GET /api/system/status: Trả về chi tiết kết nối mạng, CPU/RAM và trạng thái Microservices.
"""

from __future__ import annotations

import os
import socket
import time
from importlib import import_module
from datetime import datetime, timezone
from flask import Blueprint, jsonify

try:
    psutil = import_module("psutil")
except ImportError:
    psutil = None
import sqlalchemy as sa
from app.core.database import db
from app.services.pipeline_manager import is_pipeline_healthy

system_bp = Blueprint("system", __name__, url_prefix="/api")

_SERVER_START_TIME = time.time()


@system_bp.route("/health", methods=["GET"])
def health_check():
    """
    Kiểm tra trạng thái hoạt động hệ thống và dịch vụ (GET /api/health)
    ---
    tags:
      - System
    summary: Healthcheck kiểm tra Server, SQLite Database và ping AI Pipeline
    responses:
      200:
        description: Trạng thái tổng quát của dịch vụ
        schema:
          type: object
          properties:
            status:
              type: string
              example: healthy
            database:
              type: string
              example: connected
            ai_pipeline:
              type: string
              example: ready
            timestamp:
              type: string
              example: "2026-10-28T02:00:00Z"
      500:
        description: Lỗi kết nối cơ sở dữ liệu hoặc hệ thống
    """
    db_status = "connected"
    status_code = 200

    try:
        db.session.execute(sa.text("SELECT 1")).scalar()
    except Exception as exc:
        db_status = f"unhealthy: {str(exc)}"
        status_code = 500

    pipeline_ok = is_pipeline_healthy()
    ai_status = "ready" if pipeline_ok else "unavailable"

    overall_status = "healthy" if db_status == "connected" else "degraded"

    return (
        jsonify(
            {
                "status": overall_status,
                "database": db_status,
                "ai_pipeline": ai_status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ),
        status_code,
    )


@system_bp.route("/system/status", methods=["GET"])
def system_status():
    """
    Báo cáo chi tiết tài nguyên CPU, RAM, mạng và Microservices (GET /api/system/status)
    ---
    tags:
      - System
    summary: Báo cáo metrics phần cứng, mạng và trạng thái các tiến trình Microservices
    responses:
      200:
        description: Thông tin chi tiết hệ điều hành, CPU, RAM và kết nối
        schema:
          type: object
          properties:
            server:
              type: object
            microservices:
              type: object
            hardware:
              type: object
            network:
              type: object
      500:
        description: Lỗi thu thập số liệu hệ thống
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=None) if psutil is not None else 0.0
        virtual_mem = psutil.virtual_memory() if psutil is not None else None
        total_mb = round(virtual_mem.total / (1024 * 1024), 2) if virtual_mem else 0.0
        avail_mb = (
            round(virtual_mem.available / (1024 * 1024), 2) if virtual_mem else 0.0
        )
        percent_used = virtual_mem.percent if virtual_mem else 0.0
        cpu_count = (
            psutil.cpu_count(logical=True)
            if psutil is not None
            else (os.cpu_count() or 1)
        )
        uptime_seconds = round(time.time() - _SERVER_START_TIME, 2)
        hostname = socket.gethostname()

        pipeline_ok = is_pipeline_healthy()

        net_conns = []
        if psutil is not None:
            try:
                net_addrs = psutil.net_if_addrs()
                for iface, addrs in net_addrs.items():
                    for addr in addrs:
                        if addr.family == socket.AF_INET:
                            net_conns.append({"interface": iface, "ip": addr.address})
            except Exception:
                pass

        return (
            jsonify(
                {
                    "server": {
                        "name": "Flashcard Backend Server",
                        "port": int(os.getenv("PORT", 3000)),
                        "hostname": hostname,
                        "uptime_seconds": uptime_seconds,
                        "status": "running",
                    },
                    "microservices": {
                        "database": {
                            "type": "SQLite 3NF",
                            "foreign_keys": "ENABLED (PRAGMA ON)",
                            "status": "connected",
                        },
                        "ai_pipeline": {
                            "port": int(os.getenv("PIPELINE_PORT", 8000)),
                            "health_endpoint": "http://127.0.0.1:8000/api/pi/health",
                            "status": "online" if pipeline_ok else "offline",
                        },
                    },
                    "hardware": {
                        "cpu_percent": cpu_percent,
                        "cpu_count": cpu_count,
                        "memory": {
                            "total_mb": total_mb,
                            "available_mb": avail_mb,
                            "percent_used": percent_used,
                        },
                    },
                    "network": {
                        "interfaces": net_conns,
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            200,
        )
    except Exception as exc:
        return jsonify({"error": f"Lỗi thu thập trạng thái hệ thống: {str(exc)}"}), 500
