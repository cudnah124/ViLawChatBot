import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.services.llm_engine import get_llm
from app.schemas.procedure_schema import ProcedureGuideResponse

class ProcedureEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProcedureEngine, cls).__new__(cls)
            cls._instance.llm = get_llm(streaming=False, temperature=0.1)
        return cls._instance

    async def generate_guide(self, query: str) -> dict:
        parser = JsonOutputParser(pydantic_object=ProcedureGuideResponse)

        prompt = ChatPromptTemplate.from_template("""
        <|im_start|>system
        Bạn là Chuyên viên Tư vấn Thủ tục Hành chính Việt Nam chuyên nghiệp.
        Nhiệm vụ: Phân tích yêu cầu và trích xuất hướng dẫn thủ tục hành chính chuẩn xác.
        
        QUY TẮC QUAN TRỌNG:
        1. Chỉ trả về duy nhất một chuỗi JSON hợp lệ. Không trả về markdown (```json), không trả về lời dẫn.
        2. Nếu không xác định được thủ tục cụ thể, hãy trả về JSON với các trường để trống hoặc ghi "Cần thêm thông tin".
        3. Về lệ phí và thời gian: Nếu không chắc chắn, hãy ghi "Theo quy định hiện hành tại cơ quan tiếp nhận" thay vì bịa số liệu.
        
        Format yêu cầu:
        {format_instructions}
        <|im_end|>
        
        <|im_start|>user
        Người dùng hỏi: "{query}"
        <|im_end|>
        
        <|im_start|>assistant
        """)

        # Tạo Chain
        chain = prompt | self.llm | parser
        
        try:
            # Gọi LLM
            response = await chain.ainvoke({
                "query": query,
                "format_instructions": parser.get_format_instructions()
            })
            return response
            
        except Exception as e:
            # Fallback handling: Xử lý trường hợp LLM trả về lỗi hoặc JSON hỏng
            print(f"Error generating procedure: {e}")
            return {
                "procedure_name": "Lỗi xử lý",
                "authority": "Không xác định",
                "duration": "N/A",
                "fee": "N/A",
                "steps": [],
                "required_documents": [],
                "legal_basis": f"Hệ thống gặp lỗi khi phân tích: {str(e)}"
            }

# Helper để test nhanh
if __name__ == "__main__":
    import asyncio
    async def test():
        engine = ProcedureEngine()
        result = await engine.generate_guide("Thủ tục làm hộ chiếu phổ thông lần đầu")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    asyncio.run(test())