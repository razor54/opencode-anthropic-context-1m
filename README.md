# opencode-anthropic-context-1m

An [OpenCode](https://opencode.ai) plugin that enables the **1M context window** for supported Anthropic Claude models.

## Why?

Anthropic's Claude models (Opus 4.6, Sonnet 4.6, Sonnet 4.5, Sonnet 4) support up to 1 million tokens of context, but this requires a specific beta header (`anthropic-beta: context-1m-2025-08-07`) on every API request. Without it, the API caps context at 200K tokens.

This plugin automatically appends the required header — no manual configuration needed.

## Supported Models

| Model | Context |
|-------|---------|
| Claude Opus 4.6 | 1,000,000 |
| Claude Sonnet 4.6 | 1,000,000 |
| Claude Sonnet 4.5 | 1,000,000 |
| Claude Sonnet 4 | 1,000,000 |

## Installation

Add to your `opencode.json` plugins list:

```json
{
  "plugin": [
    "opencode-anthropic-context-1m"
  ]
}
```

Then install the package:

```bash
bun add opencode-anthropic-context-1m
```

You'll also want to override the model's context limit in your `opencode.json` so OpenCode knows to use the full window:

```json
{
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

The plugin hooks into OpenCode's `chat.headers` lifecycle to append the `context-1m-2025-08-07` flag to the `anthropic-beta` header. It reads the existing header value and appends (rather than replaces), so other beta features like interleaved thinking continue to work.

## Verify

Run `opencode debug config` and check that:

1. The plugin appears in the resolved `plugin` array
2. Your model's `limit.context` shows `1000000`

## License

MIT
