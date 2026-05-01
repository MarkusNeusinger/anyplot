# Review

Follow the `Instructions` below to **review work done against a specification file** (agentic/specs/*.md) to ensure implemented features match requirements. Use the spec file to understand the requirements and then use the git diff if available to understand the changes made. Capture screenshots of critical functionality paths as documented in the `Instructions` section. If there are issues, report them if not then report success.

## Variables

run_id: $1
spec_file: $2
agent_name: $3 if provided, otherwise use 'review_agent'
review_image_dir: `<absolute path to codebase>/agentic/runs/<run_id>/<agent_name>/review_img/`

## Instructions

- Check current git branch using `git branch` to understand context
- Run `git diff origin/main` to see all changes made in current branch. Continue even if there are no changes related to the spec file.
- Find the spec file by looking for agentic/specs/*.md files in the diff that match the current branch name
- Read the identified spec file to understand requirements
- IMPORTANT: If the work can be validated by UI validation then (if not skip the section):
  - Use the playwright mcp server commands to validate the work.
  - IMPORTANT: To be clear, we're not testing. We know the functionality works. We're reviewing the implementation against the spec to make sure it matches what was requested.
  - IMPORTANT: Take screenshots along the way to showcase the new functionality and any issues you find
    - Capture visual proof of working features through targeted screenshots
    - Navigate to the application and capture screenshots of only the critical paths based on the spec
    - Compare implemented changes with spec requirements to verify correctness
    - Do not take screenshots of the entire process, only the critical points.
    - IMPORTANT: Aim for `1-5` screenshots to showcase that the new functionality works as specified.
    - If there is a review issue, take a screenshot of the issue and add it to the `review_issues` array. Describe the issue, resolution, and severity.
    - Number your screenshots in the order they are taken like `01_<descriptive name>.png`, `02_<descriptive name>.png`, etc.
    - IMPORTANT: Be absolutely sure to take a screenshot of the critical point of the new functionality
    - IMPORTANT: Copy all screenshots to the provided `review_image_dir`
    - IMPORTANT: Store the screenshots in the `review_image_dir` and be sure to use full absolute paths.
    - Focus only on critical functionality paths - avoid unnecessary screenshots
    - Ensure screenshots clearly demonstrate that features work as specified
    - Use descriptive filenames that indicate what part of the change is being verified
- IMPORTANT: Issue Severity Guidelines
  - Think hard about the impact of the issue on the feature and the user
  - Guidelines:
    - `skippable` - the issue is non-blocker for the work to be released but is still a problem
    - `tech_debt` - the issue is non-blocker for the work to be released but will create technical debt that should be addressed in the future
    - `blocker` - the issue is a blocker for the work to be released and should be addressed immediately. It will harm the user experience or will not function as expected.
- IMPORTANT: Return ONLY the JSON object specified in the `Report` section below.
  - IMPORTANT: Do not include any preamble, explanation, or markdown formatting around the JSON.
  - We'll immediately run JSON.parse() on the output, so make sure it's valid JSON.
  - Match the schema exactly — extra keys or missing required keys will fail downstream parsing.
- Reason carefully through the review. Focus on critical functionality paths and the user experience. Do not
  report issues that are not material to the feature — inflated issue lists are noise, not signal.

## Codebase Structure

For the full project layout, conventions, and tech stack, see `agentic/docs/project-guide.md`. Read it only if you need
to map the diff back onto specific subsystems.

## Report

- IMPORTANT: Return results exclusively as a JSON array based on the `Output Structure` section below.
- `success` should be `true` if there are NO BLOCKING issues (implementation matches spec for critical functionality)
- `success` should be `false` ONLY if there are BLOCKING issues that prevent the work from being released
- `review_issues` can contain issues of any severity (skippable, tech_debt, or blocker)
- `screenshots` should contain paths to screenshots if UI validation was performed, otherwise an empty array []. Use full absolute paths.
- This allows subsequent agents to quickly identify and resolve blocking errors while documenting all issues

### Output Structure

```json
{
    success: "boolean - true if there are NO BLOCKING issues (can have skippable/tech_debt issues), false if there are BLOCKING issues",
    review_summary: "string - 2-4 sentences describing what was built and whether it matches the spec. Written as if reporting during a standup meeting. Example: 'The natural language query feature has been implemented with drag-and-drop file upload and interactive table display. The implementation matches the spec requirements for SQL injection protection and supports both CSV and JSON formats. Minor UI improvements could be made but all core functionality is working as specified.'",
    review_issues: [
        {
            "review_issue_number": "number - the issue number based on the index of this issue",
            "screenshot_path": "string - /absolute/path/to/screenshot_that_shows_review_issue.png",
            "issue_description": "string - description of the issue",
            "issue_resolution": "string - description of the resolution",
            "issue_severity": "string - severity of the issue between 'skippable', 'tech_debt', 'blocker'"
        },
        ...
    ],
    screenshots: [
        "string - /absolute/path/to/screenshot_showcasing_functionality.png",
        "string - /absolute/path/to/screenshot_showcasing_functionality.png",
        "...",
    ]
}
```
