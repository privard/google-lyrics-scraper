# Google Lyrics Scraper

SONG_TSV needs to be the path to a tab-separated file of song lyrics with 3 columns: song_id, song_title, and album_title

```
SONG_TSV="./song.tsv" OUTPUT_DIR="./lyrics" UNSCRAPPED_TSV="./unscrapped.txt" python scraper.py
```

Note: Requires selenium and the selenium chrome driver