import blenderplot

blenderplot.render_tri(
    'out.png',
    [[1, 1, 0], [1, -1, 0], [-1, 1, 0], [-1, -1, 0]],
    [[0, 1, 3], [0, 2, 3]],
    colors=[[1,0,0,1],[0,1,0,1],[0,0,1,1],[1,1,1,1]],
)
