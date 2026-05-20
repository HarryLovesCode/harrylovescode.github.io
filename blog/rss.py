from datetime import UTC, datetime
from pathlib import Path
import xml.etree.ElementTree as ET

from jinja2 import Environment

atom_ns = "http://www.w3.org/2005/Atom"
BASE_DIR = Path(__file__).parent.resolve()
TEMPLATE_PATH = BASE_DIR / "templates" / "rss.xml"
SITE_URL = "https://harrylovescode.github.io"
FEED_NAME = "Harry Loves Code"
AUTHOR_NAME = "Harry G"
FEED_PATH = "/rss.xml"
FEED_ALIAS_PATH = "/feed"

FEED_REDIRECT_HTML = """<!doctype html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\" />
    <meta http-equiv=\"refresh\" content=\"0; url={feed_path}\" />
    <meta name=\"robots\" content=\"noindex\" />
    <link rel=\"canonical\" href=\"{feed_path}\" />
    <title>{feed_name} Feed</title>
    <script>
        location.replace({feed_path_json});
    </script>
</head>
<body>
    <p>Redirecting to the feed at <a href=\"{feed_path}\">{feed_path}</a>.</p>
</body>
</html>
"""

def _atom_timestamp(value: datetime) -> str:
    return value.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")


def _post_url(link_path: Path) -> str:
    relative_path = link_path.as_posix().replace(".html", "")
    return f"{SITE_URL}/{relative_path}"


def build_feed_data(posts) -> dict:
    ordered_posts = sorted(posts, key=lambda post: post.date, reverse=True)
    last_updated = datetime.now(UTC)
    if ordered_posts:
        last_updated = ordered_posts[0].date.replace(tzinfo=UTC)

    return {
        "feed_name": FEED_NAME,
        "homepage_url": SITE_URL,
        "feed_url": f"{SITE_URL}{FEED_PATH}",
        "last_updated": last_updated.isoformat().replace("+00:00", "Z"),
        "author_name": AUTHOR_NAME,
        "posts": [
            {
                "title": post.title,
                "html_url": _post_url(post.link_path),
                "permalink": _post_url(post.link_path),
                "first_post_time": _atom_timestamp(post.date),
                "last_update_time": _atom_timestamp(post.date),
                "html": post.content_html,
            }
            for post in ordered_posts
        ],
    }


def generate_feed(posts) -> str:
    ET.register_namespace("", atom_ns)
    template_text = TEMPLATE_PATH.read_text(encoding="utf-8")
    template = Environment(autoescape=True).from_string(template_text)
    generated = template.render(**build_feed_data(posts))
    ET.fromstring(generated)
    return generated


def write_feed(posts, output_dir: Path) -> Path:
    output_path = output_dir / FEED_PATH.lstrip("/")
    output_path.write_text(generate_feed(posts), encoding="utf-8")
    alias_dir = output_dir / FEED_ALIAS_PATH.lstrip("/")
    alias_dir.mkdir(parents=True, exist_ok=True)
    (alias_dir / "index.html").write_text(
        FEED_REDIRECT_HTML.format(
            feed_name=FEED_NAME,
            feed_path=FEED_PATH,
            feed_path_json=repr(FEED_PATH),
        ),
        encoding="utf-8",
    )
    return output_path


if __name__ == "__main__":
    print("Feed generation is wired through main.py")
