// Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
// This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
// conditions defined in the file COPYING, which is part of this source code package.

mod agent_receiver_api;
mod certs;
mod cli;
mod config;
mod constants;
mod delete_connection;
mod dump;
mod import_connection;
mod monitoring_data;
mod pull;
mod push;
mod registration;
mod status;
mod tls_server;
use anyhow::{Context, Result as AnyhowResult};
use config::JSONLoader;
use log::error;
#[cfg(unix)]
use nix::unistd;
use std::io::{self, Write};
use std::sync::mpsc;
use std::thread;
use structopt::StructOpt;

fn daemon(
    registry: config::Registry,
    legacy_pull_marker: std::path::PathBuf,
    port: String,
) -> AnyhowResult<()> {
    let registry_for_push = registry.clone();
    let registry_for_pull = registry;

    let (tx_push, rx) = mpsc::channel();
    let tx_pull = tx_push.clone();

    thread::spawn(move || {
        tx_push.send(push::push(registry_for_push)).unwrap();
    });
    thread::spawn(move || {
        tx_pull
            .send(pull::pull(registry_for_pull, legacy_pull_marker, port))
            .unwrap();
    });

    // We should never receive anything here, unless one of the threads crashed.
    // In that case, this will contain an error that should be propagated.
    rx.recv().unwrap()
}

#[cfg(unix)]
fn init_logging(level: &str) -> Result<flexi_logger::LoggerHandle, flexi_logger::FlexiLoggerError> {
    flexi_logger::Logger::try_with_env_or_str(level)?
        .log_to_stderr()
        .format(flexi_logger::default_format)
        .start()
}

#[cfg(windows)]
fn init_logging(
    level: &str,
    path: &std::path::Path,
) -> Result<flexi_logger::LoggerHandle, flexi_logger::FlexiLoggerError> {
    flexi_logger::Logger::try_with_env_or_str(level)?
        .log_to_file(flexi_logger::FileSpec::try_from(path)?)
        .append()
        .format(flexi_logger::detailed_format)
        .start()
}

#[cfg(unix)]
fn become_user(user: &unistd::User) -> AnyhowResult<()> {
    unistd::setgid(user.gid).context(format!(
        "Failed to set group id {} corresponding to user {}",
        user.gid, user.name,
    ))?;
    unistd::setuid(user.uid).context(format!(
        "Failed to set user id {} corresponding to user {}",
        user.uid, user.name,
    ))?;
    Ok(())
}

#[cfg(unix)]
fn determine_paths(username: &str) -> AnyhowResult<constants::Paths> {
    let user = unistd::User::from_name(username)?.context(format!(
        "Could not find dedicated Checkmk agent user {}",
        username
    ))?;

    if let Err(error) = become_user(&user) {
        return Err(error.context(format!(
            "Failed to run as user '{}'. Please execute with sufficient permissions (maybe try 'sudo').",
            user.name,
        )));
    }

    Ok(constants::Paths::new(&user.dir))
}

#[cfg(windows)]
fn determine_paths(_: &str) -> AnyhowResult<constants::Paths> {
    let program_data_path = std::env::var(constants::ENV_PROGRAM_DATA)
        .unwrap_or_else(|_| String::from("c:\\ProgramData"));
    let home = std::path::PathBuf::from(program_data_path + constants::WIN_AGENT_HOME_DIR);
    Ok(constants::Paths::new(&home))
}

fn init() -> AnyhowResult<(cli::Args, constants::Paths)> {
    // Parse args as first action to directly exit from --help or malformatted arguments
    let args = cli::Args::from_args();

    let paths = determine_paths(constants::CMK_AGENT_USER)?;

    #[cfg(unix)]
    let logging_init_result = init_logging(&args.logging_level());
    #[cfg(windows)]
    let logging_init_result = init_logging(&args.logging_level(), &paths.log_path);

    if let Err(error) = logging_init_result {
        io::stderr()
            .write_all(format!("Failed to initialize logging: {:?}", error).as_bytes())
            .unwrap_or(());
    }

    Ok((args, paths))
}

fn run_requested_mode(args: cli::Args, paths: constants::Paths) -> AnyhowResult<()> {
    let stored_config = config::ConfigFromDisk::load(&paths.config_path)?;
    let mut registry = config::Registry::from_file(&paths.registry_path)
        .context("Error while loading registered connections.")?;
    match args {
        cli::Args::Register(reg_args) => {
            registration::register(
                config::RegistrationConfig::new(stored_config, reg_args)?,
                &mut registry,
            )?;
            pull::disallow_legacy_pull(&paths.legacy_pull_path).context(
                "Registration successful, but could not delete marker for legacy pull mode",
            )
        }
        cli::Args::RegisterSurrogatePull(surr_pull_reg_args) => {
            registration::register_surrogate_pull(config::RegistrationConfig::new(
                stored_config,
                surr_pull_reg_args,
            )?)
        }
        cli::Args::Push { .. } => push::handle_push_cycle(&registry),
        cli::Args::Pull(pull_args) => pull::pull(
            registry,
            paths.legacy_pull_path,
            pull_args
                .port
                .unwrap_or_else(|| constants::AGENT_PORT.to_owned()),
        ),
        cli::Args::Daemon(daemon_args) => daemon(
            registry,
            paths.legacy_pull_path,
            daemon_args
                .port
                .unwrap_or_else(|| constants::AGENT_PORT.to_owned()),
        ),
        cli::Args::Dump { .. } => dump::dump(),
        cli::Args::Status(status_args) => status::status(registry, status_args.json),
        cli::Args::Delete(delete_args) => {
            delete_connection::delete(&mut registry, &delete_args.connection)
        }
        cli::Args::DeleteAll { .. } => delete_connection::delete_all(&mut registry),
        cli::Args::Import(import_args) => import_connection::import(&mut registry, &import_args),
    }
}
fn main() -> AnyhowResult<()> {
    let (args, paths) = match init() {
        Ok(args) => args,
        Err(error) => {
            error!("{:?}", error);
            return Err(error);
        }
    };

    let result = run_requested_mode(args, paths);

    if let Err(error) = &result {
        error!("{:?}", error)
    }

    result
}

#[cfg(windows)]
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_windows_paths() {
        let p = determine_paths(constants::CMK_AGENT_USER).unwrap();
        let home = String::from("C:\\ProgramData") + constants::WIN_AGENT_HOME_DIR;
        assert_eq!(p.home_dir, std::path::PathBuf::from(&home));
        assert_eq!(
            p.config_path,
            std::path::PathBuf::from(&home).join("cmk-agent-ctl-config.json")
        );
        assert_eq!(
            p.registry_path,
            std::path::PathBuf::from(&home).join("registered_connections.json")
        );
        assert_eq!(
            p.log_path,
            std::path::PathBuf::from(&home)
                .join("log")
                .join("cmk-agent-ctl.log")
        );
        assert_eq!(
            p.legacy_pull_path,
            std::path::PathBuf::from(&home).join("allow-legacy-pull")
        );
    }
}
