# opencode-anthropic-context-1m

OpenCode plugin that enables the 1,000,000 token context window for supported Anthropic Claude models by injecting the `anthropic-beta: context-1m-2025-08-07` header on API calls.

## Context Limits

| Model | Default | With Plugin |
|-------|---------|-------------|
| Claude Opus 4.6 | 200,000 tokens | 1,000,000 tokens |
| Claude Sonnet 4.6 | 200,000 tokens | 1,000,000 tokens |
| Claude Sonnet 4.5 | 200,000 tokens | 1,000,000 tokens |

## Installation

```bash
# In your OpenCode profile directory
bun add opencode-anthropic-context-1m
# or
npm install opencode-anthropic-context-1m
```

Then configure `opencode.json` -- **both the plugin registration and the model limit are required**:

```json
{
  "plugin": [
    "opencode-anthropic-context-1m"
  ],
  "provider": {
    "anthropic": {
      "models": {
        "claude-opus-4-6": {
          "limit": {
            "context": 1000000,
            "output": 128000
          }
        }
      }
    }
  }
}
```

## How It Works

Two layers work together:

### 1. Plugin Layer (API Header Injection)

The plugin hooks into OpenCode's `chat.headers` lifecycle. For every API request to a supported Anthropic model, it appends `context-1m-2025-08-07` to the `anthropic-beta` header. This tells Anthropic's API to allow up to 1M tokens of input context.

The plugin is additive -- it reads any existing `anthropic-beta` value (e.g., from other beta features like interleaved thinking) and appends rather than replaces.

### 2. Config Layer (OpenCode Limit Override)

Setting `limit.context` to `1000000` in `opencode.json` tells OpenCode itself that the model supports 1M tokens. Without this, OpenCode would truncate conversation history at 200K tokens before even sending the request, regardless of what the API allows.

**Both layers are required.** The plugin without the config means the API accepts 1M but OpenCode truncates at 200K. The config without the plugin means OpenCode sends 1M but the API rejects it.

## Source Code

```typescript
import type { Plugin } from "@opencode-ai/plugin";

const BETA_FLAG = "context-1m-2025-08-07";

const SUPPORTED_MODELS = [
  "opus-4-6", "opus-4.6",
  "sonnet-4-6", "sonnet-4.6",
  "sonnet-4-5", "sonnet-4.5",
];

function isSupported(id: string): boolean {
  return id.includes("claude") && SUPPORTED_MODELS.some((m) => id.includes(m));
}

export const plugin: Plugin = async () => ({
  "chat.headers": async (input, output) => {
    if (input.model.providerID !== "anthropic") return;
    if (!isSupported(input.model.api.id)) return;

    const sdk =
      (input.provider?.options as Record<string, any>)?.headers?.[
        "anthropic-beta"
      ] ?? "";
    const existing = output.headers["anthropic-beta"] ?? sdk;

    if (existing.includes(BETA_FLAG)) return;
    output.headers["anthropic-beta"] = existing
      ? `${existing},${BETA_FLAG}`
      : BETA_FLAG;
  },
});

export default plugin;
```

The model matching checks that:
1. The model ID contains `claude`
2. The model ID contains one of the supported version strings (`opus-4-6`, `sonnet-4.5`, etc.)

This handles both hyphenated and dotted model ID formats (e.g., `claude-opus-4-6` and `claude-opus-4.6`).

## Verification

### Method 1: Configuration Check

Verify the full chain is wired correctly:

- [ ] Plugin appears in `opencode.json` `"plugin"` array
- [ ] Model `limit.context` is set to `1000000` in `opencode.json`
- [ ] `dist/index.js` exists (plugin is compiled)
- [ ] Your model ID matches a supported pattern (contains `claude` + a supported version string)
- [ ] Provider is `anthropic` (not a proxy or alternative provider)

### Method 2: Live Context Test

The definitive proof is pushing a session past 200K tokens and verifying the model still responds. Without the 1M beta header, the Anthropic API returns HTTP 400 when context exceeds the model's default limit.

**Test procedure:**

1. Generate a large file with unique markers at known positions:
   ```bash
   python3 test/generate-context-payload.py
   ```
2. In an OpenCode session with the plugin active, read the generated file in chunks using the assistant's file read tool
3. After loading enough content to push total context past 200K tokens, ask the assistant to recall the markers
4. If the assistant responds correctly, the 1M context window is active

**Verified test results (2025-03-12, claude-opus-4-6 via OpenCode):**

A file of 840,979 bytes (~210,000 tokens) was generated with 14 blocks, each containing a unique random marker. Seven blocks were loaded into a conversation that already contained ~50K tokens of system prompts and prior messages, pushing total context well past 200,000 tokens.

All markers were successfully recalled:

```
BLOCK_0: N9RS18EY2ZJL  (line 1,    offset ~0)
BLOCK_1: 40NZ6DPWWT6T  (line 456,  offset ~60K)
BLOCK_2: UOSMKYH4KF8Y  (line 912,  offset ~120K)
BLOCK_3: AZDXCZ4L1H32  (line 1375, offset ~180K)
BLOCK_4: SJXJ0N6J9E6V  (line 1829, offset ~240K)
BLOCK_5: JV0RHKCN7MQ9  (line 2277, offset ~300K)
BLOCK_6: NMOVFI03F8O2  (line 2722, offset ~360K)
```

OpenCode's context monitor confirmed: **204,300 tokens used out of 1,000,000 (20.4%)** -- exceeding the 200K default limit while maintaining full functionality.

## Building

```bash
bun install
bun run build  # runs tsc
```

## License

MIT
