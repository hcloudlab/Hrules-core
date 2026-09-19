# Third-Party Notices

This file records third-party notices for source data used by Hrules. Hrules transforms source entries into client-neutral routing matchers; source inclusion does not imply endorsement by the upstream project.

## StevenBlack first-party hosts

Source: `StevenBlack/hosts`, artifact `data/StevenBlack/hosts`.

Hrules modification: null-route hosts entries are normalized into exact canonical `domain` matchers. Hrules does not broaden these entries into suffix rules.

Upstream license: MIT.

The MIT License (MIT)

Copyright © 2023 Steven Black

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the “Software”), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## AdAway default hosts

Source: `AdAway/adaway.github.io`, artifact `hosts.txt`.

Upstream file title: AdAway default blocklist.

Upstream license: Creative Commons Attribution 3.0.

Source project: https://github.com/AdAway/adaway.github.io/

License: http://creativecommons.org/licenses/by/3.0/

Hrules modification: hosts-file null redirects are extracted and normalized into exact canonical `domain` matchers. Hrules does not broaden these entries into suffix rules. This is a transformed/derived representation, not an unmodified copy of the upstream hosts file.
