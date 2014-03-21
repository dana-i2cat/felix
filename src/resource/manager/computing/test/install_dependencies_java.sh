#!/bin/sh

sudo apt-get install junit
wget http://search.maven.org/remotecontent?filepath=junit/junit/4.11/junit-4.11.jar -O /usr/share/java/junit-4.11.jar
sudo apt-get install libhamcrest-java
wget http://search.maven.org/remotecontent?filepath=org/hamcrest/hamcrest-core/1.3/hamcrest-core-1.3.jar -O /usr/share/java/hamcrest-core-1.3.jar
