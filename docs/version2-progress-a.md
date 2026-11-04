# Version 2 Progress Report A

**Date:** November 2, 2026

## Work completed

This update moves ContrastCheck beyond its Version 1 white-background
assumption. The recursive scan now carries background context through the
Figma layer tree and matches text with the nearest supported solid ancestor
fill. Reports now include the Figma node ID, foreground color, detected
background color, background source, and separate pass, fail, and
manual-review totals.

To avoid presenting uncertain results as exact scores, text is marked
`MANUAL REVIEW` when it uses or appears over transparency, gradients, images,
multiple fills, missing fills, or no supported solid ancestor background.

The command line now accepts either a Figma design URL or a file key and lets
the user choose the report filename. Error messages cover missing tokens,
invalid URLs, timeouts, permission problems, missing files, unreadable API
responses, and report-writing problems.

Eleven automated tests now verify the WCAG contrast calculation, nearest
ancestor matching, uncertain backgrounds, duplicate removal, saved reports,
Figma URL parsing, API timeouts, and permission failures. Setup, usage, test,
privacy, and limitation instructions are included in the README.

## Current snag and feedback request

The nearest solid ancestor is a dependable improvement, but Figma's layer
tree does not by itself prove which sibling shape is visually behind a text
layer. Images, gradients, transparency, and overlapping siblings therefore
remain manual-review cases.

I would appreciate feedback on whether this clearly limited approach is
appropriate for the final course scope. My next priority would be expanding
test cases and improving report usability rather than attempting full visual
layer compositing.

## Next steps

1. Test the program against additional real Figma files and unusual node data.
2. Refine manual-review reasons and report formatting from those results.
3. Consider font size and weight so large text can use the appropriate WCAG
   threshold if this can be implemented reliably.
4. Keep color-vision simulation and a graphical interface as optional work
   only after the core checker is dependable.
