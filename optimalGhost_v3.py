#!/usr/bin/env python

__author__ = 'Alex Chung'
__email__ = 'achung@ischool.berkeley.edu'
__python_version__="2.7"

"""
Game Rules:
In the game of Ghost, two players take turns building up an English word from left to right. 
Each player adds one letter per turn. The goal is to not complete the spelling of a word: 
	if you add a letter that completes a word (of 4+ letters), 
	or if you add a letter that produces a string that cannot be extended into a word, you lose. 
	(Bluffing plays and "challenges" may be ignored for the purpose of this puzzle.) 
	
Program Description:
Write a program that allows a user to play Ghost against the computer. 

The computer should play optimally given the following dictionary: WORD.LST (1.66 MB). 
Allow the human to play first. If the computer thinks it will win, 
it should play randomly among all its winning moves; if the computer thinks it will lose, 
it should play so as to extend the game as long as possible 
(choosing randomly among choices that force the maximal game length).

Notes:
1) String length ONLY increments
2) English word ONLY [a-z]
3) Case insensitive (all lower)
4) It's okay to form a word that has less than 4 letters
5) Does the computer evaluate its chance after every human move or just the first one?
6) I'm assuming that the description means: 
	if there is a tie of multiple moves that extend the game at the same maximal length,
	the computer will choose among them.  

7) B-Tree.  Each letter will be a single node
8) remember that the CPU next moves will skip turns
9) If the computer is uncertain of winning or losing, it will choose the letter that has 
	a higher chance of leading to a win
"""

import os
import re #Regular Expression
import random #Random number
from collections import deque  #Queue

#STEP 1: Define B-Tree that will hold the words list
#Assume the words list contains only English words and there are no 
#other characters besides a-z
class BTree(object):
	def __init__(self, name='', value=-1, children=None, isWord=False):
		self.name = name #Hold the letter value
		self.value = value #Hold the level within the tree
		self.isWord = isWord  #Mark if this node is the end of a word
		if children:
			for c in children:
				self.addChild(c)
		else:
			self.children = list()
			
	def addChild(self, child):
		self.children.append(child)
		
	def findSubTree(self, name):
		if self is None:
			return False
		if not self.children:
			return False
		for c in self.children:
			if c.name == name:
				return c
		return False
		
	def dfawsHelper(self, foundWords):
		if self is None:
			return False
		if self.isWord and self.value > 3:
			foundWords.append(self)
		else:	
			for c in self.children:
				c.dfawsHelper(foundWords)
		
	def depthFirstAllWordsSearch(self):
		foundWords = list()
		
		if self is None:
			return False
		if self.isWord and self.value > 3:
			foundWords.append(self)
		else:
			for c in self.children:
				 c.dfawsHelper(foundWords)
			
		if foundWords:
			return foundWords
		else:
			return False

#STEP 2: Get WordList File then Parse Words List
#Assume data file in same directory as the python source file
#this is an easy way to get the right path name for the data file
def getLocalPathFromThisSourceFile(fname):
	curpath = os.path.abspath(fname)
	words_file = os.path.dirname(curpath)
	words_file = os.path.join(words_file, fname)
	return words_file
	
#Load and parse a words list
def parseInputFile(fname):
	words = list()
	try:
		input_file = getLocalPathFromThisSourceFile(fname)
		#Read in the words list
		fin = open(input_file, 'r')
		for line in fin:
			line = line.strip()
			#turn all strings to lowercase characters
			line.lower() 
			words.append(line)
		fin.close()
		
		return words
	except Exception as ex:
		print ("error opening file %s", ex)
		return

#STEP 3: Build a tree from the words list
def buildABTree(words):
	root = BTree("root", 0)
	if words:
		for word in words:
			#print word
			currentNode = root
			for i, char in enumerate(word):
				foundNode = currentNode.findSubTree(char)
				if foundNode:
					#there is an existing node, reuse
					currentNode = foundNode
				else:
					#create new node
					newNode = BTree(char, i + 1)
					currentNode.addChild(newNode)
					#the new node is now the current node
					currentNode = newNode
			#mark current character as the end of a read word
			currentNode.isWord = True  		
		return root
	else:
		return

singleLetterPattern = re.compile('^[a-z]$')

#STEP4: Define the Ghost Game Logic
class GhostGame(object):
	winner = None
	finalWord = None
	currString = ''
	
	def __init__(self, id=None, numHumanPlayers=None, currentNode=None):
		self.numHumanPlayers = numHumanPlayers
		self.currentNode = currentNode
	
	def promptHumanInput(self, i):
		#Error Checking on human inputs
		validInput = False
		user_input = None
		while (not validInput):
			user_input = raw_input('Player' + str(i) + '\'s turn: Please enter an English letter (a-z):')
			user_input = user_input.strip().lower()
			if len(user_input) > 1:
				print "Please enter only a single letter.  Try again."
				continue
			elif not re.match(singleLetterPattern, user_input):
				print "Please enter a letter from a -z only. Try again."
				continue
		 	else:
				validInput = True
		return user_input
		
	def WordExtensionCheck(self):
		if self.currentNode.children:
			return True
		else:
			return False	
	
	def ComputerMoveDecision(self):
		#Find all the nodes that are end of words but with more than 3 letters
		#Find a node that leads to all paths with an even number of remaining rounds from the current round
		#Choose path base on the following rules:
		#1. hasEven = True and hasOdd = False => certain win
		#2. hasEven = True and hasOdd = True  => 50/50
		#3. hasEven = False and hasOdd = True => certain lose, pick the path with the highest remaining round
		
		winningMoves = list()
		neutralMoves = list()
		losingMoves = list()
		lastMove = None
		nextMove = None
		
		#Peak at all the letter choices
		for c in self.currentNode.children:
			#Find the word stops from each of the possible letter choice
			allFoundWords = c.depthFirstAllWordsSearch()
		
			hasEvenRemainRound = 0
			hasOddRemainRound = 0
			#Calculate the number of rounds between the computer move and the next closest word stops
			#Computer is looking for even number of rounds so that it will not make the last move
			try:
				if allFoundWords:
					for w in allFoundWords:
						remainRound = w.value - c.value + 1
						if remainRound % (self.numHumanPlayers + 1) == 0:  #consider the total num of players + comp
							hasEvenRemainRound += 1
						else:
							hasOddRemainRound += 1
				
					if hasEvenRemainRound > 0 and hasOddRemainRound == 0:
						#certain win
						winningMoves.append(c)
					elif hasEvenRemainRound > 0 and hasOddRemainRound > 0:
						#50/50. Uncertain
						#Pick one path with the highest number of even remaning rounds
						#If there is a tie, randomly pick one
						neutralMoves.append((c, hasEvenRemainRound, hasOddRemainRound))
					elif hasEvenRemainRound == 0 and hasOddRemainRound > 0:
						#certain lose
						losingMoves.append(c)
					else:
						#no more move with this choice
						lastMove = c
				else:
					pass
			except:
				pass
		
		if len(winningMoves) > 0:
			nextMove = random.choice(winningMoves)
			#print "winning move: " + nextMove.name
		elif len(neutralMoves) > 0:
			maxChanceMove = None
			maxChancePercent = None
			for p in neutralMoves:
				#Calculate the percent of even number paths out of total
				pPercentOfEvenNum = float(p[1])/float(p[1] + p[2])
				
				if maxChanceMove is None:
					maxChanceMove = p
					maxChancePercent = pPercentOfEvenNum
				elif maxChancePercent < pPercentOfEvenNum:  #Compare the percentage of even number paths out of total
					maxChanceMove = p
					maxChancePercent = pPercentOfEvenNum
			nextMove = maxChanceMove[0]
		elif len(losingMoves) > 0:
			maxExtensionMove = None
			for c in losingMoves:
				if maxExtensionMove is None:
					maxExtensionMove = c
				elif maxExtensionMove.value < c.value:  #Compare and look for the longest word
					maxExtensionMove = c
			nextMove = maxExtensionMove
		else:
			nextMove = lastMove
		
		return nextMove
		
	def GameCheck(self, user_input, playerName):
		self.currString += user_input  #update the current displayed string
		
		treeNode = self.currentNode.findSubTree(user_input) #Find the node based the new user_input 
		if treeNode:
			self.currentNode = treeNode 
			
			#Check if the player has created a word
			if treeNode.isWord and len(self.currString) > 3:  #word has to have 4 or more letters
				#Yes
				self.finalWord = self.currString
				self.winner = playerName
				print playerName + " loses.  A Word has been completed: " + self.finalWord + '.'
				return True
			else:
				#No
				pass
			
			#Check if the word can be extend
			if self.WordExtensionCheck():
				#Yes
				pass
			else:
				#No
				print "Oops. " + playerName + " have entered a string that cannot be extended."
				self.finalWord = self.currString
				self.winner = playerName
				return True
				
			return False
		else:
			#not found.  User has entered an invalid word
			print "Sorry " + playerName + ".  You have entered an invalid string that cannot be extended to a word."
			self.finalWord = self.currString
			self.winner = playerName
			return True
		
	def playGame(self):
		#Display Game Instroduction
		print "WELCOME TO PLAY THE GAME OF GHOST"
		print ""
		print "Game Rules:"
		print "In the game of Ghost, two players take turns building up an English word from left to right." 
		print "Each player adds one letter per turn. The goal is to not complete the spelling of a word:" 
		print "if you add a letter that completes a word (of 4+ letters)," 
		print "or if you add a letter that produces a string that cannot be extended into a word, you lose."
		print ""
		
		currString = ''
		while (self.finalWord is None and self.winner is None):
			if len(self.currString) > 0:
				print "Game progress: " + self.currString  #what has been entered so far
			
			#Human Players
			for i in range(1, self.numHumanPlayers + 1):  #support multiple human players
				if self.winner is None:
					user_input = self.promptHumanInput(i)
								
					if self.GameCheck(user_input, 'Player' + str(i)):
						break
					
			#Computer Player
			if self.winner is None:
				#Calculate the next move
				nextMove = self.ComputerMoveDecision()
				if nextMove is None:
					#There is no next move for the computer.  Thus the human player loses
					print "Oops. You have entered a string that cannot be extended."
					self.finalWord = self.currString
					self.winner = 'Computer'
					break
				else:
					print 'Computer' + '\'s turn: ' + nextMove.name 
					if self.GameCheck(nextMove.name, 'Computer'):
						break
			
#STEP5: Execute Program
def main():
	#Load the words list into memory
	words = parseInputFile('WORD.LST')
	root = buildABTree(words)
	
	#Start A Game Instance
	game = GhostGame(1, 1, root)
	game.playGame()
	
if __name__ == '__main__':
	main()
	
	
################################
#Sample Outputs:
#
#
################################
"""
WELCOME TO PLAY THE GAME OF GHOST

Game Rules:
In the game of Ghost, two players take turns building up an English word from left to right.
Each player adds one letter per turn. The goal is to not complete the spelling of a word:
if you add a letter that completes a word (of 4+ letters),
or if you add a letter that produces a string that cannot be extended into a word, you lose.

Player1's turn: Please enter an English letter (a-z):b
Computer's turn: w
Game progress: bw
Player1's turn: Please enter an English letter (a-z):a
Computer's turn: n
Game progress: bwan
Player1's turn: Please enter an English letter (a-z):e
Sorry Player1.  You have entered an invalid string that cannot be extended to a word.
"""





