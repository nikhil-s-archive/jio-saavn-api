from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import base64
from Crypto.Cipher import DES

app = FastAPI(title="JioSaavn Unofficial API", description="Reverse-engineered JioSaavn API Wrapper")

# Allow CORS for frontends
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

# --- Helper Functions ---

async def fetch_saavn_data(call: str, **kwargs) -> dict:
    params = BASE_PARAMS.copy()
    params["__call"] = call
    params.update(kwargs)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"JioSaavn API Error: {str(e)}")

def decrypt_audio_url(encrypted_url: str) -> str:
    """
    Decrypts the media URL using DES-ECB.
    Algorithm: DES-ECB, Key: 38346591
    """
    try:
        key = b'38346591'
        cipher = DES.new(key, DES.MODE_ECB)
        decoded_b64 = base64.b64decode(encrypted_url)
        decrypted = cipher.decrypt(decoded_b64)
        
        # Remove PKCS5/PKCS7 padding
        pad_len = decrypted[-1]
        decrypted_url = decrypted[:-pad_len].decode('utf-8')
        return decrypted_url
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Decryption failed: {str(e)}")


# --- API Endpoints ---

@app.get("/")
async def root():
    return {"message": "JioSaavn API Wrapper is running."}

@app.get("/search/autocomplete")
async def autocomplete(query: str = Query(..., description="The search term")):
    """Global Autocomplete Search"""
    return await fetch_saavn_data("autocomplete.get", query=query)

@app.get("/search/songs")
async def search_songs(
    q: str = Query(..., description="Query string"), 
    n: int = Query(10, description="Limit/count number"), 
    p: int = Query(1, description="Page number (1-indexed)")
):
    """Songs Search"""
    return await fetch_saavn_data("search.getResults", q=q, n=n, p=p)

@app.get("/song")
async def get_song(pids: str = Query(..., description="Comma-separated list of song IDs")):
    """Fetch Song Details"""
    return await fetch_saavn_data("song.getDetails", pids=pids)

@app.get("/album")
async def get_album(albumid: str = Query(..., description="Album ID")):
    """Fetch Album Details"""
    return await fetch_saavn_data("content.getAlbumDetails", albumid=albumid)

@app.get("/artist")
async def get_artist(artistId: str = Query(..., description="Artist ID")):
    """Fetch Artist Details"""
    return await fetch_saavn_data("artist.getArtistPageDetails", artistId=artistId)

@app.get("/playlist")
async def get_playlist(listid: str = Query(..., description="Playlist ID")):
    """Fetch Playlist Details"""
    return await fetch_saavn_data("playlist.getDetails", listid=listid)

@app.get("/lyrics")
async def get_lyrics(lyrics_id: str = Query(..., description="Song ID to fetch lyrics for")):
    """Fetch Lyrics"""
    return await fetch_saavn_data("lyrics.get", lyrics_id=lyrics_id)

@app.get("/decrypt")
async def decrypt_url(url: str = Query(..., description="Base64 encrypted media URL")):
    """Decrypt the high-quality audio stream URL"""
    decrypted = decrypt_audio_url(url)
    return {
        "encrypted_url": url,
        "decrypted_url": decrypted,
        "qualities": {
            "12kbps": decrypted.replace("_320", "_12"),
            "48kbps": decrypted.replace("_320", "_48"),
            "96kbps": decrypted.replace("_320", "_96"),
            "160kbps": decrypted.replace("_320", "_160"),
            "320kbps": decrypted.replace("_320", "_320") # Ensures consistency
        }
    }
