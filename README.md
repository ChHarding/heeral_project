# ContrastCheck

ContrastCheck is a Python command-line accessibility tool that checks text
contrast in a Figma file. It reads the file through the Figma REST API, finds
text layers, matches supported text with the nearest solid ancestor
background, and creates a WCAG AA contrast report.

## Version 2 progress

The current application can:

- accept a Figma file key or a full Figma design URL;
- scan text inside nested pages, frames, components, and instances;
- match text with its nearest opaque, solid ancestor background;
- calculate WCAG contrast ratios and apply the correct AA threshold: 4.5:1
  for normal text or 3:1 for qualifying large text;
- mark gradients, images, transparency, missing fills, and missing backgrounds
  as `MANUAL REVIEW` instead of producing an unreliable score;
- remove duplicate results;
- save pass, fail, and manual-review totals to a text report; and
- show readable errors for missing credentials, invalid URLs, API failures,
  timeouts, missing files, and report-writing failures.

## Requirements

- Python 3.10 or newer
- A Figma personal access token
- View access to the Figma file being checked

Install the Python dependency:

```bash
python3 -m pip install -r requirements.txt
```

## Keep the Figma token private

Create a Figma personal access token and make it available in the terminal.
Do not paste the token into `main.py` and do not commit it to GitHub.

On macOS or Linux:

```bash
export FIGMA_TOKEN="paste-your-token-here"
```

## Run the application

Pass either a full Figma URL:

```bash
python3 main.py "https://www.figma.com/design/FILE_KEY/FILE_NAME"
```

or only the file key:

```bash
python3 main.py FILE_KEY
```

Choose a different report filename with:

```bash
python3 main.py FILE_KEY --output my-contrast-report.txt
```

If no file is supplied, the program uses `FIGMA_FILE_KEY` when that environment
variable exists, followed by the project's original demonstration file key.

## Read the report

Each supported text/background pair is marked `PASS` or `FAIL`. The report
includes its ratio, text sample, Figma node ID, foreground color, background
color, background container, text-size category, and required threshold. Text
at least 24 px is treated as large text. Bold text with a weight of at least
700 is treated as large beginning at 18.66 px. Missing or invalid style data
uses the stricter normal-text threshold. Results that cannot be calculated
honestly are marked `MANUAL REVIEW` with a reason.

`report.txt` is generated locally and ignored by Git because different users
and Figma files produce different results.

## Run the tests

```bash
python3 -m unittest discover -s tests -v
```

The tests use small local Figma-style examples and do not require a real token
or network connection.

## Current limitations

- ContrastCheck supports the nearest single, opaque, solid ancestor fill.
- It does not determine whether a sibling shape overlaps the text.
- Images, gradients, multiple fills, and transparency require manual review.
- The tool reads Figma's reported font size and weight but does not independently
  verify whether a font's visual appearance matches its numeric weight.
- Color-vision simulation and a graphical interface remain optional future
  features and are not part of the working application yet.

These limitations are reported clearly so the application does not present an
uncertain result as an exact accessibility score.
