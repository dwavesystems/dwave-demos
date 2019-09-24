# Tetromino (a Tetris clone)
# By Al Sweigart al@inventwithpython.com
# Modifications by Mitchell Roman
# http://inventwithpython.com/pygame
# Released under a "Simplified BSD" license
import networkx as nx
import matplotlib.pyplot as plt
import random, time, pygame, sys
from dwave.system import DWaveSampler
from dwave.system.composites.embedding import FixedEmbeddingComposite,EmbeddingComposite
from pygame.locals import *
import numpy as np
FPS = 25
WINDOWWIDTH = 640
WINDOWHEIGHT = 480
BOXSIZE = 20
BOARDWIDTH = 10
BOARDHEIGHT = 20
BLANK = '.'

MOVESIDEWAYSFREQ = 0.15
MOVEDOWNFREQ = 0.1

XMARGIN = int((WINDOWWIDTH - BOARDWIDTH * BOXSIZE) / 2)
TOPMARGIN = WINDOWHEIGHT - (BOARDHEIGHT * BOXSIZE) - 5
colours ={'T':3,'I':0,'O':4,'J':1,'S':2,'Z':6,'L':5}
#               R    G    B
WHITE       = (255, 255, 255)
GRAY        = (185, 185, 185)
BLACK       = (  0,   0,   0)
PURPLE      = (102,   0, 204)
LIGHTPURPLE = (153,   51, 255)
ORANGE      = (173,   56, 0)
LIGHTORANGE = (255,   153, 51)
PINK      = (255,   0, 255)
LIGHTPINK = (255,   102, 255)
RED         = (155,   0,   0)
LIGHTRED    = (175,  20,  20)
GREEN       = (  0, 155,   0)
LIGHTGREEN  = ( 20, 175,  20)
BLUE        = (  0,   0, 155)
LIGHTBLUE   = ( 20,  20, 175)
YELLOW      = (155, 155,   0)
LIGHTYELLOW = (175, 175,  20)

BORDERCOLOR = BLUE
BGCOLOR = BLACK
TEXTCOLOR = WHITE
TEXTSHADOWCOLOR = GRAY
COLORS      = (BLUE,GREEN,RED,YELLOW,PURPLE,ORANGE,PINK)
LIGHTCOLORS = (LIGHTBLUE, LIGHTGREEN, LIGHTRED, LIGHTYELLOW,LIGHTPURPLE,LIGHTORANGE,LIGHTPINK)
assert len(COLORS) == len(LIGHTCOLORS) # each color must have light color

TEMPLATEWIDTH = 5
TEMPLATEHEIGHT = 5

S_SHAPE_TEMPLATE = [['.....',
                     '.....',
                     '..OO.',
                     '.OO..',
                     '.....'],
                    ['.....',
                     '..O..',
                     '..OO.',
                     '...O.',
                     '.....']]

Z_SHAPE_TEMPLATE = [['.....',
                     '.....',
                     '.OO..',
                     '..OO.',
                     '.....'],
                    ['.....',
                     '..O..',
                     '.OO..',
                     '.O...',
                     '.....']]

I_SHAPE_TEMPLATE = [['..O..',
                     '..O..',
                     '..O..',
                     '..O..',
                     '.....'],
                    ['.....',
                     '.....',
                     'OOOO.',
                     '.....',
                     '.....']]

O_SHAPE_TEMPLATE = [['.....',
                     '.....',
                     '.OO..',
                     '.OO..',
                     '.....']]

J_SHAPE_TEMPLATE = [['.....',
                     '.O...',
                     '.OOO.',
                     '.....',
                     '.....'],
                    ['.....',
                     '..OO.',
                     '..O..',
                     '..O..',
                     '.....'],
                    ['.....',
                     '.....',
                     '.OOO.',
                     '...O.',
                     '.....'],
                    ['.....',
                     '..O..',
                     '..O..',
                     '.OO..',
                     '.....']]

L_SHAPE_TEMPLATE = [['.....',
                     '...O.',
                     '.OOO.',
                     '.....',
                     '.....'],
                    ['.....',
                     '..O..',
                     '..O..',
                     '..OO.',
                     '.....'],
                    ['.....',
                     '.....',
                     '.OOO.',
                     '.O...',
                     '.....'],
                    ['.....',
                     '.OO..',
                     '..O..',
                     '..O..',
                     '.....']]

T_SHAPE_TEMPLATE = [['.....',
                     '..O..',
                     '.OOO.',
                     '.....',
                     '.....'],
                    ['.....',
                     '..O..',
                     '..OO.',
                     '..O..',
                     '.....'],
                    ['.....',
                     '.....',
                     '.OOO.',
                     '..O..',
                     '.....'],
                    ['.....',
                     '..O..',
                     '.OO..',
                     '..O..',
                     '.....']]

PIECES = {'S': S_SHAPE_TEMPLATE,
          'Z': Z_SHAPE_TEMPLATE,
          'J': J_SHAPE_TEMPLATE,
          'L': L_SHAPE_TEMPLATE,
          'I': I_SHAPE_TEMPLATE,
          'O': O_SHAPE_TEMPLATE,
          'T': T_SHAPE_TEMPLATE}


def main(hj_generator,samp,DW_PARAMS,constraints_check,coor_func):
    global FPSCLOCK, DISPLAYSURF, BASICFONT, BIGFONT,couplers,qbits,embedding
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    BASICFONT = pygame.font.Font('freesansbold.ttf', 18)
    BIGFONT = pygame.font.Font('freesansbold.ttf', 100)
    pygame.display.set_caption('Tetromino')
    couplers = samp.properties['couplers']
    qbits = samp.properties['qubits']
    embedding = {f'{x}_{y}':[] for x in range(BOARDWIDTH) for y in range(BOARDHEIGHT)}
    for i,var in enumerate(embedding):
        embedding.update({var:[x for x in range(i*8,i*8+8) if x in qbits]})
    sampler =FixedEmbeddingComposite(samp,embedding)
    generate_h_J = hj_generator
    showTextScreen('Tetromino')
    while True: # game loop
#         if random.randint(0, 1) == 0:
#             pygame.mixer.music.load('tetrisb.mid')
#         else:
#             pygame.mixer.music.load('tetrisc.mid')
#         pygame.mixer.music.play(-1, 0.0)

        runGame(generate_h_J,sampler,DW_PARAMS,constraints_check,coor_func)
        #pygame.mixer.music.stop()
        showTextScreen('Game Over')

def runGame(generate_h_J,sampler,DW_PARAMS,check_constraints,coord_to_x_rot):
    # setup variables for the start of the game
    board = getBlankBoard()
    
    lastMoveDownTime = time.time()
    lastMoveSidewaysTime = time.time()
    lastFallTime = time.time()
    movingDown = False # note: there is no movingUp variable
    movingLeft = False
    movingRight = False
    score = 0
    level, fallFreq = calculateLevelAndFallFreq(score)
    
    
    fallingPiece = random.choice([{'shape': 'J', 'rotation': 0, 'x': 3, 'y': -2, 'color': 1},
                  {'shape': 'L', 'rotation': 0, 'x': 3, 'y': -2, 'color': 5},
                  {'shape': 'T', 'rotation': 0, 'x': 3, 'y': -2, 'color': 3}])

    nextPiece = getNewPiece()
    move=(-4,-1)
    
    while True: # game loop
        event_count = 0
        beta_val =2.1
        if fallingPiece == None:
            # No falling piece in play, so start a new piece at the top
            fallingPiece = nextPiece
            nextPiece = getNewPiece()
            lastFallTime = time.time() # reset lastFallTime
            if not isValidPosition(board, fallingPiece):
                return # can't fit a new piece on the board, so game over
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


                tries = 0 if not holes else 100
                while no_valid and tries < 100:
                    results = sampler.sample_ising(h,J,beta=beta_val,**DW_PARAMS)
                    valid_sample = check_constraints(results,board,fallingPiece,h,static)
                    tries+=1
                    if valid_sample is not False:
                        no_valid = False
                    else:

                        beta_val += random.gauss(0,0.4)

                beta_val =2.1
                while no_valid:
                    results = sampler.sample_ising(h,J,beta=beta_val,**DW_PARAMS)
                    valid_sample = check_constraints(results,board,fallingPiece,h,static,False)
                    if valid_sample is not False:
                        no_valid = False
                    else:
                        beta_val += random.gauss(0,0.4)

                        
                #color_filled_qmap(valid_sample,J)
                flipped = find_fliped_vars(valid_sample,{**h,**static})
                move = coord_to_x_rot(flipped,fallingPiece)
            print(nextPiece)
            print(flipped)
            print(move)
            if move[1] > 0:
                for y in range(move[1]):
                    pygame.event.post(pygame.event.Event(KEYDOWN,{'key':pygame.K_UP}))
                    pygame.event.post(pygame.event.Event(KEYUP,{'key':pygame.K_UP}))
                    event_count+=2
            elif move[1]<0:
                 for y in range(0,move[1],-1):
                    pygame.event.post(pygame.event.Event(KEYDOWN,{'key':pygame.K_q}))
                    pygame.event.post(pygame.event.Event(KEYUP,{'key':pygame.K_q}))
                    event_count+=2
            

            if move[0] > 0:
                for x in range(move[0]):
                    pygame.event.post(pygame.event.Event(KEYDOWN,{'key':pygame.K_RIGHT}))
                    pygame.event.post(pygame.event.Event(KEYUP,{'key':pygame.K_RIGHT}))
            elif move[0] < 0:
                for x in range(0,move[0],-1):
                    pygame.event.post(pygame.event.Event(KEYDOWN,{'key':pygame.K_LEFT}))
                    pygame.event.post(pygame.event.Event(KEYUP,{'key':pygame.K_LEFT}))
                    event_count+=2
            pygame.event.post(pygame.event.Event(KEYDOWN,{'key':pygame.K_SPACE}))
            pygame.event.post(pygame.event.Event(KEYUP,{'key':pygame.K_SPACE}))
            event_count+=2
        checkForQuit() 
        
        for event in pygame.event.get():
            if event.type == KEYUP:
                if (event.key == K_p):
                    # Pausing the game
                    DISPLAYSURF.fill(BGCOLOR)
                   # pygame.mixer.music.stop()
                    showTextScreen('Paused') # pause until a key press
                  #  pygame.mixer.music.play(-1, 0.0)
                    lastFallTime = time.time()
                    lastMoveDownTime = time.time()
                    lastMoveSidewaysTime = time.time()
                elif (event.key == K_LEFT or event.key == K_a):
                    movingLeft = False
                elif (event.key == K_RIGHT or event.key == K_d):
                    movingRight = False
                elif (event.key == K_DOWN or event.key == K_s):
                    movingDown = False

            elif event.type == KEYDOWN:
                # moving the piece sideways
                if (event.key == K_LEFT or event.key == K_a) and isValidPosition(board, fallingPiece, adjX=-1):
                    fallingPiece['x'] -= 1
                    movingLeft = True
                    movingRight = False
                    lastMoveSidewaysTime = time.time()

                elif (event.key == K_RIGHT or event.key == K_d) and isValidPosition(board, fallingPiece, adjX=1):
                    fallingPiece['x'] += 1
                    movingRight = True
                    movingLeft = False
                    lastMoveSidewaysTime = time.time()

                # rotating the piece (if there is room to rotate)
                elif (event.key == K_UP or event.key == K_w):
                    fallingPiece['rotation'] = (fallingPiece['rotation'] + 1) % len(PIECES[fallingPiece['shape']])
                    if not isValidPosition(board, fallingPiece):
                        fallingPiece['rotation'] = (fallingPiece['rotation'] - 1) % len(PIECES[fallingPiece['shape']])
                elif (event.key == K_q): # rotate the other direction
                    fallingPiece['rotation'] = (fallingPiece['rotation'] - 1) % len(PIECES[fallingPiece['shape']])
                    if not isValidPosition(board, fallingPiece):
                        fallingPiece['rotation'] = (fallingPiece['rotation'] + 1) % len(PIECES[fallingPiece['shape']])

                # making the piece fall faster with the down key
                elif (event.key == K_DOWN or event.key == K_s):
                    movingDown = True
                    if isValidPosition(board, fallingPiece, adjY=1):
                        fallingPiece['y'] += 1
                    lastMoveDownTime = time.time()

                # move the current piece all the way down
                elif event.key == K_SPACE:
                    movingDown = False
                    movingLeft = False
                    movingRight = False
                    for i in range(1, BOARDHEIGHT):
                        if not isValidPosition(board, fallingPiece, adjY=i):
                            break
                    fallingPiece['y'] += i - 1

        #handle moving the piece because of user input
        if (movingLeft or movingRight) and time.time() - lastMoveSidewaysTime > MOVESIDEWAYSFREQ:
            if movingLeft and isValidPosition(board, fallingPiece, adjX=-1):
                fallingPiece['x'] -= 1
            elif movingRight and isValidPosition(board, fallingPiece, adjX=1):
                fallingPiece['x'] += 1
            lastMoveSidewaysTime = time.time()

        if movingDown and time.time() - lastMoveDownTime > MOVEDOWNFREQ and isValidPosition(board, fallingPiece, adjY=1):
            fallingPiece['y'] += 1
            lastMoveDownTime = time.time()

        # let the piece fall if it is time to fall
        if time.time() - lastFallTime > fallFreq:
            # see if the piece has landed
            if not isValidPosition(board, fallingPiece, adjY=1):
                # falling piece has landed, set it on the board
                addToBoard(board, fallingPiece)
                score += removeCompleteLines(board)
                level, fallFreq = calculateLevelAndFallFreq(score)
                fallingPiece = None
            else:
                # piece did not land, just move the piece down
                fallingPiece['y'] += 1
                lastFallTime = time.time()

        # drawing everything on the screen
        DISPLAYSURF.fill(BGCOLOR)
        drawBoard(board)
        drawStatus(score, level)
        drawNextPiece(nextPiece)
        if fallingPiece != None:
            drawPiece(fallingPiece)

        pygame.display.update()
        FPSCLOCK.tick(FPS)


def makeTextObjs(text, font, color):
    surf = font.render(text, True, color)
    return surf, surf.get_rect()


def terminate():
    pygame.quit()
    sys.exit()


def checkForKeyPress():
    # Go through event queue looking for a KEYUP event.
    # Grab KEYDOWN events to remove them from the event queue.
    checkForQuit()

    for event in pygame.event.get([KEYDOWN, KEYUP]):
        if event.type == KEYDOWN:
            continue
        return event.key
    return None


def showTextScreen(text):
    # This function displays large text in the
    # center of the screen until a key is pressed.
    # Draw the text drop shadow
    titleSurf, titleRect = makeTextObjs(text, BIGFONT, TEXTSHADOWCOLOR)
    titleRect.center = (int(WINDOWWIDTH / 2), int(WINDOWHEIGHT / 2))
    DISPLAYSURF.blit(titleSurf, titleRect)

    # Draw the text
    titleSurf, titleRect = makeTextObjs(text, BIGFONT, TEXTCOLOR)
    titleRect.center = (int(WINDOWWIDTH / 2) - 3, int(WINDOWHEIGHT / 2) - 3)
    DISPLAYSURF.blit(titleSurf, titleRect)

    # Draw the additional "Press a key to play." text.
    pressKeySurf, pressKeyRect = makeTextObjs('Press a key to play.', BASICFONT, TEXTCOLOR)
    pressKeyRect.center = (int(WINDOWWIDTH / 2), int(WINDOWHEIGHT / 2) + 100)
    DISPLAYSURF.blit(pressKeySurf, pressKeyRect)

    while checkForKeyPress() == None:
        pygame.display.update()
        FPSCLOCK.tick()


def checkForQuit():
    for event in pygame.event.get(QUIT): # get all the QUIT events
        terminate() # terminate if any QUIT events are present
    for event in pygame.event.get(KEYUP): # get all the KEYUP events
        if event.key == K_ESCAPE:
            terminate() # terminate if the KEYUP event was for the Esc key
        pygame.event.post(event) # put the other KEYUP event objects back



def calculateLevelAndFallFreq(score):
    # Based on the score, return the level the player is on and
    # how many seconds pass until a falling piece falls one space.
    level = int(score / 10) + 1
    fallFreq = 0.27 - (level * 0.02)
    return level, fallFreq

def getNewPiece():
    # return a random new piece in a random rotation and color
    shape = random.choice(list(PIECES.keys()))
    newPiece = {'shape': shape,
                'rotation': 0,
                'x': int(BOARDWIDTH / 2) - int(TEMPLATEWIDTH / 2),
                'y': -2, # start it above the board (i.e. less than 0)
                'color': colours[shape]}
    return newPiece


def addToBoard(board, piece):
    # fill in the board based on piece's location, shape, and rotation
    for x in range(TEMPLATEWIDTH):
        for y in range(TEMPLATEHEIGHT):
            if PIECES[piece['shape']][piece['rotation']][y][x] != BLANK:
                board[x + piece['x']][y + piece['y']] = piece['color']


def getBlankBoard():
    # create and return a new blank board data structure
    board = []
    for i in range(BOARDWIDTH):
        board.append([BLANK] * BOARDHEIGHT)
    return board


def isOnBoard(x, y):
    return x >= 0 and x < BOARDWIDTH and y < BOARDHEIGHT


def isValidPosition(board, piece, adjX=0, adjY=0):
    # Return True if the piece is within the board and not colliding
    for x in range(TEMPLATEWIDTH):
        for y in range(TEMPLATEHEIGHT):
            isAboveBoard = y + piece['y'] + adjY < 0
            if isAboveBoard or PIECES[piece['shape']][piece['rotation']][y][x] == BLANK:
                continue
            if not isOnBoard(x + piece['x'] + adjX, y + piece['y'] + adjY):
                return False
            if board[x + piece['x'] + adjX][y + piece['y'] + adjY] != BLANK:
                return False
    return True

def isCompleteLine(board, y):
    # Return True if the line filled with boxes with no gaps.
    for x in range(BOARDWIDTH):
        if board[x][y] == BLANK:
            return False
    return True


def removeCompleteLines(board):
    # Remove any completed lines on the board, move everything above them down, and return the number of complete lines.
    numLinesRemoved = 0
    y = BOARDHEIGHT - 1 # start y at the bottom of the board
    while y >= 0:
        if isCompleteLine(board, y):
            # Remove the line and pull boxes down by one line.
            for pullDownY in range(y, 0, -1):
                for x in range(BOARDWIDTH):
                    board[x][pullDownY] = board[x][pullDownY-1]
            # Set very top line to blank.
            for x in range(BOARDWIDTH):
                board[x][0] = BLANK
            numLinesRemoved += 1
            # Note on the next iteration of the loop, y is the same.
            # This is so that if the line that was pulled down is also
            # complete, it will be removed.
        else:
            y -= 1 # move on to check next row up
    return numLinesRemoved


def convertToPixelCoords(boxx, boxy):
    # Convert the given xy coordinates of the board to xy
    # coordinates of the location on the screen.
    return (XMARGIN + (boxx * BOXSIZE)), (TOPMARGIN + (boxy * BOXSIZE))


def drawBox(boxx, boxy, color, pixelx=None, pixely=None):
    # draw a single box (each tetromino piece has four boxes)
    # at xy coordinates on the board. Or, if pixelx & pixely
    # are specified, draw to the pixel coordinates stored in
    # pixelx & pixely (this is used for the "Next" piece).
    if color == BLANK:
        return
    if pixelx == None and pixely == None:
        pixelx, pixely = convertToPixelCoords(boxx, boxy)
    pygame.draw.rect(DISPLAYSURF, COLORS[color], (pixelx + 1, pixely + 1, BOXSIZE - 1, BOXSIZE - 1))
    pygame.draw.rect(DISPLAYSURF, LIGHTCOLORS[color], (pixelx + 1, pixely + 1, BOXSIZE - 4, BOXSIZE - 4))


def drawBoard(board):
    # draw the border around the board
    pygame.draw.rect(DISPLAYSURF, BORDERCOLOR,(XMARGIN-3,TOPMARGIN-7,(BOARDWIDTH*BOXSIZE)+8,(BOARDHEIGHT*BOXSIZE)+8),5)

    # fill the background of the board
    pygame.draw.rect(DISPLAYSURF, BGCOLOR, (XMARGIN, TOPMARGIN, BOXSIZE * BOARDWIDTH, BOXSIZE * BOARDHEIGHT))
    # draw the individual boxes on the board
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            drawBox(x, y, board[x][y])


def drawStatus(score, level):
    # draw the score text
    scoreSurf = BASICFONT.render('Score: %s' % score, True, TEXTCOLOR)
    scoreRect = scoreSurf.get_rect()
    scoreRect.topleft = (WINDOWWIDTH - 150, 20)
    DISPLAYSURF.blit(scoreSurf, scoreRect)

    # draw the level text
    levelSurf = BASICFONT.render('Level: %s' % level, True, TEXTCOLOR)
    levelRect = levelSurf.get_rect()
    levelRect.topleft = (WINDOWWIDTH - 150, 50)
    DISPLAYSURF.blit(levelSurf, levelRect)


def drawPiece(piece, pixelx=None, pixely=None):
    shapeToDraw = PIECES[piece['shape']][piece['rotation']]
    if pixelx == None and pixely == None:
        # if pixelx & pixely hasn't been specified, use the location stored in the piece data structure
        pixelx, pixely = convertToPixelCoords(piece['x'], piece['y'])

    # draw each of the boxes that make up the piece
    for x in range(TEMPLATEWIDTH):
        for y in range(TEMPLATEHEIGHT):
            if shapeToDraw[y][x] != BLANK:
                drawBox(None, None, piece['color'], pixelx + (x * BOXSIZE), pixely + (y * BOXSIZE))


def drawNextPiece(piece):
    # draw the "next" text
    nextSurf = BASICFONT.render('Next:', True, TEXTCOLOR)
    nextRect = nextSurf.get_rect()
    nextRect.topleft = (WINDOWWIDTH - 120, 80)
    DISPLAYSURF.blit(nextSurf, nextRect)
    # draw the "next" piece
    drawPiece(piece, pixelx=WINDOWWIDTH-120, pixely=100)
    
def num_empty(board):# counts number of empty on board
    count =0
    for x in board:
        for y in x:
            if y=='.':
                count+=1
    return count

def num_full(board):# counts number of full on board
    count =0
    for x in board:
        for y in x:
            if isinstance(y,int):
                count+=1
    return count

def has_holes(board):
    for x in range(BOARDWIDTH):
        block_at = False
        for i,y in enumerate(range(BOARDHEIGHT)):
            if isinstance(board[x][y],int):
                block_at = True
            elif block_at and isinstance(board[x][y],str):
                return True
    return False

def is_lowest_sample(sample): # Checks if there are any holes created in peice placement
    col_truths=[]
    for x in range(BOARDWIDTH):
        col = {x:sample[x] for x in sorted({samp for samp in sample if samp.split('_')[0]==str(x)},key=lambda x: int(x.split('_')[-1]))}
        truth_str = '<='.join(list(map(str,col.values()))) 
        col_truths.append(eval(truth_str))
    return all(col_truths)
        
def find_fliped_vars(sample,h): # Returns the flipped variables from the original h and the samples returned
    flipped = []
    for k,value in sample.items():
        if value ==-1 and h[k]==-1:
            continue
        elif value ==-1 and h[k]!=-1:
            flipped.append(k)
    return flipped
            
def is_shape_sample(sample,board,piece,flip):# checks if a valid shape is placed on board
    shape=piece['shape']
    board_ =board#[ro[::-1] for ro in board]
    valid = shape_to_valid_coord_set(eval(shape+'_SHAPE_TEMPLATE'))
   # max_height = max([j for i,val in enumerate(board_) for j,x in enumerate(val) if isinstance(x,int)])+4
   # board_ = [ro[:max_height] for ro in board_]
    max_heightv = max([v[1] for x in valid for v in x])
    max_width = max([v[0] for x in valid for v in x])
    coord_4_combos = [['_'.join([str(coord[0]+x-1),str(coord[1]+y-1)])for coord in val]
                      for val in valid  for y in range(BOARDHEIGHT-max_heightv)
                      for x in range(BOARDWIDTH-max_width) if not isinstance(board_[x][-y],int)]
    is_valid = False
    flipped = flip
    if len(flipped) ==4:
        var_to_grid = [tuple(map(int,var.split('_'))) for var in flipped]
        var_min_X = min([s[0] for s in var_to_grid])
        var_min_Y = min([s[1] for s in var_to_grid])
    var_patternx = [s[0]-var_min_X for s in var_to_grid]
    var_patterny = [s[1]-var_min_Y for s in var_to_grid]#[::-1]
     
    for comb in coord_4_combos:
        comb_to_grid = [tuple(map(int,var.split('_'))) for var in comb]
        min_X = min([s[0] for s in comb_to_grid])
        min_Y = min([s[1] for s in comb_to_grid])
        patternx = [s[0]-min_X for s in comb_to_grid]
        patterny = [s[1]-min_Y for s in comb_to_grid]
        if patternx==var_patternx and patterny==var_patterny:
            is_valid = True
            break    
    return is_valid

def color_filled_qmap(uembedd,J):# generates a networkx graph of the problem grid
    G = nx.Graph()
    G.add_nodes_from(uembedd)
    G.add_weighted_edges_from([(k[0],k[1],v) for k,v in J.items()])
    plt.figure(figsize=(30,30))
    pos={}
    [pos.update(x) for x in list(map(lambda x:{x:tuple(eval(x.replace('_',',')))},uembedd.keys()))]
    edge_cols = [w[2]['weight'] for w in G.edges(data=True)]
    col_map = {-1:'blue',1:'red'}
    return nx.draw_networkx(G,node_color=[col_map[x] for x in uembedd.values()],pos=pos,edge_color=edge_cols)

def shape_to_valid_coord_set(shape_format):# takes the format of a shape and converts it to coordinates
    data = shape_format
    valid_coords = []
    for dat in data:
        coords = []
        for i,x in enumerate(dat):
            for j,y in enumerate(x):
                if y is 'O':
                    coords.append((i,j))
        valid_coords.append(coords)
    return(valid_coords)

def valid_coord_to_cobo(valid_coord,board):# takes valid coordinates and returns the combinations of empty spaces
    board_ = board#[ro [::-1]for ro in board]
    max_height = 19-min([j for i,val in enumerate(board_) for j,x in enumerate(val) if isinstance(x,int)])+4  
    board_ = [ro[max_height:] for ro in board_]
    max_heightv = max([v[1] for x in valid_coord for v in x])
    max_width = max([v[0] for x in valid_coord for v in x])
    coord_4_combos = [['_'.join([str(coord[0]+x),str(coord[1]+y)])for coord in val]
                      for val in valid_coord  for y in range(BOARDHEIGHT-(max_heightv+max_height+1))
                      for x in range(BOARDWIDTH-(max_width+1)) if not isinstance(board_[x][-y],int)]
    return coord_4_combos    
