This is a [maubot](https://github.com/maubot/maubot) plugin for invoking LLMs, based on prior work by [brokensandals](https://github.com/brokensandals/maubot-llm).

It's new(er) and (moderately) less rough. It also uses more reaction emojis. :tada:
Use at your own risk, and expect problems.

This plugin primarily uses OpenAI-compatible endpoints, so the LLM must be supplied by an OpenAI-compatible server such as:
- [llama.cpp](https://github.com/ggml-org/llama.cpp)
- [Lemonade](https://lemonade-server.ai/)
- [LM Studio](https://lmstudio.ai/)

Anthropic is available for Chat Completion only, but untested.

You should definitely limit access, see [Configuration](#configuration) for instructions.

# Installation

- [Setup maubot](https://docs.mau.fi/maubot/usage/setup/index.html)
- Clone this repo and [use `mbc build -u`](https://docs.mau.fi/maubot/usage/cli/build.html) to build the plugin
- [Create a client and an instance](https://docs.mau.fi/maubot/usage/basic.html)
- Update the configuration; see [Configuration](#configuration) and [base-config.yaml](base-config.yaml) for documentation of the available options

# Usage

Once this plugin is added to a room, any user on the allowlist using the plugin's trigger will cause the bot to invoke the backend LLM and respond with whatever the LLM returns.

You can configure multiple backends.
One of them should be designated as the default, but the bot tracks models and prompts on a per-room basis so each room can be different.

You can also define a separate URL for image generation, to use Generative AI engines which have OpenAI-compatible endpoints such as [stable-diffusion.cpp](https://github.com/leejet/stable-diffusion.cpp) alongside more text-focused LLMs.

# Commands

The following commands are available for managing the bot in a room:

- `!<trigger>`: View a "help" screen summarizing all available commands
- `!<trigger> info`: View the current backend, model, and system prompt, along with a list of available models (note: not supported for Anthropic)
  - By default, non-admin users will see `<hidden>` for the fields describing available backend models and the current system prompt
- `!<trigger> backend <your_key>`: Change to a different backend. (See [Configuration](#configuration) for details)
- `!<trigger> model <your_model>`: Change which specific LLM model the bot calls via API. Currently the name is just passed directly as the `model` field in the request json when invoking the server. Text-focused backends should work, some image generation backends (such as `stable-diffusion.cpp`) ignore this value
- `!<trigger> system <your_system_prompt>`: Change the system prompt for the room. This prompt will persistently apply to all requests by all users in the given room until cleared or changed
- `!<trigger> clear`: Clear the room's context. All past messages to the LLM from this room will be forgotten permanently
  - Does **NOT** clear any kind of cache on the backend LLM, as most OpenAI-compatible engines either have internal APIs for such a thing or simply lack this capability
- `!<trigger> complete <max_tokens> <user_prompt>`: Ask the LLM to complete whatever prompt the user sends, once, up to the max number of tokens specified
- `!<trigger> chat <user_prompt>`: Ask the LLM to respond to the provided prompt, based on existing context and system prompt if any already exist. OpenAI-compatible systems can do this two different ways, this plugin chooses to use the newer [Responses](https://developers.openai.com/api/reference/resources/responses/methods/create) API
  - Technically multi-modal input (i.e. picture post with the caption "What's in this picture?") is possible, but not yet implemented
- `!<trigger> count <user_prompt>`: Ask the LLM to count how many tokens are in a given prompt. Occasionally useful information, as how tokens are counted varies across LLMs
- `!<trigger> image <your_size> <your_format> <user_prompt>`: Traditional image generation request
  - `<your_size>`: Passed directly to the LLM, usually expects something like "256x256"
  - `<your_format>`: Passed directly to the LLM. `jpeg` or `png` are most common, some backends also support `webp` as an option
  - `<user_prompt>`: Input and results will vary heavily depending on the backend LLM (ex: some backends expect full sentences, others expect comma-separated "tags")
- `!<trigger> alter <user_prompt>`: Request an altered image based on an existing image the user provides
  - `<user_prompt>`: Input and results will vary heavily depending on the backend LLM (ex: some backends expect full sentences, others expect comma-separated "tags")

# Limitations

Most OpenAI-compatible endpoints allow for a parameter (`n`) to generate more than one response to a given request. In all cases this has been capped at `1` to avoid overwhelming any chat rooms this plugin is integrated into.

The [Matrix Specification](https://spec.matrix.org/latest/client-server-api) does not currently provide for containing multiple images in a single post, either via upload or via download. This impacts a few features:
- Multi-modal chat: Only one image can be sent to this plugin, and only the first image the backend LLM returns (if there were multiple) is selected
- Image generation: Only one image is returned from the LLM
  - Affected by the `n` variable above, so in theory LLMs wouldn't send more than one anyway
- Image edit: "Mask" or "partial" images aren't supported

# Configuration

All options are found in `base-config.yaml`.

## `allowlist`

Any user added to this array is allowed to use the plugin commands. What they see and how the bot responds can be further refined by [adminlist](#adminlist).

### Examples:
```
# Allow only "user" and "admin" from the chat domain "example.com" to query the plugin
allowlist = ["@user:example.com", "@admin:example.com"]
```
```
# Allow anyone in the room to query the plugin
allowlist = False
```

## `adminlist`

Any user added to this array is allowed full access to the plugin commands and sees everything they return. The following commands only work for admins: `backend`, `model`, `system`, and `clear`. The `info` command will display full details (instead of "<hidden>") for the current system prompt and the list of available backend models.

### Examples
```
# Allow "admin" from the chat domain "example.com" to fully use all commands
adminlist = ["@admin:example.com"]
```
```
# Allow all users to fully use all commands, but still only if they are on the allowlist
adminlist = False
```

## `default_backend`

The default backend used by the plugin in any room until changed for that room. The value must correspond to one of the entries within the next section below.

## `backends`

### local
Represents any OpenAI-compatible server

All fields except `type` and `base_url` are optional. `base_url` is passed directly, the only processing done is a check to see whether the OpenAI-compatible endpoints are available at `<base_url>/v1/` (example: llama.cpp) or just `<base_url>/`.

```
local:
  type: basic_openai
  base_url: "http://localhost:1234"
  # If you use a separate local OpenAI-compatible backend for images
  #   (such as Stable Diffusion) then enter that URL here
  img_url: null
  # Ignore unless your local backend requires an API key
  api_key: YOUR_KEY_HERE
  default_model: null
  default_system_prompt: "You are a helpful digital assistant."
```

### openai
Connect to OpenAI directly. All fields are required.

```
openai:
  type: openai
  api_key: YOUR_KEY_HERE
  default_model: gpt-4-turbo
```

### anthropic
Connect to Anthropic directly. All fields are required.

```
anthropic:
  type: anthropic
  api_key: YOUR_KEY_HERE
  max_tokens: 1024
  default_model: claude-3-opus-20240229
```

## `customization`

Options that only affect the plugin's interaction with Matrix users.

### custom_trigger

**Required field**
Unlike brokensandals' original version of this plugin, users must "tag" the bot to get a response. This is done by using an exclamation mark followed by this configured trigger.

Example:
```
# The following would mean a user could send the command "!crazypants info" in a chat room
custom_trigger: crazypants
```

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