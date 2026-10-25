#!/usr/bin/env bash
# curl_test.sh — Kiểm tra endpoint POST /api/pi/generate
# Đảm bảo AI Pipeline Microservice đang chạy trên port 8000 trước khi chạy script này.
# Khởi động: cd pipeline && python app/main.py
#
# Sử dụng: bash curl_test.sh [HOST:PORT]
# Mặc định: HOST=127.0.0.1:8000

HOST="${1:-127.0.0.1:8000}"
URL="http://$HOST/api/pi/generate"

echo "=================================================="
echo "  TEST: POST $URL"
echo "  Văn bản: Quang hợp (Photosynthesis)"
echo "=================================================="

curl -s -X POST "$URL" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Quang hợp là quá trình mà thực vật xanh, tảo và một số vi khuẩn sử dụng ánh sáng mặt trời để chuyển đổi carbon dioxide (CO2) và nước (H2O) thành glucose và oxy. Quá trình này xảy ra chủ yếu trong lục lạp, cụ thể là ở màng thylakoid và chất nền stroma. Diệp lục tố (chlorophyll) là sắc tố chính hấp thụ ánh sáng. Phương trình tổng quát: 6CO2 + 6H2O + ánh sáng → C6H12O6 + 6O2. Quang hợp gồm hai pha: pha sáng (xảy ra ở thylakoid) và pha tối hay chu trình Calvin (xảy ra ở stroma).",
    "max_cards": 5,
    "max_words_per_chunk": 150
  }' | python -m json.tool 2>/dev/null || echo "Lỗi: Kiểm tra service có đang chạy không (port 8000)"

