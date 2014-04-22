#!/bin/sh

current_dir=$PWD
cd ../..

# Compiling
javac -cp .:/usr/share/java/junit-4.11.jar computing/test/ComputeCreationTest.java
javac -cp .:/usr/share/java/junit-4.11.jar computing/test/ComputeDeletionTest.java
javac -cp .:/usr/share/java/junit-4.11.jar computing/test/ComputeSuiteTest.java
javac -cp .:/usr/share/java/junit-4.11.jar computing/test/ComputeRunnerTest.java

#Running
java -cp .:/usr/share/java/junit-4.11.jar:/usr/share/java/hamcrest-core-1.3.jar computing/test/ComputeRunnerTest

cd $PWD
