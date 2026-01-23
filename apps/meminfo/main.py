#!/usr/bin/env python3
"""AI Memorization App - Generate memorization guides from markdown/PDF files."""

import argparse
from pathlib import Path
from file_reader import read_file
from groq_client import generate_memorization_guide


def main():
    parser = argparse.ArgumentParser(
        description="Generate AI-powered memorization guides"
    )
    parser.add_argument("input", help="Input file (markdown or PDF)")
    parser.add_argument(
        "-o", "--output", help="Output markdown file (default: {input}_memorization.md)"
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = (
        Path(args.output)
        if args.output
        else input_path.with_name(f"{input_path.stem}_memorization.md")
    )

    print(f"📖 Reading: {input_path}")
    content = read_file(str(input_path))

    print("🤖 Generating memorization guide using Groq AI...")
    guide = generate_memorization_guide(content)

    output_path.write_text(guide, encoding="utf-8")
    print(f"✅ Saved: {output_path}")


if __name__ == "__main__":
    main()
