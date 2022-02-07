// Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
// This file is part of Checkmk (https://checkmk.com). It is subject to the
// terms and conditions defined in the file COPYING, which is part of this
// source code package.

#pragma once
#ifndef agent_controller_h__
#define agent_controller_h__
#include <cstdint>
#include <filesystem>
#include <string_view>

namespace YAML {
class Node;
}

namespace cma::ac {
constexpr std::string_view kLegacyPullFile{"allow-legacy-pull"};
std::filesystem::path GetController(const std::filesystem::path &service);
constexpr uint16_t windows_internal_port{50001};  // must be synced with Rust
bool StartAgentController(const std::filesystem::path &service);
bool KillAgentController();
bool IsRunController(const YAML::Node &node);
bool IsUseLegacyMode(const YAML::Node &node);
/// Creates or deletes signal file in the user dir.
///
/// Must be in sync with Rust code
void EnableLegacyMode(bool enable);
}  // namespace cma::ac

#endif  // agent_controller_h__
