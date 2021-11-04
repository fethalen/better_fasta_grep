Better FASTA Grep
-----------------

<img src="https://gitlab.com/fethalen/bfg/raw/master/images/bfg.png" alt="BFG logo - a pair of binoculars" align="right" width = "20%"/>

Better FASTA Grep, or BFG for short, is a Grep-like utility for retrieving
matching sequence records from a FASTA file. Given one or more patterns and a
FASTA file, it searches the file for matching headers and or sequences and
outputs any matching headers, sequences, or both.

## Features

* Search headers, sequences, or both
* Search via regular expressions or plain strings
* Case-insensitive search
* Select non-matching sequence records
* Count the number of matches
* Display line numbers in the result
* Sequence records, not individual lines, are selected
* Multi-line sequences are treated as singular units
* Flexible output options: output headers, sequences, or both

<img src="https://gitlab.com/fethalen/bfg/raw/master/images/bfg_screenshot_1.png" alt="BFG Screenshot" />

A screenshot of running BFG under macOS Mojave.

## Quick installation

The easiest way to install this program is via `pip`:

```bash
pip install better_fasta_grep
```

You can then launch `bfg` using _one_ of the following commands:

```bash
bfg --help
better_fasta_grep --help # equivalent
```

## [Documentation](https://github.com/fethalen/better_fasta_grep/wiki)

1. [Introduction](https://github.com/fethalen/better_fasta_grep/wiki#1-introduction)
2. [Installation](https://github.com/fethalen/better_fasta_grep/wiki#2-installation)
3. [Invoking `bfg`](https://github.com/fethalen/better_fasta_grep/wiki#3-invoking-bfg)
4. [Regular Expressions](https://github.com/fethalen/better_fasta_grep/wiki#4-regular-expressions)
5. [Input Data](https://github.com/fethalen/better_fasta_grep/wiki#5-input-data)
6. [Usage](https://github.com/fethalen/better_fasta_grep/wiki#6-usage)

© Department for Animal Evolution and Biodiversity 2019
