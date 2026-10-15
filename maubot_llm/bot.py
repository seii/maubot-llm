import base64

from maubot import Plugin
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper
from maubot import Plugin, MessageEvent
from maubot.handlers import command, event
from mautrix.types import (
    EventType,
    ImageInfo,
    MediaMessageEventContent,
    MessageType,
    RelatesTo,
    InReplyTo,
)
from typing import Type
from maubot_llm.backends import Backend, BasicOpenAIBackend, OpenAIBackend, AnthropicBackend
from maubot_llm import db
from mautrix.util.async_db import UpgradeTable


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("allowlist")
        helper.copy("default_backend")
        helper.copy("backends")
        helper.copy("customization")


class LlmBot(Plugin):
    async def start(self) -> None:
        self.config.load_and_update()
    
    def get_command_name(self) -> str:
        default_trigger = "llm"
        return self.config["customization"]["custom_trigger"] if self.config["customization"]["custom_trigger"] else default_trigger
    
    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config

    def get_wait_emoji(self) -> str:
        wait = "⏳"

        return self.config["customization"]["wait_reaction"] if self.config["customization"] and self.config["customization"]["wait_reaction"] else wait
    
    def get_done_emoji(self) -> str:
        done = "✅"

        return self.config["customization"]["done_reaction"] if self.config["customization"] and self.config["customization"]["done_reaction"] else done

    def is_allowed(self, sender: str) -> bool:
        if self.config["allowlist"] == False:
            return True
        return sender in self.config["allowlist"]
    
    async def get_room(self, room_id: str) -> db.Room:
        room = await db.fetch_room(self.database, room_id)
        if room is None:
            room = db.Room()
            room.room_id = room_id
            await db.upsert_room(self.database, room)
        return room
    
    def get_backend(self, room: db.Room) -> Backend:
        key = room.backend
        if key is None:
            key = self.config["default_backend"]
        cfg = self.config["backends"][key]
        cfg["key"] = key
        if cfg["type"] == "basic_openai":
            return BasicOpenAIBackend(cfg)
        if cfg["type"] == "openai":
            return OpenAIBackend(cfg)
        if cfg["type"] == "anthropic":
            return AnthropicBackend(cfg)
        raise ValueError(f"unknown backend type {cfg['type']}")
    
    @command.new(name=get_command_name, require_subcommand=True)
    async def llm_command(self, evt: MessageEvent) -> None:
        pass

    @llm_command.subcommand(help="Display configuration used for current room.")
    async def info(self, evt: MessageEvent) -> None:
        if not self.is_allowed(evt.sender):
            self.log.warn(f"stranger danger: sender={evt.sender}")
            return
        
        react_id = await evt.react(self.get_wait_emoji())

        room = await self.get_room(evt.room_id)
        context = await db.fetch_context(self.database, room.room_id)
        backend = self.get_backend(room)
        all_backends = ", ".join(self.config["backends"].keys())

        all_models = "unknown"
        try:
            all_models = ", ".join(await backend.fetch_models(self.http))
        except:
            pass

        items = []
        items.append(f"- Backend: {backend.cfg['key']} (available: {all_backends})")
        if room.model:
            items.append(f"- Model: {room.model}")
        elif backend.default_model:
            items.append(f"- Model (backend default): {backend.default_model}")
        else:
            items.append("- Model not specified")
        items[-1] += f" (available: {all_models})"
        if room.system_prompt:
            items.append(f"- System Prompt: {room.system_prompt}")
        elif backend.default_system_prompt:
            items.append(f"- System Prompt (backend default): {backend.default_system_prompt}")
        else:
            items.append("- System Prompt not specified")
        items.append(f"- Context Message Count: {len(context)}")
        msg = "\n".join(items)
        
        #await evt.redact(react_id)
        await evt.react(self.get_done_emoji())
        await evt.reply(msg)
    
    @llm_command.subcommand(help="Switch to a different backend for this room.")
    @command.argument("key")
    async def backend(self, evt: MessageEvent, key: str) -> None:
        if not self.is_allowed(evt.sender):
            self.log.warn(f"stranger danger: sender={evt.sender}")
            return
        if key not in self.config["backends"].keys():
            all_backends = ", ".join(self.config["backends"].keys())
            msg = f"Invalid backend. Available backends: {all_backends}"
            await evt.reply(msg)
            return
        room = await self.get_room(evt.room_id)
        room.backend = key
        await db.upsert_room(self.database, room)
        await evt.react(self.get_done_emoji())
    
    @llm_command.subcommand(help="Switch to a different model for this room. Use '-' to switch to the backend's default model.")
    @command.argument("model")
    async def model(self, evt: MessageEvent, model: str) -> None:
        if not self.is_allowed(evt.sender):
            self.log.warn(f"stranger danger: sender={evt.sender}")
            return
        # TODO validate model when the backend supports it
        room = await self.get_room(evt.room_id)
        if model == "-":
            room.model = None
        else:
            room.model = model
        await db.upsert_room(self.database, room)
        await evt.react(self.get_done_emoji())
    
    @llm_command.subcommand(help="Switch to a different system prompt for this room. Use '-' to switch to the backend's default system prompt.")
    @command.argument("prompt", pass_raw=True)
    async def system(self, evt: MessageEvent, prompt: str) -> None:
        if not self.is_allowed(evt.sender):
            self.log.warn(f"stranger danger: sender={evt.sender}")
            return
        # TODO validate model when the backend supports it
        room = await self.get_room(evt.room_id)
        if prompt == "-":
            room.system_prompt = None
        else:
            room.system_prompt = prompt
        await db.upsert_room(self.database, room)
        await evt.react(self.get_done_emoji())

    @llm_command.subcommand(help="Forget all context and treat subsequent messages as part of a new chat with the LLM.")
    async def clear(self, evt: MessageEvent) -> None:
        if not self.is_allowed(evt.sender):
            self.log.warn(f"stranger danger: sender={evt.sender}")
            return
        await db.clear_context(self.database, evt.room_id)
        await evt.react(self.get_done_emoji())

    @llm_command.subcommand(help="Ask the LLM to predict the completion (once) of a given prompt")
    @command.argument("max_tokens")
    @command.argument("prompt", pass_raw=True)
    async def complete(self, evt: MessageEvent, max_tokens: str, prompt: str) -> None:
        if not self.is_allowed(evt.sender):
            self.log.warn(f"stranger danger: sender={evt.sender}")
            return
        if prompt.startswith("!"):
            return
        room = await self.get_room(evt.room_id)
        
        if not max_tokens:
            self.log.warn("User did not provide max tokens")
            return
        if not prompt:
            self.log.warn("User did not provide prompt")
            return

        react_id = await evt.react(self.get_wait_emoji())
        await evt.mark_read()
        # TODO: refresh the typing indicator if generation takes longer
        # (or, alternatively, set a timeout for generation)
        await self.client.set_typing(evt.room_id, 30000)
        try:
            backend = self.get_backend(room)
            model = room.model or backend.default_model
            completion = await backend.create_completion(self.http, max_tokens=int(max_tokens), prompt=prompt, model=model)
            #await evt.redact(react_id)
            await evt.react(self.get_done_emoji())
            await evt.reply(completion.text)
        finally:
            await self.client.set_typing(evt.room_id, 0)

    #@event.on(EventType.ROOM_MESSAGE)
    # TODO Multi-modal input
    @llm_command.subcommand(help="Ask the LLM to start or continue the current room's chat")
    @command.argument("prompt", pass_raw=True)
    async def chat(self, evt: MessageEvent, prompt: str) -> None:
        if not self.is_allowed(evt.sender):
            self.log.warn(f"stranger danger: sender={evt.sender}")
            return
        if not prompt:
            self.log.warn("User did not provide a prompt")
            return
        if prompt.startswith("!"):
            return
        room = await self.get_room(evt.room_id)
        await db.append_context(self.database, room.room_id, "user", prompt)
        react_id = await evt.react(self.get_wait_emoji())
        await evt.mark_read()
        # TODO: refresh the typing indicator if generation takes longer
        # (or, alternatively, set a timeout for generation)
        await self.client.set_typing(evt.room_id, 30000)
        try:
            backend = self.get_backend(room)
            model = room.model or backend.default_model
            system = room.system_prompt or backend.default_system_prompt
            context = await db.fetch_context(self.database, room.room_id)
            response = await backend.create_response(self.http, context=context, model=model)
            await db.append_context(self.database, room.room_id, response.text[0]["role"], response.text[0]["content"])
            #await evt.redact(react_id)
            await evt.react(self.get_done_emoji())
            await evt.respond(response.text[0]["content"])
        finally:
            await self.client.set_typing(evt.room_id, 0)

    @llm_command.subcommand(help="Ask the LLM to count the tokens in a given prompt")
    @command.argument("prompt", pass_raw=True)
    async def count(self, evt: MessageEvent, prompt: str) -> None:
        if not self.is_allowed(evt.sender):
            self.log.warn(f"stranger danger: sender={evt.sender}")
            return
        if not prompt:
            self.log.warn("User did not provide a prompt")
            return
        if prompt.startswith("!"):
            return
        room = await self.get_room(evt.room_id)
        react_id = await evt.react(self.get_wait_emoji())
        await evt.mark_read()
        # TODO: refresh the typing indicator if generation takes longer
        # (or, alternatively, set a timeout for generation)
        await self.client.set_typing(evt.room_id, 30000)
        try:
            backend = self.get_backend(room)
            model = room.model or backend.default_model
            response = await backend.get_response_input_tokens(self.http, input=prompt, model=model)
            #await evt.redact(react_id)
            await evt.react(self.get_done_emoji())
            await evt.reply(f"I count that prompt as having {response.input_tokens} tokens.")
        finally:
            await self.client.set_typing(evt.room_id, 0)
    
    #@event.on(EventType.ROOM_MESSAGE)
    @llm_command.subcommand(help="Ask the LLM to generate a picture from the prompt the user provides")
    @command.argument("size")
    @command.argument("output_format")
    @command.argument("prompt", pass_raw=True)
    async def image(self, evt: MessageEvent, size: str, output_format: str, prompt: str) -> None:
        if not self.is_allowed(evt.sender):
            self.log.warn(f"stranger danger: sender={evt.sender}")
            return
        if evt.content.body.startswith("!"):
            return
        room = await self.get_room(evt.room_id)
        await db.append_context(self.database, room.room_id, "user", evt.content.body)
        react_id = await evt.react(self.get_wait_emoji())
        await evt.mark_read()
        # TODO: refresh the typing indicator if generation takes longer
        # (or, alternatively, set a timeout for generation)
        await self.client.set_typing(evt.room_id, 30000)

        try:
            backend = self.get_backend(room)

            if not size:
                raise ValueError(
                    "Size not specified by user"
                )
            if not output_format:
                raise ValueError(
                    "Image output format not specified by user"
                )
            if not prompt:
                raise ValueError(
                    "Prompt not specified by user"
                )
            
            images = await backend.create_image_generation(self.http, prompt, 1, size, output_format, "100")
            if not images.url or not images.url[0] or not images.url[0].get("b64_json"):
                raise ValueError(
                    "Backend image API returned an empty or malformed response"
                )

            if not images["output_format"]:
                raise ValueError(
                    "Backend image API did not specify the output format"
                )

            image_data = []
            for image in images.url:
                image_data.append(
                    base64.b64decode(
                        image["b64_json"],
                        validate=True,
                    )
                )

            if not image_data:
                raise ValueError("Backend image API returned no images")
            
            # TODO Upload/return multiple images when supported
            # Backend has possibly returned multiple images, but Matrix does not currently
            #   support posting multiple images at once so only the first returned
            #   image will be sent
            mxc_uri = await self.client.upload_media(
                    image_data[0],
                    mime_type=f"image/{images['output_format']}",
                    filename=f"image.{images['output_format']}",
                )
            
            content = MediaMessageEventContent(
                msgtype=MessageType.IMAGE,
                body=f"image.{images['output_format']}",
                url=mxc_uri,
                info=ImageInfo(
                    mimetype=f"image/{images['output_format']}",
                    size=len(image_data),
                ),
                relates_to=RelatesTo(
                    in_reply_to=InReplyTo(
                        event_id=evt.event_id,
                    )
                ),
            )

            await db.append_context(self.database, room.room_id, "user", f"Backend generated image from prompt: {evt.content.body}")
            #await evt.redact(react_id)
            await evt.react(self.get_done_emoji())
            await evt.reply(content)
        finally:
            await self.client.set_typing(evt.room_id, 0)
    
    @image.subcommand(help="Ask the LLM to generate an edited picture based on the image and prompt the user provides")
    @command.argument("prompt", pass_raw=True)
    async def edit(self, evt: MessageEvent, prompt: str) -> None:
        if not self.is_allowed(evt.sender):
            self.log.warn(f"stranger danger: sender={evt.sender}")
            return
        if evt.content.body.startswith("!"):
            return
        if not evt.content or evt.content["msgtype"] != "m.image":
            self.log.warn("Failed to parse: message does not contain an image")
            return

        room = await self.get_room(evt.room_id)

        if not prompt:
            self.log.warn("No prompt provided by user")
            return

        await db.append_context(self.database, room.room_id, "user", prompt)
        react_id = await evt.react(self.get_wait_emoji())
        await evt.mark_read()
        # TODO: refresh the typing indicator if generation takes longer
        # (or, alternatively, set a timeout for generation)
        await self.client.set_typing(evt.room_id, 30000)

        try:
            backend = self.get_backend(room)

            # TODO Implement

            await db.append_context(self.database, room.room_id, "user", f"Backend generated image from prompt: {prompt}")
            #await evt.redact(react_id)
            await evt.react(self.get_done_emoji())
            await evt.reply(content)
        finally:
            await self.client.set_typing(evt.room_id, 0)

    @classmethod
    def get_db_upgrade_table(cls) -> UpgradeTable | None:
        return db.upgrade_table
