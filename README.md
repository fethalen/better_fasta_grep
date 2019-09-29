Better FASTA Grep
-----------------

## About

<img src="https://gitlab.com/fethalen/bfg/raw/master/images/bfg.png" alt="BFG logo - a pair of binoculars" align="right" width = "20%"/>

Better FASTA Grep, or BFG for short, is a Grep-like utility for retrieving
matching sequence records from a FASTA file. Given one or more patterns and a
FASTA file, it searches the file for matching headers and or sequences and
outputs any matching headers, sequences, or both.

## Quick installation

Download the script onto your computer by clicking the 'Download' button on
this page, or use `git` to copy the `bfg` project into your current directory:

```bash
git clone https://gitlab.com/fethalen/bfg
```

Make the script executable by typing `chmod +x bfg`, while in the `bfg`
directory. `bfg` can now be run by typing the following command.

```bash
./bfg --help
```

If you see yourself using this tool frequently, then you can add it to your
path, so that you can reference it from any working directory. First, put the
`bfg` directory into a permanent location (not your Desktop or Downloads
folder). I keep my copy of `bfg` in my `~/projects` directory, so for me I
would type:

```bash
export PATH=$PATH:${HOME}/projects/bfg >> ~/.bashrc
```

## Documentation

1. [Introduction](https://gitlab.com/fethalen/bfg/wikis/home#introduction)
2. [Installation](https://gitlab.com/fethalen/bfg/wikis/home#installation)
3. [Invoking `bfg`](https://gitlab.com/fethalen/bfg/wikis/home#invocation)
4. [Regular Expressions](https://gitlab.com/fethalen/bfg/wikis/home#regex)
5. [Input Data](https://gitlab.com/fethalen/bfg/wikis/home#input)
6. [Usage](https://gitlab.com/fethalen/bfg/wikis/home#usage)

## License



© Bleidorn Lab 2019
