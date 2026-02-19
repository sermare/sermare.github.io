import Link from 'next/link';
import CardHeader from './CardHeader';
import TagBadge from './TagBadge';

export default function ResearchCard({ card, index }) {
  const { properties } = card;
  const isLarge = card.large;
  const hasImage = !!properties.imageUrl;

  return (
    <div
      className={`${
        isLarge ? 'aspect-[2] sm:col-span-2' : 'aspect-square'
      } px-1 pb-2`}
    >
      <div
        className="group relative isolate flex h-full w-full flex-col justify-between overflow-hidden rounded-lg bg-neutral-50 transition-colors focus-within:bg-neutral-100 hover:bg-neutral-100 animate-fade-in-up"
        style={{ animationDelay: `${index * 80}ms` }}
      >
        {hasImage && (
          <img
            src={properties.imageUrl}
            alt={properties.shortName}
            className="pointer-events-none absolute -z-10 h-full w-full object-cover opacity-20 transition-transform group-hover:scale-105"
          />
        )}
        <CardHeader
          section="Research"
          name={properties.shortName || properties.name}
          sectionLink="/research"
          externalUrl={properties.link?.url}
        />
        <div className="flex grow flex-col justify-end gap-3 p-5">
          {properties.tags && (
            <div className="flex flex-wrap gap-2">
              {properties.tags.map((tag, i) => (
                <TagBadge key={i} color={tag.color} label={tag.label} />
              ))}
            </div>
          )}
          <h3 className="font-serif text-xl font-light text-neutral-900 sm:text-2xl lg:text-3xl">
            {properties.shortName}
          </h3>
          <p className="text-sm text-neutral-400">{properties.venue}</p>
          {isLarge && (
            <p className="line-clamp-2 text-sm leading-relaxed text-neutral-700">
              {properties.description}
            </p>
          )}
        </div>
        <a
          href={properties.link?.url}
          target="_blank"
          rel="noopener noreferrer"
          className="absolute inset-0 z-10"
          aria-label={`View ${properties.shortName}`}
        />
      </div>
    </div>
  );
}
