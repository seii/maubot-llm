from typing import List, Optional
from aiohttp import ClientSession
from maubot_llm._backends import (
    Models,
    Completions,
    ChatCompletion,
    Responses,
    ResponsesInputTokens,
    CreateImageGenerations,
    CreateImageEdit
)


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

    async def create_image_generation(self, http: ClientSession, prompt: str, n: int, size: str, output_format: str, output_compression: str, model: Optional[str] = None) -> CreateImageGenerations:
        raise NotImplementedError()
    
    async def create_image_edit(self, http: ClientSession, prompt: str, image: str, mask: Optional[str] = None, model: Optional[str] = None) -> CreateImageEdit:
        raise NotImplementedError()


class BasicOpenAIBackend(Backend):
    def __init__(self, cfg) -> None:
        super().__init__(cfg)
        self.base_url = cfg["base_url"]
        # Use img_url if specified, otherwise fall back to base_url
        self.img_base_url = cfg.get("img_url") or self.base_url
        if cfg["api_key"] is not None:
            self.authorization = f"Bearer {cfg['api_key']}"
        else:
            self.authorization = None
    
    async def fetch_models(self, http: ClientSession) -> Models:
        url = f"{self.base_url}/v1/models"
        headers = {}
        if self.authorization is not None:
            headers["Authorization"] = self.authorization
        async with http.get(url, headers=headers) as resp:
            status = f"{resp.status} {resp.reason}"

            # Any errors should populate `error` with the response's body
            error = None
            result = None
            if not resp.ok:
                error = await resp.text()
            else:
                respbody = await resp.json()

                # Empty "data" field is valid, missing field is not
                if respbody and respbody["data"]:
                    result = [m["id"] for m in respbody["data"]]
                else:
                    error = await resp.text()
            return Models(
                data=result,
                object=respbody["object_"] if respbody["object_"] else "list",
                status=status,
                error=error
            )

    async def create_completion(self, http: ClientSession, prompt: str, max_tokens: int, model: Optional[str] = None) -> Completions:
        url = f"{self.base_url}/v1/completions"
        reqbody = {"prompt": prompt}
        if model is not None:
            reqbody["model"] = model
        if max_tokens > 0:
            reqbody["max_tokens"] = max_tokens
        else:
            reqbody["max_tokens"] = 1

        headers = {}
        if self.authorization is not None:
            headers["Authorization"] = self.authorization
        async with http.post(url, headers=headers, json=reqbody) as resp:
            status = f"{resp.status} {resp.reason}"

            # Any errors should populate `error` with the response's body
            error = None
            result = None
            if not resp.ok:
                error = await resp.text()
            else:
                respbody = await resp.json()

                # Empty "choices" field is valid, missing field is not
                if respbody and respbody["choices"]:
                    # Llama.cpp does not support multiple completions per request
                    result = respbody["choices"][0]["text"]
                else:
                    error = await resp.text()
            return Completions(
                data=result,
                status=status,
                model=respbody.get("model", None),
                error=error
            )

    # TODO Multi-modal input
    async def create_chat_completion(self, http: ClientSession, context: List[dict], system: Optional[str] = None, model: Optional[str] = None) -> ChatCompletion:
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
            status = f"{resp.status} {resp.reason}"

            # Any errors should populate `error` with the response's body
            error = None
            result = None
            if not resp.ok:
                error = await resp.text()
            else:
                respbody = await resp.json()
                # Empty "choices" field is valid, missing field is not
                if respbody and respbody["choices"]:
                    # Llama.cpp does not support multiple completions per request
                    result = respbody["choices"][0]["message"]
                else:
                    error = await resp.text()
            return ChatCompletion(
                data=result,
                status=status,
                model=respbody.get("model", None),
                error=error
            )

    # `/responses` is apparently the new OpenAI-recommended standard since
    #   [March 2025](https://openai.com/index/new-tools-for-building-agents/)
    #   Llama.cpp also apparently just [converts](https://github.com/ggml-org/llama.cpp/tree/master/tools/server#post-v1responses-openai-compatible-responses-api)
    #   `/responses` back to `/chat/completions` transparently for now
    async def create_response(self, http: ClientSession, context: List[dict], model: Optional[str] = None) -> Responses:
        url = f"{self.base_url}/v1/responses"
        reqbody = {"input": context}
        if model is not None:
            reqbody["model"] = model
        headers = {}
        if self.authorization is not None:
            headers["Authorization"] = self.authorization
        async with http.post(url, headers=headers, json=reqbody) as resp:
            status = f"{resp.status} {resp.reason}"

            # Any errors should populate `error` with the response's body
            error = None
            result = None
            if not resp.ok:
                error = await resp.text()
            else:
                respbody = await resp.json()

                # Empty "output" field is valid, missing field is not
                if respbody and respbody["output"]:
                    role = respbody["output"][0]["role"]
                    # Llama.cpp does not support multiple completions per request
                    # TODO Multi-modal input
                    result = respbody["output"][0]["content"][0]["text"]
                else:
                    error = await resp.text()
            return Responses(
                response_id=respbody["id"],
                role=role,
                data=result,
                status=status,
                model=respbody.get("model", None),
                error=error
            )
 
    async def get_response_input_tokens(self, http: ClientSession, input: str, model: Optional[str] = None) -> ResponsesInputTokens:
        url = f"{self.base_url}/v1/responses/input_tokens"
        reqbody = {"input": input}
        if model is not None:
            reqbody["model"] = model
        headers = {}
        if self.authorization is not None:
            headers["Authorization"] = self.authorization
        async with http.post(url, headers=headers, json=reqbody) as resp:
            status = f"{resp.status} {resp.reason}"

            # Any errors should populate `error` with the response's body
            error = None
            result = None
            if not resp.ok:
                error = await resp.text()
            else:
                respbody = await resp.json()
                result = respbody["input_tokens"]
            return ResponsesInputTokens(
                data=result,
                status=status,
                object_=respbody.get("object", None),
                error=error
            )

    async def create_image_generation(self, http: ClientSession, prompt: str, n: int, size: str, output_format: str, output_compression: str, model: Optional[str] = None) -> CreateImageGenerations:
        url = f"{self.img_base_url}/v1/images/generations"
        reqbody = {
            "prompt": prompt,
            "n": n,
            "size": size,
            "output_format": output_format,
            "output_compression": output_compression
            }

        # Optional because Stable Diffusion can't currently specify a model on request
        if model is not None:
            reqbody["model"] = model
        headers = {}
        if self.authorization is not None:
            headers["Authorization"] = self.authorization
        async with http.post(url, headers=headers, json=reqbody) as resp:
            status = f"{resp.status} {resp.reason}"

            # Any errors should populate `error` with the response's body
            error = None
            result = None
            if not resp.ok:
                error = await resp.text()
            else:
                respbody = await resp.json()

                # Empty "data" field is valid, missing field is not
                if respbody and respbody["data"]:
                    format = respbody.output_format
                    # respbody["data"] may contain multiple images, pull those out
                    b64_imgs = []
                    for body in respbody["data"]:
                        if body and body["b64_json"]:
                            b64_imgs.append(body)

                    # TODO Upload/return multiple images when supported
                    # `b64_imgs` may now hold multiple images, but Matrix does not currently
                    #   support posting multiple images at once so only the first returned
                    #   image will be sent
                    result = b64_imgs[0]["b64_json"] if b64_imgs else ""
                else:
                    format = None
                    error = await resp.text()

            return CreateImageGenerations(
                data=result,
                output_format=format,
                status=status,
                model=respbody.get("model", None),
                error=error
            )

    async def create_image_edit(self, http: ClientSession, prompt: str, image: str, mask: Optional[str] = None, model: Optional[str] = None) -> CreateImageEdit:
        url = f"{self.img_base_url}/v1/images/edits"
        # For multipart/form-data requests, we'll need to use aiohttp's FormData
        from aiohttp import FormData
        form = FormData()
        form.add_field("prompt", prompt)
        form.add_field("image", image)
        if mask is not None:
            form.add_field("mask", mask)
        # Optional because Stable Diffusion can't currently specify a model on request
        if model is not None:
            form.add_field("model", model)
        headers = {}
        if self.authorization is not None:
            headers["Authorization"] = self.authorization
        async with http.post(url, headers=headers, data=form) as resp:
            status = f"{resp.status} {resp.reason}"

            # Any errors should populate `error` with the response's body
            error = None
            result = None
            if not resp.ok:
                error = await resp.text()
            else:
                respbody = await resp.json()

                # Empty "data" field is valid, missing field is not
                if respbody and respbody["data"]:
                    # respbody["data"] may contain multiple images, pull those out
                    b64_imgs = []
                    for body in respbody["data"]:
                        if body and body["b64_json"]:
                            b64_imgs.append(body)

                    # TODO Upload/return multiple images when supported
                    # `b64_imgs` may now hold multiple images, but Matrix does not currently
                    #   support posting multiple images at once so only the first returned
                    #   image will be sent
                    result = b64_imgs[0]["b64_json"] if b64_imgs else ""
                else:
                    error = await resp.text()
            # Returns the entire `data` entry because it may contain multiple images
            return CreateImageEdit(
                data=result,
                status=status,
                model=respbody.get("model", None),
                error=error
            )


class OpenAIBackend(BasicOpenAIBackend):
    def __init__(self, cfg) -> None:
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
