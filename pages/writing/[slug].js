import Head from 'next/head';
import Link from 'next/link';
import { marked } from 'marked';
import Navbar from '../../components/Navbar';
import Footer from '../../components/Footer';
import { siteConfig } from '../../data/content';
import { getAllPosts, getPostBySlug } from '../../lib/posts';

export default function PostPage({ post }) {
  return (
    <>
      <Head>
        <title>
          {post.title} - {siteConfig.name}
        </title>
      </Head>
      <main className="mx-auto w-full max-w-screen-sm px-8 font-sans md:max-w-screen-md">
        <Navbar />
        <article className="pb-16 pt-8">
          <Link
            href="/writing"
            className="mb-8 inline-block text-sm text-neutral-400 hover:text-neutral-900"
          >
            &larr; Back to Writing
          </Link>
          <h1 className="font-serif text-3xl font-light text-neutral-900 md:text-5xl">
            {post.title}
          </h1>
          <span className="mt-3 mb-8 block text-sm text-neutral-400">
            {post.date &&
              new Date(post.date).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
          </span>
          {post.image && (
            <img
              src={post.image}
              alt={post.title}
              className="mb-8 w-full rounded-lg"
            />
          )}
          <div
            className="prose prose-neutral max-w-none prose-headings:font-serif prose-headings:font-light prose-a:text-neutral-900 prose-a:underline-offset-4"
            dangerouslySetInnerHTML={{ __html: marked(post.content) }}
          />
        </article>
        <Footer />
      </main>
    </>
  );
}

export async function getStaticPaths() {
  const posts = getAllPosts();
  return {
    paths: posts.map((post) => ({
      params: { slug: post.slug },
    })),
    fallback: false,
  };
}

export async function getStaticProps({ params }) {
  const post = getPostBySlug(params.slug);
  return { props: { post } };
}
