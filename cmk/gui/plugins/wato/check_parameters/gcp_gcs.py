#!/usr/bin/env python
# Copyright (C) 2022 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.
from cmk.gui.i18n import _
from cmk.gui.plugins.wato.utils import (
    CheckParameterRulespecWithItem,
    CheckParameterRulespecWithoutItem,
    Levels,
    rulespec_registry,
    RulespecGroupCheckParametersApplications,
)
from cmk.gui.plugins.wato.utils.simple_levels import SimpleLevels
from cmk.gui.valuespec import Dictionary, Filesize, Integer, MonitoringState, Percentage, ValueSpec

# A notes about the names of the Dictionary elements. They correspond to the names of the metrics in
# the check plugin. Please do not change them.


def _vs_gcs_bucket_requests() -> ValueSpec:
    return Dictionary(
        title=_("Parameters for the bucket requests"),
        elements=[
            ("requests", Levels(title=_("Parameters for the bucket requests"), unit="1/second"))
        ],
    )


rulespec_registry.register(
    CheckParameterRulespecWithItem(
        check_group_name="gcp_gcs_requests",
        group=RulespecGroupCheckParametersApplications,
        match_type="dict",
        parameter_valuespec=_vs_gcs_bucket_requests,
        title=lambda: _("GCP/GCS Requests"),
    )
)


def _vs_gcs_bucket_network() -> ValueSpec:
    return Dictionary(
        title=_("Parameters for the bucket network io"),
        elements=[
            ("net_data_sent", Levels(title=_("Parameters send bytes"), unit="bytes/s")),
            ("net_data_recv", Levels(title=_("Parameters received bytes"), unit="bytes/s")),
        ],
    )


rulespec_registry.register(
    CheckParameterRulespecWithItem(
        check_group_name="gcp_gcs_network",
        group=RulespecGroupCheckParametersApplications,
        match_type="dict",
        parameter_valuespec=_vs_gcs_bucket_network,
        title=lambda: _("GCP/GCS Network"),
    )
)


def _vs_gcs_bucket_objects() -> ValueSpec:
    return Dictionary(
        title=_("Parameters for the bucket objects io"),
        elements=[
            (
                "aws_bucket_size",
                SimpleLevels(Filesize, title=_("Parameters of total bucket size")),
            ),
            ("aws_num_objects", Levels(title=_("Parameters of bucket object counts"))),
        ],
    )


rulespec_registry.register(
    CheckParameterRulespecWithItem(
        check_group_name="gcp_gcs_objects",
        group=RulespecGroupCheckParametersApplications,
        match_type="dict",
        parameter_valuespec=_vs_gcs_bucket_objects,
        title=lambda: _("GCP/GCS Objects"),
    )
)


def _vs_sql_status() -> ValueSpec:
    return Dictionary(
        title=_("Map GCP status to check mk"),
        elements=[
            ("RUNNING", MonitoringState(title=_("Running"), default_value=0)),
            ("SUSPEND", MonitoringState(title=_("Suspend"), default_value=1)),
            ("RUNNABLE", MonitoringState(title=_("Runnable"), default_value=0)),
            ("PENDING_CREATE", MonitoringState(title=_("Pending create"), default_value=3)),
            ("MAINTENANCE", MonitoringState(title=_("Maintenance"), default_value=3)),
            ("FAILED", MonitoringState(title=_("Failed"), default_value=2)),
            ("UNKOWN_STATE", MonitoringState(title=_("Unkown"), default_value=3)),
        ],
    )


rulespec_registry.register(
    CheckParameterRulespecWithItem(
        check_group_name="gcp_sql_status",
        group=RulespecGroupCheckParametersApplications,
        match_type="dict",
        parameter_valuespec=_vs_sql_status,
        title=lambda: _("GCP/Cloud SQL status"),
    )
)


def _vs_run_network() -> ValueSpec:
    return Dictionary(
        title=_("Levels on network traffic"),
        elements=[
            ("net_data_sent", SimpleLevels(title=_("Data sent"), unit="bytes/s")),
            ("net_data_recv", SimpleLevels(title=_("Data received"), unit="bytes/s")),
        ],
    )


def _vs_run_memory() -> ValueSpec:
    return Dictionary(
        title=_("Levels memory"),
        elements=[
            (
                "memory_util",
                SimpleLevels(Percentage, title=_("Memory utilitzation"), default_value=(80, 90)),
            ),
        ],
    )


def _vs_run_cpu() -> ValueSpec:
    return Dictionary(
        title=_("Levels CPU"),
        elements=[
            ("util", SimpleLevels(Percentage, title=_("CPU utilitzation"), default_value=(80, 90))),
        ],
    )


rulespec_registry.register(
    CheckParameterRulespecWithItem(
        check_group_name="gcp_sql_cpu",
        group=RulespecGroupCheckParametersApplications,
        match_type="dict",
        parameter_valuespec=_vs_run_cpu,
        title=lambda: _("GCP/Cloud SQL CPU"),
    )
)
rulespec_registry.register(
    CheckParameterRulespecWithItem(
        check_group_name="gcp_sql_memory",
        group=RulespecGroupCheckParametersApplications,
        match_type="dict",
        parameter_valuespec=_vs_run_memory,
        title=lambda: _("GCP/Cloud SQL memory"),
    )
)

rulespec_registry.register(
    CheckParameterRulespecWithItem(
        check_group_name="gcp_sql_network",
        group=RulespecGroupCheckParametersApplications,
        match_type="dict",
        parameter_valuespec=_vs_run_network,
        title=lambda: _("GCP/Cloud SQL Network"),
    )
)


def _vs_sql_disk() -> ValueSpec:
    return Dictionary(
        title=_("Levels disk"),
        elements=[
            ("fs_used_percent", Levels(title=_("Disk usage"), unit="%", default_value=(80, 90))),
            ("disk_read_ios", Levels(title=_("Number of read IOPS"))),
            ("disk_write_ios", Levels(title=_("Number of write IOPS"))),
        ],
    )


rulespec_registry.register(
    CheckParameterRulespecWithItem(
        check_group_name="gcp_sql_disk",
        group=RulespecGroupCheckParametersApplications,
        match_type="dict",
        parameter_valuespec=_vs_sql_disk,
        title=lambda: _("GCP/Cloud SQL disk"),
    )
)

rulespec_registry.register(
    CheckParameterRulespecWithItem(
        check_group_name="gcp_filestore_disk",
        group=RulespecGroupCheckParametersApplications,
        match_type="dict",
        parameter_valuespec=_vs_sql_disk,
        title=lambda: _("GCP/Filestore"),
    )
)


def _vs_gce_cpu() -> Dictionary:
    return Dictionary(
        title=_("Levels CPU"),
        elements=[
            ("util", SimpleLevels(Percentage, title=_("CPU utilization"))),
            ("vcores", SimpleLevels(Integer, title=_("Number of vCPUs reserved for the VM"))),
        ],
    )


rulespec_registry.register(
    CheckParameterRulespecWithoutItem(
        check_group_name="gcp_gce_cpu",
        group=RulespecGroupCheckParametersApplications,
        match_type="dict",
        parameter_valuespec=_vs_gce_cpu,
        title=lambda: _("GCP/GCE CPU"),
    )
)


def _vs_gce_disk() -> Dictionary:
    return Dictionary(
        title=_("Levels disk IO"),
        elements=[
            (
                "disk_read_throughput",
                SimpleLevels(Filesize, title=_("Disk read throughput per second")),
            ),
            (
                "disk_write_throughput",
                SimpleLevels(Filesize, title=_("Disk read throughput per second")),
            ),
            ("disk_read_ios", SimpleLevels(Integer, title=_("Disk read opertions"), unit="ops")),
            ("disk_write_ios", SimpleLevels(Integer, title=_("Disk read opertions"), unit="ops")),
        ],
    )


rulespec_registry.register(
    CheckParameterRulespecWithoutItem(
        check_group_name="gcp_gce_disk",
        group=RulespecGroupCheckParametersApplications,
        match_type="dict",
        parameter_valuespec=_vs_gce_disk,
        title=lambda: _("GCP/GCE disk IO"),
    )
)


def _vs_cost() -> Dictionary:
    return Dictionary(
        title=_("Levels monthly GCP costs"),
        elements=[
            (
                "levels",
                Levels(title=_("Amount in billed currency")),
            ),
        ],
    )


rulespec_registry.register(
    CheckParameterRulespecWithItem(
        check_group_name="gcp_cost",
        group=RulespecGroupCheckParametersApplications,
        match_type="dict",
        parameter_valuespec=_vs_cost,
        title=lambda: _("GCP Cost"),
    )
)
