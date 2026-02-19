---
title: "Your Post Title Here"
date: "2026-01-15"
image: "/images/posts/your-image.png"
preview: "A short preview of your post that appears on the card (1-2 sentences)."
---

Write your full post content here using Markdown.

## Section Heading

Regular paragraph text goes here. You can use **bold**, *italic*, and `code`.

### Subsection

- Bullet points work
- Like this

1. Numbered lists too
2. Like this

> Blockquotes for emphasis

```python
# Code blocks with syntax highlighting
def hello():
    print("Hello from my digital garden!")
```

### Adding Images

Place images in `public/images/posts/` and reference them:

![Description](/images/posts/your-image.png)

### How to Publish

1. Create a new `.md` file in the `posts/` folder (e.g., `my-new-post.md`)
2. Add the frontmatter block at the top (title, date, image, preview)
3. Write your content below the `---`
4. Run `npm run build` or push to GitHub — it deploys automatically!

The filename becomes the URL slug: `my-new-post.md` → `/writing/my-new-post`
