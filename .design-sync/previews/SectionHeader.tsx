import { SectionHeader } from 'anyplot';

// The §6.3 section-header pattern: a mono prompt symbol, a serif title (an <em>
// child flips to brand-green italic), and an optional trailing link (internal
// route or external URL).
const frame = (el: React.ReactNode) => <div style={{ padding: '8px 28px', maxWidth: 860 }}>{el}</div>;

export function Plain() {
  return frame(<SectionHeader prompt="❯" title="Featured plots" />);
}

export function WithInternalLink() {
  return frame(
    <SectionHeader
      prompt="§"
      title={
        <>
          Browse the <em>full</em> catalog
        </>
      }
      linkText="all plots →"
      linkTo="/plots"
    />,
  );
}

export function WithExternalLink() {
  return frame(
    <SectionHeader
      prompt="$"
      title="Open source"
      linkText="GitHub ↗"
      linkHref="https://github.com/MarkusNeusinger/anyplot"
    />,
  );
}
