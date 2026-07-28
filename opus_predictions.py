"""Generate Opus predictions for all granularity experiments and evaluate them.

Claude Opus 4.6 predictions generated inline (no API call needed).
"""

import json
import time
import sys
from pathlib import Path
from dataclasses import dataclass


@dataclass
class TypePrediction:
    source: str
    target: str
    src_conf: float
    tgt_conf: float
    confidence: float
    latency_ms: float
    src_alternatives: list = None
    tgt_alternatives: list = None

    def __post_init__(self):
        if self.src_alternatives is None:
            self.src_alternatives = []
        if self.tgt_alternatives is None:
            self.tgt_alternatives = []


# ── K8s Coarse (6 types) ────────────────────────────────────────────
K8S_COARSE = {
    "c01": ("Cluster", "Pod"), "c02": ("Cluster", "Namespace"),
    "c03": ("Pod", "Pod"), "c04": ("Pod", "Pod"),
    "c05": ("Cluster", "Resource"), "c06": ("Pod", "Pod"),
    "c07": ("Namespace", "Resource"), "c08": ("Cluster", "Helm"),
    "c09": ("Cluster", "Resource"), "c10": ("Pod", "Pod"),
    "c11": ("Cluster", "Config"), "c12": ("Cluster", "Helm"),
    "s01": ("Cluster", "Pod"), "s02": ("Cluster", "Config"),
    "s03": ("Pod", "Pod"), "s04": ("Cluster", "Resource"),
    "s05": ("Cluster", "Pod"), "s06": ("Helm", "Helm"),
    "s07": ("Pod", "Pod"), "s08": ("Pod", "Pod"),
    "m01": ("Namespace", "Pod"), "m02": ("Namespace", "Pod"),
    "m03": ("Resource", "Pod"), "m04": ("Resource", "Pod"),
    "m05": ("Namespace", "Resource"), "m06": ("Namespace", "Resource"),
    "m07": ("Namespace", "Helm"), "m08": ("Namespace", "Pod"),
    "a01": ("Resource", "Resource"), "a02": ("Cluster", "Pod"),
    "a03": ("Pod", "Pod"), "a04": ("Namespace", "Pod"),
    "a05": ("Cluster", "Resource"), "a06": ("Cluster", "Resource"),
    "a07": ("Pod", "Pod"),
    "n01": ("Namespace", "Pod"), "n02": ("Pod", "Pod"),
    "n03": ("Helm", "Helm"), "n04": ("Cluster", "Resource"),
    "n05": ("Pod", "Pod"), "n06": ("Cluster", "Pod"),
    "n07": ("Cluster", "Namespace"), "n08": ("Namespace", "Resource"),
    "p01": ("Resource", "Resource"), "p02": ("Cluster", "Resource"),
    "p03": ("Resource", "Resource"), "p04": ("Resource", "Resource"),
    "p05": ("Cluster", "Resource"), "p06": ("Cluster", "Resource"),
    "p07": ("Namespace", "Helm"),
    "c13": ("Namespace", "Pod"), "c14": ("Pod", "Pod"),
    "c15": ("Pod", "Pod"), "c16": ("Resource", "Resource"),
    "c17": ("Cluster", "Resource"), "c18": ("Cluster", "Pod"),
    "c19": ("Cluster", "Resource"), "c20": ("Namespace", "Resource"),
    "c21": ("Resource", "Resource"), "c22": ("Cluster", "Helm"),
    "c23": ("Namespace", "Helm"), "c24": ("Pod", "Pod"),
    "c25": ("Cluster", "Config"), "c26": ("Resource", "Resource"),
    "c27": ("Helm", "Helm"), "c28": ("Resource", "Resource"),
    "s09": ("Pod", "Pod"), "s10": ("Cluster", "Namespace"),
    "s11": ("Cluster", "Pod"), "s12": ("Pod", "Pod"),
    "s13": ("Namespace", "Resource"), "s14": ("Cluster", "Pod"),
    "s15": ("Resource", "Resource"), "s16": ("Cluster", "Config"),
    "s17": ("Helm", "Helm"), "s18": ("Cluster", "Resource"),
    "s19": ("Namespace", "Helm"), "s20": ("Resource", "Resource"),
    "m09": ("Namespace", "Pod"), "m10": ("Namespace", "Pod"),
    "m11": ("Resource", "Pod"), "m12": ("Resource", "Pod"),
    "m13": ("Namespace", "Pod"), "m14": ("Resource", "Pod"),
    "m15": ("Namespace", "Pod"), "m16": ("Resource", "Pod"),
    "a08": ("Cluster", "Resource"), "a09": ("Pod", "Pod"),
    "a10": ("Cluster", "Resource"), "a11": ("Pod", "Pod"),
    "a12": ("Cluster", "Resource"), "a13": ("Cluster", "Resource"),
    "a14": ("Pod", "Pod"), "a15": ("Cluster", "Resource"),
    "n09": ("Namespace", "Pod"), "n10": ("Cluster", "Helm"),
    "n11": ("Pod", "Pod"), "n12": ("Cluster", "Resource"),
    "n13": ("Resource", "Resource"), "n14": ("Namespace", "Resource"),
    "n15": ("Resource", "Resource"), "n16": ("Cluster", "Resource"),
    "n17": ("Namespace", "Pod"), "n18": ("Helm", "Helm"),
    "p08": ("Resource", "Pod"), "p09": ("Namespace", "Resource"),
    "p10": ("Namespace", "Resource"), "p11": ("Cluster", "Resource"),
    "p12": ("Namespace", "Helm"), "p13": ("Namespace", "Pod"),
    "p14": ("Cluster", "Resource"), "p15": ("Namespace", "Resource"),
    "p16": ("Cluster", "Resource"), "p17": ("Resource", "Resource"),
    "c29": ("Cluster", "Resource"), "c30": ("Resource", "Resource"),
    "c31": ("Resource", "Pod"), "c32": ("Resource", "Resource"),
    "c33": ("Pod", "Pod"), "c34": ("Cluster", "Resource"),
    "c35": ("Namespace", "Helm"), "c36": ("Resource", "Resource"),
    "n19": ("Namespace", "Resource"), "n20": ("Resource", "Resource"),
    "m17": ("Resource", "Pod"), "m18": ("Namespace", "Pod"),
    "m19": ("Namespace", "Pod"), "m20": ("Resource", "Pod"),
}

# ── K8s Medium (13 types) ───────────────────────────────────────────
K8S_MEDIUM = {
    "c01": ("Cluster", "Pod"), "c02": ("Cluster", "Namespace"),
    "c03": ("Pod", "Pod"), "c04": ("Pod", "Pod"),
    "c05": ("Cluster", "Deployment"), "c06": ("Pod", "PodLog"),
    "c07": ("Namespace", "Service"), "c08": ("Cluster", "HelmRelease"),
    "c09": ("Cluster", "Event"), "c10": ("Pod", "CommandOutput"),
    "c11": ("Cluster", "Configuration"), "c12": ("Cluster", "HelmRelease"),
    "s01": ("Cluster", "Pod"), "s02": ("Cluster", "Configuration"),
    "s03": ("Pod", "Pod"), "s04": ("Cluster", "Deployment"),
    "s05": ("Cluster", "Pod"), "s06": ("HelmRelease", "HelmRelease"),
    "s07": ("Pod", "PodLog"), "s08": ("Pod", "CommandOutput"),
    "m01": ("Namespace", "PodLog"), "m02": ("Namespace", "CommandOutput"),
    "m03": ("Service", "CommandOutput"), "m04": ("Deployment", "PodLog"),
    "m05": ("Namespace", "Event"), "m06": ("Namespace", "Ingress"),
    "m07": ("Namespace", "HelmRelease"), "m08": ("Namespace", "CommandOutput"),
    "a01": ("Deployment", "Deployment"), "a02": ("Cluster", "Pod"),
    "a03": ("Pod", "Pod"), "a04": ("Namespace", "Pod"),
    "a05": ("Cluster", "Deployment"), "a06": ("Cluster", "Service"),
    "a07": ("Pod", "PodLog"),
    "n01": ("Namespace", "Pod"), "n02": ("Pod", "PodLog"),
    "n03": ("HelmRelease", "HelmRelease"), "n04": ("Cluster", "Deployment"),
    "n05": ("Pod", "CommandOutput"), "n06": ("Cluster", "Pod"),
    "n07": ("Cluster", "Namespace"), "n08": ("Namespace", "Event"),
    "p01": ("Service", "Service"), "p02": ("Cluster", "Ingress"),
    "p03": ("Deployment", "Deployment"), "p04": ("Node", "Node"),
    "p05": ("Cluster", "Node"), "p06": ("Cluster", "Service"),
    "p07": ("Namespace", "HelmRelease"),
    "c13": ("Namespace", "Pod"), "c14": ("Pod", "PodLog"),
    "c15": ("Pod", "Pod"), "c16": ("Ingress", "Ingress"),
    "c17": ("Cluster", "Service"), "c18": ("Cluster", "Pod"),
    "c19": ("Cluster", "Deployment"), "c20": ("Namespace", "Event"),
    "c21": ("Node", "Node"), "c22": ("Cluster", "HelmRelease"),
    "c23": ("Namespace", "HelmRelease"), "c24": ("Pod", "CommandOutput"),
    "c25": ("Cluster", "Configuration"), "c26": ("Deployment", "Deployment"),
    "c27": ("HelmRelease", "HelmRelease"), "c28": ("Service", "Service"),
    "s09": ("Pod", "PodLog"), "s10": ("Cluster", "Namespace"),
    "s11": ("Cluster", "Pod"), "s12": ("Pod", "Pod"),
    "s13": ("Namespace", "Event"), "s14": ("Cluster", "Pod"),
    "s15": ("Node", "Node"), "s16": ("Cluster", "Configuration"),
    "s17": ("HelmRelease", "HelmRelease"), "s18": ("Cluster", "Service"),
    "s19": ("Namespace", "HelmRelease"), "s20": ("Service", "Service"),
    "m09": ("Namespace", "PodLog"), "m10": ("Namespace", "CommandOutput"),
    "m11": ("Deployment", "PodLog"), "m12": ("Service", "CommandOutput"),
    "m13": ("Namespace", "PodLog"), "m14": ("Deployment", "CommandOutput"),
    "m15": ("Namespace", "PodLog"), "m16": ("Service", "CommandOutput"),
    "a08": ("Cluster", "Event"), "a09": ("Pod", "PodLog"),
    "a10": ("Cluster", "Service"), "a11": ("Pod", "PodLog"),
    "a12": ("Cluster", "Deployment"), "a13": ("Cluster", "Node"),
    "a14": ("Pod", "PodLog"), "a15": ("Cluster", "Ingress"),
    "n09": ("Namespace", "Pod"), "n10": ("Cluster", "HelmRelease"),
    "n11": ("Pod", "Pod"), "n12": ("Cluster", "Node"),
    "n13": ("Service", "Service"), "n14": ("Namespace", "Event"),
    "n15": ("Ingress", "Ingress"), "n16": ("Cluster", "Deployment"),
    "n17": ("Namespace", "Pod"), "n18": ("HelmRelease", "HelmRelease"),
    "p08": ("Deployment", "Pod"), "p09": ("Namespace", "Deployment"),
    "p10": ("Namespace", "Service"), "p11": ("Cluster", "Ingress"),
    "p12": ("Namespace", "HelmRelease"), "p13": ("Namespace", "Pod"),
    "p14": ("Cluster", "Node"), "p15": ("Namespace", "Ingress"),
    "p16": ("Cluster", "Resource"), "p17": ("Node", "Node"),
    "c29": ("Cluster", "Node"), "c30": ("Service", "Service"),
    "c31": ("Service", "Pod"), "c32": ("Deployment", "Deployment"),
    "c33": ("Pod", "CommandOutput"), "c34": ("Cluster", "Event"),
    "c35": ("Namespace", "HelmRelease"), "c36": ("Deployment", "Deployment"),
    "n19": ("Namespace", "Ingress"), "n20": ("Deployment", "Deployment"),
    "m17": ("Service", "PodLog"), "m18": ("Namespace", "CommandOutput"),
    "m19": ("Namespace", "PodLog"), "m20": ("Service", "CommandOutput"),
}

# ── K8s Fine (21 types) ─────────────────────────────────────────────
K8S_FINE = {
    "c01": ("Cluster", "Pod"), "c02": ("Cluster", "Namespace"),
    "c03": ("Pod", "PodDetail"), "c04": ("Pod", "Pod"),
    "c05": ("Cluster", "Deployment"), "c06": ("Pod", "PodLog"),
    "c07": ("Namespace", "Service"), "c08": ("Cluster", "HelmInstall"),
    "c09": ("Cluster", "Event"), "c10": ("Pod", "CommandOutput"),
    "c11": ("Cluster", "Configuration"), "c12": ("Cluster", "HelmRelease"),
    "s01": ("Cluster", "Pod"), "s02": ("Cluster", "Configuration"),
    "s03": ("Pod", "Pod"), "s04": ("Cluster", "Deployment"),
    "s05": ("Cluster", "PodCreation"), "s06": ("HelmRelease", "HelmRelease"),
    "s07": ("Pod", "PodLog"), "s08": ("Pod", "CommandOutput"),
    "m01": ("Namespace", "PodLog"), "m02": ("Namespace", "CommandOutput"),
    "m03": ("Service", "CommandOutput"), "m04": ("Deployment", "PodLog"),
    "m05": ("Namespace", "Event"), "m06": ("Namespace", "Ingress"),
    "m07": ("Namespace", "HelmInstall"), "m08": ("Namespace", "CommandOutput"),
    "a01": ("Deployment", "DeploymentDetail"), "a02": ("Cluster", "Pod"),
    "a03": ("Pod", "PodDetail"), "a04": ("Namespace", "Pod"),
    "a05": ("Cluster", "Deployment"), "a06": ("Cluster", "Service"),
    "a07": ("Pod", "PodLog"),
    "n01": ("Namespace", "Pod"), "n02": ("Pod", "PodLog"),
    "n03": ("HelmRelease", "HelmRelease"), "n04": ("Cluster", "Deployment"),
    "n05": ("Pod", "CommandOutput"), "n06": ("Cluster", "PodCreation"),
    "n07": ("Cluster", "Namespace"), "n08": ("Namespace", "Event"),
    "p01": ("Service", "ServiceDetail"), "p02": ("Cluster", "Ingress"),
    "p03": ("Deployment", "Deployment"), "p04": ("Node", "NodeDetail"),
    "p05": ("Cluster", "Node"), "p06": ("Cluster", "Service"),
    "p07": ("Namespace", "HelmRelease"),
    "c13": ("Namespace", "Pod"), "c14": ("Pod", "PodLog"),
    "c15": ("Pod", "Pod"), "c16": ("Ingress", "IngressDetail"),
    "c17": ("Cluster", "Service"), "c18": ("Cluster", "PodCreation"),
    "c19": ("Cluster", "Deployment"), "c20": ("Namespace", "Event"),
    "c21": ("Node", "NodeDetail"), "c22": ("Cluster", "HelmInstall"),
    "c23": ("Namespace", "HelmRelease"), "c24": ("Pod", "CommandOutput"),
    "c25": ("Cluster", "Configuration"), "c26": ("Deployment", "DeploymentDetail"),
    "c27": ("HelmRelease", "HelmRelease"), "c28": ("Service", "Service"),
    "s09": ("Pod", "PodLog"), "s10": ("Cluster", "Namespace"),
    "s11": ("Cluster", "Pod"), "s12": ("Pod", "Pod"),
    "s13": ("Namespace", "Event"), "s14": ("Cluster", "PodCreation"),
    "s15": ("Node", "NodeDetail"), "s16": ("Cluster", "Configuration"),
    "s17": ("HelmRelease", "HelmRelease"), "s18": ("Cluster", "Service"),
    "s19": ("Namespace", "HelmRelease"), "s20": ("Service", "ServiceDetail"),
    "m09": ("Namespace", "PodLog"), "m10": ("Namespace", "CommandOutput"),
    "m11": ("Deployment", "PodLog"), "m12": ("Service", "CommandOutput"),
    "m13": ("Namespace", "PodLog"), "m14": ("Deployment", "CommandOutput"),
    "m15": ("Namespace", "PodLog"), "m16": ("Service", "CommandOutput"),
    "a08": ("Cluster", "Event"), "a09": ("Pod", "PodLog"),
    "a10": ("Cluster", "Service"), "a11": ("Pod", "PodLog"),
    "a12": ("Cluster", "Deployment"), "a13": ("Cluster", "Node"),
    "a14": ("Pod", "PodLog"), "a15": ("Cluster", "Ingress"),
    "n09": ("Namespace", "Pod"), "n10": ("Cluster", "HelmRelease"),
    "n11": ("Pod", "PodDetail"), "n12": ("Cluster", "Node"),
    "n13": ("Service", "Service"), "n14": ("Namespace", "Event"),
    "n15": ("Ingress", "IngressDetail"), "n16": ("Cluster", "Deployment"),
    "n17": ("Namespace", "Pod"), "n18": ("HelmRelease", "HelmRelease"),
    "p08": ("Deployment", "Pod"), "p09": ("Namespace", "Deployment"),
    "p10": ("Namespace", "Service"), "p11": ("Cluster", "Ingress"),
    "p12": ("Namespace", "HelmInstall"), "p13": ("Namespace", "PodCreation"),
    "p14": ("Cluster", "Node"), "p15": ("Namespace", "Ingress"),
    "p16": ("Cluster", "Resource"), "p17": ("Node", "Node"),
    "c29": ("Cluster", "Node"), "c30": ("Service", "ServiceDetail"),
    "c31": ("Service", "Pod"), "c32": ("Deployment", "Deployment"),
    "c33": ("Pod", "CommandOutput"), "c34": ("Cluster", "Event"),
    "c35": ("Namespace", "HelmInstall"), "c36": ("Deployment", "DeploymentDetail"),
    "n19": ("Namespace", "Ingress"), "n20": ("Deployment", "DeploymentDetail"),
    "m17": ("Service", "PodLog"), "m18": ("Namespace", "CommandOutput"),
    "m19": ("Namespace", "PodLog"), "m20": ("Service", "CommandOutput"),
}

# ── AAP Coarse (8 types) ────────────────────────────────────────────
AAP_COARSE = {
    "c01": ("Platform", "Inventory"), "c02": ("Platform", "Inventory"),
    "c03": ("Platform", "Job"), "c04": ("Platform", "Credential"),
    "c05": ("Platform", "Identity"), "c06": ("Platform", "Credential"),
    "c07": ("Platform", "Identity"), "c08": ("Platform", "Identity"),
    "c09": ("Inventory", "Inventory"), "c10": ("Inventory", "Inventory"),
    "c11": ("Identity", "Credential"), "c12": ("Identity", "Identity"),
    "c13": ("Identity", "Identity"), "c14": ("Job", "Job"),
    "c15": ("Job", "Job"), "c16": ("Inventory", "Inventory"),
    "c17": ("Credential", "Credential"), "c18": ("Job", "Job"),
    "c19": ("Job", "Job"), "c20": ("Inventory", "Inventory"),
    "c21": ("Inventory", "Inventory"), "c22": ("Inventory", "Inventory"),
    "c23": ("Credential", "Credential"), "c24": ("Job", "Job"),
    "c25": ("Inventory", "Identity"), "c26": ("Platform", "EDA"),
    "c27": ("EDA", "EDA"), "c28": ("Platform", "EDA"),
    "c29": ("Platform", "Workflow"), "c30": ("Platform", "Platform"),
    "c31": ("Platform", "Auth"), "c32": ("Credential", "Credential"),
    "c33": ("Job", "Workflow"), "c34": ("Job", "Job"),
    "c35": ("Workflow", "Workflow"),
    "s01": ("Platform", "Job"), "s02": ("Platform", "Credential"),
    "s03": ("Platform", "Inventory"), "s04": ("Platform", "Platform"),
    "s05": ("Platform", "EDA"), "s06": ("Platform", "Identity"),
    "s07": ("Platform", "Workflow"), "s08": ("Job", "Job"),
    "s09": ("Job", "Job"), "s10": ("Platform", "Credential"),
    "s11": ("Platform", "Identity"), "s12": ("Platform", "Credential"),
    "s13": ("Inventory", "Inventory"), "s14": ("Credential", "Credential"),
    "s15": ("Job", "Job"), "s16": ("Platform", "Workflow"),
    "s17": ("Job", "Job"), "s18": ("Identity", "Identity"),
    "s19": ("Platform", "Inventory"), "s20": ("EDA", "EDA"),
    "m01": ("Identity", "Inventory"), "m02": ("Identity", "Inventory"),
    "m03": ("Identity", "Job"), "m04": ("Identity", "Job"),
    "m05": ("Identity", "Job"), "m06": ("Inventory", "Credential"),
    "m07": ("Identity", "Inventory"), "m08": ("Inventory", "Credential"),
    "m09": ("Inventory", "Credential"), "m10": ("Auth", "Identity"),
    "m11": ("EDA", "EDA"), "m12": ("Identity", "Inventory"),
    "m13": ("Inventory", "Workflow"), "m14": ("Inventory", "Job"),
    "m15": ("Identity", "Inventory"), "m16": ("Identity", "Inventory"),
    "m17": ("Inventory", "Job"), "m18": ("Credential", "Credential"),
    "m19": ("Platform", "Identity"), "m20": ("Inventory", "Job"),
    "a01": ("Credential", "Credential"), "a02": ("Job", "Job"),
    "a03": ("Job", "Job"), "a04": ("Workflow", "Workflow"),
    "a05": ("Platform", "Platform"), "a06": ("Credential", "Credential"),
    "a07": ("Job", "Credential"), "a08": ("Platform", "Job"),
    "a09": ("Inventory", "Inventory"), "a10": ("Credential", "Credential"),
    "a11": ("Inventory", "Inventory"), "a12": ("Platform", "Workflow"),
    "a13": ("Platform", "EDA"), "a14": ("Inventory", "Inventory"),
    "a15": ("Job", "Job"),
    "n01": ("Platform", "Inventory"), "n02": ("Inventory", "Inventory"),
    "n03": ("Identity", "Identity"), "n04": ("Job", "Job"),
    "n05": ("Job", "Workflow"), "n06": ("Job", "Credential"),
    "n07": ("Inventory", "Inventory"), "n08": ("Job", "Job"),
    "n09": ("Identity", "Credential"), "n10": ("Workflow", "Workflow"),
    "n11": ("EDA", "EDA"), "n12": ("Inventory", "Inventory"),
    "n13": ("EDA", "EDA"), "n14": ("Platform", "Platform"),
    "n15": ("Inventory", "Job"),
    "mp01": ("Job", "Workflow"), "mp02": ("Identity", "Credential"),
    "mp03": ("Platform", "Platform"), "mp04": ("Credential", "Workflow"),
    "mp05": ("Workflow", "Workflow"), "mp06": ("Inventory", "Inventory"),
    "mp07": ("Inventory", "Inventory"), "mp08": ("Inventory", "Inventory"),
    "mp09": ("Platform", "Platform"), "mp10": ("Credential", "Credential"),
    "mp11": ("Inventory", "Workflow"), "mp12": ("Workflow", "Workflow"),
    "mp13": ("Workflow", "Workflow"), "mp14": ("Credential", "Credential"),
    "mp15": ("Job", "Workflow"),
}

# ── AAP Medium (50 types) ───────────────────────────────────────────
AAP_MEDIUM = {
    "c01": ("Platform", "Inventory"), "c02": ("Platform", "Host"),
    "c03": ("Platform", "JobTemplate"), "c04": ("Platform", "Credential"),
    "c05": ("Platform", "Organization"), "c06": ("Platform", "Project"),
    "c07": ("Platform", "Team"), "c08": ("Platform", "User"),
    "c09": ("Inventory", "Host"), "c10": ("Inventory", "Group"),
    "c11": ("Organization", "Credential"), "c12": ("Organization", "Team"),
    "c13": ("Team", "User"), "c14": ("JobTemplate", "Job"),
    "c15": ("Job", "Job"), "c16": ("Inventory", "Inventory"),
    "c17": ("Project", "Project"), "c18": ("Job", "Job"),
    "c19": ("Job", "Job"), "c20": ("Group", "Host"),
    "c21": ("Inventory", "InventorySource"), "c22": ("Inventory", "Host"),
    "c23": ("Credential", "Credential"), "c24": ("JobTemplate", "Schedule"),
    "c25": ("Inventory", "Role"), "c26": ("Platform", "Activation"),
    "c27": ("Activation", "Activation"), "c28": ("Platform", "DecisionEnvironment"),
    "c29": ("Platform", "WorkflowJobTemplate"), "c30": ("Platform", "InstanceGroup"),
    "c31": ("Platform", "Authenticator"), "c32": ("Project", "Project"),
    "c33": ("JobTemplate", "NotificationTemplate"), "c34": ("Schedule", "Job"),
    "c35": ("WorkflowJob", "WorkflowJobNode"),
    "s01": ("Platform", "JobTemplate"), "s02": ("Platform", "ExecutionEnvironment"),
    "s03": ("Platform", "Host"), "s04": ("InstanceGroup", "InstanceGroup"),
    "s05": ("Platform", "Activation"), "s06": ("Platform", "Token"),
    "s07": ("Platform", "WorkflowJobTemplate"), "s08": ("Job", "Job"),
    "s09": ("Job", "Job"), "s10": ("Platform", "Credential"),
    "s11": ("Platform", "RoleDefinition"), "s12": ("Platform", "Project"),
    "s13": ("Inventory", "Host"), "s14": ("Project", "Project"),
    "s15": ("JobTemplate", "Schedule"), "s16": ("Platform", "NotificationTemplate"),
    "s17": ("JobTemplate", "Job"), "s18": ("Team", "User"),
    "s19": ("Platform", "InventorySource"), "s20": ("Activation", "Activation"),
    "m01": ("Organization", "Host"), "m02": ("Organization", "Group"),
    "m03": ("Organization", "Job"), "m04": ("Organization", "Schedule"),
    "m05": ("Organization", "AdHocCommand"), "m06": ("Inventory", "Credential"),
    "m07": ("Organization", "InventorySource"), "m08": ("Group", "Credential"),
    "m09": ("Host", "Credential"), "m10": ("Authenticator", "Role"),
    "m11": ("EventStream", "ActivationInstance"), "m12": ("Organization", "Label"),
    "m13": ("Inventory", "NotificationTemplate"), "m14": ("Host", "Schedule"),
    "m15": ("Team", "Inventory"), "m16": ("User", "Inventory"),
    "m17": ("Group", "Schedule"), "m18": ("Project", "Credential"),
    "m19": ("Instance", "Role"), "m20": ("Inventory", "Job"),
    "a01": ("Credential", "Credential"), "a02": ("Job", "Job"),
    "a03": ("JobTemplate", "JobTemplate"), "a04": ("WorkflowJobTemplate", "WorkflowJobTemplate"),
    "a05": ("Platform", "Instance"), "a06": ("ExecutionEnvironment", "ExecutionEnvironment"),
    "a07": ("Schedule", "Credential"), "a08": ("Platform", "Schedule"),
    "a09": ("Inventory", "Inventory"), "a10": ("Credential", "Credential"),
    "a11": ("Group", "Group"), "a12": ("Platform", "WorkflowJobNode"),
    "a13": ("Platform", "EdaCredentialType"), "a14": ("InventorySource", "InventorySource"),
    "a15": ("Job", "Job"),
    "n01": ("Platform", "Host"), "n02": ("Inventory", "Inventory"),
    "n03": ("Organization", "Team"), "n04": ("Job", "Job"),
    "n05": ("JobTemplate", "NotificationTemplate"), "n06": ("Schedule", "Credential"),
    "n07": ("Host", "Host"), "n08": ("JobTemplate", "Job"),
    "n09": ("Team", "Project"), "n10": ("WorkflowJob", "WorkflowJobNode"),
    "n11": ("EdaCredential", "EdaCredential"), "n12": ("Host", "Group"),
    "n13": ("Activation", "Activation"), "n14": ("Platform", "Setting"),
    "n15": ("InventorySource", "Schedule"),
    "mp01": ("JobTemplate", "NotificationTemplate"), "mp02": ("Organization", "Credential"),
    "mp03": ("Platform", "Platform"), "mp04": ("Project", "NotificationTemplate"),
    "mp05": ("WorkflowJobTemplate", "NotificationTemplate"), "mp06": ("Group", "Group"),
    "mp07": ("Inventory", "Inventory"), "mp08": ("Group", "Host"),
    "mp09": ("Instance", "Instance"), "mp10": ("Credential", "Credential"),
    "mp11": ("InventorySource", "NotificationTemplate"), "mp12": ("NotificationTemplate", "NotificationTemplate"),
    "mp13": ("WorkflowJobNode", "WorkflowJobTemplateNode"), "mp14": ("Credential", "Credential"),
    "mp15": ("SystemJobTemplate", "NotificationTemplate"),
}

# ── AAP Fine (88 types) ─────────────────────────────────────────────
AAP_FINE = {
    "c01": ("Platform", "Inventory"), "c02": ("Platform", "Host"),
    "c03": ("Platform", "JobTemplate"), "c04": ("Platform", "Credential"),
    "c05": ("Platform", "Organization"), "c06": ("Platform", "Project"),
    "c07": ("Platform", "Team"), "c08": ("Platform", "User"),
    "c09": ("Inventory", "Host"), "c10": ("Inventory", "Group"),
    "c11": ("Organization", "Credential"), "c12": ("Organization", "Team"),
    "c13": ("Team", "User"), "c14": ("JobTemplate", "Job"),
    "c15": ("Job", "Job"), "c16": ("Inventory", "Inventory"),
    "c17": ("Project", "Project"), "c18": ("Job", "JobDetail"),
    "c19": ("Job", "JobListing"), "c20": ("Group", "Host"),
    "c21": ("Inventory", "InventorySource"), "c22": ("Inventory", "Host"),
    "c23": ("Credential", "Credential"), "c24": ("JobTemplate", "Schedule"),
    "c25": ("Inventory", "Role"), "c26": ("Platform", "Activation"),
    "c27": ("Activation", "Activation"), "c28": ("Platform", "DecisionEnvironment"),
    "c29": ("Platform", "WorkflowJobTemplate"), "c30": ("Platform", "InstanceGroup"),
    "c31": ("Platform", "Authenticator"), "c32": ("Project", "Project"),
    "c33": ("JobTemplate", "NotificationTemplate"), "c34": ("Schedule", "Job"),
    "c35": ("WorkflowJob", "WorkflowJobNode"),
    "s01": ("Platform", "JobTemplate"), "s02": ("Platform", "ExecutionEnvironment"),
    "s03": ("Platform", "Host"), "s04": ("InstanceGroup", "InstanceGroup"),
    "s05": ("Platform", "Activation"), "s06": ("Platform", "Token"),
    "s07": ("Platform", "WorkflowJobTemplate"), "s08": ("Job", "JobDetail"),
    "s09": ("Job", "Job"), "s10": ("Platform", "Credential"),
    "s11": ("Platform", "RoleDefinition"), "s12": ("Platform", "Project"),
    "s13": ("Inventory", "Host"), "s14": ("Project", "Project"),
    "s15": ("JobTemplate", "Schedule"), "s16": ("Platform", "NotificationTemplate"),
    "s17": ("JobTemplate", "Job"), "s18": ("Team", "User"),
    "s19": ("Platform", "InventorySource"), "s20": ("Activation", "Activation"),
    "m01": ("Organization", "Host"), "m02": ("Organization", "Group"),
    "m03": ("Organization", "Job"), "m04": ("Organization", "Schedule"),
    "m05": ("Organization", "AdHocCommand"), "m06": ("Inventory", "Credential"),
    "m07": ("Organization", "InventorySource"), "m08": ("Group", "Credential"),
    "m09": ("Host", "Credential"), "m10": ("Authenticator", "Role"),
    "m11": ("EventStream", "ActivationInstance"), "m12": ("Organization", "Label"),
    "m13": ("Inventory", "NotificationTemplate"), "m14": ("Host", "Schedule"),
    "m15": ("Team", "Inventory"), "m16": ("User", "Inventory"),
    "m17": ("Group", "Schedule"), "m18": ("Project", "Credential"),
    "m19": ("Instance", "Role"), "m20": ("Inventory", "Job"),
    "a01": ("Credential", "CredentialListing"), "a02": ("Job", "JobListing"),
    "a03": ("JobTemplate", "JobTemplate"), "a04": ("WorkflowJobTemplate", "WorkflowJobTemplate"),
    "a05": ("Platform", "Instance"), "a06": ("ExecutionEnvironment", "ExecutionEnvironment"),
    "a07": ("Schedule", "Credential"), "a08": ("Platform", "Schedule"),
    "a09": ("Inventory", "InventoryListing"), "a10": ("Credential", "Credential"),
    "a11": ("Group", "GroupListing"), "a12": ("Platform", "WorkflowJobNode"),
    "a13": ("Platform", "EdaCredentialType"), "a14": ("InventorySource", "InventorySource"),
    "a15": ("Job", "JobListing"),
    "n01": ("Platform", "Host"), "n02": ("Inventory", "Inventory"),
    "n03": ("Organization", "Team"), "n04": ("Job", "JobDetail"),
    "n05": ("JobTemplate", "NotificationTemplate"), "n06": ("Schedule", "Credential"),
    "n07": ("Host", "Host"), "n08": ("JobTemplate", "Job"),
    "n09": ("Team", "Project"), "n10": ("WorkflowJob", "WorkflowJobNode"),
    "n11": ("EdaCredential", "EdaCredential"), "n12": ("Host", "Group"),
    "n13": ("Activation", "Activation"), "n14": ("Platform", "Setting"),
    "n15": ("InventorySource", "Schedule"),
    "mp01": ("JobTemplate", "NotificationTemplate"), "mp02": ("Organization", "Credential"),
    "mp03": ("Platform", "PlatformListing"), "mp04": ("Project", "NotificationTemplate"),
    "mp05": ("WorkflowJobTemplate", "NotificationTemplate"), "mp06": ("Group", "Group"),
    "mp07": ("Inventory", "InventoryListing"), "mp08": ("Group", "Host"),
    "mp09": ("Instance", "Instance"), "mp10": ("Credential", "Credential"),
    "mp11": ("InventorySource", "NotificationTemplate"), "mp12": ("NotificationTemplate", "NotificationTemplate"),
    "mp13": ("WorkflowJobNode", "WorkflowJobTemplateNode"), "mp14": ("Credential", "Credential"),
    "mp15": ("SystemJobTemplate", "NotificationTemplate"),
}

ALL_PREDICTIONS = {
    ("k8s", "coarse_entities"): K8S_COARSE,
    ("k8s", "medium_granularity"): K8S_MEDIUM,
    ("k8s", "fine_granularity"): K8S_FINE,
    ("aap", "coarse_entities"): AAP_COARSE,
    ("aap", "medium_granularity"): AAP_MEDIUM,
    ("aap", "fine_granularity"): AAP_FINE,
}

BASES = {
    "k8s": Path("/Users/jmorenas/tcr-k8s-demo/experiments"),
    "aap": Path("/Users/jmorenas/tcr-aap-demo/experiments"),
}


class FilePredictor:
    def __init__(self, predictions: dict[str, tuple[str, str]]):
        self._preds = predictions

    def predict(self, query: str, query_id: str = "") -> TypePrediction:
        src, tgt = self._preds.get(query_id, ("", ""))
        return TypePrediction(
            source=src, target=tgt,
            src_conf=1.0, tgt_conf=1.0, confidence=1.0,
            latency_ms=0.0,
        )


def evaluate_with_predictions(domain: str, experiment: str, predictions: dict):
    base = BASES[domain]
    exp_dir = base / experiment

    sys.path.insert(0, str(exp_dir))
    sys.path.insert(0, str(base))

    with open(exp_dir / "data" / "graph_snapshot.json") as f:
        graph_raw = json.load(f)
    with open(exp_dir / "data" / "test_queries.json") as f:
        queries = json.load(f)

    from tcr.graph import CompositionGraph
    graph = CompositionGraph(exp_dir / "data" / "graph_snapshot.json")

    tools = graph_raw["tools"]
    type_names = set(graph_raw["entity_types"].keys())

    # Validate predictions
    invalid = 0
    for qid, (src, tgt) in predictions.items():
        if src not in type_names or tgt not in type_names:
            invalid += 1

    src_correct = 0
    tgt_correct = 0
    exact_match = 0
    per_query = []

    all_tools_text = "\n".join(
        f"- {t['name']}: {t['description']}" for t in tools
    )
    all_tools_tokens = len(all_tools_text.split()) * 4 // 3

    for q in queries:
        qid = q["id"]
        gold_src, gold_tgt = q["source_type"], q["target_type"]
        expected = set(q["expected_tools"])

        pred_src, pred_tgt = predictions.get(qid, ("", ""))

        s_ok = pred_src == gold_src
        t_ok = pred_tgt == gold_tgt
        if s_ok: src_correct += 1
        if t_ok: tgt_correct += 1
        if s_ok and t_ok: exact_match += 1

        if pred_src in type_names and pred_tgt in type_names:
            candidates = set(graph.candidate_tools(pred_src, pred_tgt))
        else:
            candidates = set()

        tp = expected & candidates
        fp = candidates - expected
        fn = expected - candidates

        precision = len(tp) / len(candidates) if candidates else 0.0
        recall = len(tp) / len(expected) if expected else 1.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        per_query.append({
            "id": qid,
            "query": q["query"],
            "gold": f"{gold_src} -> {gold_tgt}",
            "pred": f"{pred_src} -> {pred_tgt}",
            "src_ok": s_ok,
            "tgt_ok": t_ok,
            "f1": round(f1, 4),
            "candidates": len(candidates),
        })

    n = len(queries)
    f1s = [r["f1"] for r in per_query]
    cands = [r["candidates"] for r in per_query]

    import statistics
    result = {
        "domain": domain,
        "experiment": experiment,
        "n_types": len(type_names),
        "n_queries": n,
        "source_accuracy": round(src_correct / n, 4),
        "target_accuracy": round(tgt_correct / n, 4),
        "exact_match": round(exact_match / n, 4),
        "routing_f1": round(statistics.mean(f1s), 4),
        "candidate_size_avg": round(statistics.mean(cands), 2),
        "invalid_predictions": invalid,
    }

    return result, per_query


def main():
    print("=" * 70)
    print("Claude Opus 4.6 — Granularity Experiment Predictions")
    print("=" * 70)

    all_results = {}

    for (domain, experiment), predictions in ALL_PREDICTIONS.items():
        result, per_query = evaluate_with_predictions(domain, experiment, predictions)
        key = f"{domain}/{experiment}"
        all_results[key] = result

        print(f"\n{key} ({result['n_types']} types, {result['n_queries']} queries)")
        print(f"  Source accuracy:  {result['source_accuracy']:.4f}")
        print(f"  Target accuracy:  {result['target_accuracy']:.4f}")
        print(f"  Exact match:      {result['exact_match']:.4f}")
        print(f"  Routing F1:       {result['routing_f1']:.4f}")
        print(f"  Avg candidates:   {result['candidate_size_avg']:.1f}")
        if result['invalid_predictions'] > 0:
            print(f"  ⚠ Invalid preds: {result['invalid_predictions']}")

        # Show errors
        errors = [r for r in per_query if not (r["src_ok"] and r["tgt_ok"])]
        if errors:
            print(f"  Errors ({len(errors)}):")
            for e in errors[:10]:
                print(f"    {e['id']}: gold={e['gold']} pred={e['pred']}")
            if len(errors) > 10:
                print(f"    ... and {len(errors) - 10} more")

        # Save full results
        base = BASES[domain]
        results_dir = base / experiment / "results"
        results_dir.mkdir(parents=True, exist_ok=True)

        full_result = {
            "experiment": experiment,
            "model": "claude-opus-4-6",
            "model_slug": "opus",
            "end_to_end": {
                "mode": "end_to_end",
                "n_queries": result["n_queries"],
                "source_accuracy": result["source_accuracy"],
                "target_accuracy": result["target_accuracy"],
                "exact_match": result["exact_match"],
                "routing_f1": result["routing_f1"],
                "candidate_size_avg": result["candidate_size_avg"],
            },
            "per_query": per_query,
        }
        out_path = results_dir / "results_opus.json"
        with open(out_path, "w") as f:
            json.dump(full_result, f, indent=2)

    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"{'Config':<30} {'Types':>5} {'EM':>6} {'F1':>6} {'Cands':>6}")
    print("-" * 55)
    for key, r in all_results.items():
        print(f"{key:<30} {r['n_types']:>5} {r['exact_match']:>6.3f} {r['routing_f1']:>6.4f} {r['candidate_size_avg']:>6.1f}")


if __name__ == "__main__":
    main()
