import '../styles/globals.css';

export default function App({ Component, pageProps }) {
  return (
    <div
      style={{
        '--font-sans': "'Inter', system-ui, sans-serif",
        '--font-serif': "'Newsreader', Georgia, serif",
      }}
    >
      <Component {...pageProps} />
    </div>
  );
}
