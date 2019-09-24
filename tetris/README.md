# Tetris Demo
### Requirements
- pygame 
- networkx
- dwave.system
- numpy
- jupyter notebook

## Usage
1. install needed requirements
2. run "jupyter notebook" command within tetris directory
3. open tetris_solver_base.ipynb
3. run the cells in the jupyter notebook
4. a window pop up will display the tetris board
5. place the first tetris piece and watch as the D-Wave places the rest
6. make modifications to the function that creates h and J values to try an achieve better results

## Code overview
This is just an example to prove that the D-Wave can play tetris, however is nowhere near the best approch to tackle this problem. Currently my method is to use the D-Wave as a sampler randomly flipping approximatly 4 grid points with a higher probability given to the lower empty grid points and then checking if any returned samples match the given constraints (ie.correct shape and no holes). If a soltuion is not found within a given number of reads the beta parameter is manipulated for the next round of anneals and the "no holes" constraint is relaxed in an attempt to prevent the D-Wave from getting stuck.

The board also waits for the D-Wave to return a solution before the peice begins to fall. In the future real time decision making should be implemented.  

## Code specifics 
To improve upon this demo you can make changes to the following generate_h function.
```python
def generate_h(board,piece,embedding):# generates an h with only non fixed varaibles and no J 
    board_full = [ro [::-1]for ro in board]
    max_height = max([j for i,val in enumerate(board_full) for j,x in enumerate(val) if isinstance(x,int)])
    if max_height <=4:
        max_height=4
    else:
        max_height = max_height
        
    max_width = max([i for i,val in enumerate(board_full) for j,x in enumerate(val) if isinstance(x,int)])
    if max_width <=5:
        max_width=max_width+4
    else:
        max_width =9
    board_ = [ro[:max_height] for ro in board_full][:max_width]
#     shape = PIECES[piece['shape']][piece['rotation']]
#     coords = shape_to_valid_coord_set([shape])
#     coord_combos = valid_coord_to_cobo(coords,board)
    h={}
    for x in range(max_width):
        for y in range(max_height):
             if isinstance(board_[x][y],str):
                    h.update({f'{x}_{y}':-y/max_height})
        
    static = {}
    for x in range(max_width):
        for y in range(max_height):
            if isinstance(board_[x][y],int) and f'{x}_{y}' not in h.keys():
                static.update({f'{x}_{y}':-1})
    for var in embedding.keys():
        if var in h.keys():
            continue
        x,y = map(int,var.split('_'))
        if isinstance(board_full[x][y],int):
            static.update({f'{x}_{y}':-1})
        else:
            static.update({f'{x}_{y}':1})
    return h,{},static
```
where h are the biases of the empty grid spaces, {} is a placeholder for J couplings if you would like to include them, and static are the grid spaces which are already filled.  

In the tetris.py folder I made the choice to not place any peices in the last column (max_width=9 in generate_h) and instead do a quick check when an "I" shape appears to see if four lines can be cleared. This is in an attempt to maximize the points by trying to always clear four lines at once. The relevant lines to change this behaviour in tetris.py are 226-235
```python
if fallingPiece['shape']=='I' and all([isinstance(y,int) for x in board[-4:] for y in x]):
                flipped = ['9_0','9_1','9_2','9_3']
                if fallingPiece['rotation']==0:
                    move = (5,0)
                else:
                    move=(5,1)
            else:
                h,J,static = generate_h_J(board,fallingPiece,embedding)
                no_valid = True
                holes=has_holes(board)
                ```

 
