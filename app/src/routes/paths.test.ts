import { describe, expect, it } from 'vitest';

import {
  agentChatPath,
  isAgentChatAddress,
  isPlotsPath,
  langFromPath,
  namesAgentChat,
  paths,
  RESERVED_TOP_LEVEL,
  specIdFromPath,
  specPath,
} from 'src/routes/paths';

describe('namesAgentChat', () => {
  const names = (query: string) => namesAgentChat(new URLSearchParams(query));

  it('takes a well-formed spec id with a catalogue library as a chat', () => {
    expect(names('spec=scatter-basic&library=matplotlib&language=python')).toBe(true);
    // The language follows the library on the page, so the query needs none.
    expect(names('spec=line-basic&library=d3')).toBe(true);
  });

  it('takes anything else as the explainer', () => {
    expect(names('')).toBe(false);
    expect(names('spec=scatter-basic')).toBe(false);
    expect(names('library=matplotlib')).toBe(false);
    expect(names('spec=scatter-basic&library=excel')).toBe(false);
    expect(names('spec=Scatter_Basic&library=matplotlib')).toBe(false);
    expect(names(`spec=${'a'.repeat(101)}&library=matplotlib`)).toBe(false);
  });
});

describe('isAgentChatAddress', () => {
  it('is the chat at /agent with a pair, at every path the router serves as the chat page', () => {
    expect(isAgentChatAddress('/agent', '?spec=bar-basic&library=ggplot2')).toBe(true);
    expect(isAgentChatAddress('/agent/', '?spec=bar-basic&library=ggplot2')).toBe(true);
    // The router matches paths without regard to case, so this address renders the chat too.
    expect(isAgentChatAddress('/Agent', '?spec=bar-basic&library=ggplot2')).toBe(true);
    expect(isAgentChatAddress('/AGENT/', '?spec=bar-basic&library=ggplot2')).toBe(true);
  });

  it('is no chat without a pair, or on another path with the same query', () => {
    expect(isAgentChatAddress('/agent', '')).toBe(false);
    expect(isAgentChatAddress('/agent', '?spec=bar-basic')).toBe(false);
    expect(isAgentChatAddress('/debug/agent', '?spec=bar-basic&library=ggplot2')).toBe(false);
    expect(isAgentChatAddress('/plots', '?spec=bar-basic&library=ggplot2')).toBe(false);
    expect(isAgentChatAddress('/agent/x', '?spec=bar-basic&library=ggplot2')).toBe(false);
    expect(isAgentChatAddress('/agents', '?spec=bar-basic&library=ggplot2')).toBe(false);
  });
});

describe('agentChatPath', () => {
  it('builds the one chat URL for a catalogue pair, for visitors and admins', () => {
    expect(agentChatPath('scatter-basic', 'matplotlib', 'python')).toBe(
      '/agent?spec=scatter-basic&library=matplotlib&language=python'
    );
  });

  it('adds the source for agent_open and is exposed as paths.agentChat', () => {
    expect(paths.agentChat('bar-grouped', 'seaborn', 'python', 'plot_page')).toBe(
      '/agent?spec=bar-grouped&library=seaborn&language=python&source=plot_page'
    );
  });
});

describe('specPath', () => {
  it('builds the cross-language hub path', () => {
    expect(specPath('scatter-basic')).toBe('/scatter-basic');
  });

  it('builds the language overview path', () => {
    expect(specPath('scatter-basic', 'python')).toBe('/scatter-basic/python');
  });

  it('builds the implementation detail path', () => {
    expect(specPath('scatter-basic', 'python', 'matplotlib')).toBe(
      '/scatter-basic/python/matplotlib'
    );
  });

  it('ignores library without language', () => {
    expect(specPath('scatter-basic', undefined, 'matplotlib')).toBe('/scatter-basic');
  });
});

describe('langFromPath', () => {
  it('returns the language segment of a spec path', () => {
    expect(langFromPath('/scatter-basic/python')).toBe('python');
  });

  it('returns undefined for single-segment paths', () => {
    expect(langFromPath('/scatter-basic')).toBeUndefined();
  });

  it('returns undefined when the first segment is a reserved route', () => {
    expect(langFromPath('/plots/python')).toBeUndefined();
  });
});

describe('isPlotsPath', () => {
  it('is the gallery with and without a trailing slash, as the router serves it', () => {
    expect(isPlotsPath(paths.plots)).toBe(true);
    expect(isPlotsPath('/plots/')).toBe(true);
  });

  it('is no other page', () => {
    expect(isPlotsPath('/')).toBe(false);
    expect(isPlotsPath('/plots/python')).toBe(false);
    expect(isPlotsPath('/plots-of-the-day')).toBe(false);
  });
});

describe('specIdFromPath', () => {
  it('returns the first segment of a spec route', () => {
    expect(specIdFromPath('/scatter-basic')).toBe('scatter-basic');
    expect(specIdFromPath('/scatter-basic/python/altair')).toBe('scatter-basic');
  });

  it('returns undefined for the root path', () => {
    expect(specIdFromPath('/')).toBeUndefined();
    expect(specIdFromPath('')).toBeUndefined();
  });

  it('returns undefined when the first segment is a reserved route', () => {
    expect(specIdFromPath('/stats')).toBeUndefined();
    expect(specIdFromPath('/about/team')).toBeUndefined();
  });
});

describe('paths registry', () => {
  it('exposes every static route', () => {
    expect(paths.home).toBe('/');
    expect(paths.plots).toBe('/plots');
    expect(paths.specs).toBe('/specs');
    expect(paths.libraries).toBe('/libraries');
    expect(paths.map).toBe('/map');
    expect(paths.palette).toBe('/palette');
    expect(paths.about).toBe('/about');
    expect(paths.legal).toBe('/legal');
    expect(paths.mcp).toBe('/mcp');
    expect(paths.stats).toBe('/stats');
    expect(paths.debug).toBe('/debug');
  });

  it('every static route is a reserved top-level slug', () => {
    const staticRoutes = [
      paths.plots,
      paths.specs,
      paths.libraries,
      paths.map,
      paths.palette,
      paths.about,
      paths.legal,
      paths.mcp,
      paths.stats,
      paths.debug,
      paths.agent,
    ];
    for (const route of staticRoutes) {
      expect(RESERVED_TOP_LEVEL.has(route.slice(1))).toBe(true);
    }
  });

  it('builds encoded plots filter URLs', () => {
    expect(paths.plotsFiltered('lib', 'ggplot2')).toBe('/plots?lib=ggplot2');
    expect(paths.plotsFiltered('plot', 'scatter plot')).toBe('/plots?plot=scatter%20plot');
  });

  it('exposes specPath as paths.spec', () => {
    expect(paths.spec('heatmap-basic', 'r', 'ggplot2')).toBe('/heatmap-basic/r/ggplot2');
  });
});
