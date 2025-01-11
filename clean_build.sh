#!/bin/bash
if [ -d "/tmp/.apt" ]; then
    echo "Cleaning up conflicting .apt directory"
    rm -rf /tmp/.apt
fi