#! /usr/bin/env bash

SESSION_NAME=cs594_proj
PORT=$1

source ./env/bin/activate

if tmux has-session -t $SESSION_NAME &> /dev/null
then
    tmux attach -t $SESSION_NAME
else
    tmux new -s $SESSION_NAME -d    

    tmux set -g pane-border-status top
    tmux bind X confirm-before "kill-session -t ''"

    tmux select-pane -T 'server'
    tmux send-keys -t 0 "./server.py $PORT" C-m
    tmux split-window -h

    tmux select-pane -T 'client'
    tmux send-keys -t 1 "sleep 0.1; python3 ./client.py $PORT" C-m
    tmux split-window -h

    tmux select-pane -T 'client2'
    tmux send-keys -t 2 "sleep 0.1; python3 ./client.py $PORT" C-m

    tmux a -t $SESSION_NAME
fi
    
