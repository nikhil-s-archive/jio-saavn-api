from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import requests
import base64
import os
import re
import tempfile
from Crypto.Cipher import DES
from mutagen.mp4 import MP4, MP4Cover
from typing import Literal

app = FastAPI(title="JioSaavn Unofficial API", description="Reverse-engineered JioSaavn API Wrapper with auto-decrypted media URLs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_URL = "https://www.jiosaavn.com/api.php"
BASE_PARAMS = {
    "_format": "json",
    "_marker": "0",
    "ctx": "web6dot0",
    "api_version": "4"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
    "Referer": "https://www.jiosaavn.com/",
    "Origin": "https://www.jiosaavn.com",
    "X-Forwarded-For": "49.36.15.10",
    "Cookie": "L=english; DL=english; country=IN;"
}

# --- Decryption & URL Enrichment Utilities ---

def decrypt_audio_url_safe(encrypted_url: str) -> str | None:
    """Decrypts DES-ECB media URL safely without throwing fatal exceptions."""
    if not encrypted_url or not isinstance(encrypted_url, str):
        return None
    try:
        key = b'38346591'
        cipher = DES.new(key, DES.MODE_ECB)
        decoded_b64 = base64.b64decode(encrypted_url)
        decrypted = cipher.decrypt(decoded_b64)
        
        pad_len = decrypted[-1]
        if isinstance(pad_len, int) and 1 <= pad_len <= 8:
            return decrypted[:-pad_len].decode('utf-8')
        return decrypted.decode('utf-8', errors='ignore')
    except Exception:
        return None

def generate_qualities(decrypted_url: str) -> dict:
    """Generates direct CDN URLs for all standard bitrates."""
    if not decrypted_url:
        return {}
        
    # Match standard bitrate suffixes like _96.mp4, _160.mp4, _320.mp4 or .mp3
    match = re.search(r"_(12|48|96|160|320)\.(mp4|mp3)$", decrypted_url)
    if match:
        base = decrypted_url[:match.start()]
        ext = match.group(2)
        return {
            "12kbps": f"{base}_12.{ext}",
            "48kbps": f"{base}_48.{ext}",
            "96kbps": f"{base}_96.{ext}",
            "160kbps": f"{base}_160.{ext}",
            "320kbps": f"{base}_320.{ext}"
        }
    
    # Fallback string replacement
    return {
        "12kbps": decrypted_url.replace("_320", "_12").replace("_160", "_12").replace("_96", "_12"),
        "48kbps": decrypted_url.replace("_320", "_48").replace("_160", "_48").replace("_96", "_48"),
        "96kbps": decrypted_url.replace("_320", "_96").replace("_160", "_96"),
        "160kbps": decrypted_url.replace("_320", "_160").replace("_96", "_160"),
        "320kbps": decrypted_url.replace("_160", "_320").replace("_96", "_320")
    }

def enrich_song_dict(song: dict) -> dict:
    """Appends decrypted media URLs and quality variations directly into the song dict."""
    enc_url = song.get("encrypted_media_url")
    if enc_url:
        decrypted = decrypt_audio_url_safe(enc_url)
        song["decrypted_media_url"] = decrypted
        song["media_urls"] = generate_qualities(decrypted)
    else:
        song["decrypted_media_url"] = None
        song["media_urls"] = {}
        
    # Also add high-resolution artwork
    if "image" in song and isinstance(song["image"], str):
        song["image_highres"] = song["image"].replace("150x150", "500x500").replace("50x50", "500x500")
        
    return song

def enrich_response_recursively(data):
    """Recursively traverses the API response to find and enrich all song dictionaries."""
    if isinstance(data, dict):
        if "encrypted_media_url" in data:
            enrich_song_dict(data)
        for key in list(data.keys()):
            enrich_response_recursively(data[key])
    elif isinstance(data, list):
        for item in data:
            enrich_response_recursively(item)
    return data

def fetch_saavn_data(call: str, **kwargs) -> dict:
    """Helper function to make requests and automatically enrich song data."""
    params = BASE_PARAMS.copy()
    params["__call"] = call
    params.update(kwargs)
    
    try:
        response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        raw_json = response.json()
        
        # Injects decrypted data across all song objects in the response
        return enrich_response_recursively(raw_json)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"JioSaavn API Error: {str(e)}")


# --- API Endpoints ---

@app.get("/")
def root():
    return {"message": "JioSaavn API Wrapper with pre-decrypted media URLs is running."}

@app.get("/search/autocomplete")
def autocomplete(query: str = Query(..., description="The search term")):
    return fetch_saavn_data("autocomplete.get", query=query)

@app.get("/search/songs")
def search_songs(
    q: str = Query(..., description="Query string"), 
    n: int = Query(10, description="Limit/count number"), 
    p: int = Query(1, description="Page number (1-indexed)")
):
    return fetch_saavn_data("search.getResults", q=q, n=n, p=p)

@app.get("/song")
def get_song(pids: str = Query(..., description="Comma-separated list of song IDs")):
    return fetch_saavn_data("song.getDetails", pids=pids)

@app.get("/album")
def get_album(albumid: str = Query(..., description="Album ID")):
    return fetch_saavn_data("content.getAlbumDetails", albumid=albumid)

@app.get("/artist")
def get_artist(artistId: str = Query(..., description="Artist ID")):
    return fetch_saavn_data("artist.getArtistPageDetails", artistId=artistId)

@app.get("/playlist")
def get_playlist(listid: str = Query(..., description="Playlist ID")):
    return fetch_saavn_data("playlist.getDetails", listid=listid)

@app.get("/lyrics")
def get_lyrics(lyrics_id: str = Query(..., description="Song ID to fetch lyrics for")):
    return fetch_saavn_data("lyrics.get", lyrics_id=lyrics_id)

@app.get("/charts", tags=["Charts & Discovery"])
def get_charts(
    category: Literal["all", "trending", "new-releases", "top-artists", "top-playlists", "charts-list", "chart-details"] = Query(
        "all", 
        description="Select a specific chart, or use 'all' for a dashboard."
    ),
    chart_token: str = Query(
        "zlJfJYVuyjpxWb5,FqsjKg__", 
        description="Pass the token extracted from 'charts-list' to fetch its specific songs."
    ),
    n: int = Query(50, description="Number of items to fetch"), 
    p: int = Query(1, description="Page number")
    ):
    """Fetches JioSaavn charts and dynamically extracts playlist tokens."""
    results = {}
    
    # 1. Trending
    if category in ["all", "trending"]:
        results["trending"] = fetch_saavn_data("content.getTrending")
        
    # 2. New Releases
    if category in ["all", "new-releases"]:
        results["new_releases"] = fetch_saavn_data("content.getAlbums", n=n, p=p, ctx="wap6dot0")
        
    # 3. Top Artists
    if category in ["all", "top-artists"]:
        results["top_artists"] = fetch_saavn_data("social.getTopArtists", ctx="wap6dot0")
        
    # 4. Top Playlists
    if category in ["all", "top-playlists"]:
        results["top_playlists"] = fetch_saavn_data(
            "content.getFeaturedPlaylists", 
            fetch_from_serialized_files="true", 
            n=n, 
            p=p, 
            ctx="wap6dot0"
        )
        
    # 5. List of All Top Charts (Extracting the token from perma_url)
    if category in ["all", "charts-list"]:
        charts_raw = fetch_saavn_data("content.getCharts", ctx="wap6dot0")
        
        charts_list = []
        for chart in charts_raw:
            perma_url = chart.get("perma_url", "")
            # The token is always the final string in the URL after the last slash
            token = perma_url.strip("/").split("/")[-1] if perma_url else ""
            
            charts_list.append({
                "id": chart.get("id"),
                "title": chart.get("title"),
                "subtitle": chart.get("subtitle"),
                "image": chart.get("image", "").replace("50x50", "500x500"),
                "token": token # Pass this token to /charts?category=chart-details
            })
            
        results["charts_list"] = charts_list
        
    # 6. Chart Details / Hit Songs (Dynamic)
    if category in ["all", "chart-details"]:
        results["chart_details"] = fetch_saavn_data(
            "webapi.get",
            token=chart_token, # Uses the dynamic token
            type="playlist",
            p=p,
            n=n,
            includeMetaTags=0,
            ctx="wap6dot0"
        )
        
    # Return a specific category
    if category != "all":
        target_key = category.replace("-", "_")
        return results[target_key]
        
    # Return everything
    return {"status": "success", "results": results}

@app.get("/decrypt")
def decrypt_url(url: str = Query(..., description="Base64 encrypted media URL")):
    decrypted = decrypt_audio_url_safe(url)
    if not decrypted:
        raise HTTPException(status_code=400, detail="Decryption failed")
    return {
        "encrypted_url": url,
        "decrypted_url": decrypted,
        "qualities": generate_qualities(decrypted)
    }

@app.get("/download")
def download_audio(
    url: str = Query(..., description="Direct audio URL to download"),
    title: str = Query("", description="Song Title"),
    artist: str = Query("", description="Artist Name"),
    album: str = Query("", description="Album Name"),
    image: str = Query("", description="Cover Image URL")
):
    """Downloads audio, adds ID3 tags, and returns it as an attachment."""
    if not url:
        raise HTTPException(status_code=400, detail="Missing audio URL")
        
    audio_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.m4a') as tmp_audio:
            audio_path = tmp_audio.name
        
        audio_resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, stream=True)
        audio_resp.raise_for_status()
        
        with open(audio_path, 'wb') as f:
            for chunk in audio_resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        audio = MP4(audio_path)
        if title: audio['\xa9nam'] = title
        if artist: audio['\xa9ART'] = artist
        if album: audio['\xa9alb'] = album
        
        if image:
            try:
                img_resp = requests.get(image, headers={'User-Agent': 'Mozilla/5.0'})
                if img_resp.status_code == 200:
                    audio['covr'] = [MP4Cover(img_resp.content, imageformat=MP4Cover.FORMAT_JPEG)]
            except Exception:
                pass
            
        audio.save()
        
        with open(audio_path, 'rb') as f:
            data = f.read()
            
        os.unlink(audio_path)
        
        safe_title = ''.join([c for c in title if c.isalnum() or c in ' -_']).strip() or 'song'
        headers = {
            'Content-Disposition': f'attachment; filename="{safe_title}.m4a"'
        }
        return Response(content=data, media_type="audio/mp4", headers=headers)
        
    except Exception as e:
        if audio_path and os.path.exists(audio_path):
            os.unlink(audio_path)
        raise HTTPException(status_code=500, detail=str(e))
