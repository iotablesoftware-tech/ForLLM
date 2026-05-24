from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uuid

class ProblemDetails(BaseModel):
    """Unified RFC 7807 error format mapping machine-readable error context."""
    type: str = Field(..., description="URI reference identifying the problem type.")
    title: str = Field(..., description="Short, human-readable summary of the problem.")
    status: int = Field(..., description="HTTP status code set by the origin server.")
    detail: str = Field(..., description="Detailed explanation of the problem instance.")
    instance: Optional[str] = Field(None, description="URI reference identifying the specific occurrence.")
    extensions: Dict[str, Any] = Field(default_factory=dict, description="Custom details for debugging or structured validations.")

def create_problem_response(
    status_code: int, 
    title: str, 
    detail: str, 
    error_code: str, 
    instance: Optional[str] = None,
    validation_errors: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Helper to construct standard RFC 7807 problem details HTTP responses."""
    extensions = {"error_code": error_code}
    if validation_errors:
        extensions["validation_errors"] = validation_errors

    problem = ProblemDetails(
        type=f"https://iotables.net/errors/{error_code.lower()}",
        title=title,
        status=status_code,
        detail=detail,
        instance=instance,
        extensions=extensions
    )
    
    return JSONResponse(
        status_code=status_code,
        content=problem.model_dump(exclude_none=True),
        headers={"Content-Type": "application/problem+json"}
    )

async def correlation_id_middleware(request: Request, call_next):
    """Middleware attaching a unique Correlation ID to trace logs and tracing requests."""
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    response: Response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response
