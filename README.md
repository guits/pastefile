Little daemon written with python flask for sharing any files quickly via http

Usage:


  Upload a file:
curl -F file=@<file> http://pastefile.fr

  View all uploaded files:
curl http://pastefile.fr/ls

  Get infos about one file:
curl http://pastefile.fr/<id>/infos

  Get a file:
curl -JO http://pastefile.fr/<id>
