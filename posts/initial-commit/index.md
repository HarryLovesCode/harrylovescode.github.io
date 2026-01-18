---
date: 1-1-2025
---

# Initial Commit

Every year, almost like clock-work, I have found myself on the couch building a blog from the ground-up. Typically, I go the route of either using Jekyll and rolling one that way, or building an over-engineered CMS. However, lately I have been taking the approach of less is more. 

I stumbled upon a post this morning on HackerNews of a single-file Python script to statically generate a blog (link below). For a while, I have been contemplating doing this with Handlebars, but the script was elegant in its simplicity. Leveraging the `markdown2` library which includes support out-of-the-box for Pygments syntax highlighting.

I will make one note, the script he included has some redundant code, as well as not properly supporting syntax highlighting out of the box. I dug through the documentation on Markdown2, and found that they use `.codehilite` as the class prefix for all syntax highlighting. You can use the pygmentize CLI tool to generate the CSS like so:

```bash
pygmentize -S github-dark -f html -a .codehilite > default.css
```

And just like that, you have Github dark syntax highlighting for your posts.

```py
def main():
    print("Niceeee")
```

So here we go, hopefully this blog doesn't end the same way the others have.

---

Link to: [Carl Öst Wilkens' Blog](https://ostwilkens.se/blog/setting-up-blog).