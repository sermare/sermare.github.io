import Head from 'next/head';
import Navbar from '../components/Navbar';
import CardGrid from '../components/CardGrid';
import Footer from '../components/Footer';
import { featured, siteConfig } from '../data/content';

export default function Home() {
  return (
    <>
      <Head>
        <title>{siteConfig.name} - Digital Garden</title>
      </Head>
      <main className="mx-auto w-full max-w-screen-sm px-8 font-sans md:max-w-screen-md lg:max-w-screen-lg xl:max-w-screen-2xl">
        <Navbar />
        <CardGrid cards={featured} />
        <Footer />
      </main>
    </>
  );
}

export async function getStaticProps() {
  return { props: {} };
}
