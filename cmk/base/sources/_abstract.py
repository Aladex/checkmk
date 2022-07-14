#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

import abc
import logging
from functools import partial
from pathlib import Path
from typing import final, Final, Generic, Optional, Sequence

import cmk.utils
import cmk.utils.debug
import cmk.utils.log  # TODO: Remove this!
import cmk.utils.misc
import cmk.utils.paths
from cmk.utils.check_utils import ActiveCheckResult
from cmk.utils.log import VERBOSE
from cmk.utils.type_defs import HostAddress, result, SourceType

from cmk.snmplib.type_defs import TRawData

import cmk.core_helpers.cache as file_cache
from cmk.core_helpers import Fetcher, get_raw_data, Parser, Summarizer
from cmk.core_helpers.cache import FileCache
from cmk.core_helpers.controller import FetcherType
from cmk.core_helpers.host_sections import HostSections, TRawDataSection
from cmk.core_helpers.type_defs import Mode, SectionNameCollection

from cmk.base.config import HostConfig

__all__ = ["Source"]


class Source(Generic[TRawData, TRawDataSection], abc.ABC):
    """Hold the configuration to fetchers and checkers.

    At best, this should only hold static data, that is, every
    attribute is final.

    """

    use_outdated_persisted_sections: bool = False

    def __init__(
        self,
        host_config: HostConfig,
        ipaddress: Optional[HostAddress],
        *,
        source_type: SourceType,
        fetcher_type: FetcherType,
        description: str,
        default_raw_data: TRawData,
        default_host_sections: HostSections[TRawDataSection],
        id_: str,
        cache_dir: Optional[Path] = None,
        persisted_section_dir: Optional[Path] = None,
    ) -> None:
        self.host_config: Final = host_config
        self.ipaddress: Final = ipaddress
        self.source_type: Final = source_type
        self.fetcher_type: Final = fetcher_type
        self.description: Final = description
        self.default_raw_data: Final = default_raw_data
        self.default_host_sections: Final = default_host_sections
        self.id: Final = id_
        if not cache_dir:
            cache_dir = Path(cmk.utils.paths.data_source_cache_dir) / self.id
        if not persisted_section_dir:
            persisted_section_dir = Path(cmk.utils.paths.var_dir) / "persisted_sections" / self.id

        self.file_cache_base_path: Final = cache_dir
        self.file_cache_max_age: file_cache.MaxAge = file_cache.MaxAge.none()
        self.persisted_sections_file_path: Final = persisted_section_dir / self.host_config.hostname

        self._logger: Final = logging.getLogger("cmk.base.data_source.%s" % id_)

        self.exit_spec = self.host_config.exit_code_spec(id_)

    def __repr__(self) -> str:
        return "%s(%r, %r, description=%r, id=%r)" % (
            type(self).__name__,
            self.host_config,
            self.ipaddress,
            self.description,
            self.id,
        )

    @property
    def fetcher_configuration(self):
        return self._make_fetcher().to_json()

    @property
    def file_cache_configuration(self):
        return self._make_file_cache().to_json()

    @final
    def fetch(self, mode: Mode) -> result.Result[TRawData, Exception]:
        return get_raw_data(self._make_file_cache(), self._make_fetcher(), mode)

    @final
    def parse(
        self,
        raw_data: result.Result[TRawData, Exception],
        *,
        selection: SectionNameCollection,
    ) -> result.Result[HostSections[TRawDataSection], Exception]:
        try:
            return raw_data.map(partial(self._make_parser().parse, selection=selection))
        except Exception as exc:
            self._logger.log(VERBOSE, "ERROR: %s", exc)
            if cmk.utils.debug.enabled():
                raise
            return result.Error(exc)

    @final
    def summarize(
        self,
        host_sections: result.Result[HostSections[TRawDataSection], Exception],
    ) -> Sequence[ActiveCheckResult]:
        summarizer = self._make_summarizer()
        if host_sections.is_ok():
            return summarizer.summarize_success()
        return summarizer.summarize_failure(host_sections.error)

    @abc.abstractmethod
    def _make_file_cache(self) -> FileCache[TRawData]:
        raise NotImplementedError

    @abc.abstractmethod
    def _make_fetcher(self) -> Fetcher:
        """Create a fetcher with this configuration."""
        raise NotImplementedError

    @abc.abstractmethod
    def _make_parser(self) -> Parser[TRawData, TRawDataSection]:
        """Create a parser with this configuration."""
        raise NotImplementedError

    @abc.abstractmethod
    def _make_summarizer(self) -> Summarizer:
        """Create a summarizer with this configuration."""
        raise NotImplementedError
