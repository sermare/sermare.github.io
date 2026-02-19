import IntroBlock from './cards/IntroBlock';
import ResearchCard from './cards/ResearchCard';
import WritingCard from './cards/WritingCard';
import ReadingCard from './cards/ReadingCard';
import HobbyCard from './cards/HobbyCard';

function renderCard(item, index) {
  const { card } = item;

  switch (card.type) {
    case 'intro':
      return <IntroBlock key={card.id} />;
    case 'research':
      return <ResearchCard key={card.id} card={card} index={index} />;
    case 'writing':
      return <WritingCard key={card.id} card={card} index={index} />;
    case 'reading':
      return <ReadingCard key={card.id} card={card} index={index} />;
    case 'hobbies':
      return <HobbyCard key={card.id} card={card} index={index} />;
    default:
      return null;
  }
}

export default function CardGrid({ cards }) {
  return (
    <div className="grid grid-cols-1 sm:grid-flow-row-dense sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {cards.map((item, index) => renderCard(item, index))}
    </div>
  );
}
