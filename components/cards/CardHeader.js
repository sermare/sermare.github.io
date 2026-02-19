import Link from 'next/link';

function ExternalLinkIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 14 14"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M5.25 2.625H3.0625C2.82088 2.625 2.58912 2.72098 2.41815 2.89194C2.24719 3.06291 2.15121 3.29466 2.15121 3.53628V10.9375C2.15121 11.1791 2.24719 11.4109 2.41815 11.5819C2.58912 11.7528 2.82088 11.8488 3.0625 11.8488H10.4637C10.7054 11.8488 10.9371 11.7528 11.1081 11.5819C11.279 11.4109 11.375 11.1791 11.375 10.9375V8.75"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M8.75 2.625H11.375V5.25"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M6.125 7.875L11.375 2.625"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function CardHeader({ section, name, sectionLink, externalUrl }) {
  return (
    <div className="flex items-center justify-between pl-4 pr-2 pt-2 text-sm tracking-tight text-neutral-400">
      <span>
        <Link
          href={sectionLink}
          className="relative z-20 hover:text-neutral-900 hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          {section}
        </Link>
        {name && (
          <>
            {' '}
            <span className="text-neutral-300">&middot;</span> {name}
          </>
        )}
      </span>
      {externalUrl && (
        <a
          href={externalUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="relative z-20 flex h-8 w-8 items-center justify-center rounded-full cursor-alias text-neutral-400 transition-all group-hover:bg-white group-hover:text-neutral-900 group-hover:shadow-skeuo"
          onClick={(e) => e.stopPropagation()}
          aria-label="Open external link"
        >
          <ExternalLinkIcon />
        </a>
      )}
    </div>
  );
}
