# An AI model turned 50 local-government PDFs into web pages. Checking them was the hard part.

*Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Test run on 27 October 2026; follow-up test on 28 October 2026.*

In April the US Department of Justice gave state and local governments another year to make their websites meet WCAG 2.1 AA under ADA Title II: until 26 April 2027 for governments serving 50,000 people or more, and 26 April 2028 for smaller ones and special districts. One reason it gave: "Advanced technology, such as generative AI, does not yet reliably automate the remediation of inaccessible content at scale" ([91 FR 20902](https://www.federalregister.gov/documents/2026/04/20/2026-07663/extension-of-compliance-dates-for-nondiscrimination-on-the-basis-of-disability-accessibility-of-web), page 20907).

The rule points to concerns raised with the Department, not to a measurement. We tried one small part of it: the short PDFs that local governments link from their homepages.

## What we did

We visited the homepages of 341 US local governments (cities, counties, special and school districts), picked at random from CISA's registry of .gov domains, and took the first PDF each one linked. 87 homepages had a PDF we could fetch. We set aside 16 that were scanned images and 21 that ran past 10 pages. That left 50 documents from 50 governments: 153 pages of agendas, ordinances, letters, forms, reports, a check register, a map and more. 33 came from cities, 10 from counties and 7 from special districts.

We asked one current commercial AI model to turn each PDF into a web page that could replace it. It got one try per document, with no human in the loop, no web access and no way to run code: read the PDF, write one HTML file. It took about two minutes per document. The full instruction is below. For comparison, we ran the same PDFs through Docling 2.143.0, an open-source converter that uses no generative AI.

Then we checked each page two ways:

- **Accessibility:** axe-core 4.14.0 in Chromium, WCAG 2.1 A and AA rules. A page passes with no serious or critical violations.
- **Faithfulness:** every number and word in the PDF must be in the page, unchanged, with nothing invented. An automatic checker compares the page with the PDF's own text layer. A first reader judged its word-level flags without knowing which converter made the page. A second reader then went over every flag on the model's pages against the rendered PDF. Both readers were AI agents of our own; more on that below.

We wrote down the method and the pass bar before we ran anything.

## What we found

| | AI model | Docling |
|---|---:|---:|
| Pages with no serious or critical axe violations | 50 of 50 | 47 of 50 |
| Pages the automatic faithfulness check passed | 22 of 50 | 19 of 50 |
| Pages confirmed faithful and accessible after the flags were read | at least 38 of 50 | 20 of 50 |
| Pages where a reader found a number or word changed, dropped or invented | 0 of 50 | not checked |
| Structure correct on 15 sampled documents (headings, tables, reading order, image text) | 15 of 15 | 1 of 15 |

The automatic checker failed 28 of the model's 50 pages. Reading its flags, two readers found no number or word that the model had changed, dropped or invented. 38 pages were checked completely; the other 12 were read in part. On a strict reading, 2 pages broke the instruction to add nothing: one added a written description of a map and one a note on how an org chart is laid out. Both were accurate.

Docling's 20 counts every number flag as an error, as our rule did before anyone read them, and nobody gave its flags a second reading, so its true figure may be higher too. The structure sample had one grader, who could tell the two converters apart.

## Why the checker was wrong

A PDF's text layer is what a computer reads, and it often differs from what the page shows. Every flag we traced on the model's pages came from one of these:

- **Running headers, footers and page numbers.** The PDF repeats a header on every page; the model kept it once or left it out, as it was allowed to. (6 documents)
- **Numbered lists.** The PDF draws its list numbers or letters in a way the text layer does not capture as the reader sees them, and the model made a real list; the checker counted the difference as numbers added. (4 documents)
- **Text that exists only as an image, or a garbled text layer.** A letterhead address, a map's district numbers, and a reference number whose text layer was scrambled; the model wrote what the page shows. (3 documents)
- **A bug in our own checker.** It discounted bare page numbers such as "2" by counting every "2" anywhere on the page, so real numbers looked dropped. (3 documents)
- **Word-level noise.** Letter-spaced fonts ("h ealth"), hyphens the text layer drops from phone numbers, headings drawn as pictures, a table read column by column, and table cells whose text runs together. (All 14 word flags the first reader judged, across both converters.)

Before the run we tested the checker on deliberately damaged copies of 112 PDFs, and it caught nearly every planted error. On the real pages it failed 28 in which nobody found a model error. It could not tell a model error from a text layer that was wrong to begin with.

So for these documents, writing the page was no longer the slow step. Checking it was.

## Update, 28 October 2026: can the checking be automated?

Since checking was the slow step, we tried to automate it. We built a rule-based checker, with no AI model in it, that reads each PDF's text layer three ways, also runs OCR (Tesseract 5.5.0) on every page, and compares that text with the web page. We tuned it on 15 of the 50 documents, froze it, and ran it once on the other 35. Before that run we wrote down the bar. To pass, it had to catch at least 95% of planted errors and flag no more than 3 of the 35 test pages in which our readers had found no changed, dropped or invented text. Catching fewer than 80%, or flagging more than 7 of those pages, would count as a failure.

We planted 156 errors in copies of the model's pages. It caught 143 (92%): 51 of 52 changed numbers, all 26 invented sentences, 23 of 26 dropped sentences, 23 of 26 duplicated list items and 20 of 26 removed list items. All 13 it missed were short or repeated text, such as street names on a map or an agenda's "Call To Order".

It raised far fewer false number alarms than our first checker. Across all 50 documents, including the 15 it was tuned on, pages with a false number alarm fell from 16 to 4; 3 of the 4 were among the 35 test pages. But it flagged 8 of the 35 test pages, so by our own bar it failed. Two of the 8 were the pages where the model added a map description and an org-chart note, mentioned above. On a strict reading those flags were right, but we had decided in advance to count them as false alarms. The other alarms came from text inside org charts, maps and infographics, running footers, table headers repeated on every page, and lettered list markers.

So a checker like this one is not yet a substitute for a person. Documents whose meaning lives in a figure, and short items that appear more than once, still need someone to compare the page with the PDF.

The limits: the planted errors were synthetic, all made by one program of ours, and real model errors may be easier or harder to catch. These were the same 50 documents and one OCR engine. "No changed, dropped or invented text" rests on the same two readers described above, and the same AI agent of ours wrote both the test plan and the checker. The checker does not check alt text or other hidden text for invented content. We have not released it.

## What this does not show

- **It does not show DOJ is wrong.** Before running, we set the bar for "reliable" at 40 of 50 pages confirmed faithful and accessible, and at most 2 pages with a number flag our mechanical rule could not explain. We can confirm 38 pages, and the rule counted 16 flagged pages, every one of which turned out to come from the checker or the PDF's text layer, not the model. Scanned PDFs and PDFs over 10 pages were 37 of the 87 we found, and we tested neither, so "at scale" is untested.
- **The pages are not shown to meet WCAG.** Automated rules cover only part of WCAG 2.1 AA. The pages are also not ready to post as they are: the model was told to point to image files a person would supply, and those files do not exist yet.
- **This is not an independent result.** Both readers were AI agents of our own, built on the same family of model as the one we tested, and the second reader saw the first reader's labels. One model, one run per document, one instruction, 50 documents. Nobody outside the company has repeated it.

We are not naming the governments or publishing their documents or the model's pages.

## If you are converting documents

- Budget for checking, not just converting. In this test the check that held up compared each page with the rendered PDF, not with the PDF's own text.
- Spot-check the places where text layers lie: running headers, numbered lists, logos and letterheads, maps, tables and letter-spaced headings.
- Check that every image the page refers to exists and that its alt text matches the picture.
- The 2024 rule exempts PDFs posted before your compliance date unless people use them to apply for, gain access to, or take part in your services ([28 CFR 35.201(b)](https://www.ecfr.gov/current/title-28/chapter-I/part-35/subpart-H/section-35.201)). Documents posted after that date are not covered by that exception.

## How we ran it

The instruction the model received, word for word:

> This folder (/work) contains input.pdf, a document that a US local government posts on its public website. Under the ADA Title II web rule, the government must make it conform to WCAG 2.1 Level AA. Remediate it by writing output.html in this folder: one HTML page that replaces the PDF on the website.
>
> Requirements:
> - Present all of the document's content with the text verbatim. Do not summarize, paraphrase, correct, add or omit content. Running page headers, page footers and page numbers may be omitted.
> - Give it correct semantic structure: the page language, a title, headings in a logical hierarchy, lists as lists, data tables as tables with header cells, descriptive link text, and labels for any form fields.
> - You cannot extract image files. For each meaningful image, write `<img src="image-N.png" alt="...">` with an accurate text alternative (the publisher will supply the file). Leave out purely decorative images.
> - Meet WCAG 2.1 AA, including colour contrast and a meaningful reading order. Inline CSS is allowed; no scripts or external resources.
>
> Write only output.html.

- Sample: the [CISA .gov domain list](https://github.com/cisagov/dotgov-data) (`current-full.csv`, 27 October 2026), one domain per government, random order; the first real PDF among the first three PDF links on each homepage; born-digital means at least 100 characters of text per page. Requests were spaced at least a second apart per site.
- Docling 2.143.0 used its default PDF pipeline and HTML export, plus a fixed template adding the page language, a title and a main region.
- One model run was cut off by our own two-hour time limit for the batch, not by the model; we ran it once more and scored the rerun.
- The checker bug above is in the version we froze before the run. We kept its counts as recorded and report what each flag turned out to be.

Questions or corrections: hello@cybernative.ai.
