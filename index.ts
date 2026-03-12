import type { Plugin } from "@opencode-ai/plugin";

const BETA_FLAG = "context-1m-2025-08-07";

const SUPPORTED_MODELS = [
  "opus-4-6",
  "opus-4.6",
  "sonnet-4-6",
  "sonnet-4.6",
  "sonnet-4-5",
  "sonnet-4.5",
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
