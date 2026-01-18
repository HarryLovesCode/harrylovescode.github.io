import os
import shutil
from datetime import datetime

import markdown2
import yaml


def ssg():
    # Define the directory containing the Markdown files
    posts_dir = "./posts"
    output_dir = "./blog"

    # Read template.html
    with open("template.html", "r", encoding="utf-8") as file:
        template = file.read()

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, posts_dir), exist_ok=True)

    posts = []

    # Iterate over all dirs in the posts directory
    for post_directory in os.listdir(posts_dir):
        post_code = post_directory

        # Construct full file path
        file_path = os.path.join(posts_dir, post_directory, "index.md")

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
        html_content = html_content.replace(
            '<img src="', f'<img src="/posts/{post_code}/'
        )
        html_content = template.replace("{{ content }}", html_content)

        # Construct HTML file path
        html_filename = post_code + ".html"  # Replace .md with .html
        html_path = os.path.join(output_dir, posts_dir, html_filename)
        link_path = os.path.join(posts_dir, html_filename)

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

    # Render index.html
    index_html = ""

    # Load greetings.md
    with open("landing.md", "r", encoding="utf-8") as file:
        md_content = file.read()

    index_html = markdown2.markdown(
        md_content, extras=["fenced-code-blocks", "header-ids"]
    )

    for post in posts:
        index_html += f'<li><a href="{post["path"]}">{post["title"]}</a></li>'

    index_html = template.replace("{{ content }}", index_html)
    index_path = f"{output_dir}/index.html"

    with open(index_path, "w", encoding="utf-8") as file:
        file.write(index_html)

    print("Rendered index.html")

    # Copy default.css to output directory
    shutil.copy2("default.css", output_dir)


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
