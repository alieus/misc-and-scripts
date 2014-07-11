# converts tha given audio files to wav, audio cd, format
# if something goes wrong, nothing happens
# uses avconv - https://libav.org/avconv.html
# Stathis Alip.

for i; do
  avconv -i "$i" -ar 44100 -ac 2 "${i%.*}.wav";
done

