import Head from 'next/head';
import Navbar from '../components/Navbar';
import CardGrid from '../components/CardGrid';
import Footer from '../components/Footer';
import { featured, siteConfig } from '../data/content';
import { getAllPosts, postsToCards } from '../lib/posts';

const validTypes = ['research', 'writing', 'reading', 'hobbies'];

export default function TypePage({ type, cards }) {
  const title = type.charAt(0).toUpperCase() + type.slice(1);

  return (
    <>
      <Head>
        <title>
          {title} - {siteConfig.name}
        </title>
      </Head>
      <main className="mx-auto w-full max-w-screen-sm px-8 font-sans md:max-w-screen-md lg:max-w-screen-lg xl:max-w-screen-2xl">
        <Navbar />
        <div className="mb-12 mt-8">
          <h1 className="font-serif text-4xl font-light text-neutral-900 md:text-5xl">
            {title}
          </h1>
          <p className="mt-2 text-neutral-400">
            {type === 'research' && 'Publications and research projects.'}
            {type === 'writing' && 'Blog posts and essays.'}
            {type === 'reading' && "Books and papers I've been reading."}
            {type === 'hobbies' && 'Things I enjoy outside of research.'}
          </p>
        </div>
        <CardGrid cards={cards} />
        <Footer />
      </main>
    </>
  );
}

export async function getStaticPaths() {
  return {
    paths: validTypes.map((type) => ({ params: { type } })),
    fallback: false,
  };
}

export async function getStaticProps({ params }) {
  let allCards = [...featured];

  if (params.type === 'writing') {
    const posts = getAllPosts();
    const postCards = postsToCards(posts);
    allCards = [...allCards, ...postCards];
  }

  const filtered = allCards
    .filter((item) => item.card.type === params.type)
    .sort((a, b) => a.ordering - b.ordering);

  return {
    props: {
      type: params.type,
      cards: filtered,
    },
  };
}
