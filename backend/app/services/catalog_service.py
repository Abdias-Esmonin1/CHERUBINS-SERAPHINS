"""Service Catalogue — logique métier pour categories, languages,
artists, albums, songs.

Cf. Livrable 2 §2.1 : un service ne lève que des exceptions métier,
jamais de HTTPException.
"""

import re
import unicodedata
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, NotFoundError
from app.models.album import Album
from app.models.artist import Artist
from app.models.category import Category
from app.models.language import Language
from app.models.song import Song
from app.repositories.album_repository import AlbumRepository
from app.repositories.artist_repository import ArtistRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.language_repository import LanguageRepository
from app.repositories.song_repository import SongRepository
from app.schemas.album import AlbumCreate
from app.schemas.artist import ArtistCreate
from app.schemas.category import CategoryCreate
from app.schemas.language import LanguageCreate
from app.schemas.song import SongCreate, SongUpdate


def _slugify(value: str) -> str:
    """Convertit une chaîne en slug ASCII minuscule (ex. "Way Maker" ->
    "way-maker"). Utilitaire technique, pas une règle métier — aucune
    valeur définie dans les documents de référence pour cet algorithme.
    """
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    return slug or "item"


class CatalogService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.categories = CategoryRepository(session)
        self.languages = LanguageRepository(session)
        self.artists = ArtistRepository(session)
        self.albums = AlbumRepository(session)
        self.songs = SongRepository(session)

    # ---------------------------------------------------------- Category

    async def create_category(self, payload: CategoryCreate) -> Category:
        if await self.categories.get_by_name(payload.name) is not None:
            raise ConflictError("Cette catégorie existe déjà.", code="CATEGORY_ALREADY_EXISTS")
        category = Category(name=payload.name, description=payload.description)
        category = await self.categories.create(category)
        await self._session.commit()
        return category

    # ---------------------------------------------------------- Language

    async def create_language(self, payload: LanguageCreate) -> Language:
        if await self.languages.get_by_code(payload.code) is not None:
            raise ConflictError("Cette langue existe déjà.", code="LANGUAGE_ALREADY_EXISTS")
        language = Language(code=payload.code, name=payload.name, native_name=payload.native_name)
        language = await self.languages.create(language)
        await self._session.commit()
        return language

    # ------------------------------------------------------------ Artist

    async def create_artist(self, payload: ArtistCreate) -> Artist:
        slug = await self._unique_artist_slug(payload.name)
        artist = Artist(
            name=payload.name,
            slug=slug,
            biography=payload.biography,
            country=payload.country,
            image_url=payload.image_url,
            official_links=payload.official_links,
        )
        artist = await self.artists.create(artist)
        await self._session.commit()
        return artist

    async def get_artist_by_slug(self, slug: str) -> Artist:
        artist = await self.artists.get_by_slug(slug)
        if artist is None:
            raise NotFoundError("Artiste introuvable.", code="ARTIST_NOT_FOUND")
        return artist

    async def _unique_artist_slug(self, name: str) -> str:
        base = _slugify(name)
        slug = base
        suffix = 2
        while await self.artists.slug_exists(slug):
            slug = f"{base}-{suffix}"
            suffix += 1
        return slug

    # ------------------------------------------------------------- Album

    async def create_album(self, payload: AlbumCreate) -> Album:
        if await self.artists.get_by_id(payload.artist_id) is None:
            raise NotFoundError("Artiste introuvable.", code="ARTIST_NOT_FOUND")
        album = Album(
            artist_id=payload.artist_id,
            title=payload.title,
            release_year=payload.release_year,
            cover_url=payload.cover_url,
        )
        album = await self.albums.create(album)
        await self._session.commit()
        return await self.albums.get_by_id(album.id)  # recharge avec artist eager-loaded

    async def get_album(self, album_id: UUID) -> Album:
        album = await self.albums.get_by_id(album_id)
        if album is None:
            raise NotFoundError("Album introuvable.", code="ALBUM_NOT_FOUND")
        return album

    # -------------------------------------------------------------- Song

    async def create_song(self, payload: SongCreate) -> Song:
        if await self.artists.get_by_id(payload.artist_id) is None:
            raise NotFoundError("Artiste introuvable.", code="ARTIST_NOT_FOUND")
        if payload.album_id is not None and await self.albums.get_by_id(payload.album_id) is None:
            raise NotFoundError("Album introuvable.", code="ALBUM_NOT_FOUND")
        if payload.category_id is not None and await self.categories.get_by_id(payload.category_id) is None:
            raise NotFoundError("Catégorie introuvable.", code="CATEGORY_NOT_FOUND")
        if await self.languages.get_by_id(payload.original_language_id) is None:
            raise NotFoundError("Langue introuvable.", code="LANGUAGE_NOT_FOUND")

        slug = await self._unique_song_slug(payload.title)
        song = Song(
            title=payload.title,
            slug=slug,
            artist_id=payload.artist_id,
            album_id=payload.album_id,
            category_id=payload.category_id,
            original_language_id=payload.original_language_id,
            cover_url=payload.cover_url,
            external_provider=payload.external_provider,
            external_id=payload.external_id,
            external_url=payload.external_url,
            status="DRAFT",
        )
        song = await self.songs.create(song)
        await self._session.commit()
        return await self.songs.get_by_id(song.id)  # recharge avec relations eager-loaded

    async def get_song_by_slug(self, slug: str) -> Song:
        song = await self.songs.get_by_slug(slug)
        if song is None:
            raise NotFoundError("Chanson introuvable.", code="SONG_NOT_FOUND")
        return song

    async def update_song(self, song_id: UUID, payload: SongUpdate) -> Song:
        song = await self.songs.get_by_id(song_id)
        if song is None:
            raise NotFoundError("Chanson introuvable.", code="SONG_NOT_FOUND")

        if payload.status is not None and payload.status not in ("DRAFT", "PUBLISHED", "ARCHIVED"):
            raise ConflictError("Statut invalide.", code="INVALID_STATUS")
        if payload.album_id is not None and await self.albums.get_by_id(payload.album_id) is None:
            raise NotFoundError("Album introuvable.", code="ALBUM_NOT_FOUND")
        if payload.category_id is not None and await self.categories.get_by_id(payload.category_id) is None:
            raise NotFoundError("Catégorie introuvable.", code="CATEGORY_NOT_FOUND")

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(song, field, value)

        await self._session.commit()
        return await self.songs.get_by_id(song.id)

    async def _unique_song_slug(self, title: str) -> str:
        base = _slugify(title)
        slug = base
        suffix = 2
        while await self.songs.slug_exists(slug):
            slug = f"{base}-{suffix}"
            suffix += 1
        return slug
