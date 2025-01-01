from __future__ import annotations

import re
import xml.etree.ElementTree as etree

from markdown import Markdown, util
from markdown.blockprocessors import BlockQuoteProcessor
from markdown.extensions import Extension


class ObsidianCalloutsBlockProcessor(BlockQuoteProcessor):
    CALLOUT_PATTERN = re.compile(
        r"""
        # Group 1: Leading content/whitespace
        ((?:^|\n) *(?:[^>].*)?(?:^|\n))

        # Callout start: up to 3 spaces followed by >
        [ ]{0,3}>[ ]*

        # Group 2: Callout type inside [! ]
        \[!([A-Za-z0-9_-]+)\]

        # Group 3: Optional fold marker (+ or -)
        ([-+]?)[ ]*

        # Group 4: Title text
        (.*?)(?:\n|$)

        # Group 5: Content (lines starting with >)
        ((?:(?:>[ ]*[^\n]*\n?)*))
        """,
        flags=re.MULTILINE | re.IGNORECASE | re.VERBOSE,
    )

    def test(self, parent, block):
        return (
            bool(self.CALLOUT_PATTERN.search(block))
            and not self.parser.state.isstate("blockquote")
            and not util.nearing_recursion_limit()
        )

    def run(self, parent: etree.Element, blocks: list[str]) -> None:
        block = blocks.pop(0)
        m = self.CALLOUT_PATTERN.search(block)
        assert m

        before = block[: m.start()]
        if before.strip():
            self.parser.parseBlocks(parent, [before])

        kind = m[2]
        fold = m[3]
        title = m[4]
        content = m[5] or ""

        # Clean up the content lines
        content = "\n".join(self.clean(line) for line in content.split("\n"))

        # Create the main callout container
        admon = etree.SubElement(
            parent, "div", {"class": "callout", "data-callout": kind.lower()}
        )

        # Create title container
        title_container = etree.SubElement(admon, "div", {"class": "callout-title"})

        # Add icon container
        icon_container = etree.SubElement(
            title_container, "div", {"class": "callout-icon"}
        )
        # For now, using simple emoji icons - you might want to replace with proper SVG icons
        icon_map = {
            "note": "📝",
            "abstract": "📄",
            "document": "📄",
            "info": "ℹ️",
            "todo": "✅",
            "tip": "💡",
            "success": "✅",
            "question": "❓",
            "warning": "⚠️",
            "failure": "❌",
            "danger": "⛔",
            "bug": "🐛",
            "example": "📋",
            "quote": "💬",
        }
        icon_container.text = icon_map.get(kind.lower(), "📝")

        # Add title text
        title_inner = etree.SubElement(
            title_container, "div", {"class": "callout-title-inner"}
        )
        title_inner.text = title.strip() if title.strip() else kind.title()

        # Only add content div if there is content
        if content.strip():
            content_div = etree.SubElement(admon, "div", {"class": "callout-content"})
            self.parser.state.set("blockquote")
            self.parser.parseChunk(content_div, content)
            self.parser.state.reset()

        # Handle any remaining content
        if m.end() < len(block):
            blocks.insert(0, block[m.end() :])


class ObsidianCalloutsExtension(Extension):
    @classmethod
    def extendMarkdown(cls, md: Markdown) -> None:
        parser = md.parser
        parser.blockprocessors.register(
            ObsidianCalloutsBlockProcessor(md.parser),
            "obsidian-callouts",
            21.1,  # Priority just before blockquote
        )


makeExtension = ObsidianCalloutsExtension  # noqa: N816
