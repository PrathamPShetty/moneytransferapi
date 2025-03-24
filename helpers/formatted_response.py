from rest_framework.response import Response

def formatted_response(status_code: int, data: any = None, description: str = "", record_count: int = 0, status_flag: int=1):
    if data and isinstance(data, (list, tuple)):
        record_count = len(data)
    return Response(
        {
            "status": status_flag,
            "data": data,
            "description": description,
            "recordCount": record_count,
        },
        status=status_code,
    )
