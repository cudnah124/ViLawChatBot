from fastapi import APIRouter, HTTPException
from app.services.drafter import DrafterService
from app.schemas.contract_schema import ContractDraftRequest, ContractDraftResponse, RiskAnalysisRequest, RiskAnalysisResponse
from app.services.risk_checker import RiskCheckerService

router = APIRouter()
drafter_service = DrafterService()
risk_service = RiskCheckerService()

@router.post("/draft", response_model=ContractDraftResponse)
async def draft_endpoint(request: ContractDraftRequest):
    """
    POST /api/v1/contracts/draft
    """
    try:
        return await drafter_service.draft_contract(request)
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Lỗi hệ thống khi soạn thảo.")

@router.post("/check-risk", response_model=RiskAnalysisResponse)
async def check_risk_endpoint(request: RiskAnalysisRequest):
    """
    API 3.0: Rà soát rủi ro hợp đồng (Risk Checker Engine).
    Input: Nội dung văn bản text.
    Output: Báo cáo rủi ro chi tiết (JSON).
    """
    result = await risk_service.analyze_document(request)
    # Sanitize output to match response model: ensure `legal_basis` is a string
    try:
        risks = result.get("risks") if isinstance(result, dict) else None
        if isinstance(risks, list):
            for r in risks:
                if r.get("legal_basis") is None:
                    r["legal_basis"] = "Theo quy định pháp luật hiện hành"
    except Exception:
        pass
    return result
