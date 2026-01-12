from typing import Dict


def render_template(document_type: str, metadata: Dict[str, str]) -> str:
    """Return a simple Vietnamese template filled with metadata (fallback).
    Supported document_type values:
      - "Đơn Khiếu Nại"
      - "Hợp Đồng Thuê Nhà"
      - "Đơn xin Việc"
      - "Đơn tố cáo"
    """
    m = {k: v for k, v in metadata.items()} if metadata else {}
    date = m.get("date", m.get("ngay", "[ngày/tháng/năm]"))
    name = m.get("name", m.get("ten", "[Họ và tên]") )
    address = m.get("address", m.get("dia_chi", "[Địa chỉ]") )

    if document_type == "Đơn Khiếu Nại":
        subject = m.get("subject", "Về việc ...")
        details = m.get("details", "Mô tả nội dung khiếu nại ở đây.")
        return (
            "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n"
            "Độc lập - Tự do - Hạnh phúc\n\n"
            "ĐƠN KHIẾU NẠI\n\n"
            f"Kính gửi: {m.get('recipient','[Tên cơ quan/đơn vị]')}\n"
            f"Họ và tên: {name}\n"
            f"Địa chỉ: {address}\n"
            f"Ngày: {date}\n\n"
            f"Nội dung khiếu nại: {subject}\n\n"
            f"Chi tiết: {details}\n\n"
            "Kính đề nghị cơ quan xem xét và giải quyết.\n\n"
            f"Người khiếu nại\n{ name }")

    if document_type == "Hợp Đồng Thuê Nhà":
        landlord = m.get("landlord", "[Bên cho thuê]")
        tenant = m.get("tenant", "[Bên thuê]")
        rent = m.get("rent", "[Số tiền thuê]")
        duration = m.get("duration", "[Thời hạn thuê]")
        address_house = m.get("property_address", "[Địa chỉ nhà]")
        return (
            "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n"
            "Độc lập - Tự do - Hạnh phúc\n\n"
            "HỢP ĐỒNG THUÊ NHÀ\n\n"
            f"Bên cho thuê: {landlord}\n"
            f"Bên thuê: {tenant}\n"
            f"Địa chỉ bất động sản: {address_house}\n"
            f"Giá thuê: {rent}\n"
            f"Thời hạn: {duration}\n\n"
            "Các điều khoản: \n1. Mục đích sử dụng\n2. Thanh toán\n3. Quyền và nghĩa vụ của các bên\n\n"
            "Ký: \nBên cho thuê:\nBên thuê:")

    if document_type == "Đơn xin Việc":
        position = m.get("position", "[Vị trí ứng tuyển]")
        company = m.get("company", "[Tên công ty]")
        education = m.get("education", "[Trình độ học vấn]")
        skills = m.get("skills", "[Kỹ năng nổi bật]")
        content = m.get("content", "Tôi xin ứng tuyển vào vị trí...\nTôi cam kết...")
        return (
            "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n"
            "Độc lập - Tự do - Hạnh phúc\n\n"
            "ĐƠN XIN VIỆC\n\n"
            f"Kính gửi: {company}\n"
            f"Họ và tên: {name}\n"
            f"Địa chỉ: {address}\n"
            f"Vị trí ứng tuyển: {position}\n"
            f"Trình độ: {education}\n"
            f"Kỹ năng: {skills}\n\n"
            f"Nội dung: {content}\n\n"
            "Kính mong Nhà tuyển dụng xem xét.\n\n"
            f"Người làm đơn\n{ name }")

    if document_type == "Đơn tố cáo":
        accused = m.get("accused", "[Người/bên bị tố cáo]")
        incident = m.get("incident", "Mô tả sự việc vi phạm")
        evidence = m.get("evidence", "Các chứng cứ (nếu có)")
        return (
            "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n"
            "Độc lập - Tự do - Hạnh phúc\n\n"
            "ĐƠN TỐ CÁO\n\n"
            f"Kính gửi: {m.get('recipient','[Tên cơ quan/đơn vị]')}\n"
            f"Người tố cáo: {name}\n"
            f"Địa chỉ: {address}\n\n"
            f"Nội dung tố cáo liên quan đến: {accused}\n"
            f"Sự việc: {incident}\n"
            f"Chứng cứ: {evidence}\n\n"
            "Kính đề nghị cơ quan chức năng làm rõ và xử lý theo quy định pháp luật.\n\n"
            f"Người tố cáo\n{ name }")

    # Default generic document
    return (
        "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n"
        "Độc lập - Tự do - Hạnh phúc\n\n"
        f"VĂN BẢN: {document_type}\n\n"
        f"Người/Đơn vị: {name}\n"
        f"Địa chỉ: {address}\n"
        f"Nội dung: {m.get('content','[Nội dung]')}\n\n"
        f"Ký: {name}")
