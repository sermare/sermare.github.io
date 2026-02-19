import CardHeader from './CardHeader';
import TagBadge from './TagBadge';

export default function ReadingCard({ card, index }) {
  const { properties } = card;

  return (
    <div className="aspect-square px-1 pb-2">
      <div
        className="group isolate flex h-full w-full flex-col overflow-hidden rounded-lg bg-neutral-50 transition-colors focus-within:bg-neutral-100 hover:bg-neutral-100 animate-fade-in-up"
        style={{ animationDelay: `${index * 80}ms` }}
      >
        <CardHeader
          section="Reading"
          name={properties.type}
          sectionLink="/reading"
          externalUrl={properties.link?.url}
        />
        <div className="grid grow grid-cols-2 items-end gap-6 px-7 pb-10">
          <div className="flex items-center justify-center">
            <div className="flex h-40 w-28 items-center justify-center rounded bg-gradient-to-br from-neutral-200 to-neutral-300 shadow-lg transition-transform group-hover:-rotate-3 group-hover:scale-110 group-hover:shadow-xl">
              <span className="px-2 text-center font-serif text-sm font-light text-neutral-600">
                {properties.title}
              </span>
            </div>
          </div>
          <div>
            {properties.tags?.map((tag, i) => (
              <TagBadge key={i} color={tag.color} label={tag.label} />
            ))}
            <h3 className="mt-3 font-serif text-lg font-light text-neutral-900">
              {properties.title}
            </h3>
            <span className="text-sm text-neutral-400">
              {properties.author}
            </span>
          </div>
        </div>
        {properties.link?.url && (
          <a
            href={properties.link.url}
            target="_blank"
            rel="noopener noreferrer"
            className="absolute inset-0 z-10"
            aria-label={`View ${properties.title}`}
          />
        )}
      </div>
    </div>
  );
}
