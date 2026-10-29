export function removeShellDefaults(head: HTMLHeadElement = document.head): number {
  const elements = head.querySelectorAll('[data-shell-default]');
  let count = 0;
  elements.forEach(el => {
    el.remove();
    count++;
  });
  return count;
}
