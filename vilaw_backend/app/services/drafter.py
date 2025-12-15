import os
from datetime import datetime
from docx import Document
from docx.shared import Pt
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.services.llm_engine import get_llm
from app.services.risk_checker import RiskCheckerService
from app.schemas.contract_schema import ContractDraftRequest

class DrafterService:
    def __init__(self):
        self.llm = get_llm(streaming=False)
        self.risk_checker = RiskCheckerService()

    async def draft_contract(self, data: ContractDraftRequest) -> dict:
        prompt = ChatPromptTemplate.from_template("""
        <|im_start|>system
        Bạn là Luật sư cao cấp tại Việt Nam. Nhiệm vụ: Soạn thảo văn bản pháp lý.
        
        YÊU CẦU NGHIÊM NGẶT:
        1. Cấu trúc chuẩn: Quốc hiệu -> Tên văn bản -> Căn cứ pháp lý -> Các điều khoản.
        2. Ngôn ngữ: Trang trọng, chính xác, khách quan.
        3. Tự động bổ sung các điều khoản tiêu chuẩn (Bất khả kháng, Giải quyết tranh chấp) để bảo vệ rủi ro.
        4. Trình bày rõ ràng: Điều 1, Điều 2...
        <|im_end|>
        
        <|im_start|>user
        Yêu cầu soạn thảo:
        - Loại văn bản: {contract_type}
        - Bên A: {party_a}
        - Bên B: {party_b}
        - Chi tiết điều khoản: {key_terms}
        <|im_end|>
        
        <|im_start|>assistant
        """)
        chain = prompt | self.llm | StrOutputParser()
        raw_content = await chain.ainvoke({
            "contract_type": data.contract_type,
            "party_a": data.party_a,
            "party_b": data.party_b,
            "key_terms": str(data.key_terms)
        })
        # 3. Chạy Risk Checker (Bây giờ nó trả về Dict chi tiết)
        from app.schemas.contract_schema import RiskAnalysisRequest
        risk_data_input = RiskAnalysisRequest(contract_type=data.contract_type, content=raw_content)
        risk_result_json = await self.risk_checker.analyze_document(risk_data_input)
        # Convert JSON result sang String tóm tắt cho Feature 2 (để đỡ sửa Schema Feature 2 nhiều)
        score = risk_result_json.get("overall_score", 0)
        high_risks = [r['issue'] for r in risk_result_json.get('risks', []) if r['severity'] == 'High']
        risk_summary = f"Điểm an toàn: {score}/100\n"
        if high_risks:
            risk_summary += "⚠️ CẢNH BÁO RỦI RO CAO:\n- " + "\n- ".join(high_risks)
        else:
            risk_summary += "✅ Văn bản khá an toàn."
        filename = self._save_docx(raw_content, data.contract_type)
        return {
            "content_preview": raw_content,
            "risk_report": risk_summary,
            "download_url": f"/static/docs/{filename}"
        }

    def _save_docx(self, content: str, doc_type: str) -> str:
        doc = Document()
        style = doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = Pt(12)
        for line in content.split('\n'):
            line = line.strip()
            if not line: continue
            if len(line) < 100 and line.isupper():
                doc.add_heading(line, level=1)
            else:
                doc.add_paragraph(line)
        save_dir = "static/docs"
        os.makedirs(save_dir, exist_ok=True)
        timestamp = int(datetime.now().timestamp())
        filename = f"ViLaw_{doc_type}_{timestamp}.docx"
        doc.save(os.path.join(save_dir, filename))
        return filename
