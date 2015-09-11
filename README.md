# swift-doccomment-converter

This is a script to convert Swift 1.2 documentation comments to new
Swift 2.0 format while respecting line length and hanging indents.

## Usage:

```sh
$ convert-comments [MAX LINE LENGTH] [FILES TO CONVERT...]
```

## Example usage:

You can pass a single file and limit lines to 80 characters:

```sh
$ convert-comments 80 path/to/foo.swift
```

You can also leverage [`git
ls-files`](https://www.kernel.org/pub/software/scm/git/docs/git-ls-files.html)
to convert all Swift files checked into git and limit them to 110
characters:

```sh
$ git ls-files -z "*.swift" | xargs -0 convert-comments 110
```

#### Warning:

Please check everything important into source control before running
this script. It could have unexpected side effects.

### Motivation:

Unfortunately the Swift 2 conversion tool doesn't handle all the cases
of documentation comments I've run into. For example if you have a
comment like this:

```swift
/**
:param: something This is the comment
                  it is on multiple lines
*/
```

The Swift conversion tool converts this to:

```swift
/**
- parameter something: This is the comment
                  it is on multiple lines
*/
```

Where the hanging indent is off. Besides this spacing the tool doesn't
seem to to catch all cases.
