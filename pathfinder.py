import pyglet
import math
from queue import PriorityQueue

gridsize = 25

bat=pyglet.graphics.Batch()

# Colors
BLACK = (0, 0, 0) #Empty
WHITE = (255, 255, 255) #Wall
GRAY = (128, 128, 128) #Grid Lines
RED = (255, 0 , 0) #Closed
GREEN = (0, 255, 0) #Open
ORANGE = (255, 165, 0) #Start
PURPLE = (128, 0 , 128) #End
CYAN = (64, 224, 208) #Path

class Window(pyglet.window.Window):
	lvl=None#line vector list
	qvl=None#quad vector list
	_start=None
	_end=None
	gen=None#A* generator
	def __init__(self):
		global WIDTH,HEIGHT
		super().__init__(caption='A* path finding!')
		self.maximize()
		self.map=[[0]*gridsize for i in range(gridsize)]
		#0→ nothing 
		#1→ wall
		#2→ start
		#3→ end
		#4→ path
	def on_draw(self):
		self.clear()
		todraw=[(),()]#verteces,colors
		for x,col in enumerate(self.map):
			for y,cell in enumerate(col):
				cl=None
				if cell==1:
					cl=WHITE
				elif cell==2:
					cl=ORANGE
				elif cell==3:
					cl=PURPLE
				elif cell==4:
					cl=CYAN
				if cl:
					x_,y_,_x,_y=WIDTH*x/gridsize,HEIGHT*y/gridsize,WIDTH*(x+1)/gridsize,HEIGHT*(y+1)/gridsize
					todraw[0]+=(x_,y_,_x,y_,_x,_y,x_,_y)
					todraw[1]+=cl*4
		if self.qvl:
			self.qvl.delete()
		self.qvl=bat.add(len(todraw[0])//2,pyglet.gl.GL_QUADS,None,('v2f',todraw[0]),('c3B',todraw[1]))
		bat.draw()
		pyglet.clock.tick()
	def on_mouse_press(self,x,y,btn,mods):
		x_,y_=gridsize*x//WIDTH,gridsize*y//HEIGHT
		if x_>gridsize-1:
			x_=gridsize-1
		if y_>gridsize-1:
			y_=gridsize-1
		if self.map[x_][y_]==2:
			self._start=None
			self.map[x_][y_]=0
		elif self.map[x_][y_]==3:
			self._end=None
			self.map[x_][y_]=0
		elif self.map[x_][y_]==1:
			self.map[x_][y_]=0
		elif not self._start:
			self._start=(x_,y_)
			self.map[x_][y_]=2
		elif not self._end:
			self._end=(x_,y_)
			self.map[x_][y_]=3
		else:
			self.map[x_][y_]=1
	def on_key_press(self,sym,mods):
		if sym==pyglet.window.key.SPACE and self._start and self._end:
			for col in self.map:
				for y in range(gridsize):
					if col[y]==4:
						col[y]=0
			self.gen=get_path(self._start,self._end)
			pyglet.clock.schedule_interval(self.update,1/60)
		elif sym==pyglet.window.key.ENTER and self._start and self._end:
			for col in self.map:
				for y in range(gridsize):
					if col[y]==4:
						col[y]=0
			gen=get_path(self._start,self._end)
			try:
				while True:
					next(gen)
			except StopIteration:
				pass
	def update(self,dt):
		try:
			curnode,nodes=next(self.gen)
		except StopIteration:
			pyglet.clock.unschedule(self.update)
		else:
			x,y=curnode[-2:]
			if self.map[x][y]==4:
				self.map[x][y]=0
			for node in nodes:
				x,y=node[-2:]
				if self.map[x][y]==0:
					self.map[x][y]=4

win=Window()

WIDTH,HEIGHT=win.get_size()

lvl=()

def get_dist(x,y,_x,_y):
	return math.sqrt(abs(x-_x)**2+abs(y-_y)**2)

def get_node(x,y,cost,_x,_y):
	dist=get_dist(x,y,_x,_y)
	return [dist+cost,dist,cost,x,y]

def get_path(start,end):#A* power
	nodes=[]#only nodes where there's an adjacent node that's not been looked at
	covered=[[None for y in range(gridsize)] for x in range(gridsize)]
	nodes.append(get_node(*start,0,*end))
	j=4096#number of tries before quitting
	found=False
	while j>0 and not found:
		j-=1
		print(f"Try {4096-j}/4096",end="\r")
		if nodes:
			curnode=min(nodes)#this works
		else:
			return
		dc,dist,cost,x,y=curnode
		for _x,_y in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
			if not 0<=_x<gridsize or not 0<=_y<gridsize:#if out of grid
				continue
			repl=covered[_x][_y]
			if repl:
				continue
			else:
				val=win.map[_x][_y]
				if val==1:#wall
					continue
				elif val==3:#end
					found=True
					break
				node=get_node(_x,_y,cost+1,*end)
				nodes.append(node)
				covered[_x][_y]=node
		for _x,_y in ((x+1,y+1),(x-1,y+1),(x+1,y-1),(x-1,y-1)):
			if not 0<=_x<gridsize or not 0<=_y<gridsize:#if out of grid
				continue
			repl=covered[_x][_y]
			if repl:
				continue
			else:
				val=win.map[_x][_y]
				if val==1:#wall
					continue
				elif val==3:#end
					found=True
					break
				node=get_node(_x,_y,cost+1.5,*end)
				nodes.append(node)
				covered[_x][_y]=node
		del nodes[nodes.index(curnode)]#remove node from nodes since it looked at all sourrounding nodes
		if win.gen:
			yield curnode,nodes
	if j<=0:#no path found
		print()
		return
	found=False
	path=[]
	x,y=end
	sc=gridsize
	while j>=0:
		j-=1
		print(f"path {4096-j}/4096",end="\r")
		for _x,_y in ((x+1,y),(x-1,y),(x,y+1),(x,y-1),(x+1,y+1),(x-1,y+1),(x+1,y-1),(x-1,y-1)):
			node=covered[_x][_y]
			if node:
				dc,dist,cost,_x,_y=node
				if _x==start[0] and _y==start[1]:
					for col in win.map:
						for i in range(gridsize):
							if col[i]==4:
								col[i]=0
					for x,y in path:
						win.map[x][y]=4
					print()
					return
				elif cost<sc:
					sc=cost
					x,y=node[-2:]
		path.append((x,y))
	for col in win.map:
		for i in range(gridsize):
			if col[i]==4:
				col[i]=0
	print("oof")

for col in range(gridsize+1):
	x=1+WIDTH*col/gridsize
	lvl+=(x,0,x,HEIGHT)
for row in range(gridsize+1):
	y=HEIGHT*row/gridsize
	lvl+=(0,y,WIDTH,y)

win.lvl=bat.add(4+gridsize*4,pyglet.gl.GL_LINES,None,('v2f',lvl),('c3B',GRAY*(4+gridsize*4)))
del lvl

pyglet.app.run()
