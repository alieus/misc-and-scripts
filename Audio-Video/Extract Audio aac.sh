#!/bin/sh

# extracts aac audio from the given video files
# if something goes wrong or the audio is not encoded in aac, nothing happens
# uses avconv - https://libav.org/avconv.html
# Stathis Alip.

for i; do
  avconv -i "$i" -vn -acodec copy "${i%.*}.aac";
done

