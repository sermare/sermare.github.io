const colorMap = {
  lime: 'bg-lime-400/40 text-lime-900',
  orange: 'bg-orange-400/40 text-orange-900',
  sky: 'bg-sky-400/40 text-sky-900',
  purple: 'bg-purple-400/40 text-purple-900',
  amber: 'bg-amber-400/40 text-amber-900',
  green: 'bg-green-400/40 text-green-900',
  rose: 'bg-rose-400/40 text-rose-900',
  teal: 'bg-teal-400/40 text-teal-900',
  fuchsia: 'bg-fuchsia-400/40 text-fuchsia-900',
};

export default function TagBadge({ color, label }) {
  const colorClasses = colorMap[color] || colorMap.sky;

  return (
    <span
      className={`inline-block rounded px-1.5 pt-0.5 pb-1 font-mono text-sm tracking-tight shadow-inset-skeuo ${colorClasses}`}
    >
      {label}
    </span>
  );
}
