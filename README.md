# tilesplit
CLI tilesheet splitter in Py3

usage: `python3 tilesplit.py tilesheet.png 16 tilesheet.txt`

Exported tiles are placed in a folder with the same name as the original directory. It uses `pathlib` and should work on Windows. Tested on Mac. Having someone test it on Windows would be greatly appreciated.

![](image.png)

```
default _blank_
empty _noexport_
0 0 top
1 0 side_a
2 0 side_b
0 1 side_c
1 1 side_d
2 1 bottom
```

![](finder.png)