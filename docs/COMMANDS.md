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