import html
import logging
import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

import markdown2
import yaml
from images import compress_image, filter_invalid_images
from render import add_line_numbers

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass(frozen=True)
class Config:
    base_dir: Path = Path(__file__).parent.resolve()
    posts_dir: Path = base_dir / "posts"
    pages_dir: Path = base_dir / "pages"
    output_dir: Path = base_dir / "build"
    template_path: Path = base_dir / "static" / "template.html"
    static_dir: Path = base_dir / "static"


@dataclass(frozen=True)
class Page:
    name: str  # e.g. 'about'
    filename: str  # e.g. 'about.html'
    display_name: str  # e.g. 'About'


@dataclass
class Post:
    code: str
    title: str
    date: datetime
    tags: List[str]
    excerpt: str
    content_html: str
    link_path: Path  # relative path used in links


def load_template(template_path: Path) -> str:
    """
    Read the template file.
    """
    return template_path.read_text(encoding="utf-8")


def discover_pages(pages_dir: Path) -> List[Page]:
    """
    Return a sorted list of Page objects found in *pages_dir*.
    """
    pages = []

    for entry in sorted(pages_dir.iterdir()):
        if entry.suffix.lower() == ".html":
            name = entry.stem
            display_name = name.capitalize()
            pages.append(
                Page(name=name, filename=entry.name, display_name=display_name)
            )
    return pages


def generate_nav_links(pages: List[Page]) -> str:
    """
    Build the navigation bar (Home + each page).
    """
    links = ['<a href="/">Home</a>\n']
    for page in pages:
        links.append(f'<a href="/{page.filename}">{page.display_name}</a>\n')
    return "".join(links)


def ensure_dirs(paths: Iterable[Path]) -> None:
    """
    Create directories if they don't exist.
    """
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def extract_front_matter(md_text: str) -> Tuple[Dict, str]:
    """
    Split *md_text* into (metadata_dict, body_text).

    Front-matter is expected to be wrapped in `---` at the start of the file.
    """
    if md_text.startswith("---"):
        parts = md_text.split("---", 2)
        front_matter_yaml = parts[1]
        body = parts[2] if len(parts) > 2 else ""
        metadata = yaml.safe_load(front_matter_yaml) or {}
        return metadata, body

    return {}, md_text


def extract_title(body: str) -> str:
    """
    Return the first H1 heading from *body*.
    Falls back to the very first non-empty line if no H1 is found.
    """
    match = re.search(r"^#\s*(.*)", body, flags=re.MULTILINE)

    if match:
        return match.group(1).strip()
    lines = [ln for ln in body.splitlines() if ln.strip()]

    return lines[0].strip() if lines else "Untitled"


def extract_tags_from_title(title: str) -> Tuple[List[str], str]:
    """
    Detect leading `[Tag]` tokens and return them along with the cleaned title.
    Example: "[news][python] My Post" → (["news", "python"], "My Post")
    """
    tags = []
    match = re.match(r"^\s*((?:$[^$]+$\s*)+)", title)
    if match:
        prefix = match.group(1)
        tags = [t.strip() for t in re.findall(r"$([^$]+)$", prefix)]
        title = title[len(prefix) :].strip()

    return tags, title


def extract_excerpt(body: str) -> str:
    """
    Grab the first paragraph (or first block of text separated by double newlines),
    convert it to Markdown → HTML → plain text and truncate to 150 chars.
    """
    paragraphs = [p for p in body.split("\n\n") if p.strip()]
    if not paragraphs:
        return ""

    first_para = paragraphs[0]
    html_frag = markdown2.markdown(
        first_para,
        extras=["fenced-code-blocks", "header-ids"],
    )
    text = re.sub(r"<[^>]+>", "", html_frag).strip().replace("\n", " ")

    if len(text) > 150:
        return text[:147].rstrip() + "..."

    return text


def convert_markdown(md: str) -> str:
    """
    Render Markdown to HTML with the required extras.
    """
    return markdown2.markdown(
        md,
        extras=["fenced-code-blocks", "header-ids", "mermaid", "codehilite"],
    )


def process_post(
    post_code: str, post_dir: Path, output_images_dir: Path, img_set: Set[str]
) -> Post | None:
    """
    Read a single post, parse its content and return a `Post` object.

    *post_dir* must contain an `index.md`.  Images are copied/compressed to
    *output_images_dir*.  Duplicate images across posts are skipped.
    """
    index_md = post_dir / "index.md"
    if not index_md.is_file():
        logging.warning(f"Missing index.md in {post_dir}")
        return None

    md_text = index_md.read_text(encoding="utf-8")
    metadata, body = extract_front_matter(md_text)

    raw_title = extract_title(body)
    date_str = metadata.get("date", "01-01-1997")
    try:
        date_obj = datetime.strptime(date_str, "%m-%d-%Y")
    except ValueError:
        logging.warning(
            f"Invalid date '{date_str}' in {post_code}, defaulting to 01-01-1997"
        )
        date_obj = datetime(1997, 1, 1)

    # Tag get
    if isinstance(metadata.get("tags"), list):
        tags = metadata["tags"]
    elif isinstance(metadata.get("tags"), str):
        tags = [t.strip() for t in metadata["tags"].split(",") if t.strip()]
    else:
        tags = []

    title = raw_title
    if not tags:  # try to pull tags from the title itself
        extracted, cleaned = extract_tags_from_title(raw_title)
        tags = extracted
        title = cleaned

    # Front-matter can override the title
    title = metadata.get("title", title)
    body = re.sub(r"(?m)^#\s*(?:$[^$]+$\s*)*(.*)$", r"# \1", body, count=1)

    excerpt_text = extract_excerpt(body)

    # Markdown + Code helpers
    html_content = convert_markdown(body)
    html_content = add_line_numbers(html_content)

    # Tag write
    if tags:
        tag_html = (
            '<div class="post-meta"><div class="tags">'
            + "".join(f'<span class="tag">{t}</span>' for t in tags)
            + "</div></div>"
        )
        if "</h1>" in html_content:
            html_content = html_content.replace("</h1>", f"</h1>{tag_html}", 1)
        else:
            html_content = tag_html + html_content
    # Fix image paths
    html_content = html_content.replace('<img src="', '<img src="/posts/images/')

    for img_name in filter_invalid_images(post_dir):
        if img_name in img_set:
            continue
        src_path = post_dir / img_name
        dst_path = output_images_dir / img_name
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        compress_image(src_path, dst_path, quality=85)
        img_set.add(img_name)

    link_path = Path("posts") / f"{post_code}.html"

    return Post(
        code=post_code,
        title=title,
        date=date_obj,
        tags=tags,
        excerpt=excerpt_text,
        content_html=html_content,
        link_path=link_path,
    )


def render_template(template: str, content: str, nav_links: str) -> str:
    """
    Replace placeholders in the template.
    """
    return template.replace("{{ content }}", content).replace(
        "{{ nav_links }}", nav_links
    )


def render_posts(
    posts: List[Post], template: str, nav_links: str, output_dir: Path
) -> None:
    """
    Write each post's rendered HTML to *output_dir*.
    """
    for post in posts:
        rendered = render_template(template, post.content_html, nav_links)
        out_path = output_dir / f"{post.code}.html"
        out_path.write_text(rendered, encoding="utf-8")
        logging.info(f"Rendered {post.code} → {out_path.name}")


def build_landing_list(posts: List[Post]) -> str:
    """
    Return the HTML snippet for the landing page list of posts.
    """
    if not posts:
        return ""

    items = []

    for post in posts:
        title_html = html.escape(post.title)
        href = post.link_path.as_posix()  # e.g. 'posts/2024-01-index.html'
        date_iso = post.date.strftime("%Y-%m-%d")
        date_disp = post.date.strftime("%b %d, %Y")
        meta_html = f'<div class="post-meta"><time datetime="{date_iso}">{date_disp}</time></div>'
        items.append(
            f'<div class="landing-item">'
            f'<a class="landing-title" href="{href}">{title_html}</a>{meta_html}'
            f"</div>"
        )

    return '<div class="landing-list">\n' + "\n".join(items) + "\n</div>"


def render_pages(
    pages: List[Page],
    posts: List[Post],
    template: str,
    nav_links: str,
    output_dir: Path,
) -> None:
    """
    Render the static pages (including index with post list).
    """
    landing_list = build_landing_list(posts)

    for page in pages:
        page_path = Config.pages_dir / page.filename
        page_content = page_path.read_text(encoding="utf-8")

        content = page_content
        if page.name == "index":
            content += landing_list

        rendered_page = render_template(template, content, nav_links)
        out_name = "index.html" if page.name == "index" else page.filename
        out_path = output_dir / out_name
        out_path.write_text(rendered_page, encoding="utf-8")
        logging.info(f"Rendered {out_name}")


def copy_static(static_dir: Path, output_dir: Path) -> None:
    """
    Copy all files (and sub-directories) from *static_dir* to *output_dir*.
    """
    for item in static_dir.iterdir():
        dest = output_dir / item.name
        if item.is_file():
            shutil.copy2(item, dest)
        else:
            shutil.copytree(item, dest, dirs_exist_ok=True)


def ssg() -> None:
    """
    Run the static site generator.
    """
    config = Config()

    template = load_template(config.template_path)
    pages = discover_pages(config.pages_dir)
    nav_links = generate_nav_links(pages)

    ensure_dirs(
        {
            config.output_dir,
            config.output_dir / "posts",
            config.output_dir / "posts" / "images",
        }
    )

    img_set: Set[str] = set()
    posts: List[Post] = []

    for entry in sorted(config.posts_dir.iterdir()):
        if not entry.is_dir():
            continue
        post = process_post(
            entry.name, entry, config.output_dir / "posts" / "images", img_set
        )
        if post:
            posts.append(post)

    posts.sort(key=lambda p: p.date, reverse=True)
    render_posts(posts, template, nav_links, config.output_dir / "posts")
    render_pages(pages, posts, template, nav_links, config.output_dir)
    copy_static(config.static_dir, config.output_dir)


if __name__ == "__main__":
    import argparse
    import asyncio

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dev", action="store_true", help="Run dev server with live reload"
    )
    parser.add_argument("--host", default="127.0.0.1", help="Dev server host")
    parser.add_argument("--port", type=int, default=8000, help="Dev server port")
    args = parser.parse_args()

    ssg()

    live_env = os.getenv("LIVE_RELOAD")
    if args.dev or (live_env and live_env != "0"):
        # Import dev server only when requested so CI remains unaffected
        from dev_server import run_dev

        try:
            asyncio.run(run_dev(ssg, host=args.host, port=args.port))
        except KeyboardInterrupt:
            print("Dev server stopped")
