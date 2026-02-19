import CardHeader from './CardHeader';

export default function WritingCard({ card, index }) {
  const { properties } = card;

  return (
    <div className="aspect-square px-1 pb-2">
      <a
        href={properties.url}
        target={properties.url.startsWith('http') ? '_blank' : undefined}
        rel={properties.url.startsWith('http') ? 'noopener noreferrer' : undefined}
        className="group flex h-full w-full cursor-alias flex-col justify-between overflow-hidden rounded-lg bg-neutral-50 transition-colors focus-within:bg-neutral-100 hover:bg-neutral-100 animate-fade-in-up"
        style={{ animationDelay: `${index * 80}ms` }}
      >
        <CardHeader
          section="Writing"
          name={properties.type}
          sectionLink="/writing"
          externalUrl={properties.url.startsWith('http') ? properties.url : null}
        />
        <div className="p-5">
          <h3 className="font-serif text-2xl font-light text-neutral-900 sm:text-3xl">
            {properties.title}
          </h3>
          <span className="mt-2 mb-4 block text-sm text-neutral-400">
            {properties.publishedOn}
          </span>
          <p className="line-clamp-3 leading-relaxed text-neutral-700 md:line-clamp-4">
            {properties.contentPreview}
          </p>
        </div>
      </a>
    </div>
  );
}
