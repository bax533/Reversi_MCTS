import math
import random
import time
import copy

INFINITY = 10000000

ME = 0
ENEMY = 1

width = 8
height = 8

directions = [(-1,0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]

def InsideBoard(pos):
	if(pos[0] >= 0 and pos[1] >= 0 and pos[0] < width and pos[1] < height):
		return True
	else:
		return False

def GetFromMove(mov):
	for i in range(8):
		if(directions[i] == mov):
			return directions[(i+4)%8]

class State: #0 - me, 1 - enemy

	enemyPawns = set()
	myPawns = set()
	actionMoves = set()

	def __init__(self, myPawns, enemyPawns, playerNr):
		self.myPawns = myPawns
		self.enemyPawns = enemyPawns
		self.player = playerNr
		self.actionMoves = self.actions()

	def actions(self):
		retPos = set()
		if(self.player == ME):
			for pawn in self.enemyPawns:
				for mov in directions:
					newPos = (pawn[0] + mov[0], pawn[1] + mov[1])
					if(InsideBoard(newPos) and newPos not in self.enemyPawns and newPos not in self.myPawns):
						if(self.CheckLine(pawn, GetFromMove(mov), self.player)):
							retPos.add(newPos)
		else:
			for pawn in self.myPawns:
				for mov in directions:
					newPos = (pawn[0] + mov[0], pawn[1] + mov[1])
					if(InsideBoard(newPos) and newPos not in self.enemyPawns and newPos not in self.myPawns):
						if(self.CheckLine(pawn, GetFromMove(mov), self.player)):
							retPos.add(newPos)
		return retPos


	def CheckLine(self, startPos, direction, player):
		currentPos = startPos

		if(player == ME):
			while(InsideBoard(currentPos) and currentPos in self.enemyPawns):
				currentPos = (currentPos[0] + direction[0], currentPos[1] + direction[1])

			if(InsideBoard(currentPos) and currentPos in self.myPawns):
				return True
			else:
				return False
		else:
			while(InsideBoard(currentPos) and currentPos in self.myPawns):
				currentPos = (currentPos[0] + direction[0], currentPos[1] + direction[1])

			if(InsideBoard(currentPos) and currentPos in self.enemyPawns):
				return True
			else:
				return False


	def GetFromLine(self, startPos, direction, player):
		retPositions = set()

		currentPos = startPos

		if(player == ME):
			while(InsideBoard(currentPos) and currentPos in self.enemyPawns):
				retPositions.add(currentPos)
				currentPos = (currentPos[0] + direction[0], currentPos[1] + direction[1])

			return retPositions
		else:
			while(InsideBoard(currentPos) and currentPos in self.myPawns):
				retPositions.add(currentPos)
				currentPos = (currentPos[0] + direction[0], currentPos[1] + direction[1])

			return retPositions

	def MakeMove(self, placePos):
		newMyPawns = self.myPawns.copy()
		newEnemyPawns = self.enemyPawns.copy()

		if(self.player == ME):
			newMyPawns.add(placePos)
			for mov in directions:
				lineStart = (placePos[0] + mov[0], placePos[1] + mov[1])
				if(InsideBoard(lineStart) and self.CheckLine(lineStart, mov, self.player)):
					onLine = self.GetFromLine(lineStart, mov, self.player)
					for point in onLine:
						newEnemyPawns.remove(point)
						newMyPawns.add(point)
		else:
			newEnemyPawns.add(placePos)
			for mov in directions:
				lineStart = (placePos[0] + mov[0], placePos[1] + mov[1])
				if(InsideBoard(lineStart) and self.CheckLine(lineStart, mov, self.player)):
					onLine = self.GetFromLine(lineStart, mov, self.player)
					for point in onLine:
						newMyPawns.remove(point)
						newEnemyPawns.add(point)

		return State(newMyPawns, newEnemyPawns, 1-self.player)

	def PrintBoard(self):
		for y in range(height):
			row = ''
			for x in range(width):
				if((x, y) in self.myPawns):
					row += 'O'
				elif((x, y) in self.enemyPawns):
					row += '#'
				else:
					row += '.'
			print(row)
		print("----------")

	def Win(self):
		return len(self.myPawns) > len(self.enemyPawns)

	def Terminal(self):
		if (len(self.actionMoves) == 0):
			nextState = State(self.myPawns, self.enemyPawns, 1-self.player)
			if(len(nextState.actionMoves) == 0):
				return True
		return False

	def __eq__(self, o):
		return self.myPawns == o.myPawns and self.enemyPawns == o.enemyPawns

	def __hash__(self):
		return hash(frozenset(self.myPawns)) ^ hash(frozenset(self.enemyPawns))

class Node:

	def __init__(self, state, parent):
		self.visits = 0
		self.wins = 0
		self.state = state
		self.parent = parent
		self.children = set()


	def FullyExpanded(self):
		if(len(self.children) == len(self.state.actionMoves)):
			return True
		return False

	def NewChild(self):
		for a in self.state.actionMoves:
			newState = self.state.MakeMove(a)
			if(Node(newState, self) not in self.children):
				addNode = Node(newState, self)
				self.children.add(addNode)
				return addNode


	def UCB(self, t):
		c = 1.0
		return float(self.wins)/float(t) + c*math.sqrt(math.log(t)/float(self.visits))

	def GetChildUCB(self, t):
		bestVal = -1
		bestChild = self
		for child in self.children:
			childUCB = child.UCB(t)
			if(childUCB > bestVal):
				bestVal = childUCB
				bestChild = child
		return bestChild

	def __eq__(self, o):
		return self.state == o.state

	def __hash__(self):
		return hash(self.state) ^ hash(self.parent)


class MCTS:

	def __init__(self, root):
		self.root = root
		self.time = 1

	def traverse(self):
		node = self.root
		if(node.state.Terminal()):
			return node

		while(node.FullyExpanded()):
			if(len(node.state.actionMoves) == 0):
				return node
			node = node.GetChildUCB(self.time)

		return node.NewChild()

	def PlayRandomGame(self, node):
		state = copy.deepcopy(node.state)
		while(not state.Terminal()):

			if(len(state.actionMoves) == 0):
				state = State(state.myPawns, state.enemyPawns, 1-state.player)
				continue
			act = random.choice(tuple(state.actionMoves))
			state = state.MakeMove(act)
		return state.Win()

	def BackPropagate(self, node, result):
		if(node == self.root):
			return
		node.visits += 1
		if(result):
			node.wins += 1
		self.BackPropagate(node.parent, result)

	def Search(self):
		leaf = self.traverse()
		result = self.PlayRandomGame(leaf)
		self.BackPropagate(leaf, result)

	def GetGOTONode(self, timeLimit):#in seconds
		start = time.time()
		while(time.time() - start < timeLimit):
			self.Search()
			self.time += 1
			
		return self.root.GetChildUCB(self.time)

def GetMoveBetweenStates(fromState, toState):
	for a in fromState.actionMoves:
		newState = fromState.MakeMove(a)
		if(newState == toState):
			return a
myWins = 0
num_games = 100
for it in range(num_games):

	StartState = State(set([(3, 4), (4, 3)]), set([(3, 3), (4, 4)]), ME)

	curState = StartState

	#curNode =Node(curState, curState)


	#mcts = MCTS(curNode)

	while(True):
		#curState.PrintBoard()
		if(curState.Terminal()):
			break

		a = (0,0)
		if(curState.player == ENEMY):
			if(len(curState.actionMoves) == 0):
				curState.player = (curState.player + 1)%2
				continue
			a = random.choice(tuple(curState.actionMoves))
		else:
			if(len(curState.actionMoves) == 0):
				curState.player = (curState.player + 1)%2
				continue

			mcts = MCTS(Node(curState, curState))
			GOTONode = mcts.GetGOTONode(0.3)
			a = GetMoveBetweenStates(curState, GOTONode.state)

		curState = curState.MakeMove(a)
		
	if(curState.Win()):
		myWins += 1
#print(temperature)
	print(myWins, '/', it+1)
print(myWins)





		