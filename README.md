# JioSaavn API Wrapper (FastAPI) 🎵

An unofficial, high-performance Python API wrapper for JioSaavn, built with **FastAPI**. It reverse-engineers the internal JioSaavn API to fetch songs, albums, playlists, lyrics, decrypt high-quality audio streams, and download metadata-tagged audio files.

Built for deployment on **Vercel** with built-in geo-unblocking (Indian IP spoofing) to bypass regional licensing restrictions.

## Features
- **Comprehensive Search:** Fetch global autocomplete results, songs, albums, artists, and playlists.
- **Audio Decryption:** Decrypts JioSaavn's DES-ECB encrypted media URLs to direct audio streams (12kbps to 320kbps).
- **Direct Downloads & Tagging:** Download endpoint that automatically injects ID3 metadata (Title, Artist, Album, and Cover Art) into `.m4a` files using `mutagen`.
- **Geo-Restriction Bypass:** Spoofs Indian IPs and headers to access original tracks in geo-blocked regions (e.g., US/Europe).
- **Interactive Docs:** Out-of-the-box Swagger UI documentation at `/docs`.

## Deploy to Vercel

You can deploy this API directly to your Vercel account with one click:

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/nikhil-s-archive/jio-saavn-api)

> **⚠️ Vercel Deployment Note:** Vercel's free serverless functions have a **4.5 MB maximum response limit**. If you use the `/download` endpoint for `320kbps` songs (which are often 8MB+), Vercel will throw a `500 Internal Server Error`. The download endpoint works perfectly on Vercel for `96kbps` and `160kbps` qualities. For 320kbps downloads, consider hosting on a VPS like Railway, Render, or DigitalOcean.

## API Endpoints

Once deployed (or running locally), you can access the following endpoints:

| Endpoint | Method | Parameters | Description |
|----------|--------|------------|-------------|
| `/` | `GET` | None | Health check / Root |
| `/search/autocomplete` | `GET` | `query` | Global autocomplete search |
| `/search/songs` | `GET` | `q`, `n`, `p` | Search for songs (with pagination) |
| `/song` | `GET` | `pids` | Fetch details for a specific song ID |
| `/album` | `GET` | `albumid` | Fetch details for a specific album ID |
| `/playlist` | `GET` | `listid` | Fetch details for a specific playlist ID |
| `/artist` | `GET` | `artistId` | Fetch artist details |
| `/lyrics` | `GET` | `lyrics_id` | Fetch lyrics for a song ID |
| `/decrypt` | `GET` | `url` | Decrypts a Base64 media URL into direct audio links |
| `/download` | `GET` | `url`, `title`, `artist`, `album`, `image` | Downloads audio, adds cover/metadata, returns `.m4a` file |

### Try the Interactive UI
Navigate to `https://jio-saavn-api-three-drab.vercel.app/docs` to test all endpoints interactively.

## Local Setup

To run this project locally on your machine:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME.git)
   cd YOUR_REPO_NAME
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the FastAPI development server:**
   ```bash
   uvicorn api.index:app --reload
   ```

4. Open `http://127.0.0.1:8000/docs` in your browser.

## Credits & Disclaimer
* API reverse engineering specification and DES decryption logic based on research by [Sagarithm / Sagar Kewat](https://www.sagarithm.in/b/jiosaavn-api-reverse-engineering-client-specification).
* **Disclaimer:** This project is for educational and research purposes only. The JioSaavn API is internal. Do not use this to pirate copyrighted content or overload JioSaavn's servers.
