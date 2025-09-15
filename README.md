Draft proposal for the BBCT Micro .inf format, attempting to tidy up
some loose ends.

Discussion here: https://stardot.org.uk/forums/viewtopic.php?t=31577

# `inf.py`

Python 3 script that finds .inf files and tries to parse them. Point
it at your own collection and see what it says. Example invocation,
suitable for me on my laptop:

    inf.py c:\tom\github\beeb-files\ c:\temp\

If it moans about invalid chars in your .inf files, run it with
`--accept-all-chars` to allow the optional handling of invalid chars.

Run with `--no-crc` to stop it trying to check any CRCs of all the
data files.
