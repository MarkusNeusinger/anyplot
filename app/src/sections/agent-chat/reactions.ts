/**
 * The site feedback's four reactions as the agent chat draws them: the result
 * card's quick feedback (`ResultFeedback`) and the debug page's triage of the
 * stored cases (`src/sections/debug/`) share one icon, colour and wording per
 * reaction.
 */

import type { ComponentType } from 'react';

import BugReportIcon from '@mui/icons-material/BugReport';
import BugReportOutlinedIcon from '@mui/icons-material/BugReportOutlined';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import LightbulbOutlinedIcon from '@mui/icons-material/LightbulbOutlined';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import ThumbDownOutlinedIcon from '@mui/icons-material/ThumbDownOutlined';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbUpOutlinedIcon from '@mui/icons-material/ThumbUpOutlined';

import type { FeedbackReaction } from 'src/lib/agent';
import { colors } from 'src/theme';

export interface ReactionOption {
  value: FeedbackReaction;
  /** The accessible name, in words. */
  label: string;
  /** The tooltip, a method call like the plot page's `.like()`. */
  verb: string;
  color: string;
  Outlined: ComponentType<{ fontSize?: 'small' | 'inherit' }>;
  Filled: ComponentType<{ fontSize?: 'small' | 'inherit' }>;
}

/** The site feedback's reaction set, in the order of the plot page and the feedback widget. */
export const REACTIONS: readonly ReactionOption[] = [
  {
    value: 'thumbs_up',
    label: 'Thumbs up',
    verb: '.like()',
    color: colors.primary,
    Outlined: ThumbUpOutlinedIcon,
    Filled: ThumbUpIcon,
  },
  {
    value: 'thumbs_down',
    label: 'Thumbs down',
    verb: '.dislike()',
    color: colors.error,
    Outlined: ThumbDownOutlinedIcon,
    Filled: ThumbDownIcon,
  },
  {
    value: 'idea',
    label: 'Idea',
    verb: '.idea()',
    color: colors.accent,
    Outlined: LightbulbOutlinedIcon,
    Filled: LightbulbIcon,
  },
  {
    value: 'bug',
    label: 'Bug',
    verb: '.bug()',
    color: colors.error,
    Outlined: BugReportOutlinedIcon,
    Filled: BugReportIcon,
  },
];

/** A reaction in lowercase words, as the sent line and the triage list show it. */
export const REACTION_TEXT: Record<FeedbackReaction, string> = {
  thumbs_up: 'thumbs up',
  thumbs_down: 'thumbs down',
  idea: 'idea',
  bug: 'bug',
};

/** The option of a reaction; `undefined` for a value outside the four. */
export function reactionOption(reaction: string): ReactionOption | undefined {
  return REACTIONS.find(option => option.value === reaction);
}
