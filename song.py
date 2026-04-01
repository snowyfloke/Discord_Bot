import yt_dlp

ydl_opts = {
    'format': 'bestaudio',
    'quiet': True,
    'noplaylist': True,
}

def get_audio(query):
    if not query.startswith("http"):
        query = f"ytsearch:{query}"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)

        if 'entries' in info:
            info = info['entries'][0]
        return info['url'], info['title']