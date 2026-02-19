import { useState, useRef, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { navTabs, siteConfig } from '../data/content';

export default function Navbar() {
  const router = useRouter();
  const [indicator, setIndicator] = useState({ width: 0, x: 0, opacity: 0 });
  const tabRefs = useRef({});

  const handleMouseEnter = useCallback((path) => {
    const el = tabRefs.current[path];
    if (el) {
      setIndicator({
        width: el.offsetWidth,
        x: el.offsetLeft,
        opacity: 1,
      });
    }
  }, []);

  const handleMouseLeave = useCallback(() => {
    // Snap to active tab or hide
    const activePath = router.asPath === '/' ? '/' : `/${router.asPath.split('/')[1]}`;
    const activeEl = tabRefs.current[activePath];
    if (activeEl) {
      setIndicator({
        width: activeEl.offsetWidth,
        x: activeEl.offsetLeft,
        opacity: 1,
      });
    } else {
      setIndicator((prev) => ({ ...prev, opacity: 0 }));
    }
  }, [router.asPath]);

  const isActive = (path) => {
    if (path === '/') return router.asPath === '/';
    return router.asPath.startsWith(path);
  };

  return (
    <nav className="pointer-events-none sticky top-0 isolate z-10 flex items-center justify-center py-4 px-1 md:justify-between">
      {/* Tab pill */}
      <div
        className="pointer-events-auto relative flex rounded-lg border border-neutral-200 bg-white/70 p-1 shadow-md backdrop-blur-md"
        onMouseLeave={handleMouseLeave}
      >
        {/* Animated indicator */}
        <div
          className="absolute left-0 -z-10 h-7 rounded bg-neutral-200 backdrop-blur transition-[width,transform,opacity] duration-200"
          style={{
            width: indicator.width,
            transform: `translateX(${indicator.x}px)`,
            opacity: indicator.opacity,
            top: '4px',
          }}
        />
        {navTabs.map((tab) => (
          <Link
            key={tab.path}
            href={tab.path}
            ref={(el) => { tabRefs.current[tab.path] = el; }}
            onMouseEnter={() => handleMouseEnter(tab.path)}
            className={`rounded py-1 px-2 text-sm tracking-tight transition-colors focus-visible:ring-4 focus-visible:ring-blue-200 ${
              isActive(tab.path)
                ? 'text-neutral-900'
                : 'text-neutral-400 hover:text-neutral-900'
            }`}
          >
            {tab.label}
          </Link>
        ))}
      </div>

      {/* External links */}
      <div className="pointer-events-auto hidden items-center gap-4 rounded-lg border border-neutral-200 bg-white/70 p-1 px-3 shadow-md backdrop-blur-md md:flex">
        <a
          href={siteConfig.social.github}
          target="_blank"
          rel="noopener noreferrer"
          className="cursor-alias text-sm text-neutral-400 decoration-wavy underline-offset-4 transition-colors hover:text-neutral-900 hover:underline"
        >
          GitHub
        </a>
        <a
          href={siteConfig.social.scholar}
          target="_blank"
          rel="noopener noreferrer"
          className="cursor-alias text-sm text-neutral-400 decoration-wavy underline-offset-4 transition-colors hover:text-neutral-900 hover:underline"
        >
          Scholar
        </a>
        <a
          href={siteConfig.social.linkedin}
          target="_blank"
          rel="noopener noreferrer"
          className="cursor-alias text-sm text-neutral-400 decoration-wavy underline-offset-4 transition-colors hover:text-neutral-900 hover:underline"
        >
          LinkedIn
        </a>
        <a
          href={siteConfig.social.twitter}
          target="_blank"
          rel="noopener noreferrer"
          className="cursor-alias text-sm text-neutral-400 decoration-wavy underline-offset-4 transition-colors hover:text-neutral-900 hover:underline"
        >
          X
        </a>
      </div>
    </nav>
  );
}
