This is a [maubot](https://github.com/maubot/maubot) plugin for invoking LLMs, based on prior work by [brokensandals](https://github.com/brokensandals/maubot-llm).

It's new(er) and (moderately) less rough. It also uses more reaction emojis. :tada:<br/>
Use at your own risk, and expect problems.

This plugin primarily uses OpenAI-compatible endpoints, so the LLM must be supplied by an OpenAI-compatible server such as:
- [llama.cpp](https://github.com/ggml-org/llama.cpp)
- [Lemonade](https://lemonade-server.ai/)
- [LM Studio](https://lmstudio.ai/)

(Technically the Anthropic endpoint for Chat Completion only is available, but it's untested.)

You should definitely limit access, see [Configuration](#configuration) for instructions.

# Installation

- [Setup maubot](https://docs.mau.fi/maubot/usage/setup/index.html)
- Clone this repo and [use `mbc build -u`](https://docs.mau.fi/maubot/usage/cli/build.html) to build the plugin
- [Create a client and an instance](https://docs.mau.fi/maubot/usage/basic.html)
- Update the configuration; see [Configuration](#configuration) and [base-config.yaml](base-config.yaml) for documentation of the available options

# Usage

Once this plugin is added to a room, any user on the allowlist using the plugin's trigger will cause the bot to invoke the backend LLM and respond with whatever the LLM returns. Don't forget that DMing the bot directly also counts as "posting to a room".

You can configure multiple backends.
One of them should be designated as the default, but the bot tracks models and prompts on a per-room basis so each room can be different.

You can also define a separate URL for image generation, to use Generative AI engines which have OpenAI-compatible endpoints such as [stable-diffusion.cpp](https://github.com/leejet/stable-diffusion.cpp) alongside more text-focused LLMs.

# Limitations

Most OpenAI-compatible endpoints allow for a parameter (`n`) to generate more than one response to a given request. In all cases this has been capped at `1` to avoid overwhelming any chat rooms this plugin is integrated into.

The [Matrix Specification](https://spec.matrix.org/latest/client-server-api) does not currently provide for containing multiple images in a single post, either via upload or via download. This impacts a few features:
- Multi-modal chat: Only one image can be sent to this plugin, and only the first image the backend LLM returns (if there were multiple) is selected
- Image generation: Only one image is returned from the LLM
  - Affected by the `n` variable above, so in theory LLMs wouldn't send more than one anyway
- Image edit: "Mask" or "partial" images aren't supported

### Reactions
_Optional field_
This plugin will react to user tags with several kinds of emoji to indicate request status

- `wait_reaction`: Indicates that some amount of processing is occurring
- `error_reaction`: Indicates that some kind of underlying error occurred and can be viewed in Maubot's logs
- `denied_reaction`: Indicates that the user is not allowed to execute this command (example: running `!<trigger> clear` as a non-admin user)
- `done_reaction`: Indicates that the request succeeded in full

When appropriate the plugin will also reply (the kind of message that shows your message above it) or respond (the default message in a chat room) with text or image results from the backend LLM.

_Hint:_ A `wait_reaction` where nothing else happens is typically a code-level exception, which can also be viewed in Maubot's logs.

**NOTE:** Technically you could put any text for each of these, but Matrix servers may react in unpredictable ways if the reaction succeeds at all. Stick to emojis, you'll be happier.
