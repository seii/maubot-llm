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

All fields except `type` and `base_url` are optional. `base_url` is used directly in API calls to the backend, so if you're a llama.cpp or stable-diffusion.cpp user you will want to add `/v1` to the end of this value.

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
