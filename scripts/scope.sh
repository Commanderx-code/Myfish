#!/usr/bin/env bash
set -o noclobber -o noglob -o pipefail
IFS=$'\n'

FILE_PATH="$1"
PV_WIDTH="$2"
PV_HEIGHT="$3"
CACHE_PATH="$4"
IMAGE_CACHE="$CACHE_PATH.preview.jpg"

handle_exit() {
    rm -f "$IMAGE_CACHE"
}
trap handle_exit EXIT

mimetype=$(file --mime-type -Lb "$FILE_PATH")

# -----------------------------
# IMAGE PREVIEW (ueberzug)
# -----------------------------
case "$mimetype" in
    image/*)
        convert "$FILE_PATH" -thumbnail "${PV_WIDTH}x${PV_HEIGHT}>" "$IMAGE_CACHE" 2>/dev/null
        ueberzug layer --parser bash --silent <<EOF
add [identifier]="preview" [x]=0 [y]=0 [width]=$PV_WIDTH [height]=$PV_HEIGHT [path]="$IMAGE_CACHE"
EOF
        exit 0
        ;;
esac

# -----------------------------
# VIDEO PREVIEW (thumbnail)
# -----------------------------
case "$mimetype" in
    video/*)
        ffmpegthumbnailer -i "$FILE_PATH" -o "$IMAGE_CACHE" -s 512
        ueberzug layer --parser bash --silent <<EOF
add [identifier]="preview" [x]=0 [y]=0 [width]=$PV_WIDTH [height]=$PV_HEIGHT [path]="$IMAGE_CACHE"
EOF
        exit 0
        ;;
esac

# -----------------------------
# PDF PREVIEW
# -----------------------------
case "$mimetype" in
    application/pdf)
        pdftoppm -f 1 -l 1 "$FILE_PATH" "$CACHE_PATH/pdf"
        convert "$CACHE_PATH/pdf-1.ppm" "$IMAGE_CACHE"
        ueberzug layer --parser bash --silent <<EOF
add [identifier]="preview" [x]=0 [y]=0 [width]=$PV_WIDTH [height]=$PV_HEIGHT [path]="$IMAGE_CACHE"
EOF
        exit 0
        ;;
esac

# -----------------------------
# AUDIO PREVIEW (metadata)
# -----------------------------
case "$mimetype" in
    audio/*)
        mediainfo "$FILE_PATH"
        exit 0
        ;;
esac

# -----------------------------
# ARCHIVE PREVIEW
# -----------------------------
case "$FILE_PATH" in
    *.zip|*.tar|*.tar.gz|*.tgz|*.rar|*.7z)
        atool --list "$FILE_PATH"
        exit 0
        ;;
esac

# -----------------------------
# TEXT + CODE PREVIEW (syntax)
# -----------------------------
case "$mimetype" in
    text/*)
        highlight -O ansi "$FILE_PATH" || cat "$FILE_PATH"
        exit 0
        ;;
esac

# -----------------------------
# FALLBACK
# -----------------------------
file "$FILE_PATH"
exit 0

