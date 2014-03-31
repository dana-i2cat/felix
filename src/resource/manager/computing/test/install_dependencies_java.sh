#!/bin/sh

java_library_path=/usr/share/java

if [ ! -f $java_library_path/junit-4.11.jar ]; then
  sudo apt-get install junit
  wget http://search.maven.org/remotecontent?filepath=junit/junit/4.11/junit-4.11.jar -O $java_library_path/junit-4.11.jar
fi

if [ ! -f $java_library_path/hamcrest-core-1.3.jar ]; then
  sudo apt-get install libhamcrest-java
  wget http://search.maven.org/remotecontent?filepath=org/hamcrest/hamcrest-core/1.3/hamcrest-core-1.3.jar -O $java_library_path/hamcrest-core-1.3.jar
fi
