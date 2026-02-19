import CardHeader from './CardHeader';
import TagBadge from './TagBadge';

export default function HobbyCard({ card, index }) {
  const { properties } = card;
  const inner = properties.properties || {};

  return (
    <div className="aspect-square px-1 pb-2">
      <div
        className="group flex h-full w-full flex-col justify-between overflow-hidden rounded-lg bg-neutral-50 transition-colors focus-within:bg-neutral-100 hover:bg-neutral-100 animate-fade-in-up"
        style={{ animationDelay: `${index * 80}ms` }}
      >
        <CardHeader
          section="Hobbies"
          name={properties.label}
          sectionLink="/hobbies"
          externalUrl={properties.link?.url}
        />
        <div className="p-5">
          {inner.tags && (
            <div className="mb-3 flex flex-wrap gap-2">
              {inner.tags.map((tag, i) => (
                <TagBadge key={i} color={tag.color} label={tag.label} />
              ))}
            </div>
          )}
          <h3 className="font-serif text-4xl font-light text-neutral-900 md:text-5xl lg:text-6xl">
            {inner.heading}
          </h3>
          {inner.subheading && (
            <p className="mt-1 text-neutral-400">{inner.subheading}</p>
          )}
          {inner.body && (
            <p className="mt-2 text-neutral-700">{inner.body}</p>
          )}
        </div>
        {properties.link?.url && (
          <a
            href={properties.link.url}
            target="_blank"
            rel="noopener noreferrer"
            className="absolute inset-0 z-10"
            aria-label={`View ${properties.label}`}
          />
        )}
      </div>
    </div>
  );
}
