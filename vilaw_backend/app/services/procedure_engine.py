import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.services.llm_engine import get_llm
from app.schemas.procedure_schema import ProcedureGuideResponse

class ProcedureEngine:
    def __init__(self):
        # Dùng model "Brain" (Llama 3.3 hoặc Gemini Flash)
        self.llm = get_llm(streaming=False, temperature=0.3)

    async def generate_guide(self, query: str) -> dict:
        parser = JsonOutputParser(pydantic_object=ProcedureGuideResponse)

        prompt = ChatPromptTemplate.from_template("""
        <|im_start|>system
        Bạn là Chuyên viên Tư vấn Thủ tục Hành chính Việt Nam.
        Nhiệm vụ: Tạo hướng dẫn thực hiện thủ tục chi tiết, chính xác theo quy định pháp luật hiện hành.
        
        Yêu cầu output: Trả về JSON (không markdown) gồm:
        - authority: Cơ quan tiếp nhận.
        - duration: Thời gian theo luật định.
        - fee: Lệ phí nhà nước (ước lượng).
        - steps: Các bước thực hiện (1, 2, 3...).
        - required_documents: Danh sách hồ sơ cần có kèm hướng dẫn (bản chính/sao y).
        
        {format_instructions}
        <|im_end|>
        
        <|im_start|>user
        Người dùng muốn làm thủ tục: "{query}"
        <|im_end|>
        
        <|im_start|>assistant
        """)

        chain = prompt | self.llm | parser
        
        try:
            return await chain.ainvoke({
                "query": query,
                "format_instructions": parser.get_format_instructions()
            })
        except Exception as e:
            return {"error": str(e)}
