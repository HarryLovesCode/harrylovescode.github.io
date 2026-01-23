import os
import shutil
from datetime import datetime
import markdown2
from PIL import Image
import yaml


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

    return list(filter(lambda x: x is not None, images))


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

    map(
        lambda x: os.makedirs(x, exist_ok=True),
        [OUTPUT_DIR, OUTPUT_POSTS_DIR, OUTPUT_IMAGES_DIR],
    )

    posts = []

    # Iterate over all dirs in the posts directory
    for post_code in os.listdir(POSTS_DIR):
        post_dir = os.path.join(POSTS_DIR, post_code)

        # Construct full file path
        file_path = os.path.join(post_dir, "index.md")

        # Read the Markdown file
        with open(file_path, "r", encoding="utf-8") as file:
            md_content = file.read()

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

        # Convert Markdown to HTML
        html_content = markdown2.markdown(
            md_content, extras=["fenced-code-blocks", "header-ids", "mermaid"]
        )

        # Fix image src paths and render into template
        html_content = html_content.replace('<img src="', '<img src="/posts/images/')
        html_content = template.replace("{{ content }}", html_content)

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
            file.write(html_content)

        # Append to posts list
        posts.append(
            {
                "title": title,
                "path": link_path,
                "date": datetime.strptime(date, "%m-%d-%Y"),
            }
        )

        print(f"Rendered {post_code} to {html_filename}")

    # Sort posts by date descending
    posts.sort(key=lambda x: x["date"], reverse=True)

    # Load landing.md
    with open("pages/landing.md", "r", encoding="utf-8") as file:
        md_content = file.read()

    index_html = markdown2.markdown(
        md_content, extras=["fenced-code-blocks", "header-ids"]
    )

    for post in posts:
        index_html += (
            f'<li class="landing-li"><a href="{post["path"]}">{post["title"]}</a></li>'
        )

    index_html = template.replace("{{ content }}", index_html)
    index_path = os.path.join(OUTPUT_DIR, "index.html")

    with open(index_path, "w", encoding="utf-8") as file:
        file.write(index_html)

    print("Rendered index.html")

    # Copy default.css to output directory
    shutil.copy2("static/styles.css", OUTPUT_DIR)
    shutil.copy2("static/default.css", OUTPUT_DIR)


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
