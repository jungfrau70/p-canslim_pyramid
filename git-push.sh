#!/bin/bash
#cat git-ignore.sh 
#git rm -r --cached .

git add .
git commit -m "$(date +"%Y_%m_%d_%I_%M_%p")"
git push origin master

#git log
