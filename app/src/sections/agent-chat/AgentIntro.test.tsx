/**
 * The explainer's own text: its paragraph, the line on how the chat is built, and the terms of use
 * under their heading, three labelled sentences in the wording decided for the explainer and a
 * line that links to the legal page's section on what the assistant stores. The texts are written
 * out here, not imported, so a change of their wording fails this test. The page around the
 * explainer (the lane, the head, the examples) is AgentChatPage.public.test.tsx's.
 */

import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { ThemeProvider } from '@mui/material/styles';

import { AgentIntro } from 'src/sections/agent-chat/AgentIntro';
import { theme } from 'src/theme';

function renderIntro() {
  return render(
    <ThemeProvider theme={theme}>
      <MemoryRouter initialEntries={['/agent']}>
        <AgentIntro />
      </MemoryRouter>
    </ThemeProvider>
  );
}

describe('AgentIntro paragraph', () => {
  it('says what the chat does, verbatim', () => {
    renderIntro();
    const paragraph = within(screen.getByTestId('agent-intro')).getAllByRole('paragraph')[0];
    expect(paragraph.textContent).toBe(
      "experimental, open to everyone since 2 november 2026. pick any plot, choose .use_my_data() on its page, and paste your data. an agent adapts that plot's code to your columns, renders it in a sandbox with no network access, reviews the render against the catalogue's rubric, repairs it once if needed, and hands back the image and the code. the model is Claude by Anthropic, served through Google Cloud Vertex AI in the EU. your chat and data live only in server memory and are deleted after an hour idle, unless you send feedback."
    );
  });

  it('says how the chat is built between the way on and the terms, with its design on GitHub', () => {
    renderIntro();
    const intro = screen.getByTestId('agent-intro');
    const line = within(intro).getAllByRole('paragraph')[1];
    expect(line.textContent).toBe(
      'how it works: one agent talks to you, and the loop around it is plain code. the design and the code are on GitHub.'
    );
    const browse = within(intro).getByRole('link', { name: 'Browse plots' });
    const terms = within(intro).getByTestId('agent-intro-terms');
    expect(browse.compareDocumentPosition(line) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(line.compareDocumentPosition(terms) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    // The README's section on the chat, in a new tab like the site's other links to GitHub.
    const github = within(line).getByRole('link', { name: 'on GitHub' });
    expect(github).toHaveAttribute(
      'href',
      'https://github.com/MarkusNeusinger/anyplot#use-with-my-data-agent-chat'
    );
    expect(github).toHaveAttribute('target', '_blank');
    expect(github).toHaveAttribute('rel', 'noopener noreferrer');
  });
});

describe('AgentIntro terms', () => {
  it('lists the terms as labelled lines under their heading, in order, verbatim', () => {
    renderIntro();
    const terms = screen.getByTestId('agent-intro-terms');
    expect(terms.tagName).toBe('DL');
    const heading = screen.getByRole('heading', { level: 3, name: 'ground rules' });
    expect(terms.previousElementSibling).toBe(heading);
    const labels = within(terms).getAllByRole('term');
    const texts = within(terms).getAllByRole('definition');
    expect(labels.map(label => label.textContent)).toEqual([
      'your code',
      'privacy',
      'limits',
      'status',
    ]);
    expect(texts.map(text => text.textContent)).toEqual([
      'yours to use, as is. Highcharts needs a licence from Highsoft for commercial use.',
      'what is stored, where and for how long',
      'use it only with data you may share, never for unlawful content or automated requests. daily limits apply per tab and per network; a misuse can pause you for the day.',
      'experimental, without warranty: results can be wrong and nobody checks them by hand. the operator may pause it at any time.',
    ]);
  });

  it("links the privacy line to the legal page's section on the assistant, in the same tab", () => {
    renderIntro();
    const terms = screen.getByTestId('agent-intro-terms');
    const link = within(terms).getByRole('link', {
      name: 'what is stored, where and for how long',
    });
    expect(link).toHaveAttribute('href', '/legal#assistant');
    // The explainer holds no session, so leaving it loses nothing: no new tab.
    expect(link).not.toHaveAttribute('target');
  });

  it('stands below the way on to the catalogue, as the last part of the explainer', () => {
    renderIntro();
    const intro = screen.getByTestId('agent-intro');
    const browse = within(intro).getByRole('link', { name: 'Browse plots' });
    const terms = within(intro).getByTestId('agent-intro-terms');
    expect(browse.compareDocumentPosition(terms) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(intro.lastElementChild).toBe(terms);
  });
});
