# Version 2 Progress Report B

**Date:** November 17, 2026

## Work completed since Progress Report A

This update improves the accuracy of ContrastCheck's WCAG classifications.
The application now reads `fontSize` and `fontWeight` from each Figma text
layer and chooses the appropriate WCAG AA threshold. Normal text must meet
4.5:1. Text at least 24 px, or bold text at least 18.66 px with a weight of
700 or greater, uses the 3:1 large-text threshold.

Each supported report result now explains the threshold used, labels the text
as normal or large, and includes available pixel size and font weight. Missing
or invalid style information automatically uses the stricter 4.5:1 rule.

Figma can store more than one character style inside a single text layer. The
program detects character style overrides and conservatively uses 4.5:1 for
the whole layer rather than assuming every character qualifies as large text.
The README now documents these rules and limitations.

The automated suite increased from 11 to 17 tests. New tests cover normal
text, 24 px large text, bold 19 px text, missing styles, mixed character
styles, and a report result that passes at the 3:1 large-text threshold. All
17 tests pass.

## Current snag and feedback request

The conservative mixed-style rule is safe but may report a failure when every
individual span is actually large enough to qualify for 3:1. Fully evaluating
each styled character range would add complexity and make the report much
longer.

I would appreciate feedback on whether the conservative 4.5:1 rule is
appropriate for mixed-style text in the final course scope. I would also like
feedback on whether the remaining time should prioritize more real-file
testing and report clarity instead of detailed per-character analysis.

## Next steps

1. Test normal, large, bold, and mixed-style examples in additional real Figma
   files.
2. Refine report wording based on real-file output.
3. Add more unusual and incomplete Figma node cases to the automated tests.
4. Perform final cleanup and documentation before the code freeze.
