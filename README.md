This is a [maubot](https://github.com/maubot/maubot) plugin for invoking LLMs, based on prior work by [brokensandals](https://github.com/brokensandals/maubot-llm).

It's new(er) and (moderately) less rough. It also uses more reaction emojis. :tada:<br/>
Use at your own risk, and expect problems.

This plugin primarily uses OpenAI-compatible endpoints, so the LLM must be supplied by an OpenAI-compatible server such as:
- [llama.cpp](https://github.com/ggml-org/llama.cpp)
- [Lemonade](https://lemonade-server.ai/)
- [LM Studio](https://lmstudio.ai/)

(Technically the Anthropic endpoint for Chat Completion only is available, but it's untested.)

You should definitely limit access, see [Configuration](docs/CONFIGURATION.md) for instructions.

# Installation

- [Setup maubot](https://docs.mau.fi/maubot/usage/setup/index.html)
- Clone this repo and [use `mbc build -u`](https://docs.mau.fi/maubot/usage/cli/build.html) to build the plugin
- [Create a client and an instance](https://docs.mau.fi/maubot/usage/basic.html)
- Update the configuration; see [Configuration](docs/CONFIGURATION.md) and [base-config.yaml](base-config.yaml) for documentation of the available options

# Usage

See [Commands](docs/COMMANDS.md) for a full reference of all commands.

Once this plugin is added to a room, any user on the allowlist can post to that room with the plugin's trigger (example: `!llm info`). Some commands are for admin or maintenance of the plugin, but most commands invoke a backend LLM and respond with whatever that LLM returns.

Private messages to the bot that this plugin is part of counts as posting to a room, so triggers work there as well.

You can configure one backend and one model per room. If you do not specify any using commands, rooms will use any backend or model defaults in the plugin configuration.

You can also configure a separate URL for image generation. This feature is useful when you prefer Generative AI engines (with OpenAI-compatible endpoints) such as [stable-diffusion.cpp](https://github.com/leejet/stable-diffusion.cpp) to handle images instead of more generalized LLM models.

# Limitations

Most OpenAI-compatible endpoints allow for a parameter (`n`) to generate more than one response to a given request. In all cases this has been capped at `1` to avoid overwhelming any chat rooms this plugin is integrated into.

The [Matrix Specification](https://spec.matrix.org/latest/client-server-api) does not currently provide for containing multiple images in a single post, either via upload or via download. This impacts a few features:
- Multi-modal chat: Only one image can be sent to this plugin, and only the first image the backend LLM returns (if there were multiple) is selected
- Image generation: Only one image is returned from the LLM
  - Affected by the `n` variable above, so in theory LLMs wouldn't send more than one anyway
- Image edit: "Mask" or "partial" images aren't supported