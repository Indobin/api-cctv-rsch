from typing import Any, Optional

def success_response(message: str, data: Any = None):
    """
    Response format untuk success
    """
    return {
        "status": "success",
        "message": message,
        "data": data
    }

def error_response(message: str, error_data: Optional[Any] = None):
    """
    Response format untuk error
    """
    response = {
        "status": "error",
        "message": message
    }
    
    if error_data is not None:
        response["error"] = error_data
        
    return response