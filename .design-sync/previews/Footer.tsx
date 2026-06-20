import { Footer } from 'anyplot';

// The site footer — a single mono row of links with an animated underline on
// hover. One cell: the footer has a single appearance (the selectedSpec /
// selectedLibrary props only retarget a hidden "report an issue" href, so a
// second variant would render identically).
export function Default() {
  return <Footer />;
}
