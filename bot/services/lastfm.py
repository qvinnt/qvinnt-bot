from __future__ import annotations

import asyncio

import httpx
import pydantic

from bot.services import errors


class Track(pydantic.BaseModel):
    title: str
    artist: str
    listeners: int


class LastFmClient:
    def __init__(self, api_key: str, app_name: str) -> None:
        self.__api_key = api_key
        self.__client = httpx.AsyncClient(headers={"user-agent": app_name})

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.__client.aclose()

    async def search_tracks(
        self,
        song_name: str,
        artist_name: str | None = None,
        limit: int = 3,
    ) -> list[Track]:
        url = "https://ws.audioscrobbler.com/2.0/"

        params = {
            "method": "track.search",
            "track": song_name,
            "api_key": self.__api_key,
            "format": "json",
            "limit": limit,
        }

        if artist_name:
            params["artist"] = artist_name

        response = await self.__client.get(url, params=params)

        if response.status_code != 200:  # noqa: PLR2004
            msg = f"failed to search tracks: {response.status_code} {response.text}"
            raise errors.LastFmServiceError(msg)

        data = response.json()

        if "results" in data and "trackmatches" in data["results"]:
            tracks = data["results"]["trackmatches"]["track"]

            if isinstance(tracks, dict):
                tracks = [tracks]

            return sorted(
                [
                    Track(
                        title=track.get("name"),
                        artist=track.get("artist"),
                        listeners=track.get("listeners", 0),
                    )
                    for track in tracks
                ],
                key=lambda x: x.listeners,
                reverse=True,
            )

        return []


async def main():
    last_fm_client = LastFmClient("119866155dab585472c9cfbd9f00331d", "Qvinnt Bot")

    tracks = await last_fm_client.search_tracks("я стану популярным в интернете")

    for track in tracks:
        print(track)


if __name__ == "__main__":
    asyncio.run(main())
