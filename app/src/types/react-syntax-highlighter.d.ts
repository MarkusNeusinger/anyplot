// @types/react-syntax-highlighter ships an ambient declaration for this path,
// but TypeScript's bundler module resolution doesn't pick it up — it resolves
// the import to the sibling `.js` file before consulting the @types index,
// breaking `tsc` (and therefore the Cloud Build `yarn build` step) with TS7016.
// A project-local shim wins over @types, so this is enough to unblock the build.
declare module 'react-syntax-highlighter/dist/esm/languages/prism/r' {
  const language: unknown;
  export default language;
}

declare module 'react-syntax-highlighter/dist/esm/languages/prism/julia' {
  const language: unknown;
  export default language;
}
