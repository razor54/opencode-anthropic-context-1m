#!/usr/bin/env python3
"""
Generate a large file with unique markers for verifying 1M context window support.

Usage:
    python3 test/generate-context-payload.py [output_file] [target_bytes]

Defaults:
    output_file: context-test-payload.txt (in current directory)
    target_bytes: 900000 (~225K tokens, exceeds 200K default limit)

The generated file contains blocks of realistic-looking TypeScript code with
unique random markers at known positions. Load this file into an OpenCode
session with the plugin active — if the assistant can recall the markers after
the total context exceeds 200K tokens, the 1M context window is working.
"""

import random
import string
import sys
import os
import json


def generate_marker(prefix: str, length: int = 12) -> str:
    return (
        prefix
        + "_"
        + "".join(random.choices(string.ascii_uppercase + string.digits, k=length))
    )


def generate_payload(output_file: str, target_bytes: int) -> dict:
    lines: list[str] = []
    markers: dict[str, str] = {}
    chars_written = 0
    line_num = 0
    block_id = 0
    block_size = target_bytes // 14  # 14 blocks
    next_block = block_size

    # First marker
    marker = generate_marker("BLOCK_0")
    markers["BLOCK_0"] = marker
    lines.append(f"=== BLOCK_0 MARKER: {marker} === (approx char offset: 0)")
    chars_written += len(lines[-1]) + 1
    line_num += 1

    while chars_written < target_bytes:
        if chars_written >= next_block:
            block_id += 1
            marker = generate_marker(f"BLOCK_{block_id}")
            markers[f"BLOCK_{block_id}"] = marker
            line = f"=== BLOCK_{block_id} MARKER: {marker} === (approx char offset: {chars_written})"
            lines.append(line)
            next_block += block_size
        else:
            # Generate varied realistic-looking code
            nums = ", ".join([str(random.randint(0, 999)) for _ in range(20)])
            templates = [
                f'const config_{block_id}_{line_num} = {{ host: "db-{block_id}.cluster.internal", port: {5432 + block_id}, pool: {random.randint(5, 50)}, ssl: true }};',
                f'export async function handle_{block_id}_{line_num}(req: Request): Promise<Response> {{ const data = await db.query("SELECT * FROM table_{block_id} WHERE id = $1", [req.params.id]); return Response.json(data); }}',
                f"/** @deprecated since v{block_id}.{line_num}.0 - use new{block_id}Handler instead */ export class Legacy_{block_id}_{line_num} extends BaseHandler {{ override process() {{ return this.fallback(); }} }}",
                f"const metrics_{block_id}_{line_num} = {{ latency_p50: {random.uniform(1, 100):.2f}, latency_p99: {random.uniform(100, 2000):.2f}, error_rate: {random.uniform(0, 0.05):.4f}, throughput: {random.randint(100, 10000)} }};",
                f'if (feature_flags.get("experiment_{block_id}_{line_num}")) {{ analytics.track("variant_b", {{ user_id: ctx.userId, cohort: "{random.choice(["control", "treatment_a", "treatment_b"])}" }}); }}',
            ]
            line = random.choice(templates)
            lines.append(line)

        chars_written += len(lines[-1]) + 1
        line_num += 1

    # Final marker
    block_id += 1
    marker = generate_marker("FINAL")
    markers["FINAL"] = marker
    lines.append(
        f"=== FINAL MARKER: {marker} === (approx char offset: {chars_written})"
    )

    content = "\n".join(lines)
    with open(output_file, "w") as f:
        f.write(content)

    return {
        "file": output_file,
        "bytes": len(content),
        "lines": len(lines),
        "estimated_tokens": len(content) // 4,
        "markers": markers,
    }


def main():
    output_file = sys.argv[1] if len(sys.argv) > 1 else "context-test-payload.txt"
    target_bytes = int(sys.argv[2]) if len(sys.argv) > 2 else 900_000

    print(f"Generating context test payload...")
    print(f"  Target: {target_bytes:,} bytes (~{target_bytes // 4:,} tokens)")
    print(f"  Output: {output_file}")
    print()

    result = generate_payload(output_file, target_bytes)

    print(f"Generated:")
    print(f"  Bytes:  {result['bytes']:,}")
    print(f"  Lines:  {result['lines']:,}")
    print(f"  Tokens: ~{result['estimated_tokens']:,} (estimated)")
    print(f"  Blocks: {len(result['markers'])}")
    print()
    print("MARKERS (use these to verify recall in your OpenCode session):")
    print("-" * 60)
    for key, value in result["markers"].items():
        print(f"  {key}: {value}")
    print("-" * 60)
    print()
    print("NEXT STEPS:")
    print("  1. Start an OpenCode session with this plugin active")
    print("  2. Ask the assistant to read the generated file in chunks")
    print("  3. After loading enough to exceed 200K total tokens,")
    print("     ask the assistant to list all the markers it found")
    print("  4. If markers are recalled correctly, 1M context is working")
    print()
    print(f"  Without the plugin, the API would reject requests")
    print(f"  exceeding ~200K tokens with HTTP 400.")

    # Also save markers as JSON for programmatic verification
    markers_file = os.path.splitext(output_file)[0] + "-markers.json"
    with open(markers_file, "w") as f:
        json.dump(result["markers"], f, indent=2)
    print(f"\n  Markers saved to: {markers_file}")


if __name__ == "__main__":
    main()
