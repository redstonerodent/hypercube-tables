from functools import reduce
from sys import argv
prod = lambda xs: reduce(int.__mul__, xs, 1)

file = argv[1]

# format:
"""
param 1	value 1	cell color	value 2	cell color etc.
param 2	value 1	etc.
etc.	etc.	etc.

horizontal	dimensions	in	precedence	order
vertical	dimensions	in	precedence	order
entry 1	cell color	param 1	0 (param 1 value)	param 2	etc.
entry 2	cell color	param 2	etc.
"""
# (each cell) is for things like background color that need to be repeated across multirows
# a cell goes with its earliest result in the list
# e.g. you might want the last line to be 'open	' with no parameters to cover everything else
# a line that starts with % is a comment


def parse(file):
    with open(file) as f:
        dimvals = {}
        while line := f.readline()[:-1]:
            if line[0]=='%': continue
            d, *vs = line.split('\t')
            dimvals[d] = list(zip(vs[::2],vs[1::2]))
        dims = {d:len(v) for d,v in dimvals.items()}
        while (line := f.readline())[0] == '%': continue
        hdims = line[:-1].split('\t')
        while (line := f.readline())[0] == '%': continue
        vdims = line[:-1].split('\t')
        entries, entryvals = [], []
        while line := f.readline()[:-1]:
            if line[0]=='%': continue
            val, each, *ds = line.split('\t')
            entryvals.append((val,each))
            try:
                entries.append(dict(zip(ds[::2],map(int,ds[1::2]))))
            except Exception as e:
                print('error processing line:')
                print(line)
                raise e

    return dimvals, dims, hdims, vdims, entries, entryvals
    # dimvals = {parameter: [value, cell color]}
    # dims = {parameter: number of values}
    # hdims = [horizontal dimensions (the top header), in order]
    # vdims = [vertical dimensions (the top header), in order]
    # entries = [{dimension: value}]
    # entryvals = [(entry name, cell color)]

dimvals, dims, hdims, vdims, entries, entryvals = parse(file+'.tsv')

# count of values for these dimensions
combos = lambda ds: prod(dims[d] for d in ds)

# translate between overall index and dictionary of each index
fold = lambda xdims, idx: fold(xdims[:-1], idx // dims[xdims[-1]]) | {xdims[-1]: idx % dims[xdims[-1]]} if xdims else {}

unfold = lambda xdims, vs: unfold(xdims[:-1], vs)*dims[xdims[-1]] + vs[xdims[-1]] if xdims else 0

# the first entry that matches this position
findentry = lambda row, col: next(i for i,e in enumerate(entries) if all(e[d]==(fold(vdims, row) | fold(hdims, col))[d] for d in e))

entrygrid = [[findentry(row, col) for col in range(combos(hdims))] for row in range(combos(vdims))]

# text version
# for d in hdims:
#     print(' '*(len(vdims)+1) + ''.join(dimvals[d][fold(hdims, c)[d]] for c in range(combos(hdims))))
# print()
# for r in range(combos(vdims)):
#     print(''.join(dimvals[d][fold(vdims, r)[d]] for d in vdims) + ' ' + ''.join(entryvals[findentry(r,c)] for c in range(combos(hdims))))

# rectangles is a list of tuples ((hstart, hend, vstart, vend), (entry, color))
# meaning [hstart, hend) x [vstart, vend) (0 indexed) should have entry (as a Block)
# and all cells should be colored
# assumes the rectangles partition combos(vdims) x combos(hdims)
def writerecs(rectangles, outfile):
    width = combos(hdims)
    height = combos(vdims)
    hoff = len(vdims)+1
    voff = len(hdims)+1

    # a list of rectangles to draw in the table, in a more convenient format
    # includes headers and handles offset
    # [((vstart, vlen, hstart, hlen), (value, color))]
    # if color is the empty string, latex will use white
    tablerects = [((1,voff-1,1,hoff-1),('',''))]
    # that's the top left empty region

    # top headers
    for i,d in enumerate(hdims):
        for copy in range(combos(hdims[:i])):
            for j,v in enumerate(dimvals[d]):
                wth = combos(hdims[i+1:])
                col = hoff + copy * combos(hdims[i:]) + j * wth
                tablerects.append(((i+1, 1, col, wth), v))

    # right headers
    for i,d in enumerate(vdims):
        for copy in range(combos(vdims[:i])):
            for j,v in enumerate(dimvals[d]):
                hgt = combos(vdims[i+1:])
                row = voff + copy * combos(vdims[i:]) + j * hgt
                tablerects.append(((row, hgt, i+1, 1), v))
                # todo

    # body
    for (hs, he, vs, ve), v in rectangles:
        tablerects.append(((vs+voff, ve-vs, hs+hoff, he-hs), v))

    with open(outfile, 'w') as f:
        f.write(f'''
\\documentclass{{standalone}}
\\usepackage[table]{{xcolor}}
\\usepackage{{nicematrix}}

\\begin{{document}}

\\begin{{NiceTabular}}{{{'c'*(width+hoff-1)}}}[hvlines]
''')
        # coloring rectangles
        f.write(f'  \\CodeBefore')

        for (vs, vl, hs, hl), (_, color) in tablerects:
            f.write(f'    \\rectanglecolor{{{color}}}{{{vs}-{hs}}}{{{vs+vl-1}-{hs+hl-1}}}\n')

        # the table content
        f.write('  \\Body\n')

        # this is 1 bigger than needed since latex 1 indexes
        # i'll ignore the first row and column
        blocks = [['' for _ in range(width+hoff)] for _ in range(height+voff)]
        for (vs, vl, hs, hl), (val, _) in tablerects:
            blocks[vs][hs] = f' \\Block{{{vl}-{hl}}}{{{val}}}'

        for row in range(1,height+voff):
            f.write('    ')
            f.write(' & '.join(blocks[row][1:]))
            f.write('\\\\\n')

        f.write('''
\\end{NiceTabular}
\\end{document}
''')

## approach 1 to prepping rectangles: greedily partition cells

# given a grid of booleans, gives rectangles (hstart, hend, vstart, vend) partitioning trues
# destructive
def rectangulate(grid):
    height = len(grid)
    width = len(grid[0])
    ans = []
    for vs in range(height):
        for hs in range(width):
            if grid[vs][hs]:
                # greedily find biggest rectangle, horizontal first
                he, ve = hs, vs
                while he < width and grid[vs][he]:
                    he += 1
                while ve < height and all(grid[ve][hs:he]):
                    ve += 1
                ans.append((hs, he, vs, ve))
                for i in range(vs, ve):
                    for j in range(hs, he):
                        grid[i][j] = False
    return ans

matches = lambda grid, val: [[entry==val for entry in row] for row in grid]

## approach 2 to prepping rectangles: sequence of splits

# a subspace is a dictionary specificing some subset of dimensions (e.g. an entry)
split = lambda subspace, d: [subspace | {d:i} for i in range(dims[d])]

disjoint = lambda s1, s2: any(d in s1 and s1[d] != s2[d] for d in s2)

contained = lambda small, big: all(d in small and small[d]==big[d] for d in big)

# split onion into subspaces fully inside or fully outside knife
# cuts in the order of dims
def dice(onion, knife):
    if disjoint(onion, knife) or contained(onion, knife):
        return [onion]
    d = next(d for d in hdims+vdims if d in knife and d not in onion)
    return [piece for chunk in split(onion, d) for piece in dice(chunk, knife)]

# dice by a sequence of knives, stopping at chunks entirely in a single knife
def multidice(onion, knives):
    ans = []
    active = [onion]
    for i,k in enumerate(knives):
        chunks = [p for c in active for p in dice(c,k)]
        ans += [(c,i) for c in chunks if contained(c,k)]
        active = [c for c in chunks if disjoint(c,k)]
    return ans

# split subspace into contiguous rectangles under dimension list ds
def separate(subspace, ds):
    # split_by = [d for d in ds[:max(i for i,d in enumerate(ds) if d in subspace)] if d not in subspace]
    ans = [subspace]
    for i,d in enumerate(ds):
        if d not in subspace and any(x in subspace for x in ds[i:]):
            ans = [p for c in ans for p in split(c, d)]
    return ans

# convert subspace to range wrt ldims, assuming it's continguous (e.g. from separate)
def interval(subspace, ldims):
    length = combos(d for d in ldims if d not in subspace)
    first = unfold([d for d in ldims if d in subspace], subspace)*length
    return first, first+length


# output files

# version that merges cells from the same entry
if 0:
    writerecs([(rec, entryvals[e]) for e in range(len(entries)) for rec in rectangulate(matches(entrygrid, e))], file+'-merge.tex')

# version that merges cells that have the same content, including different entries with the same value and color
if 1:
    entryvalgrid = [[entryvals[cell] for cell in row] for row in entrygrid]
    writerecs([(rec, e) for e in set(entryvals) for rec in rectangulate(matches(entryvalgrid, e))], file+'-mergemore.tex')

# version that splits in a guillotine and then doesn't merge back; seems to be usually worse
if 0:
    writerecs([(interval(s,hdims)+interval(s,vdims), entryvals[i]) for c,i in multidice({}, entries) for p in separate(c, hdims) for s in separate(p, vdims)], file+'-guillotine.tex')


