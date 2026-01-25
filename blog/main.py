import os
import shutil
from datetime import datetime
import re
import html

import markdown2
import yaml
from PIL import Image


def add_line_numbers(html_content):
    """Add line numbers to code blocks."""
    import re

    def add_lines_to_block(code_block):
        # Remove trailing empty lines for counting
        lines = code_block.rstrip("\n").split("\n")
        numbered_lines = []

        for i, line in enumerate(lines, 1):
            numbered_lines.append(f'<span class="ln">{i}</span>{line}')

        return chr(10).join(numbered_lines)

    # Find all codehilite code blocks and add line numbers
    def process_codehilite(match):
        code_block = match.group(1)
        numbered = add_lines_to_block(code_block)
        return f'<div class="codehilite"><pre><span></span><code>{numbered}</code></pre></div>'

    html_content = re.sub(
        r'<div class="codehilite">\s*<pre><span></span><code>(.*?)</code></pre>\s*</div>',
        process_codehilite,
        html_content,
        flags=re.DOTALL,
    )

    # Find all plain code blocks (txt, without codehilite) and add line numbers
    # Also wrap them in codehilite div for consistent styling
    def process_plain(match):
        code_block = match.group(1)
        numbered = add_lines_to_block(code_block)
        return f'<div class="codehilite"><pre><span></span><code>{numbered}</code></pre></div>'

    html_content = re.sub(
        r"<pre><code>(.*?)</code></pre>", process_plain, html_content, flags=re.DOTALL
    )

    return html_content


def check_image_valid(image_path):
    try:
        with Image.open(image_path) as img:
            img.verify()  # Verify that it is, in fact an image
        return True
    except (IOError, SyntaxError):
        # Invalid, don't spam logs.
        return False


def filter_invalid_images(base_path):
    potential_images = os.listdir(base_path)
    images = [
        img if check_image_valid(os.path.join(base_path, img)) else None
        for img in potential_images
    ]

    return [img for img in images if img is not None]


def compress_image(image_path, output_path, quality=50):
    try:
        with Image.open(image_path) as img:
            # Handle some of my screenshots being in RGBA mode
            rgb_im = img.convert("RGB")
            # Resize to maximum 1280 pixels on the longest side
            max_size = 720
            rgb_im.thumbnail((max_size, max_size))
            rgb_im.save(output_path, "WEBP", quality=quality)
    except Exception as e:
        print(f"Error compressing image {image_path}: {e}")


def ssg():
    # Directory configuration
    POSTS_DIR = os.path.abspath("posts")
    OUTPUT_DIR = os.path.abspath(os.path.join(os.getcwd(), "../build"))
    OUTPUT_POSTS_DIR = os.path.join(OUTPUT_DIR, "posts")
    OUTPUT_IMAGES_DIR = os.path.join(OUTPUT_POSTS_DIR, "images")

    # Read template.html
    with open("static/template.html", "r", encoding="utf-8") as file:
        template = file.read()

    # Discover and process HTML pages
    pages_dir = "pages"
    html_pages = []
    for filename in sorted(os.listdir(pages_dir)):
        if filename.endswith(".html"):
            page_name = filename[:-5]  # Remove .html extension
            html_pages.append(
                {
                    "name": page_name,
                    "filename": filename,
                    "display_name": page_name.capitalize(),
                }
            )

    # Generate navigation links for HTML pages
    nav_links = '<a href="/">Home</a>\n'
    for page in html_pages:
        if page["name"] != "landing":  # Don't add landing page link, it's the home
            nav_links += (
                f'          <a href="/{page["filename"]}">{page["display_name"]}</a>\n'
            )

    for d in [OUTPUT_DIR, OUTPUT_POSTS_DIR, OUTPUT_IMAGES_DIR]:
        os.makedirs(d, exist_ok=True)

    posts = []

    # Iterate over all dirs in the posts directory
    for post_code in os.listdir(POSTS_DIR):
        post_dir = os.path.join(POSTS_DIR, post_code)

        # Construct full file path
        file_path = os.path.join(post_dir, "index.md")

        # Read the Markdown file
        with open(file_path, "r", encoding="utf-8") as file:
            md_content = file.read()

        parsed = {}
        title = md_content.split("# ", 1).pop(1).split("\n").pop(0)
        # Find first line which contains "# "
        if md_content.startswith("---"):
            front_matter = md_content.split("---", 2)[1]
            parsed = yaml.safe_load(front_matter)

            title = parsed.get("title", title)
            date = parsed.get("date", "01-01-1997")
            md_content = md_content.split("---", 2)[2]
        else:
            date = "01-01-1997"

        # Extract tags from front-matter (if provided) or from bracketed tokens in title
        tags = []
        if "parsed" in locals():
            raw_tags = parsed.get("tags")
            if isinstance(raw_tags, str):
                tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
            elif isinstance(raw_tags, list):
                tags = raw_tags

        # If no tags from front-matter, try to extract leading [Tag] tokens from the title
        prefix_match = re.match(r"^\s*((?:\[[^\]]+\]\s*)+)", title)
        if prefix_match and not tags:
            prefix = prefix_match.group(1)
            tags = [t.strip() for t in re.findall(r"\[([^\]]+)\]", prefix)]
            title = title[len(prefix) :].strip()

        # Ensure the H1 in md_content does not contain bracketed tags
        md_content = re.sub(
            r"(?m)^#\s*(?:\[[^\]]+\]\s*)*(.*)$", r"# \1", md_content, count=1
        )

        # Extract a short excerpt (first paragraph) for landing
        paragraphs = [p for p in md_content.split("\n\n") if p.strip()]
        if paragraphs:
            first_para = paragraphs[0]
            excerpt_html = markdown2.markdown(
                first_para, extras=["fenced-code-blocks", "header-ids"]
            )
            excerpt_text = (
                re.sub(r"<[^>]+>", "", excerpt_html).strip().replace("\n", " ")
            )
            if len(excerpt_text) > 150:
                excerpt_text = excerpt_text[:147].rstrip() + "..."
        else:
            excerpt_text = ""

        # Convert Markdown to HTML
        html_content = markdown2.markdown(
            md_content,
            extras=["fenced-code-blocks", "header-ids", "mermaid", "codehilite"],
        )

        # Add line numbers to code blocks
        html_content = add_line_numbers(html_content)

        # Inject tags HTML (if any) right after the first H1
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

        # Fix image src paths and render into template
        html_content = html_content.replace('<img src="', '<img src="/posts/images/')
        rendered_template = template.replace("{{ content }}", html_content).replace(
            "{{ nav_links }}", nav_links
        )

        # Copy and compress images from post dir to output images dir
        valid_images = filter_invalid_images(post_dir)
        for image_name in valid_images:
            image_path = os.path.join(post_dir, image_name)
            out_image_path = os.path.join(OUTPUT_IMAGES_DIR, image_name)
            os.makedirs(os.path.dirname(out_image_path), exist_ok=True)
            compress_image(image_path, out_image_path, quality=85)

        # Construct HTML file path
        html_filename = f"{post_code}.html"
        html_path = os.path.join(OUTPUT_POSTS_DIR, html_filename)
        link_path = os.path.join("posts", html_filename)

        # Save the HTML file
        with open(html_path, "w", encoding="utf-8") as file:
            file.write(rendered_template)

        # Append to posts list
        posts.append(
            {
                "title": title,
                "path": link_path,
                "date": datetime.strptime(date, "%m-%d-%Y"),
                "tags": tags,
                "excerpt": excerpt_text,
            }
        )

        print(f"Rendered {post_code} to {html_filename}")

    # Sort posts by date descending
    posts.sort(key=lambda x: x["date"], reverse=True)

    # Load landing.html
    with open("pages/landing.html", "r", encoding="utf-8") as file:
        landing_content = file.read()

    index_html = landing_content

    # Build a compact list of posts with title + date only
    if posts:
        list_items = []
        for post in posts:
            title = html.escape(post["title"])
            path = post["path"]
            date_iso = post["date"].strftime("%Y-%m-%d")
            date_display = post["date"].strftime("%b %d, %Y")
            # Build a compact card with title + date only
            meta_html = f'<div class="post-meta"><time datetime="{date_iso}">{date_display}</time></div>'
            list_items.append(
                f'<div class="landing-item"><a class="landing-title" href="{path}">{title}</a>{meta_html}</div>'
            )
        index_html += '<div class="landing-list">' + "\n".join(list_items) + "</div>"

    index_html = template.replace("{{ content }}", index_html).replace(
        "{{ nav_links }}", nav_links
    )
    index_path = os.path.join(OUTPUT_DIR, "index.html")

    # Load and render interests.html as a separate page
    with open("pages/interests.html", "r", encoding="utf-8") as file:
        interests_html = file.read()

    interests_page = template.replace("{{ content }}", interests_html).replace(
        "{{ nav_links }}", nav_links
    )
    interests_path = os.path.join(OUTPUT_DIR, "interests.html")

    with open(index_path, "w", encoding="utf-8") as file:
        file.write(index_html)

    print("Rendered index.html")

    with open(interests_path, "w", encoding="utf-8") as file:
        file.write(interests_page)

    print("Rendered interests.html")

    # Copy all CSS and JS files from static to output directory
    for static_file in os.listdir("static"):
        shutil.copy2(os.path.join("static", static_file), OUTPUT_DIR)


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
