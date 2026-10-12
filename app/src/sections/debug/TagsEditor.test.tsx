import { describe, expect, it, vi } from 'vitest';

import { TagChips, TagsEditor } from 'src/sections/debug/TagsEditor';
import { fireEvent, render, screen, userEvent } from 'src/test-utils';

function setup(tags: string[] = ['legend']) {
  const onChange = vi.fn();
  render(<TagsEditor tags={tags} disabled={false} onChange={onChange} />);
  return { onChange, input: screen.getByLabelText('Add a tag') };
}

describe('TagsEditor', () => {
  it('adds a tag on Enter, lowercased, with the whole list', async () => {
    const user = userEvent.setup();
    const { onChange, input } = setup();
    await user.type(input, 'Log-Scale{Enter}');
    expect(onChange).toHaveBeenCalledWith(['legend', 'log-scale']);
    expect(input).toHaveValue('');
  });

  it('adds a tag on a comma', () => {
    const { onChange, input } = setup([]);
    fireEvent.change(input, { target: { value: 'overlap,' } });
    expect(onChange).toHaveBeenCalledWith(['overlap']);
  });

  it('refuses a tag that is not a slug', async () => {
    const user = userEvent.setup();
    const { onChange, input } = setup();
    await user.type(input, 'two words{Enter}');
    expect(onChange).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toHaveTextContent(
      'tags are lowercase slugs, at most 40 characters'
    );
  });

  it('refuses the eleventh tag', async () => {
    const user = userEvent.setup();
    const tags = Array.from({ length: 10 }, (_, index) => `t${index}`);
    const { onChange, input } = setup(tags);
    await user.type(input, 'one-more{Enter}');
    expect(onChange).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toHaveTextContent('at most 10 tags');
  });

  it('refuses a duplicate', async () => {
    const user = userEvent.setup();
    const { onChange, input } = setup();
    await user.type(input, 'legend{Enter}');
    expect(onChange).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toHaveTextContent('already there');
  });

  it('removes a tag and sends the rest', async () => {
    const user = userEvent.setup();
    const { onChange } = setup(['legend', 'overlap']);
    await user.click(screen.getByRole('button', { name: 'remove tag legend' }));
    expect(onChange).toHaveBeenCalledWith(['overlap']);
  });

  it('locks while a change is in flight', () => {
    render(<TagsEditor tags={['legend']} disabled onChange={vi.fn()} />);
    expect(screen.getByLabelText('Add a tag')).toBeDisabled();
    expect(screen.getByRole('button', { name: 'remove tag legend' })).toBeDisabled();
  });
});

describe('TagChips', () => {
  it('lists the tags and renders nothing without any', () => {
    const { container, rerender } = render(<TagChips tags={['legend', 'overlap']} />);
    expect(screen.getAllByRole('listitem').map(item => item.textContent)).toEqual([
      'legend',
      'overlap',
    ]);
    rerender(<TagChips tags={[]} />);
    expect(container.querySelector('ul')).toBeNull();
  });
});
