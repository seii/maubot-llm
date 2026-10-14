from typing import List, Optional
from aiohttp import ClientSession

class Models:
    def __init__(self, object: str = "list", data: List[dict]) -> None:
        self.object = object
        self.data = data

    def __eq__(self, other) -> bool:
        return self.object == other.object and self.data == other.data


class Completions:
    def __init__(self, text: str, finish_reason: str, model: Optional[str]) -> None:
        self.text = text
        self.finish_reason = finish_reason
        self.model = model
    
    def __eq__(self, other) -> bool:
        return self.text == other.text and self.finish_reason == other.finish_reason and self.model == other.model


class ChatCompletion:
    def __init__(self, message: dict, finish_reason: str, model: Optional[str]) -> None:
        self.message = message
        self.finish_reason = finish_reason
        self.model = model
    
    def __eq__(self, other) -> bool:
        return self.message == other.message and self.finish_reason == other.finish_reason and self.model == other.model


class Responses:
    def __init__(self, response_id: str, text: str, finish_reason: str, model: Optional[str]) -> None:
        self.response_id = response_id
        self.text = text
        self.finish_reason = finish_reason
        self.model = model
    
    def __eq__(self, other) -> bool:
        return (self.response_id == other.response_id and 
                self.text == other.text and 
                self.finish_reason == other.finish_reason and 
                self.model == other.model)


class ResponsesInputTokens:
    def __init__(self, response_id: str, input_tokens: int, model: Optional[str]) -> None:
        self.response_id = response_id
        self.input_tokens = input_tokens
        self.model = model
    
    def __eq__(self, other) -> bool:
        return (self.response_id == other.response_id and 
                self.input_tokens == other.input_tokens and 
                self.model == other.model)


class Backend:
    def __init__(self, cfg: dict) -> None:
        self.cfg = cfg
        self.default_model = cfg.get("default_model")
        self.default_system_prompt = cfg.get("default_system_prompt")

    async def fetch_models(self, http: ClientSession) -> List[str]:
        raise NotImplementedError()

    async def create_completion(self, http: ClientSession, prompt: str, model: Optional[str] = None) -> Completions:
        raise NotImplementedError()

    async def create_chat_completion(self, http: ClientSession,  context: List[dict], system: Optional[str] = None, model: Optional[str] = None) -> ChatCompletion:
        raise NotImplementedError()

    async def create_response(self, http: ClientSession, prompt: str, model: Optional[str] = None) -> Responses:
        raise NotImplementedError()
    
    async def get_response_input_tokens(self, http: ClientSession, response_id: str) -> ResponsesInputTokens:
        raise NotImplementedError()


class BasicOpenAIBackend(Backend):
    def __init__(self, cfg) -> None:
        super().__init__(cfg)
        self.base_url = cfg["base_url"]
        self.authorization = cfg["authorization"]
    
    async def fetch_models(self, http: ClientSession) -> List[str]:
        url = f"{self.base_url}/v1/models"
        headers = {}
        if self.authorization is not None:
            headers["Authorization"] = self.authorization
        async with http.get(url, headers=headers) as resp:
            # TODO error handling
            respbody = await resp.json()
            return [m["id"] for m in respbody["data"]]

    async def create_completion(self, http: ClientSession, prompt: str, model: Optional[str] = None) -> Completions:
        url = f"{self.base_url}/v1/completions"
        reqbody = {"prompt": prompt}
        if model is not None:
            reqbody["model"] = model
        headers = {}
        if self.authorization is not None:
            headers["Authorization"] = self.authorization
        async with http.post(url, headers=headers, json=reqbody) as resp:
            # TODO error handling
            respbody = await resp.json()
            choice = respbody["choices"][0]
            return Completions(
                text=choice["text"],
                finish_reason=choice["finish_reason"],
                model=choice.get("model", None)
            )

    async def create_chat_completion(self, http: ClientSession,  context: List[dict], system: Optional[str] = None, model: Optional[str] = None) -> ChatCompletion:
        url = f"{self.base_url}/v1/chat/completions"
        reqbody = {"messages": context}
        if system is not None:
            reqbody["messages"].insert(0, {"role": "system", "content": system})
        if model is not None:
            reqbody["model"] = model
        headers = {}
        if self.authorization is not None:
            headers["Authorization"] = self.authorization
        async with http.post(url, headers=headers, json=reqbody) as resp:
            # TODO error handling
            respbody = await resp.json()
            choice = respbody["choices"][0]
            return ChatCompletion(
                message=choice["message"],
                finish_reason=choice["finish_reason"],
                model=choice.get("model", None)
            )
    
    async def create_response(self, http: ClientSession, prompt: str, model: Optional[str] = None) -> Responses:
        url = f"{self.base_url}/v1/responses"
        reqbody = {"prompt": prompt}
        if model is not None:
            reqbody["model"] = model
        headers = {}
        if self.authorization is not None:
            headers["Authorization"] = self.authorization
        async with http.post(url, headers=headers, json=reqbody) as resp:
            # TODO error handling
            respbody = await resp.json()
            return Responses(
                response_id=respbody["id"],
                text=respbody["text"],
                finish_reason=respbody["finish_reason"],
                model=respbody.get("model", None)
            )
    
    async def get_response_input_tokens(self, http: ClientSession, response_id: str) -> ResponsesInputTokens:
        url = f"{self.base_url}/v1/responses/{response_id}/input_tokens"
        headers = {}
        if self.authorization is not None:
            headers["Authorization"] = self.authorization
        async with http.get(url, headers=headers) as resp:
            # TODO error handling
            respbody = await resp.json()
            return ResponsesInputTokens(
                response_id=response_id,
                input_tokens=respbody["input_tokens"],
                model=respbody.get("model", None)
            )


class OpenAIBackend(BasicOpenAIBackend):
    def __init__(self, cfg) -> None:
        cfg["authorization"] = f"Bearer {cfg['api_key']}"
        if cfg.get("base_url") is None:
            cfg["base_url"] = "https://api.openai.com"
        super().__init__(cfg)


class AnthropicBackend(Backend):
    def __init__(self, cfg) -> None:
        super().__init__(cfg)
        self.base_url = cfg.get("base_url", "https://api.anthropic.com")
        self.api_key = cfg["api_key"]
        self.max_tokens = cfg["max_tokens"]

    async def create_chat_completion(self, http: ClientSession,  context: List[dict], system: Optional[str] = None, model: Optional[str] = None) -> ChatCompletion:
        url = f"{self.base_url}/v1/messages"
        reqbody = {"messages": context}
        if system is not None:
            reqbody["system"] = system
        if model is not None:
            reqbody["model"] = model
        reqbody["max_tokens"] = self.max_tokens
        headers = {}
        headers["anthropic-version"] = "2023-06-01"
        headers["x-api-key"] = self.api_key
        async with http.post(url, headers=headers, json=reqbody) as resp:
            # TODO error handling
            respbody = await resp.json()
            text = "\n\n".join(c["text"] for c in respbody["content"])
            return ChatCompletion(
                message=dict(role="assistant", content=text),
                finish_reason=respbody["stop_reason"],
                model=respbody["model"]
            )

