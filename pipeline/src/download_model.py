import os
import sys
import argparse
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

DEFAULT_MODEL = "google/flan-t5-base"
SAVE_DIR = os.path.join(os.path.dirname(__file__), "..", "models_weights")

def download(model_id: str = DEFAULT_MODEL):
    target_path = os.path.join(SAVE_DIR, model_id.split("/")[-1])
    print(f"[*] Bắt đầu tải model '{model_id}' về: {target_path}")
    
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_id)
    
    tokenizer.save_pretrained(target_path)
    model.save_pretrained(target_path)
    print(f"[+] Hoàn tất! Model đã sẵn sàng chạy offline tại: {target_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tải model offline từ Hugging Face")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="Tên model trên Hugging Face Hub")
    args = parser.parse_args()
    download(args.model)
