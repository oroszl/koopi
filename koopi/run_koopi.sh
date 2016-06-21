#!/bin/bash
{ configurable-http-proxy --log-level debug & python3 /srv/koopi/koopi.py; } 2>&1  
