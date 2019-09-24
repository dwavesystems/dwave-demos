# Tetris 
### Requirements

- pygame 
- networkx
- dwave.system
- numpy
- jupyter notebook

## How to use
1. install needed requirements
2. run "jupyter notebook" command within tetris directory
3. run the cells in the jupyter notebook
4. a window pop up will display the tetris board
5. place the first piece and watch as the D-Wave places the rest
6. make modifications to the function that creates h and J values to try an achieve better results

## Notes
This is just an example to prove that the D-Wave can play tetris, however is nowhere near the best approch to tacle this problem. Currently my method is to use the D-Wave as a sampler randomly flipping approximatly 4 grid points with a higher probability given to the lower empty grid points and then checking if any returned samples match the given constraints (ie.correct shape and no holes). If a soltuion is not found within a given number of reads the beta parameter is manipulated for the next round of anneals and the "no holes" constraint is relaxed in an attempt to prevent the D-Wave from getting stuck.

The board also waits for the D-Wave to return a solution before the peice begins to fall. In the future real time decision making should be implemented.  

 
