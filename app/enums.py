from enum import Enum


class TagType(str, Enum):
    ARTIST = "artist"
    GENERAL = "general"
    CHARACTER = "character"
    PARODY = "parody"


class ReactionType(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    NONE = "none"
