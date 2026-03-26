import re
from pathlib import Path
from typing import List
import logging
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(default=True),
)
_codehilite_template = jinja_env.get_template("codehilite.html")
_post_tags_template = jinja_env.get_template("post-tags.html")


def add_line_numbers(html_content: str) -> str:
    """
    Idempotently add line-number spans to code blocks.

    If the block already contains a span with class "ln" we skip it.
    """

    def add_lines_to_block(code_block: str) -> str:
        lines = code_block.rstrip("\n").split("\n")
        numbered_lines = [f'<span class="ln">{i}</span>{line}' for i, line in enumerate(lines, 1)]
        return "\n".join(numbered_lines)

    def process_codehilite(match: re.Match) -> str:
        code_block = match.group(1)
        if "class=\"ln\"" in code_block or "<span class=\"ln\"" in code_block:
            return match.group(0)
        numbered = add_lines_to_block(code_block)
        return _codehilite_template.render(code=numbered)

    html_content = re.sub(
        r'<div class="codehilite">\s*<pre><span></span><code>(.*?)</code></pre>\s*</div>',
        process_codehilite,
        html_content,
        flags=re.DOTALL,
    )

    def process_plain(match: re.Match) -> str:
        code_block = match.group(1)
        if "class=\"ln\"" in code_block or "<span class=\"ln\"" in code_block:
            return match.group(0)
        numbered = add_lines_to_block(code_block)
        return _codehilite_template.render(code=numbered)

    html_content = re.sub(r"<pre><code>(.*?)</code></pre>", process_plain, html_content, flags=re.DOTALL)

    return html_content


def inject_tags_and_fix_image_paths(html_content: str, tags: List[str], post_code: str) -> str:
    """
    Insert tags HTML after the first H1 and rewrite local image src paths.

    Local relative image sources (not starting with '/', 'http', or 'data:') are rewritten
    to `/posts/images/{post_code}/{filename}`. External or absolute URLs are left untouched.
    """
    if tags:
        tag_html = _post_tags_template.render(tags=tags)
        if "</h1>" in html_content:
            html_content = html_content.replace("</h1>", f"</h1>{tag_html}", 1)
        else:
            html_content = tag_html + html_content

    # Replace only relative/local src attributes
    def _repl_img(match: re.Match) -> str:
        prefix = match.group(1)
        quote = match.group(2)
        src = match.group(3)
        # Skip absolute or data URIs
        if src.startswith("/") or src.startswith("http://") or src.startswith("https://") or src.startswith("data:"):
            return match.group(0)
        new_src = f"/posts/images/{post_code}/{Path(src).name}"
        return f"{prefix}src={quote}{new_src}{quote}"

    img_pattern = re.compile(r"(<img\b[^>]*?)src=(['\"])([^'\"]+)\2", flags=re.IGNORECASE)
    html_content = img_pattern.sub(_repl_img, html_content)

    return html_content
