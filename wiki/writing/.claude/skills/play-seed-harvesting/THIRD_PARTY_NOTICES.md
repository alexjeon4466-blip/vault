# Rights and third-party notices

The source SKILL.md declares `license: MIT` and `author: Hermes Agent`. This distribution preserves that declaration and supplies the MIT text in LICENSE; it does not invent a copyright owner's personal name. Confirm ownership/permission for any further material you add before public redistribution.

The MIT declaration applies to the skill software/documentation to the extent the relevant author can license it. It is not a license for community post bodies, news articles, books, participant data or the underlying podcast/newsletter material. This package does not include a harvested source archive or reproduce those full works.

## Selected methodological adaptations: RefoundAI/lenny-skills

Pinned source commit: `13598cc54e09399bc1bc1398b0fca284110efb2f`.

- A1 evaluation methods: https://github.com/RefoundAI/lenny-skills/blob/13598cc54e09399bc1bc1398b0fca284110efb2f/skills/ai-evals/SKILL.md
- Service idea validation: https://github.com/RefoundAI/lenny-skills/blob/13598cc54e09399bc1bc1398b0fca284110efb2f/skills/idea-validation/SKILL.md
- License: https://raw.githubusercontent.com/RefoundAI/lenny-skills/13598cc54e09399bc1bc1398b0fca284110efb2f/LICENSE

Original attribution to Hamel Husain, Shreya Shankar and Lenny's Podcast/Newsletter contributors remains in the corresponding references. Selected methods are adapted in original wording. The upstream license does not turn underlying third-party material into unrestricted content.

Upstream license, retrieved from the pinned revision:

```text
MIT License

Copyright (c) 2025 Refound AI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Optional dependency: Scrapy

Project: https://github.com/scrapy/scrapy

Scrapy is an external BSD-3-Clause dependency, not vendored in this ZIP. `requirements-crawler.txt` pins the optional parser-test version. Its distribution and transitive dependencies carry their own licenses when installed; this skill does not relicense them.
