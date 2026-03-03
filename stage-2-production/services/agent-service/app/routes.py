from fastapi import APIRouter
from app.schemas import ProcessRequest, AgentResponse
from app.agent import AsyncCustomerSuccessAgent

router = APIRouter()
agent = AsyncCustomerSuccessAgent()


@router.post("/process", response_model=AgentResponse)
async def process_message(request: ProcessRequest):
    """Direct processing endpoint for testing without Kafka."""
    result = await agent.process_message(
        message=request.message,
        channel=request.channel,
        customer_email=request.customer_email,
        customer_phone=request.customer_phone,
        customer_name=request.customer_name,
    )
    return AgentResponse(**result)
