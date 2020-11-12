Project Goal : Learn Python via a project
============
Date: 11/11/2020
Author: Neelesh Kamkolkar

Project Notes: 
==============
My goal was to simply learn Python in a bit more depth. I wanted to build this as project to incrementally learn various topics and go indepth in some areas. This was primarily an effort for me to just get a bit more familiar with Python in an End to End way. 

Using Model View Controller design pattern with Tkinter, Object Oriented syntax, Programming sockets, and designing custom protocols are the skills I picked up through this project. Its been a fun few weekends. I am relatively new to Python and I wanted a bit more in-depth understand and a broader familiarity with python so I can build tools on my own.

I built this out in multiple phases with evolving complexity of goals so I can go more in depth and learn along the way and apply the learned concepts.  

 Phase 1 : Build a stand alone TicTacToe Application for sinlge player (same person plays both sides) 
=========

The focus here was to start with the user and simply build a UI client that allowed me to play the game by myself. Here, I learnt about the Tkinter library. While QT library may have been a good one to learn, I was too cheap to pay for a license of QT to learn, so I chose Tkinter. 

 Phase 2 : Build a simple client/server to learn how to use python to implement simple sockets 
=========

Once I had a client that worked well and learnt about the GUI layout manager, Frames, Buttons etc. I wanted to make this a bit more real. I wanted to build out a multi player version which meant I needed a server. To do that, I wanted to build out a simple TCP client/server app.

 Phase 3 : Build the TicTacToe application using a client/server architecture for multiplayer support
=========

Making some minor tweaks to the UX from Phase 1, I defined a client/server communication protocol and discovered JSON as a good mechanism to serialize and deserialize commands and data between the clinet and server. 

I build out the backend server to run in a separate process where the soure of truth for the game state would reside. 

I learnt more about socketserver.TCPServer and ServerRequestHandler as a better way of implementing the backend. While I did learn and implement a side test project to learn the use of "select" to allow for complete reads/writes to sockets in co-ordination with the OS, the simple implementation for a 2 player game seem to suffice and worked well. Perhaps, if I decide to expand the backend to support N players instead of 2, this is an important implementation to bring in, so I don't end up reading sockets when they are not ready or writing to them when not ready. 

I focused first on getting the data model working with the custom protocol. The data model for TicTacToe is a simple 3x3 matrix that visually mimics the players active board of 3x3 button grid. 

 Phase 4 : Build a fully functional TicTacToe application for use by end users
=========

Once I had the model updating correctly and client server communication working well, I wanted to build out the user functionality to the level of my stand alone application, except this time using a shared server. 

I worked out the state machine for the game, the various client/server calls needed and started implementing them using the custom protocol. Once I had a fully working client/server application, I worked out bugs with state synchronization across clients, optimized performance( not updating the GUI repeatedly ), managing the state of the UI on the client side to minimize server calls. 

Phase 5: Expand backend to support similar multi-player games  (NEXT STEPS)
========
Some bugs remain that need to be fixed (eg: a player can play multiple turns, workaround: for a full game a player should wait for the game board to be updated and then play their next turn).  

I would like to see if I can build out the backend to support more than two players making it a generic backend that supports simple multi-player board games ( example, extend tictactoe backend to battle ship). Similar idea, but different game.

This was primarily an effort for me to just get a bit more familiar with Python in an End to End way. Using Model View Controller design pattern with Tkinter, Object Oriented syntax, Programming sockets, and designing custom protocols are the skills I picked up through this project. Its been a fun few weekends, but time well spent. 

Run the project:
================
To run the project yourself: 
1. Download all the files in a folder. 
2. Update Protocol.py with your own server IP
3. Open three python windows to downloaded location (assumes python 3.6+ preinstalled)
4. Type 'python Server.py' to run server. Then type 'python main.py' to run each of the clients


