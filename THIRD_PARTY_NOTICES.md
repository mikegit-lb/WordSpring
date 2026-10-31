# Third-party data notices

## Openjam vocabulary data

`additional_seed_data.py` contains 367 A2/B1 entries derived from the English vocabulary data in [Openjam](https://github.com/amirj4m/openjam). Openjam identifies Princeton WordNet 3.1 as a source for word senses and says its CEFR labels are cross-referenced from public lists. This project selected the added headwords using the Oxford 3000 CEFR-level list as a level reference. The added definition and example text is retained from the Openjam data subset. Source notes are in [Openjam's attribution file](https://github.com/amirj4m/openjam/blob/main/ATTRIBUTION.md).

Openjam is distributed under the MIT License:

> MIT License
>
> Copyright (c) 2026 Openjam contributors
>
> Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Oxford 3000 level reference

The added entries' A2/B1 selection was cross-checked against the [Oxford 3000 by CEFR level](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000_by_CEFR_level.pdf). Oxford Learner's Dictionaries and Oxford 3000 are trademarks of Oxford University Press. This project is independent and is not endorsed by Oxford University Press.

## Application runtime and build tools

The Windows release is built with CPython 3.12.10, PySide6 6.12.0, pyttsx3 2.99, pywin32 312, comtypes 1.4.17, and PyInstaller 6.22.3. The exact package versions used for the reproducible build are recorded in `requirements.lock`.

- **Qt for Python / PySide6 6.12.0** — The community distribution offers LGPLv3/GPLv3 licensing. WordSpring uses the LGPLv3 route for the Qt components it imports. The Store build excludes the unused Qt Virtual Keyboard module, which is GPL-only. A copy of LGPLv3 is included in the Store package under `Licenses/LGPL-3.0.txt`. Review the [Qt for Python licensing terms](https://doc.qt.io/qtforpython-6/commercial/index.html), the [Qt for Python third-party notices](https://doc.qt.io/qtforpython-6/licenses.html), and the [Qt licensing guide](https://doc.qt.io/qt-6/licensing.html) before distributing. If you cannot meet the applicable LGPL requirements, use an appropriate commercial Qt for Python distribution instead.
- **Python 3.12** — Python Software Foundation License; the license is included in the Store package under `Licenses/Python-3.12.txt`.
- **PyInstaller 6.22.3** — GNU GPL version 2 or later with the PyInstaller bootloader exception; its license text is included under `Licenses/PyInstaller-COPYING.txt`.
- **pyttsx3 2.99** — Mozilla Public License 2.0; its license text is included under `Licenses/pyttsx3-MPL-2.0.txt`.
- **pywin32 312** — PSF-style license; its license text is included under `Licenses/pywin32.txt`.
- **comtypes 1.4.17** — MIT License; its license text is included under `Licenses/comtypes-MIT.txt`.
- **Inno Setup 7.1.1** — used to build `WordSpring-Setup.exe`. Copyright (C) 1997-2026 Jordan Russell; portions Copyright (C) 2000-2026 Martijn Laan. https://jrsoftware.org/ The Inno Setup license permits commercial use and redistribution subject to its stated conditions; its required copyright notices are retained in the installer.

The Store build does not include the optional `edge-tts` package and makes no network requests. Its speech output uses Windows SAPI.
