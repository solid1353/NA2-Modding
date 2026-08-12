# Interactive mode

**Enter with:** `int mode` or `interactive mode`.

No other wording enters Interactive mode. Plain `int` and `interactive` do not
enter it.

While Interactive mode is active:

- discuss freely;
- implement only what the user explicitly tells the agent to implement;
- validate the changes as the work is iteratively refined;
- do not commit unless the user sends `commit` or `ver`.

`ver` accepts and commits the accumulated result, then exits Interactive mode.
`commit` commits the current result without accepting it or exiting the mode.
`exit mode` exits without committing or accepting the result.
