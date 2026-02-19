import Link from 'next/link';

export default function IntroBlock() {
  return (
    <div className="row-span-2 px-1 pb-2 sm:col-span-2 lg:aspect-square">
      <div className="group flex h-full w-full flex-col justify-center overflow-hidden rounded-lg bg-neutral-50 p-8 transition-colors hover:bg-neutral-100 sm:p-10 lg:p-14">
        <h1 className="font-serif text-2xl font-light !leading-tight text-neutral-400 sm:text-3xl lg:text-4xl">
          Hey there, I&apos;m{' '}
          <span className="text-neutral-900">Sergio</span> 👋
          <br />
          Welcome to my{' '}
          <span className="text-neutral-900 decoration-dotted underline-offset-4 hover:underline">
            digital garden
          </span>{' '}
          🌱
          <br />
          <br />
          I&apos;m a{' '}
          <span className="text-neutral-900">
            Computational Biology Ph.D. candidate
          </span>{' '}
          at{' '}
          <span className="text-neutral-900">UC Berkeley</span>, working at the
          intersection of{' '}
          <Link
            href="/research"
            className="text-neutral-900 decoration-sky-400 underline-offset-4 hover:underline"
          >
            cancer genetics
          </Link>{' '}
          and{' '}
          <Link
            href="/research"
            className="text-neutral-900 decoration-purple-400 underline-offset-4 hover:underline"
          >
            deep learning
          </Link>
          . I spend my time building{' '}
          <Link
            href="/research"
            className="text-neutral-900 decoration-orange-400 underline-offset-4 hover:underline"
          >
            ML models
          </Link>{' '}
          for immunotherapy, playing{' '}
          <Link
            href="/hobbies"
            className="text-neutral-900 decoration-amber-400 underline-offset-4 hover:underline"
          >
            chess
          </Link>
          , and diving into{' '}
          <Link
            href="/reading"
            className="text-neutral-900 decoration-fuchsia-400 underline-offset-4 hover:underline"
          >
            research papers
          </Link>
          . I also do some{' '}
          <Link
            href="/writing"
            className="text-neutral-900 decoration-teal-400 underline-offset-4 hover:underline"
          >
            writing
          </Link>{' '}
          about my research journey.
        </h1>
      </div>
    </div>
  );
}
