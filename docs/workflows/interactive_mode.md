# Interactive mode

**Enter with:** `int mode` or `interactive mode`.

No other wording enters Interactive mode. Plain `int` and `interactive` do not
enter it.

While Interactive mode is active:

- discuss freely;
- implement only what the user explicitly tells the agent to implement;
- validate the changes as the work is iteratively refined;
- do not commit.

Continue discussion, implementation, validation, and correction until the user
sends `qwe`. Then commit and push the accumulated result and exit Interactive
mode. Normal mode resumes.
