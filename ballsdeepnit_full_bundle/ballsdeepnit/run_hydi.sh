#!/bin/bash
cd src/hydi_repl
javac -cp . *.java
java -cp . CommandREPL
