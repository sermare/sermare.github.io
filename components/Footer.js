export default function Footer() {
  return (
    <footer className="flex flex-col items-center justify-center pt-36 pb-20">
      <div className="group flex flex-col items-center">
        <div className="relative h-16 w-16 mb-4">
          {/* Animated GIF on hover */}
          <img
            src="/images/epitope_mhc_rotating.gif"
            alt="Rotating molecule"
            className="absolute inset-0 h-full w-full object-contain opacity-0 transition-opacity duration-500 group-hover:opacity-100"
          />
          {/* Static avatar */}
          <img
            src="/images/avatar.png"
            alt="Sergio E. Mares"
            className="absolute inset-0 h-full w-full rounded-full object-cover transition-opacity duration-500 group-hover:opacity-0"
          />
        </div>
        <span className="text-sm text-neutral-400">
          Planted by Sergio
        </span>
      </div>
    </footer>
  );
}
