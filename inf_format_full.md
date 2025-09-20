# .inf Format for Acorn Stuff

This is a draft version of the document, and everything remains up for debate. The spec is written like it's a done deal, but only because it's fewer words that way. 

# Preamble

The keywords MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.html). As per [RFC 8174](https://www.ietf.org/rfc/rfc8174.html), the standardized meaning only applies when they appear all in capitals, as above.

Syntax specifications are as per [RFC 2234](https://www.rfc-editor.org/rfc/rfc2234).

# What is the .inf format?

As well as the actual file data or directory contents, Acorn systems maintained some amount of additional metadata associated with the file or directory. There's nowhere particularly convenient to store this stuff on modern systems, and as an additional annoyance, the Acorn file naming rules have always been a bit different from everything else.

The .inf format was created by Wouter Scholten to solve these problems. Each Acorn file is stored as 2 files on the modern system: one file containing the actual file contents, an opaque sequence of bytes, and a second structured file holding the Acorn-specific metadata and original Acorn name.

# Aim of this document

The .inf format has been well used over the years, and has grown some extensions to support directories, additional attributes and metadata, and so on. This spec attempts to tie things together by creating a syntax that covers everything (or as nearly everything as possible).

Goals:

- specify a synax that matches all (or as very nearly all as possible...) existing files
- extend the format to cover previously-underspecified cases
- try not to make it _too_ much effort to update existing consumers to support it
- ensure metadata is perfectly round-trippable, at least in principle
- be interpretable as equally applicable to ADFS and DFS
- keep it straightforward to produce (and feasible to consume) on 8-bit systems in 6502 or 8-bit BBC BASIC

Non-goals:

- clean sheet redesign
- restrict Acorn file/directory naming (the names are opaque sequences of bytes)

For existing unmodified producers: the updated syntax it defines attempts to be one that will accept very nearly all existing .inf files. Problem cases are rare enough they can be fixed by hand. Existing .inf file producers will therefore automatically already be generally conforming in practice.

For existing unmodified consumers: existing consumers are inevitably limited to accepting whatever they are able to interpret. But since they interpret existing .inf files, as per the above goal, the syntax they accept will be conformant (even if they can't accept all conforming .inf files).

For updated producers: additional extensions give newer or updated producers the ability to deal with previously problematic or ambiguous cases. Updated producers that would like to retain compatibility with particular consumers can emit compatible files (likely a subset of all valid ones), and, as per the consumer compatibility goal, those files are conformant.

Finally, for updated consumers: the syntax has been expanded to accommodate a wider range of .inf files, while remaining hopefully similar enough to the previous spec that it's not going to be too annoying to update the code.

One additional note: this document assumes that producing and consuming tools are running a modern system. (On the basis that on an Acorn system, there'll already be somewhere to store the attributes, and that's where they'll be stored already.) The format is intended not to be too difficult to produce on an Acorn system, whether you're trying to do it in 6502 or BBC BASIC, but this is not an expected use case.

Consuming .inf files on an Acorn system is intended to be feasible, even if 8-bit, but this isn't an expected use case.

# .inf format description

To represent an Acorn file/directory on a modern system (henceforth described as a PC, but it could be anything), the .inf format uses 2 directory entries on the PC.

One holds the file/directory contents. For an Acorn file, it's a file, the so-called data file, holding the contents of the file as it would be seen on the Acorn system; for an Acorn directory, it's a directory, the so-called PC directory, containing any further PC directory entries corresponding to Acorn files/directories under the corresponding Acorn directory (and so on, possibly recursively).

The other, always a file in both cases, is the attribute file, holding the Acorn-specific metadata, including the Acorn name. 

The two entries are related by their PC names, with the name of the attribute file being the full name of the data file/PC directory, extension (if any) and all, with `.inf` or `.INF` appended.

These two extensions are considered equivalent, so tools MUST try both when running on a case-sensitive filing system. (Rationale: there are `.inf` and `.INF` files out there, and this document is trying to specify how to handle everything.)

Producers MUST always use `.inf` or `.INF` specifically. (Rationale: existing producers do one or the other.)

(This document calls it `.inf`. As per the above rules: any time this document uses `.inf`, `.INF` also applies.)

Example data file names and attribute file names:

| Data file name | PC attribute file name | Notes                                     |
|----------------|------------------------|-------------------------------------------|
| `$.ELITE`      | `$.ELITE.inf`          |                                           |
| `ELITE`        | `ELITE.inf`            |                                           |
| `ELITE.dat`    | `ELITE.dat.inf`        | `.inf` doesn't replace existing extension |
| `ELITE.inf`    | `ELITE.inf.inf`        | this is a SHOULD NOT! - see below         |

Example PC directory names and attribute file names:

| PC directory name | PC attribute file name | Notes                                     |
|-------------------|------------------------|-------------------------------------------|
| `$`               | `$.inf`                |                                           |
| `LIBRARY.dir`     | `LIBRARY.dir.inf`      | `.inf` doesn't replace existing extension |
| `TEST.inf`        | `TEST.inf.inf`         | this is a SHOULD NOT! - see below         |

The `.inf` extension is added by simple string concatenation, and any existing extensions remain in place.

## Naming PC directory entries

The naming of the PC directory entries is up to the producer. Most modern systems and tooling can deal with most Acorn names, but there'll always be corner cases.

The Acorn file/directory name is stored in the attribute file, so the PC directory entry naming doesn't actually matter, but as a rule of thumb producers should try to reproduce the Acorn name as best they can. This makes life easier for the person using the tool.

(The annoying Windows file name restrictions are worth bearing in mind: https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file. Shell annoyances are also be worth thinking about: names with `%` or `^` in are annoying to deal with in the Windows command prompt; names with `$` (not exactly uncommon on Acorn systems...) can be a pain in POSIX-type shells. And so on.)

Producers SHOULD bear in mind the possibility of creating odd loops of `.inf` names, such as the `ELITE.inf.inf` and `TEST.inf` cases above, and SHOULD NOT emit them. (Rationale: depending how the consuming tool searches for files, it may get confused.)

## Finding data files/PC directories by Acorn name

It's up to each consuming tool how it finds the PC file/directory corresponding to an Acorn name.

Consumers SHOULD do an exhaustive search of some kind, because otherwise they run the risk of not finding a file that exists. The extent of this exhaustive search is not prescribed, but it should at least include the PC directory likely to contain the file. (Rationale: the Acorn name is the one in the attribute file, so this has to be at least a SHOULD.)

Even if not doing an exhaustive search, consumers MUST check the Acorn name supplied against the Acorn name found in the attribute file, and consider the file not found if the name doesn't match. (Rationale: only the Acorn name in the attribute file counts.)

The spec imposes no particular restriction on what form the Acorn name should actually take, and how tools might map PC directory structure to Acorn directory structure.

## Contents of the data file (for Acorn files)

The data file is the contents of the file exactly as it would be found on the Acorn system. No processing should be done on the contents. It needs be exactly the sequence of bytes you'd see from `*DUMP` or `*LOAD` or similar.

This MUST be stored verbatim. (Rationale: any translations that modern systems might apply (line ending conversion, Unicode stuff, etc.) will make a mess of files that are intended for consumption as-is by Acorn systems.)

## Contents of the PC directory (for Acorn directories)

The PC directory should contain the attribute and data files for any Acorn files under that directory, and the attribute file and PC directories for any nested Acorn directories.

## Contents of the attribute file

The attribute file is a text file with the following character set, a subset of the 7-bit ASCII range:

    VALID_CHAR = HTAB / LF / CR / SP / VCHAR
	
Invalid chars are anything else:

	INVALID_CHAR = %x00-08 / %x0B-0C / %x0E-1F / %x7F-FF

Producers MUST NOT emit files containing characters matching `INVALID_CHAR`.

Consumers MAY reject files containing them. (Rationale: be strict about what you accept...)

Consumers MAY choose to accept chars outside the valid range, for compatibility with .inf files from older tools. (Rationale: the spec is trying to support everything.) If doing this, consider any set containing the character %x7E to also include `INVALID_CHAR`. Consumers that do this MUST treat the chars as-is. (Rationale: they are presumably that way for a reason.)

There are no specific size limits to the attribute file, which, in particular, may end up longer than 256 bytes.

### Syntax elements in the attribute file

The attribute file consists of one line, terminated by end of file or end of line. (For the definition of `LF`, etc., see [RFC 2234 section 6.1](https://www.rfc-editor.org/rfc/rfc2234#section-6.1).)

    eol = LF / CR / (CR LF)

Producers MUST NOT emit `LF CR`. (Rationale: it is not widely supported on non-Acorn systems.)

Consumers MAY accept `LF CR`. (Rationale: despite being non-standard and not well supported, it is still a perfectly good 2-byte line ending.)

Fields are separated with runs of white space.

    spaces = 1*(HTAB / SP)
	
A string field consists of a run of printable non-space 7-bit ASCII characters starting with a character other than a `DQUOTE` (`"`), or a run of printable 7-bit ASCII characters surrounded by `DQUOTE` characters. See the [string fields section](#string-fields) below.

    unquoted_string_field = (%x21 / %x23-7E) *(%x21-7E)
	quoted_string_field = DQUOTE *(%x20-7E) DQUOTE
	string_field = unquoted_string_field / quoted_string_field
	
A hex field consists of a run of hex digits. Lower case and upper case are equivalent.

    ALLHEXDIG = DIGIT / "A"-"F" / "a"-"f"
    hex_field = 1*(ALLHEXDIG)
	
A generic extra info field is of the form `KEY=` or `KEY=VALUE`, where `KEY` is an alphanumeric string and `VALUE` (if present) is a `string_field`. (If `VALUE` is not present, the value is an empty string.)

	extra_info_field_with_no_value = 1*(ALPHA / DIGIT / "_") "="
    extra_info_field_with_value = 1*(ALPHA / DIGIT / "_") "=" string_field
	
There is one exceptional extra info field, `CRC` that may have one single extra `SP` after the `=` and before the value. There are .inf files with this syntax in the The BBC Lives! collection, possibly due to a bug in early iterations of tools. This deprecated version of the CRC field gets its own completely unique irregular special syntax:

    deprecated_crc_extra_info_field = "CRC=" SP hex_field
	
The syntax for each extra info field is then:

    extra_info_field = extra_info_field_with_no_value / extra_info_field_with_value / deprecated_crc_extra_info_field
	
The deprecated CRC extra info field case is included in the syntax, and consumers MAY decide to support it, but it is optional. (Rationale: it's deprecated, for hopefully obvious reasons, and this isn't in Wouter's spec so it isn't even a "SHOULD". But these files exist, so the spec should note them, and it should be permissible to support them.)

The deprecated crc extra info field specifies exactly how this one specific field is to be treated. Consumers MUST NOT accept multiple spaces after the `=`, nor use this logic for a field with any other name. This is a one-off special case. (Rationale: no reason to allow this to happen again.)

Producers MUST NOT emit `CRC` extra info fields with this syntax. (Rationale: it's deprecated.)
	
Keys starting with `_` are syntactically valid, but reserved for future expansion in some unspecified way.
	
The access field is a sequence of Acorn attribute chars, upper case or lower case, or `Locked`, or `LOCKED`.

    access_field = "LOCKED" / "Locked" / 1*("E" / "e" / "L" / "l" / "W" / "w" / "R" / "r" / "D" / "d")
	
The access field syntax is not always unambiguously non-hex. If given the choice between `hex_field` and `access_field`, tools SHOULD interpret `E` or `D` (or their lower-case equivalents) as matching `access_field`. (Rationale: it's always guesswork, and it'll probably be 2 hex digits if output as a byte. This is probably the least bad way to do it.)

If it otherwise looks like hex, it SHOULD be treated as hex. (Rationale: Seems safest, but, as above regarding the guesswork aspect. `ED` and `DE` aren't valid Acorn attributes, nor are duplicated letters such as the `DDDDDD` in Hypersports.)

The DFS access field can hold a subset of the `access_field` values.

    dfs_access_field = "Locked" / "LOCKED" / "L"

### String fields

The rules for this are a mite untidy, but not ambiguous.

#### Unquoted strings

Unquoted strings start with a non-`DQUOTE`, and end at the next space character or end of file. Any `DQUOTE` or `%` in the string counts as itself; only `spaces` or eof terminates the unquoted string.

#### Quoted strings

Quoted strings start with a `DQUOTE`, and end at the next `DQUOTE`. (Quoted strings must have a terminating `DQUOTE`. End of file is not a valid terminator.)

Inside a quoted string, percent-encoding (see [RFC 3986 section 2.1](https://www.rfc-editor.org/rfc/rfc3986#section-2.1)) can be used to specify any 8-bit value for a given character.

Producers MUST percent-encode `DQUOTE` (`%22`). (Rationale: to avoid literal `DQUOTE` chars appearing in the string and terminating it.)

Producers MUST percent-encode `%` (`%25`), as per the RFC. (Rationale: there's no other way to do it.)

Producers MUST percent-encode any bytes in the filename outside the 7-bit printable range. (Rationale: even updated consumers capable of handling the quoted syntax are not guaranteed to be able to accept unprintable bytes.)

Producers MAY percent-encode any other char, even if it could just be used verbatim. (Rationale: many percent-encoding helper routines are intended for URLs, and will percent encode characters with the URL-safe set in mind.)

Consumers MUST accept percent encoding for any char value, even when providing that char verbatim would be an option. (Rationale: as above, producers cannot be assumed to encode just the minimal set. Or maybe it's just easiest to percent-encode everything sometimes.)

Consumers MUST NOT attempt to interpret any kind of escaping other than percent-encoding, including (but not limited to) other widely-supported syntaxes such as doubled-up quotes, GSREAD syntax, C/JSON-style escaping, and the like. (Rationale: percent encoding covers everything. There is no reason to support multiple syntaxes.)

### Attribute file fields

Putting all the above components together, the syntax for the attribute file is as follows.

`...` here indicates the remainder of the first line of the file.

Every field mentioned here is separated by `spaces` from the next and previous, even though this isn't explictly called out. There are a lot of fields, and the syntax is involved enough already.
	
    ("TAPE") string_field (access_field / (hex_field (hex_field (dfs_access_field / (hex_field ((access_field / hex_field) *(hex_field))))))) *(extra_info_field) ("NEXT" ...)
	
This is a bit much, but it boils down to matching one of 3 syntaxes.

Syntax 1 allows any number of hex fields, the 4th of which may be an access field.

	("TAPE") string_field (hex_field (hex_field (hex_field (hex_field / access_field) *(hex_field)))) *(extra_info_field) ("NEXT" ...)
	    ; syntax 1

Syntax 2 allows up to 2 hex fields and an optional DFS access field.

    ("TAPE") string_field (hex_field (hex_field (dfs_access_field))) *(extra_info_field) ("NEXT" ...)
	    ; syntax 2 (TubeHost/BeebLink produce this)

(Note that syntax 2 is not distinguishable from syntax 1 until you meet a DFS access field.)

Syntax 3 allows a mandatory access field only.

	("TAPE") string_field access_field *(extra_info_field) ("NEXT" ...)
	    ; syntax 3 (ADFS Explorer produces this for directories)

Taking these fields in order:

`TAPE`, if specified, indicates that this file came from a cassette tape. (Note that `TAPE` is not a string field, and only matches the literal value.) This doesn't seem to have seen much use, and it's syntactically kind of ambiguous, so it's deprecated. Consumers MUST check for this and treat the following field as file name if present. (Rationale: it's in Wouter's spec.)

Producers MUST NOT emit this. (Rationale: it's deprecated.) 

`string_field` is the Acorn file/directory name. This spec imposes no specific restrictions on its format, but consumers may reject names if they'd be inappropriate for the tool's specific use case.

Producers MUST quote the name if it would be literally `TAPE`. (Rationale: so that it doesn't trip the `TAPE` rule for consumers that support that.)

Producers MUST emit names using the original medium's character set, quoted and encoded with percent encoding if required. The name is a string field, so any bytes can be encoded, and they don't have to make sense to any modern encoding. In particular, producers MUST NOT do any conversion to UTF-8. (Rationale: the Acorn name is for the Acorn system's use, and should be stored verbatim in the attribute file.)

The `hex_field` fields are the metadata fields. There's no limit on how many can be specified, but the first 10 have specific interpretations, as follows.

| # | What              | Notes                             |
|---|-------------------|-----------------------------------|
| 0 | load address      | not very relevant for directories |
| 1 | exec address      | not very relevant for directories |
| 2 | length            | not very relevant for directories |
| 3 | access            |                                   |
| 4 | modification date |                                   |
| 5 | modification time |                                   |
| 6 | creation date     |                                   |
| 7 | creation time     |                                   |
| 8 | user account      |                                   |
| 9 | auxiliary account |                                   |

(If encountering syntax 2, only load and exec addresses are provided. The DFS access field provides the value for the access attribute. The length, if needed, must come from the data file.)

(If encountering syntax 3, no addresses are provided, and the access provides the value for the access attribute. This only really makes sense for directories. Producers SHOULD NOT emit this syntax for files. Consumers MAY reject this syntax for non-directories.)

Producers SHOULD emit hex fields #0 and #1 as 8-digit 32-bit hex numbers, certainly at least when the numbers get past 4 digits. (Rationale: every bit is then unambiguous.)

Consumers MAY try to detect 6-digit hex numbers supplied for load and execution addresses, and sign-extend them to 32 bits if the most significant two digits are `FF` specifically. For example, treat the load address `FF0E00` as representing the address 0xffff0e00. (Rationale: it seems some tools did print the 6-digit DFS-style output.)

If trying to detect 6-digit hex numbers, consumers MAY also attempt to guess, though this is a bit risky. For example, perhaps `00FF0E00` should be interpreted as `FFFF0E00`. (Rationale: this may sometimes be more useful than treating it as-is.)

The load, exec and length fields are not very useful for directories, but are needed when specifying a numeric access bytes.

`*(extra_info_field)` are the optional extra info fields, a structured set of key/value pairs, each with an alphanumeric name and a string value. The extra info fields end at the end of file, or if a verbatim `NEXT` is encountered. Note that there is no separator between the hex fields and the extra info (or `NEXT`) fields, but neither option is valid as a hex value or an access field (of either kind) so the change can be detected that way.

`NEXT` if present, indicates the file name of the next exepcted file on tape. This is deprecated, on account of the specific syntax. Consumers MUST handle this field, and ignore the rest of the line, but they are not obliged to actually pay any attention. (Rationale: it's in Wouter's spec.)

Producers MUST NOT emit this. (Rationale: it's deprecated.)

Consumers MUST stop reading at end of line (first `LF` or `CR`), or end of file. (Rationale: subsequent lines are reserved for future expansion.)

Producers SHOULD emit syntax 1. (Rationale: syntax 1 supports the widest range of stuff.)

Producers SHOULD emit access bytes as 2-digit hex values. (Rationale: avoids any ambiguity about whether it's a DFS-style or ADFS-style access value.)

### The access byte

The access byte can be translated to or from the symbolic access characters as follows.

| Bit | Value | Char | What                    | Notes               |
|-----|-------|------|-------------------------|---------------------|
| 0   | 0x01  | R    | Readable by you         |                     |
| 1   | 0x02  | W    | Writeable by you        |                     |
| 2   | 0x04  | E    | Executable by you       |                     |
| 3   | 0x08  | L    | Not deletable by you    |                     |
| 4   | 0x10  | r    | Readable by others      | NFS, not 8-bit ADFS |
| 5   | 0x20  | w    | Writeable by others     | NFS, not 8-bit ADFS |
| 6   | 0x40  | e    | Executable by others    | NFS, not 8-bit ADFS |
| 7   | 0x80  | l    | Not deletable by others | NFS, not 8-bit ADFS |

The access byte can be guessed at from the DFS-style access field as follows.

| Bit | Value | State    | What                 | Notes |
|-----|-------|----------|----------------------|-------|
| 3   | 0x08  | `Locked` | Not deletable by you |       |

Consumers MAY treat the DFS Locked state as implying other bits are set. (Rationale: this is basically impossible to do nicely, so we can't insist on anything.)

Producers SHOULD emit an access byte rather than a DFS-style access field, but, if they must, they MAY treat other bits set as implying the DFS-style access state is `Locked`. (Rationale: same.)

Note that there is no access byte bit for `D` or `d`. If the corresponding PC directory entry is a directory, the Acorn directory entry is a directory; and if the corresponding PC directory entry is a file, the Acorn directory entry is a file.

If the access is specified symbolically, consumers SHOULD NOT use it to check that the directory entry is of the right type. (Rationale: make symbolic and non-symbolic access bytes symmetrical. Maybe it's arguable though.)

If specifying the access symbolically, producers SHOULD NOT emit `D` if the entry is a directory. (Rationale: same.)

### No attribute file?

Consumers MAY treat PC files/directories that don't have associated attribute files as representing Acorn files/directories. As no PC file name encoding is specified, translating the corresponding PC names to Acorn names would be up to each tool, as would be the values for any of the Acorn attributes.

Producers could avoid writing an attribute file, but in practice they probably SHOULD, as the PC file name encoding is not specified and this wil ensure the Acorn name will transfer to other tools.

### Known extra info fields

#### `CRC`

16-bit CRC of the data file, as a hex value. The algorithm is [CRC16/XMODEM](https://reveng.sourceforge.io/crc-catalogue/16.htm#crc.cat.crc-16-xmodem), same as the BBC Micro tape checksum.

In Python, `binascii.crc_hqx(data,0)` will give the same result.

Some of the files in The BBC Lives! archive have invalid CRCs, including some that specify a value of `FFFFFFFF`. Not sure what the story is here.

Producers SHOULD NOT emit this field for directories. (Rationale: whatever it's the CRC of, it's almost certainly going to be inconvenient to check.)

Producers MUST NOT emit incorrect values for this field for files. It's an optional field; simpler just not to emit it.

#### `CRC32`

32-bit CRC of the file, as a hex value. The algorithm is the same as used by the .zip file format. See, [CRC-32 example on Wikipedia](https://en.wikipedia.org/wiki/Computation_of_cyclic_redundancy_checks#CRC-32_example).

In Python, `binascii.crc32(data)` will give the same result.

Producers SHOULD NOT emit this field for directories. (Rationale: whatever it's the CRC of, it's almost certainly going to be inconvenient to check.)

Producers MUST NOT emit incorrect values for this field for files. It's an optional field; simpler just not to emit it.

#### `OPT`

Auto-boot option for the directory, found in its attribute file: typically 0 (none), 1 (`*LOAD !BOOT`), 2 (`*RUN !BOOT`) or 3 (`*EXEC !BOOT`).

#### `OPT4`

Auto-boot option for the `!BOOT` file, found in its attribute file. Values as above.

#### `DIRTITLE`, `TITLE`

Title of the directory.

#### `DATETIME`

String value of the form `YYYYMMDDhhmmss`.

# Example parsing code

TODO

There's some in `inf.py` in the repository, but it's more of a sanity check for the syntax than necessarily something to be copied, let alone reused.

# Test data

TODO

Set of .inf files, including some that should be considered invalid, and expected results for the valid ones. Creating the cases shouldn't be too hard but not sure offhand how to represent the expected data.

JSON is easy to parse on modern systems, but insists on UTF-8, which might be a blocker for some tests. Also annoying to parse on the 8-bits, which is a bit mean if this spec is hoping to make 8-bit implementations feasible.

# How existing tools arrange files

This section is purely informative.

The attribute and data files can in principle be arranged in the PC directory structure however would be convenient, but in practice tools have ended up dealing with this in two ways: one to cater for files extracted from DFS disks, and one to cater for files extracted from ADFS disks. In both cases the PC directory structure reflects the UI on the Acorn side.

This isn't to suggest that future tools couldn't (or shouldn't) do things differently.

## DFS-style arrangement

A DFS drive (or the tool's equivalent of) is represented by a PC directory.

Attribute and data files for Acorn files in that DFS drive are immediate children of that PC directory.

The attribute file provides the DFS directory and name, e.g., `$.!BOOT` or `B.LOADER`.

The DFS is not hierarchical.

Disc Image Manager produces an attribute file for the DFS drive's PC directory, which is probably a good idea, as it's somewhere sensible to store the drive title and boot option. (You can use the `OPT4` extra info value in the `!BOOT` file, but now the value can only be changed when `!BOOT` exists, which isn't how the DFS works.)

## ADFS-style arrangement

An Acorn directory is represented by a PC directory and corresponding attribute file.

Attribute files and data files/PC directories for Acorn files in that Acorn directory are immediate children of that PC directory.

The attribute file provides the parent-relative Acorn name, e.g., `!BOOT` or `LOADER`.

# What if we need to further extend the format?

The hex fields can be added to if required. This is already part of the syntax.

The extra info section provides scope for additional key/value pairs, with opaque values that are round-trippable.

Keys starting with `_` are deliberately reserved for additional future expansion - and the .inf format is currently restricted to the first line in the file. If additional new syntax is really necessary then some combination of these can be brought into play.

# Questions I have no idea about

I got bored of going back and forth in my mind without being able to come up with a decision.

## Exhaustive search

Should this be a MUST? But I was thinking, I'd quite like to leave open (pending discussion) the option of having an empty name (`""`) in the .INF file, meaning the PC name is authoritative. But maybe that'd be silly and we should leave that option for another day.

## Load/exec/length for directories

Feels like consumers SHOULD ignore these - or would there be something useful in them??

Producers SHOULD write them all as 0 (IMO), but it doesn't really matter if the consumer is just going to ignore them.

## Length for files

I feel like having producers update this ought to be a MUST, but... maybe not.

Consumers MAY check - after all, it's there! But SHOULD they?

## Access byte stuff

Not happy about this bit, but DFS and ADFS just don't work the same way.

## `OPT4=`

I don't like having this attached to `!BOOT` specifically, but there's no directories in DFS (from the .inf point of view) - so where else should it go? BeebLink does its own thing. I think the Disc Image Manager idea of maintaining a .inf for the drive is tidier.

# More suggestions please

As per the start, same at the end: this remains all up for debate.

<!--
Local Variables:
tom-disable-fill-paragraph: t
End:
-->
