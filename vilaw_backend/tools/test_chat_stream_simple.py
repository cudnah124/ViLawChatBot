#!/usr/bin/env python3
"""Simple test script to call POST /api/v1/contracts/draft with new schema.

Usage examples:
  python test_chat_stream_simple.py --base http://localhost:8000 --action draft_all
  python test_chat_stream_simple.py --base http://localhost:8000 --action draft --type "Đơn Khiếu Nại"

This script sends example metadata for four document types and prints brief response info.
"""
import argparse
import json
import requests
from textwrap import shorten


DEFAULT_BASE = "http://localhost:8000"


EXAMPLES = {
    "Đơn Khiếu Nại": {
        "recipient": "Ủy ban nhân dân phường X",
        "name": "Nguyễn Văn A",
        "address": "123 Đường Lê Lợi, Quận 1, TP. HCM",
        "date": "01/01/2025",
        "subject": "Khiếu nại về trục lợi phí dịch vụ",
        "details": "Tôi đã đóng phí nhưng không được hoàn trả dù đã chấm dứt dịch vụ...",
        "summary": "Khách hàng khiếu nại công ty cung cấp dịch vụ không hoàn trả phí sau khi chấm dứt, yêu cầu hoàn trả số tiền đã đóng."
    },
    "Hợp Đồng Thuê Nhà": {
        "landlord": "Ông Bùi Văn B",
        "tenant": "Bà Trần Thị C",
        "property_address": "45/6 Nguyễn Huệ, Quận 1, TP. HCM",
        "rent": "6.000.000 VND/tháng",
        "duration": "12 tháng",
        "summary": "Hợp đồng thuê nhà giữa Bùi Văn B (chủ nhà) và Trần Thị C (người thuê), thuê trong 12 tháng với mức thuê 6.000.000 VND/tháng."
    },
    "Đơn xin Việc": {
        "company": "Công ty TNHH ABC",
        "name": "Lê Thị D",
        "address": "78 Trần Phú, Hà Nội",
        "position": "Chuyên viên pháp chế",
        "education": "Cử nhân Luật",
        "skills": "Soạn thảo hợp đồng, Tư vấn pháp lý",
        "content": "Tôi xin ứng tuyển vào vị trí Chuyên viên pháp chế tại Công ty...",
        "summary": "Ứng viên Lê Thị D xin ứng tuyển vị trí Chuyên viên pháp chế, có kinh nghiệm soạn thảo hợp đồng và tư vấn pháp lý."
    },
    "Đơn tố cáo": {
        "recipient": "Cơ quan CSĐT Công an Quận Y",
        "name": "Phạm Văn E",
        "address": "9A Phố X, Thị xã Z",
        "accused": "Công ty XYZ",
        "incident": "Công ty XYZ đã thực hiện hành vi lừa đảo khi...",
        "evidence": "Hóa đơn, Biên bản giao nhận",
        "date": "02/02/2025"
        ,
        "summary": "Cá nhân tố cáo Công ty XYZ có hành vi lừa đảo trong giao dịch mua bán, đề nghị cơ quan điều tra xác minh."
    }
}


def post_draft(base_url: str, document_type: str, metadata: dict, timeout: int = 120):
    url = base_url.rstrip("/") + "/api/v1/contracts/draft"
    # `summary` is the main input; prefer explicit summary in metadata if present
    summary = metadata.pop("summary", "") if metadata else ""
    payload = {"document_type": document_type, "summary": summary, "metadata": metadata}
    try:
        r = requests.post(url, json=payload, timeout=timeout)
    except Exception as e:
        print(f"Request error for {document_type}: {e}")
        return None

    try:
        data = r.json()
    except Exception:
        print(f"Non-JSON response ({r.status_code}): {r.text[:200]}")
        return None

    print(f"--- {document_type} -> HTTP {r.status_code}")
    preview = data.get("content_preview") or data.get("content") or "(no preview)"
    print("Preview:", shorten(preview.replace('\n',' '), width=300))
    print("Download:", data.get("download_url"))
    print()
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=DEFAULT_BASE, help="Base URL of backend")
    parser.add_argument("--action", default="draft_all", choices=["draft_all", "draft"], help="Action to run")
    parser.add_argument("--type", help="Document type (if action=draft)")
    parser.add_argument("--metadata", help="JSON string of metadata (optional)")
    parser.add_argument("--req-timeout", type=int, default=120, help="HTTP request timeout in seconds (default 120)")
    args = parser.parse_args()

    base = args.base


    if args.action == "draft_all":
        for doc_type, meta in EXAMPLES.items():
            post_draft(base, doc_type, meta, timeout=args.req_timeout)
    else:
        if not args.type:
            print("--type is required when --action=draft")
            return
        meta = EXAMPLES.get(args.type, {})
        if args.metadata:
            try:
                user_meta = json.loads(args.metadata)
                meta.update(user_meta)
            except Exception as e:
                print("Invalid --metadata JSON:", e)
                return
        post_draft(base, args.type, meta, timeout=args.req_timeout)


if __name__ == "__main__":
    main()
