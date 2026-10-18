from typing import List, Optional


# Convention:
#   `data` = already-parsed data intended for user consumption (return type changes per-class)
#   `status` = aiohttp's `status` + `reason` as one string
#   `error` = Raw body text from aiohttp (only populate in case of error)
#   Any other parameters are custom to each class
class Models:
    def __init__(self, data: List[str], status: str, object_: str = "list", error: Optional[str] = None) -> None:
        self.data = data
        self.status = status
        self.object_ = object_
        self.error = error

    def __eq__(self, other) -> bool:
        return (self.data == other.data and
                self.status == other.status and
                self.object_ == other.object_ and
                self.error == other.error
                )


class Completions:
    def __init__(self, data: str, status: str, model: Optional[str], error: Optional[str] = None) -> None:
        self.data = data
        self.status = status
        self.model = model
        self.error = error
    
    def __eq__(self, other) -> bool:
        return (self.data == other.data and
                self.status == other.status and
                self.model == other.model and
                self.error == other.error
                )


class ChatCompletion:
    def __init__(self, data: dict, status: str, model: Optional[str], error: Optional[str] = None) -> None:
        self.data = data
        self.status = status
        self.model = model
        self.error = error
    
    def __eq__(self, other) -> bool:
        return (self.data == other.data and
                self.status == other.status and
                self.model == other.model and
                self.error == other.error
                )


class Responses:
    def __init__(self, response_id: str, role: str, data: str, status: str, model: Optional[str], error: Optional[str] = None) -> None:
        self.response_id = response_id
        self.role = role
        self.data = data
        self.status = status
        self.model = model
        self.error = error
    
    def __eq__(self, other) -> bool:
        return (self.response_id == other.response_id and
                self.role == other.role and
                self.data == other.data and
                self.status == other.status and
                self.model == other.model and
                self.error == other.error
                )


class ResponsesInputTokens:
    def __init__(self, data: str, status: str, object_: str, error: Optional[str] = None) -> None:
        self.data = data
        self.status = status
        self.object_ = object_
        self.error = error
    
    def __eq__(self, other) -> bool:
        return (self.data == other.data and
                self.status == other.status and
                self.object_ == other.object_ and
                self.error == other.error
                )


class CreateImageGenerations:
    def __init__(self, data: str, output_format: str, status: str, error: Optional[str] = None) -> None:
        self.data = data
        self.output_format = output_format
        self.status = status
        self.error = error
    
    def __eq__(self, other) -> bool:
        return (self.data == other.data and
                self.output_format == other.output_format and
                self.status == other.status and
                self.error == other.error
                )


class CreateImageEdit:
    def __init__(self, data: str, output_format: str, status: str, model: Optional[str], error: Optional[str] = None) -> None:
        self.data = data
        self.output_format = output_format
        self.status = status
        self.model = model
        self.error = error
    
    def __eq__(self, other) -> bool:
        return (self.data == other.data and
                self.output_format == other.output_format and
                self.status == other.status and
                self.model == other.model and
                self.error == other.error
                )