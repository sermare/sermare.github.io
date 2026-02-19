import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';

const postsDirectory = path.join(process.cwd(), 'posts');

export function getAllPosts() {
  if (!fs.existsSync(postsDirectory)) return [];

  const fileNames = fs
    .readdirSync(postsDirectory)
    .filter((name) => name.endsWith('.md') && !name.startsWith('_'));

  const posts = fileNames.map((fileName) => {
    const slug = fileName.replace(/\.md$/, '');
    const fullPath = path.join(postsDirectory, fileName);
    const fileContents = fs.readFileSync(fullPath, 'utf8');
    const { data, content } = matter(fileContents);

    return {
      slug,
      title: data.title || slug,
      date: data.date || '',
      image: data.image || null,
      preview: data.preview || content.slice(0, 200) + '...',
      content,
    };
  });

  return posts.sort((a, b) => (a.date > b.date ? -1 : 1));
}

export function getPostBySlug(slug) {
  const fullPath = path.join(postsDirectory, `${slug}.md`);
  if (!fs.existsSync(fullPath)) return null;

  const fileContents = fs.readFileSync(fullPath, 'utf8');
  const { data, content } = matter(fileContents);

  return {
    slug,
    title: data.title || slug,
    date: data.date || '',
    image: data.image || null,
    preview: data.preview || content.slice(0, 200) + '...',
    content,
  };
}

export function postsToCards(posts) {
  return posts.map((post, i) => ({
    ordering: 5 + i * 0.1,
    card: {
      id: `post-${post.slug}`,
      type: 'writing',
      large: false,
      published_at: post.date,
      properties: {
        type: 'Blog',
        title: post.title,
        url: `/writing/${post.slug}`,
        publishedOn: post.date
          ? new Date(post.date).toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })
          : '',
        contentPreview: post.preview,
        image: post.image,
      },
    },
  }));
}
