"""Internationalization (i18n) support for MDKV CLI messages.

Uses Python's built-in ``gettext`` module.  Translation files are
stored in ``mdkv/locales/<lang>/LC_MESSAGES/mdkv.po`` (compiled to ``.mo``).

Currently only English is shipped.  The infrastructure is in place for
future translations.
"""
from __future__ import annotations

import gettext as _gettext
import os
from pathlib import Path

_localedir = Path(__file__).resolve().parent / "locales"
_current_lang = "en"
_translator = _gettext.NullTranslations()


def set_language(lang: str = "en") -> None:
    """Set the current language for CLI messages.

    Falls back to English if the requested language is not available.
    """
    global _current_lang, _translator
    _current_lang = lang
    try:
        _translator = _gettext.translation("mdkv", localedir=str(_localedir), languages=[lang])
    except FileNotFoundError:
        _translator = _gettext.NullTranslations()


def gettext(msg: str) -> str:
    """Translate a message string."""
    return _translator.gettext(msg)


# Convenience alias
_ = gettext


# Initialize with environment language or English
_env_lang = os.environ.get("MDKV_LANG") or os.environ.get("LANG", "en").split(".")[0].split("_")[0]
set_language(_env_lang)
