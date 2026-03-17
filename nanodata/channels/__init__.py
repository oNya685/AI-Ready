"""Chat channels module with plugin architecture."""

from nanodata.channels.base import BaseChannel
from nanodata.channels.manager import ChannelManager

__all__ = ["BaseChannel", "ChannelManager"]
