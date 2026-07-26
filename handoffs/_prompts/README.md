# Dispatch prompts

The exact text handed to an agent, kept so it is recoverable later.

Builder prompts were being reconstructed from chat scrollback each time, which meant the
wording that was actually dispatched — the constraints a builder was or was not given —
could not be checked afterwards. When a build goes wrong, the prompt is evidence.

```
<module>-builder.txt    what the builder was told
<module>-auditor.txt    what the auditor was told (add when dispatched)
```

**Plain text, not markdown.** These get copied into a terminal; formatting only gets in
the way.

**Update the file when you re-dispatch.** A prompt that no longer matches what was sent is
worse than none — see `SPEC_PROTOCOL.md §2.1` on claims that reach a builder unverified.
